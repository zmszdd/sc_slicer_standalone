"""Build original/patched Foundry projects for one case.

Two patching paths:
- M1 reference: if ``case/patched/`` exists it is used verbatim.
- M4 injection: otherwise ``binding.json`` may carry a ``patch`` spec; the
  pipeline injects P/I assertions into the original source using ``lib.codegen``.

The injection plan supports multiple functions and multiple files. Each function
may carry its own ``file`` / ``contract`` and falls back to the top-level
``patch.file`` / ``patch.contract``. Contract scoping disambiguates same-named
functions in different contracts.
"""
from __future__ import annotations

import re
import shutil
from pathlib import Path

from lib.codegen import expr_to_solidity
from lib.spec_loader import SpecError

DEFAULT_FOUNDRY_TOML = '[profile.default]\nsrc = "src"\ntest = "test"\nout = "out"\n'

IDENT_RE = r'[A-Za-z_$][A-Za-z0-9_$]*'

_KIND_TYPES = {
    'numeric_value': 'uint256',
    'address_value': 'address',
    'boolean_predicate': 'bool',
}

_STOP_RE = re.compile(r'\bstop\s*\(')
_STOP_CALL_RE = re.compile(r'\bstop\s*\(\s*\)')
_SELF_DESTRUCT_RE = re.compile(r'\bselfdestruct\s*\(')
_HALT_OPCODE_RE = re.compile(r'\b(?:stop|selfdestruct)\s*\(')

# Assembly-valid replacement for ``stop()``: revert with Error("stage3:halt").
# Mirrors the pattern already used by the Forte slice for its negative-sign
# revert, so the forge failure reason decodes to ``stage3:halt``.
_HALT_MARKER = (
    'mstore(0x00, 0x08c379a000000000000000000000000000000000000000000000000000000000)\n'
    '        mstore(0x04, 0x20)\n'
    '        mstore(0x24, 11)\n'
    '        mstore(0x44, "stage3:halt")\n'
    '        revert(0x00, 0x64)')


def _strip_block_comments_and_strings(text: str) -> str:
    """Blank comments/strings with *equal-length* spaces so offsets stay aligned."""
    out = []
    i = 0
    n = len(text)
    while i < n:
        if text.startswith('//', i):
            j = text.find('\n', i)
            if j != -1:
                out.append(' ' * (j - i) + '\n')
                i = j + 1
            else:
                out.append(' ' * (n - i))
                i = n
            continue
        if text.startswith('/*', i):
            j = text.find('*/', i + 2)
            out.append(' ' * (j - i + 2 if j != -1 else n - i))
            i = j + 2 if j != -1 else n
            continue
        ch = text[i]
        if ch in ('"', "'"):
            q = ch
            j = i + 1
            while j < n and text[j] != q:
                j += 1
            out.append(' ' * (j - i + 1))
            i = j + 1
            continue
        out.append(ch)
        i += 1
    return ''.join(out)


def _strip_comments_preserve_strings(text: str) -> str:
    """Remove Solidity comments while preserving string literal contents.

    Codegen for a high-level revert witness re-emits the original argument
    list. A trailing ``// ...`` inside that list would otherwise comment out
    the synthetic ``) {`` added by the try/catch wrapper.
    """
    out = []
    i = 0
    n = len(text)
    while i < n:
        if text.startswith('//', i):
            j = text.find('\n', i)
            if j == -1:
                break
            out.append('\n')
            i = j + 1
            continue
        if text.startswith('/*', i):
            j = text.find('*/', i + 2)
            i = j + 2 if j != -1 else n
            continue
        ch = text[i]
        if ch in ('"', "'"):
            quote = ch
            out.append(ch)
            i += 1
            while i < n:
                out.append(text[i])
                if text[i] == '\\' and i + 1 < n:
                    out.append(text[i + 1])
                    i += 2
                    continue
                if text[i] == quote:
                    i += 1
                    break
                i += 1
            continue
        out.append(ch)
        i += 1
    return ''.join(out)


def _copy_tree(src: Path, dst: Path):
    if not src.is_dir():
        raise SpecError(f'missing directory: {src}')
    shutil.copytree(src, dst, dirs_exist_ok=True)


def _copy_optional(src: Path, dst: Path):
    if src.is_dir():
        shutil.copytree(src, dst, dirs_exist_ok=True)
    elif src.is_file():
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)


def _matching_brace(source: str, open_idx: int) -> int:
    """Return the index of the ``}`` matching the ``{`` at ``open_idx``.

    Skips ``//`` and ``/* */`` comments and honours string escapes so that
    braces inside comments/strings do not unbalance the scan.
    """
    depth = 0
    in_string = None
    i = open_idx
    n = len(source)
    while i < n:
        ch = source[i]
        nxt = source[i + 1] if i + 1 < n else ''
        if in_string:
            if ch == '\\':
                i += 2
                continue
            if ch == in_string:
                in_string = None
            i += 1
            continue
        if ch == '"' or ch == "'":
            in_string = ch
            i += 1
            continue
        if ch == '/' and nxt == '/':
            j = source.find('\n', i)
            i = j if j != -1 else n
            continue
        if ch == '/' and nxt == '*':
            j = source.find('*/', i + 2)
            i = j + 2 if j != -1 else n
            continue
        if ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                return i
        i += 1
    raise SpecError('unbalanced braces in source')


_CONTRACT_KIND = r'(?:abstract\s+contract|contract|library)'


def _contract_region(source: str, contract: str) -> tuple[int, int]:
    marker = re.search(r'\b' + _CONTRACT_KIND + r'\s+'
                       + re.escape(contract) + r'\b', source)
    if not marker:
        raise SpecError(f'contract/library not found: {contract}')
    open_idx = source.find('{', marker.end())
    if open_idx < 0:
        raise SpecError(f'contract {contract} has no body')
    return open_idx, _matching_brace(source, open_idx)


def _function_body(source: str, name: str, contract: str | None = None) -> tuple[int, int]:
    """Return (open_brace_index, close_brace_index) for one function body."""
    region_start, region_end = (0, len(source))
    if contract:
        region_start, region_end = _contract_region(source, contract)
    region = source[region_start:region_end]
    pattern = r'\bfunction\s+' + re.escape(name) + r'\s*\('
    matches = list(re.finditer(pattern, region))
    if not matches:
        where = f' in contract {contract}' if contract else ''
        raise SpecError(f'function {name} not found{where}')
    if len(matches) != 1:
        matches = _disambiguate_overloads(source, region, name, matches, contract)
    marker = matches[0]
    open_idx = region_start + marker.end()
    # skip whitespace between the parameter list and the body brace
    brace_idx = source.find('{', open_idx)
    if brace_idx < 0 or brace_idx >= region_end:
        where = f' in contract {contract}' if contract else ''
        raise SpecError(f'function {name} has no body{where}')
    return brace_idx, _matching_brace(source, brace_idx)


