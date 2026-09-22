"""Stage-2 triage and observable-variable review annotations.

Merged from automatic_triage.py and review_observability.py (2026-09-21);
both are the post-solve review layer.
"""
import argparse
import json
from pathlib import Path


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
    if bundle['core_formalization_status'] != 'formalized_candidate' or infeasible_claims:
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
    blockers = continuation_blockers(bundle, unresolved_review)
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
    if result['review_status'] == 'needs_review':
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
