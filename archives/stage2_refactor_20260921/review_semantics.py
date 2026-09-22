"""Offline I/V relationship sanity check, NOT a semantic truth oracle."""
import argparse
import json
from pathlib import Path

import z3
import report_only as r


def relationship_review(claim, text, require_direct_counterexample=False):
    r.validate(claim, text)
    address = z3.DeclareSort('ReportAddress')
    symbols = {name: z3.Bool(name) if item['sort'] == 'bool' else
               z3.Const(name, address) if item['sort'] == 'address' else z3.Int(name)
               for name, item in claim['symbols'].items()}
    formulas = {name: r.lower(prop['expression'], symbols)
                for name, prop in claim['properties'].items() if prop['expression'] is not None}
    if 'safety' not in formulas or 'effects' not in formulas:
        return {'review_status': 'incomplete_check', 'queries': {},
                'warnings': ['I or V absent; effect/safety relationship not checked'],
                'eligible_for_stage3': False, 'human_semantic_review_required': True}
    pre = [formulas['preconditions']] if 'preconditions' in formulas else []
    def check(*expressions):
        solver = z3.Solver(); solver.set(timeout=5000)
        solver.add(*expressions)
        return str(solver.check())
    queries = {'P_and_V': check(*pre, formulas['effects']),
               'P_and_V_and_not_I': check(*pre, formulas['effects'], z3.Not(formulas['safety'])),
               'P_and_V_and_I': check(*pre, formulas['effects'], formulas['safety'])}
    warnings = []
    if queries['P_and_V'] != 'sat':
        warnings.append('claimed effect infeasible or feasibility unknown')
    elif queries['P_and_V_and_not_I'] == 'unsat':
        warnings.append('claimed effect entails safety under P; possible I/V inversion, weak I, or wrong pairing')
    elif queries['P_and_V_and_not_I'] == 'unknown':
        warnings.append('effect/safety relationship unknown')
    if require_direct_counterexample:
        if queries['P_and_V_and_I'] == 'sat':
            warnings.append('effects do not entail not-safety under P; direct V/I counterexample relation failed')
        elif queries['P_and_V_and_I'] == 'unknown':
            warnings.append('cannot prove that effects exclude safety under P')
    result = {'review_status': 'needs_review' if warnings else 'no_relationship_warning',
            'queries': queries, 'warnings': warnings, 'eligible_for_stage3': False,
            'human_semantic_review_required': True,
            'limitation': 'No code transition T. A SAT witness is not semantic correctness or report validity.'}
    if require_direct_counterexample:
        result['direct_counterexample_status'] = (
            'passed' if queries['P_and_V'] == 'sat' and
            queries['P_and_V_and_not_I'] == 'sat' and
            queries['P_and_V_and_I'] == 'unsat' else 'failed')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    args = parser.parse_args()
    spec_path = args.directory / 'constraints.json'
    spec = json.loads(spec_path.read_text())
    text = (args.directory / 'extraction-input.txt').read_text()
    claim = {k: spec[k] for k in ('symbols', 'properties', 'assumptions', 'unresolved')}
    result = relationship_review(claim, text)
    result['constraints_sha256'] = r.sha(spec_path.read_bytes())
    result['model_calls'] = 0
    output = args.directory / 'semantic-review.json'
    with output.open('x') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__': main()
