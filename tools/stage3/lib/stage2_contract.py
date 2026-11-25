"""Deterministic enforcement of the Stage-2 formalization contract.

Stage 2 writes ``formalization-contract.json`` to describe whether a claim may
be auto-asserted in Stage 3.  Historically Stage 3 copied that record into the
execution contract but continued into binding/forge for every route.  This
module turns the record into a fail-closed handoff decision.

The decision is deliberately conservative:

* ``auto_assert`` is the only route allowed to continue automatically;
* ``stage2_repair`` and ``rejected`` claims stop before binding;
* ``binding_review`` and ``reference_patch_candidate`` stop before forge and
  remain explicit unresolved outcomes;
* a missing contract is kept as a legacy diagnostic rather than silently
  pretending the claim was reviewed.
"""
from __future__ import annotations

import json
from pathlib import Path

SCHEMA_VERSION = 'stage3-stage2-contract-gate/1'

AUTO_ASSERT = 'auto_assert'
BINDING_REVIEW = 'binding_review'
STAGE2_REPAIR = 'stage2_repair'
REFERENCE_PATCH = 'reference_patch_candidate'
NEGATIVE_WITNESS = 'negative_witness'
LEGACY_MISSING = 'legacy_missing'

_BLOCKING_ROUTES = {
    BINDING_REVIEW: 'stage2_review_required',
    STAGE2_REPAIR: 'stage2_repair_required',
    REFERENCE_PATCH: 'stage2_reference_patch_candidate',
}

_RESTATEMENT_CODES = {
    'EFFECT_NOT_INDEPENDENT', 'I_V_POLARITY_ONLY', 'I_V_RESTATEMENT',
    'I_V_TAUTOLOGY', 'I_COPIED_FROM_P', 'I_ONLY_REUSES_P',
    # Single-snapshot invariants are not a transition witness.  They must be
    # restated (or explicitly reviewed) before stage 3 may inject ``I``.
    'I_SNAPSHOT_ONLY', 'I_SNAPSHOT_BARE_VAR',
    'I_CHECKPOINT_COLLAPSED', 'I_LAYER_MISMATCH',
}
_SOFT_LABEL_CODES = _RESTATEMENT_CODES | {
    'EFFECT_NOT_INDEPENDENT', 'I_IMPLIED_BY_P',
    'OBSERVABILITY_HIGH_RISK', 'OBSERVABILITY_REQUIRES_CODE_FACT',
    'I_MUTATION_SITE_MISSING', 'I_SAME_CHECKPOINT_ONLY',
    'I_NOT_TRANSITION',
}


def load(stage2_dir: Path, claim_id: str) -> dict:
    """Load one claim's formalization contract, if the file exists."""
    path = Path(stage2_dir) / 'formalization-contract.json'
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return {}
    claims = payload.get('claims') or {}
    if isinstance(claims, list):
        for row in claims:
            if isinstance(row, dict) and row.get('claim_id') == claim_id:
                return row
        return {}
    if isinstance(claims, dict):
        row = claims.get(claim_id)
        return row if isinstance(row, dict) else {}
    return {}


