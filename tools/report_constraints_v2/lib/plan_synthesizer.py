"""Deterministically compile a compact neural semantic plan into formalization/2."""
import json
import re

import report_only as r
from semantic_core import identifier, predicate_paths, require, strings


PLAN_VERSION = 'report-formal-plan/1'
STRUCTURED_PLAN_VERSION = 'report-formal-plan/2'
CLASSIFIED_PLAN_VERSION = 'report-formal-plan/3'
FIXED_PLAN_VERSION = 'report-formal-plan/4'
EXPANDED_PLAN_VERSION = 'report-formal-plan/5'
UNRESOLVED_CATEGORIES = {
    'missing_report_definition', 'ambiguous_actor', 'ambiguous_condition',
    'missing_unit', 'unsupported_relation', 'missing_checkpoint',
}
PATTERNS = {'condition_forbids_effect', 'condition_requires_effect',
            'effect_requires_any_authorization', 'state_preservation',
            'relation_obligation', 'monotonicity', 'conservation',
            'authorization_guard', 'bounded_relation', 'correspondence',
            'temporal_order', 'required_effect', 'proportional_relation'}
RELATION_CLASSES = {
    'access_control', 'value_relation', 'bounded_value', 'monotonicity',
    'conservation', 'proportional_fairness', 'state_correspondence',
    'temporal_validity', 'sequence_preservation', 'data_structure_integrity',
    'progress_or_liveness', 'range_capacity',
}
RELATION_CLASS_PATTERNS = {
    'access_control': {'effect_requires_any_authorization', 'condition_forbids_effect'},
    'value_relation': {'relation_obligation'},
    'bounded_value': {'relation_obligation'},
    'monotonicity': {'monotonicity'},
    'conservation': {'conservation', 'relation_obligation'},
    'proportional_fairness': {'relation_obligation'},
    'state_correspondence': {'relation_obligation'},
    'temporal_validity': {'relation_obligation', 'condition_forbids_effect'},
    'sequence_preservation': {'relation_obligation', 'condition_requires_effect'},
    'data_structure_integrity': {'relation_obligation', 'condition_requires_effect'},
    'progress_or_liveness': {'condition_forbids_effect', 'condition_requires_effect'},
    'range_capacity': {'relation_obligation'},
}

# v4 deliberately removes template selection from the model.  The model still
# identifies the semantic relation class and binds report observables, while the
# compiler fixes the logical skeleton.  relation_obligation is expressive enough
# for positive, negative, authorization, temporal and correspondence relations.
FIXED_RELATION_CLASS_PATTERN = {
    name: ('monotonicity' if name == 'monotonicity' else
           'conservation' if name == 'conservation' else
           'relation_obligation')
    for name in RELATION_CLASSES
}

# v5 retains a generic escape hatch only for relations whose shape is genuinely
# open-ended.  Common safety relations receive typed slots so the model cannot
# silently swap the protected effect, bound, ordering, or completion predicate.
EXPANDED_RELATION_CLASS_PATTERN = {
    'access_control': 'authorization_guard',
    'value_relation': 'relation_obligation',
    'bounded_value': 'bounded_relation',
    'monotonicity': 'monotonicity',
    'conservation': 'conservation',
    'proportional_fairness': 'proportional_relation',
    'state_correspondence': 'correspondence',
    'temporal_validity': 'temporal_order',
    'sequence_preservation': 'required_effect',
    'data_structure_integrity': 'relation_obligation',
    'progress_or_liveness': 'required_effect',
    'range_capacity': 'bounded_relation',
}

IMPACT_QUALIFIER_PATTERNS = {
    'temporal': re.compile(
        r'\b(?:after|before|once|until|while|only\s+(?:after|before|while))\b',
        re.IGNORECASE),
    'threshold': re.compile(
        r'\b(?:exceeds?|below|above|at\s+least|at\s+most)\b', re.IGNORECASE),
    'state': re.compile(
        r'\b(?:despite|even\s+(?:if|when|though)|only\s+(?:if|when))\b',
        re.IGNORECASE),
}


def impact_qualifier_types(text):
    """Conservatively classify explicit impact-scope cues for v5 auditing."""
    return sorted(name for name, pattern in IMPACT_QUALIFIER_PATTERNS.items()
                  if pattern.search(text))


def _index(rows, label):
    result = {}
    for row in rows:
        require(isinstance(row, dict) and identifier(row.get('id')), 'invalid ' + label + ' id')
        require(row['id'] not in result, 'duplicate ' + label + ' id')
        result[row['id']] = row
    return result


def _unique(values):
    result = []
    for value in values:
        if value not in result:
            result.append(value)
    return result


def _operand(value, symbols):
    require(isinstance(value, dict), 'invalid predicate operand')
    if set(value) == {'symbol'}:
        require(value['symbol'] in symbols, 'unknown predicate symbol')
        return {'var': value['symbol']}
    if set(value) == {'power_of_two', 'offset'}:
        require(type(value['power_of_two']) is int and
                0 <= value['power_of_two'] <= 4096 and
                type(value['offset']) is int,
                'invalid exact power-of-two operand')
        return {'const': (1 << value['power_of_two']) + value['offset']}
    require(set(value) == {'const'} and type(value['const']) in (int, bool),
            'invalid predicate operand')
    return {'const': value['const']}


