"""Build a compact, replayable execution contract for one stage-3 claim.

The stage-2 handoff carries formulas and symbols, but not the evidence needed
to decide whether those formulas can be observed on the PoC path.  This module
records that missing bridge in one artifact: role symbols, checkpoints,
binding completeness, weak-invariant findings, and whether the claim needs a
test-level monitor instead of a single business-function assertion.

The contract is descriptive.  It does not mutate a binding or weaken a gate;
the pipeline still decides expressibility from the actual source lint.
"""
from __future__ import annotations

from lib.spec_loader import (precondition_symbols_for_claim,
                             safety_symbols_for_claim)

SCHEMA_VERSION = 'stage3-execution-contract/1'


def _claims(formal: dict) -> dict:
    return {
        row.get('id'): row
        for row in (formal.get('claims') or [])
        if isinstance(row, dict) and row.get('id')
    }


def _expr_symbols(node) -> set[str]:
    if not isinstance(node, dict):
        return set()
    if 'var' in node:
        return {node['var']}
    found: set[str] = set()
    for value in node.values():
        if isinstance(value, dict):
            found |= _expr_symbols(value)
        elif isinstance(value, list):
            for item in value:
                found |= _expr_symbols(item)
    return found


def _property_expr(claim: dict, name: str):
    return (((claim.get('properties') or {}).get(name) or {})
            .get('expression'))


def _binding_row(entry: dict | None) -> dict:
    entry = entry if isinstance(entry, dict) else {}
    expr = str(entry.get('solidity_expr') or '').strip()
    return {
        'bound': bool(expr) and expr != 'UNBOUND',
        'solidity_expr': expr or None,
        'kind': entry.get('kind'),
        'checkpoint': entry.get('checkpoint'),
        'solidity_type': entry.get('solidity_type'),
        'snapshot_after': entry.get('snapshot_after'),
    }


def build(formal: dict, binding: dict, claim_id: str, *,
          weak_invariant: dict | None = None,
          monitor: dict | None = None,
          execution_gate: dict | None = None,
          formalization_contract: dict | None = None) -> dict:
    """Return a JSON-serialisable execution contract for ``claim_id``."""
    claims = _claims(formal)
    claim = claims.get(claim_id)
    if claim is None:
        return {
            'schema_version': SCHEMA_VERSION,
            'claim_id': claim_id,
            'status': 'claim_missing',
            'symbols': {},
            'requirements': {},
            'monitor': monitor or {},
        }

    p_symbols = precondition_symbols_for_claim(formal, claim_id)
    i_symbols = safety_symbols_for_claim(formal, claim_id)
    v_symbols = _expr_symbols(_property_expr(claim, 'effects')) - p_symbols
    entries = binding.get('bindings') or {}
    roles = {}
    for role, symbols in (('P', p_symbols), ('I', i_symbols), ('V', v_symbols)):
        for symbol in sorted(symbols):
            row = roles.setdefault(symbol, {
                'roles': [], 'binding': _binding_row(entries.get(symbol))})
            row['roles'].append(role)

    required = p_symbols | i_symbols
    unbound_required = sorted(
        symbol for symbol in required
        if not _binding_row(entries.get(symbol))['bound'])
    unbound_effect = sorted(
        symbol for symbol in v_symbols
        if not _binding_row(entries.get(symbol))['bound'])
    checkpoints = sorted({
        row['binding']['checkpoint'] for row in roles.values()
        if row['binding'].get('checkpoint')})
    probe = binding.get('probe') or {}
    patch = binding.get('patch') or {}
    patch_functions = patch.get('functions') or []
    target_function = None
    if patch_functions:
        first = patch_functions[0]
        target_function = (first.get('name') if isinstance(first, dict)
                           else first)
    target_contract = patch.get('contract')
    if patch_functions and isinstance(patch_functions[0], dict):
        target_contract = patch_functions[0].get('contract') or target_contract
    test_level = bool(
        probe.get('exploit_test') and target_function == probe.get('exploit_test'))

    return {
        'schema_version': SCHEMA_VERSION,
        'claim_id': claim_id,
        'status': 'ready' if not unbound_required else 'incomplete',
        'probe': {
            'contract': probe.get('contract'),
            'exploit_test': probe.get('exploit_test'),
        },
        'patch_target': {
            'file': patch.get('file'),
            'contract': target_contract,
            'function': target_function,
            'test_level': test_level,
        },
        'stage2_contract': formalization_contract or {},
        'symbols': roles,
        'checkpoints': checkpoints,
        'requirements': {
            'invariant_probe': 'assert(!P || I)',
            'effect_probe': 'assert(!P || V)',
            'required_symbols_bound': not unbound_required,
            'unbound_required_symbols': unbound_required,
            'unbound_effect_symbols': unbound_effect,
            'same_trace_required': True,
        },
        'weak_invariant': weak_invariant or {},
        'execution_gate': execution_gate or {},
        'monitor': monitor or {},
    }
