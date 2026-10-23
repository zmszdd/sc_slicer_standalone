"""Build an auditable, source-scoped input card for one explicit Impact."""
import copy

from lib.plan_synthesizer import impact_qualifier_types


SCHEMA_VERSION = 'stage2-impact-semantic-card/1'
APPLICABILITY_SCHEMA_VERSION = 'stage2-impact-applicability/1'
# The compiled report-formalization schema accepts at most 64 claims. In the
# multi-I pipeline each selected (Impact, I source) becomes one independent
# claim, so reject an oversized selection before spending calls on rules.
MAX_SELECTED_INTENT_RULES = 64


def validate_applicability(raw, elements):
    """Validate a report-level selection of explicit P/I sources per Impact."""
    if not isinstance(raw, dict) or raw.get('schema_version') != APPLICABILITY_SCHEMA_VERSION:
        raise ValueError('invalid Impact applicability schema')
    impacts = {row['id']: row for row in elements.get('statements', [])
               if row.get('kind') == 'impact'}
    statements = {row['id']: row for row in elements.get('statements', [])}
    rows = raw.get('impacts')
    if not isinstance(rows, list) or len(rows) != len(impacts):
        raise ValueError('Impact applicability must cover every Impact exactly once')
    seen = set()
    validated = []
    for row in rows:
        if not isinstance(row, dict) or set(row) != {
                'impact_id', 'status', 'precondition_ids', 'intent_ids', 'reason'}:
            raise ValueError('invalid Impact applicability entry')
        impact_id = row['impact_id']
        if impact_id not in impacts or impact_id in seen:
            raise ValueError('unknown or duplicate applicability Impact ID')
        seen.add(impact_id)
        status = row['status']
        p_ids, i_ids = row['precondition_ids'], row['intent_ids']
        if status not in ('selected', 'explicit_but_insufficient', 'needs_review'):
            raise ValueError('invalid Impact applicability status')
        if not isinstance(p_ids, list) or not isinstance(i_ids, list):
            raise ValueError('applicability source IDs must be arrays')
        if len(set(p_ids)) != len(p_ids) or len(set(i_ids)) != len(i_ids):
            raise ValueError('duplicate applicability source ID')
        for source_id in p_ids:
            source = statements.get(source_id)
            if (source is None or source.get('kind') not in ('precondition', 'assumption')
                    or not source.get('evidence_ids', source.get('evidence'))):
                raise ValueError('P source is not an evidence-backed precondition/assumption')
        for source_id in i_ids:
            source = statements.get(source_id)
            if (source is None or source.get('kind') != 'security_intent' or
                    source.get('modality') not in ('asserted', 'potential') or
                    not source.get('evidence_ids', source.get('evidence'))):
                raise ValueError('I source is not an explicit evidence-backed intent')
        if status == 'selected' and not i_ids:
            raise ValueError('selected applicability requires at least one explicit I source')
        if status != 'selected' and (p_ids or i_ids):
            raise ValueError('unresolved applicability cannot select P/I sources')
        if (not isinstance(row['reason'], str) or not row['reason'].strip() or
                len(row['reason']) > 1000 or '\n' in row['reason'] or
                '\r' in row['reason']):
            raise ValueError('applicability reason is required')
        validated.append({key: row[key] for key in (
            'impact_id', 'status', 'precondition_ids', 'intent_ids', 'reason')})
    if seen != set(impacts):
        raise ValueError('Impact applicability does not match the Impact inventory')
    selected_pair_count = sum(
        len(row['intent_ids']) for row in validated
        if row['status'] == 'selected')
    if selected_pair_count > MAX_SELECTED_INTENT_RULES:
        raise ValueError(
            'Impact applicability selects more than '
            f'{MAX_SELECTED_INTENT_RULES} independent I-source rules')
    return {'schema_version': APPLICABILITY_SCHEMA_VERSION, 'impacts': validated}


def applicability_by_impact(validated):
    return {row['impact_id']: row for row in validated['impacts']}


