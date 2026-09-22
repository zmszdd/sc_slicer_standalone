"""Replay preliminary human-style ratings and local diagnostics; no model calls."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

HERE = Path(__file__).resolve().parent
MODULE = HERE.parents[1]
sys.path.insert(0, str(MODULE))
import report_only as r
from evidence_catalog import build_catalog, hydrate_elements, hydrate_formalization
from semantic_core import predicate_paths, validate_elements, validate_formalization
from verify_semantic import verify
import z3

DIMENSIONS = ('scope_actors', 'preconditions', 'safety_intent', 'formal_I',
              'core_V', 'qualifiers_coverage')


def diagnostic(case_id, formal):
    """Manually aligned narrow safety only; cannot admit a rejected candidate."""
    symbols = {name: {k: v for k, v in item.items() if k != 'entity_ids'}
               for name, item in formal['symbols'].items()}
    ast = formal['claims'][0]['properties']['safety']['expression']
    result = {'scope': 'assistant-aligned abstract core I under candidate P; no code T'}
    try:
        if ast is None or r.expr_type(ast, symbols) != ('bool', None):
            raise ValueError('missing/non-Boolean I')
    except (ValueError, KeyError) as exc:
        return {**result, 'status': 'type_error', 'error': str(exc)}
    address = z3.DeclareSort('EvaluationAddress')
    v = {name: z3.Bool(name) if item['sort'] == 'bool' else
         z3.Const(name, address) if item['sort'] == 'address' else z3.Int(name)
         for name, item in symbols.items()}
    expected = {
        'kinetiq_pause': lambda: z3.Not(v['hype_withdrawn']),
        'sukuk_authority': lambda: z3.Implies(v['owner_shares_burned'] > 0,
                                              v['caller_allowance_from_owner'] >= v['shares']),
        'merkl_callback': lambda: v['callback_amount'] == v['transferred_toSend'],
        'gte_zero_cost': lambda: z3.Not(v['trade_blocked']),
    }
    if case_id not in expected:
        return {**result, 'status': 'not_evaluated'}
    claim = formal['claims'][0]
    pre = r.lower(claim['properties']['preconditions']['expression'], v)
    actual = r.lower(ast, v)
    reference = expected[case_id]()
    domain = [v[name] >= 0 for name, item in symbols.items() if item['sort'] == 'int']
    feasible = z3.Solver(); feasible.set(timeout=5000); feasible.add(*domain, pre)
    if feasible.check() != z3.sat:
        return {**result, 'status': 'infeasible_or_unknown'}
    solver = z3.Solver(); solver.set(timeout=5000)
    solver.add(*domain, pre, z3.Xor(actual, reference))
    status = solver.check()
    witness = None
    if status == z3.sat:
        model = solver.model()
        witness = {name: str(model.eval(var, model_completion=True)) for name, var in v.items()}
    return {**result, 'status': str(status),
            'comparison': 'equivalent_in_narrow_context' if status == z3.unsat else
                          'different' if status == z3.sat else 'unknown',
            'difference_witness': witness}


def evaluate():
    ratings = json.loads((HERE / 'ratings.json').read_text())
    if hashlib.sha256((HERE / 'REFERENCE.md').read_bytes()).hexdigest() != ratings['reference_sha256']:
        raise ValueError('Pre-registered reference changed; review ratings before rerun')
    manifest = json.loads((HERE / 'cases.json').read_text())
    ids = [row['id'] for row in manifest['cases']]
    reviewed = {row['id']: row for row in ratings['cases']}
    if set(reviewed) != set(ids) or len(reviewed) != len(ratings['cases']):
        raise ValueError('Ratings must cover all cases exactly once')
    root = MODULE / 'results' / 'semantic' / 'multi_report_model_01'
    results = []
    identities = set()
    usage_steps = []
    for case_id in ids:
        manual = reviewed[case_id]
        if set(manual['ratings']) != set(DIMENSIONS) or any(
                value not in ('pass', 'partial', 'fail', 'not_evaluable')
                for value in manual['ratings'].values()):
            raise ValueError('Invalid rating dimensions/value')
        directory = root / case_id
        provenance = json.loads((directory / 'provenance.json').read_text())
        identities.add((provenance['case_id'].split('__')[0], provenance['finding_uid']))
        raw = (directory / 'original-report').read_bytes()
        text = (directory / 'extraction-input.txt').read_text()
        if r.sha(raw) != provenance['report_sha256'] or r.sha(text.encode()) != provenance['report_input_sha256']:
            raise ValueError('Input snapshot mismatch')
        if text != r.prose_only(json.loads(raw)['body']):
            raise ValueError('Prose derivation mismatch')
        catalog = json.loads((directory / 'evidence-catalog.json').read_text())
        if catalog != build_catalog(text):
            raise ValueError('Evidence catalog mismatch')
        elements_raw = json.loads((directory / 'elements-ids.json').read_text())
        formal_raw = json.loads((directory / 'formalization-ids.json').read_text())
        elements = hydrate_elements(elements_raw, catalog, text)
        formal = hydrate_formalization(formal_raw, catalog, text)
        if elements != json.loads((directory / 'elements.json').read_text()) or formal != json.loads((directory / 'formalization.json').read_text()):
            raise ValueError('Hydrated output mismatch')
        validate_elements(elements, text)
        for name, candidate in (('neural-elements', elements_raw), ('neural-formalization', formal_raw)):
            if candidate != json.loads((directory / name / 'model-claim.json').read_text()):
                raise ValueError('Original model candidate changed')
            usage_steps.extend(json.loads((directory / name / 'model-usage.json').read_text())['steps'])
        status = json.loads((directory / 'status.json').read_text())
        error = None
        try:
            validate_formalization(formal, elements, text)
        except ValueError as exc:
            error = str(exc)
        if error != status.get('error'):
            raise ValueError('Formal validation rejection does not replay')
        missing = []
        invalid_links = []
        type_errors = []
        symbol_base = {n: {k: v for k, v in item.items() if k != 'entity_ids'}
                       for n, item in formal['symbols'].items()}
        for claim in formal['claims']:
            for name, prop in claim['properties'].items():
                try:
                    paths = set(predicate_paths(prop['expression'], symbol_base)) if prop['expression'] is not None else set()
                except ValueError as exc:
                    paths = set()
                    type_errors.append({'claim': claim['id'], 'property': name, 'error': str(exc)})
                absent = sorted(paths - set(claim['formula_sources'][name]))
                if absent:
                    missing.append({'claim': claim['id'], 'property': name, 'paths': absent})
                for path, sources in claim['formula_sources'][name].items():
                    if not set(sources) <= set(prop['source_ids']):
                        invalid_links.append({'claim': claim['id'], 'property': name, 'path': path,
                                              'outside_property_sources': sorted(set(sources) - set(prop['source_ids']))})
        full_replay = verify(directory) if (directory / 'constraints.json').exists() else None
        results.append({**manual, 'pipeline_status': status,
                        'elements_grounding_replayed': True,
                        'formal_validation_error_replayed': error,
                        'missing_formula_source_paths': missing,
                        'invalid_subformula_sources': invalid_links,
                        'additional_formula_type_errors': type_errors,
                        'additional_invalid_symbol_names': [name for name in formal['symbols']
                            if not re.fullmatch(r'[a-z][a-z0-9_]{0,63}', name)],
                        'full_pipeline_replay': full_replay,
                        'narrow_I_diagnostic': diagnostic(case_id, formal),
                        'candidate_hashes': {name: r.sha((directory / name).read_bytes())
                            for name in ('elements-ids.json', 'formalization-ids.json')},
                        'complete_semantic_pass': all(x == 'pass' for x in manual['ratings'].values())})
    if len(identities) != len(ids):
        raise ValueError('Duplicate findings cannot count as independent cases')
    total = len(ids)
    counts = {name: {value: sum(row['ratings'][name] == value for row in results)
                        for value in ('pass', 'partial', 'fail', 'not_evaluable')}
              for name in DIMENSIONS}
    return {
        'schema_version': 'preliminary-multi-report-evaluation/1',
        'reviewer': ratings['reviewer'], 'reference_status': ratings['reference_status'],
        'reference_sha256': ratings['reference_sha256'],
        'distinct_reports': total, 'actual_model_invocations': sum(row['pipeline_status']['external_model_invocations'] for row in results),
        'evaluation_model_invocations': 0,
        'metric_counts': counts,
        'preliminary_formal_I_pass_count': counts['formal_I']['pass'],
        'preliminary_formal_I_pass_percentage': 100 * counts['formal_I']['pass'] / total,
        'formal_pipeline_completed_count': sum(row['full_pipeline_replay'] is not None for row in results),
        'candidate_checks_passed_count': sum(row['pipeline_status']['acceptance_status'] == 'candidate_checks_passed' for row in results),
        'complete_semantic_pass_count': sum(row['complete_semantic_pass'] for row in results),
        'reported_total_tokens': sum(step['tokens']['total'] for step in usage_steps),
        'reported_tokens_by_kind': {k: sum(step['tokens'][k] for step in usage_steps) for k in ('input', 'output', 'reasoning')},
        'reported_cost_not_verified_bill': round(sum(step['cost'] for step in usage_steps), 8),
        'general_accuracy_percentage': None,
        'limitations': ['Five selected short reports, not random sampling',
                       'Assistant-only preliminary reference and grading; no independent expert confirmation',
                       'Pass percentage is core I only, not full-report accuracy',
                       'Rejected raw candidates may be diagnosed but never count as formal pipeline success',
                       'No code T, helper reachability or PoC/report consistency verdict'],
        'results': results,
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, help='optional new JSON archive; never overwrite')
    args = parser.parse_args()
    value = evaluate()
    text = json.dumps(value, ensure_ascii=False, indent=2) + '\n'
    if args.output:
        with args.output.open('x') as stream:
            stream.write(text)
    print(text)
