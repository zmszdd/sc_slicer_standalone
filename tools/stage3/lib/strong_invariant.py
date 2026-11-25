#!/usr/bin/env python3
"""Validate the strong-invariant contract required for automatic assertion.

A claim is only machine-checkable when the invariant is tied to an observable
transition (or an accepted deterministic restatement), has before/after
checkpoints, an independent violation witness, and a source-backed observable
route.  Static snapshots remain diagnostic and must not enter Stage 3 as
``auto_assert``.
"""
from __future__ import annotations

SCHEMA_VERSION = 'stage3-strong-invariant/1'

_WEAK_BUCKETS = {'snapshot_only', 'unclassified', 'tautological',
                 'contradictory', 'effect_restatement',
                 'precondition_restatement', 'precondition_only'}
_WEAK_CODES = {'I_SNAPSHOT_ONLY', 'I_SNAPSHOT_BARE_VAR',
               'I_NOT_TRANSITION', 'I_LAYER_MISMATCH',
               'I_CHECKPOINT_COLLAPSED', 'I_V_POLARITY_ONLY',
               'I_V_RESTATEMENT', 'I_V_TAUTOLOGY', 'I_COPIED_FROM_P',
               'I_ONLY_REUSES_P'}
_HARD_REASON_PREFIXES = (
    'invariant symbols have no complete checkpoints',
    'invariant symbols have no observable route',
    'violation is not independent of the invariant',
)


def _codes(contract: dict) -> set[str]:
    out = set()
    for row in contract.get('problems') or []:
        if isinstance(row, dict) and row.get('code'):
            out.add(str(row['code']))
    for row in contract.get('warnings') or []:
        out.add(str(row))
    for row in contract.get('advisories') or []:
        out.add(str(row))
    return out


def validate(contract: dict | None) -> dict:
    """Return a fail-closed strong-invariant validation record."""
    contract = contract if isinstance(contract, dict) else {}
    profile = contract.get('semantic_profile') or {}
    iv = contract.get('i_v') or {}
    restatement = contract.get('invariant_restatement') or {}
    reasons = []

    bucket = str(profile.get('bucket') or contract.get('semantic_bucket') or '')
    accepted = bool(restatement.get('accepted'))
    restated = str(restatement.get('status') or '') in {'restated', 'partial'}
    transition = bool(profile.get('has_before_after')) or bucket == 'transition'
    if bucket in _WEAK_BUCKETS and not (accepted and restated):
        reasons.append(f'invariant has weak semantic bucket: {bucket or "unknown"}')
    elif not transition and not (accepted and restated):
        reasons.append('invariant is not tied to a before/after transition')

    if contract.get('checkpoint_missing'):
        reasons.append('invariant symbols have no complete checkpoints')
    if contract.get('observable_missing'):
        reasons.append('invariant symbols have no observable route')
    if not iv.get('independent', True):
        reasons.append('violation is not independent of the invariant')

    codes = _codes(contract)
    weak_codes = sorted(codes & _WEAK_CODES)
    if weak_codes and not (accepted and restated):
        reasons.append('weak semantic codes remain: ' + ', '.join(weak_codes))

    return {
        'schema_version': SCHEMA_VERSION,
        'ok': not reasons,
        'bucket': bucket,
        'transition': transition,
        'restatement_accepted': accepted,
        'reasons': reasons,
    }


def assess(contract: dict | None) -> dict:
    """Split strong-invariant findings into hard failures and quality labels.

    A+ keeps checkpoints, observability and independence as hard requirements:
    without them no witness can be trusted.  Snapshot/restatement weak buckets
    become quality labels so a downstream witness can still decide whether the
    claim is useful.
    """
    result = validate(contract)
    hard = [reason for reason in result['reasons']
            if reason.startswith(_HARD_REASON_PREFIXES)]
    soft = [reason for reason in result['reasons'] if reason not in hard]
    return {
        'schema_version': 'stage3-strong-invariant-assess/1',
        'ok': not hard,
        'hard_reasons': hard,
        'soft_reasons': soft,
        'bucket': result['bucket'],
        'transition': result['transition'],
        'restatement_accepted': result['restatement_accepted'],
    }