def _matching_paren(text: str, open_idx: int) -> int:
    """Return the index of the ``)`` matching the ``(`` at ``open_idx``."""
    depth = 0
    for i in range(open_idx, len(text)):
        if text[i] == '(':
            depth += 1
        elif text[i] == ')':
            depth -= 1
            if depth == 0:
                return i
    raise SpecError('unbalanced parentheses in function signature')


def _arity_of_params(params: str) -> int:
    """Count top-level commas in a parameter/argument list; empty list -> 0."""
    params = params.strip()
    if not params:
        return 0
    depth = 0
    commas = 0
    for ch in params:
        if ch == '(':
            depth += 1
        elif ch == ')':
            depth -= 1
        elif ch == ',' and depth == 0:
            commas += 1
    return commas + 1


def _match_arity(region: str, match) -> int:
    open_idx = match.end() - 1
    params = region[match.end():_matching_paren(region, open_idx)]
    return _arity_of_params(params)


def _call_site_arities(source: str, name: str) -> list[int]:
    """Arity of every non-definition call site of ``name`` in ``source``."""
    arities: list[int] = []
    for match in re.finditer(r'\b' + re.escape(name) + r'\s*\(', source):
        prefix = source[:match.start()].rstrip()
        if prefix.endswith('function'):
            continue
        open_idx = match.end() - 1
        arities.append(_arity_of_params(
            source[match.end():_matching_paren(source, open_idx)]))
    return arities


def _match_line(region: str, match) -> str:
    start = region.rfind('\n', 0, match.start()) + 1
    end = region.find('\n', match.start())
    if end < 0:
        end = len(region)
    return region[start:end]


def _has_function_body(region: str, match) -> bool:
    """True when a function match is a concrete definition, not a declaration."""
    open_idx = match.end() - 1
    close_idx = _matching_paren(region, open_idx)
    tail = region[close_idx + 1:close_idx + 1200]
    body = tail.find('{')
    semicolon = tail.find(';')
    if body < 0:
        return False
    return semicolon < 0 or body < semicolon


def _disambiguate_overloads(source: str, region: str, name: str, matches: list,
                            contract: str | None) -> list:
    """Pick one same-name function by arity + call-site evidence.

    A contract may legitimately overload a function (e.g. an ERC4626
    ``redeem(uint256,address,address)`` beside a one-argument
    ``redeem(uint256)``). The binding names the function without a signature,
    so the bare-name lookup is ambiguous. The PoC test's own call sites are
    the ground truth for which overload the invariant constrains, so prefer
    the arity the source actually calls. When call-site evidence is absent or
    tied, prefer the most parameterised definition, then the concrete
    ``override`` definition, then the last match.
    """
    arities = [_match_arity(region, m) for m in matches]
    distinct = sorted(set(arities))
    where = f' in contract {contract}' if contract else ''
    if len(distinct) == 1:
        concrete = [match for match in matches
                    if _has_function_body(region, match)]
        if concrete and len(concrete) < len(matches):
            return concrete[-1:]
        signatures = [
            'function ' + name + '(' +
            region[m.end():_matching_paren(region, m.end() - 1)] + ')'
            for m in matches]
        raise SpecError(
            f'function {name} is ambiguous (found {len(matches)} matches '
            f'with the same arity){where}: ' + '; '.join(signatures) +
            '; specify patch.contract or a per-function contract, or a unique '
            'function name')
    call_arities = _call_site_arities(source, name)
    scored = sorted(distinct,
                    key=lambda arity: (-call_arities.count(arity), -arity))
    chosen = scored[0]
    if (len(scored) > 1
            and call_arities.count(scored[0]) == call_arities.count(scored[1])):
        chosen = max(distinct)
    selected = [m for m, arity in zip(matches, arities) if arity == chosen]
    if len(selected) == 1:
        return selected
    override = [m for m in selected if 'override' in _match_line(region, m)]
    if override:
        return override[-1:]
    return selected[-1:]


def function_has_halt(source: str, name: str,
                      contract: str | None = None) -> bool:
    """True when a target function body contains an execution-terminating
    opcode (``stop()`` / ``selfdestruct``).

    These opcodes halt the current execution context successfully instead of
    returning, so an ``assert(!P || I)`` injected after the transition is
    unreachable: forge still reports the PoC test as ``Success`` and the
    violation is misclassified as ``violation_not_reproduced`` (the TP-1 false
    negative). Such claims need a halt-aware witness (low-level call +
    returndata check) rather than assert-after-transition.
    """
    try:
        open_idx, close_idx = _function_body(source, name, contract)
    except SpecError:
        return False
    body = _strip_block_comments_and_strings(source[open_idx + 1:close_idx])
    return bool(_HALT_OPCODE_RE.search(body))


def function_has_stop(source: str, name: str,
                      contract: str | None = None) -> bool:
    """True when a target function body contains ``stop()`` (the opcode that
    halts the current execution context successfully)."""
    try:
        open_idx, close_idx = _function_body(source, name, contract)
    except SpecError:
        return False
    body = _strip_block_comments_and_strings(source[open_idx + 1:close_idx])
    return bool(_STOP_RE.search(body))


def function_has_selfdestruct(source: str, name: str,
                              contract: str | None = None) -> bool:
    """True when a target function body contains ``selfdestruct``.

    ``selfdestruct`` halts the current execution context and cannot be turned
    into a revert via the ``stop()`` marker rewrite, so these targets need a
    halt-aware witness instead.
    """
    try:
        open_idx, close_idx = _function_body(source, name, contract)
    except SpecError:
        return False
    body = _strip_block_comments_and_strings(source[open_idx + 1:close_idx])
    return bool(_SELF_DESTRUCT_RE.search(body))


def _rewrite_stop_globally(source: str) -> str:
    """Rewrite every ``stop()`` outside comments/strings into an assembly
    marker revert, across the whole patched slice. The halt may live in a
    callee rather than the injection target, so a function-scoped rewrite is
    not enough.
    """
    cleaned = _strip_block_comments_and_strings(source)
    matches = list(_STOP_CALL_RE.finditer(cleaned))
    if not matches:
        return source
    out = source
    for match in reversed(matches):
        out = out[:match.start()] + _HALT_MARKER + out[match.end():]
    return out


def injection_has_halt(case_dir: Path, binding: dict) -> tuple[bool, list[str]]:
    """Scan every injection target in ``binding.patch`` for halt opcodes.

    Returns ``(has_halt, matches)`` where ``matches`` lists the offending
    ``file:function`` targets. A target with no body (for example a function
    whose body cannot be located) is skipped rather than raising.
    """
    patch = binding.get('patch')
    if not isinstance(patch, dict):
        return False, []
    plan = _injection_plan(patch)
    matches: list[str] = []
    for target_file, functions in plan.items():
        target = case_dir / 'src' / target_file
        if not target.is_file():
            continue
        source = target.read_text()
        for name, contract in functions:
            if function_has_halt(source, name, contract):
                matches.append(f'{target_file}:{name}')
    return bool(matches), matches