def _quantity_expression(value, symbols, depth=0):
    require(depth <= 3 and isinstance(value, dict), 'invalid quantity expression')
    if set(value) in ({'symbol'}, {'const'}, {'power_of_two', 'offset'}):
        expression = _operand(value, symbols)
        sort, _ = r.expr_type(expression, symbols)
        require(sort in ('int', 'literal'), 'quantity expression requires integer')
        return expression
    require(set(value) == {'op', 'args'} and value['op'] in ('add', 'sub', 'mul') and
            isinstance(value['args'], list) and len(value['args']) == 2,
            'invalid quantity expression')
    expression = {'op': value['op'], 'args': [
        _quantity_expression(item, symbols, depth + 1) for item in value['args']]}
    require(r.expr_type(expression, symbols)[0] == 'int', 'invalid quantity expression types')
    return expression


def _predicate(value, symbols, depth=0):
    require(depth <= 4 and isinstance(value, dict) and value.get('kind') in (
        'truth', 'comparison', 'divisible_by', 'all_of', 'any_of', 'relation'),
            'invalid predicate binding')
    if value['kind'] in ('all_of', 'any_of'):
        require(set(value) == {'kind', 'terms'} and isinstance(value['terms'], list) and
                2 <= len(value['terms']) <= 4, 'invalid compound predicate')
        expressions = [_predicate(item, symbols, depth + 1) for item in value['terms']]
        return _and(expressions) if value['kind'] == 'all_of' else _or(expressions)
    if value['kind'] == 'relation':
        require(set(value) == {'kind', 'left', 'operator', 'right'} and
                value['operator'] in ('eq', 'ne', 'lt', 'le', 'gt', 'ge'),
                'invalid quantity relation')
        require(value['left'] != value['right'],
                'trivial self-comparison predicate')
        expression = {'op': value['operator'], 'args': [
            _quantity_expression(value['left'], symbols),
            _quantity_expression(value['right'], symbols)]}
        require(r.expr_type(expression, symbols) == ('bool', None),
                'invalid quantity relation types/units')
        return expression
    if value['kind'] == 'divisible_by':
        require(set(value) == {'kind', 'dividend', 'divisor', 'value'} and
                value['dividend'] in symbols and
                symbols[value['dividend']]['sort'] == 'int' and
                type(value['divisor']) is int and value['divisor'] > 0 and
                type(value['value']) is bool, 'invalid divisibility binding')
        remainder = {'op': 'mod', 'args': [
            {'var': value['dividend']}, {'const': value['divisor']}]}
        expression = {'op': 'eq' if value['value'] else 'ne',
                      'args': [remainder, {'const': 0}]}
        require(r.expr_type(expression, symbols) == ('bool', None),
                'invalid divisibility type/unit')
        return expression
    if value['kind'] == 'truth':
        require(set(value) == {'kind', 'symbol', 'value'} and value['symbol'] in symbols and
                type(value['value']) is bool, 'invalid truth binding')
        require(symbols[value['symbol']]['sort'] == 'bool', 'truth binding requires bool symbol')
        atom = {'var': value['symbol']}
        return atom if value['value'] else {'op': 'not', 'args': [atom]}
    require(set(value) == {'kind', 'left', 'operator', 'right'} and
            value['operator'] in ('eq', 'ne', 'lt', 'le', 'gt', 'ge'),
            'invalid comparison binding')
    require(isinstance(value['left'], str) and value['left'] in symbols,
            'unknown comparison symbol')
    require(not (set(value['right']) == {'symbol'} and
                 value['right']['symbol'] == value['left']),
            'trivial self-comparison predicate')
    expression = {'op': value['operator'],
                  'args': [{'var': value['left']}, _operand(value['right'], symbols)]}
    require(r.expr_type(expression, symbols) == ('bool', None), 'invalid comparison types/units')
    return expression


def _and(expressions):
    require(bool(expressions), 'empty conjunction')
    return expressions[0] if len(expressions) == 1 else {'op': 'and', 'args': expressions}


def _or(expressions):
    require(bool(expressions), 'empty disjunction')
    return expressions[0] if len(expressions) == 1 else {'op': 'or', 'args': expressions}


def _not(expression):
    return {'op': 'not', 'args': [expression]}


def _expression_variables(expression):
    if not isinstance(expression, dict):
        return set()
    if set(expression) == {'var'}:
        return {expression['var']}
    return {name for child in expression.get('args', [])
            for name in _expression_variables(child)}


