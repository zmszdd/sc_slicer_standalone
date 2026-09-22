#!/usr/bin/env python3
"""Run a bounded blind v3.7 batch; gold/reference files are never sent to the model."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
from pathlib import Path
import subprocess
import sys


HERE = Path(__file__).resolve().parent
MODULE = HERE.parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--allow-report-upload', action='store_true')
    parser.add_argument('--model', default='opencode-go/deepseek-v4-flash')
    parser.add_argument('--formal-retries', type=int, choices=(0, 1), default=0,
                        help='optional bounded retry of the formalization step only')
    args = parser.parse_args()
    if not args.allow_report_upload:
        parser.error('explicit upload consent required; no model calls made')
    manifest = json.loads((HERE / 'manifest.json').read_text())
    cases = manifest['cases']
    if len(cases) != 5:
        parser.error('gold-v1 blind batch requires exactly five frozen cases')
    for case in cases:
        path = HERE / case['input']
        if case.get('sensitivity') != 'non-sensitive':
            parser.error('all blind inputs must be explicitly non-sensitive')
        if not path.is_file() or sha(path) != case['snapshot_sha256']:
            parser.error('input snapshot mismatch: ' + case['id'])
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / 'blind-manifest.json').write_text(json.dumps({
        'schema_version': 'gold-v1-blind-run/1',
        'prompt_version': 'semantic-v3.7',
        'model': args.model,
        'formal_retries_allowed': args.formal_retries,
        'reference_answers_provided_to_model': False,
        'case_inputs': [{'id': case['id'], 'input': case['input'],
                         'snapshot_sha256': case['snapshot_sha256']} for case in cases],
    }, indent=2) + '\n')

    def run(case):
        output = args.output / case['id']
        command = [sys.executable, str(MODULE / 'semantic_pipeline.py'),
                   '--report', str(HERE / case['input']), '--extract',
                   '--allow-report-upload', '--model', args.model,
                   '--formal-retries', str(args.formal_retries),
                   '--prompt-version', 'semantic-v3.7', '--evidence-mode', 'ids',
                   '--formalization-scope', 'core', '--output', str(output)]
        proc = subprocess.run(command, capture_output=True, text=True)
        if output.is_dir():
            (output / 'pipeline-stdout.txt').write_text(proc.stdout)
        status_path = output / 'status.json'
        status = json.loads(status_path.read_text()) if status_path.is_file() else {
            'error_type': 'MissingStatus', 'error': proc.stderr[-1000:]}
        return {'case_id': case['id'], 'exit_code': proc.returncode, 'status': status}

    results = []
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = {pool.submit(run, case): case['id'] for case in cases}
        for future in as_completed(futures):
            result = future.result(); results.append(result)
            print(json.dumps(result), flush=True)
    ids = [case['id'] for case in cases]
    results.sort(key=lambda result: ids.index(result['case_id']))
    summary = {
        'schema_version': 'gold-v1-blind-summary/1',
        'prompt_version': 'semantic-v3.7',
        'model': args.model,
        'case_count': len(cases),
        'maximum_model_invocations': (2 + args.formal_retries) * len(cases),
        'retry_count': sum(max(0, result['status'].get('external_model_invocations', 0) - 2)
                           for result in results),
        'reference_answers_provided_to_model': False,
        'accuracy': None,
        'accuracy_blocked_until_human_gold_and_ratings_approved': True,
        'results': results,
    }
    (args.output / 'batch-summary.json').write_text(json.dumps(summary, indent=2) + '\n')


if __name__ == '__main__':
    main()
