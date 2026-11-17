"""Deterministically compile a compact neural semantic plan into formalization/2."""
import json
import re

import z3

from lib import report_only as r
from lib.piv_contract import PIV_PROPERTY_NAMES
from lib.semantic_core import (identifier, predicate_paths, require, strings,
                              MAX_PLAN_SYMBOLS)
from lib.solving import (direct_relation_diagnostics, direct_relation_feasible,
                         setup as relation_setup)


PLAN_VERSION = 'report-formal-plan/1'
STRUCTURED_PLAN_VERSION = 'report-formal-plan/2'
CLASSIFIED_PLAN_VERSION = 'report-formal-plan/3'
FIXED_PLAN_VERSION = 'report-formal-plan/4'
LEGACY_EXPANDED_PLAN_VERSION = 'report-formal-plan/5'
EXPANDED_PLAN_VERSION = 'report-formal-plan/6'
LIVE_EXPANDED_PLAN_VERSION = 'report-formal-plan/8'
LIVE_RELAXED_PLAN_VERSIONS = ('report-formal-plan/7',
                              LIVE_EXPANDED_PLAN_VERSION)
EXPANDED_PLAN_VERSIONS = (LEGACY_EXPANDED_PLAN_VERSION,
                          EXPANDED_PLAN_VERSION,
                          'report-formal-plan/7',
                          LIVE_EXPANDED_PLAN_VERSION)
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

PLAN_SYMBOL_REQUIRED_FIELDS = {
    'sort', 'unit', 'meaning', 'checkpoint', 'entity_ids', 'source_ids'}
PLAN_SYMBOL_OPTIONAL_FIELDS = {
    'scope', 'observable_kind', 'receiver', 'contract_type', 'binding_risk'}
OBSERVABLE_KINDS = {
    'state', 'getter', 'call', 'derived', 'timestamp', 'balance', 'mapping',
    'struct_field'}
SYMBOL_SCOPES = {'business', 'poc_instance', 'cross_contract'}
BINDING_RISKS = {'low', 'medium', 'high'}

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


_EXPANDED_PATTERN_TO_CLASSES = {}
for _expanded_class, _expanded_kind in EXPANDED_RELATION_CLASS_PATTERN.items():
    _EXPANDED_PATTERN_TO_CLASSES.setdefault(_expanded_kind, set()).add(_expanded_class)

IMPACT_QUALIFIER_PATTERNS = {
    'temporal': re.compile(
        r'\b(?:after|before|once|until|while|only\s+(?:after|before|while))\b',
        re.IGNORECASE),
    'trigger': re.compile(
        r'\b(?:if|when|whenever|upon|during|provided\s+that)\b',
        re.IGNORECASE),
    'threshold': re.compile(
        r'\b(?:exceeds?|below|above|at\s+least|at\s+most|more\s+than|'
        r'less\s+than|greater\s+than|lower\s+than|higher\s+than|'
        r'fewer\s+than)\b', re.IGNORECASE),
    'comparison_direction': re.compile(
        r'\b(?:more\s+than|less\s+than|greater\s+than|lower\s+than|'
        r'higher\s+than|fewer\s+than|increases?|decreases?|rises?|falls?|'
        r'drops?|declines?|exceeds?|underperforms?)\b', re.IGNORECASE),
    'state': re.compile(
        r'\b(?:despite|even\s+(?:if|when|though)|only\s+(?:if|when))\b',
        re.IGNORECASE),
    'scope': re.compile(
        r'\b(?:all|every|each|entire|whole|any|newly\s+created|'
        r'newly\s+deployed)\b', re.IGNORECASE),
    'duration_or_repetition': re.compile(
        r'\b(?:permanent(?:ly)?|forever|indefinitely|continuously|'
        r'repeatedly|repeated|constantly|keep\s+(?:re)?(?:deposit|submit|retry)|'
        r'for\s+\d+\s+(?:seconds?|minutes?|hours?|days?))\b', re.IGNORECASE),
    'range': re.compile(
        r'\b(?:between\s+\S+\s+and\s+\S+|from\s+\S+\s+to\s+\S+|'
        r'range\s+of|up\s+to|approximately|about)\b', re.IGNORECASE),
    'rate_or_cost': re.compile(
        r'(?:\bper\s+(?:second|minute|hour|day|week|month)|'
        r'\b\d+(?:\.\d+)?\s*(?:gwei|wei|usd|\$)|\bcosts?\b)',
        re.IGNORECASE),
}


def impact_qualifier_types(text):
    """Classify explicit impact conditions and qualifiers for formal-plan auditing."""
    return sorted(name for name, pattern in IMPACT_QUALIFIER_PATTERNS.items()
                  if pattern.search(text))


def _legacy_impact_qualifier_types(text):
    """Qualifier contract used by frozen /5 plans during deterministic replay."""
    legacy_types = {'temporal', 'threshold', 'state'}
    return sorted(set(impact_qualifier_types(text)) & legacy_types)


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


def _plan_referenced_symbols(plan):
    """Symbols referenced by a plan predicate, pattern, or derived expression."""
    symbols = plan.get('symbols') if isinstance(plan, dict) else None
    symbols = symbols if isinstance(symbols, dict) else {}
    names = set(symbols)
    referenced = set()

    def add(name):
        if isinstance(name, str) and name in names:
            referenced.add(name)

    for term in list(plan.get('precondition_terms') or []) + \
            list(plan.get('impact_context_terms') or []):
        if isinstance(term, dict):
            _referenced_plan_symbols(term.get('predicate'), add)
    outcome = plan.get('impact_outcome')
    if isinstance(outcome, dict):
        _referenced_plan_symbols(outcome.get('predicate'), add)
    _referenced_plan_symbols(plan.get('pattern'), add)
    for item in plan.get('derived_definitions') or []:
        if isinstance(item, dict):
            _referenced_plan_symbols(item.get('expression'), add)
    return referenced


def observability_contract(plan):
    """Return per-symbol stage-3 observability metadata declared by a plan.

    The contract is deliberately separate from ``formalization.json``: the
    report-only formal claim schema stays byte-compatible, while stage 3 can
    receive the extra routing metadata through ``binding_contract``.  Old plans
    carry no observability fields; those rows keep ``binding_risk: null`` so
    replay of historical bundles is unchanged.
    """
    symbols = plan.get('symbols') if isinstance(plan, dict) else None
    symbols = symbols if isinstance(symbols, dict) else {}
    definitions = plan.get('derived_definitions') if isinstance(plan, dict) else None
    derived_targets = {
        item.get('symbol') for item in (definitions or [])
        if isinstance(item, dict)}
    contract_present = any(
        isinstance(item, dict) and
        (set(item) & PLAN_SYMBOL_OPTIONAL_FIELDS)
        for item in symbols.values())
    referenced = _plan_referenced_symbols(plan)
    rows = {}
    high_risk = []
    for name in sorted(symbols):
        item = symbols[name] if isinstance(symbols[name], dict) else {}
        kind = item.get('observable_kind')
        scope = item.get('scope')
        missing = []
        if contract_present and name in referenced:
            if kind not in OBSERVABLE_KINDS:
                missing.append('observable_kind')
            if scope not in SYMBOL_SCOPES:
                missing.append('scope')
            if kind == 'derived' and name not in derived_targets:
                missing.append('derived_definition')
            if scope == 'cross_contract' and not (
                    isinstance(item.get('receiver'), str) and
                    item['receiver'].strip()):
                missing.append('receiver')
        risk = item.get('binding_risk')
        if risk not in BINDING_RISKS:
            risk = ('high' if (contract_present and missing) else
                    'low' if contract_present else None)
        if risk == 'high':
            high_risk.append(name)
        rows[name] = {
            'observable_kind': kind,
            'scope': scope,
            'receiver': item.get('receiver'),
            'contract_type': item.get('contract_type'),
            'binding_risk': risk,
            'missing': missing,
        }
    return {
        'schema_version': 'observability-contract/1',
        'contract_present': contract_present,
        'symbols': rows,
        'high_risk': high_risk,
    }


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


def _quantity_expression(value, symbols, depth=0, enforce_units=True):
    require(depth <= 3 and isinstance(value, dict), 'invalid quantity expression')
    if set(value) in ({'symbol'}, {'const'}, {'power_of_two', 'offset'}):
        expression = _operand(value, symbols)
        sort, _ = r.expr_type(expression, symbols, enforce_units=enforce_units)
        require(sort in ('int', 'literal'), 'quantity expression requires integer')
        return expression
    require(set(value) == {'op', 'args'} and value['op'] in ('add', 'sub', 'mul') and
            isinstance(value['args'], list) and len(value['args']) == 2,
            'invalid quantity expression')
    expression = {'op': value['op'], 'args': [
        _quantity_expression(item, symbols, depth + 1, enforce_units)
        for item in value['args']]}
    require(r.expr_type(expression, symbols, enforce_units=enforce_units)[0] in ('int', 'literal'),
            'invalid quantity expression types')
    return expression


