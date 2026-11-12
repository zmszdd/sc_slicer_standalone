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


def _contract_region(source: str, contract: str) -> tuple[int, int]:
    marker = re.search(r'\bcontract\s+' + re.escape(contract) + r'\b', source)
    if not marker:
        raise SpecError(f'contract not found: {contract}')
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
        raise SpecError(
            f'function {name} is ambiguous (found {len(matches)} matches); '
            'set patch.contract or per-function contract')
    marker = matches[0]
    open_idx = region_start + marker.end()
    # skip whitespace between the parameter list and the body brace
    brace_idx = source.find('{', open_idx)
    if brace_idx < 0 or brace_idx >= region_end:
        where = f' in contract {contract}' if contract else ''
        raise SpecError(f'function {name} has no body{where}')
    return brace_idx, _matching_brace(source, brace_idx)


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


def _render_expr(expr, entries: dict) -> str | None:
    if expr is None:
        return None
    rendered = {}
    for symbol, entry in entries.items():
        solidity_expr = entry['solidity_expr']
        if str(solidity_expr).strip() == 'UNBOUND':
            raise SpecError(
                f'symbol {symbol} has solidity_expr=UNBOUND; '
                'binding must be completed before patch injection')
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
                          identifiers: set[str]) -> dict[str, str]:
    """Map each identifier to the local-declaration statement that declares it.

    A ``before`` snapshot is injected at function entry; an expression that
    reads a variable declared later in the function body fails to compile with
    ``Undeclared identifier``.  This helper locates the declaring statement for
    each offending identifier so the caller can set ``snapshot_after`` and move
    the snapshot assignment past the declaration instead of neutralizing the
    binding (which silently downgrades the claim to ``partial_binding``).
    """
    marker = re.search(rf'\bfunction\s+{re.escape(function_name)}\s*\(', source)
    if not marker:
        return {}
    open_idx = source.find('{', marker.end())
    if open_idx < 0:
        return {}
    close_idx = _matching_brace(source, open_idx)
    body = source[open_idx + 1:close_idx]
    decl_re = re.compile(
        rf'(?m)^[ \t]+(?:mapping\([^)]*\)|[A-Za-z_$][A-Za-z0-9_$]*'
        rf'(?:\s*\[[^\]]*\])?)(?:\s+(?:storage|memory|calldata))?\s+'
        rf'([A-Za-z_$][A-Za-z0-9_$]*)\s*(?:=[^\n]*;|;)')
    found: dict[str, str] = {}
    for match in decl_re.finditer(body):
        name = match.group(1)
        if name in identifiers and name not in found:
            found[name] = body[match.start():match.end()].strip()
    return found


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
        decls = local_decl_statements(source, fn_name, roots)
        if not decls:
            continue
        # Anchor at the last-declared referenced local so every root is in scope.
        order = []
        for ident, stmt in decls.items():
            idx = source.find(stmt)
            order.append((idx, ident, stmt))
        if not order:
            continue
        anchor = max(order)[2]
        entry['snapshot_after'] = anchor
        anchors[name] = anchor
    return binding, anchors


def _snapshot_decls(entries: dict) -> tuple[list[str], list[tuple[str, str]]]:
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
        type_name = str(entry.get('solidity_type')
                        or _KIND_TYPES.get(entry['kind'], 'uint256'))
        solidity_expr = entry['solidity_expr']
        if str(solidity_expr).strip() == 'UNBOUND':
            raise SpecError(
                f'symbol {symbol} has solidity_expr=UNBOUND; '
                'binding must be completed before snapshot injection')
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
    else:
        target_expr = properties.get('safety', {}).get('expression')
        target_name = 'I'
    if target_expr is None:
        raise SpecError(f'claim has no {target_name} expression to inject')
    target_sol = _render_expr(target_expr, entries)
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
    lines.append(f'        assert({post_assert});')
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
    """
    index = body.find(anchor)
    if index < 0:
        raise SpecError(f'snapshot anchor not found in function body: {anchor!r}')
    line_end = body.find('\n', index)
    if line_end < 0:
        line_end = len(body)
    return body[:line_end] + '\n' + decl + body[line_end:]


def inject_patched_sources(case_dir: Path, patched_dir: Path, binding: dict,
                           spec: dict, formal: dict,
                           probe_kind: str = 'invariant'):
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

    patched_src = case_dir / 'patched'
    if patched_src.is_dir():
        _copy_tree(patched_src, patched / 'src')
    else:
        if binding is None or spec is None or formal is None:
            raise SpecError('M4 injection requires binding/spec/formal')
        inject_patched_sources(case_dir, patched / 'src', binding, spec, formal)
    _normalize_project_src(patched / 'src')
    _copy_tree(case_dir / 'test', patched / 'test')
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
    inject_patched_sources(case_dir, effect_dir / 'src', binding, spec, formal,
                           probe_kind='effect')
    _copy_tree(case_dir / 'test', effect_dir / 'test')
    _write_project_config(case_dir, effect_dir)
    return effect_dir


def _write_project_config(case_dir: Path, project_dir: Path):
    """Honour a case-level Foundry config, else write the minimal default."""
    case_toml = case_dir / 'foundry.toml'
    if case_toml.is_file():
        shutil.copy2(case_toml, project_dir / 'foundry.toml')
    else:
        (project_dir / 'foundry.toml').write_text(DEFAULT_FOUNDRY_TOML)
    _copy_optional(case_dir / 'remappings.txt', project_dir / 'remappings.txt')
    _copy_optional(case_dir / 'lib', project_dir / 'lib')