def injection_selfdestruct_targets(case_dir: Path, binding: dict) -> list[str]:
    """List injection targets whose function body contains ``selfdestruct``."""
    patch = binding.get('patch')
    if not isinstance(patch, dict):
        return []
    plan = _injection_plan(patch)
    matches: list[str] = []
    for target_file, functions in plan.items():
        target = case_dir / 'src' / target_file
        if not target.is_file():
            continue
        source = target.read_text()
        for name, contract in functions:
            if function_has_selfdestruct(source, name, contract):
                matches.append(f'{target_file}:{name}')
    return matches


def _claim(spec: dict, formal: dict, claim_id: str) -> dict:
    for row in formal.get('claims', []):
        if row.get('id') == claim_id:
            return row
    raise SpecError(f'claim {claim_id} not found in formalization.json')


def _expr_symbols(expr) -> set[str]:
    """Collect every ``var`` symbol referenced by an expression AST."""
    if not isinstance(expr, dict):
        return set()
    if 'var' in expr:
        return {expr['var']}
    out: set[str] = set()
    for arg in expr.get('args') or []:
        out |= _expr_symbols(arg)
    return out


def _render_expr(expr, entries: dict, *, allow_unbound: set[str] | None = None) -> str | None:
    if expr is None:
        return None
    referenced = _expr_symbols(expr)
    rendered = {}
    for symbol, entry in entries.items():
        solidity_expr = entry['solidity_expr']
        if str(solidity_expr).strip() == 'UNBOUND':
            # A revert-expected PoC only needs the precondition P; UNBOUND
            # I/V symbols are never rendered by the revert-witness rewrite,
            # so they must not block it. Symbols the expression actually
            # references still fail through expr_to_solidity below.
            if symbol in referenced and symbol not in (allow_unbound or set()):
                raise SpecError(
                    f'symbol {symbol} has solidity_expr=UNBOUND; '
                    'binding must be completed before patch injection')
            continue
        if entry.get('checkpoint') == 'before':
            rendered[symbol] = f'stage3_{symbol}'
        else:
            rendered[symbol] = solidity_expr
    return expr_to_solidity(expr, rendered)


def _entry_prelude(entry: dict) -> list[str]:
    """Deterministic helper statements declared immediately before a snapshot.

    Tuple-returning getters (``pair.getReserves()``, ``oracle.snapshotHistory()``)
    cannot be assigned to a scalar; bindings declare destructuring statements in
    ``solidity_stmts`` and reference the destructured names in ``solidity_expr``.
    """
    raw = entry.get('solidity_stmts') or []
    if isinstance(raw, str):
        raw = [raw]
    return [str(line).rstrip(';') + ';' for line in raw if str(line).strip()]


def local_decl_statements(source: str, function_name: str,
                           identifiers: set[str],
                           contract: str | None = None) -> dict[str, str]:
    """Map each identifier to the local-declaration statement that declares it.

    A ``before`` snapshot is injected at function entry; an expression that
    reads a variable declared later in the function body fails to compile with
    ``Undeclared identifier``.  This helper locates the declaring statement for
    each offending identifier so the caller can set ``snapshot_after`` and move
    the snapshot assignment past the declaration instead of neutralizing the
    binding (which silently downgrades the claim to ``partial_binding``).
    """
    try:
        open_idx, close_idx = _function_body(source, function_name, contract)
    except SpecError:
        return {}
    body_start = open_idx + 1
    body = source[body_start:close_idx]
    decl_re = re.compile(
        rf'(?m)^[ \t]+(?:mapping\([^)]*\)|[A-Za-z_$][A-Za-z0-9_$]*'
        rf'(?:\s*\[[^\]]*\])?)(?:\s+(?:storage|memory|calldata))?\s+'
        rf'([A-Za-z_$][A-Za-z0-9_$]*)\s*(?==|;)')
    found: dict[str, str] = {}
    for match in decl_re.finditer(body):
        name = match.group(1)
        if name in identifiers and name not in found:
            end = _statement_end(source, body_start + match.end())
            if end is not None:
                found[name] = source[body_start + match.start():end].strip()
    return found


def _statement_end(source: str, start: int) -> int | None:
    """Return index just after the semicolon ending a Solidity statement."""
    paren = bracket = brace = 0
    quote = None
    i = start
    while i < len(source):
        if quote:
            if source[i] == '\\':
                i += 2
                continue
            if source[i] == quote:
                quote = None
            i += 1
            continue
        if source.startswith('//', i):
            j = source.find('\n', i)
            i = len(source) if j < 0 else j + 1
            continue
        if source.startswith('/*', i):
            j = source.find('*/', i + 2)
            if j < 0:
                return None
            i = j + 2
            continue
        ch = source[i]
        if ch in ('"', "'"):
            quote = ch
        elif ch == '(':
            paren += 1
        elif ch == ')':
            paren -= 1
        elif ch == '[':
            bracket += 1
        elif ch == ']':
            bracket -= 1
        elif ch == '{':
            brace += 1
        elif ch == '}':
            brace -= 1
        elif ch == ';' and paren == 0 and bracket == 0 and brace == 0:
            return i + 1
        i += 1
    return None


_PARAM_NAME_RE = re.compile(
    rf'(?:(?:address|bool|string|bytes[0-9]*|u?int[0-9]*|'
    rf'[A-Za-z_$][A-Za-z0-9_$.]*)(?:\s*\[[^\]]*\])?'
    rf'(?:\s+(?:memory|storage|calldata))?\s+)?'
    rf'({IDENT_RE})\s*$')


def _function_param_names(source: str, name: str,
                          contract: str | None = None) -> set[str]:
    try:
        open_idx, _ = _function_body(source, name, contract)
    except SpecError:
        return set()
    region_start = 0
    if contract:
        try:
            region_start, _ = _contract_region(source, contract)
        except SpecError:
            return set()
    marker = None
    for candidate in re.finditer(
            r'\bfunction\s+' + re.escape(name) + r'\s*\(',
            source[region_start:open_idx]):
        marker = candidate
    if marker is None:
        return set()
    open_paren = region_start + marker.end() - 1
    try:
        close_paren = _matching_paren(source, open_paren)
    except SpecError:
        return set()
    params = source[open_paren + 1:close_paren]
    names = set()
    for item in _split_top_level(params):
        match = _PARAM_NAME_RE.search(item.strip())
        if match:
            names.add(match.group(1))
    return names


def _split_top_level(text: str) -> list[str]:
    parts, start, depth = [], 0, 0
    for i, ch in enumerate(text):
        if ch in '([{':
            depth += 1
        elif ch in ')]}':
            depth -= 1
        elif ch == ',' and depth == 0:
            parts.append(text[start:i])
            start = i + 1
    parts.append(text[start:])
    return parts


