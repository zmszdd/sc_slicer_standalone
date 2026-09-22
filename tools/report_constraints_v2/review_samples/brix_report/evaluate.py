"""Read-only Brix formula comparison; not a general semantic accuracy benchmark."""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import report_only as r
import z3


def evaluate(directory, origin):
    path = ROOT / 'results' / 'semantic' / directory / 'formalization.json'
    formal = json.loads(path.read_text())
    if len(formal['claims']) != 1:
        raise ValueError('This narrow comparison requires exactly one core claim')
    claim = formal['claims'][0]
    variables = {name: z3.Bool(name) if item['sort'] == 'bool' else z3.Int(name)
                 for name, item in formal['symbols'].items()
                 if item['sort'] in {'bool', 'int'}}
    # Manual alignment to the user-reviewed narrow obligation, not model input.
    expected = {
        'preconditions': z3.And(variables['buffered_flow_used'],
                                variables['msg_value'] > variables['native_fee']),
        'safety': z3.Not(variables['paynative_reverted']),
        'effects': z3.And(variables['paynative_reverted'],
                          z3.Not(variables['message_dispatched'])),
    }
    # These mathematical domain assumptions are evaluation-side only.
    domain = [variables['msg_value'] >= 0, variables['native_fee'] >= 0]
    feasible = z3.Solver()
    feasible.set(timeout=5000)
    feasible.add(*domain, expected['preconditions'])
    if feasible.check() != z3.sat:
        raise ValueError('Reference domain must be feasible')
    checks = {}
    for key, reference in expected.items():
        ast = claim['properties'][key]['expression']
        if ast is None:
            checks[key] = {'comparison': 'missing', 'solver_status': None}
            continue
        candidate = r.lower(ast, variables)
        solver = z3.Solver()
        solver.set(timeout=5000)
        solver.add(*domain, z3.Xor(reference, candidate))
        if key != 'preconditions':
            solver.add(expected['preconditions'])
        status = solver.check()
        witness = None
        if status == z3.sat:
            model = solver.model()
            witness = {name: str(model.eval(var, model_completion=True))
                       for name, var in variables.items()}
        checks[key] = {
            'comparison': 'equivalent' if status == z3.unsat else
                          'different' if status == z3.sat else 'unknown',
            'solver_status': str(status), 'difference_witness': witness,
        }
    return {
        'directory': directory, 'origin': origin,
        'formalization_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
        'checks': checks,
        'all_three_narrow_formulas_equivalent': all(
            item['comparison'] == 'equivalent' for item in checks.values()),
    }


def main():
    reference = Path(__file__).with_name('REVIEW.md')
    result = {
        'schema_version': 'brix-local-formula-evaluation/1',
        'reference_sha256': hashlib.sha256(reference.read_bytes()).hexdigest(),
        'reference_basis': 'user-reviewed narrow core obligation; assistant symbol alignment',
        'distinct_real_reports': 1, 'evaluated_latest_model_candidates': 1,
        'new_external_model_calls': 0, 'general_accuracy_percentage': None,
        'scope': 'aligned report-only formulas; no helper arithmetic, code T or PoC execution',
        'domain_assumptions': ['msg_value >= 0', 'native_fee >= 0'],
        'results': [evaluate('brix_fee_ids_core_model_01', 'external_model'),
                    evaluate('brix_observable_control_01', 'assistant_review')],
        'limitations': [
            'Repeated Brix runs are not independent reports',
            'Manual alignment is an assumption, not evidence of correct code binding',
            'Equivalent narrow formulas do not establish complete impact coverage',
            'Assistant control is excluded from model accuracy',
            'No general semantic accuracy or report-validity verdict',
        ],
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
