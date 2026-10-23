"""Deterministic helpers for grounded P/I/V claims and impact/I source pairs."""
import copy
import hashlib

from lib.piv_contract import PIV_PROPERTY_BY_SYMBOL
from lib.semantic_core import require


def claim_id_for_impact(impact_id):
    digest = hashlib.sha256(impact_id.encode()).hexdigest()[:8]
    prefix = ''.join(ch if ch.isalnum() or ch == '_' else '_' for ch in impact_id)
    prefix = prefix.strip('_')[:42] or 'impact'
    return f'impact_claim_{prefix}_{digest}'


def claim_id_for_impact_intent(impact_id, intent_id):
    """Return a stable ID for one independent (Impact, I-source) claim."""
    impact_hash = hashlib.sha256(impact_id.encode()).hexdigest()[:8]
    intent_hash = hashlib.sha256(intent_id.encode()).hexdigest()[:8]
    prefix = ''.join(ch if ch.isalnum() or ch == '_' else '_'
                     for ch in impact_id).strip('_')[:27] or 'impact'
    return f'impact_claim_{prefix}_{impact_hash}_{intent_hash}'


def impact_intent_key(impact_id, intent_id):
    """Human-readable stable key for per-(Impact, I source) audit records."""
    return f'{impact_id}::{intent_id}'


def unformalized_claim(elements, impact_id, reason):
    """Preserve a failed impact as a reviewable claim disposition."""
    statements = {row['id']: row for row in elements['statements']}
    impact = statements[impact_id]
    intents = [row for row in elements['statements']
               if row['kind'] == 'security_intent']
    preconditions = [row for row in elements['statements']
                     if row['kind'] in ('precondition', 'assumption')]
    p_sources = [row['id'] for row in preconditions]
    i_sources = [row['id'] for row in intents]
    properties = {
        PIV_PROPERTY_BY_SYMBOL['P']: {
            'text': '; '.join(row['text'] for row in preconditions) or '未提取到可用前提',
            'expression': None,
            'evidence_ids': list(dict.fromkeys(
                q for row in preconditions for q in row.get('evidence_ids', row.get('evidence', [])))),
            'derivation': '未能生成忠实的形式化前提。',
            'source_ids': p_sources,
        },
        PIV_PROPERTY_BY_SYMBOL['I']: {
            'text': '; '.join(row['text'] for row in intents) or '未提取到安全性质',
            'expression': None,
            'evidence_ids': list(dict.fromkeys(
                q for row in intents for q in row.get('evidence_ids', row.get('evidence', [])))),
            'derivation': '未能为该影响生成忠实的安全关系。',
            'source_ids': i_sources,
        },
        PIV_PROPERTY_BY_SYMBOL['V']: {
            'text': impact['text'], 'expression': None,
            'evidence_ids': list(impact.get('evidence_ids', impact.get('evidence', []))),
            'derivation': '该影响保留在覆盖清单中，但未生成形式化谓词。',
            'source_ids': [impact_id],
        },
    }
    return {
        'id': claim_id_for_impact(impact_id),
        'scope': elements['scope']['flow'],
        'modality': impact['modality'],
        'impact_ids': [impact_id],
        'properties': properties,
        'formula_sources': {name: {} for name in PIV_PROPERTY_BY_SYMBOL.values()},
        'effect_coverage': [{'statement_id': impact_id, 'status': 'unformalized',
                             'reason': reason}],
        'assumptions': [],
        'unresolved': [reason],
    }


def _namespace_expression(value, mapping):
    if isinstance(value, list):
        return [_namespace_expression(item, mapping) for item in value]
    if not isinstance(value, dict):
        return value
    if set(value) == {'var'}:
        return {'var': mapping[value['var']]}
    return {key: _namespace_expression(item, mapping) for key, item in value.items()}


def namespace_formalization(formal, claim_id):
    """Give each isolated P/I/V plan private symbols while preserving its AST."""
    formal = copy.deepcopy(formal)
    require(len(formal['claims']) == 1, 'per-impact plan must synthesize one claim')
    prefix = 'c' + hashlib.sha256(claim_id.encode()).hexdigest()[:8] + '_'
    mapping = {name: prefix + name[:64 - len(prefix)] for name in formal['symbols']}
    symbols = {mapping[name]: value for name, value in formal['symbols'].items()}
    claim = formal['claims'][0]
    claim['id'] = claim_id
    for prop in claim['properties'].values():
        prop['expression'] = _namespace_expression(prop['expression'], mapping)
    formal['symbols'] = symbols
    return formal