def _function_local_names(source: str, name: str,
                          contract: str | None = None) -> set[str]:
    try:
        open_idx, close_idx = _function_body(source, name, contract)
    except SpecError:
        return set()
    body = source[open_idx + 1:close_idx]
    pattern = re.compile(
        rf'(?m)^[ \t]+(?:mapping\([^)]*\)|{IDENT_RE}(?:\s*\[[^\]]*\])?)'
        rf'(?:\s+(?:storage|memory|calldata))?\s+({IDENT_RE})\s*(?==|;)')
    return {match.group(1) for match in pattern.finditer(body)}


def _binding_identifiers(binding: dict) -> set[str]:
    found = set()
    for entry in (binding.get('bindings') or {}).values():
        if not isinstance(entry, dict):
            continue
        text = str(entry.get('solidity_expr') or '')
        stmts = entry.get('solidity_stmts') or []
        if isinstance(stmts, str):
            stmts = [stmts]
        text += ' ' + ' '.join(str(row) for row in stmts)
        found |= set(re.findall(IDENT_RE, text))
    return found


def relocate_injection_to_test(binding: dict, *, source: str | None = None,
                               test_source: str | None = None) -> dict | None:
    """Return a binding whose injection point is moved to the PoC test function.

    ``Undeclared identifier`` compile failures usually mean the binding's
    snapshot expressions reference locals of the PoC test (or state visible
    only in the harness contract) while ``patch.functions[0]`` points at a
    business function.  The probe already names the real exploit test; moving
    the injection there puts those identifiers back in scope and the
    before/after snapshot semantics are still respected (snapshots at test
    entry, assertion at test tail).  Returns ``None`` when no such test is
    available or the injection point already is the test function.
    """
    patch = binding.get('patch')
    probe = binding.get('probe')
    if not isinstance(patch, dict) or not isinstance(probe, dict):
        return None
    functions = patch.get('functions') or []
    if not functions:
        return None
    target = functions[0]
    target_name = (target.get('name') if isinstance(target, dict) else target)
    test_name = probe.get('exploit_test')
    if not isinstance(test_name, str) or not test_name:
        return None
    if target_name == test_name:
        return None
    if source is not None and test_source is not None:
        target_contract = (target.get('contract')
                           if isinstance(target, dict) else None)
        target_contract = target_contract or patch.get('contract')
        test_contract = probe.get('contract')
        referenced = _binding_identifiers(binding)
        business_scope = (_function_param_names(
            source, str(target_name), target_contract)
            | _function_local_names(source, str(target_name), target_contract))
        test_scope = (_function_param_names(
            test_source, test_name, test_contract)
            | _function_local_names(test_source, test_name, test_contract))
        escaped = sorted((referenced & business_scope) - test_scope)
        if escaped:
            return None
    import copy
    out = copy.deepcopy(binding)
    new_functions = copy.deepcopy(functions)
    new_functions[0] = {
        'name': test_name,
        'file': (target.get('file') if isinstance(target, dict)
                 else patch.get('file')),
    }
    if probe.get('contract'):
        new_functions[0]['contract'] = probe['contract']
    out['patch']['functions'] = new_functions
    if probe.get('contract'):
        out['patch']['contract'] = probe['contract']
    return out


def relocate_before_snapshots(binding: dict, source: str) -> dict:
    """Add ``snapshot_after`` anchors to before-snapshot bindings whose
    expressions read PoC-local variables declared later in the injection
    function.  Returns the binding and the per-symbol anchor map."""
    patch = binding.get('patch')
    anchors = {}
    if not isinstance(patch, dict):
        return binding, anchors
    functions = patch.get('functions') or []
    if not functions:
        return binding, anchors
    fn = functions[0]
    fn_name = (fn.get('name') if isinstance(fn, dict) else fn)
    fn_contract = ((fn.get('contract') if isinstance(fn, dict) else None)
                   or patch.get('contract'))
    if not isinstance(fn_name, str) or not fn_name:
        return binding, anchors
    for name, entry in (binding.get('bindings') or {}).items():
        if not isinstance(entry, dict):
            continue
        if entry.get('checkpoint') != 'before':
            continue
        if str(entry.get('snapshot_after') or '').strip():
            continue
        expr = str(entry.get('solidity_expr') or '')
        stmts = entry.get('solidity_stmts') or []
        if isinstance(stmts, str):
            stmts = [stmts]
        scan_text = expr + ' ' + ' '.join(str(line) for line in stmts)
        roots = {r for r in re.findall(r'[A-Za-z_$][A-Za-z0-9_$]*', scan_text)
                 if r not in ('true', 'false')}
        decls = local_decl_statements(source, fn_name, roots,
                                      contract=fn_contract)
        if not decls:
            continue
        try:
            open_idx, close_idx = _function_body(source, fn_name, fn_contract)
        except SpecError:
            continue
        function_body = source[open_idx + 1:close_idx]
        # Anchor at the last-declared referenced local so every root is in scope.
        order = []
        for ident, stmt in decls.items():
            # Compare positions inside this function, not their first global
            # occurrence. Flattened contracts often repeat an identical local
            # declaration in several functions; a global lookup can select a
            # declaration in an earlier function and leave the real target
            # local out of scope at the anchor.
            idx = function_body.find(stmt)
            order.append((idx, ident, stmt))
        if not order or min(item[0] for item in order) < 0:
            continue
        anchor = max(order)[2]
        entry['snapshot_after'] = anchor
        anchors[name] = anchor
    return binding, anchors


def _snapshot_decls(entries: dict, *, allow_unbound: bool = False) -> tuple[list[str], list[tuple[str, str]]]:
    """Split ``before`` snapshots into entry-level and statement-anchored.

    Returns ``(head_decls, anchored_decls)``. ``anchored_decls`` is a list of
    ``(anchor_text, assign_block)`` for symbols that carry a ``snapshot_after``
    statement anchor; the snapshot value is assigned immediately after that
    statement instead of at the function entry. This supports mid-function
    checkpoints (for example ``before attacker init``) that the entry/tail
    model cannot express.

    Anchored symbols are *declared* at the function head (uninitialized) and
    *assigned* at the anchor. Solidity scopes a declaration to its enclosing
    block, so declaring the variable at the anchor point would make it
    invisible to the tail assertion when the anchor sits inside a loop or
    ``if`` body.
    """
    head: list[str] = []
    anchored: list[tuple[str, str]] = []
    for symbol, entry in entries.items():
        if entry.get('checkpoint') != 'before':
            continue
        solidity_expr = entry['solidity_expr']
        if str(solidity_expr).strip() == 'UNBOUND':
            if allow_unbound:
                continue
            raise SpecError(
                f'symbol {symbol} has solidity_expr=UNBOUND; '
                'binding must be completed before snapshot injection')
        type_name = str(entry.get('solidity_type')
                        or _KIND_TYPES.get(entry['kind'], 'uint256'))
        prelude = [f'        {line}' for line in _entry_prelude(entry)]
        anchor = str(entry.get('snapshot_after') or '').strip()
        if anchor:
            head.append(f'        {type_name} stage3_{symbol};')
            block = '\n'.join(prelude + [f'        stage3_{symbol} = {solidity_expr};'])
            anchored.append((anchor, block))
        else:
            head.extend(prelude)
            head.append(f'        {type_name} stage3_{symbol} = {solidity_expr};')
    return head, anchored

