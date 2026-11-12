"""Source-aware binding lint for stage-3 cases.

Cross-checks a filled ``binding.json`` against the case Solidity sources so the
most common manual-binding mistakes (unfilled ``TODO_BIND_*`` placeholders,
typo'd identifiers, missing patch targets, mismatched probe contracts) fail
fast *before* ``forge`` is invoked.

This is a lint/suggestion layer, not a semantic proof: a binding can lint clean
and still be semantically wrong. Its value is deterministic, zero-model-cost
fault triage on the stage-2 -> stage-3 handoff channel.
"""
from __future__ import annotations

import re
from pathlib import Path

from lib.solidity_scan import (IDENT, KEYWORDS, is_snapshot_identifier,
                               scan_src, base_identifiers,
                               contract_visible_functions,
                               contract_visible_state_vars,
                               contract_has_function, file_level_functions,
                               file_level_state_vars)

LINT_SCHEMA = 'stage3-binding-lint/1'

# Roots that may legally start a Solidity expression without a user declaration.
ALLOWED_ROOTS = {
    'msg', 'block', 'tx', 'address', 'this', 'type', 'super', 'now', 'abi',
    'bytes', 'string', 'bool', 'true', 'false', 'gasleft', 'keccak256',
    'sha256', 'ripemd160', 'ecrecover', 'addmod', 'mulmod', 'blockhash',
    'uint', 'int', 'uint256', 'int256', 'uint8', 'uint16', 'uint24',
    'uint32', 'uint40', 'uint48', 'uint64', 'uint128', 'uint160', 'uint192',
    'int8', 'int16', 'int24', 'int32', 'int64', 'int128', 'int256',
    'bytes1', 'bytes2', 'bytes4', 'bytes8', 'bytes16', 'bytes32', 'ufixed',
    'fixed', 'uint128', 'uint160', 'uint192', 'uint256',
    # Solidity numeric/time-unit literals: "1 ether", "2 days", ...
    'wei', 'gwei', 'ether',
    'seconds', 'minutes', 'hours', 'days', 'weeks',
}


def _unknown_roots(expr: str, declared: set[str]) -> set[str]:
    roots = base_identifiers(expr)
    unknown: set[str] = set()
    for root in roots:
        if is_snapshot_identifier(root):
            continue
        if root in ALLOWED_ROOTS or root in KEYWORDS:
            continue
        if root in declared:
            continue
        # numeric/hex literals were already dropped by base_identifiers
        unknown.add(root)
    return unknown


def _source_file(source: str) -> str | None:
    if not source or ':' not in source:
        return None
    return source.split(':', 1)[0]


def _trivial_bool_literal(expr: str) -> str | None:
    """Return ``'true'``/``'false'`` when *expr* is a bare boolean literal,
    ignoring whitespace and redundant enclosing parentheses. A vacuous binding
    (for example ``solidity_expr: true``) makes the safety invariant a constant
    and therefore never exposes a violation through differential witness, so it
    must be treated as a binding error rather than silently passing lint.
    """
    text = expr.strip()
    while text.startswith('(') and text.endswith(')'):
        depth = 0
        balanced = True
        for i, char in enumerate(text):
            if char == '(':
                depth += 1
            elif char == ')':
                depth -= 1
                if depth < 0:
                    balanced = False
                    break
            if depth == 0 and i != len(text) - 1:
                balanced = False
                break
        if not balanced or depth != 0:
            break
        text = text[1:-1].strip()
    if text in ('true', 'false'):
        return text
    return None


def _find_patch_file(src: Path, file_name: str, index) -> Path | None:
    """Resolve ``patch.file`` to a scanned source path, tolerant of prefixes."""
    if not file_name:
        return None
    direct = src / file_name
    if direct.is_file():
        return direct
    for path in index.files:
        if path.name == file_name or str(path).endswith(file_name):
            return path
    return None


