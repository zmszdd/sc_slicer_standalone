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
                               contract_decl_kind,
                               contract_visible_functions,
                               contract_visible_state_vars,
                               contract_has_function, file_level_functions,
                               file_level_state_vars)
from lib.rebind import parse_source_signatures

LINT_SCHEMA = 'stage3-binding-lint/2'

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


def _top_level_operator(expr: str) -> str | None:
    depth = 0
    for index, char in enumerate(expr):
        if char in '([{':
            depth += 1
        elif char in ')]}':
            depth = max(0, depth - 1)
        elif depth == 0:
            for operator in ('==', '!=', '<=', '>=', '&&', '||'):
                if expr.startswith(operator, index):
                    return operator
            if char in '<>':
                return char
    return None


def _single_call_returns(expr: str, signatures: dict) -> list[str] | None:
    text = expr.strip()
    match = re.fullmatch(
        r'[A-Za-z_$][A-Za-z0-9_$]*(?:\s*\.\s*[A-Za-z_$][A-Za-z0-9_$]*)*'
        r'\s*\(.*\)', text, re.S)
    if not match:
        return None
    head = text.split('(', 1)[0]
    name = head.split('.')[-1].strip()
    overloads = (signatures.get('functions') or {}).get(name) or []
    if not overloads:
        return None
    overload = max(overloads, key=lambda row: row.get('arity') or 0)
    return list(overload.get('returns') or [])


def _shape_problems(name: str, entry: dict, signatures: dict) -> list[dict]:
    expr = str(entry.get('solidity_expr') or '').strip()
    kind = entry.get('kind')
    if not expr or expr == 'UNBOUND':
        return []
    where = f'bindings.{name}.solidity_expr'
    problems: list[dict] = []
    returns = _single_call_returns(expr, signatures)
    if returns is not None and len(returns) > 1:
        problems.append({
            'where': where, 'severity': 'error',
            'code': 'BINDING_SHAPE_TUPLE_AS_SCALAR',
            'message': (f'call returns {len(returns)} values but the binding '
                        'uses it as one scalar; destructure it in solidity_stmts'),
        })
        return problems
    if returns and len(returns) == 1:
        returned = str(returns[0]).lower()
        expected_type = {
            'boolean_predicate': 'bool',
            'address_value': 'address',
            'numeric_value': 'int',
        }.get(kind)
        mismatch = (
            expected_type == 'bool' and returned != 'bool' or
            expected_type == 'address' and returned != 'address' or
            expected_type == 'int' and not (returned.startswith('uint') or
                                             returned.startswith('int') or
                                             returned.startswith('fixed') or
                                             returned.startswith('ufixed')))
        if mismatch:
            problems.append({
                'where': where, 'severity': 'error',
                'code': 'BINDING_SHAPE_KIND_MISMATCH',
                'message': (f'{kind} symbol is bound to a call returning '
                            f'{returned!r}'),
            })
    if (kind in {'numeric_value', 'address_value'} and
            expr.startswith('(') and expr.endswith(')') and
            ',' in expr):
        problems.append({
            'where': where, 'severity': 'error',
            'code': 'BINDING_SHAPE_TUPLE_AS_SCALAR',
            'message': 'tuple literal cannot be bound to one scalar symbol',
        })
    if kind == 'boolean_predicate' and re.fullmatch(r'-?\d+(?:\.\d+)?', expr):
        problems.append({
            'where': where, 'severity': 'error',
            'code': 'BINDING_SHAPE_NUMBER_AS_BOOL',
            'message': 'numeric literal cannot be bound to a boolean symbol',
        })
    return problems

def lint_binding(binding: dict, src: Path, *, test_dir: Path | None = None,
                 strict: bool = False, safety_symbols: set[str] | None = None,
                 observable_ir: dict | None = None) -> dict:
    """Return a machine-readable lint record for one binding.json.

    ``src`` is the contracts directory, ``test_dir`` (optional) the Foundry test
    directory used to resolve ``probe.contract`` test-contract names.
    """
    problems: list[dict] = []
    index = scan_src(src)
    all_files = dict(index.files)
    contracts = set().union(*(f.contracts for f in index.files.values()))
    all_functions = set().union(*(set(f.functions) for f in index.files.values()))
    if test_dir is not None:
        try:
            test_index = scan_src(test_dir)
        except FileNotFoundError:
            test_index = None
        if test_index is not None:
            all_files.update(test_index.files)
            contracts |= set().union(*(f.contracts for f in test_index.files.values()))
            all_functions |= set().union(*(set(f.functions)
                                           for f in test_index.files.values()))
    declared = set().union(*(f.declared() for f in all_files.values()))
    src_files = {path.name for path in all_files}
    signatures = parse_source_signatures(
        '\n'.join(path.read_text() for path in all_files))

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
        if patch_file is not None and patch_file in all_files:
            same_file_state_vars = set(all_files[patch_file].state_vars)
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
    all_entry_declared = set(declared)
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
        all_entry_declared |= entry_declared - declared
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
        for problem in _shape_problems(name, entry, signatures):
            problems.append(problem)
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
                if (root in same_file_state_vars
                        and root not in patch_scope
                        and root not in (patch_function_scope or set())):
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

    if safety_symbols:
        checkpoints = {
            str((bindings.get(name) or {}).get('checkpoint') or '')
            for name in safety_symbols
            if isinstance(bindings.get(name), dict)
            and str((bindings.get(name) or {}).get('checkpoint') or '').strip()
        }
        if len(checkpoints) == 1:
            problems.append({
                'where': 'bindings.I.checkpoint',
                'severity': 'notice',
                'code': 'I_SINGLE_CHECKPOINT',
                'message': (f'all invariant symbols use one checkpoint '
                            f'({next(iter(checkpoints))}); verify this is a '
                            'transition rather than a single snapshot'),
            })

    ir_audit = None
    if observable_ir:
        from lib.observable_ir import audit_binding
        ir_audit = audit_binding(binding, observable_ir,
                                 declared_roots=all_entry_declared)
        for row in ir_audit.get('problems') or []:
            problems.append({
                'where': f"bindings.{row['symbol']}.solidity_expr",
                'severity': row.get('severity', 'warning'),
                'code': row.get('code'),
                'message': row.get('message'),
            })
    if isinstance(patch, dict):
        for label, file in (('patch.file', patch.get('file')),
                            ('patch.contract', patch.get('contract'))):
            file_ok = (file in src_files or
                       (file and Path(file).name in src_files))
            if file and label.endswith('.file') and not file_ok:
                problems.append({'where': label, 'severity': 'error',
                                 'message': f'patch target not found in src: {file}'})
        for i, fn in enumerate(patch.get('functions') or []):
            fn_file = fn.get('file') if isinstance(fn, dict) else None
            fn_ok = (fn_file in src_files or
                     (fn_file and Path(fn_file).name in src_files))
            if isinstance(fn, dict) and fn_file and not fn_ok:
                problems.append({'where': f'patch.functions[{i}].file',
                                 'severity': 'error',
                                 'message': f'patch target not found in src: {fn_file}'})
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
                if contract and exists and path is not None:
                    try:
                        kind = contract_decl_kind(path.read_text(), contract)
                    except OSError:
                        kind = None
                    if kind == 'library':
                        problems.append({
                            'where': f'patch.functions[{i}].contract',
                            'severity': 'error',
                            'message': (f'patch target {contract!r} is a library; '
                                        'inject into the business contract or use '
                                        'an explicit test-level monitor')})
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
        'observable_ir_audit': ir_audit,
    }
