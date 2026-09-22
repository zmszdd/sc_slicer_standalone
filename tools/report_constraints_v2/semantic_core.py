"""Evidence-grounded report elements and per-claim symbolic acceptance gates."""
import copy
import re

import report_only as r

ELEMENT_VERSION = 'report-elements/1'
FORMAL_VERSION = 'report-formalization/1'
KINDS = {'precondition', 'action', 'root_cause', 'impact', 'security_intent', 'assumption'}
MODALITIES = {'asserted', 'potential', 'inferred'}
ROLES = {'attacker', 'victim', 'authority', 'asset', 'contract', 'other'}


def require(condition, message):
    if not condition: raise ValueError(message)


def strings(value):
    return isinstance(value, list) and all(isinstance(x, str) for x in value)


def identifier(value):
    return isinstance(value, str) and re.fullmatch(r'[a-z][a-z0-9_]{0,63}', value)


def evidence_spans(quotes, text):
    require(strings(quotes) and bool(quotes), 'missing evidence quotes')
    spans = []
    for quote in quotes:
        require(bool(quote.strip()) and quote in text, 'evidence absent from input')
        # Record every occurrence; never silently disambiguate repeated evidence.
        starts, start = [], 0
        while True:
            pos = text.find(quote, start)
            if pos < 0: break
            starts.append(pos); start = pos + 1
        spans.append({'quote': quote, 'occurrences': [
            {'start': pos, 'end': pos + len(quote), 'line': text.count('\n', 0, pos) + 1}
            for pos in starts]})
    return spans


def index(items, label):
    require(isinstance(items, list) and len(items) <= 32, 'invalid ' + label)
    result = {}
    for item in items:
        require(isinstance(item, dict) and identifier(item.get('id')), 'invalid ' + label + ' id')
        require(item['id'] not in result, 'duplicate ' + label + ' id')
        result[item['id']] = item
    return result


def validate_elements(elements, text):
    require(isinstance(elements, dict) and set(elements) == {
        'schema_version', 'scope', 'entities', 'statements', 'attack_steps', 'ambiguities'},
        'unexpected elements fields')
    require(elements['schema_version'] == ELEMENT_VERSION, 'unknown elements schema')
    scope = elements['scope']
    require(isinstance(scope, dict) and set(scope) == {'flow', 'environment', 'evidence'}, 'invalid scope')
    require(all(isinstance(scope[k], str) and scope[k].strip() for k in ('flow', 'environment')), 'missing scope')
    evidence_spans(scope['evidence'], text)
    entities = index(elements['entities'], 'entity')
    statements = index(elements['statements'], 'statement')
    grounded = {'scope': evidence_spans(scope['evidence'], text), 'entities': {}, 'statements': {}}
    for name, entity in entities.items():
        require(set(entity) == {'id', 'name', 'role', 'evidence'}, 'unexpected entity fields')
        require(entity['role'] in ROLES and isinstance(entity['name'], str) and entity['name'].strip(), 'invalid entity')
        grounded['entities'][name] = evidence_spans(entity['evidence'], text)
    for name, statement in statements.items():
        require(set(statement) == {'id', 'kind', 'text', 'modality', 'entity_ids', 'evidence'}, 'unexpected statement fields')
        require(statement['kind'] in KINDS and statement['modality'] in MODALITIES, 'invalid kind/modality')
        require(isinstance(statement['text'], str) and statement['text'].strip(), 'missing statement text')
        require(strings(statement['entity_ids']) and all(x in entities for x in statement['entity_ids']), 'unknown entity reference')
        grounded['statements'][name] = evidence_spans(statement['evidence'], text)
    require(strings(elements['attack_steps']), 'invalid attack steps')
    require(len(set(elements['attack_steps'])) == len(elements['attack_steps']), 'duplicate attack step')
    require(all(x in statements and statements[x]['kind'] == 'action' for x in elements['attack_steps']), 'attack step must reference action')
    require(strings(elements['ambiguities']), 'invalid ambiguities')
    return grounded


def predicate_paths(expr, symbols, path=''):
    """Every Boolean operation/root must have an independently inspectable source."""
    result = []
    if expr is None: return result
    if path == '' or ('op' in expr and r.expr_type(expr, symbols) == ('bool', None)):
        result.append(path)
    for n, child in enumerate(expr.get('args', [])):
        result.extend(predicate_paths(child, symbols, (path + '.' if path else '') + f'args.{n}'))
    return result


