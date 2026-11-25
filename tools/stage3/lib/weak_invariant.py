"""Stage-3 weak-invariant risk diagnostics.

Stage 2 can only prove that a symbolic V falsifies I.  Code execution can still
find I constant on the exploit path, so stage 3 records a small deterministic
risk profile before injecting the assertion: checkpoint collapse, copied I/V,
tautological implications, and numeric/boolean layer mismatch.  This is an
advisory diagnostic consumed by triage; it never weakens P or I.
"""
from __future__ import annotations


SCHEMA_VERSION = 'stage3-weak-invariant/1'
BLOCKING_CODES = {
    'I_LAYER_MISMATCH',
    'I_SELF_IMPLICATION',
    'I_COPIED_FROM_V',
}
REVIEW_CODES = {'I_CHECKPOINT_COLLAPSED'}


def _vars(node):
    if not isinstance(node, dict):
        return set()
    if 'var' in node:
        return {node['var']}
    found = set()
    for value in node.values():
        if isinstance(value, dict):
            found |= _vars(value)
        elif isinstance(value, list):
            for item in value:
                found |= _vars(item)
    return found


def _claim(formal, claim_id):
    return next((row for row in formal.get('claims', [])
                 if isinstance(row, dict) and row.get('id') == claim_id), None)


def diagnose(formal, claim_id, binding, declaration=None):
    claim = _claim(formal, claim_id)
    codes = []
    if claim is None:
        return {'schema_version': SCHEMA_VERSION, 'claim_id': claim_id,
                'codes': ['CLAIM_MISSING'], 'risk': 'unknown',
                'stage2_diagnostics': [],
                'i_falsifier_hint': (declaration or {}).get('i_falsifier_hint')}
    properties = claim.get('properties') or {}
    safety = (properties.get('safety') or {}).get('expression')
    effects = (properties.get('effects') or {}).get('expression')
    pre = (properties.get('preconditions') or {}).get('expression')
    i_symbols = _vars(safety) - _vars(pre)
    v_symbols = _vars(effects)
    entries = binding.get('bindings') or {}
    checkpoints = {
        name: str((entries.get(name) or {}).get('checkpoint') or '')
        for name in i_symbols if isinstance(entries.get(name), dict)}
    i_checkpoints = {value for value in checkpoints.values() if value}
    v_checkpoints = {
        str((entries.get(name) or {}).get('checkpoint') or '')
        for name in v_symbols if isinstance(entries.get(name), dict)}
    v_checkpoints = {value for value in v_checkpoints if value}
    if len(i_checkpoints) == 1 and len(v_checkpoints) >= 2:
        codes.append('I_CHECKPOINT_COLLAPSED')
    if (isinstance(safety, dict) and safety.get('op') == 'implies' and
            isinstance(safety.get('args'), list) and len(safety['args']) == 2 and
            safety['args'][0] == safety['args'][1]):
        codes.append('I_SELF_IMPLICATION')
    if isinstance(safety, dict) and isinstance(effects, dict) and safety == effects:
        codes.append('I_COPIED_FROM_V')
    if i_symbols and all(
            str((formal.get('symbols', {}).get(name) or {}).get('sort')) == 'bool'
            for name in i_symbols):
        numeric_ops = set()
        def walk(node):
            if not isinstance(node, dict):
                return
            if node.get('op') in ('add', 'sub', 'mul', 'lt', 'le', 'gt', 'ge'):
                numeric_ops.add(node['op'])
            for child in node.get('args') or []:
                walk(child)
        walk(effects)
        if numeric_ops:
            codes.append('I_LAYER_MISMATCH')
    stage2_diagnostics = (declaration or {}).get('weak_invariant_diagnostics') or []
    blocking = [item for item in stage2_diagnostics
                if isinstance(item, dict) and item.get('severity') == 'blocking']
    risk = 'high' if codes or blocking else 'low'
    return {
        'schema_version': SCHEMA_VERSION,
        'claim_id': claim_id,
        'codes': sorted(set(codes)),
        'risk': risk,
        'i_symbols': sorted(i_symbols),
        'v_symbols': sorted(v_symbols),
        'i_checkpoints': sorted(i_checkpoints),
        'v_checkpoints': sorted(v_checkpoints),
        'stage2_diagnostics': stage2_diagnostics,
        'i_falsifier_hint': (declaration or {}).get('i_falsifier_hint'),
    }


def gate(report: dict | None) -> dict:
    """Turn weak-invariant diagnostics into a fail-closed stage-3 route.

    A high-risk diagnostic is not a dynamic verdict.  It means the invariant
    may hold on the exploit path or collapse to a single snapshot, so forge
    would only produce a misleading ``violation_not_reproduced`` result.  The
    deterministic action is to send the claim back to stage-2 restatement.
    """
    report = report if isinstance(report, dict) else {}
    codes = set(report.get('codes') or [])
    stage2_diag = [
        row for row in (report.get('stage2_diagnostics') or [])
        if isinstance(row, dict) and row.get('severity') == 'blocking'
    ]
    blocking_codes = sorted(codes & BLOCKING_CODES)
    review_codes = sorted(codes & REVIEW_CODES)
    blocking_codes.extend(
        str(row.get('code') or 'STAGE2_WEAK_INVARIANT')
        for row in stage2_diag)
    blocking_codes = sorted(set(blocking_codes))
    blocking = bool(blocking_codes)
    return {
        'schema_version': 'stage3-weak-invariant-gate/1',
        'claim_id': report.get('claim_id'),
        'blocking': blocking,
        'category': 'stage2_restatement_required' if blocking else None,
        'codes': blocking_codes,
        'review_codes': review_codes,
        'risk': report.get('risk'),
        'reason': (
            'weak invariant cannot provide a falsifiable dynamic witness; '
            'restate I with transition/after evidence before forge'
            if blocking else None),
    }
