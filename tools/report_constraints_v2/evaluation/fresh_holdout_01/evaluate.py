#!/usr/bin/env python3
"""Read-only stage-2 holdout audit; never calls a model or edits results."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
STAGE2 = HERE.parents[1]
sys.path.insert(0, str(STAGE2))
for _d in (STAGE2 / 'lib', STAGE2 / 'cli'):
    _s = str(_d)
    if _s not in sys.path:
        sys.path.insert(0, _s)

from cli.semantic_pipeline import load_report  # noqa: E402
from prompts.versions import semantic_prompts_v311 as prompts  # noqa: E402
from cli.batch_verify import verify  # noqa: E402

DIMENSIONS = ('P_evidence', 'P_semantics', 'I_evidence', 'I_semantics',
              'V_evidence', 'V_semantics')
RATINGS = ('pass', 'partial', 'fail', 'unknown', 'not_evaluable')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


# S10：代码已迁至 cli/ 与 lib/，部分模块被合并、原文件名已不再指向实现。
# 记录/校验哈希时，按“现在真正包含该代码的文件”来解析名字。
CODE_PATHS = {
    'semantic_pipeline.py': 'cli/semantic_pipeline.py',
    'report_only.py': 'lib/report_only.py',
    'plan_synthesizer.py': 'lib/plan_synthesizer.py',
    'semantic_core.py': 'lib/semantic_core.py',
    'evidence_catalog.py': 'lib/ingest.py',
    'report_readiness.py': 'lib/ingest.py',
    'fidelity.py': 'lib/salvage.py',
    'numeric_fidelity.py': 'lib/salvage.py',
    'address_fidelity.py': 'lib/salvage.py',
    'review.py': 'lib/solving.py',
    'symbolic_queries.py': 'lib/solving.py',
}


def code_path(name):
    if name.startswith('semantic_prompts'):
        return STAGE2 / 'prompts/versions' / name
    return STAGE2 / CODE_PATHS.get(name, name)


def read_json(path):
    return json.loads(path.read_text())


def validate_manifest(path):
    manifest = read_json(path)
    require(manifest.get('schema_version') == 'stage2-fresh-holdout/1', 'manifest schema mismatch')
    require(manifest.get('prompt_version') == prompts.PROMPT_VERSION, 'prompt version changed')
    require(manifest.get('input_policy') == 'report-json-input/3', 'input policy changed')
    require(manifest.get('element_prompt_sha256') == sha(prompts.ID_ELEMENT_PROMPT.encode()),
            'element prompt changed')
    require(manifest.get('formal_prompt_sha256') == sha(prompts.formal_prompt('ids', 'core').encode()),
            'formal prompt changed')
    code_hashes = manifest.get('code_sha256', {})
    require(isinstance(code_hashes, dict) and code_hashes,
            'frozen implementation hashes missing')
    code_drift = []
    for name, expected in code_hashes.items():
        require(Path(name).name == name, 'unsafe implementation path: ' + name)
        path = code_path(name)
        if sha(path.read_bytes()) != expected:
            code_drift.append(name)
    root = Path(manifest['source_root']).resolve()
    ids, projects = set(), set()
    for case in manifest['cases']:
        cid = case['case_id']
        require(Path(cid).name == cid and cid not in ids, 'duplicate/unsafe case id')
        require(case['project'] not in projects, 'duplicate project stratum')
        ids.add(cid)
        projects.add(case['project'])
        directory = root / cid
        require(directory.is_dir() and directory.resolve().parent == root,
                'missing or escaped case directory: ' + cid)
        text, raw, provenance = load_report(case_dir=directory, input_policy_version=3)
        metadata = read_json(directory / 'metadata.json')
        require(metadata['project'] == case['project'], 'project changed: ' + cid)
        require(provenance['report_sha256'] == case['report_sha256'], 'report changed: ' + cid)
        require(provenance['report_input_sha256'] == case['input_sha256'],
                'model input changed: ' + cid)
        require(len(text.encode()) == case['input_bytes'], 'model input length changed: ' + cid)
        require(provenance['report_input_policy']['policy_version'] == manifest['input_policy'],
                'report input policy changed: ' + cid)
    manifest['_current_code_drift'] = code_drift
    return manifest


def evaluate_runs(manifest, results_root):
    rows = []
    for case in manifest['cases']:
        cid = case['case_id']
        directory = results_root / cid
        if not directory.is_dir():
            rows.append({'case_id': cid, 'state': 'not_run'})
            continue
        provenance = read_json(directory / 'provenance.json')
        require(provenance['report_sha256'] == case['report_sha256'],
                'result report mismatch: ' + cid)
        require(provenance['report_input_sha256'] == case['input_sha256'],
                'result input mismatch: ' + cid)
        require(provenance.get('prompt_version') == manifest['prompt_version'],
                'result prompt mismatch: ' + cid)
        status = read_json(directory / 'status.json')
        extracted = (directory / 'elements.json').is_file() and \
            (directory / 'evidence-spans.json').is_file()
        formalized = (directory / 'formalization.json').is_file() and \
            (directory / 'constraints.json').is_file()
        solver_done = (directory / 'solver-results.json').is_file()
        replay_passed = False
        if formalized and solver_done:
            verify(directory)
            replay_passed = True
        triage_path = directory / 'auto-triage.json'
        route = read_json(triage_path)['route'] if triage_path.is_file() else None
        rows.append({'case_id': cid, 'state': 'finished' if replay_passed else 'incomplete',
                     'extraction_completed': extracted, 'formalization_completed': formalized,
                     'z3_completed': solver_done, 'offline_replay_passed': replay_passed,
                     'route': route,
                     'failure_stage': ('extraction' if not extracted else
                                       'formalization' if not formalized else
                                       'solver_or_replay' if not replay_passed else None),
                     'error_type': status.get('error_type'),
                     'model_invocations': status.get('external_model_invocations', 0)})
    n = len(rows)
    attempted = sum(row['state'] != 'not_run' for row in rows)
    errors = sorted({row['error_type'] for row in rows if row.get('error_type')})
    return {'cases': rows, 'denominator_all_frozen_reports': n,
            'attempted': attempted, 'not_run': n - attempted,
            'failure_types': {name: sum(row.get('error_type') == name for row in rows)
                              for name in errors},
            'extraction_success_rate_on_attempted':
                sum(row.get('extraction_completed', False) for row in rows) / attempted if attempted else None,
            'formalization_success_rate_on_attempted':
                sum(row.get('formalization_completed', False) for row in rows) / attempted if attempted else None,
            'z3_success_rate_on_attempted':
                sum(row.get('z3_completed', False) for row in rows) / attempted if attempted else None,
            'replay_success_rate_on_attempted':
                sum(row.get('offline_replay_passed', False) for row in rows) / attempted if attempted else None,
            'semantic_accuracy': None,
            'semantic_accuracy_reason': 'independent artifact-bound P/I/V ratings not supplied'}


def evaluate_ratings(manifest, results_root, path):
    ratings = read_json(path)
    require(ratings.get('schema_version') == 'stage2-fresh-ratings/1', 'ratings schema mismatch')
    require(ratings.get('reviewer_kind') in ('human', 'independent_model'),
            'reviewer kind missing')
    require(isinstance(ratings.get('reviewer'), str) and ratings['reviewer'].strip(),
            'reviewer identity missing')
    by_id = {row['case_id']: row for row in ratings.get('cases', [])}
    require(len(by_id) == len(ratings.get('cases', [])), 'duplicate rating case')
    require(set(by_id) == {case['case_id'] for case in manifest['cases']},
            'ratings must cover every frozen case')
    counts = {name: {rating: 0 for rating in RATINGS} for name in DIMENSIONS}
    determinate = exact = 0
    for cid, row in by_id.items():
        result = results_root / cid
        artifacts = row.get('artifact_sha256', {})
        if result.is_dir():
            for filename in ('status.json', 'elements.json', 'formalization.json'):
                file = result / filename
                expected = artifacts.get(filename)
                require((expected is None and not file.exists()) or
                        (isinstance(expected, str) and file.is_file() and
                         sha(file.read_bytes()) == expected),
                        'ratings not bound to result artifact: ' + cid + '/' + filename)
        else:
            require(not artifacts, 'unrun case has artifact hashes: ' + cid)
        dimensions = row.get('dimensions', {})
        require(set(dimensions) == set(DIMENSIONS), 'ratings dimensions incomplete: ' + cid)
        if not (result / 'elements.json').is_file():
            require(all(value == 'not_evaluable' for value in dimensions.values()),
                    'case without extracted P/I/V cannot receive semantic ratings: ' + cid)
        require(isinstance(row.get('reason'), str) and row['reason'].strip(),
                'ratings reason missing: ' + cid)
        for name, value in dimensions.items():
            require(value in RATINGS, 'invalid rating: ' + cid + '/' + name)
            counts[name][value] += 1
        if all(dimensions[name] in ('pass', 'partial', 'fail') for name in DIMENSIONS):
            determinate += 1
            exact += all(dimensions[name] == 'pass' for name in DIMENSIONS)
    return {'reviewer_kind': ratings['reviewer_kind'], 'dimension_counts': counts,
            'fully_determinate_cases': determinate, 'strict_all_six_pass_cases': exact,
            'strict_case_accuracy_on_determinate':
                exact / determinate if determinate and ratings['reviewer_kind'] == 'human' else None,
            'interpretation': ('human-reviewed selected pilot cases only; not population accuracy'
                               if ratings['reviewer_kind'] == 'human' else
                               'provisional model review; not a ground-truth accuracy estimate')}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, default=HERE / 'manifest.json')
    parser.add_argument('--results-root', type=Path, default=HERE / 'runs')
    parser.add_argument('--ratings', type=Path)
    args = parser.parse_args()
    manifest = validate_manifest(args.manifest)
    result = {'schema_version': 'stage2-fresh-evaluation/1',
              'selection_frozen': True,
              'current_code_differs_from_frozen': manifest['_current_code_drift'],
              'engineering': evaluate_runs(manifest, args.results_root)}
    if args.ratings:
        result['semantic_review'] = evaluate_ratings(manifest, args.results_root, args.ratings)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
