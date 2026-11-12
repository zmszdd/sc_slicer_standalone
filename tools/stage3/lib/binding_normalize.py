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

    for entry in (binding.get('bindings') or {}).values():
        if not isinstance(entry, dict):
            continue
        expr = str(entry.get('solidity_expr') or '')
        if not expr.strip() or expr.strip() == 'UNBOUND':
            continue
        roots = base_identifiers(expr)
        if any(root in probe_scope and root not in patch_scope for root in roots):
            binding['patch'] = _redirect_patch(binding)['patch']
            changes.append('patch redirected to PoC test '
                           f'{probe_contract}.{probe["exploit_test"]}')
            break
    return binding, changes