def _predicate(value, symbols, depth=0, enforce_units=True):
    require(depth <= 4 and isinstance(value, dict) and value.get('kind') in (
        'truth', 'comparison', 'divisible_by', 'all_of', 'any_of', 'relation'),
            'invalid predicate binding')
    if value['kind'] in ('all_of', 'any_of'):
        require(set(value) == {'kind', 'terms'} and isinstance(value['terms'], list) and
                2 <= len(value['terms']) <= 8, 'invalid compound predicate')
        expressions = [_predicate(item, symbols, depth + 1, enforce_units)
                       for item in value['terms']]
        return _and(expressions) if value['kind'] == 'all_of' else _or(expressions)
    if value['kind'] == 'relation':
        require(set(value) == {'kind', 'left', 'operator', 'right'} and
                value['operator'] in ('eq', 'ne', 'lt', 'le', 'gt', 'ge'),
                'invalid quantity relation')
        require(value['left'] != value['right'],
                'trivial self-comparison predicate')
        expression = {'op': value['operator'], 'args': [
            _quantity_expression(value['left'], symbols, enforce_units=enforce_units),
            _quantity_expression(value['right'], symbols, enforce_units=enforce_units)]}
        require(r.expr_type(expression, symbols, enforce_units=enforce_units) == ('bool', None),
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
        require(r.expr_type(expression, symbols, enforce_units=enforce_units) == ('bool', None),
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
    require(r.expr_type(expression, symbols, enforce_units=enforce_units) == ('bool', None),
            'invalid comparison types/units')
    return expression


def _and(expressions):
    require(bool(expressions), 'empty conjunction')
    return expressions[0] if len(expressions) == 1 else {'op': 'and', 'args': expressions}


def _or(expressions):
    require(bool(expressions), 'empty disjunction')
    return expressions[0] if len(expressions) == 1 else {'op': 'or', 'args': expressions}


def _not(expression):
    return {'op': 'not', 'args': [expression]}


def _collapse_double_negation(expression):
    """Drop ``not(not(x))`` so cross-auditors read the witness literally.

    ``_predicate`` encodes a false truth binding as ``not(x)``, and the
    direct-witness effect then negates the pattern's effect once more.  The
    result is logically equivalent to ``x`` but the redundant double negation
    makes the faithfulness auditor misread the polarity of V.  Collapse only
    under the live direct-witness feature so frozen plan schemas keep their
    byte-for-byte replay shape.
    """
    if not isinstance(expression, dict):
        return expression
    if expression.get('op') == 'not':
        args = expression.get('args')
        if (isinstance(args, list) and len(args) == 1 and
                isinstance(args[0], dict) and args[0].get('op') == 'not' and
                isinstance(args[0].get('args'), list) and
                len(args[0]['args']) == 1):
            return _collapse_double_negation(args[0]['args'][0])
    args = expression.get('args')
    if isinstance(args, list):
        return {**expression, 'args': [_collapse_double_negation(x) for x in args]}
    return expression


def _expression_variables(expression):
    if not isinstance(expression, dict):
        return set()
    if set(expression) == {'var'}:
        return {expression['var']}
    return {name for child in expression.get('args', [])
            for name in _expression_variables(child)}


def _numeric_relation_ops(expression):
    """Return the numeric arithmetic/comparison ops present in an expression."""
    ops = set()

    def walk(node):
        if not isinstance(node, dict):
            return
        if isinstance(node.get('op'), str):
            ops.add(node['op'])
        for child in (node.get('args') or []):
            walk(child)
    walk(expression)
    return ops & {'lt', 'gt', 'lte', 'gte', 'add', 'sub', 'mul', 'div', 'mod'}


def _numeric_symbols(claim):
    """Return symbol names whose declared sort is numeric (int/real)."""
    symbols = claim.get('symbols') or {}
    return {name for name, item in symbols.items()
            if isinstance(item, dict) and item.get('sort') in ('int', 'real')}


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


def _plan_truth_literal(value):
    """Return (symbol, boolean) for a truth atom; None otherwise."""
    if not isinstance(value, dict) or value.get('kind') != 'truth':
        return None
    if not isinstance(value.get('symbol'), str) or not isinstance(value.get('value'), bool):
        return None
    return value['symbol'], value['value']


def _negated_condition_outcome_symbol(plan):
    """Detect the direct-witness contradiction where the impact outcome is the

    negation of the pattern condition (V contains condition AND NOT condition).
    Returns the shared Boolean symbol, or None when the shape is absent.
    """
    if not isinstance(plan, dict):
        return None
    pattern = plan.get('pattern') if isinstance(plan.get('pattern'), dict) else None
    outcome = plan.get('impact_outcome') if isinstance(plan.get('impact_outcome'), dict) else None
    if pattern is None or outcome is None:
        return None
    condition = pattern.get('condition')
    predicate = outcome.get('predicate')
    c = _plan_truth_literal(condition)
    o = _plan_truth_literal(predicate)
    if c and o and c[0] == o[0] and c[1] != o[1]:
        return c[0]
    return None


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


def classified_relation_alignment(plan, elements, allow_missing=False):
    """Audit that classified I/V observables are grounded by intent and impacts."""
    require(plan.get('schema_version') in (
        CLASSIFIED_PLAN_VERSION, FIXED_PLAN_VERSION, *EXPANDED_PLAN_VERSIONS),
            'relation alignment requires plan schema v3')
    statements = _index(elements['statements'], 'statement')
    core_symbols = sorted(_core_relation_symbols(plan['pattern']))
    if plan.get('schema_version') == LIVE_EXPANDED_PLAN_VERSION:
        core_symbols = sorted(set(core_symbols) |
                              _predicate_binding_symbols(
                                  plan['impact_outcome']['predicate']))
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
    if not allow_missing:
        require(not missing, 'core relation observables lack intent/impact grounding')
    require(all(source in statements for source in source_union),
            'core relation observable has unknown source')
    result = {
        'schema_version': ('safety-relation-alignment/1'
                           if plan.get('schema_version') == CLASSIFIED_PLAN_VERSION
                           else 'safety-relation-alignment/3'
                           if plan.get('schema_version') in EXPANDED_PLAN_VERSIONS
                           else 'safety-relation-alignment/2'),
        'relation_class': plan['relation_class'],
        'pattern_kind': plan['pattern']['kind'],
        'core_observables': core_symbols,
        'observable_source_ids': coverage,
        'required_source_ids': required_sources,
        'missing_required_source_ids': missing,
        'direct_negation_by_construction':
            plan.get('schema_version') != LIVE_EXPANDED_PLAN_VERSION,
        'passed': not missing,
    }
    if allow_missing:
        result['review_only'] = True
    if plan.get('schema_version') in (FIXED_PLAN_VERSION, *EXPANDED_PLAN_VERSIONS):
        result.update({'intent_source_id': plan['intent_id'],
                       'intent_grounding': 'selected_safety_property'})
    return result


def _evidence(source_ids, statements):
    return _unique([evidence for source in source_ids
                    for evidence in statements[source]['evidence_ids']])


def _links(expression, source_ids, symbols):
    if not source_ids:
        return {}
    return {path: list(source_ids) for path in predicate_paths(expression, symbols)}


def structured_unresolved_review(plan, elements):
    """Validate v2 unresolved records and separate blocking from audit-only items."""
    require(plan.get('schema_version') in (
        STRUCTURED_PLAN_VERSION, CLASSIFIED_PLAN_VERSION, FIXED_PLAN_VERSION,
        *EXPANDED_PLAN_VERSIONS),
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


def _relocated_trigger_predicates(plan, symbols):
    """Return ``truth`` condition/effect predicates that are P-scope triggers.

    For implication-shaped patterns the antecedent must be witnessed by the
    PoC precondition, not asserted inside the injected invariant.  When a
    boolean event condition is grounded by the intent/impact instead of an
    explicit precondition, it is a scenario trigger and must move to P so the
    safety property stays unconditional (otherwise ``trigger=False`` makes the
    invariant vacuously true).

    This covers every implication-shaped template:
    * ``condition``-based templates (required_effect, correspondence, ...)
    * ``trigger``-based templates (monotonicity, conservation, preservation)
    * ``effect``-based authorization templates (authorization_guard and
      effect_requires_any_authorization) where the guarded effect is the
      scenario trigger.
    """
    pattern = plan.get('pattern') or {}
    kind = pattern.get('kind')
    candidate = pattern.get('condition')
    if kind in ('monotonicity', 'conservation', 'preservation'):
        candidate = pattern.get('trigger')
    if not (isinstance(candidate, dict) and candidate.get('kind') == 'truth'):
        return []
    name = candidate.get('symbol')
    if name not in symbols or symbols[name].get('sort') != 'bool':
        return []
    sources = set(symbols[name].get('source_ids') or [])
    preconditions = set(plan.get('precondition_ids') or [])
    if sources & preconditions:
        return []
    return [candidate]


def _pattern_expressions(pattern, symbols, enforce_units=True,
                         trigger_symbols=None):
    require(isinstance(pattern, dict) and pattern.get('kind') in PATTERNS,
            'unknown synthesis pattern')
    trigger_symbols = trigger_symbols or set()

    def _scoped(condition_dict, condition_expr, consequent, negate=False):
        """Build ``condition -> consequent`` unless the condition is a P-scope
        trigger, in which case the bare consequent is returned (the trigger
        moves to P so the injected invariant stays unconditional).
        """
        atom = None
        if (isinstance(condition_dict, dict) and condition_dict.get('kind') == 'truth'
                and condition_dict.get('symbol') in trigger_symbols):
            atom = consequent if not negate else _not(consequent)
        else:
            atom = {'op': 'implies', 'args': [condition_expr, consequent if not negate
                                              else _not(consequent)]}
        return atom

    kind = pattern['kind']
    if kind in ('condition_forbids_effect', 'condition_requires_effect'):
        require(set(pattern) == {'kind', 'condition', 'effect'}, 'invalid condition pattern')
        condition = _predicate(pattern['condition'], symbols, enforce_units=enforce_units)
        effect = _predicate(pattern['effect'], symbols, enforce_units=enforce_units)
        if kind == 'condition_forbids_effect':
            return _scoped(pattern['condition'], condition, effect, negate=True), _and([condition, effect])
        return _scoped(pattern['condition'], condition, effect), _and([condition, _not(effect)])
    if kind == 'effect_requires_any_authorization':
        require(set(pattern) == {'kind', 'effect', 'authorization_terms'} and
                isinstance(pattern['authorization_terms'], list) and
                bool(pattern['authorization_terms']), 'invalid authorization pattern')
        effect = _predicate(pattern['effect'], symbols, enforce_units=enforce_units)
        authorization = _or([_predicate(x, symbols, enforce_units=enforce_units)
                             for x in pattern['authorization_terms']])
        return {'op': 'implies', 'args': [effect, authorization]}, _and([effect, _not(authorization)])
    if kind == 'authorization_guard':
        require(set(pattern) == {'kind', 'effect', 'authorization'},
                'invalid authorization guard pattern')
        effect = _predicate(pattern['effect'], symbols, enforce_units=enforce_units)
        authorization = _predicate(pattern['authorization'], symbols,
                                   enforce_units=enforce_units)
        return {'op': 'implies', 'args': [effect, authorization]}, \
            _and([effect, _not(authorization)])
    if kind == 'relation_obligation':
        require(set(pattern) == {'kind', 'condition', 'relation'},
                'invalid relation obligation pattern')
        condition = _predicate(pattern['condition'], symbols, enforce_units=enforce_units)
        relation = _predicate(pattern['relation'], symbols, enforce_units=enforce_units)
        return _scoped(pattern['condition'], condition, relation), \
            _and([condition, _not(relation)])
    if kind == 'bounded_relation':
        require(set(pattern) == {'kind', 'condition', 'value', 'operator', 'bound'} and
                pattern['operator'] in ('lt', 'le', 'gt', 'ge'),
                'invalid bounded relation pattern')
        condition = _predicate(pattern['condition'], symbols, enforce_units=enforce_units)
        relation = {'op': pattern['operator'], 'args': [
            _quantity_expression(pattern['value'], symbols, enforce_units=enforce_units),
            _quantity_expression(pattern['bound'], symbols, enforce_units=enforce_units)]}
        require(r.expr_type(relation, symbols, enforce_units=enforce_units) == ('bool', None),
                'bounded relation type/unit mismatch')
        return _scoped(pattern['condition'], condition, relation), \
            _and([condition, _not(relation)])
    if kind == 'correspondence':
        require(set(pattern) == {'kind', 'condition', 'observed_symbol',
                                 'expected_symbol'},
                'invalid correspondence pattern')
        observed, expected = pattern['observed_symbol'], pattern['expected_symbol']
        require(observed in symbols and expected in symbols,
                'unknown correspondence symbol')
        condition = _predicate(pattern['condition'], symbols, enforce_units=enforce_units)
        relation = {'op': 'eq', 'args': [{'var': observed}, {'var': expected}]}
        require(r.expr_type(relation, symbols, enforce_units=enforce_units) == ('bool', None),
                'correspondence type/unit mismatch')
        return _scoped(pattern['condition'], condition, relation), \
            _and([condition, _not(relation)])
    if kind == 'temporal_order':
        require(set(pattern) == {'kind', 'condition', 'earlier_symbol',
                                 'later_symbol', 'strict'} and
                type(pattern['strict']) is bool,
                'invalid temporal order pattern')
        earlier, later = pattern['earlier_symbol'], pattern['later_symbol']
        require(earlier in symbols and later in symbols,
                'unknown temporal order symbol')
        if symbols[earlier]['sort'] != 'int' or symbols[later]['sort'] != 'int':
            raise ValueError(
                'temporal_order earlier/later symbols must be integer '
                'quantities with units; for boolean event ordering use '
                'progress_or_liveness/required_effect instead')
        condition = _predicate(pattern['condition'], symbols, enforce_units=enforce_units)
        relation = {'op': 'lt' if pattern['strict'] else 'le',
                    'args': [{'var': earlier}, {'var': later}]}
        require(r.expr_type(relation, symbols, enforce_units=enforce_units) == ('bool', None),
                'temporal order type/unit mismatch')
        return _scoped(pattern['condition'], condition, relation), \
            _and([condition, _not(relation)])
    if kind == 'required_effect':
        require(set(pattern) == {'kind', 'condition', 'effect'},
                'invalid required effect pattern')
        condition = _predicate(pattern['condition'], symbols, enforce_units=enforce_units)
        effect = _predicate(pattern['effect'], symbols, enforce_units=enforce_units)
        return _scoped(pattern['condition'], condition, effect), \
            _and([condition, _not(effect)])
    if kind == 'proportional_relation':
        require(set(pattern) == {'kind', 'condition', 'left', 'operator', 'right'} and
                pattern['operator'] in ('eq', 'le', 'ge'),
                'invalid proportional relation pattern')
        condition = _predicate(pattern['condition'], symbols, enforce_units=enforce_units)
        relation = {'op': pattern['operator'], 'args': [
            _quantity_expression(pattern['left'], symbols, enforce_units=enforce_units),
            _quantity_expression(pattern['right'], symbols, enforce_units=enforce_units)]}
        require(r.expr_type(relation, symbols, enforce_units=enforce_units) == ('bool', None),
                'proportional relation type/unit mismatch')
        return _scoped(pattern['condition'], condition, relation), \
            _and([condition, _not(relation)])
    if kind == 'monotonicity':
        require(set(pattern) == {'kind', 'trigger', 'before_symbol', 'after_symbol',
                                 'direction'} and
                pattern['direction'] in ('nondecreasing', 'nonincreasing'),
                'invalid monotonicity pattern')
        require(pattern['before_symbol'] in symbols and pattern['after_symbol'] in symbols,
                'unknown monotonicity symbol')
        trigger = _predicate(pattern['trigger'], symbols, enforce_units=enforce_units)
        relation = {'op': 'ge' if pattern['direction'] == 'nondecreasing' else 'le',
                    'args': [{'var': pattern['after_symbol']},
                             {'var': pattern['before_symbol']}]}
        require(r.expr_type(relation, symbols, enforce_units=enforce_units) == ('bool', None),
                'monotonicity type/unit mismatch')
        return _scoped(pattern['trigger'], trigger, relation), \
            _and([trigger, _not(relation)])
    if kind == 'conservation':
        require(set(pattern) == {'kind', 'trigger', 'before', 'after'},
                'invalid conservation pattern')
        trigger = _predicate(pattern['trigger'], symbols, enforce_units=enforce_units)
        before = _quantity_expression(pattern['before'], symbols, enforce_units=enforce_units)
        after = _quantity_expression(pattern['after'], symbols, enforce_units=enforce_units)
        relation = {'op': 'eq', 'args': [after, before]}
        require(r.expr_type(relation, symbols, enforce_units=enforce_units) == ('bool', None),
                'conservation type/unit mismatch')
        return _scoped(pattern['trigger'], trigger, relation), \
            _and([trigger, _not(relation)])
    require(set(pattern) == {'kind', 'trigger', 'before_symbol', 'after_symbol'},
            'invalid preservation pattern')
    require(pattern['before_symbol'] in symbols and pattern['after_symbol'] in symbols,
            'unknown preservation symbol')
    trigger = _predicate(pattern['trigger'], symbols, enforce_units=enforce_units)
    equal = {'op': 'eq', 'args': [{'var': pattern['after_symbol']},
                                  {'var': pattern['before_symbol']}]}
    require(r.expr_type(equal, symbols, enforce_units=enforce_units) == ('bool', None),
            'state preservation type/unit mismatch')
    return _scoped(pattern['trigger'], trigger, equal), _and([trigger, _not(equal)])


#: ``a op b`` is ``b MIRROR[op] a`` for the directional ops; folding direction
#: makes mirrored comparisons (blind-batch_03 GTE: the two salt facts as
#: ``real ne derived`` and ``derived ne real``) one predicate.
_MIRROR = {'lt': 'gt', 'le': 'ge'}
_COMPARISON_OPS = ('eq', 'ne', 'lt', 'le', 'gt', 'ge')


def _operand_key(operand):
    """One key per logical operand: a symbol may be written either as a bare
    name or as ``{"symbol": name}``, and the two spellings are the same
    operand (blind-batch_03 GTE wrote one side of each mirror differently)."""
    if isinstance(operand, str):
        return json.dumps(['sym', operand])
    if (isinstance(operand, dict) and set(operand) == {'symbol'}
            and isinstance(operand['symbol'], str)):
        return json.dumps(['sym', operand['symbol']])
    return json.dumps(operand, sort_keys=True, separators=(',', ':'))


def predicate_keys(predicate):
    """Canonical keys under which two P predicates count as reused.

    The first key folds exact JSON equality and logical mirrors (swapped
    eq/ne sides; ``a lt b`` vs ``b gt a``).  The second, optional key is the
    zero-bound family: the same single symbol compared against ``const 0``
    from two distinct sources (blind-batch_03 Monetrix: ``borrow_value > 0``
    and ``borrow_value != 0``).  Those are NOT logically equivalent over the
    integers, but at most one report fact can live in a same-observable
    zero-bound predicate, so a second source constraining the same pair is
    the same silent fact-drop the exact duplicate causes.
    """
    if not isinstance(predicate, dict) or predicate.get('kind') != 'comparison':
        return [json.dumps(predicate, sort_keys=True, separators=(',', ':'))]
    left, right = predicate.get('left'), predicate.get('right')
    op = predicate.get('operator')
    if op not in _COMPARISON_OPS:
        return [json.dumps(['cmp', _operand_key(left), _operand_key(right), op],
                           separators=(',', ':'))]
    if op in ('eq', 'ne'):
        # Commutative: order the two sides so mirrors fold.
        sides = sorted((_operand_key(left), _operand_key(right)))
        keys = [json.dumps(['cmp', *sides, op], separators=(',', ':'))]
    else:
        # Directional: a lt b -> (gt, b, a); a le b -> (ge, b, a).  gt/ge
        # keep their orientation, so 0 lt x and x gt 0 fold onto one key.
        first, second, oriented = ((right, left, _MIRROR[op])
                                   if op in ('lt', 'le') else (left, right, op))
        keys = [json.dumps(['cmp', _operand_key(first), _operand_key(second),
                            oriented], separators=(',', ':'))]
    if ((isinstance(left, str) and right == {'const': 0}) or
            (isinstance(right, str) and left == {'const': 0})):
        symbol_key = _operand_key(left) if isinstance(left, str) \
            else _operand_key(right)
        keys.append(json.dumps(['zero', symbol_key], separators=(',', ':')))
    return keys


def identical_p_predicates(plan):
    """``source_id``s whose P predicate repeats an earlier source's.

    Two distinct precondition sources must not share one predicate: the
    conjunction then collapses (``(and X X)`` is just ``X``) and one of the
    report's facts stops being represented, with nothing left to notice it.  The
    SMT shows it directly as a doubled conjunct in ``report_preconditions``.

    "Repeats" covers exact equality, mirrored comparisons and the same-symbol
    zero-bound family (see ``predicate_keys``).  Deliberately NOT used to
    reject under ``report-formal-plan/4``: one frozen run in the replay
    battery carries a duplicate, so tightening the live schema would break
    its recorded artifacts.  ``cli/batch_verify.py`` reports this instead --
    verification output is not an artifact, so old runs stay replayable while
    the defect becomes visible for every run, old and new.
    """
    seen, duplicates = set(), []
    for term in plan.get('precondition_terms') or []:
        if not isinstance(term, dict) or 'predicate' not in term:
            continue
        keys = predicate_keys(term['predicate'])
        if any(key in seen for key in keys):
            duplicates.append(term.get('source_id'))
        else:
            seen.update(keys)
    return duplicates


def check_distinct_p_predicates(plan):
    """Gate form of ``identical_p_predicates`` for live runs (semantic-live-5).

    The v5 schema already rejects a repeated predicate outright; under v4 the
    rejection was deliberately withheld because a frozen replay-battery run
    carries a duplicate.  Feature-gating the same check keeps that run
    replayable (its recorded features predate the key) while new live runs
    fail loudly instead of silently dropping one of the report's facts.
    """
    duplicates = identical_p_predicates(plan)
    require(not duplicates, 'distinct P sources reuse identical predicate')


#: Cues that a statement's content comes from an external document or spec
#: rather than the incident narrative.  Advisory only (n=1 observed defect:
#: SukukFi final-holdout P mixed a documentation requirement into the facts).
#: Matching the cue never rewrites anything; it surfaces the statement for
#: review in ``requirement-source-review.json``.
REQUIREMENT_CUES = (
    re.compile(r'\b(?:documentation|docs?|spec(?:ification)?s?|whitepaper|'
               r'readme|standard)\b[^.]{0,120}\b(?:states?|says?|requires?|'
               r'specifies?|mandates?|dictates?)\b', re.IGNORECASE),
    re.compile(r'\b(?:per|according to|as per)\s+the\s+(?:documentation|docs?|'
               r'spec(?:ification)?s?|whitepaper|standard)\b', re.IGNORECASE),
    re.compile(r'\bthe\s+.{0,40}\b(?:documentation|spec(?:ification)?s?)\b'
               r'[^.]{0,80}\b(?:should|must|is expected)\b', re.IGNORECASE),
)


def requirement_source_review(elements, plan):
    """Flag P sources whose text cites documentation requirements.

    A precondition must be a fact of the incident; a statement grounded in
    what external documentation *should* say is a normative expectation, not
    an observed before-condition.  The distinction is semantic, so this stays
    a review (visible, never auto-rejecting): one real defect family is known
    and the stingy threshold for a gate is not met.
    """
    flagged = []
    for term in plan.get('precondition_terms') or []:
        source_id = term.get('source_id') if isinstance(term, dict) else None
        row = next((x for x in elements['statements']
                    if isinstance(x, dict) and x.get('id') == source_id), None)
        if row is None:
            continue
        matched = [pattern.pattern for pattern in REQUIREMENT_CUES
                   if pattern.search(row.get('text', ''))]
        if matched:
            flagged.append({
                'statement_id': source_id,
                'statement_kind': row.get('kind'),
                'statement_text': row.get('text'),
                'matched_cue_count': len(matched),
            })
    return {
        'schema_version': 'requirement-source-review/1',
        'advisory_only': True,
        'blocks_candidate_acceptance': False,
        'flagged_count': len(flagged),
        'flagged': flagged,
        'note': ('A flagged P source cites documentation/spec requirements; '
                 'verify it is an incident fact, not a normative expectation. '
                 'This review never rewrites or rejects the plan.'),
    }


#: Cues that a statement asserts a structural derivation -- how a value is
#: computed -- which the plan language (symbol comparisons) cannot express.
#: A bare truth symbol standing in for such a fact names it without encoding
#: it (blind-batch_03: both GTE salt facts became truth symbols sharing one
#: derived-address concept).  Advisory only: the cue is lexical, not semantic.
STRUCTURAL_DERIVATION_CUES = (
    re.compile(r'\bkeccak\b|\bcreate2\b|\bsalt\b', re.IGNORECASE),
    re.compile(r'\bhash(?:ed|ing)?\b\s+(?:of|with|using)\b', re.IGNORECASE),
    re.compile(r'\b(?:derived|computed|calculated)\s+'
               r'(?:from|using|via|by|as)\b', re.IGNORECASE),
    re.compile(r'abi\.encode', re.IGNORECASE),
)


def placeholder_predicate_review(elements, plan):
    """Flag P predicates that stand in for facts they cannot express.

    Two flags, both advisory (``blocks_candidate_acceptance`` stays False --
    the cues are lexical and one blind-batch defect family is stingy
    evidence for a gate):

    - ``truth_placeholder``: the source statement asserts a structural
      derivation (a salt, a hash, a computed formula) but its P predicate
      is a bare truth symbol.  The symbol names the fact; the fact's
      structure stays unrepresented, so the review asks for a distinct
      observable per source, an honest unresolved entry, or a relocation
      to assumptions.
    - ``trivial_zero_bound``: a non-strict zero bound (``x >= 0`` /
      ``x <= 0``) whose statement does not literally state a zero
      comparison.  Such a bound is satisfied by default and carries no
      report fact (blind-batch_03 Monetrix stood four facts on such
      bounds).
    """
    flagged = []
    for term in plan.get('precondition_terms') or []:
        source_id = term.get('source_id') if isinstance(term, dict) else None
        row = next((x for x in elements['statements']
                    if isinstance(x, dict) and x.get('id') == source_id), None)
        if row is None or not isinstance(term, dict):
            continue
        predicate = term.get('predicate')
        if not isinstance(predicate, dict):
            continue
        text = row.get('text') or ''
        if (predicate.get('kind') == 'truth' and
                any(pattern.search(text) for pattern in
                    STRUCTURAL_DERIVATION_CUES)):
            flagged.append({
                'statement_id': source_id,
                'statement_kind': row.get('kind'),
                'statement_text': text,
                'flag': 'truth_placeholder',
                'predicate': {'kind': 'truth',
                              'symbol': predicate.get('symbol')},
            })
        elif predicate.get('kind') == 'comparison' and \
                predicate.get('operator') in ('ge', 'le'):
            operands = (predicate.get('left'), predicate.get('right'))
            has_zero = any(side == {'const': 0} for side in operands)
            has_symbol = any(isinstance(side, str) for side in operands)
            if has_zero and has_symbol and 'zero' not in text.lower():
                flagged.append({
                    'statement_id': source_id,
                    'statement_kind': row.get('kind'),
                    'statement_text': text,
                    'flag': 'trivial_zero_bound',
                    'predicate': predicate,
                })
    return {
        'schema_version': 'placeholder-predicate-review/1',
        'advisory_only': True,
        'blocks_candidate_acceptance': False,
        'flagged_count': len(flagged),
        'flagged': flagged,
        'note': ('A flagged P predicate likely stands in for a fact it cannot '
                 'express. Verify each: encode a distinct report-grounded '
                 'observable, record the fact in unresolved, or move it to '
                 'assumptions. This review never rewrites or rejects the '
                 'plan.'),
    }


FAITHFULNESS_VERDICTS = frozenset({'consistent', 'inverted', 'wrong_constant',
                                   'wrong_symbol', 'other_mismatch'})


def predicate_binding_symbols(value):
    """Public wrapper: names of every symbol a P predicate JSON references."""
    return set(_predicate_binding_symbols(value))


def validate_faithfulness_verdict(verdict, plan, include_relations=False):
    """Structural check of a faithfulness-audit verdict dict.

    The verdict is the only free-form input the deterministic chain later
    replays on, so its shape must be as narrow as the plan schema itself:
    exactly one row per selected P source, each with a verdict from the
    fixed enum and a one-line reason.
    """
    expected_fields = {'checks', 'piv_relation'} if include_relations else {'checks'}
    require(isinstance(verdict, dict) and set(verdict) == expected_fields,
            'invalid faithfulness verdict shape')
    checks = verdict['checks']
    require(isinstance(checks, list) and bool(checks),
            'invalid faithfulness verdict checks')
    seen = []
    for check in checks:
        check_fields = ({'source_id', 'role', 'verdict', 'reason'}
                        if include_relations else
                        {'source_id', 'verdict', 'reason'})
        require(isinstance(check, dict) and set(check) == check_fields,
                'invalid faithfulness check shape')
        require(isinstance(check['source_id'], str) and check['source_id'],
                'invalid faithfulness check source_id')
        require(check['verdict'] in FAITHFULNESS_VERDICTS,
                'invalid faithfulness verdict value')
        require(isinstance(check['reason'], str) and bool(check['reason'].strip()),
                'invalid faithfulness check reason')
        if include_relations:
            require(check['role'] in ('P', 'I', 'V'), 'invalid faithfulness check role')
        seen.append((check['source_id'], check.get('role')))
    if include_relations:
        expected = ([(source, 'P') for source in plan['precondition_ids']] +
                    [(plan['intent_id'], 'I')] +
                    [(source, 'V') for source in plan['impact_ids']])
        require(set(seen) == set(expected) and len(seen) == len(expected),
                'faithfulness verdict must cover selected P/I/V sources exactly once')
        relation = verdict['piv_relation']
        require(isinstance(relation, dict) and set(relation) == {'verdict', 'reason'} and
                relation['verdict'] in ('consistent', 'weakened', 'mismatch') and
                isinstance(relation['reason'], str) and relation['reason'].strip(),
                'invalid P/I/V relation verdict')
    else:
        sources = [source for source, _role in seen]
        require(set(sources) == set(plan['precondition_ids']) and
                len(sources) == len(plan['precondition_ids']),
                'faithfulness verdict must cover selected P sources exactly once')


def faithfulness_mismatches(verdict):
    """Rows the deterministic gates replay on: non-consistent verdicts."""
    rows = [dict(check) for check in (verdict or {}).get('checks', [])
            if check.get('verdict') != 'consistent']
    relation = (verdict or {}).get('piv_relation')
    if relation and relation.get('verdict') != 'consistent':
        rows.append({'source_id': 'P/I/V relation', 'role': 'PIV',
                     'verdict': 'other_mismatch', 'reason': relation['reason']})
    return rows


def faithfulness_repair_mismatches(verdict):
    """Return only role-local formula findings eligible for a bounded repair.

    A cross-role relation finding is retained for review, but changing formulas
    that individually match their frozen sources can make them less faithful.
    """
    return [dict(check) for check in (verdict or {}).get('checks', [])
            if check.get('verdict') != 'consistent']


def faithfulness_status(verdict):
    """Classify component fidelity separately from an uncertain P/I/V link."""
    if not isinstance(verdict, dict):
        return 'unavailable'
    if any(row.get('verdict') != 'consistent'
           for row in verdict.get('checks', [])):
        return 'failed'
    relation = verdict.get('piv_relation')
    if relation is None:
        return 'passed'
    if relation.get('verdict') == 'consistent':
        return 'passed'
    if relation.get('verdict') == 'weakened':
        return 'needs_review'
    if relation.get('verdict') == 'mismatch':
        return 'failed'
    return 'unavailable'


def _referenced_plan_symbols(value, add):
    """Tolerant walk: report every declared symbol name the value mentions.

    Used only by the advisory symbol-table review, so unknown shapes are
    skipped rather than rejected.  Inside predicates, patterns and derived
    expressions every string that names a declared symbol is a reference;
    the strings that are not symbol names (operators, kinds, qualifier
    types, statement ids) simply match no declared name.
    """
    if isinstance(value, str):
        add(value)
    elif isinstance(value, dict):
        for item in value.values():
            _referenced_plan_symbols(item, add)
    elif isinstance(value, list):
        for item in value:
            _referenced_plan_symbols(item, add)


def plan_symbol_references(value, declared_symbols):
    """Names from ``declared_symbols`` referenced anywhere inside ``value``.

    Tolerant walk used by the local-repair guard: frozen fields (pattern,
    precondition_terms) must still resolve after the model is allowed to edit
    ``symbols``.  Unknown shapes are skipped instead of rejected.
    """
    names = set(declared_symbols)
    referenced = set()

    def add(name):
        if isinstance(name, str) and name in names:
            referenced.add(name)

    _referenced_plan_symbols(value, add)
    return referenced


def report_impact_expression(plan, symbols, enforce_units=False):
    """Compile the report-grounded V: impact_outcome conjoined with qualifiers.

    Excludes the pattern's program-generated direct falsifier so the
    faithfulness auditor sees the Impact statement's own observable, not the
    SMT witness assembled for the continuation gate.
    """
    predicates = []
    outcome = plan.get('impact_outcome')
    if isinstance(outcome, dict) and outcome.get('predicate') is not None:
        predicates.append(_predicate(outcome['predicate'], symbols,
                                     enforce_units=enforce_units))
    for term in plan.get('impact_context_terms') or []:
        if isinstance(term, dict) and term.get('predicate') is not None:
            predicates.append(_predicate(term['predicate'], symbols,
                                         enforce_units=enforce_units))
    return _and(predicates) if predicates else None


def symbol_table_review(plan):
    """Flag declared plan symbols no predicate or definition ever uses.

    Two flags, both advisory (``blocks_candidate_acceptance`` stays False --
    one blind-batch defect family is stingy evidence for a gate):

    - ``unreferenced_symbol``: a declared symbol that no P predicate, impact
      context term, pattern slot or derived expression references
      (blind-batch_05 GTE: ``ninety_pct_sold_flag`` declared beside the
      referenced ``ninety_pct_sold``).  The formula-layer fact is usually
      still represented once; the dead entry is symbol-table noise that
      stage 3 would otherwise have to bind or explain.
    - ``same_source_near_duplicate``: two symbols with identical
      ``source_ids`` whose normalized names share a prefix.  Same source,
      near-same name, one referenced and one not is the signature of a
      fact being redeclared instead of reused.
    """
    symbols = plan.get('symbols')
    symbols = symbols if isinstance(symbols, dict) else {}
    names = set(symbols)
    referenced = _plan_referenced_symbols(plan)

    def source_ids(name):
        meta = symbols[name]
        return sorted(meta.get('source_ids')) if isinstance(meta, dict) else []

    flagged = []
    for name in sorted(names):
        if name not in referenced:
            flagged.append({
                'symbol': name,
                'flag': 'unreferenced_symbol',
                'source_ids': source_ids(name),
            })
    order = sorted(names, key=lambda name: name.lower())
    for index, first in enumerate(order):
        for second in order[index + 1:]:
            if source_ids(first) != source_ids(second):
                continue
            low_first, low_second = first.lower(), second.lower()
            if not (low_first.startswith(low_second) or
                    low_second.startswith(low_first)):
                continue
            flagged.append({
                'symbol': first,
                'flag': 'same_source_near_duplicate',
                'duplicate_of': second,
                'source_ids': source_ids(first),
                'referenced': {first: first in referenced,
                               second: second in referenced},
            })
    contract = observability_contract(plan)
    if contract['contract_present']:
        for name in sorted(referenced & set(symbols)):
            row = contract['symbols'].get(name) or {}
            if row.get('missing'):
                flagged.append({
                    'symbol': name,
                    'flag': 'missing_observability',
                    'missing': list(row['missing']),
                    'binding_risk': row.get('binding_risk'),
                    'source_ids': source_ids(name),
                })
    return {
        'schema_version': 'symbol-table-review/1',
        'advisory_only': True,
        'blocks_candidate_acceptance': False,
        'flagged_count': len(flagged),
        'flagged': flagged,
        'note': ('A flagged symbol is declared but never used, or redeclares '
                 'a same-source neighbour under a near-duplicate name. '
                 'Deduplicate the symbol table or bind the symbol knowingly. '
                 'This review never rewrites or rejects the plan.'),
    }


#: Applicability-scope cues in an intent statement.  Advisory only: the dual
#: reviews disagreed on strictness for this family, so the check surfaces the
#: narrowing risk instead of enforcing a contested standard.
INTENT_SCOPE_CUES = re.compile(
    r'\b(?:any|every|all|whenever|only\s+(?:if|when|by|after)|for\s+any|'
    r'unauthorized|non-owner|not\s+the\s+owner|arbitrary)\b', re.IGNORECASE)

#: Pattern slot holding the applicability condition ('condition' for the
#: relation_obligation family, 'trigger' for the monotonicity family).
_CONDITION_SLOT = {
    'relation_obligation': 'condition', 'bounded_relation': 'condition',
    'correspondence': 'condition', 'temporal_order': 'condition',
    'required_effect': 'condition', 'proportional_relation': 'condition',
    'monotonicity': 'trigger', 'conservation': 'trigger',
    'state_preservation': 'trigger',
}


def intent_scope_review(plan, elements):
    """Flag condition predicates grounded only by impact statements.

    When the intent states a general applicability scope (any/every caller,
    whenever...), the condition of I must carry that scope, and scope comes
    from the intent or the preconditions -- never from the impact, which
    describes only the concrete incident subcase.  A condition whose every
    symbol is grounded solely by impact statements is the narrowing defect
    the dual reviews rated partial; this review makes it visible in every
    new run without enforcing the contested strictness.
    """
    statements = {row.get('id'): row for row in elements['statements']
                  if isinstance(row, dict)}
    intent = statements.get(plan.get('intent_id')) or {}
    scope_cues = sorted({match.group(0).lower()
                         for match in INTENT_SCOPE_CUES.finditer(
                             intent.get('text', ''))})
    pattern = plan.get('pattern') or {}
    slot = _CONDITION_SLOT.get(pattern.get('kind'))
    condition_symbols = sorted(_predicate_binding_symbols(pattern[slot])) \
        if slot and isinstance(pattern.get(slot), dict) else []
    impact_ids = set(plan.get('impact_ids') or [])
    scope_grounded = []
    impact_only = []
    for name in condition_symbols:
        symbol = (plan.get('symbols') or {}).get(name) or {}
        sources = set(symbol.get('source_ids') or [])
        if sources - impact_ids:
            scope_grounded.append(name)
        elif sources:
            impact_only.append(name)
    narrowed = bool(scope_cues and condition_symbols and impact_only and
                    not scope_grounded)
    return {
        'schema_version': 'intent-scope-review/1',
        'advisory_only': True,
        'blocks_candidate_acceptance': False,
        'intent_id': plan.get('intent_id'),
        'intent_scope_cues': scope_cues,
        'condition_symbols': condition_symbols,
        'condition_symbols_grounded_outside_impacts': scope_grounded,
        'condition_symbols_grounded_only_by_impacts': impact_only,
        'scope_narrowing_risk': narrowed,
        'note': ('Intent declares a general scope but every condition symbol '
                 'is grounded only by impact statements: the condition may '
                 'protect only the incident subcase. This review never '
                 'rewrites or rejects the plan.'),
    }


def relax_unsupported_relation(plan, elements):
    """Downgrade a blocking unsupported_relation the plan already represents.

    The honest fallback for an inexpressible relation (rates without
    division) is a declared bool symbol standing for the whole relation.  If
    the plan BOTH declares such a symbol (its source_ids covering the
    unresolved item's sources, and it is referenced by the pattern's
    condition or relation predicate) AND marks that relation blocking, the
    two declarations contradict each other: the logical skeleton exists, so
    "no faithful formula can be built" is false.  Resolve the contradiction
    mechanically toward the representation -- the item becomes nonblocking
    with a machine-readable note, and the change is audited.  Without the
    representing symbol the blocking verdict stands unchanged.

    Returns ``(plan, changes)``; ``changes`` is empty when nothing applied.
    """
    if not isinstance(plan, dict) or not isinstance(plan.get('unresolved'), list):
        return plan, []
    pattern = plan.get('pattern') or {}
    kind = pattern.get('kind')
    referenced = set()
    for slot in ('condition', 'relation', 'effect', 'authorization', 'trigger'):
        value = pattern.get(slot)
        if isinstance(value, dict):
            try:
                referenced |= _predicate_binding_symbols(value)
            except ValueError:
                return plan, []
    if not referenced:
        return plan, []
    symbols = plan.get('symbols') or {}
    changes = []
    for item in plan['unresolved']:
        if not (isinstance(item, dict) and
                item.get('category') == 'unsupported_relation' and
                item.get('blocks_formalization') is True):
            continue
        sources = set(item.get('source_ids') or [])
        representing = next((
            name for name in referenced
            if isinstance(symbols.get(name), dict) and
            symbols[name].get('sort') == 'bool' and
            sources <= set(symbols[name].get('source_ids') or [])), None)
        if representing is None:
            continue
        item['blocks_formalization'] = False
        changes.append({
            'kind': 'relax_unsupported_relation',
            'unresolved': item.get('description'),
            'representing_symbol': representing,
            'reason': ('the plan already encodes this relation as the truth '
                       'predicate of a declared bool symbol, so a faithful '
                       'logical skeleton exists; binding deferred to stage 3'),
        })
    return plan, changes


def realign_expanded_relation_class(plan, elements):
    """Deterministically realign relation_class to the plan's chosen pattern.

    The expanded schema fixes ``pattern.kind`` per ``relation_class``.  When the
    model names a class whose template differs from the class that UNIQUELY owns
    the pattern.kind it actually produced, the pattern is the more concrete
    choice, so flip the label to match it.  Ambiguous kinds (relation_obligation,
    bounded_relation, required_effect map to multiple classes) stay untouched so
    we never guess semantics.  This is a zero-call rebind aligned with KASC's
    strategy-invalidation rebind loop.
    """
    if not isinstance(plan, dict) or not isinstance(elements, dict):
        return plan, []
    if plan.get('schema_version') not in EXPANDED_PLAN_VERSIONS:
        return plan, []
    relation_class = plan.get('relation_class')
    pattern = plan.get('pattern') or {}
    kind = pattern.get('kind')
    if relation_class not in EXPANDED_RELATION_CLASS_PATTERN:
        return plan, []
    if kind == EXPANDED_RELATION_CLASS_PATTERN[relation_class]:
        return plan, []
    candidates = _EXPANDED_PATTERN_TO_CLASSES.get(kind)
    if not candidates or len(candidates) != 1:
        return plan, []
    target = next(iter(candidates))
    if target == relation_class:
        return plan, []
    plan['relation_class'] = target
    changes = [{
        'kind': 'realign_expanded_relation_class',
        'from': relation_class, 'to': target,
        'pattern_kind': kind,
        'reason': (f"pattern.kind={kind!r} uniquely matches relation_class "
                   f"{target!r}, not the declared {relation_class!r}"),
    }]
    return plan, changes


def _is_same_symbol_equality(expression):
    """Return True for ``eq(x, x)`` / ``ne(x, x)`` in the synthesized AST."""
    if not isinstance(expression, dict) or expression.get('op') not in ('eq', 'ne'):
        return False
    args = expression.get('args')
    return isinstance(args, list) and len(args) == 2 and args[0] == args[1]


def _contains_expression(expression, predicate):
    if not isinstance(expression, dict):
        return False
    if predicate(expression):
        return True
    return any(_contains_expression(child, predicate)
               for child in expression.get('args', []))


def _vacuous_safety_shapes(claim):
    """Return human-readable reasons for gate-defeating safety shapes.

    These are deterministic syntactic signatures of the observed 30-report
    failures: an I whose consequent is a tautology (``A => x == x`` or
    ``A => A``), and a program-generated V that contains the negation of a
    self-equality (``not(x == x)``). The post-generation fidelity audit may
    still mark such formulas consistent, so the gate must name them before the
    expensive local repair loop runs.
    """
    return [item['detail'] for item in _claim_weak_invariant_diagnostics(claim)
            if item['severity'] == 'blocking']


def _same_argument_true_shape(expression):
    """Return a reason when an expression is true for every value of its args."""
    if not isinstance(expression, dict):
        return None
    op = expression.get('op')
    args = expression.get('args')
    if op in ('eq', 'le', 'ge') and isinstance(args, list) and len(args) == 2 \
            and args[0] == args[1]:
        return 'safety contains a tautological self-comparison'
    if op == 'or' and isinstance(args, list) and len(args) == 2:
        left, right = args
        if (isinstance(right, dict) and right.get('op') == 'not' and
                isinstance(right.get('args'), list) and len(right['args']) == 1 and
                right['args'][0] == left):
            return 'safety contains a tautological excluded-middle disjunction'
        if (isinstance(left, dict) and left.get('op') == 'not' and
                isinstance(left.get('args'), list) and len(left['args']) == 1 and
                left['args'][0] == right):
            return 'safety contains a tautological excluded-middle disjunction'
    return None


def _checkpoint_info(claim):
    """Return ``(i_checkpoints, effect_checkpoints)`` for advisory diagnostics."""
    symbols = claim.get('symbols') or {}
    properties = claim.get('properties') or {}
    pre = (properties.get('preconditions') or {}).get('expression')
    safety = (properties.get('safety') or {}).get('expression')
    effects = (properties.get('effects') or {}).get('expression')

    def checkpoints(expression, exclude=None):
        names = _expression_variables(expression)
        if exclude is not None:
            names -= _expression_variables(exclude)
        return {str((symbols.get(name) or {}).get('checkpoint') or '').strip()
                for name in names
                if isinstance(symbols.get(name), dict)} - {''}

    return checkpoints(safety, exclude=pre), checkpoints(effects)


def _claim_advisory_diagnostics(claim):
    """Advisory alignment warnings; these never block a candidate by themselves."""
    reasons = []
    i_checkpoints, effect_checkpoints = _checkpoint_info(claim)
    if len(i_checkpoints) == 1 and len(effect_checkpoints) >= 2:
        reasons.append({
            'code': 'I_CHECKPOINT_COLLAPSED',
            'severity': 'advisory',
            'detail': ('safety observes every I symbol at one checkpoint while '
                       'effects compare distinct before/after checkpoints; '
                       'verify I is not a single-snapshot proxy for a '
                       'cross-checkpoint harm'),
        })
    symbols = claim.get('symbols') or {}
    for name in sorted(_expression_variables(
            (claim.get('properties', {}).get('safety') or {}).get('expression'))):
        checkpoint = str((symbols.get(name) or {}).get('checkpoint') or '').lower()
        if 'before' in checkpoint and 'after' in checkpoint:
            reasons.append({
                'code': 'I_CHECKPOINT_REUSED',
                'severity': 'advisory',
                'detail': ('safety symbol ' + name + ' names both before and '
                           'after in one checkpoint; use distinct snapshots'),
            })
    return reasons


def _claim_weak_invariant_diagnostics(claim):
    """Return structured ``{code, severity, detail}`` weak-invariant findings."""
    reasons = []
    safety = claim.get('properties', {}).get('safety', {}).get('expression')
    effects = claim.get('properties', {}).get('effects', {}).get('expression')
    if isinstance(safety, dict) and safety.get('op') == 'implies':
        args = safety.get('args')
        if isinstance(args, list) and len(args) == 2:
            antecedent, consequent = args
            if consequent == antecedent:
                reasons.append({
                    'code': 'I_SELF_IMPLICATION',
                    'severity': 'blocking',
                    'detail': 'safety is a tautological self-implication'})
            elif _is_same_symbol_equality(consequent):
                reasons.append({
                    'code': 'I_TAUTOLOGY',
                    'severity': 'blocking',
                    'detail': 'safety consequent is a tautological self-equality'})
            elif (isinstance(consequent, dict) and
                    consequent.get('op') == 'const' and
                    consequent.get('const') is True):
                reasons.append({
                    'code': 'I_TAUTOLOGY',
                    'severity': 'blocking',
                    'detail': 'safety consequent is the constant true'})
    if _is_same_symbol_equality(safety):
        reasons.append({
            'code': 'I_TAUTOLOGY',
            'severity': 'blocking',
            'detail': 'safety is a tautological self-equality'})
    trivial = _same_argument_true_shape(safety)
    if trivial:
        reasons.append({'code': 'I_TRIVIAL_BOUND',
                        'severity': 'blocking', 'detail': trivial})
    if (isinstance(safety, dict) and isinstance(effects, dict)
            and _numeric_relation_ops(effects)
            and not (_expression_variables(safety) & _numeric_symbols(claim))):
        reasons.append({
            'code': 'I_LAYER_MISMATCH',
            'severity': 'blocking',
            'detail': ('safety is qualitative-only while effects assert a '
                       'numeric harm; restate I over the numeric relation')})
    if isinstance(safety, dict) and isinstance(effects, dict) and safety == effects:
        reasons.append({
            'code': 'I_COPIED_FROM_V',
            'severity': 'blocking',
            'detail': ('safety and effects are the same expression; V must be '
                       'defined independently of I')})
    if isinstance(effects, dict):
        contradictory_not = (lambda node: (
            isinstance(node, dict) and node.get('op') == 'not' and
            isinstance(node.get('args'), list) and len(node['args']) == 1 and
            _is_same_symbol_equality(node['args'][0])))
        if _contains_expression(effects, contradictory_not):
            reasons.append({
                'code': 'EFFECT_CONTRADICTION',
                'severity': 'blocking',
                'detail': ('effects contains an unsatisfiable negation of a '
                           'self-equality')})
        def contradictory_pair(node):
            if not isinstance(node, dict) or node.get('op') != 'and':
                return False
            args = node.get('args') or []
            positives = []
            negations = []
            for child in args:
                if (isinstance(child, dict) and child.get('op') == 'not' and
                        isinstance(child.get('args'), list) and
                        len(child['args']) == 1):
                    negations.append(child['args'][0])
                else:
                    positives.append(child)
            return any(neg == pos for neg in negations for pos in positives)
        if _contains_expression(effects, contradictory_pair):
            reasons.append({
                'code': 'EFFECT_CONTRADICTION',
                'severity': 'blocking',
                'detail': 'effects contains a term and its own negation'})
    reasons.extend(_claim_advisory_diagnostics(claim))
    return reasons


WEAK_INVARIANT_BUCKETS = {
    'I_HOLDS_ON_EXPLOIT_PATH': 'weak_invariant',
    'I_IMPLIED_BY_P': 'weak_invariant',
    'I_NOT_FALSIFIED_BY_V': 'weak_invariant',
    'I_INCONSISTENT_WITH_P': 'relation_infeasible',
    'V_INCONSISTENT_WITH_P': 'relation_infeasible',
    'I_CHECKPOINT_COLLAPSED': 'semantic_alignment',
    'I_CHECKPOINT_REUSED': 'semantic_alignment',
    'I_LAYER_MISMATCH': 'numeric_alignment',
    'I_TRIVIAL_BOUND': 'generator_defect',
    'I_SELF_IMPLICATION': 'generator_defect',
    'I_TAUTOLOGY': 'generator_defect',
    'I_COPIED_FROM_V': 'generator_defect',
    'I_OUTCOME_GUARDED': 'generator_defect',
    'I_AUTHORIZATION_SELF_IMPLICATION': 'generator_defect',
    'I_OUTCOME_NEGATES_CONDITION': 'generator_defect',
    'EFFECT_CONTRADICTION': 'generator_defect',
    'DIRECT_GATE_MISSING': 'generator_defect',
}


def weak_invariant_bucket(code):
    """Route one structured diagnostic to its recovery bucket."""
    return WEAK_INVARIANT_BUCKETS.get(code, 'unknown')


def _p_implies_i(claim):
    """True only when P is satisfiable and entails I (P AND NOT I UNSAT)."""
    _, conditions = relation_setup(claim)
    if 'P_and_not_I' not in conditions or 'P_and_I' not in conditions:
        return False
    solver = z3.Solver()
    solver.set(timeout=5000)
    solver.add(*conditions['P_and_I'])
    if str(solver.check()) != 'sat':
        return False
    solver = z3.Solver()
    solver.set(timeout=5000)
    solver.add(*conditions['P_and_not_I'])
    return str(solver.check()) == 'unsat'


_DIRECT_CELL_DIAGNOSTICS = {
    'P_and_I': ('I_INCONSISTENT_WITH_P', 'sat',
                'P and I are not jointly satisfiable'),
    'P_and_V': ('V_INCONSISTENT_WITH_P', 'sat',
                'P and V are not jointly satisfiable'),
    'P_and_V_and_not_I': ('I_NOT_FALSIFIED_BY_V', 'sat',
                          'P, V and NOT I are not jointly satisfiable'),
    'P_and_V_and_I': ('I_HOLDS_ON_EXPLOIT_PATH', 'unsat',
                      'P, V and I are jointly satisfiable; I holds on the exploit path'),
}


def weak_invariant_diagnostics(plan=None, formal=None, claim_id='core_claim',
                               include_advisory=True):
    """Return structured weak-invariant diagnostics for a plan and/or formal claim.

    ``reject_vacuous_safety`` uses only ``severity == 'blocking'`` findings; the
    advisory alignment codes are surfaced for triage without rejecting a plan
    that is otherwise mathematically feasible.
    """
    reasons = []
    if isinstance(plan, dict):
        pattern = plan.get('pattern')
        if isinstance(pattern, dict):
            def bound_symbols(predicate):
                try:
                    return _predicate_binding_symbols(predicate)
                except ValueError:
                    return set()
            outcome_symbols = bound_symbols(plan.get('impact_outcome') or {})
            condition = pattern.get('condition')
            if (isinstance(condition, dict) and outcome_symbols and
                    outcome_symbols & bound_symbols(condition)):
                reasons.append({
                    'code': 'I_OUTCOME_GUARDED',
                    'severity': 'blocking',
                    'detail': ('safety condition is guarded by the reported '
                               'impact outcome')})
            if pattern.get('kind') == 'authorization_guard':
                effect_symbols = bound_symbols(pattern.get('effect') or {})
                authorization_symbols = bound_symbols(
                    pattern.get('authorization') or {})
                if effect_symbols == authorization_symbols:
                    reasons.append({
                        'code': 'I_AUTHORIZATION_SELF_IMPLICATION',
                        'severity': 'blocking',
                        'detail': ('authorization guard is a tautological '
                                   'self-implication')})
        negated_symbol = _negated_condition_outcome_symbol(plan)
        if negated_symbol:
            reasons.append({
                'code': 'I_OUTCOME_NEGATES_CONDITION',
                'severity': 'blocking',
                'detail': ('impact outcome negates the pattern condition '
                           'symbol: ' + negated_symbol)})
    if formal is not None:
        claim = next((item for item in formal.get('claims', [])
                      if item.get('id') == claim_id), None)
        if claim is not None:
            merged_claim = dict(claim)
            if 'symbols' not in merged_claim and isinstance(formal.get('symbols'), dict):
                merged_claim['symbols'] = formal['symbols']
            reasons.extend(_claim_weak_invariant_diagnostics(merged_claim))
            if _p_implies_i(merged_claim):
                reasons.append({
                    'code': 'I_IMPLIED_BY_P',
                    'severity': 'blocking',
                    'detail': ('P entails I, so I adds no independent safety '
                               'content beyond the preconditions')})
            diagnostics = direct_relation_diagnostics(merged_claim)
            if not diagnostics['feasible']:
                for name, info in diagnostics['cells'].items():
                    code, _expected, detail = _DIRECT_CELL_DIAGNOSTICS[name]
                    if info['ok']:
                        continue
                    if info['status'] == 'missing':
                        code, detail = ('DIRECT_GATE_MISSING',
                                        'required P/I/V gate cell is missing')
                    reasons.append({
                        'code': code,
                        'severity': 'blocking',
                        'detail': (detail + ': ' + name + '=' + info['status'] +
                                   ' (expected ' + info['expected'] + ')'),
                    })
    if not include_advisory:
        reasons = [item for item in reasons if item['severity'] == 'blocking']
    # Preserve first occurrence order while dropping exact duplicates.
    unique = []
    seen = set()
    for item in reasons:
        key = (item['code'], item['detail'], item['severity'])
        if key not in seen:
            seen.add(key)
            unique.append(item)
    return unique


def reject_vacuous_safety(plan, formal=None, claim_id='core_claim'):
    """Return blocking reasons when a generated safety property cannot satisfy
    the stage-2 handoff gate.

    The stage-2 continuation gate requires V to falsify I under P
    (``P AND V`` SAT, ``P AND V AND NOT I`` SAT, ``P AND V AND I`` UNSAT).
    Two generator shapes silently defeat that gate even though the fidelity
    audit may pass: an I whose guard is the impact outcome itself
    (``NOT V implies condition``), and an ``authorization_guard`` whose effect
    and authorization bind the same symbol (``x implies x``).  A downstream
    semantic check catches any other indirect-consequence plan.
    """
    return [item['code'] + ': ' + item['detail']
            for item in weak_invariant_diagnostics(
                plan, formal, claim_id=claim_id, include_advisory=False)]


def synthesize_id_formalization(plan, elements, claim_id='core_claim',
                                include_unselected_limitations=True,
                                fidelity_only=False,
                                direct_witness_effects=False):
    base_fields = {
        'schema_version', 'precondition_ids', 'intent_id', 'impact_ids', 'symbols',
        'precondition_terms', 'pattern', 'assumptions', 'unresolved', 'limitations'}
    require(isinstance(plan, dict), 'invalid formal plan')
    version = plan.get('schema_version')
    expected_fields = (base_fields | {'relation_class', 'derived_definitions',
        'impact_context_terms'}
                       if version in EXPANDED_PLAN_VERSIONS else
                       base_fields | {'relation_class', 'derived_definitions'}
                       if version == FIXED_PLAN_VERSION else
                       base_fields | {'relation_class'}
                       if version == CLASSIFIED_PLAN_VERSION else base_fields)
    if version == LIVE_EXPANDED_PLAN_VERSION:
        expected_fields = expected_fields | {'impact_outcome'}
    require(set(plan) == expected_fields, 'unexpected formal plan fields')
    require(version in (PLAN_VERSION, STRUCTURED_PLAN_VERSION, CLASSIFIED_PLAN_VERSION,
                        FIXED_PLAN_VERSION, *EXPANDED_PLAN_VERSIONS),
            'unknown formal plan schema')
    if version in (CLASSIFIED_PLAN_VERSION, FIXED_PLAN_VERSION,
                   *EXPANDED_PLAN_VERSIONS):
        require(plan['relation_class'] in RELATION_CLASSES, 'unknown relation class')
        require(isinstance(plan['pattern'], dict), 'invalid classified relation pattern')
        if version == FIXED_PLAN_VERSION:
            require(plan['pattern'].get('kind') ==
                    FIXED_RELATION_CLASS_PATTERN[plan['relation_class']],
                    'fixed relation template mismatch')
            if not fidelity_only:
                _reject_cancellable_relation(plan['pattern'])
        elif version in EXPANDED_PLAN_VERSIONS:
            require(plan['pattern'].get('kind') ==
                    EXPANDED_RELATION_CLASS_PATTERN[plan['relation_class']],
                    'expanded relation template mismatch')
            if not fidelity_only:
                _reject_cancellable_relation(plan['pattern'])
        else:
            require(plan['pattern'].get('kind') in
                    RELATION_CLASS_PATTERNS[plan['relation_class']],
                    'relation class and pattern mismatch')
    statements = _index(elements['statements'], 'statement')
    entities = _index(elements['entities'], 'entity')
    require(strings(plan['precondition_ids']) and
            (bool(plan['precondition_ids']) or
             version in ('report-formal-plan/7', LIVE_EXPANDED_PLAN_VERSION)) and
            len(set(plan['precondition_ids'])) ==
            len(plan['precondition_ids']), 'invalid plan precondition IDs')
    require(all(x in statements and statements[x]['kind'] in ('precondition', 'assumption')
                for x in plan['precondition_ids']), 'plan P source role mismatch')
    require(isinstance(plan['intent_id'], str) and plan['intent_id'] in statements and
            statements[plan['intent_id']]['kind'] == 'security_intent', 'invalid plan intent ID')
    impact_limit = 1 if version in (
        CLASSIFIED_PLAN_VERSION, FIXED_PLAN_VERSION,
        *EXPANDED_PLAN_VERSIONS) else 2
    require(strings(plan['impact_ids']) and 1 <= len(plan['impact_ids']) <= impact_limit and
            len(set(plan['impact_ids'])) == len(plan['impact_ids']) and
            all(x in statements and statements[x]['kind'] == 'impact' for x in plan['impact_ids']),
            'invalid plan impact IDs')
    require(strings(plan['assumptions']) and strings(plan['limitations']),
            'invalid plan caveats')
    if fidelity_only:
        formal_unresolved = []
    elif version == PLAN_VERSION:
        require(strings(plan['unresolved']), 'invalid plan caveats')
        formal_unresolved = list(plan['unresolved'])
    else:
        unresolved_review = structured_unresolved_review(plan, elements)
        formal_unresolved = [
            f"[{item['category']}] {item['description']}"
            for item in unresolved_review['items'] if item['blocks_formalization']
        ]
    if not isinstance(plan['symbols'], dict):
        detail = 'got a non-object symbol table'
    elif not (1 <= len(plan['symbols']) <= MAX_PLAN_SYMBOLS):
        detail = f'got {len(plan["symbols"])} symbol declarations'
    else:
        detail = 'symbol table failed later validation'
    require(isinstance(plan['symbols'], dict) and
            1 <= len(plan['symbols']) <= MAX_PLAN_SYMBOLS,
            'invalid plan symbols: expected 1..12 symbol declarations, ' + detail)

    symbols, output_symbols = {}, {}
    for name, item in plan['symbols'].items():
        require(identifier(name) and isinstance(item, dict) and
                PLAN_SYMBOL_REQUIRED_FIELDS <= set(item) and
                set(item) <= (PLAN_SYMBOL_REQUIRED_FIELDS |
                              PLAN_SYMBOL_OPTIONAL_FIELDS),
            'invalid plan symbol')
        require(item['sort'] in ('int', 'bool', 'address'), 'invalid plan symbol sort')
        if item['sort'] == 'int':
            if fidelity_only and (not isinstance(item['unit'], str) or
                                  not item['unit'].strip()):
                item['unit'] = 'unspecified'
            require(isinstance(item['unit'], str) and item['unit'].strip(), 'missing plan quantity unit')
        else:
            if fidelity_only:
                item['unit'] = None
            require(item['unit'] is None, 'non-quantity plan unit')
        require(all(isinstance(item[x], str) and item[x].strip()
                    for x in ('meaning', 'checkpoint')), 'missing plan symbol semantics')
        if fidelity_only:
            item['entity_ids'] = [x for x in item.get('entity_ids', [])
                                  if x in entities] or list(entities)
            allowed_sources = list(dict.fromkeys(
                plan['precondition_ids'] + [plan['intent_id']] + plan['impact_ids']))
            item['source_ids'] = [x for x in item.get('source_ids', [])
                                  if x in statements] or allowed_sources
        require(strings(item['entity_ids']) and bool(item['entity_ids']) and
                all(x in entities for x in item['entity_ids']), 'invalid plan symbol entities')
        require(strings(item['source_ids']) and bool(item['source_ids']) and
                all(x in statements for x in item['source_ids']), 'invalid plan symbol sources')
        evidence_ids = _evidence(item['source_ids'], statements)
        require(bool(evidence_ids), 'plan symbol lacks evidence')
        if 'observable_kind' in item:
            require(item['observable_kind'] in OBSERVABLE_KINDS,
                    'invalid plan symbol observable_kind')
        if 'scope' in item:
            require(item['scope'] in SYMBOL_SCOPES,
                    'invalid plan symbol scope')
        if 'binding_risk' in item:
            require(item['binding_risk'] in BINDING_RISKS,
                    'invalid plan symbol binding_risk')
        for key in ('receiver', 'contract_type'):
            if key in item:
                require(item[key] is None or
                        (isinstance(item[key], str) and item[key].strip()),
                        'invalid plan symbol ' + key)
        if item.get('scope') == 'cross_contract':
            require(isinstance(item.get('receiver'), str) and
                    item['receiver'].strip(),
                    'cross-contract plan symbol lacks receiver')
        symbols[name] = {'sort': item['sort'], 'unit': item['unit'],
                         'meaning': item['meaning'], 'checkpoint': item['checkpoint']}
        output_symbols[name] = {**symbols[name], 'evidence_ids': evidence_ids,
                                'entity_ids': item['entity_ids']}

    definition_expressions = []
    if version in (FIXED_PLAN_VERSION, *EXPANDED_PLAN_VERSIONS):
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
            expression = _quantity_expression(
                item['expression'], symbols, enforce_units=True)
            require(target not in _expression_variables(expression),
                    'recursive derived definition')
            targets.append(target)
            definition = {'op': 'eq', 'args': [{'var': target}, expression]}
            require(r.expr_type(definition, symbols,
                                enforce_units=True) == ('bool', None),
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
        if not fidelity_only:
            require(term['source_id'] in plan['precondition_ids'],
                    'P term source not selected')
        term_sources.append(term['source_id'])
        expression = _predicate(term['predicate'], symbols,
                                enforce_units=True)
        if version in EXPANDED_PLAN_VERSIONS and not fidelity_only:
            require(all(term['source_id'] in plan['symbols'][name]['source_ids']
                        for name in _expression_variables(expression)),
                    'P predicate symbol not grounded by its own source')
        elif version not in EXPANDED_PLAN_VERSIONS and not fidelity_only:
            require(all(any(source in plan['precondition_ids']
                            for source in plan['symbols'][name]['source_ids'])
                        for name in _expression_variables(expression)),
                    'P predicate symbol not grounded by selected preconditions')
        p_expressions.append(expression)
    if not fidelity_only:
        require(set(term_sources) == set(plan['precondition_ids']) and
                len(term_sources) == len(plan['precondition_ids']),
                'P terms must cover selected preconditions exactly once')
    if version in (LEGACY_EXPANDED_PLAN_VERSION, EXPANDED_PLAN_VERSION):
        require(not identical_p_predicates(plan),
                'distinct P sources reuse identical predicate')
    # No explicit report precondition means the claim is unconditional; encode
    # P=true so the compiler and the post-generation fidelity audit can still
    # evaluate I/V without inventing a P source.
    p_expression = (_and(p_expressions) if p_expressions else
                    {'const': True} if version in (
                        'report-formal-plan/7', LIVE_EXPANDED_PLAN_VERSION) else None)
    trigger_predicates = _relocated_trigger_predicates(plan, plan['symbols'])
    trigger_symbols = {p['symbol'] for p in trigger_predicates}
    if trigger_predicates:
        trigger_expressions = [_predicate(p, symbols, enforce_units=True)
                               for p in trigger_predicates]
        if p_expression is None:
            p_expression = _and(trigger_expressions)
        else:
            p_expression = _and([p_expression] + trigger_expressions)
    # Validate the selected template's exact fields before alignment walks
    # into symbols such as observed_symbol/earlier_symbol. Malformed model
    # plans must produce a retryable ValueError, never an unhandled KeyError.
    safety, pattern_effects = _pattern_expressions(
        plan['pattern'], symbols, enforce_units=True,
        trigger_symbols=trigger_symbols)
    effects = pattern_effects
    # live-16 defers this semantic source-alignment judgment until after P/I/V
    # generation. Frozen schemas keep their original validation behavior.
    if version not in LIVE_RELAXED_PLAN_VERSIONS and version in (
            CLASSIFIED_PLAN_VERSION, FIXED_PLAN_VERSION, *EXPANDED_PLAN_VERSIONS):
        classified_relation_alignment(plan, elements)
    if version in EXPANDED_PLAN_VERSIONS:
        context_terms = plan['impact_context_terms']
        require(isinstance(context_terms, list) and len(context_terms) <= 4,
                'invalid impact context terms')
        context_types = {source: set() for source in plan['impact_ids']}
        context_expressions = []
        for term in context_terms:
            require(isinstance(term, dict) and set(term) == {
                'source_id', 'qualifier_types', 'predicate'},
                    'invalid impact context term')
            source_id = (plan['impact_ids'][0] if fidelity_only
                         else term['source_id'])
            if not fidelity_only:
                require(source_id in plan['impact_ids'],
                        'impact context source not selected')
                require(strings(term['qualifier_types']) and
                        len(term['qualifier_types']) == len(set(term['qualifier_types'])) and
                        set(term['qualifier_types']) <= set(IMPACT_QUALIFIER_PATTERNS),
                        'invalid impact qualifier types')
            expression = _predicate(term['predicate'], symbols,
                                    enforce_units=True)
            if not fidelity_only:
                require(all(source_id in plan['symbols'][name]['source_ids']
                            for name in _expression_variables(expression)),
                        'impact context symbol not grounded by its own source')
                context_types[source_id].update(term['qualifier_types'])
            context_expressions.append(expression)
        detector = (_legacy_impact_qualifier_types
                    if version == LEGACY_EXPANDED_PLAN_VERSION
                    else impact_qualifier_types)
        missing_context = {
            source: sorted(set(detector(statements[source]['text'])) -
                           context_types[source])
            for source in plan['impact_ids']
        }
        missing_context = {source: kinds for source, kinds in missing_context.items()
                           if kinds}
        if missing_context and version not in LIVE_RELAXED_PLAN_VERSIONS and not fidelity_only:
            require(not missing_context,
                    'impact qualifier missing from formal plan: ' +
                    json.dumps(missing_context, sort_keys=True, separators=(',', ':')))
        # Earlier live schemas folded the impact context into the safety
        # relation, then fabricated V as its negation.  Live-19+ carries a
        # source-grounded impact observation separately so the audit can check
        # whether the report's actual outcome violates I.
        if version == LIVE_EXPANDED_PLAN_VERSION:
            outcome = plan['impact_outcome']
            require(isinstance(outcome, dict) and set(outcome) == {
                'source_id', 'predicate'}, 'invalid direct impact outcome')
            source_id = (plan['impact_ids'][0] if fidelity_only
                         else outcome['source_id'])
            if not fidelity_only:
                require(source_id in plan['impact_ids'],
                        'impact outcome source not selected')
                require(len(plan['impact_ids']) == 1,
                        'direct impact outcome requires exactly one impact')
            outcome_expression = _predicate(
                outcome['predicate'], symbols, enforce_units=True)
            if not fidelity_only:
                require(all(source_id in plan['symbols'][name]['source_ids']
                            for name in _expression_variables(outcome_expression)),
                        'impact outcome symbol not grounded by its own source')
            if direct_witness_effects:
                effects = _and([pattern_effects, outcome_expression,
                                *context_expressions])
            else:
                effects = _and([outcome_expression, *context_expressions])
        elif context_expressions:
            # Historical plan schemas remain byte-for-byte replay compatible.
            context = _and(context_expressions)
            safety = {'op': 'implies', 'args': [context, safety]}
            effects = _and([context, effects])
    if version in (FIXED_PLAN_VERSION, *EXPANDED_PLAN_VERSIONS):
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
    if direct_witness_effects:
        safety = _collapse_double_negation(safety)
        effects = _collapse_double_negation(effects)
    require(r.expr_type(safety, symbols, enforce_units=True) == ('bool', None) and
            r.expr_type(effects, symbols, enforce_units=True) == ('bool', None),
            'synthesized property is not Boolean')

    p_sources = list(plan['precondition_ids'])
    if trigger_predicates:
        # A scenario trigger moved into P is grounded by the intent/impact
        # statement that declared its symbol, not by an explicit report
        # precondition.  Carry those sources into P so the synthesized
        # precondition is never rejected as 'formal property missing source'.
        trigger_sources = _unique(
            source for predicate in trigger_predicates
            for source in plan['symbols'][predicate['symbol']].get('source_ids', []))
        p_sources = list(dict.fromkeys([*p_sources, *trigger_sources]))
    i_sources = [plan['intent_id']]
    v_sources = plan['impact_ids']
    p_text = '; '.join(statements[x]['text'] for x in p_sources)
    i_text = statements[plan['intent_id']]['text']
    v_text = '; '.join(statements[x]['text'] for x in v_sources)
    properties = {
        PIV_PROPERTY_NAMES[0]: {'text': p_text, 'expression': p_expression,
                          'evidence_ids': _evidence(p_sources, statements) if p_sources else [],
                          'derivation': 'Program conjunction of selected report preconditions.',
                          'source_ids': p_sources},
        PIV_PROPERTY_NAMES[1]: {'text': i_text, 'expression': safety,
                   'evidence_ids': _evidence(i_sources, statements),
                   'derivation': 'Program synthesis from the selected intent and logical pattern.',
                   'source_ids': i_sources},
        PIV_PROPERTY_NAMES[2]: {'text': v_text, 'expression': effects,
                    'evidence_ids': _evidence(v_sources, statements),
                    'derivation': 'Program-generated direct negation witness for the selected safety pattern.',
                    'source_ids': v_sources},
    }
    formula_sources = dict(zip(PIV_PROPERTY_NAMES, (
        _links(p_expression, p_sources, symbols) if p_expression else {},
        _links(safety, i_sources, symbols),
        _links(effects, v_sources, symbols),
    )))
    modality = ('potential' if any(statements[x]['modality'] == 'potential' for x in v_sources)
                else 'inferred' if any(statements[x]['modality'] == 'inferred' for x in v_sources)
                else 'asserted')
    unselected = [row['id'] for row in elements['statements']
                  if row['kind'] == 'impact' and row['id'] not in v_sources]
    limitations = list(plan['limitations'])
    if include_unselected_limitations:
        limitations.extend(f'Deferred report impact: {x}' for x in unselected)
    claim = {
        'id': claim_id, 'scope': elements['scope']['flow'], 'modality': modality,
        'impact_ids': v_sources, 'properties': properties, 'formula_sources': formula_sources,
        'effect_coverage': [{'statement_id': x, 'status': 'formalized',
                             'reason': 'Program-generated exact coverage for selected direct impact.'}
                            for x in v_sources],
        'assumptions': plan['assumptions'], 'unresolved': formal_unresolved,
    }
    return {'schema_version': 'report-formalization/2', 'symbols': output_symbols,
            'claims': [claim], 'limitations': limitations}
