"""P/I/V synthesis + Z3 countermodels, and the post-solve triage/review layer.

合并自两个模块（S7），函数体逐字未改：
  - symbolic_queries.py : modular P/I/V synthesis and Z3 report countermodels,
                          never code traces.
  - review.py           : stage-2 triage and observable-variable review annotations
                          (itself merged from automatic_triage.py +
                          review_observability.py on 2026-09-21).
"""
import argparse
import json
from pathlib import Path

import z3

import report_only as r
from semantic_core import require


# ------------------- 节选自 symbolic_queries.py -------------------

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


# ------------------- 节选自 review.py -------------------

def continuation_blockers(bundle, unresolved_review=None):
    """Only missing core structure blocks progress; review warnings remain visible."""
    blockers = []
    claims = bundle.get('claims', [])
    if bundle.get('core_formalization_status') != 'formalized_candidate' or not claims:
        blockers.append('core P/I/V is not fully formalized')
    if unresolved_review and unresolved_review.get('blocks_candidate_acceptance'):
        blockers.append('model declared a blocking unresolved core relation')
    for claim in claims:
        name = claim.get('id', 'unnamed_claim')
        # v3.12 formal claim.unresolved contains only model-declared blocking items;
        # advisory items remain in the separate structured review artifact.
        if (bundle.get('provenance', {}).get('prompt_version') == 'semantic-v3.12' and
                any(isinstance(note, str) and note.startswith('[') and ']' in note
                    for note in claim.get('unresolved', []))):
            blockers.append(name + ': model declared an unresolved core relation')
        properties = claim.get('properties', {})
        if any(properties.get(field, {}).get('expression') is None
               for field in ('preconditions', 'safety', 'effects')):
            blockers.append(name + ': P, I, or V formula is missing')
        queries = claim.get('semantic_relationship', {}).get('queries', {})
        if (queries.get('P_and_V') != 'sat' or
                queries.get('P_and_V_and_not_I') != 'sat' or
                queries.get('P_and_V_and_I') != 'unsat'):
            blockers.append(name + ': direct P/I/V relationship is absent or infeasible')
    return blockers


def from_bundle(bundle, unresolved_review=None):
    acceptance = bundle['acceptance_status']
    infeasible_claims = [claim['id'] for claim in bundle.get('claims', [])
                         if claim.get('semantic_relationship', {}).get('queries', {}).get(
                             'P_and_V') in ('unsat', 'unknown')]
    blockers = continuation_blockers(bundle, unresolved_review)
    # A route is an action decision, so it must agree with the continuation
    # gate.  Previously a bundle with a missing P or V could be labelled
    # ``candidate`` while ``stage2_can_continue`` was false.
    if blockers or infeasible_claims or acceptance == 'rejected':
        route = 'abstain'
    elif acceptance == 'candidate_checks_passed':
        route = 'candidate'
    else:
        route = 'review'
    reasons = list(bundle.get('report_warnings', []))
    for claim in bundle.get('claims', []):
        reasons.extend(f"{claim['id']}: {reason}"
                       for reason in claim.get('review_reasons', []))
    if route == 'abstain' and not reasons:
        reasons.append('core P/I/V is not fully formalized')
    if infeasible_claims:
        reasons.append('P AND V is not feasible for claim(s): ' + ', '.join(infeasible_claims))
    return {'schema_version': 'stage2-auto-triage/1', 'route': route,
            'reasons': list(dict.fromkeys(reasons)),
            'stage2_can_continue': not blockers,
            'continuation_blockers': blockers,
            'semantic_truth_verified': False, 'poc_consistency_verdict': 'not_evaluated'}


def from_failure(status):
    return {'schema_version': 'stage2-auto-triage/1', 'route': 'pipeline_failure',
            'reasons': [f"{status['error_type']}: {status['error']}"],
            'stage2_can_continue': False,
            'continuation_blockers': [f"{status['error_type']}: {status['error']}"],
            'semantic_truth_verified': False, 'poc_consistency_verdict': 'not_evaluated'}


def variables(expr):
    if expr is None: return set()
    if 'var' in expr: return {expr['var']}
    return set().union(*(variables(child) for child in expr.get('args', [])))


def review(formal, bundle):
    compiled = {claim['id']: claim for claim in bundle['claims']}
    claims = []
    for claim in formal['claims']:
        props = claim['properties']
        used = {key: variables(prop['expression']) for key, prop in props.items()}
        isolated = sorted(name for name in used['safety'] - used['preconditions'] - used['effects']
                          if formal['symbols'][name]['sort'] == 'bool')
        warnings = []
        if isolated:
            warnings.append('safety-only Boolean observations require a definition or manual binding review: '
                            + ', '.join(isolated))
        queries = compiled[claim['id']]['semantic_relationship'].get('queries', {})
        both = queries.get('P_and_V_and_not_I') == 'sat' and queries.get('P_and_V_and_I') == 'sat'
        if both:
            warnings.append('effects can coexist with either safety truth value under P; review weak I, '
                            'missing predicate definitions or partial effects')
        claims.append({'claim_id': claim['id'], 'safety_variables': sorted(used['safety']),
                       'safety_only_booleans': isolated, 'effects_allow_both_safety_values': both,
                       'review_status': 'needs_review' if warnings else
                           'incomplete_check' if props['safety']['expression'] is None else 'no_structural_warning',
                       'warnings': warnings})
    return {'schema_version': 'observability-review/1', 'claims': claims,
            'review_status': 'needs_review' if any(x['warnings'] for x in claims) else
                'incomplete_check' if any(x['review_status'] == 'incomplete_check' for x in claims) else 'no_structural_warning',
            'observability_established': False, 'human_semantic_review_required': True,
            'limitations': ['I-only Boolean may be a legitimate observation; hints are not automatic errors',
                           'No code binding, predicate-name interpretation or report truth assessment',
                           'Both SAT is a review hint, not a universal UNSAT requirement'], 'model_calls': 0}


def attach_review(bundle, formal):
    """Add a review gate without changing any candidate AST or symbolic queries."""
    result = review(formal, bundle)
    bundle['observability_review'] = result
    lookup = {claim['id']: claim for claim in bundle['claims']}
    for claim in result['claims']:
        if claim['warnings']:
            target = lookup[claim['claim_id']]
            target['review_reasons'].extend(claim['warnings'])
            if target['formalization_status'] == 'formalized_candidate':
                target['formalization_status'] = 'needs_review'
    # A review may escalate severity, never soften it: a bundle the compiler
    # already rejected for a contradictory P must not be talked back up to
    # `needs_review` by the observability layer.
    if (result['review_status'] == 'needs_review' and
            bundle['acceptance_status'] != 'rejected'):
        bundle['acceptance_status'] = 'needs_review'
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    args = parser.parse_args()
    # CLI is read-only, including for historical bundles.
    formal = json.loads((args.directory / 'formalization.json').read_text())
    bundle = json.loads((args.directory / 'constraints.json').read_text())
    print(json.dumps(review(formal, bundle), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
