"""Deterministic stage-3 binding normalization for the automatic loop.

The binding LLM makes one recurring mistake: it sets ``patch`` to a *business*
contract while its binding expressions reference identifiers that are only
visible inside the PoC test harness (``probe.contract``).  The resulting
project fails to compile (``undeclared identifier``) even though the binding
names the right test-contract state.

This module rewrites the injection point to the PoC test function when — and
only when — at least one referenced identifier is visible in the probe test
contract but not in the current patch contract.  It never rewrites a binding
whose referenced identifiers are already owned by the current patch contract.
"""
from __future__ import annotations

import copy
import re
from pathlib import Path

from lib.solidity_scan import (base_identifiers, contract_visible_functions,
                               contract_visible_state_vars)


def _find_source_file(src: Path, file_name: str | None) -> Path | None:
    if not file_name:
        return None
    direct = src / file_name
    if direct.is_file():
        return direct
    for path in sorted(src.glob('**/*.sol')):
        if path.name == file_name:
            return path
    return None


def _visible_roots(source: str, contract: str | None) -> set[str]:
    if not contract:
        return set()
    return (contract_visible_state_vars(source, contract) |
            contract_visible_functions(source, contract))


def _binding_roots(binding: dict) -> set[str]:
    roots: set[str] = set()
    for entry in (binding.get('bindings') or {}).values():
        if not isinstance(entry, dict):
            continue
        text = str(entry.get('solidity_expr') or '')
        statements = entry.get('solidity_stmts') or []
        if isinstance(statements, str):
            statements = [statements]
        text += ' ' + ' '.join(str(statement) for statement in statements)
        roots |= base_identifiers(text)
    return roots


def _function_scope(source: str, function: str | None,
                    contract: str | None) -> set[str]:
    """Return parameter and local-variable names for one function.

    The state-variable scanner is intentionally lexically broad (it also sees
    struct fields in flattened bases). That is useful for suggestions, but it
    must not justify moving an expression that reads a business-function
    parameter/local into the PoC test, where that binding is out of scope.
    """
    if not function:
        return set()
    from lib.patch import _function_local_names, _function_param_names
    return (_function_param_names(source, function, contract) |
            _function_local_names(source, function, contract))


def _redirect_escapes_business_scope(binding: dict, source: str,
                                     probe_contract: str,
                                     exploit_test: str) -> bool:
    functions = binding.get('patch', {}).get('functions') or []
    if not functions:
        return False
    target = functions[0]
    target_name = target.get('name') if isinstance(target, dict) else target
    target_contract = ((target.get('contract') if isinstance(target, dict)
                        else None)
                       or binding.get('patch', {}).get('contract'))
    business_scope = _function_scope(
        source, str(target_name) if target_name else None, target_contract)
    test_scope = _function_scope(source, exploit_test, probe_contract)
    return bool((_binding_roots(binding) & business_scope) - test_scope)


def _redirect_patch(binding: dict) -> dict:
    result = copy.deepcopy(binding)
    probe = result.get('probe') or {}
    patch = result.get('patch') or {}
    exploit_test = probe.get('exploit_test')
    probe_contract = probe.get('contract')
    file_name = patch.get('file') or 'Contract.sol'
    result['patch'] = {
        'file': file_name,
        'contract': probe_contract,
        'functions': [{
            'name': exploit_test,
            'file': file_name,
            'contract': probe_contract,
        }],
    }
    return result


def _matching_brace(text: str, open_idx: int) -> int:
    depth = 0
    for index in range(open_idx, len(text)):
        if text[index] == '{':
            depth += 1
        elif text[index] == '}':
            depth -= 1
            if depth == 0:
                return index
    return -1


def _function_span(source: str, contract: str, function: str) -> tuple[int, int] | None:
    contract_match = re.search(rf'\bcontract\s+{re.escape(contract)}\b', source)
    if contract_match is None:
        return None
    contract_open = source.find('{', contract_match.end())
    if contract_open < 0:
        return None
    contract_close = _matching_brace(source, contract_open)
    if contract_close < 0:
        return None
    function_match = re.search(
        rf'\bfunction\s+{re.escape(function)}\s*\(', source[contract_open:contract_close])
    if function_match is None:
        return None
    function_start = contract_open + function_match.start()
    function_open = source.find('{', contract_open + function_match.end())
    if function_open < 0 or function_open >= contract_close:
        return None
    function_close = _matching_brace(source, function_open)
    if function_close < 0 or function_close > contract_close:
        return None
    return function_open + 1, function_close


def _line_before(body: str, index: int) -> str | None:
    lines = body[:index].splitlines()
    for line in reversed(lines):
        stripped = line.strip()
        if not stripped or stripped.startswith('//'):
            continue
        return stripped
    return None


