"""Deterministic, dependency-free Solidity source scanning.

Extracts the identifier surface a stage-3 binding may legally reference:
contracts, functions, parameters, state variables, modifiers, events and
user-defined types. It is deliberately a *best effort* lexical scanner; it
never claims a full parse, and consumers (``lib.binding_validate``) use it for
lint/suggestion rather than authority.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

IDENT = r'[A-Za-z_$][A-Za-z0-9_$]*'

# Solidity reserved words that are not user-declared identifiers.
KEYWORDS = {
    'abstract', 'after', 'alias', 'apply', 'auto', 'byte', 'case', 'catch',
    'copyof', 'default', 'define', 'final', 'implements', 'in', 'inline',
    'let', 'macro', 'match', 'mutable', 'null', 'of', 'partial', 'promise',
    'reference', 'relocatable', 'sealed', 'sizeof', 'static', 'supports',
    'switch', 'try', 'typedef', 'typeof', 'unchecked', 'var',
    # actual Solidity keywords
    'pragma', 'solidity', 'import', 'as', 'from', 'contract', 'interface',
    'library', 'is', 'struct', 'enum', 'function', 'modifier', 'event',
    'constructor', 'receive', 'fallback', 'returns', 'return', 'emit',
    'if', 'else', 'for', 'while', 'do', 'break', 'continue', 'delete',
    'new', 'throw', 'public', 'private', 'internal', 'external', 'pure',
    'view', 'payable', 'constant', 'immutable', 'anonymous', 'indexed',
    'storage', 'memory', 'calldata', 'mapping', 'address', 'bool', 'string',
    'bytes', 'byte', 'uint', 'int', 'fixed', 'ufixed', 'true', 'false',
    'using', 'revert', 'require', 'assert', 'assembly', 'tuple',
    'block', 'msg', 'tx', 'abi', 'this', 'super', 'now', 'selfdestruct',
    'error', 'revert', 'type', 'unchecked',
}

# Builtin member names reachable via msg/block/tx/type without declaration.
BUILTIN_MEMBERS = {
    'sender', 'value', 'data', 'sig', 'gas', 'origin', 'gasprice', 'coinbase',
    'timestamp', 'number', 'difficulty', 'gaslimit', 'chainid', 'basefee',
    'prevrandao', 'blobbasefee', 'creationCode', 'runtimeCode', 'interfaceId',
    'min', 'max', 'balance', 'code', 'codehash', 'call', 'delegatecall',
    'staticcall', 'transfer', 'send', 'length', 'push', 'pop', 'encode',
    'encodePacked', 'encodeWithSelector', 'encodeWithSignature', 'encodeCall',
    'decode', 'creationCode', 'to', 'from', 'gasleft', 'keccak256', 'sha256',
    'ripemd160', 'ecrecover', 'addmod', 'mulmod', 'blockhash',
}

_DECL_RE = re.compile(
    rf'(?m)^\s*(abstract\s+)?(contract|interface|library)\s+({IDENT})')
_FUNC_RE = re.compile(
    rf'(?m)\bfunction\s+({IDENT})\s*\(([^)]*)\)')
_MOD_RE = re.compile(
    rf'(?m)\bmodifier\s+({IDENT})\s*(?:\([^)]*\))?')
_EVENT_RE = re.compile(
    rf'(?m)\bevent\s+({IDENT})\s*\(([^)]*)\)')
_ERROR_RE = re.compile(
    rf'(?m)\berror\s+({IDENT})\s*\(([^)]*)\)')
_STRUCT_RE = re.compile(
    rf'(?m)\bstruct\s+({IDENT})')
_ENUM_RE = re.compile(
    rf'(?m)\benum\s+({IDENT})')
_UDVT_RE = re.compile(
    rf'(?m)\btype\s+({IDENT})\s+is\s+')
_PARAM_RE = re.compile(
    rf'\b(?:[A-Za-z_][A-Za-z0-9_.]*|mapping\([^)]*\))(?:\s*\[[^\]]*\])?\s+(?:'
    rf'(?:storage|memory|calldata)\s+)?(?:indexed\s+)?({IDENT})')
_LOCAL_DECL_RE = re.compile(
    rf'(?m)^[ \t]+(?:mapping\([^)]*\)|{IDENT}(?:\s*\[[^\]]*\])?)'
    rf'(?:\s+(?:storage|memory|calldata))?\s+({IDENT})\s*(?:=|;)')


@dataclass
class SolFile:
    path: Path
    contracts: list[str] = field(default_factory=list)
    functions: dict[str, list[dict]] = field(default_factory=dict)
    params: set[str] = field(default_factory=set)
    state_vars: set[str] = field(default_factory=set)
    modifiers: set[str] = field(default_factory=set)
    events: set[str] = field(default_factory=set)
    errors: set[str] = field(default_factory=set)
    structs: set[str] = field(default_factory=set)
    enums: set[str] = field(default_factory=set)
    user_types: set[str] = field(default_factory=set)
    locals: set[str] = field(default_factory=set)

    def declared(self) -> set[str]:
        return (set(self.contracts) | set(self.functions) | self.params |
                self.state_vars | self.modifiers | self.events | self.errors |
                self.structs | self.enums | self.user_types | self.locals)

    def observable(self) -> set[str]:
        """Runtime values a stage-3 binding may snapshot or call: state
        variables, function parameters and callable functions/getters.

        Deliberately excludes constants/enums/struct/contract names because a
        binding ``solidity_expr`` cannot snapshot a type or compile-time
        constant as an observable state value.
        """
        return self.state_vars | self.params | set(self.functions)


@dataclass
class SolidityIndex:
    files: dict[Path, SolFile] = field(default_factory=dict)

    def all_declared(self) -> set[str]:
        out: set[str] = set()
        for f in self.files.values():
            out |= f.declared()
        return out

    def all_observable(self) -> set[str]:
        out: set[str] = set()
        for f in self.files.values():
            out |= f.observable()
        return out

    def all_state_vars(self) -> set[str]:
        out: set[str] = set()
        for f in self.files.values():
            out |= f.state_vars
        return out


def _strip_comments_and_strings(source: str) -> str:
    """Blank out comments and string/nat-spec bodies to avoid false matches."""
    out = []
    i = 0
    n = len(source)
    while i < n:
        if source.startswith('//', i):
            j = source.find('\n', i)
            out.append('\n' if j != -1 else '')
            i = j if j != -1 else n
            continue
        if source.startswith('/*', i):
            j = source.find('*/', i + 2)
            out.append(' ' * (j - i + 2 if j != -1 else n - i))
            i = j + 2 if j != -1 else n
            continue
        ch = source[i]
        if ch in ('"', "'"):
            q = ch
            j = i + 1
            while j < n and source[j] != q:
                j += 1
            out.append(' ' * (j - i + 1))
            i = j + 1
            continue
        out.append(ch)
        i += 1
    return ''.join(out)


def _scan_params(signature: str) -> set[str]:
    params: set[str] = set()
    for m in _PARAM_RE.finditer(signature):
        params.add(m.group(1))
    return params


_STATE_VAR_RE = re.compile(
    rf'(?m)^\s*(?:mapping\([^)]*\)|{IDENT}(?:\s*\[[^\]]*\])?)'
    rf'(?:\s+(?:public|private|internal|constant|immutable|override))*'
    rf'\s+({IDENT})\s*(?:=|;)')


def _matching_brace(clean: str, open_idx: int) -> int:
    """Return the index of the ``}`` matching ``{`` at ``open_idx`` in already
    comment/string-stripped text."""
    depth = 0
    i = open_idx
    n = len(clean)
    while i < n:
        if clean[i] == '{':
            depth += 1
        elif clean[i] == '}':
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return n - 1


def contract_state_vars(source: str, contract: str) -> set[str]:
    """Best-effort state-variable names declared directly inside ``contract``.

    Includes function-local declarations too (the scanner is lexical), so it is
    only meaningful as an *over-approximation* of what ``contract`` can see.
    Returns an empty set when the contract is not found.
    """
    clean = _strip_comments_and_strings(source)
    return _contract_state_vars_clean(clean, contract)


def file_level_functions(source: str) -> set[str]:
    """Function declarations outside any contract/interface/library body."""
    clean = _strip_comments_and_strings(source)
    masked = list(clean)
    for m in _DECL_RE.finditer(clean):
        open_idx = clean.find('{', m.end())
        if open_idx < 0:
            continue
        close_idx = _matching_brace(clean, open_idx)
        for i in range(open_idx, close_idx + 1):
            masked[i] = ' '
    outside = ''.join(masked)
    return {m.group(1) for m in re.finditer(
        rf'\bfunction\s+({IDENT})\s*\(', outside)}


def file_level_state_vars(source: str) -> set[str]:
    """State-variable declarations outside any contract/interface/library.

    Flattened files keep top-level ``uint256 constant X = ...`` helpers that
    are visible from every contract.  These must not be treated as
    cross-contract references by the stage-3 binding linter.
    """
    clean = _strip_comments_and_strings(source)
    masked = list(clean)
    for m in _DECL_RE.finditer(clean):
        open_idx = clean.find('{', m.end())
        if open_idx < 0:
            continue
        close_idx = _matching_brace(clean, open_idx)
        for i in range(open_idx, close_idx + 1):
            masked[i] = ' '
    outside = ''.join(masked)
    return {m.group(1) for m in _STATE_VAR_RE.finditer(outside)}


def _contract_state_vars_clean(clean: str, contract: str) -> set[str]:
    """Direct state vars of ``contract`` in already comment-stripped text."""
    marker = re.search(
        rf'\b(?:abstract\s+)?(?:contract|interface|library)\s+'
        rf'{re.escape(contract)}\b', clean)
    if not marker:
        return set()
    open_idx = clean.find('{', marker.end())
    if open_idx < 0:
        return set()
    close_idx = _matching_brace(clean, open_idx)
    return {m.group(1) for m in _STATE_VAR_RE.finditer(clean[open_idx + 1:close_idx])}
_INSTANCE_VAR_RE = re.compile(
    rf'(?m)^\s*({IDENT})'
    rf'(?:(?:\s+public|\s+private|\s+internal|\s+constant|\s+immutable|\s+override)+)*'
    rf'\s+({IDENT})\s*(?:=[^;]*)?;')


def contract_instances(source: str, contract: str) -> dict[str, str]:
    """Return ``{instance_name: type_name}`` for contract-typed state variables.

    Scans ``contract``'s body for ``<ContractType> <visibility> <name> [= ...];``
    and keeps only declarations whose type is itself a declared contract /
    interface / library name in the same file. Used to suggest
    ``instance.member`` bindings for cross-contract invariants anchored in a
    PoC test harness (for example ``ServiceNft public snft;`` -> ``{"snft":
    "ServiceNft"}``).
    """
    clean = _strip_comments_and_strings(source)
    marker = re.search(
        rf'\b(?:abstract\s+)?(?:contract|interface|library)\s+'
        rf'{re.escape(contract)}\b', clean)
    if not marker:
        return {}
    open_idx = clean.find('{', marker.end())
    if open_idx < 0:
        return {}
    close_idx = _matching_brace(clean, open_idx)
    body = clean[open_idx + 1:close_idx]
    contract_names = {m.group(3) for m in _DECL_RE.finditer(clean)}
    out: dict[str, str] = {}
    for m in _INSTANCE_VAR_RE.finditer(body):
        type_name = m.group(1)
        var_name = m.group(2)
        if type_name in contract_names and var_name not in out:
            out[var_name] = type_name
    return out


def _contract_functions_clean(clean: str, contract: str) -> set[str]:
    """Function names declared directly inside ``contract``."""
    marker = re.search(
        rf'\b(?:abstract\s+)?(?:contract|interface|library)\s+'
        rf'{re.escape(contract)}\b', clean)
    if not marker:
        return set()
    open_idx = clean.find('{', marker.end())
    if open_idx < 0:
        return set()
    close_idx = _matching_brace(clean, open_idx)
    body = clean[open_idx + 1:close_idx]
    return {m.group(1) for m in re.finditer(
        rf'\bfunction\s+({IDENT})\s*\(', body)}


_INHERIT_RE = re.compile(
    rf'\b(?:abstract\s+)?(?:contract|interface|library)\s+'
    rf'({IDENT})(?:\s+is\s+([^{{]+))?\{{')


def _bases(head: str) -> list[str]:
    """Parse ``is Base1, Base2(...)`` into base contract names."""
    bases: list[str] = []
    for item in head.split(','):
        item = item.strip()
        if not item:
            continue
        m = re.match(rf'({IDENT})', item)
        if m:
            bases.append(m.group(1))
    return bases


def contract_visible_state_vars(source: str, contract: str) -> set[str]:
    """State variables visible inside ``contract`` via transitive inheritance.

    Lexical best effort: walks the ``is`` chain and unions each base contract's
    direct state variables. Returns the direct vars only when inheritance
    cannot be resolved (for example when ``contract`` is not found).
    """
    clean = _strip_comments_and_strings(source)
    decls = {m.group(1): _bases(m.group(2) or '')
             for m in _INHERIT_RE.finditer(clean)}
    seen: set[str] = set()
    out: set[str] = set()
    queue = [contract]
    while queue:
        name = queue.pop(0)
        if not name or name in seen:
            continue
        seen.add(name)
        out |= _contract_state_vars_clean(clean, name)
        for base in decls.get(name, []):
            if base not in seen:
                queue.append(base)
    return out


def contract_visible_functions(source: str, contract: str) -> set[str]:
    """Functions visible inside ``contract`` via transitive inheritance.

    Same lexical best-effort walk as ``contract_visible_state_vars``.
    """
    clean = _strip_comments_and_strings(source)
    decls = {m.group(1): _bases(m.group(2) or '')
             for m in _INHERIT_RE.finditer(clean)}
    seen: set[str] = set()
    out: set[str] = set()
    queue = [contract]
    while queue:
        name = queue.pop(0)
        if not name or name in seen:
            continue
        seen.add(name)
        out |= _contract_functions_clean(clean, name)
        for base in decls.get(name, []):
            if base not in seen:
                queue.append(base)
    return out


def poc_test_contract(source: str) -> str | None:
    """Return the concrete contract that defines the PoC ``test_*`` function.

    Scans contract bodies for ``function test_<name>`` and returns the last
    such contract (the PoC harness is normally the final contract in a
    flattened file). Returns ``None`` when no PoC test function is found.
    """
    clean = _strip_comments_and_strings(source)
    result = None
    for m in _DECL_RE.finditer(clean):
        name = m.group(3)
        open_idx = clean.find('{', m.end())
        if open_idx < 0:
            continue
        close_idx = _matching_brace(clean, open_idx)
        body = clean[open_idx + 1:close_idx]
        if re.search(r'\bfunction\s+test_[A-Za-z0-9_]+', body):
            result = name
    return result


def poc_test_function(source: str) -> tuple[str, str] | None:
    """Return ``(contract, test_function_name)`` for the PoC harness.

    Scans contract bodies for ``function test_<name>`` and returns the last
    such (contract, function) pair. Returns ``None`` when no PoC test function
    is found.
    """
    clean = _strip_comments_and_strings(source)
    result = None
    for m in _DECL_RE.finditer(clean):
        contract = m.group(3)
        open_idx = clean.find('{', m.end())
        if open_idx < 0:
            continue
        close_idx = _matching_brace(clean, open_idx)
        body = clean[open_idx + 1:close_idx]
        for fn in re.finditer(r'\bfunction\s+(test_[A-Za-z0-9_]+)\s*\(', body):
            result = (contract, fn.group(1))
    return result


def contract_has_function(source: str, contract: str, function: str) -> bool:
    """Return whether ``function`` is declared inside ``contract``."""
    clean = _strip_comments_and_strings(source)
    marker = re.search(
        rf'\b(?:abstract\s+)?(?:contract|interface|library)\s+'
        rf'{re.escape(contract)}\b', clean)
    if not marker:
        return False
    open_idx = clean.find('{', marker.end())
    if open_idx < 0:
        return False
    close_idx = _matching_brace(clean, open_idx)
    body = clean[open_idx + 1:close_idx]
    return bool(re.search(rf'\bfunction\s+{re.escape(function)}\s*\(', body))


def function_owner(source: str, function: str) -> set[str]:
    """Return the set of contracts/interfaces/libraries that declare
    ``function`` directly, plus ``None`` when it is a file-level function."""
    clean = _strip_comments_and_strings(source)
    owners: set[str] = set()
    for m in _DECL_RE.finditer(clean):
        cname = m.group(3)
        open_idx = clean.find('{', m.end())
        if open_idx < 0:
            continue
        close_idx = _matching_brace(clean, open_idx)
        body = clean[open_idx + 1:close_idx]
        if re.search(rf'\bfunction\s+{re.escape(function)}\s*\(', body):
            owners.add(cname)
    # file-level functions (outside every contract body)
    masked = list(clean)
    for m in _DECL_RE.finditer(clean):
        open_idx = clean.find('{', m.end())
        if open_idx < 0:
            continue
        close_idx = _matching_brace(clean, open_idx)
        for i in range(open_idx, close_idx + 1):
            masked[i] = ' '
    outside = ''.join(masked)
    if re.search(rf'\bfunction\s+{re.escape(function)}\s*\(', outside):
        owners.add(None)
    return owners


def state_var_owner(source: str, var: str) -> set[str]:
    """Return the set of contracts declaring ``var``, or ``None`` for a
    file-level constant/declaration."""
    clean = _strip_comments_and_strings(source)
    owners: set[str] = set()
    for m in _DECL_RE.finditer(clean):
        cname = m.group(3)
        open_idx = clean.find('{', m.end())
        if open_idx < 0:
            continue
        close_idx = _matching_brace(clean, open_idx)
        body = clean[open_idx + 1:close_idx]
        if any(mm.group(1) == var for mm in _STATE_VAR_RE.finditer(body)):
            owners.add(cname)
    if var in file_level_state_vars(source):
        owners.add(None)
    return owners


def scan_file(path: Path) -> SolFile:
    source = path.read_text()
    clean = _strip_comments_and_strings(source)
    f = SolFile(path=path)
    f.contracts = [m.group(3) for m in _DECL_RE.finditer(clean)]
    f.functions = {m.group(1): [] for m in _FUNC_RE.finditer(clean)}
    f.modifiers = set(_MOD_RE.findall(clean))
    f.events = {m.group(1) for m in _EVENT_RE.finditer(clean)}
    f.errors = {m.group(1) for m in _ERROR_RE.finditer(clean)}
    f.structs = set(_STRUCT_RE.findall(clean))
    f.enums = set(_ENUM_RE.findall(clean))
    f.user_types = {m.group(1) for m in _UDVT_RE.finditer(clean)}
    for m in _FUNC_RE.finditer(clean):
        name, sig = m.group(1), m.group(2)
        f.functions.setdefault(name, [])
        f.params |= _scan_params(sig)
    f.locals = {m.group(1) for m in _LOCAL_DECL_RE.finditer(clean)}
    # State variables: declaration statements inside contracts, approximated by
    # "type ... name (;|=)" lines that are not function-local (already covered
    # by params) and not keywords. This is intentionally tolerant.
    for m in _STATE_VAR_RE.finditer(clean):
        f.state_vars.add(m.group(1))
    return f


def scan_src(src: Path) -> SolidityIndex:
    """Scan a src directory or a single .sol file into an identifier index."""
    src = Path(src)
    files: list[Path] = []
    if src.is_dir():
        files = sorted(src.glob('**/*.sol'))
    elif src.is_file() and src.suffix == '.sol':
        files = [src]
    if not files:
        raise FileNotFoundError(f'no .sol files under {src}')
    index = SolidityIndex()
    for path in files:
        index.files[path] = scan_file(path)
    return index


def expr_identifiers(expr: str) -> list[str]:
    """Return every identifier token in a binding ``solidity_expr``."""
    return re.findall(r'(?<![0-9])' + IDENT, expr)


def base_identifiers(expr: str) -> set[str]:
    """Root identifiers only.

    An identifier is treated as a non-root member/index/call argument when it is
    immediately preceded by ``.``, ``[``, ``,``, or by ``(`` that itself follows
    an identifier (a function call). Grouping parentheses do not hide a root.
    """
    roots: set[str] = set()
    for m in re.finditer(r'(?<![0-9])' + IDENT, expr):
        start = m.start()
        prefix = expr[:start]
        prev = prefix.rstrip()
        if not prev:
            roots.add(m.group(0))
            continue
        ch = prev[-1]
        if ch in '.[,':
            continue
        if ch == '(':
            # ch index in expr is len(prev)-1; the call check is the char
            # immediately before it.
            before_paren = expr[len(prev) - 2] if len(prev) >= 2 else ''
            if before_paren and (before_paren.isalnum() or before_paren in '_$'):
                continue
        roots.add(m.group(0))
    return roots

def is_snapshot_identifier(name: str) -> bool:
    return name.startswith('stage3_')
