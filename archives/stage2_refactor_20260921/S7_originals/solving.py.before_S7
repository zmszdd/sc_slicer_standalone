"""Modular P/I/V synthesis and Z3 report countermodels, never code traces."""
import z3

import report_only as r
from semantic_core import require


def setup(claim):
    address = z3.DeclareSort('ReportAddress')
    variables = {name: z3.Bool(name) if item['sort'] == 'bool' else
                 z3.Const(name, address) if item['sort'] == 'address' else z3.Int(name)
                 for name, item in claim['symbols'].items()}
    props = {name: r.lower(prop['expression'], variables) for name, prop in claim['properties'].items()
             if prop['expression'] is not None}
    conditions = {}
    pre = [props['preconditions']] if 'preconditions' in props else []
    if pre: conditions['P'] = pre
    if 'safety' in props:
        conditions['P_and_I'] = pre + [props['safety']]
        conditions['P_and_not_I'] = pre + [z3.Not(props['safety'])]
    if 'effects' in props:
        conditions['P_and_V'] = pre + [props['effects']]
        if 'safety' in props:
            conditions['P_and_V_and_not_I'] = pre + [props['effects'], z3.Not(props['safety'])]
            conditions['P_and_V_and_I'] = pre + [props['effects'], props['safety']]
    return variables, conditions


def solve_queries(claim, text):
    r.validate(claim, text)
    _, modules = r.compile_spec(claim, text)
    variables, conditions = setup(claim)
    predicates = {'P': ['report_preconditions'], 'P_and_I': ['report_safety'],
                  'P_and_not_I': ['(not report_safety)'], 'P_and_V': ['report_effects'],
                  'P_and_V_and_not_I': ['report_effects', '(not report_safety)'],
                  'P_and_V_and_I': ['report_effects', 'report_safety']}
    results = {}
    for name, expressions in conditions.items():
        solver = z3.Solver(); solver.set(timeout=5000); solver.add(*expressions)
        status = str(solver.check())
        witness = None
        if status == 'sat':
            model = solver.model()
            assigned = {decl.name() for decl in model.decls()}
            witness = {}
            for symbol, variable in variables.items():
                value = model.eval(variable, model_completion=True)
                value = value.as_long() if z3.is_int_value(value) else True if z3.is_true(value) else False if z3.is_false(value) else str(value)
                witness[symbol] = {'value': value, 'model_completion': symbol not in assigned}
        parts = list(predicates[name])
        if name != 'P' and 'preconditions' in claim['properties'] and claim['properties']['preconditions']['expression'] is not None:
            parts.insert(0, 'report_preconditions')
        smt = modules + '\n'.join(f'(assert {part})' for part in parts) + '\n(check-sat)\n'
        if status == 'sat': smt += '(get-model)\n'
        results[name] = {'status': status, 'witness': witness, 'smt': smt,
                         'meaning': 'report-only mathematical model; NOT a PoC execution or report-validity verdict'}
    return results


def verify_witness(claim, query, witness):
    variables, conditions = setup(claim)
    require(query in conditions and set(witness) == set(variables), 'invalid witness query/symbols')
    solver = z3.Solver(); solver.set(timeout=5000); solver.add(*conditions[query])
    address_values = {}
    for name, variable in variables.items():
        item = witness[name]
        require(set(item) == {'value', 'model_completion'} and type(item['model_completion']) is bool, 'invalid witness fields')
        value = item['value']
        sort = claim['symbols'][name]['sort']
        if sort == 'int': require(type(value) is int, 'invalid integer witness')
        elif sort == 'bool': require(type(value) is bool, 'invalid Boolean witness')
        else:
            require(isinstance(value, str), 'invalid address identity witness')
            if value not in address_values:
                address_values[value] = z3.Const('witness_identity_' + str(len(address_values)), variable.sort())
            value = address_values[value]
        solver.add(variable == value)
    if len(address_values) > 1: solver.add(z3.Distinct(*address_values.values()))
    require(str(solver.check()) == 'sat', 'saved witness does not satisfy query')
    return True