def _assert_tail(spec: dict, formal: dict, claim_id: str, entries: dict,
                 probe_kind: str = 'invariant',
                 guard_precondition: bool = True) -> list[str]:
    claim = _claim(spec, formal, claim_id)
    properties = claim.get('properties', {})
    pre_expr = properties.get('preconditions', {}).get('expression')
    if probe_kind == 'effect':
        target_expr = properties.get('effects', {}).get('expression')
        target_name = 'V'
    elif probe_kind == 'negative':
        target_expr = properties.get('effects', {}).get('expression')
        target_name = 'not_V'
    else:
        target_expr = properties.get('safety', {}).get('expression')
        target_name = 'I'
    if target_expr is None:
        raise SpecError(f'claim has no {target_name} expression to inject')
    target_sol = _render_expr(target_expr, entries)
    if probe_kind == 'negative':
        target_sol = f'!({target_sol})'
    pre_sol = _render_expr(pre_expr, entries) if pre_expr is not None else None
    # P scopes the target; it is not enforced as a standalone requirement.
    # A safe path where P is false must pass the contract unchanged.
    post_assert = target_sol if pre_sol is None else f'!({pre_sol}) || ({target_sol})'
    lines = []
    if pre_sol is not None and guard_precondition:
        # Only guard when the before-snapshot carries an explicit
        # ``snapshot_after`` mid-function checkpoint. For entry-level
        # snapshots on victim-contract functions the same function is often
        # called legitimately during PoC setup with P false; a hard revert
        # there would block the exploit before it runs. The plain
        # ``assert(!P || target)`` is still the correct guard for those paths.
        lines.append(
            f'        if (!({pre_sol})) revert("stage3:precondition_unwitnessed");')
    marker = f'stage3:{target_name}'
    lines.append(f'        require({post_assert}, "{marker}");')
    return lines


def _injection_plan(patch: dict) -> dict[str, list[tuple[str, str | None]]]:
    """Group the patch spec by target file, preserving order.

    Returns ``{file: [(function_name, contract_or_None), ...]}``. The first
    file determines injection order; functions in the same file are injected
    in the order given.
    """
    if not isinstance(patch, dict):
        raise SpecError('binding.patch must be an object')
    default_file = patch.get('file')
    default_contract = patch.get('contract')
    functions = patch.get('functions', [])
    if not isinstance(functions, list) or not functions:
        raise SpecError('patch.functions must be a non-empty list')
    plan: dict[str, list[tuple[str, str | None]]] = {}
    for fn in functions:
        if isinstance(fn, dict):
            name = fn.get('name')
            file = fn.get('file') or default_file
            contract = fn.get('contract') or default_contract
        else:
            name = fn
            file = default_file
            contract = default_contract
        if not isinstance(name, str) or not name:
            raise SpecError('patch function name is required')
        if not isinstance(file, str) or not file:
            raise SpecError('patch.file is required')
        plan.setdefault(file, []).append((name, contract))
    return plan


def _non_before_preludes(entries: dict) -> list[str]:
    """Prelude statements for non-before symbols rendered inline in the tail.

    ``input``/``after`` symbols are not snapshotted; their ``solidity_stmts``
    (for example tuple destructuring of a getter used inside the assertion) must
    still be emitted before the tail assertion so the rewritten
    ``solidity_expr`` can reference the destructured locals.
    """
    lines: list[str] = []
    for entry in entries.values():
        if not isinstance(entry, dict):
            continue
        if entry.get('checkpoint') == 'before':
            continue
        for line in _entry_prelude(entry):
            lines.append(f'        {line}')
    return lines


def _inject_into_source(source: str, spec: dict, formal: dict, claim_id: str,
                        entries: dict, functions: list[tuple[str, str | None]],
                        probe_kind: str = 'invariant') -> str:
    head, anchored = _snapshot_decls(entries)
    guard_precondition = any(
        entry.get('checkpoint') == 'before' and str(entry.get('snapshot_after') or '').strip()
        for entry in entries.values() if isinstance(entry, dict))
    tail = _assert_tail(spec, formal, claim_id, entries, probe_kind=probe_kind,
                        guard_precondition=guard_precondition)
    injection_head = ('\n' + '\n'.join(head) + '\n') if head else ''
    injection_tail = ('\n' + '\n'.join(tail) + '\n    ') if tail else ''
    non_before = _non_before_preludes(entries)
    injection_prelude = ('\n' + '\n'.join(non_before) + '\n') if non_before else ''
    for name, contract in functions:
        open_idx, close_idx = _function_body(source, name, contract)
        body = source[open_idx + 1:close_idx]
        # "before" snapshots must capture the function-entry state, before any
        # executable statement. Injecting after the last declaration is wrong
        # when a PoC declares variables after the exploit (e.g. walletBefore/
        # attackerAfter): the snapshot would sample the post-exploit state and
        # make the precondition false, turning assert(!P || I) vacuous.
        body = injection_head + body
        for anchor, decl in anchored:
            body = _insert_after_statement(body, anchor, decl)
        body = body + injection_prelude + injection_tail
        source = source[:open_idx + 1] + body + source[close_idx:]
    return source


def _insert_after_statement(body: str, anchor: str, decl: str) -> str:
    """Insert ``decl`` on its own line immediately after the first statement
    containing ``anchor``. Raises ``SpecError`` when the anchor is absent so a
    stale binding fails fast instead of silently sampling at the wrong point.

    ``anchor`` is the full statement text returned by
    ``local_decl_statements``, which can span multiple lines (for example a
    long constructor/helper call).  Insert after the end of the whole
    statement, not after its first newline, otherwise the anchor is split and
    subsequent anchored injections can no longer find it.
    """
    index = body.find(anchor)
    if index < 0:
        raise SpecError(f'snapshot anchor not found in function body: {anchor!r}')
    line_end = index + len(anchor)
    return body[:line_end] + '\n' + decl + body[line_end:]


_PRECONDITION_UNWITNESSED_MARKER = 'stage3:precondition_unwitnessed'


