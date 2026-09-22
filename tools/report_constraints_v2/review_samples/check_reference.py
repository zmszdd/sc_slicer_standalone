"""Read-only formula comparison against pending public-spec references; no model/code."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import z3
from lib import report_only as r

HERE = Path(__file__).resolve().parent


def cases():
    return json.loads((HERE / 'reference.json').read_text())['cases']


def compare(case, candidate):
    if not isinstance(candidate, dict) or set(candidate) != {'preconditions', 'safety'}:
        raise ValueError('candidate must contain exactly preconditions and safety ASTs')
    symbols = case['symbols']
    address = z3.DeclareSort('ReviewAddress')
    variables = {name: z3.Const(name, address) if item['sort'] == 'address' else z3.Int(name)
                 for name, item in symbols.items()}
    formulas = {}
    for origin, values in (('reference', case), ('candidate', candidate)):
        for key in ('preconditions', 'safety'):
            if r.expr_type(values[key], symbols) != ('bool', None):
                raise ValueError('property must be Boolean')
            formulas[origin + '_' + key] = r.lower(values[key], variables)
    domain = [variables[name] >= 0 for name, item in symbols.items() if item['sort'] == 'int']
    feasible = z3.Solver(); feasible.set(timeout=5000)
    feasible.add(*domain, formulas['reference_preconditions'])
    if feasible.check() != z3.sat:
        raise ValueError('reference domain/precondition is infeasible or unknown')
    queries = {
        'preconditions': [z3.Xor(formulas['reference_preconditions'], formulas['candidate_preconditions'])],
        'safety_under_reference_preconditions': [formulas['reference_preconditions'],
            z3.Xor(formulas['reference_safety'], formulas['candidate_safety'])]
    }
    results = {}
    for key, conditions in queries.items():
        solver = z3.Solver(); solver.set(timeout=5000); solver.add(*domain, *conditions)
        status = str(solver.check())
        witness = None
        if status == 'sat':
            model = solver.model()
            witness = {name: str(model.eval(var, model_completion=True)) for name, var in variables.items()}
        results[key] = {'solver_status': status,
                        'comparison': 'equivalent' if status == 'unsat' else 'different' if status == 'sat' else 'unknown',
                        'difference_witness': witness}
    return {'case_id': case['id'], 'reference_status': 'pending_user_review',
            'scope': 'aligned abstract formulas only; no semantic understanding or code validation',
            'checks': results,
            'both_equivalent': all(item['solver_status'] == 'unsat' for item in results.values()),
            'model_calls': 0, 'consistency_verdict': 'not_evaluated'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case', choices=[case['id'] for case in cases()])
    parser.add_argument('--candidate', type=Path)
    args = parser.parse_args()
    if bool(args.case) != bool(args.candidate):
        parser.error('--case and --candidate must be supplied together')
    if args.candidate:
        case = next(item for item in cases() if item['id'] == args.case)
        result = compare(case, json.loads(args.candidate.read_text()))
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result['both_equivalent'] else 2
    results = [compare(case, {key: case[key] for key in ('preconditions', 'safety')}) for case in cases()]
    print(json.dumps({'run_kind': 'reference_self_check_NOT_model_accuracy', 'model_calls': 0,
                      'results': results}, ensure_ascii=False, indent=2))
    return 0 if all(item['both_equivalent'] for item in results) else 2


if __name__ == '__main__': raise SystemExit(main())