def _quantity_binding_symbols(value):
    require(isinstance(value, dict), 'invalid quantity binding')
    if set(value) == {'symbol'}:
        return {value['symbol']}
    if set(value) in ({'const'}, {'power_of_two', 'offset'}):
        return set()
    require(set(value) == {'op', 'args'} and value['op'] in ('add', 'sub', 'mul') and
            isinstance(value['args'], list) and len(value['args']) == 2,
            'invalid quantity binding')
    return set().union(*(_quantity_binding_symbols(item) for item in value['args']))


def _predicate_binding_symbols(value):
    require(isinstance(value, dict), 'invalid predicate binding')
    kind = value.get('kind')
    if kind in ('all_of', 'any_of'):
        return set().union(*(_predicate_binding_symbols(item) for item in value['terms']))
    if kind == 'truth':
        return {value['symbol']}
    if kind == 'divisible_by':
        return {value['dividend']}
    if kind == 'comparison':
        result = {value['left']}
        if set(value['right']) == {'symbol'}:
            result.add(value['right']['symbol'])
        return result
    if kind == 'relation':
        return (_quantity_binding_symbols(value['left']) |
                _quantity_binding_symbols(value['right']))
    raise ValueError('invalid predicate binding')


def _multiplicative_symbols(value):
    """Return factors for a pure product, or None for a non-product QEXPR."""
    if not isinstance(value, dict):
        return None
    if set(value) == {'symbol'}:
        return {value['symbol']}
    if set(value) in ({'const'}, {'power_of_two', 'offset'}):
        return set()
    if set(value) == {'op', 'args'} and value.get('op') == 'mul' and \
            isinstance(value.get('args'), list) and len(value['args']) == 2:
        left = _multiplicative_symbols(value['args'][0])
        right = _multiplicative_symbols(value['args'][1])
        return None if left is None or right is None else left | right
    return None


def _reject_cancellable_relation(pattern):
    """Reject vacuous proportional formulas that reuse the same unknown factor."""
    if pattern.get('kind') == 'proportional_relation':
        left_value, right_value = pattern.get('left'), pattern.get('right')
    elif pattern.get('kind') == 'relation_obligation':
        relation = pattern.get('relation', {})
        if relation.get('kind') != 'relation':
            return
        left_value, right_value = relation.get('left'), relation.get('right')
    else:
        return
    left = _multiplicative_symbols(left_value)
    right = _multiplicative_symbols(right_value)
    if left is not None and right is not None and left & right:
        raise ValueError('relation repeats cancellable observable on both sides')


def _core_relation_symbols(pattern):
    """Return observables defining I/V, excluding scenario-only triggers."""
    kind = pattern.get('kind')
    if kind in ('condition_forbids_effect', 'condition_requires_effect'):
        return _predicate_binding_symbols(pattern['effect'])
    if kind == 'effect_requires_any_authorization':
        return (_predicate_binding_symbols(pattern['effect']) |
                set().union(*(_predicate_binding_symbols(item)
                              for item in pattern['authorization_terms'])))
    if kind == 'relation_obligation':
        return _predicate_binding_symbols(pattern['relation'])
    if kind == 'authorization_guard':
        return (_predicate_binding_symbols(pattern['effect']) |
                _predicate_binding_symbols(pattern['authorization']))
    if kind == 'bounded_relation':
        return (_quantity_binding_symbols(pattern['value']) |
                _quantity_binding_symbols(pattern['bound']))
    if kind == 'correspondence':
        return {pattern['observed_symbol'], pattern['expected_symbol']}
    if kind == 'temporal_order':
        return {pattern['earlier_symbol'], pattern['later_symbol']}
    if kind == 'required_effect':
        return _predicate_binding_symbols(pattern['effect'])
    if kind == 'proportional_relation':
        return (_quantity_binding_symbols(pattern['left']) |
                _quantity_binding_symbols(pattern['right']))
    if kind in ('monotonicity', 'state_preservation'):
        return {pattern['before_symbol'], pattern['after_symbol']}
    if kind == 'conservation':
        return (_quantity_binding_symbols(pattern['before']) |
                _quantity_binding_symbols(pattern['after']))
    raise ValueError('unknown synthesis pattern')