def _precondition_sol(spec: dict, formal: dict, claim_id: str,
                      entries: dict) -> str | None:
    claim = _claim(spec, formal, claim_id)
    pre_expr = claim.get('properties', {}).get('preconditions', {}).get('expression')
    if pre_expr is None:
        return None
    return _render_expr(pre_expr, entries)


def _test_function_body(source: str, name: str,
                        contract: str | None = None) -> tuple[int, int]:
    return _function_body(source, name, contract)


def _call_selector_expr(source: str, target_expr: str, method: str,
                        args: str) -> str:
    """Return the calldata expression for the low-level rewrite.

    Non-overloaded methods use ``target.method.selector``; overloaded methods
    resolve by argument arity and use ``abi.encodeWithSignature`` because
    ``.selector`` is ambiguous for overloads. Raises SpecError when the
    overload cannot be resolved unambiguously.
    """
    from lib.rebind import parse_source_signatures
    sigs = parse_source_signatures(source)
    overloads = sigs.get('functions', {}).get(method) or []
    if len(overloads) <= 1:
        return f'abi.encodeWithSelector({target_expr}.{method}.selector, {args})'
    depth = 0
    commas = 0
    for ch in args:
        if ch == '(':
            depth += 1
        elif ch == ')':
            depth -= 1
        elif ch == ',' and depth == 0:
            commas += 1
    arg_count = commas + 1 if args.strip() else 0
    matches = [o for o in overloads if o.get('arity') == arg_count]
    if len(matches) != 1:
        raise SpecError(
            f'overloaded method {method} has no unique arity-{arg_count} '
            f'overload ({len(matches)} matches)')
    param_types = matches[0].get('param_types') or []
    if len(param_types) != arg_count:
        raise SpecError(f'could not recover param types for {method}')
    sig = f'{method}({",".join(param_types)})'
    return f'abi.encodeWithSignature("{sig}", {args})'


def _find_revert_exploit_call(body: str) -> tuple[int, int, dict] | None:
    """Return ``(start, end, call)`` for the direct call that follows the last
    ``vm.expectRevert`` statement in a revert-expected PoC test body.

    Comments/strings are blanked (equal-length) so commented-out
    ``vm.expectRevert`` directives never fake a revert-expected shape. The
    matcher accepts both high-level ``target.method(...)`` calls and low-level
    ``address(target).call(...)`` statements, using balanced-paren scanning so
    nested ``abi.encodeWithSignature(...)`` calldata is never mistaken for the
    exploit call itself.
    """
    cleaned = _strip_block_comments_and_strings(body)
    expect_matches = list(re.finditer(r'vm\.expectRevert\s*\([^;]*\);', cleaned))
    if not expect_matches:
        return None
    after = expect_matches[-1].end()
    target_re = re.compile(
        r'(?P<target>'
        r'(?:address\s*\([^()]*\)|payable\s*\([^()]*\)|'
        r'[A-Za-z_$][A-Za-z0-9_$]*\s*\([^()]*\)|'
        r'[A-Za-z_$][A-Za-z0-9_$]*)'
        r'(?:\.[A-Za-z_$][A-Za-z0-9_$]*)*'
        r')'
        r'\s*\.\s*(?P<method>[A-Za-z_$][A-Za-z0-9_$]*)'
        r'\s*(?P<opts>\{[^}]*\})?\s*\(')
    for match in target_re.finditer(cleaned, after):
        target = match.group('target')
        if target.split('.', 1)[0].rstrip().lower() in ('vm', 'console', 'cheats'):
            continue
        method = match.group('method')
        if method not in ('call', 'delegatecall', 'staticcall'):
            prefix = cleaned[:match.start()]
            last_delim = max(prefix.rfind(';'), prefix.rfind('{'), prefix.rfind('}'))
            segment = prefix[last_delim + 1:]
            if re.search(r'=\s*$', segment) and method[:1].isupper():
                continue
        open_idx = match.end() - 1
        close_idx = _matching_paren(cleaned, open_idx)
        tail = close_idx + 1
        while tail < len(cleaned) and cleaned[tail].isspace():
            tail += 1
        if tail >= len(cleaned) or cleaned[tail] != ';':
            continue
        args = body[open_idx + 1:close_idx].strip()
        return match.start(), tail + 1, {
            'target': match.group('target'),
            'method': method,
            'opts': match.group('opts'),
            'args': args,
        }
    return None


def _before_snapshot_exprs(entries: dict) -> list[str]:
    return [str(e.get('solidity_expr') or '').strip()
            for e in entries.values()
            if isinstance(e, dict) and e.get('checkpoint') == 'before']


def _precondition_trivially_true(entries: dict) -> bool:
    exprs = _before_snapshot_exprs(entries)
    return not exprs or all(expr == 'true' for expr in exprs)


def _business_called_in_setup(test_body: str, method: str) -> bool:
    if not method:
        return False
    expect_matches = list(re.finditer(r'vm\.expectRevert\s*\([^;]*\);', test_body))
    if not expect_matches:
        return True
    limit = expect_matches[-1].start()
    pattern = re.compile(rf'(?<![\.A-Za-z0-9_$]){re.escape(method)}\s*\(')
    return bool(pattern.search(test_body[:limit]))


def _revert_witness_check(pre_sol: str | None) -> str:
    if pre_sol is None:
        return '            require(stage3_ok, "stage3:I");'
    cmp = ('keccak256(stage3_ret) == keccak256(abi.encodeWithSignature('
           '"Error(string)", "stage3:precondition_unwitnessed"))')
    return (
        '            if (!stage3_ok) {\n'
        f'                require({cmp}, "stage3:I");\n'
        '            }')


def _inject_precondition_guard(source: str, fn_name: str, contract: str | None,
                               pre_sol: str | None, entries: dict) -> str:
    """Inject before-snapshot declarations plus a forced precondition guard at
    the business function entry so a false P reverts with a distinct marker."""
    if pre_sol is None:
        return source
    head, anchored = _snapshot_decls(entries, allow_unbound=True)
    if anchored:
        return source
    guard = (f'\n        if (!({pre_sol})) revert("{_PRECONDITION_UNWITNESSED_MARKER}");\n')
    injection_head = ('\n' + '\n'.join(head) + '\n') if head else ''
    open_idx, close_idx = _function_body(source, fn_name, contract)
    body = source[open_idx + 1:close_idx]
    body = injection_head + body + guard
    return source[:open_idx + 1] + body + source[close_idx:]