def _previous_statement(body: str, index: int) -> str | None:
    """Return the complete statement immediately before ``index``.

    A target call may sit on the second line of a multi-line initializer
    (``bool ok = oracle`` / ``    .validatePrice(0);``).  Taking the previous
    physical line yields an incomplete statement and injecting after it splits
    the initializer.  Statement boundaries, not line boundaries, are required.
    """
    boundary = max(body.rfind(';', 0, index),
                   body.rfind('{', 0, index),
                   body.rfind('}', 0, index))
    current_start = boundary + 1
    prev_boundary = max(body.rfind(';', 0, boundary),
                        body.rfind('{', 0, boundary),
                        body.rfind('}', 0, boundary))
    candidate = body[prev_boundary + 1:current_start].strip()
    return candidate or None


def _exploit_anchor(source: str, contract: str, test_function: str,
                    target_function: str) -> str | None:
    """Return a stable statement immediately before the first target call.

    A test-level injection used to snapshot ``before`` symbols at test entry.
    That samples the zero-initialised state before the PoC setup and makes P
    false, so ``require(!P || I)`` passes vacuously.  Anchor snapshots just
    before the first call to the originally-bound business function instead.
    Prefer the nearest ``vm.startPrank``/``vm.prank`` so caller-sensitive
    preconditions are sampled in the attacker context.
    """
    span = _function_span(source, contract, test_function)
    if span is None:
        return None
    start, end = span
    body = source[start:end]
    call = re.search(rf'\.\s*{re.escape(target_function)}\s*\(', body)
    if call is None:
        return None
    before_call = body[:call.start()]
    prank_matches = list(re.finditer(r'(?m)^\s*vm\.(?:startPrank|prank)\s*\([^;]*\);',
                                     before_call))
    if prank_matches:
        anchor = prank_matches[-1].group(0).strip()
        if anchor and body.count(anchor) == 1:
            return anchor
    anchor = _previous_statement(body, call.start())
    if anchor and body.count(anchor) == 1:
        return anchor
    return None


def normalize_binding(binding: dict, src: Path, *, test_dir: Path | None = None,
                      strict: bool = True) -> tuple[dict, list[str]]:
    """Normalize the binding and report which deterministic repair was applied.

    Returns ``(binding, changes)``.  ``binding`` is modified in place.
    ``test_dir``/``strict`` are accepted for interface parity and ignored.
    """
    del test_dir, strict
    changes: list[str] = []
    probe = binding.get('probe') or {}
    patch = binding.get('patch') or {}
    if not isinstance(probe, dict) or not isinstance(patch, dict):
        return binding, changes
    if not probe.get('exploit_test') or not probe.get('contract'):
        return binding, changes

    probe_contract = probe['contract']
    patch_contract = patch.get('contract')
    if patch_contract == probe_contract:
        return binding, changes

    source_path = _find_source_file(src, patch.get('file') or 'Contract.sol')
    if source_path is None:
        return binding, changes
    source = source_path.read_text()
    probe_scope = _visible_roots(source, probe_contract)
    patch_scope = _visible_roots(source, patch_contract)

    # A redirect is safe only when the binding does not depend on a parameter
    # or local of the original business function that the PoC test cannot see.
    # Without this guard, a broad state-variable scan can mistake a parameter
    # such as ``from`` for test-visible state and move the assertion out of the
    # only scope where it compiles (Ekubo transferFrom is the regression case).
    if not _redirect_escapes_business_scope(
            binding, source, probe_contract, probe['exploit_test']):
        for entry in (binding.get('bindings') or {}).values():
            if not isinstance(entry, dict):
                continue
            expr = str(entry.get('solidity_expr') or '')
            if not expr.strip() or expr.strip() == 'UNBOUND':
                continue
            roots = base_identifiers(expr)
            if not any(root in probe_scope and root not in patch_scope
                       for root in roots):
                continue
            functions = patch.get('functions') or []
            target_name = None
            if functions:
                first = functions[0]
                target_name = (first.get('name') if isinstance(first, dict)
                               else first)
            binding['patch'] = _redirect_patch(binding)['patch']
            changes.append('patch redirected to PoC test '
                           f'{probe_contract}.{probe["exploit_test"]}')
            if isinstance(target_name, str) and target_name:
                anchor = _exploit_anchor(
                    source, probe_contract, probe['exploit_test'], target_name)
                if anchor:
                    anchored = 0
                    for entry in (binding.get('bindings') or {}).values():
                        if (isinstance(entry, dict)
                                and entry.get('checkpoint') == 'before'
                                and not str(entry.get('snapshot_after') or '').strip()):
                            entry['snapshot_after'] = anchor
                            anchored += 1
                    if anchored:
                        changes.append(
                            f'before snapshots anchored before exploit call '
                            f'({anchored} symbols)')
            break
    return binding, changes
