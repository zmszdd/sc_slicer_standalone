"""Report-only A+ invariant candidate extraction.

The module consumes the same report-derived artifacts as the existing Stage-2
pipeline.  It never reads source code and never calls a model: it turns the
already report-grounded P/I/V claim plus explicit intent statements into ranked
semantic invariant candidates, normalizes their natural-language checkpoints,
and carries weak-invariant labels forward instead of silently dropping them.
"""
from __future__ import annotations

SCHEMA_VERSION = 'report-invariant-candidates/1'

_BEFORE_WORDS = ('before', 'pre', 'prior', 'initial', 'entry', 'input')
_AFTER_WORDS = ('after', 'post', 'final', 'outcome', 'completion', 'result',
                'occurred', 'emitted')
_SOFT_CODES = {
    'I_SNAPSHOT_ONLY', 'I_SNAPSHOT_BARE_VAR', 'I_NOT_TRANSITION',
    'I_LAYER_MISMATCH', 'I_CHECKPOINT_COLLAPSED', 'I_V_POLARITY_ONLY',
    'I_V_RESTATEMENT', 'I_V_TAUTOLOGY', 'I_COPIED_FROM_P', 'I_ONLY_REUSES_P',
    'EFFECT_NOT_INDEPENDENT',
}


def _vars(node) -> set[str]:
    if not isinstance(node, dict):
        return set()
    if 'var' in node:
        return {str(node['var'])}
    found = set()
    for value in node.values():
        if isinstance(value, dict):
            found |= _vars(value)
        elif isinstance(value, list):
            for item in value:
                found |= _vars(item)
    return found


def normalize_checkpoint(value) -> str:
    """Map report prose checkpoints to a small, stable checkpoint vocabulary."""
    text = str(value or '').strip().lower()
    if not text:
        return 'missing'
    before = any(word in text for word in _BEFORE_WORDS)
    after = any(word in text for word in _AFTER_WORDS)
    if before and after:
        first = text.split(',')[0].split(' ')[0]
        if first in _BEFORE_WORDS:
            return 'before'
        if first in _AFTER_WORDS:
            return 'after'
        return 'transition'
    if before:
        return 'before'
    if after:
        return 'after'
    return 'snapshot'


def _statement_index(elements: dict) -> dict[str, dict]:
    return {row['id']: row for row in (elements or {}).get('statements', [])
            if isinstance(row, dict) and row.get('id')}


def _evidence_ids(statement: dict | None) -> list[str]:
    if not statement:
        return []
    return [quote for quote in (statement.get('evidence') or [])
            if isinstance(quote, str) and quote.strip()]


def _applicable_intent_ids(applicability: dict | None, impact_ids: list[str]) -> set[str]:
    if not isinstance(applicability, dict):
        return set()
    out = set()
    wanted = set(impact_ids)
    for row in applicability.get('impacts') or []:
        if not isinstance(row, dict):
            continue
        if wanted and row.get('impact_id') not in wanted:
            continue
        for value in row.get('intent_ids') or []:
            if isinstance(value, str):
                out.add(value)
    return out


def _checkpoints_for_claim(claim: dict, formal: dict, plan: dict | None) -> dict:
    safety = ((claim.get('properties') or {}).get('safety') or {}).get('expression')
    used = _vars(safety)
    symbols = (formal or {}).get('symbols') or {}
    raw = {}
    for name in sorted(used):
        meta = symbols.get(name) if isinstance(symbols, dict) else None
        if isinstance(meta, dict):
            raw[name] = meta.get('checkpoint')
    normalized = {name: normalize_checkpoint(value) for name, value in raw.items()}
    if plan is not None:
        for name, meta in ((plan.get('symbols') or {}).items()
                           if isinstance(plan.get('symbols'), dict) else []):
            if name in used and name not in normalized and isinstance(meta, dict):
                raw[name] = meta.get('checkpoint')
                normalized[name] = normalize_checkpoint(meta.get('checkpoint'))
    return {'raw': raw, 'normalized': normalized}