def applicability_payload(elements, catalog=None):
    """Minimal report element view used for applicability judgment and replay."""
    impacts = [row for row in elements.get('statements', [])
               if row.get('kind') == 'impact']
    p_sources = [row for row in elements.get('statements', [])
                 if row.get('kind') in ('precondition', 'assumption') and
                 row.get('evidence_ids', row.get('evidence'))]
    i_sources = [row for row in elements.get('statements', [])
                 if row.get('kind') == 'security_intent' and
                 row.get('modality') in ('asserted', 'potential') and
                 row.get('evidence_ids', row.get('evidence'))]
    payload = {
        'impacts': [{key: row.get(key) for key in
                     ('id', 'text', 'modality', 'evidence_ids')}
                    for row in impacts],
        'precondition_candidates': [{key: row.get(key) for key in
                                     ('id', 'kind', 'text', 'evidence_ids')}
                                    for row in p_sources],
        'explicit_intent_candidates': [{key: row.get(key) for key in
                                       ('id', 'text', 'modality', 'evidence_ids')}
                                      for row in i_sources],
    }
    if catalog is not None:
        allowed_evidence = {evidence_id for section in
                            ('impacts', 'precondition_candidates',
                             'explicit_intent_candidates')
                            for row in payload[section]
                            for evidence_id in row.get('evidence_ids', [])}
        payload['evidence_fragments'] = [
            {'id': row['id'], 'text': row['text']}
            for row in catalog.get('fragments', [])
            if row.get('id') in allowed_evidence]
    return payload


def build_impact_card(elements, impact_id, applicability=None, intent_id=None):
    """Project one Impact and its report-grounded P/I candidates into a card.

    This is a deterministic scope/evidence index, not a semantic judgment. It
    deliberately does not claim that the available statements are sufficient
    for a faithful formula.
    """
    statements = {row['id']: row for row in elements.get('statements', [])}
    impact = statements.get(impact_id)
    if impact is None or impact.get('kind') != 'impact':
        raise ValueError('semantic card requires a selected Impact statement')

    selected = (applicability_by_impact(applicability).get(impact_id)
                if applicability else None)
    selected_p = set(selected['precondition_ids']) if selected else None
    selected_i = set(selected['intent_ids']) if selected else None
    if intent_id is not None:
        if selected_i is None or intent_id not in selected_i:
            raise ValueError('target I source is not selected for this Impact')
        selected_i = {intent_id}

    def source_rows(kinds):
        return [{key: row.get(key) for key in
                 ('id', 'kind', 'text', 'modality', 'evidence_ids')}
                for row in elements.get('statements', [])
                if row.get('kind') in kinds and
                (applicability is None or
                 row.get('evidence_ids', row.get('evidence'))) and
                (selected_p is None or row.get('id') in selected_p)]

    eligible_intents = [row for row in elements.get('statements', [])
                        if row.get('kind') == 'security_intent' and
                        row.get('modality') in ('asserted', 'potential') and
                        row.get('evidence_ids', row.get('evidence')) and
                        (selected_i is None or row.get('id') in selected_i)]
    excluded_intents = [row['id'] for row in elements.get('statements', [])
                        if row.get('kind') == 'security_intent' and
                        (row.get('modality') not in ('asserted', 'potential') or
                         not row.get('evidence_ids', row.get('evidence')))]
    if applicability is None:
        excluded_intents = [row['id'] for row in elements.get('statements', [])
                            if row.get('kind') == 'security_intent' and
                            row not in eligible_intents]
    card = {
        'schema_version': SCHEMA_VERSION,
        'impact': {key: impact.get(key) for key in
                   ('id', 'text', 'modality', 'evidence_ids')},
        'impact_qualifier_types': impact_qualifier_types(impact['text']),
        'precondition_sources': source_rows({'precondition', 'assumption'}),
        'intent_sources': [{key: row.get(key) for key in
                            ('id', 'kind', 'text', 'modality', 'evidence_ids')}
                           for row in eligible_intents],
        'excluded_inferred_intent_ids': excluded_intents,
        'formalizability': {
            'status': (selected['status'] if selected else
                       ('not_assessed' if eligible_intents else
                        'explicit_but_insufficient')),
            'reason': ('The explicit P/I source selection is recorded; formula validity '
                       'remains unassessed.' if selected and selected['status'] == 'selected'
                       else 'Applicability is unresolved; do not formalize this Impact.'
                       if selected else
                       ('Applicability has not been assessed.' if eligible_intents else
                        'No report-supported, non-inferred security intent is available.')),
        },
        'rules': [
            'Only the selected impact may supply V.',
            'Use a P or I source only when its cited report evidence supports it.',
            'Do not infer a desired safety relation or add an impact from other sections.',
            'If the report does not support a complete P/I/V relation, leave this impact pending.',
        ],
    }
    if applicability is not None:
        card['formalizability']['applicability'] = {
            key: selected[key] for key in
            ('impact_id', 'status', 'precondition_ids', 'intent_ids')}
        if intent_id is not None:
            card['formalizability']['applicability']['intent_ids'] = [intent_id]
    return card


def explicit_intent_ids(elements):
    """Return report-asserted or report-potential intents; exclude inferred ones."""
    return [row['id'] for row in elements.get('statements', [])
            if row.get('kind') == 'security_intent' and
            row.get('modality') in ('asserted', 'potential') and
            row.get('evidence_ids', row.get('evidence'))]