def inject_revert_witness(case_dir: Path, patched_dir: Path, binding: dict,
                          spec: dict, formal: dict) -> None:
    """Build the patched project for a revert-expected PoC.

    A revert-based effect cannot be witnessed by ``assert(!P || I)`` placed
    after the reverting call (the assertion is unreachable).  Instead:

    * when P is trivially true (all before-snapshots are ``true``), any revert
      of the exploit call is a violation of "operation completes";
    * otherwise the business function gets a forced entry-level precondition
      guard reverting with ``stage3:precondition_unwitnessed`` when P is false,
      applied only when the business function is not called during test setup;
    * the PoC test's ``vm.expectRevert`` is removed and its exploit call is
      wrapped in a low-level call capturing ``stage3_ok``/``stage3_ret``;
    * any non-P-false revert then violates the invariant and is reported with
      the ``stage3:I`` marker.
    """
    _copy_tree(case_dir / 'src', patched_dir)
    patch = binding.get('patch')
    probe = binding.get('probe') or {}
    if not isinstance(patch, dict):
        raise SpecError('no binding.patch spec for revert witness')
    target_file = patch.get('file')
    if not isinstance(target_file, str) or not target_file:
        raise SpecError('binding.patch.file is required')
    test_fn = probe.get('exploit_test')
    test_contract = probe.get('contract')
    if not isinstance(test_fn, str) or not test_fn:
        raise SpecError('revert witness requires probe.exploit_test')
    target = patched_dir / target_file
    if not target.is_file():
        raise SpecError(f'patch target not found in src: {target_file}')
    source = target.read_text()
    entries = binding.get('bindings') or {}
    claim_id = binding.get('claim_id')
    # Revert-witness does not enforce P on code: it only flips the PoC's
    # `vm.expectRevert` so original Success / patched Failure is the witness.
    # Rendering P here pulls UNBOUND P-symbols into `_render_expr` and turns
    # otherwise-runnable revert cases into `binding_error`, so leave P unrendered.
    pre_sol = None

    functions = patch.get('functions') or []
    biz_name = None
    biz_contract = patch.get('contract')
    if functions and isinstance(functions[0], dict):
        biz_name = functions[0].get('name')
        biz_contract = functions[0].get('contract') or biz_contract
    elif functions:
        biz_name = functions[0]

    # Revert-expected PoCs witness the revert directly. Injecting a
    # precondition guard into the business function is what previously pulled
    # out-of-scope snapshot expressions (e.g. an interface getter) into the
    # patched project and caused avoidable compile errors. The differential
    # only needs the expectRevert removed: the original test still passes and
    # the patched test fails when the exploit call reverts.
    pre_sol = None

    test_open, test_close = _test_function_body(source, test_fn, test_contract)
    body = source[test_open + 1:test_close]
    call = _find_revert_exploit_call(body)
    if call is None:
        raise SpecError('no exploit call after vm.expectRevert in PoC test')
    start, end, groups = call
    target_expr = groups['target']
    method = groups['method']
    opts = groups['opts'] or ''
    args = _strip_comments_preserve_strings(groups['args']).strip()

    if not _precondition_trivially_true(entries) and pre_sol is not None and             _business_called_in_setup(body, biz_name or method):
        raise SpecError('business function is called during PoC setup; '
                        'entry-level precondition guard would break it')

    if method in ('call', 'delegatecall', 'staticcall'):
        # The PoC already uses a low-level call to assert the revert. Keep that
        # call intact (its calldata is already the full encoded call) and flip
        # the witness: patched code must see the call succeed, otherwise the
        # original revert is still present and the invariant has not been
        # established.
        success_var = None
        prefix = body[:start]
        lhs = re.search(
            r'\(\s*bool\s+([A-Za-z_$][A-Za-z0-9_$]*)\s*,'
            r'\s*(?:bytes\s+[^)]*)?\)\s*=\s*$', prefix)
        if lhs:
            success_var = lhs.group(1)
        if success_var:
            check = f'        require({success_var}, "stage3:I");'
        else:
            # Unusual low-level call spelling without an explicit bool LHS.
            # Replace the call with a capturing low-level call, then apply the
            # standard witness check.
            call_expr = body[start:end].rstrip().rstrip(';').strip()
            low_call = (f'        (bool stage3_ok, bytes memory stage3_ret) = '
                        f'{call_expr};\n'
                        + _revert_witness_check(pre_sol))
            body = body[:start] + low_call + body[end:]
            body = re.sub(r'vm\.expectRevert\s*\([^;]*\);\s*', '', body)
            injected = source[:test_open + 1] + body + source[test_close:]
            injected = _rewrite_stop_globally(injected)
            target.write_text(injected)
            return
        low_call = body[start:end] + '\n' + check
    else:
        prefix = body[:start]
        if re.search(r'=\s*$', prefix):
            # The exploit call is the initializer of a variable assignment
            # (e.g. ``address token = protocol.tokenize(...)``). Keeping that
            # statement intact and removing ``vm.expectRevert`` makes the
            # patched PoC fail exactly when the buggy call still reverts,
            # which is the desired original Success / patched Failure witness.
            body = re.sub(r'vm\.expectRevert\s*\([^;]*\);\s*', '', body)
            injected = source[:test_open + 1] + body + source[test_close:]
            injected = _rewrite_stop_globally(injected)
            target.write_text(injected)
            return
        # High-level external call. Wrap it in Solidity ``try/catch`` instead
        # of rebuilding a low-level call with ``.selector``. The compiler
        # resolves the high-level call (including overloads and struct
        # arguments) natively, which avoids the selector ambiguity that a
        # hand-written ``abi.encodeWithSelector`` cannot recover from source
        # text alone.
        low_call = (
            '        bool stage3_ok;\n'
            '        bytes memory stage3_ret;\n'
            f'        try {target_expr}.{method}{opts}({args}) {{\n'
            '            stage3_ok = true;\n'
            '        } catch (bytes memory _stage3_reason) {\n'
            '            stage3_ret = _stage3_reason;\n'
            '        }\n'
            + _revert_witness_check(pre_sol))
    body = body[:start] + low_call + body[end:]
    body = re.sub(r'vm\.expectRevert\s*\([^;]*\);\s*', '', body)
    injected = source[:test_open + 1] + body + source[test_close:]
    injected = _rewrite_stop_globally(injected)
    target.write_text(injected)


def _is_revert_vulnerability_test(source: str, test_fn: str,
                                  contract: str | None = None) -> bool:
    """Detect stage-2 ``@revert`` markers in the raw PoC test body.

    A revert-based DoS PoC does not always contain an explicit
    ``vm.expectRevert`` (often it is commented out), but stage-2 writes
    ``//@revert`` / ``//@it just revert here`` markers. This shape must be
    routed to a fix patch (original Failure + patched Success), not the
    normal original Success + patched Failure reference-patch direction.
    """
    try:
        open_idx, close_idx = _function_body(source, test_fn, contract)
    except SpecError:
        return False
    body = source[open_idx + 1:close_idx]
    return ('//@revert' in body or '@revert' in body)


def _is_revert_expected_test(source: str, test_fn: str,
                               contract: str | None = None) -> bool:
    try:
        open_idx, close_idx = _function_body(source, test_fn, contract)
    except SpecError:
        return False
    body = _strip_block_comments_and_strings(source[open_idx + 1:close_idx])
    return 'vm.expectRevert' in body


