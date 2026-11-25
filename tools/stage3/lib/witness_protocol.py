"""Deterministic P/I/V witness classification for a Stage-3 run.

The legacy ``poc_not_witnessed`` label mixed compile failures, a missing test,
an unbound precondition, a false snapshot, and a genuine business revert.  This
module records the exact evidence instead of collapsing those cases.
"""
from __future__ import annotations

import re

SCHEMA_VERSION = 'stage3-witness-protocol/2'

_FORK_OR_SETUP_RE = re.compile(
    r'\b(?:fork|rpc|setup failed|setUp|fixture|state not found|'
    r'missing account|no code at)\b', re.I)


def unavailable(claim_id: str, code: str, reason: str | None = None,
                status: str = 'unavailable') -> dict:
    return {
        'schema_version': SCHEMA_VERSION,
        'claim_id': claim_id,
        'status': status,
        'failure_code': code,
        'reason': reason,
        'effect_witnessed': False,
        'invariant_contradicted': False,
        'invariant_held': None,
        'queries': {},
    }


def _reason(result: dict | None) -> str:
    return str((result or {}).get('reason') or '')


def _success(result: dict | None) -> bool:
    return bool(result) and result.get('status') == 'Success'


def _compile_text(compile_error) -> str:
    if isinstance(compile_error, dict):
        return str(compile_error.get('original') or
                   compile_error.get('patched') or '')
    return str(compile_error or '')


def checkpoint_evidence(binding: dict | None) -> dict:
    """Describe where each P/I/V symbol is observed without claiming truth."""
    if not isinstance(binding, dict):
        return {}
    patch = binding.get('patch') or {}
    probe = binding.get('probe') or {}
    entries = binding.get('bindings') or {}
    rows = {}
    for symbol, entry in sorted(entries.items()):
        if not isinstance(entry, dict):
            continue
        rows[symbol] = {
            'checkpoint': entry.get('checkpoint'),
            'snapshot_after': entry.get('snapshot_after'),
            'solidity_type': entry.get('solidity_type'),
            'bound': (bool(str(entry.get('solidity_expr') or '').strip())
                      and str(entry.get('solidity_expr')).strip() != 'UNBOUND'),
        }
    return {
        'probe': {'contract': probe.get('contract'),
                  'exploit_test': probe.get('exploit_test')},
        'injection': {'contract': patch.get('contract'),
                      'file': patch.get('file'),
                      'functions': patch.get('functions') or []},
        'symbols': rows,
    }


def classify(claim_id: str, *, original_result: dict | None = None,
             patched_result: dict | None = None,
             effect_result: dict | None = None,
             queries: dict | None = None,
             compile_error=None, test_missing: bool = False,
             precondition_failure: str | None = None,
             invariant_unbound: list[str] | None = None,
             binding: dict | None = None) -> dict:
    code = None
    status = 'unknown'
    reason = None
    compile_text = _compile_text(compile_error)
    if compile_text:
        code, status = 'poc_compile_failed', 'unavailable'
        reason = compile_text[:2000]
    elif test_missing:
        code, status = 'poc_test_missing', 'unavailable'
        reason = 'the probe exploit test was not present in forge output'
    elif invariant_unbound:
        code, status = 'precondition_unobservable', 'unavailable'
        reason = 'required P/I symbols are UNBOUND: ' + ', '.join(invariant_unbound)
    elif original_result is None:
        code, status = 'poc_not_run', 'unavailable'
        reason = 'the original exploit test produced no result'
    elif not _success(original_result):
        original_reason = _reason(original_result)
        if _FORK_OR_SETUP_RE.search(original_reason):
            code = 'fork_state_missing'
        else:
            code = 'poc_revert_before_effect'
        status = 'failed'
        reason = original_reason
    elif precondition_failure == 'snapshot_unwitnessed':
        code, status = 'precondition_false', 'failed'
        reason = _reason(patched_result)
    elif effect_result is not None and not _success(effect_result):
        code, status = 'effect_not_witnessed', 'failed'
        reason = ('the exploit action completed, but the independent effect '
                  'probe did not observe the claimed effect')
    elif effect_result is None and queries.get('P_and_T_and_V') == 'unsat':
        code, status = 'effect_not_witnessed', 'failed'
        reason = ('the exploit action completed, but no independent effect '
                  'witness was produced')
    else:
        status = 'witnessed'

    queries = queries or {}
    effect_witnessed = _success(effect_result)
    action_witnessed = _success(original_result)
    invariant_contradicted = queries.get('P_and_T_and_not_I') == 'sat'
    return {
        'schema_version': SCHEMA_VERSION,
        'claim_id': claim_id,
        'status': status,
        'failure_code': code,
        'reason': reason,
        'revert_reason': (_reason(original_result)
                          if original_result and not _success(original_result)
                          else None),
        'original_status': (original_result or {}).get('status'),
        'patched_status': (patched_result or {}).get('status'),
        'effect_status': (effect_result or {}).get('status'),
        'action_witnessed': action_witnessed,
        'effect_witnessed': effect_witnessed,
        'effect_after_action': action_witnessed and effect_witnessed,
        'evidence_level': ('complete' if action_witnessed and effect_witnessed
                           else 'partial' if action_witnessed else
                           'unavailable'),
        'invariant_contradicted': invariant_contradicted,
        'invariant_held': queries.get('P_and_T_and_not_I') == 'unsat',
        'queries': dict(queries),
        'precondition_failure': precondition_failure,
        'checkpoint_evidence': checkpoint_evidence(binding),
    }