def classified_relation_alignment(plan, elements):
    """Audit that classified I/V observables are grounded by intent and impacts."""
    require(plan.get('schema_version') in (
        CLASSIFIED_PLAN_VERSION, FIXED_PLAN_VERSION, EXPANDED_PLAN_VERSION),
            'relation alignment requires plan schema v3')
    statements = _index(elements['statements'], 'statement')
    core_symbols = sorted(_core_relation_symbols(plan['pattern']))
    require(bool(core_symbols), 'classified relation has no core observables')
    require(isinstance(plan.get('symbols'), dict) and
            all(name in plan['symbols'] for name in core_symbols),
            'classified relation uses unknown core observable')
    coverage = {
        name: sorted(set(plan['symbols'][name].get('source_ids', [])))
        for name in core_symbols
    }
    source_union = set().union(*(set(ids) for ids in coverage.values()))
    # The selected intent already grounds the generated I property itself.  Requiring
    # the same intent ID again on an observable conflates formula provenance with
    # variable provenance and caused valid `reverted`/`returned` observables to be
    # rejected.  v4 keeps the stronger requirement where it matters: every selected
    # direct impact must ground at least one core observable.  v3 remains unchanged
    # for exact replay of frozen results.
    required_sources = ([plan['intent_id'], *plan['impact_ids']]
                        if plan.get('schema_version') == CLASSIFIED_PLAN_VERSION
                        else list(plan['impact_ids']))
    missing = [source for source in required_sources if source not in source_union]
    require(not missing, 'core relation observables lack intent/impact grounding')
    require(all(source in statements for source in source_union),
            'core relation observable has unknown source')
    result = {
        'schema_version': ('safety-relation-alignment/1'
                           if plan.get('schema_version') == CLASSIFIED_PLAN_VERSION
                           else 'safety-relation-alignment/3'
                           if plan.get('schema_version') == EXPANDED_PLAN_VERSION
                           else 'safety-relation-alignment/2'),
        'relation_class': plan['relation_class'],
        'pattern_kind': plan['pattern']['kind'],
        'core_observables': core_symbols,
        'observable_source_ids': coverage,
        'required_source_ids': required_sources,
        'missing_required_source_ids': [],
        'direct_negation_by_construction': True,
        'passed': True,
    }
    if plan.get('schema_version') in (FIXED_PLAN_VERSION, EXPANDED_PLAN_VERSION):
        result.update({'intent_source_id': plan['intent_id'],
                       'intent_grounding': 'selected_safety_property'})
    return result


def _evidence(source_ids, statements):
    return _unique([evidence for source in source_ids
                    for evidence in statements[source]['evidence_ids']])


def _links(expression, source_ids, symbols):
    return {path: list(source_ids) for path in predicate_paths(expression, symbols)}


def structured_unresolved_review(plan, elements):
    """Validate v2 unresolved records and separate blocking from audit-only items."""
    require(plan.get('schema_version') in (
        STRUCTURED_PLAN_VERSION, CLASSIFIED_PLAN_VERSION, FIXED_PLAN_VERSION,
        EXPANDED_PLAN_VERSION),
            'structured unresolved requires plan schema v2')
    statements = _index(elements['statements'], 'statement')
    items = plan.get('unresolved')
    require(isinstance(items, list) and len(items) <= 4, 'invalid structured unresolved list')
    normalized = []
    for item in items:
        require(isinstance(item, dict) and set(item) == {
            'category', 'description', 'source_ids', 'blocks_formalization'},
            'invalid structured unresolved item')
        require(item['category'] in UNRESOLVED_CATEGORIES,
                'invalid structured unresolved category')
        require(isinstance(item['description'], str) and item['description'].strip(),
                'missing structured unresolved description')
        require(strings(item['source_ids']) and bool(item['source_ids']) and
                all(source in statements for source in item['source_ids']),
                'invalid structured unresolved sources')
        require(type(item['blocks_formalization']) is bool,
                'invalid structured unresolved blocking flag')
        normalized.append({key: item[key] for key in (
            'category', 'description', 'source_ids', 'blocks_formalization')})
    blocking = [item for item in normalized if item['blocks_formalization']]
    return {
        'schema_version': 'structured-unresolved-review/1',
        'items': normalized,
        'blocking_count': len(blocking),
        'advisory_count': len(normalized) - len(blocking),
        'blocks_candidate_acceptance': bool(blocking),
    }