def decide(contract: dict | None, *, strict: bool = False,
           mode: str | None = None) -> dict:
    """Return a fail-closed routing decision for one contract record."""
    aplus = mode == 'aplus'
    contract = contract if isinstance(contract, dict) else {}
    if not contract:
        return {
            'schema_version': SCHEMA_VERSION,
            'status': 'missing',
            'route': LEGACY_MISSING,
            'category': None,
            'blocking': False,
            'auto_assert_allowed': False,
            'reason': ('no formalization-contract.json claim record; legacy '
                       'run remains diagnostic and cannot establish a current '
                       'auto-assert result'),
        }

    if (str(contract.get('route') or '') == NEGATIVE_WITNESS
            or (contract.get('negative_witness_route') or {}).get('eligible')):
        return {
            'schema_version': SCHEMA_VERSION,
            'status': str(contract.get('status') or 'negative_witness'),
            'route': NEGATIVE_WITNESS,
            'semantic_route': 'negative_witness',
            'category': None,
            'blocking': False,
            'auto_assert_allowed': False,
            'can_auto_assert': False,
            'reason': ('trusted negative label routes to the negative '
                       'witness harness; vulnerability eligibility stays off'),
            'problems': list(contract.get('problems') or []),
            'warnings': list(contract.get('warnings') or []),
            'i_v': dict(contract.get('i_v') or {}),
            'strong_invariant': None,
        }

    route = str(contract.get('route') or '').strip() or AUTO_ASSERT
    original_route = route
    status = str(contract.get('status') or '').strip()
    can_auto = contract.get('can_auto_assert')
    if can_auto is None:
        can_auto = status == 'ready' and route == AUTO_ASSERT
    can_auto = bool(can_auto)

    if status == 'rejected' or route == STAGE2_REPAIR:
        route = STAGE2_REPAIR
    elif route not in _BLOCKING_ROUTES and route != AUTO_ASSERT:
        # Unknown future routes must not silently gain auto-assert authority.
        route = BINDING_REVIEW

    codes = {
        str(row.get('code')) for row in (contract.get('problems') or [])
        if isinstance(row, dict) and row.get('code')}
    codes |= {str(code) for code in (contract.get('warnings') or [])}
    quality_labels = []
    if (aplus and original_route == BINDING_REVIEW
            and codes <= _SOFT_LABEL_CODES):
        route = AUTO_ASSERT
        can_auto = True
        quality_labels.extend(sorted(codes))
    semantic_route = None
    if aplus and codes & _RESTATEMENT_CODES:
        quality_labels.extend(sorted(codes & _RESTATEMENT_CODES))
        semantic_route = 'stage2_quality_label'
    elif codes & _RESTATEMENT_CODES:
        semantic_route = 'stage2_restatement'
    elif route == REFERENCE_PATCH:
        semantic_route = 'reference_patch'
    elif route == STAGE2_REPAIR:
        semantic_route = 'stage2_repair'
    blocking = (route != AUTO_ASSERT or not can_auto
                or (not aplus and semantic_route == 'stage2_restatement'))
    if route == AUTO_ASSERT and can_auto and semantic_route != 'stage2_restatement':
        category = None
        reason = 'formalization contract permits automatic assertion'
    elif semantic_route == 'stage2_restatement':
        category = 'stage2_restatement_required'
        reason = ('formalization contract contains a semantic review code; '
                  'restate the claim before automatic assertion')
    elif route in _BLOCKING_ROUTES:
        category = _BLOCKING_ROUTES[route]
        reason = f'formalization contract route {route!r} requires review'
    else:
        category = 'stage2_review_required'
        reason = 'formalization contract does not permit automatic assertion'

    strong_invariant = None
    if aplus:
        from lib import strong_invariant as strong_invariant_lib

        strong_invariant = strong_invariant_lib.assess(contract)
        quality_labels.extend(strong_invariant['soft_reasons'])
        if strong_invariant['soft_reasons'] and not semantic_route:
            semantic_route = 'stage2_quality_label'
        if not strong_invariant['ok']:
            blocking = True
            semantic_route = 'stage2_strong_invariant_required'
            category = 'stage2_strong_invariant_required'
            reason = ('strong invariant contract failed hard requirements: '
                      + '; '.join(strong_invariant['hard_reasons']))
    elif strict:
        from lib import strong_invariant as strong_invariant_lib

        strong_invariant = strong_invariant_lib.validate(contract)
        if not strong_invariant['ok']:
            blocking = True
            semantic_route = 'stage2_restatement'
            category = 'stage2_strong_invariant_required'
            reason = ('strong invariant contract failed: '
                      + '; '.join(strong_invariant['reasons']))

    return {
        'schema_version': SCHEMA_VERSION,
        'status': status or 'unknown',
        'route': route,
        'semantic_route': semantic_route,
        'category': category,
        'blocking': blocking,
        'auto_assert_allowed': bool(
            route == AUTO_ASSERT and can_auto and not blocking),
        'can_auto_assert': can_auto,
        'reason': reason,
        'problems': list(contract.get('problems') or []),
        'warnings': list(contract.get('warnings') or []),
        'i_v': dict(contract.get('i_v') or {}),
        'strong_invariant': strong_invariant,
        'quality_labels': sorted(set(quality_labels)),
        'gate_mode': 'aplus' if aplus else 'strict' if strict else 'legacy',
    }


def summary(claim_id: str, decision: dict, contract: dict | None = None) -> dict:
    """Build the early-exit summary used by ``stage3_pipeline``."""
    return {
        'schema_version': 'stage3-run-summary/1',
        'claim_id': claim_id,
        'consistency_verdict': decision['category'],
        'stage2_contract_gate': decision,
        'execution_contract': {'stage2_contract': contract or {}},
        'witness': {
            'schema_version': 'stage3-witness-protocol/1',
            'claim_id': claim_id,
            'status': 'unavailable',
            'failure_code': decision['category'],
            'reason': decision['reason'],
            'effect_witnessed': False,
            'invariant_contradicted': False,
            'invariant_held': None,
            'queries': {},
        },
    }