def node_at(expr, path):
    if not path: return expr
    parts = path.split('.')
    require(len(parts) % 2 == 0, 'invalid formula path')
    for n in range(0, len(parts), 2):
        require(parts[n] == 'args' and parts[n + 1].isdigit(), 'invalid formula path')
        require(isinstance(expr, dict) and 'args' in expr, 'formula path absent')
        offset = int(parts[n + 1])
        require(offset < len(expr['args']), 'formula path absent')
        expr = expr['args'][offset]
    return expr


def validate_formalization(formal, elements, text):
    validate_elements(elements, text)
    require(isinstance(formal, dict) and set(formal) == {'schema_version', 'symbols', 'claims', 'limitations'}, 'unexpected formalization fields')
    require(formal['schema_version'] == FORMAL_VERSION, 'unknown formalization schema')
    require(strings(formal['limitations']), 'invalid limitations')
    require(isinstance(formal['symbols'], dict), 'invalid symbols')
    entities = index(elements['entities'], 'entity')
    statements = index(elements['statements'], 'statement')
    symbol_base = {}
    for name, item in formal['symbols'].items():
        require(isinstance(item, dict) and set(item) == {'sort', 'unit', 'meaning', 'checkpoint', 'evidence', 'entity_ids'}, 'unexpected observable fields')
        require(strings(item['entity_ids']) and all(x in entities for x in item['entity_ids']), 'unknown observable entity')
        symbol_base[name] = {k: v for k, v in item.items() if k != 'entity_ids'}
    claims = index(formal['claims'], 'claim')
    require(len(claims) <= 8, 'too many claims')
    claimed_impacts = set()
    for claim in claims.values():
        require(set(claim) == {'id', 'scope', 'modality', 'impact_ids', 'properties', 'formula_sources', 'effect_coverage', 'assumptions', 'unresolved'}, 'unexpected claim fields')
        require(isinstance(claim['scope'], str) and claim['scope'].strip(), 'missing claim scope')
        require(claim['modality'] in MODALITIES, 'invalid claim modality')
        require(strings(claim['impact_ids']) and all(x in statements and statements[x]['kind'] == 'impact' for x in claim['impact_ids']), 'invalid claim impacts')
        claimed_impacts.update(claim['impact_ids'])
        if any(statements[x]['modality'] == 'potential' for x in claim['impact_ids']):
            require(claim['modality'] == 'potential', 'potential impact upgraded to asserted effect')
        require(set(claim['properties']) == {'preconditions', 'safety', 'effects'}, 'unexpected properties')
        base_props = {}
        allowed = {'preconditions': {'precondition', 'assumption'},
                   'safety': {'security_intent'}, 'effects': {'impact'}}
        require(set(claim['formula_sources']) == set(allowed), 'unexpected formula source fields')
        for name, prop in claim['properties'].items():
            require(set(prop) == {'text', 'expression', 'evidence', 'derivation', 'source_ids'}, 'unexpected property fields')
            sources = prop['source_ids']
            require(strings(sources) and all(x in statements for x in sources), 'unknown property source')
            require(all(statements[x]['kind'] in allowed[name] for x in sources), 'property source role mismatch: ' + name)
            if prop['expression'] is not None:
                require(bool(sources), 'formal property missing source')
                if name == 'effects': require(set(sources) <= set(claim['impact_ids']), 'effect source outside claim')
                # Ground formula evidence in its own declared source, not just any report sentence.
                quotes = {q for x in sources for q in statements[x]['evidence']}
                require(set(prop['evidence']) <= quotes, 'property quote not linked to source')
            base_props[name] = {k: v for k, v in prop.items() if k != 'source_ids'}
            links = claim['formula_sources'][name]
            require(isinstance(links, dict), 'invalid formula sources')
            if prop['expression'] is None:
                require(not links, 'null property has formula paths')
                continue
            for path, ids in links.items():
                node_at(prop['expression'], path)
                require(strings(ids) and bool(ids) and set(ids) <= set(sources), 'invalid subformula sources')
            require(set(predicate_paths(prop['expression'], symbol_base)) <= set(links), 'predicate lacks source mapping')
        base = {'symbols': symbol_base, 'properties': base_props,
                'assumptions': claim['assumptions'], 'unresolved': claim['unresolved']}
        r.validate(base, text)
        coverage = index([dict(row, id=row.get('statement_id')) for row in claim['effect_coverage']], 'coverage')
        require(set(coverage) == set(claim['impact_ids']), 'impact coverage missing or duplicate')
        for row in claim['effect_coverage']:
            require(set(row) == {'statement_id', 'status', 'reason'}, 'unexpected coverage fields')
            require(row['status'] in ('formalized', 'partial', 'unformalized'), 'invalid coverage status')
            require(isinstance(row['reason'], str) and row['reason'].strip(), 'missing coverage reason')
            if row['status'] in ('formalized', 'partial'):
                require(base_props['effects']['expression'] is not None and row['statement_id'] in claim['properties']['effects']['source_ids'], 'coverage lacks effect expression/source')
    # Missing claims/impacts are reported, never silently equated with complete coverage.
    return symbol_base, claimed_impacts