def target_elements(elements, impact_id, card=None):
    """Restrict a formalization request to one Impact and explicit I sources."""
    value = copy.deepcopy(elements)
    intents = set(explicit_intent_ids(elements))
    selected_p = ({row['id'] for row in card.get('precondition_sources', [])}
                  if card else None)
    selected_i = ({row['id'] for row in card.get('intent_sources', [])}
                  if card else None)
    value['statements'] = [
        row for row in value.get('statements', [])
        if row.get('kind') != 'impact' or row.get('id') == impact_id
    ]
    value['statements'] = [
        row for row in value['statements']
        if row.get('kind') != 'security_intent' or
        (row.get('id') in intents and
         (selected_i is None or row.get('id') in selected_i))
    ]
    if selected_p is not None:
        value['statements'] = [row for row in value['statements']
                               if row.get('kind') not in ('precondition', 'assumption')
                               or row.get('id') in selected_p]
    if card is None:
        return value
    selected_statement_ids = {impact_id} | selected_p | selected_i
    value['statements'] = [row for row in value['statements']
                           if row.get('id') in selected_statement_ids]
    value['ambiguities'] = []
    if 'flow' in value.get('scope', {}):
        # The compiled claim requires a nonempty scope. Reuse only the target
        # Impact's own wording so no report-wide flow narrative leaks forward.
        value['scope']['flow'] = card['impact'].get('text', '')
    if 'environment' in value.get('scope', {}):
        value['scope']['environment'] = ''
    used_entities = {entity_id for row in value['statements']
                     for entity_id in row.get('entity_ids', [])}
    value['entities'] = [row for row in value.get('entities', [])
                         if row.get('id') in used_entities]
    selected_evidence = {evidence_id for row in value['statements']
                         for evidence_id in row.get('evidence_ids', row.get('evidence', []))}
    selected_evidence = set(card['impact'].get('evidence_ids', []))
    selected_evidence.update(evidence_id for source in
                             card.get('precondition_sources', []) +
                             card.get('intent_sources', [])
                             for evidence_id in source.get('evidence_ids', []))
    for row in value['entities']:
        evidence_key = 'evidence_ids' if 'evidence_ids' in row else 'evidence'
        if evidence_key in row:
            row[evidence_key] = [evidence_id for evidence_id in row[evidence_key]
                                 if evidence_id in selected_evidence]
    if isinstance(value.get('scope'), dict) and 'evidence_ids' in value['scope']:
        value['scope']['evidence_ids'] = [evidence_id for evidence_id in
                                          value['scope']['evidence_ids']
                                          if evidence_id in selected_evidence]
    return value


def target_formal_input(base, scoped_elements, card):
    """Narrow the model payload to this card's evidence and one Impact."""
    value = copy.deepcopy(base)
    allowed_ids = {row['id'] for row in scoped_elements.get('statements', [])}
    strict_applicability = bool(card.get('formalizability', {}).get('applicability'))
    allowed_evidence = (set() if strict_applicability else
                        set(scoped_elements.get('scope', {}).get('evidence_ids', [])))
    for row in scoped_elements.get('entities', []) + scoped_elements.get('statements', []):
        allowed_evidence.update(row.get('evidence_ids', row.get('evidence', [])))

    if 'elements' in value:
        value['elements'] = scoped_elements
        catalog = value.get('evidence_catalog')
        if isinstance(catalog, dict) and isinstance(catalog.get('fragments'), list):
            catalog['fragments'] = [row for row in catalog['fragments']
                                    if row.get('id') in allowed_evidence]
    elif 'statements' in value:
        value['statements'] = [row for row in value['statements']
                               if row.get('id') in allowed_ids]
        value['entities'] = [row for row in value.get('entities', [])
                             if row.get('id') in {
                                 entity_id for row in scoped_elements.get('statements', [])
                                 for entity_id in row.get('entity_ids', [])}]

    allowed = value.get('allowed_statement_ids')
    if isinstance(allowed, dict):
        allowed['preconditions'] = [row['id'] for row in scoped_elements['statements']
                                    if row.get('kind') in ('precondition', 'assumption')]
        allowed['safety'] = [row['id'] for row in scoped_elements['statements']
                             if row.get('kind') == 'security_intent']
        allowed['effects'] = [card['impact']['id']]
    value['numeric_fact_inventory'] = [row for row in
                                       value.get('numeric_fact_inventory', [])
                                       if row.get('source_id') in allowed_ids]
    value['semantic_card'] = card
    return value