def merge_claim_formalizations(successful, elements, failures=(), *,
                               include_failed_claims=True):
    """Merge isolated per-impact formalizations.

    ``include_failed_claims`` preserves the historical bookkeeping claim
    format for replay. New live runs can omit failed impacts from the rule
    bundle while keeping their dispositions in the plan/status artifacts.
    """
    successful = list(successful)
    failures = list(failures)
    pair_mode = any(len(row) == 3 for row in successful + failures)
    claims, symbols, limitations = [], {}, []
    represented_pairs = set()
    for row in successful:
        if pair_mode:
            require(len(row) == 3, 'mixed impact and impact/I formalization records')
            impact_id, intent_id, formal = row
            claim_id = claim_id_for_impact_intent(impact_id, intent_id)
            require((impact_id, intent_id) not in represented_pairs,
                    'duplicate Impact/I formalization')
            represented_pairs.add((impact_id, intent_id))
            claim = formal['claims'][0]
            require(claim['properties']['safety']['source_ids'] == [intent_id] and
                    claim['properties']['effects']['source_ids'] == [impact_id],
                    'Impact/I claim changed its frozen I or V source')
        else:
            impact_id, formal = row
            claim_id = claim_id_for_impact(impact_id)
        private = namespace_formalization(formal, claim_id)
        claims.extend(private['claims'])
        overlap = set(symbols) & set(private['symbols'])
        require(not overlap, 'namespaced claim symbols collided')
        symbols.update(private['symbols'])
        limitations.extend(item for item in private['limitations']
                           if not item.startswith('Deferred report impact:'))
    if pair_mode:
        for row in failures:
            require(len(row) == 3, 'mixed impact and impact/I failure records')
            impact_id, intent_id, reason = row
            if intent_id is not None:
                statements = {item['id']: item for item in elements['statements']}
                require(intent_id in statements and
                        statements[intent_id]['kind'] == 'security_intent',
                        'Impact/I failure names an invalid I source')
                require((impact_id, intent_id) not in represented_pairs,
                        'Impact/I source both succeeded and failed')
                represented_pairs.add((impact_id, intent_id))
            limitations.append(f'{impact_id}' +
                               (f'/{intent_id}' if intent_id else '') +
                               f': {reason}')
        require(len(represented_pairs) == len(set(represented_pairs)),
                'duplicate Impact/I disposition')
    else:
        for impact_id, reason in failures:
            if include_failed_claims:
                claims.append(unformalized_claim(elements, impact_id, reason))
            limitations.append(f'{impact_id}: {reason}')
        represented = [impact_id for claim in claims for impact_id in claim['impact_ids']]
        expected = [row['id'] for row in elements['statements']
                    if row['kind'] == 'impact']
        failed_ids = {impact_id for impact_id, _ in failures}
        expected_claims = expected if include_failed_claims else [
            impact_id for impact_id in expected if impact_id not in failed_ids]
        require(sorted(represented) == sorted(expected_claims),
                'each included impact must have exactly one claim disposition')
        require(len(represented) == len(set(represented)),
                'an impact is assigned to multiple claims')
    claims.sort(key=lambda row: (row['impact_ids'][0], row['id']))
    return {'schema_version': 'report-formalization/2', 'symbols': symbols,
            'claims': claims, 'limitations': list(dict.fromkeys(limitations))}


def apply_multi_intent_coverage(bundle, applicability, plan_records, *,
                                require_fidelity=False):
    """Summarize generated rules and, when configured, their fidelity verdicts."""
    records = {(row.get('impact_id'), row.get('intent_id')): row
               for row in plan_records if row.get('intent_id')}
    compiled = {row['id']: row for row in bundle.get('claims', [])}
    coverage = {row['impact_id']: row
                for row in bundle.get('report_impact_coverage', [])}
    incomplete_selected_impacts = []
    for selected in applicability.get('impacts', []):
        impact_id = selected['impact_id']
        if selected['status'] != 'selected':
            continue
        pairs = [(impact_id, intent_id) for intent_id in selected['intent_ids']]
        passed, generated, reasons, claim_ids = [], [], [], []
        for pair in pairs:
            record = records.get(pair)
            claim_id = claim_id_for_impact_intent(*pair)
            claim = compiled.get(claim_id)
            claim_coverage = next((row for row in (claim or {}).get(
                'effect_coverage', []) if row.get('statement_id') == impact_id), None)
            is_generated = bool(
                record and record.get('status') == 'formalized_candidate' and
                claim)
            fidelity_passed = (not require_fidelity or bool(
                record and record.get('fidelity_status') == 'passed'))
            is_formalized = is_generated and fidelity_passed
            generated.append(is_generated)
            passed.append(is_formalized)
            if is_formalized:
                claim_ids.append(claim_id)
            elif is_generated and require_fidelity:
                reasons.append('post-generation P/I/V fidelity audit ' +
                               str(record.get('fidelity_status', 'unavailable')))
            else:
                reasons.append((record or {}).get('reason') or
                               (claim_coverage or {}).get('reason') or
                               f'No complete rule was produced for I source {pair[1]}.')
        row = coverage.get(impact_id)
        if row is None:
            row = {'impact_id': impact_id, 'evidence': [], 'claim_ids': [],
                   'status': 'unformalized', 'reason': ''}
            bundle.setdefault('report_impact_coverage', []).append(row)
            coverage[impact_id] = row
        row['claim_ids'] = sorted(claim_ids)
        row['generated_rule_count'] = sum(generated)
        row['selected_i_source_count'] = len(pairs)
        if passed and all(passed):
            row['status'] = 'formalized'
        elif any(passed):
            row['status'] = 'partial'
        elif require_fidelity and generated and all(generated):
            row['status'] = 'fidelity_failed'
        elif any(generated):
            row['status'] = 'partial'
        else:
            row['status'] = 'unformalized'
        row['reason'] = ('All selected I-source rules were formalized.'
                         if row['status'] == 'formalized' else
                         '; '.join(dict.fromkeys(reasons)))
        if row['status'] != 'formalized':
            incomplete_selected_impacts.append(impact_id)
    bundle['report_impact_coverage'].sort(key=lambda row: row['impact_id'])
    if incomplete_selected_impacts:
        bundle['core_formalization_status'] = 'partial'
        if bundle.get('acceptance_status') == 'candidate_checks_passed':
            bundle['acceptance_status'] = 'needs_review'
        bundle.setdefault('report_warnings', []).append(
            'selected I-source rules are incomplete for Impact(s): ' +
            ', '.join(sorted(incomplete_selected_impacts)))
    return bundle