def _contract_scope(patch: dict | None, src: Path, index,
                     contract: str | None = None) -> set[str] | None:
    """Over-approximated name set visible inside the injection contract.

    Uses the transitive inheritance closure so state variables declared in a
    test-harness base contract (for example ``C4PoCTestbed`` inherited by the
    PoC contract) are correctly treated as visible rather than cross-contract.

    The explicit ``contract`` override is used when ``patch.contract`` is
    missing so the scoped cross-contract check still runs (the failure is then
    classified as ``cross_contract_reference`` instead of surfacing late as a
    forge ``compile_error``).
    """
    if not isinstance(patch, dict):
        return None
    contract = contract or patch.get('contract')
    if not contract:
        return None
    path = _find_patch_file(src, patch.get('file') or '', index)
    if path is None:
        return None
    try:
        return contract_visible_state_vars(path.read_text(), contract)
    except OSError:
        return None

def lint_binding(binding: dict, src: Path, *, test_dir: Path | None = None,
                 strict: bool = False, safety_symbols: set[str] | None = None) -> dict:
    """Return a machine-readable lint record for one binding.json.

    ``src`` is the contracts directory, ``test_dir`` (optional) the Foundry test
    directory used to resolve ``probe.contract`` test-contract names.
    """
    problems: list[dict] = []
    index = scan_src(src)
    declared = index.all_declared()
    src_files = {f.name for f in index.files}
    contracts = set().union(*(f.contracts for f in index.files.values()))
    all_functions = set().union(*(set(f.functions) for f in index.files.values()))
    if test_dir is not None:
        try:
            test_index = scan_src(test_dir)
        except FileNotFoundError:
            test_index = None
        if test_index is not None:
            contracts |= set().union(*(f.contracts for f in test_index.files.values()))
            all_functions |= set().union(*(set(f.functions)
                                           for f in test_index.files.values()))

    patch = binding.get('patch')
    probe_hint = binding.get('probe') or {}
    patch_contract = patch.get('contract') if isinstance(patch, dict) else None
    effective_contract = patch_contract
    if not effective_contract and isinstance(patch, dict):
        for fn in patch.get('functions') or []:
            if isinstance(fn, dict) and fn.get('contract'):
                effective_contract = fn['contract']
                break
    if not effective_contract:
        effective_contract = probe_hint.get('contract')
    patch_scope = _contract_scope(patch, src, index, contract=effective_contract)
    same_file_state_vars: set[str] = set()
    file_level_vars: set[str] = set()
    patch_function_scope: set[str] | None = None
    file_level_fn_set: set[str] = set()
    if isinstance(patch, dict):
        patch_file = _find_patch_file(src, patch.get('file') or '', index)
        if patch_file is not None and patch_file in index.files:
            same_file_state_vars = set(index.files[patch_file].state_vars)
            try:
                raw = patch_file.read_text()
                file_level_vars = file_level_state_vars(raw)
                if effective_contract:
                    patch_function_scope = contract_visible_functions(
                        raw, effective_contract)
                file_level_fn_set = file_level_functions(raw)
            except OSError:
                file_level_vars = set()

    bindings = binding.get('bindings') or {}
    for name, entry in bindings.items():
        if not isinstance(entry, dict):
            problems.append({'where': f'bindings.{name}', 'severity': 'error',
                             'message': 'binding entry is not an object'})
            continue
        expr = str(entry.get('solidity_expr') or '')
        # ``solidity_stmts`` declare helper locals (tuple destructuring); those
        # names are visible in ``solidity_expr`` even though they are not
        # declared in the source.
        entry_declared = set(declared)
        stmts = entry.get('solidity_stmts') or []
        if isinstance(stmts, str):
            stmts = [stmts]
        for stmt in stmts:
            lhs = str(stmt).split('=', 1)[0]
            entry_declared |= {token for token in re.findall(IDENT, lhs)}
        if not expr.strip():
            problems.append({'where': f'bindings.{name}.solidity_expr',
                             'severity': 'error', 'message': 'empty solidity_expr'})
            continue
        if re.search(r'TODO_BIND_', expr):
            problems.append({'where': f'bindings.{name}.solidity_expr',
                             'severity': 'error',
                             'message': f'unfilled placeholder: {expr}'})
            continue
        trivial = _trivial_bool_literal(expr)
        # A constant boolean only vacates the differential witness when the
        # symbol itself appears in the safety invariant I. A constant P-side
        # boolean (e.g. a direct-call precondition that the PoC establishes by
        # construction) is a faithful precondition and must not be rejected.
        if safety_symbols is not None and name not in safety_symbols:
            trivial = None
        if trivial is not None:
            problems.append({'where': f'bindings.{name}.solidity_expr',
                             'severity': 'error',
                             'message': (f'trivially constant binding: {expr!r} '
                                         f'evaluates to literal {trivial}; '
                                         f'bind to an observable expression')})
            continue
        if expr.strip() == name and name not in declared:
            problems.append({'where': f'bindings.{name}.solidity_expr',
                             'severity': 'error',
                             'message': f'self-referential placeholder: {expr!r} equals the symbol name and is not declared in src'})
            continue
        for root in sorted(_unknown_roots(expr, entry_declared)):
            problems.append({'where': f'bindings.{name}.solidity_expr',
                             'severity': 'warning' if not strict else 'error',
                             'message': f'identifier {root!r} not declared in src'})
        if patch_scope is not None:
            for root in sorted(base_identifiers(expr)):
                if is_snapshot_identifier(root):
                    continue
                if root in ALLOWED_ROOTS or root in KEYWORDS:
                    continue
                if root in file_level_vars:
                    continue
                if root in (entry_declared - declared):
                    continue
                if root in same_file_state_vars and root not in patch_scope:
                    problems.append({
                        'where': f'bindings.{name}.solidity_expr',
                        'severity': 'warning' if not strict else 'error',
                        'message': (f'cross-contract reference: {root!r} is a '
                                    f'state variable outside {effective_contract!r} '
                                    f'and is not visible from the injection point')
                    })
                if (patch_function_scope is not None
                        and root not in patch_scope
                        and root in all_functions
                        and root not in patch_function_scope
                        and root not in file_level_fn_set):
                    problems.append({
                        'where': f'bindings.{name}.solidity_expr',
                        'severity': 'warning' if not strict else 'error',
                        'message': (f'cross-contract reference: {root!r} is a '
                                    f'function declared outside {effective_contract!r} '
                                    f'and is not visible from the injection point')
                    })

    if isinstance(patch, dict):
        for label, file in (('patch.file', patch.get('file')),
                            ('patch.contract', patch.get('contract'))):
            if file and label.endswith('.file') and file not in src_files:
                problems.append({'where': label, 'severity': 'error',
                                 'message': f'patch target not found in src: {file}'})
        for i, fn in enumerate(patch.get('functions') or []):
            if isinstance(fn, dict) and fn.get('file') and fn['file'] not in src_files:
                problems.append({'where': f'patch.functions[{i}].file',
                                 'severity': 'error',
                                 'message': f'patch target not found in src: {fn["file"]}'})
            if isinstance(fn, dict) and fn.get('name'):
                contract = fn.get('contract') or patch.get('contract')
                file_name = fn.get('file') or patch.get('file')
                path = _find_patch_file(src, file_name, index)
                exists = False
                if path is not None and contract:
                    try:
                        exists = contract_has_function(path.read_text(),
                                                       contract, fn['name'])
                    except OSError:
                        exists = False
                if contract and not exists:
                    problems.append({
                        'where': f'patch.functions[{i}].name',
                        'severity': 'error',
                        'message': (f'function {fn["name"]!r} not found in '
                                    f'contract {contract!r}; bind to the actual '
                                    f'PoC test function name')})
    elif patch is not None:
        problems.append({'where': 'patch', 'severity': 'warning',
                         'message': 'patch must be an object'})

    probe = binding.get('probe') or {}
    if probe and probe.get('contract') and probe['contract'] not in contracts:
        problems.append({'where': 'probe.contract', 'severity': 'warning',
                         'message': f'contract {probe["contract"]!r} not found in src'})
    if probe and probe.get('exploit_test'):
        if probe['exploit_test'] not in all_functions:
            problems.append({
                'where': 'probe.exploit_test',
                'severity': 'error',
                'message': (f'test function {probe["exploit_test"]!r} not '
                            f'found in src or test sources')})

    errors = sum(1 for p in problems if p['severity'] == 'error')
    warnings = sum(1 for p in problems if p['severity'] == 'warning')
    return {
        'schema_version': LINT_SCHEMA,
        'strict': strict,
        'ok': errors == 0 and (not strict or warnings == 0),
        'summary': {'errors': errors, 'warnings': warnings},
        'problems': problems,
    }