def _pattern_expressions(pattern, symbols):
    require(isinstance(pattern, dict) and pattern.get('kind') in PATTERNS,
            'unknown synthesis pattern')
    kind = pattern['kind']
    if kind in ('condition_forbids_effect', 'condition_requires_effect'):
        require(set(pattern) == {'kind', 'condition', 'effect'}, 'invalid condition pattern')
        condition = _predicate(pattern['condition'], symbols)
        effect = _predicate(pattern['effect'], symbols)
        if kind == 'condition_forbids_effect':
            return {'op': 'implies', 'args': [condition, _not(effect)]}, _and([condition, effect])
        return {'op': 'implies', 'args': [condition, effect]}, _and([condition, _not(effect)])
    if kind == 'effect_requires_any_authorization':
        require(set(pattern) == {'kind', 'effect', 'authorization_terms'} and
                isinstance(pattern['authorization_terms'], list) and
                bool(pattern['authorization_terms']), 'invalid authorization pattern')
        effect = _predicate(pattern['effect'], symbols)
        authorization = _or([_predicate(x, symbols) for x in pattern['authorization_terms']])
        return {'op': 'implies', 'args': [effect, authorization]}, _and([effect, _not(authorization)])
    if kind == 'authorization_guard':
        require(set(pattern) == {'kind', 'effect', 'authorization'},
                'invalid authorization guard pattern')
        effect = _predicate(pattern['effect'], symbols)
        authorization = _predicate(pattern['authorization'], symbols)
        return {'op': 'implies', 'args': [effect, authorization]}, \
            _and([effect, _not(authorization)])
    if kind == 'relation_obligation':
        require(set(pattern) == {'kind', 'condition', 'relation'},
                'invalid relation obligation pattern')
        condition = _predicate(pattern['condition'], symbols)
        relation = _predicate(pattern['relation'], symbols)
        return {'op': 'implies', 'args': [condition, relation]}, \
            _and([condition, _not(relation)])
    if kind == 'bounded_relation':
        require(set(pattern) == {'kind', 'condition', 'value', 'operator', 'bound'} and
                pattern['operator'] in ('lt', 'le', 'gt', 'ge'),
                'invalid bounded relation pattern')
        condition = _predicate(pattern['condition'], symbols)
        relation = {'op': pattern['operator'], 'args': [
            _quantity_expression(pattern['value'], symbols),
            _quantity_expression(pattern['bound'], symbols)]}
        require(r.expr_type(relation, symbols) == ('bool', None),
                'bounded relation type/unit mismatch')
        return {'op': 'implies', 'args': [condition, relation]}, \
            _and([condition, _not(relation)])
    if kind == 'correspondence':
        require(set(pattern) == {'kind', 'condition', 'observed_symbol',
                                 'expected_symbol'},
                'invalid correspondence pattern')
        observed, expected = pattern['observed_symbol'], pattern['expected_symbol']
        require(observed in symbols and expected in symbols,
                'unknown correspondence symbol')
        condition = _predicate(pattern['condition'], symbols)
        relation = {'op': 'eq', 'args': [{'var': observed}, {'var': expected}]}
        require(r.expr_type(relation, symbols) == ('bool', None),
                'correspondence type/unit mismatch')
        return {'op': 'implies', 'args': [condition, relation]}, \
            _and([condition, _not(relation)])
    if kind == 'temporal_order':
        require(set(pattern) == {'kind', 'condition', 'earlier_symbol',
                                 'later_symbol', 'strict'} and
                type(pattern['strict']) is bool,
                'invalid temporal order pattern')
        earlier, later = pattern['earlier_symbol'], pattern['later_symbol']
        require(earlier in symbols and later in symbols,
                'unknown temporal order symbol')
        condition = _predicate(pattern['condition'], symbols)
        relation = {'op': 'lt' if pattern['strict'] else 'le',
                    'args': [{'var': earlier}, {'var': later}]}
        require(r.expr_type(relation, symbols) == ('bool', None),
                'temporal order type/unit mismatch')
        return {'op': 'implies', 'args': [condition, relation]}, \
            _and([condition, _not(relation)])
    if kind == 'required_effect':
        require(set(pattern) == {'kind', 'condition', 'effect'},
                'invalid required effect pattern')
        condition = _predicate(pattern['condition'], symbols)
        effect = _predicate(pattern['effect'], symbols)
        return {'op': 'implies', 'args': [condition, effect]}, \
            _and([condition, _not(effect)])
    if kind == 'proportional_relation':
        require(set(pattern) == {'kind', 'condition', 'left', 'operator', 'right'} and
                pattern['operator'] in ('eq', 'le', 'ge'),
                'invalid proportional relation pattern')
        condition = _predicate(pattern['condition'], symbols)
        relation = {'op': pattern['operator'], 'args': [
            _quantity_expression(pattern['left'], symbols),
            _quantity_expression(pattern['right'], symbols)]}
        require(r.expr_type(relation, symbols) == ('bool', None),
                'proportional relation type/unit mismatch')
        return {'op': 'implies', 'args': [condition, relation]}, \
            _and([condition, _not(relation)])
    if kind == 'monotonicity':
        require(set(pattern) == {'kind', 'trigger', 'before_symbol', 'after_symbol',
                                 'direction'} and
                pattern['direction'] in ('nondecreasing', 'nonincreasing'),
                'invalid monotonicity pattern')
        require(pattern['before_symbol'] in symbols and pattern['after_symbol'] in symbols,
                'unknown monotonicity symbol')
        trigger = _predicate(pattern['trigger'], symbols)
        relation = {'op': 'ge' if pattern['direction'] == 'nondecreasing' else 'le',
                    'args': [{'var': pattern['after_symbol']},
                             {'var': pattern['before_symbol']}]}
        require(r.expr_type(relation, symbols) == ('bool', None),
                'monotonicity type/unit mismatch')
        return {'op': 'implies', 'args': [trigger, relation]}, \
            _and([trigger, _not(relation)])
    if kind == 'conservation':
        require(set(pattern) == {'kind', 'trigger', 'before', 'after'},
                'invalid conservation pattern')
        trigger = _predicate(pattern['trigger'], symbols)
        before = _quantity_expression(pattern['before'], symbols)
        after = _quantity_expression(pattern['after'], symbols)
        relation = {'op': 'eq', 'args': [after, before]}
        require(r.expr_type(relation, symbols) == ('bool', None),
                'conservation type/unit mismatch')
        return {'op': 'implies', 'args': [trigger, relation]}, \
            _and([trigger, _not(relation)])
    require(set(pattern) == {'kind', 'trigger', 'before_symbol', 'after_symbol'},
            'invalid preservation pattern')
    require(pattern['before_symbol'] in symbols and pattern['after_symbol'] in symbols,
            'unknown preservation symbol')
    trigger = _predicate(pattern['trigger'], symbols)
    equal = {'op': 'eq', 'args': [{'var': pattern['after_symbol']},
                                  {'var': pattern['before_symbol']}]}
    require(r.expr_type(equal, symbols) == ('bool', None), 'state preservation type/unit mismatch')
    return {'op': 'implies', 'args': [trigger, equal]}, _and([trigger, _not(equal)])