def inject_patched_sources(case_dir: Path, patched_dir: Path, binding: dict,
                           spec: dict, formal: dict,
                           probe_kind: str = 'invariant'):
    if probe_kind == 'invariant':
        probe = binding.get('probe') or {}
        test_fn = probe.get('exploit_test')
        patch = binding.get('patch')
        if isinstance(test_fn, str) and test_fn and isinstance(patch, dict):
            target_file = patch.get('file')
            if isinstance(target_file, str) and target_file:
                src_file = case_dir / 'src' / target_file
                if src_file.is_file():
                    source = src_file.read_text()
                    if _is_revert_expected_test(source, test_fn,
                                                probe.get('contract')):
                        try:
                            inject_revert_witness(case_dir, patched_dir, binding,
                                                  spec, formal)
                            return
                        except SpecError:
                            pass
    _copy_tree(case_dir / 'src', patched_dir)
    patch = binding.get('patch')
    if not isinstance(patch, dict):
        raise SpecError(
            'no case/patched/ reference and no binding.patch spec; '
            'provide one of them')
    plan = _injection_plan(patch)
    for target_file, functions in plan.items():
        target = patched_dir / target_file
        if not target.is_file():
            raise SpecError(f'patch target not found in src: {target_file}')
        source = target.read_text()
        injected = _inject_into_source(
            source, spec, formal, binding['claim_id'], binding['bindings'],
            functions, probe_kind=probe_kind)
        injected = _rewrite_stop_globally(injected)
        target.write_text(injected)




def _normalize_artifact_refs(text: str) -> str:
    """Rewrite file-path artifact references that flattening broke.

    Stage-1 flattening renames every source file to ``Contract.sol``, so
    Foundry can no longer resolve ``vm.getCode("TestUSDC.sol")`` (registered
    under the original file path). The contract name is still a valid artifact
    reference, so ``"TestUSDC.sol"`` becomes ``"TestUSDC"`` and
    ``"contracts/.../Pair.sol"`` becomes ``"Pair"``.
    """
    import re
    pattern = re.compile(
        r'((?:vm\.getCode|deployCodeTo|deployCode)\(")([^"]+\.sol)(")')

    def _repl(match):
        path = match.group(2)
        name = path.rsplit('/', 1)[-1]
        if name.endswith('.sol'):
            name = name[:-4]
        return match.group(1) + name + match.group(3)

    return pattern.sub(_repl, text)


def _normalize_project_src(src_dir: Path) -> None:
    for sol in src_dir.glob('**/*.sol'):
        text = sol.read_text()
        normalized = _normalize_artifact_refs(text)
        if 'importCLContracts("local")' in normalized:
            normalized = normalized.replace(
                'importCLContracts("local");',
                '// stage3: CL export fixture unavailable; skip importCLContracts')
        if normalized != text:
            sol.write_text(normalized)


def build_projects(case_dir: Path, run_dir: Path, binding: dict | None = None,
                   spec: dict | None = None, formal: dict | None = None) -> tuple[Path, Path]:
    case_dir = Path(case_dir)
    run_dir = Path(run_dir)
    original = run_dir / 'original'
    patched = run_dir / 'patched'

    _copy_tree(case_dir / 'src', original / 'src')
    _normalize_project_src(original / 'src')
    _copy_tree(case_dir / 'test', original / 'test')
    _write_project_config(case_dir, original)

    # Copy the harness before injecting: a test-level monitor targets
    # ``../test/<file>`` relative to the copied ``src`` tree, so the target
    # must exist when ``inject_patched_sources`` rewrites it.
    _copy_tree(case_dir / 'test', patched / 'test')
    patched_src = case_dir / 'patched'
    if patched_src.is_dir():
        _copy_tree(patched_src, patched / 'src')
    else:
        if binding is None or spec is None or formal is None:
            raise SpecError('M4 injection requires binding/spec/formal')
        inject_patched_sources(case_dir, patched / 'src', binding, spec, formal)
    _normalize_project_src(patched / 'src')
    _write_project_config(case_dir, patched)
    return original, patched


def build_effect_project(case_dir: Path, effect_dir: Path, binding: dict,
                         spec: dict, formal: dict) -> Path:
    """Build a third project that injects ``assert(!P || V)`` instead of I.

    The original PoC passing already witnesses ``P AND T``; the I-probe only
    tells us whether ``not-I`` is reachable.  When I is vacuous on the exploit
    path (a ``guard -> property`` implication whose guard never fires on the
    vulnerable code), the I-probe passes and the run would be misclassified as
    ``violation_not_reproduced`` even though the effect actually occurred.  The
    effect probe closes that gap by witnessing ``P AND T AND V`` independently.
    """
    case_dir = Path(case_dir)
    effect_dir = Path(effect_dir)
    _copy_tree(case_dir / 'src', effect_dir / 'src')
    _normalize_project_src(effect_dir / 'src')
    _copy_tree(case_dir / 'test', effect_dir / 'test')
    inject_patched_sources(case_dir, effect_dir / 'src', binding, spec, formal,
                           probe_kind='effect')
    # ``inject_patched_sources`` re-copies the case source over the target
    # directory.  Normalize again after injection so the effect probe uses the
    # same flattened-source fixes (for example disabled local CL imports) as
    # the original/patched projects.
    _normalize_project_src(effect_dir / 'src')
    _write_project_config(case_dir, effect_dir)
    return effect_dir


def build_negative_project(case_dir: Path, negative_dir: Path, binding: dict,
                           spec: dict, formal: dict) -> Path:
    """Build an independent ``assert(!P || !V)`` negative witness project.

    The negative probe never rewrites a dynamic verdict.  It only supplies the
    ``P_and_T_and_not_V`` witness required before a trusted negative may be
    counted as TN.
    """
    case_dir = Path(case_dir)
    negative_dir = Path(negative_dir)
    _copy_tree(case_dir / 'src', negative_dir / 'src')
    _normalize_project_src(negative_dir / 'src')
    _copy_tree(case_dir / 'test', negative_dir / 'test')
    inject_patched_sources(case_dir, negative_dir / 'src', binding, spec,
                           formal, probe_kind='negative')
    _normalize_project_src(negative_dir / 'src')
    _write_project_config(case_dir, negative_dir)
    return negative_dir


def _write_project_config(case_dir: Path, project_dir: Path):
    """Honour a case-level Foundry config, else write the minimal default."""
    case_toml = case_dir / 'foundry.toml'
    if case_toml.is_file():
        shutil.copy2(case_toml, project_dir / 'foundry.toml')
    else:
        (project_dir / 'foundry.toml').write_text(DEFAULT_FOUNDRY_TOML)
    _copy_optional(case_dir / 'remappings.txt', project_dir / 'remappings.txt')
    _copy_optional(case_dir / 'lib', project_dir / 'lib')
