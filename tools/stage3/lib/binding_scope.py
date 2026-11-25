"""Deterministic probe/patch scope recovery for the observable IR.

The observable IR computes candidate visibility at the point where ``I`` will
be injected.  A binding often records that point as the PoC test function even
though the report facts are computed in a business contract.  This module
recovers the real business patch target from the binding's ``source`` fields
(or from the deterministic anchor resolver) so that IR visibility and recipe
compilation use the same program slice as the final differential.
"""
from __future__ import annotations

import json
from pathlib import Path

from lib.solidity_scan import (contract_decl_kind, contract_has_function,
                               function_callees, function_owner,
                               poc_test_contract, poc_test_function_for_case)

SCHEMA_VERSION = 'stage3-binding-scope/1'


def _source_text(case_dir: Path, source_name: str | None,
                 src_dir: Path | None) -> str:
    paths = []
    if case_dir and source_name:
        paths.append(Path(case_dir) / 'src' / str(source_name))
    if src_dir:
        root = Path(src_dir)
        paths.extend(sorted(root.rglob('*.sol')) if root.is_dir() else [root])
    seen = set()
    for path in paths:
        key = str(path)
        if key in seen or not path.is_file():
            continue
        seen.add(key)
        try:
            return path.read_text(errors='replace')
        except OSError:
            continue
    return ''


def _function_names(binding: dict) -> list[str]:
    patch = binding.get('patch') if isinstance(binding.get('patch'), dict) else {}
    names = []
    for row in patch.get('functions') or []:
        name = row.get('name') if isinstance(row, dict) else row
        if name and str(name) not in names:
            names.append(str(name))
    probe = binding.get('probe') if isinstance(binding.get('probe'), dict) else {}
    exploit_test = probe.get('exploit_test')
    if exploit_test and str(exploit_test) not in names:
        names.append(str(exploit_test))
    return names


def _call_paths(source: str, contract: str, starts: list[str],
                targets: list[str], *, max_depth: int = 4) -> list[list[str]]:
    """Find minimal same-contract call paths from patch targets to facts."""
    if not source or not contract or not starts or not targets:
        return []
    targets_set = set(targets)
    paths: list[list[str]] = []
    for start in starts:
        if not contract_has_function(source, contract, start):
            continue
        queue: list[list[str]] = [[start]]
        seen = {start}
        while queue:
            path = queue.pop(0)
            current = path[-1]
            if current in targets_set:
                paths.append(path)
                continue
            if len(path) > max_depth:
                continue
            for callee in sorted(function_callees(source, contract, current)):
                if callee in seen:
                    continue
                seen.add(callee)
                queue.append([*path, callee])
    unique = {tuple(path): path for path in paths}
    return [unique[key] for key in sorted(unique)]


def from_binding(case_dir: Path, binding: dict | None,
                 *, src_dir: Path | None = None) -> dict:
    """Return the IR scope recorded by one binding, with business target repair."""
    binding = binding if isinstance(binding, dict) else {}
    probe = binding.get('probe') if isinstance(binding.get('probe'), dict) else {}
    patch = binding.get('patch') if isinstance(binding.get('patch'), dict) else {}
    probe_contract = probe.get('contract')
    probe_function = probe.get('exploit_test')
    patch_contract = patch.get('contract')
    patch_file = patch.get('file')
    patch_functions = _function_names(binding)
    if not probe_contract or not probe_function:
        detected = poc_test_function_for_case(case_dir, _source_text(
            Path(case_dir) if case_dir else Path('.'), patch_file, src_dir))
        if detected:
            probe_contract, probe_function = detected

    source = _source_text(Path(case_dir) if case_dir else Path('.'),
                          patch_file or 'Contract.sol', src_dir)
    probe_functions = {probe_function} if probe_function else set()
    business_owners: set[str] = set()
    business_functions: list[str] = []
    for entry in (binding.get('bindings') or {}).values():
        if not isinstance(entry, dict):
            continue
        source_ref = str(entry.get('source') or '')
        function = source_ref.rsplit(':', 1)[-1].strip()
        if not function or function in probe_functions or function.startswith('test'):
            continue
        owners = {
            owner for owner in function_owner(source, function)
            if owner and owner != probe_contract
            and contract_decl_kind(source, owner) != 'interface'
        }
        if len(owners) == 1:
            business_owners |= owners
            if function not in business_functions:
                business_functions.append(function)

    call_slices: list[list[str]] = []
    if len(business_owners) == 1:
        owner = next(iter(business_owners))
        patch_contract = owner
        patch_starts = [
            name for name in dict.fromkeys(patch_functions + business_functions)
            if name != probe_function and not name.startswith('test')
            and contract_has_function(source, owner, name)
        ]
        call_slices = [
            path for path in _call_paths(source, owner, patch_starts,
                                         business_functions)
            if len(path) > 1
        ]
        slice_functions = {
            name for path in call_slices for name in path
        }
        patch_functions = sorted((
            set(patch_functions) | set(business_functions) | slice_functions
        ) - {probe_function})

    scope = {
        'probe_contract': probe_contract,
        'probe_function': probe_function,
        'patch_contract': patch_contract,
        'patch_functions': patch_functions,
    }
    if call_slices:
        scope['call_slices'] = call_slices
    return {key: value for key, value in scope.items()
            if value not in (None, '', [])}


def from_anchor(anchor: dict | None) -> dict:
    """Return patch scope that the deterministic anchor resolver can supply."""
    anchor = anchor if isinstance(anchor, dict) else {}
    contract = anchor.get('suggested_patch_contract')
    return {'patch_contract': contract} if contract else {}


def load_binding_scope(case_dir: Path, claim_id: str,
                       *, src_dir: Path | None = None) -> dict:
    path = Path(case_dir) / 'bindings' / f'{claim_id}.json'
    if not path.is_file():
        return {}
    try:
        binding = json.loads(path.read_text())
    except (OSError, ValueError):
        return {}
    return from_binding(case_dir, binding, src_dir=src_dir)


def merge(*scopes: dict | None) -> dict:
    """Merge scopes by specificity; later values win only when non-empty."""
    result: dict = {}
    for scope in scopes:
        if not isinstance(scope, dict):
            continue
        for key, value in scope.items():
            if value not in (None, '', []):
                result[key] = value
    return result