def identical_p_predicates(plan):
    """``source_id``s whose P predicate repeats an earlier source's exactly.

    Two distinct precondition sources must not share one predicate: the
    conjunction then collapses (``(and X X)`` is just ``X``) and one of the
    report's facts stops being represented, with nothing left to notice it.  The
    SMT shows it directly as a doubled conjunct in ``report_preconditions``.

    Deliberately NOT used to reject under ``report-formal-plan/4``: one frozen run
    in the replay battery carries a duplicate, so tightening the live schema would
    break its recorded artifacts.  ``cli/batch_verify.py`` reports this instead --
    verification output is not an artifact, so old runs stay replayable while the
    defect becomes visible for every run, old and new.
    """
    seen, duplicates = set(), []
    for term in plan.get('precondition_terms') or []:
        if not isinstance(term, dict) or 'predicate' not in term:
            continue
        canonical = json.dumps(term['predicate'], sort_keys=True,
                               separators=(',', ':'))
        if canonical in seen:
            duplicates.append(term.get('source_id'))
        else:
            seen.add(canonical)
    return duplicates


def synthesize_id_formalization(plan, elements):
    base_fields = {
        'schema_version', 'precondition_ids', 'intent_id', 'impact_ids', 'symbols',
        'precondition_terms', 'pattern', 'assumptions', 'unresolved', 'limitations'}
    require(isinstance(plan, dict), 'invalid formal plan')
    version = plan.get('schema_version')
    expected_fields = (base_fields | {'relation_class', 'derived_definitions',
                                      'impact_context_terms'}
                       if version == EXPANDED_PLAN_VERSION else
                       base_fields | {'relation_class', 'derived_definitions'}
                       if version == FIXED_PLAN_VERSION else
                       base_fields | {'relation_class'}
                       if version == CLASSIFIED_PLAN_VERSION else base_fields)
    require(set(plan) == expected_fields, 'unexpected formal plan fields')
    require(version in (PLAN_VERSION, STRUCTURED_PLAN_VERSION, CLASSIFIED_PLAN_VERSION,
                        FIXED_PLAN_VERSION, EXPANDED_PLAN_VERSION),
            'unknown formal plan schema')
    if version in (CLASSIFIED_PLAN_VERSION, FIXED_PLAN_VERSION,
                   EXPANDED_PLAN_VERSION):
        require(plan['relation_class'] in RELATION_CLASSES, 'unknown relation class')
        require(isinstance(plan['pattern'], dict), 'invalid classified relation pattern')
        if version == FIXED_PLAN_VERSION:
            require(plan['pattern'].get('kind') ==
                    FIXED_RELATION_CLASS_PATTERN[plan['relation_class']],
                    'fixed relation template mismatch')
            _reject_cancellable_relation(plan['pattern'])
        elif version == EXPANDED_PLAN_VERSION:
            require(plan['pattern'].get('kind') ==
                    EXPANDED_RELATION_CLASS_PATTERN[plan['relation_class']],
                    'expanded relation template mismatch')
            _reject_cancellable_relation(plan['pattern'])
        else:
            require(plan['pattern'].get('kind') in
                    RELATION_CLASS_PATTERNS[plan['relation_class']],
                    'relation class and pattern mismatch')
    statements = _index(elements['statements'], 'statement')
    entities = _index(elements['entities'], 'entity')
    require(strings(plan['precondition_ids']) and bool(plan['precondition_ids']) and
            len(set(plan['precondition_ids'])) ==
            len(plan['precondition_ids']), 'invalid plan precondition IDs')
    require(all(x in statements and statements[x]['kind'] in ('precondition', 'assumption')
                for x in plan['precondition_ids']), 'plan P source role mismatch')
    require(isinstance(plan['intent_id'], str) and plan['intent_id'] in statements and
            statements[plan['intent_id']]['kind'] == 'security_intent', 'invalid plan intent ID')
    impact_limit = 1 if version in (
        CLASSIFIED_PLAN_VERSION, FIXED_PLAN_VERSION, EXPANDED_PLAN_VERSION) else 2
    require(strings(plan['impact_ids']) and 1 <= len(plan['impact_ids']) <= impact_limit and
            len(set(plan['impact_ids'])) == len(plan['impact_ids']) and
            all(x in statements and statements[x]['kind'] == 'impact' for x in plan['impact_ids']),
            'invalid plan impact IDs')
    require(strings(plan['assumptions']) and strings(plan['limitations']),
            'invalid plan caveats')
    if version == PLAN_VERSION:
        require(strings(plan['unresolved']), 'invalid plan caveats')
        formal_unresolved = list(plan['unresolved'])
    else:
        unresolved_review = structured_unresolved_review(plan, elements)
        formal_unresolved = [
            f"[{item['category']}] {item['description']}"
            for item in unresolved_review['items'] if item['blocks_formalization']
        ]
    require(isinstance(plan['symbols'], dict) and 1 <= len(plan['symbols']) <= 8,
            'invalid plan symbols')

    symbols, output_symbols = {}, {}
    for name, item in plan['symbols'].items():
        require(identifier(name) and isinstance(item, dict) and set(item) == {
            'sort', 'unit', 'meaning', 'checkpoint', 'entity_ids', 'source_ids'},
            'invalid plan symbol')
        require(item['sort'] in ('int', 'bool', 'address'), 'invalid plan symbol sort')
        if item['sort'] == 'int':
            require(isinstance(item['unit'], str) and item['unit'].strip(), 'missing plan quantity unit')
        else:
            require(item['unit'] is None, 'non-quantity plan unit')
        require(all(isinstance(item[x], str) and item[x].strip()
                    for x in ('meaning', 'checkpoint')), 'missing plan symbol semantics')
        require(strings(item['entity_ids']) and bool(item['entity_ids']) and
                all(x in entities for x in item['entity_ids']), 'invalid plan symbol entities')
        require(strings(item['source_ids']) and bool(item['source_ids']) and
                all(x in statements for x in item['source_ids']), 'invalid plan symbol sources')
        evidence_ids = _evidence(item['source_ids'], statements)
        require(bool(evidence_ids), 'plan symbol lacks evidence')
        symbols[name] = {'sort': item['sort'], 'unit': item['unit'],
                         'meaning': item['meaning'], 'checkpoint': item['checkpoint']}
        output_symbols[name] = {**symbols[name], 'evidence_ids': evidence_ids,
                                'entity_ids': item['entity_ids']}

    definition_expressions = []
    if version in (FIXED_PLAN_VERSION, EXPANDED_PLAN_VERSION):
        definitions = plan['derived_definitions']
        require(isinstance(definitions, list) and len(definitions) <= 6,
                'invalid derived definitions')
        targets = []
        allowed_definition_sources = set(
            plan['precondition_ids'] + [plan['intent_id']] + plan['impact_ids'])
        for item in definitions:
            require(isinstance(item, dict) and set(item) == {
                'symbol', 'expression', 'source_ids'}, 'invalid derived definition')
            target = item['symbol']
            require(target in symbols and symbols[target]['sort'] == 'int',
                    'derived definition target must be integer symbol')
            require(target not in targets, 'duplicate derived definition')
            require(strings(item['source_ids']) and bool(item['source_ids']) and
                    set(item['source_ids']) <= allowed_definition_sources,
                    'invalid derived definition sources')
            expression = _quantity_expression(item['expression'], symbols)
            require(target not in _expression_variables(expression),
                    'recursive derived definition')
            targets.append(target)
            definition = {'op': 'eq', 'args': [{'var': target}, expression]}
            require(r.expr_type(definition, symbols) == ('bool', None),
                    'derived definition type/unit mismatch')
            definition_expressions.append(definition)
        # Keep the first implementation intentionally acyclic and auditable.
        require(not any((_expression_variables(expression) & set(targets))
                        for expression in [x['args'][1] for x in definition_expressions]),
                'derived definitions may reference base symbols only')

    require(isinstance(plan['precondition_terms'], list), 'invalid plan P terms')
    term_sources, p_expressions = [], []
    for term in plan['precondition_terms']:
        require(isinstance(term, dict) and set(term) == {'source_id', 'predicate'},
                'invalid plan P term')
        require(term['source_id'] in plan['precondition_ids'], 'P term source not selected')
        term_sources.append(term['source_id'])
        expression = _predicate(term['predicate'], symbols)
        if version == EXPANDED_PLAN_VERSION:
            require(all(term['source_id'] in plan['symbols'][name]['source_ids']
                        for name in _expression_variables(expression)),
                    'P predicate symbol not grounded by its own source')
        else:
            require(all(any(source in plan['precondition_ids']
                            for source in plan['symbols'][name]['source_ids'])
                        for name in _expression_variables(expression)),
                    'P predicate symbol not grounded by selected preconditions')
        p_expressions.append(expression)
    require(set(term_sources) == set(plan['precondition_ids']) and
            len(term_sources) == len(plan['precondition_ids']),
            'P terms must cover selected preconditions exactly once')
    if version == EXPANDED_PLAN_VERSION:
        require(not identical_p_predicates(plan),
                'distinct P sources reuse identical predicate')
    p_expression = _and(p_expressions) if p_expressions else None
    if version in (CLASSIFIED_PLAN_VERSION, FIXED_PLAN_VERSION,
                   EXPANDED_PLAN_VERSION):
        classified_relation_alignment(plan, elements)
    safety, effects = _pattern_expressions(plan['pattern'], symbols)
    if version == EXPANDED_PLAN_VERSION:
        context_terms = plan['impact_context_terms']
        require(isinstance(context_terms, list) and len(context_terms) <= 3,
                'invalid impact context terms')
        context_types = {source: set() for source in plan['impact_ids']}
        context_expressions = []
        for term in context_terms:
            require(isinstance(term, dict) and set(term) == {
                'source_id', 'qualifier_types', 'predicate'},
                    'invalid impact context term')
            source_id = term['source_id']
            require(source_id in plan['impact_ids'],
                    'impact context source not selected')
            require(strings(term['qualifier_types']) and
                    len(term['qualifier_types']) == len(set(term['qualifier_types'])) and
                    set(term['qualifier_types']) <= set(IMPACT_QUALIFIER_PATTERNS),
                    'invalid impact qualifier types')
            expression = _predicate(term['predicate'], symbols)
            require(all(source_id in plan['symbols'][name]['source_ids']
                        for name in _expression_variables(expression)),
                    'impact context symbol not grounded by its own source')
            context_types[source_id].update(term['qualifier_types'])
            context_expressions.append(expression)
        missing_context = {
            source: sorted(set(impact_qualifier_types(statements[source]['text'])) -
                           context_types[source])
            for source in plan['impact_ids']
        }
        missing_context = {source: kinds for source, kinds in missing_context.items()
                           if kinds}
        require(not missing_context,
                'impact qualifier missing from formal plan: ' +
                json.dumps(missing_context, sort_keys=True, separators=(',', ':')))
        if context_expressions:
            context = _and(context_expressions)
            safety = {'op': 'implies', 'args': [context, safety]}
            effects = _and([context, effects])
    if version in (FIXED_PLAN_VERSION, EXPANDED_PLAN_VERSION):
        referenced = (_expression_variables(safety) | _expression_variables(effects) |
                      set().union(*(_expression_variables(x) for x in p_expressions)))
        declared_derived = {
            name for name in referenced
            if plan['symbols'][name]['checkpoint'].strip().lower().startswith('derived')
        }
        require(declared_derived <= set(targets),
                'referenced derived symbol lacks definition')
        if definition_expressions:
            definitions = _and(definition_expressions)
            # I is valid under the report-grounded definitions; V is its exact
            # constructive negation under those same definitions.
            safety = {'op': 'implies', 'args': [definitions, safety]}
            effects = _and([definitions, effects])
    require(r.expr_type(safety, symbols) == ('bool', None) and
            r.expr_type(effects, symbols) == ('bool', None), 'synthesized property is not Boolean')

    p_sources = plan['precondition_ids']
    i_sources = [plan['intent_id']]
    v_sources = plan['impact_ids']
    p_text = '; '.join(statements[x]['text'] for x in p_sources)
    i_text = statements[plan['intent_id']]['text']
    v_text = '; '.join(statements[x]['text'] for x in v_sources)
    properties = {
        'preconditions': {'text': p_text, 'expression': p_expression,
                          'evidence_ids': _evidence(p_sources, statements) if p_sources else [],
                          'derivation': 'Program conjunction of selected report preconditions.',
                          'source_ids': p_sources},
        'safety': {'text': i_text, 'expression': safety,
                   'evidence_ids': _evidence(i_sources, statements),
                   'derivation': 'Program synthesis from the selected intent and logical pattern.',
                   'source_ids': i_sources},
        'effects': {'text': v_text, 'expression': effects,
                    'evidence_ids': _evidence(v_sources, statements),
                    'derivation': 'Program-generated direct negation witness for the selected safety pattern.',
                    'source_ids': v_sources},
    }
    formula_sources = {
        'preconditions': _links(p_expression, p_sources, symbols) if p_expression else {},
        'safety': _links(safety, i_sources, symbols),
        'effects': _links(effects, v_sources, symbols),
    }
    modality = ('potential' if any(statements[x]['modality'] == 'potential' for x in v_sources)
                else 'inferred' if any(statements[x]['modality'] == 'inferred' for x in v_sources)
                else 'asserted')
    unselected = [row['id'] for row in elements['statements']
                  if row['kind'] == 'impact' and row['id'] not in v_sources]
    limitations = list(plan['limitations']) + [f'Deferred report impact: {x}' for x in unselected]
    claim = {
        'id': 'core_claim', 'scope': elements['scope']['flow'], 'modality': modality,
        'impact_ids': v_sources, 'properties': properties, 'formula_sources': formula_sources,
        'effect_coverage': [{'statement_id': x, 'status': 'formalized',
                             'reason': 'Program-generated exact coverage for selected direct impact.'}
                            for x in v_sources],
        'assumptions': plan['assumptions'], 'unresolved': formal_unresolved,
    }
    return {'schema_version': 'report-formalization/2', 'symbols': output_symbols,
            'claims': [claim], 'limitations': limitations}