def classify_summary(claim_id: str, summary: dict) -> dict:
    """Classify an existing ``stage3-summary.json`` without rerunning forge.

    New runs already carry a ``witness`` record; legacy runs are reconstructed
    from compile/forge/query fields.  The reconstruction intentionally keeps
    ``unknown`` separate from a genuine business revert.
    """
    recorded = summary.get('witness')
    if isinstance(recorded, dict) and recorded.get('failure_code') is not None:
        return {**recorded, 'source': 'recorded'}
    if isinstance(recorded, dict) and recorded.get('status') == 'witnessed':
        return {**recorded, 'source': 'recorded'}

    forge = summary.get('forge') or {}
    exploit = forge.get('exploit') or {}
    effect = forge.get('effect')
    queries = summary.get('code_query_results') or {}
    original = exploit.get('original')
    patched = exploit.get('patched')
    precondition_failure = summary.get('precondition_failure')
    compile_error = summary.get('compile_error')
    verdict = summary.get('consistency_verdict')
    record = classify(
        claim_id,
        original_result=original,
        patched_result=patched,
        effect_result=effect,
        queries=queries,
        compile_error=compile_error,
        precondition_failure=precondition_failure,
    )
    record['source'] = 'reconstructed'
    record['verdict'] = verdict
    if record.get('failure_code'):
        return record
    if verdict == 'effect_observed_invariant_holds':
        record.update({
            'status': 'witnessed',
            'failure_code': 'effect_witnessed_invariant_holds',
            'effect_witnessed': (effect or {}).get('status') == 'Success',
            'invariant_contradicted': False,
            'invariant_held': True,
        })
    elif verdict == 'violation_not_reproduced':
        effect_ok = (effect or {}).get('status') == 'Success'
        record.update({
            'status': 'failed',
            'failure_code': ('effect_witnessed_but_no_violation'
                             if effect_ok else 'effect_not_witnessed'),
            'effect_witnessed': effect_ok,
        })
    elif verdict in {'binding_error', 'compile_error', 'compile_blocked'}:
        record.update({
            'status': 'unavailable',
            'failure_code': 'binding_or_compile_failure',
        })
    elif verdict == 'inconclusive':
        record.update({'status': 'unknown', 'failure_code': 'inconclusive'})
    elif verdict == 'impact_insufficient':
        record.update({'status': 'witnessed', 'failure_code': 'impact_insufficient'})
    else:
        record.update({'status': 'unknown', 'failure_code': 'unclassified'})
    return record