def compile_bundle(elements, formal, text, strict_piv=False):
    symbol_base, covered = validate_formalization(formal, elements, text)
    impacts = {x['id'] for x in elements['statements'] if x['kind'] == 'impact'}
    unassigned_preconditions = set()
    if strict_piv:
        extracted_preconditions = {x['id'] for x in elements['statements']
                                   if x['kind'] == 'precondition'}
        used_preconditions = {source for claim in formal['claims']
                              for source in claim['properties']['preconditions']['source_ids']
                              if source in extracted_preconditions}
        unassigned_preconditions = extracted_preconditions - used_preconditions
    output, warnings = [], []
    for claim in formal['claims']:
        base = {'symbols': symbol_base,
                'properties': {name: {k: v for k, v in prop.items() if k != 'source_ids'}
                               for name, prop in claim['properties'].items()},
                'assumptions': claim['assumptions'], 'unresolved': claim['unresolved']}
        validation, smt = r.compile_spec(base, text)
        relationship = r.relationship_review(base, text, require_direct_counterexample=strict_piv)
        reasons = list(validation['warnings']) + list(relationship['warnings'])
        if claim['modality'] != 'asserted': reasons.append('claim is qualified or inferred; not a verified realized effect')
        if any(x['status'] != 'formalized' for x in claim['effect_coverage']): reasons.append('claimed impact coverage is partial/unformalized')
        if claim['unresolved']: reasons.append('unresolved claim limitations require review')
        needs_review = bool(reasons) or bool(elements['ambiguities']) or bool(formal['limitations'])
        status = validation['formalization_status']
        if status == 'formalized_candidate' and needs_review: status = 'needs_review'
        output.append({'id': claim['id'], 'formalization_status': status,
                       'structural_formalization_status': validation['formalization_status'],
                       'validation': validation, 'semantic_relationship': relationship,
                       'review_reasons': reasons, 'smt': smt, 'properties': copy.deepcopy(claim['properties']),
                       'formula_sources': copy.deepcopy(claim['formula_sources']),
                       'effect_coverage': copy.deepcopy(claim['effect_coverage']),
                       'scope': claim['scope'], 'modality': claim['modality'],
                       'assumptions': claim['assumptions'], 'unresolved': claim['unresolved']})
    if impacts - covered: warnings.append('report impacts not assigned to a claim: ' + ', '.join(sorted(impacts - covered)))
    if strict_piv and unassigned_preconditions:
        warnings.append('extracted preconditions not used by formal P: ' +
                        ', '.join(sorted(unassigned_preconditions)))
    if elements['ambiguities']: warnings.append('report has declared ambiguities')
    if formal['limitations']: warnings.append('formalization has declared limitations')
    core = 'formalized_candidate' if output and all(x['structural_formalization_status'] != 'not_formalized' for x in output) else 'partial'
    review = 'needs_review' if warnings or any(x['formalization_status'] != 'formalized_candidate' for x in output) else 'candidate_checks_passed'
    result = {'schema_version': 'stage2-semantic-bundle/1', 'core_formalization_status': core,
            'acceptance_status': review, 'report_warnings': warnings,
            'unassigned_impact_ids': sorted(impacts - covered), 'claims': output,
            'coverage_is_model_declared_not_semantically_verified': True,
            'human_semantic_review_required': True, 'code_alignment_status': 'not_attempted',
            'execution_ready': False, 'consistency_verdict': 'not_evaluated'}
    if strict_piv:
        result['unassigned_precondition_ids'] = sorted(unassigned_preconditions)
        result['precondition_coverage_is_structural_not_semantic'] = True
        result['strict_piv_gate'] = True
    return result