def _quality_labels(claim_id: str, weak_triage: dict | None,
                    checkpoints: dict) -> list[str]:
    row = ((weak_triage or {}).get('claims') or {}).get(claim_id) or {}
    labels = {str(item.get('code')) for item in (row.get('diagnostics') or [])
              if isinstance(item, dict) and item.get('code')}
    for bucket in row.get('buckets') or []:
        if bucket and bucket != 'unknown':
            labels.add('bucket:' + str(bucket))
    if any(value == 'snapshot' for value in checkpoints['normalized'].values()):
        labels.add('CHECKPOINT_SNAPSHOT_ONLY')
    if any(value == 'missing' for value in checkpoints['normalized'].values()):
        labels.add('CHECKPOINT_MISSING')
    return sorted(labels)


def _score(candidate: dict, has_before: bool, has_after: bool) -> float:
    score = 2.0 if candidate['executable'] else 0.0
    if candidate['derivation'] == 'explicit_report_intent':
        score += 1.0
    elif candidate['derivation'] == 'canonical_formalization':
        score += 0.5
    if has_before and has_after:
        score += 1.0
    elif has_before or has_after:
        score += 0.25
    score += min(len(candidate.get('evidence_ids') or []), 3) * 0.2
    score -= sum(0.4 for label in candidate.get('quality_labels', [])
                 if label in _SOFT_CODES or label.startswith('bucket:'))
    return round(score, 4)


def build(elements: dict | None, formal: dict | None, *,
          weak_triage: dict | None = None,
          applicability: dict | None = None,
          plans: dict | None = None) -> dict:
    """Build ranked report-only invariant candidates for every formal claim."""
    elements = elements if isinstance(elements, dict) else {}
    formal = formal if isinstance(formal, dict) else {}
    statements = _statement_index(elements)
    intent_statements = [row for row in statements.values()
                         if row.get('kind') == 'security_intent']
    claims = {}
    for claim in formal.get('claims') or []:
        if not isinstance(claim, dict) or not claim.get('id'):
            continue
        claim_id = str(claim['id'])
        plan = (plans or {}).get(claim_id) if isinstance(plans, dict) else None
        impact_ids = [str(value) for value in claim.get('impact_ids') or []]
        safety = ((claim.get('properties') or {}).get('safety') or {})
        checkpoints = _checkpoints_for_claim(claim, formal, plan)
        labels = _quality_labels(claim_id, weak_triage, checkpoints)
        canonical_intent = str((plan or {}).get('intent_id') or '')
        canonical = {
            'candidate_id': claim_id + '::canonical',
            'text': safety.get('text') or '',
            'expression': safety.get('expression'),
            'derivation': 'canonical_formalization',
            'source_ids': [canonical_intent] if canonical_intent else [],
            'evidence_ids': _evidence_ids(statements.get(canonical_intent)),
            'checkpoints': checkpoints,
            'quality_labels': labels,
            'executable': safety.get('expression') is not None,
        }
        candidates = [canonical]
        allowed = _applicable_intent_ids(applicability, impact_ids)
        for statement in intent_statements:
            statement_id = str(statement['id'])
            if statement_id == canonical_intent:
                continue
            if allowed and statement_id not in allowed:
                continue
            candidate_checkpoints = {
                'raw': {},
                'normalized': {'report_level': normalize_checkpoint(
                    statement.get('text'))},
            }
            candidates.append({
                'candidate_id': claim_id + '::' + statement_id,
                'text': statement.get('text') or '',
                'expression': None,
                'derivation': 'explicit_report_intent',
                'source_ids': [statement_id],
                'evidence_ids': _evidence_ids(statement),
                'checkpoints': candidate_checkpoints,
                'quality_labels': ['CANDIDATE_ONLY'],
                'executable': False,
            })
        for candidate in candidates:
            values = set(candidate['checkpoints']['normalized'].values())
            candidate['score'] = _score(
                candidate, 'before' in values or 'transition' in values,
                'after' in values or 'transition' in values)
        ranked = sorted(candidates, key=lambda row: (-row['score'],
                                                     row['candidate_id']))
        claims[claim_id] = {
            'impact_ids': impact_ids,
            'canonical_candidate_id': canonical['candidate_id'],
            'selected_candidate_id': ranked[0]['candidate_id'],
            'candidates': ranked,
        }
    return {
        'schema_version': SCHEMA_VERSION,
        'source_policy': 'report-only',
        'claims': claims,
    }
