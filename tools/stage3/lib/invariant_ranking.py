"""Rank Stage-3 claims with report-only A+ invariant evidence.

The ranking is deliberately advisory: it changes execution order/count, not the
Stage-2 verdict or the binding contract.  It uses no source code and no model.
"""
from __future__ import annotations

import json
from pathlib import Path

SCHEMA_VERSION = 'stage3-invariant-ranking/1'

_SOFT_CODES = {
    'I_SNAPSHOT_ONLY', 'I_SNAPSHOT_BARE_VAR', 'I_NOT_TRANSITION',
    'I_LAYER_MISMATCH', 'I_CHECKPOINT_COLLAPSED', 'I_V_POLARITY_ONLY',
    'I_V_RESTATEMENT', 'I_V_TAUTOLOGY', 'I_COPIED_FROM_P', 'I_ONLY_REUSES_P',
    'EFFECT_NOT_INDEPENDENT', 'stage2_review_required',
}


def _load_candidates(stage2_dir: Path) -> dict:
    path = Path(stage2_dir) / 'invariant-candidates.json'
    try:
        payload = json.loads(path.read_text())
    except (OSError, ValueError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _codes(contract: dict) -> set[str]:
    out = set()
    for row in contract.get('problems') or []:
        if isinstance(row, dict) and row.get('code'):
            out.add(str(row['code']))
    for row in contract.get('warnings') or []:
        out.add(str(row) if isinstance(row, str) else str(row.get('code', '')))
    return {code for code in out if code}


def _contract_score(contract: dict) -> tuple[float, list[str]]:
    contract = contract if isinstance(contract, dict) else {}
    profile = contract.get('semantic_profile') or {}
    iv = contract.get('i_v') or {}
    restatement = contract.get('invariant_restatement') or {}
    labels = sorted(_codes(contract))
    score = 0.0
    if contract.get('route') == 'auto_assert':
        score += 2.0
    if contract.get('can_auto_assert'):
        score += 1.0
    if profile.get('has_before_after') or profile.get('bucket') == 'transition':
        score += 2.0
    if restatement.get('accepted'):
        score += 1.0
    if iv.get('independent', True):
        score += 1.0
    score -= 0.5 * sum(code in _SOFT_CODES for code in labels)
    return score, labels


def rank_claims(stage2_dir: Path, spec: dict, *, limit: int = 0) -> dict:
    """Return ranked claim ids and the evidence used for the ordering."""
    claims = [row for row in (spec or {}).get('claims', [])
              if isinstance(row, dict) and row.get('claim_id')]
    candidates = _load_candidates(stage2_dir)
    candidate_index = candidates.get('claims') or {}
    rows = []
    for claim in claims:
        claim_id = str(claim['claim_id'])
        contract = claim.get('formalization_contract') or {}
        score, labels = _contract_score(contract)
        reasons = ['contract_score=' + str(round(score, 4))]
        candidate = (candidate_index.get(claim_id) or {}) if isinstance(
            candidate_index, dict) else {}
        selected_id = candidate.get('selected_candidate_id')
        selected = next((row for row in candidate.get('candidates') or []
                         if isinstance(row, dict)
                         and row.get('candidate_id') == selected_id), None)
        if selected:
            score += 0.1 * float(selected.get('score') or 0.0)
            reasons.append('candidate_score=' + str(selected.get('score')))
            if selected.get('derivation') == 'explicit_report_intent':
                reasons.append('explicit_report_intent')
        rows.append({
            'claim_id': claim_id,
            'score': round(score, 4),
            'quality_labels': sorted(set(labels + list(
                selected.get('quality_labels') or [] if selected else []))),
            'selected_candidate_id': selected_id,
            'reasons': reasons,
        })
    rows.sort(key=lambda row: (-row['score'], row['claim_id']))
    selected = rows if limit <= 0 else rows[:limit]
    return {
        'schema_version': SCHEMA_VERSION,
        'limit': limit,
        'ranked': rows,
        'selected': selected,
        'selected_claim_ids': [row['claim_id'] for row in selected],
    }
