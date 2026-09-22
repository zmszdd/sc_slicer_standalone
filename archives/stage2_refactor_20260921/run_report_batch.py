"""Bounded report-only batch. Default is offline replay, never automatic upload."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, default=HERE / 'report_cases.json')
    parser.add_argument('--data-root', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--mode', choices=('replay', 'extract'), default='replay')
    parser.add_argument('--allow-report-upload', action='store_true')
    parser.add_argument('--model')
    args = parser.parse_args()
    if args.mode == 'extract' and not args.allow_report_upload:
        parser.error('extract requires explicit report-upload authorization')
    manifest = json.loads(args.manifest.read_text())
    cases = manifest['cases']
    if not 1 <= len(cases) <= 3: parser.error('this smoke batch allows at most three cases/calls')
    data_root = args.data_root or Path(manifest['data_root'])
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / 'case-manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
    rows = []
    for case in cases:
        ident = case['id']
        if not ident or Path(ident).name != ident or ident in ('.', '..'):
            raise ValueError('invalid case output name')
        output = args.output / ident
        command = [sys.executable, str(HERE / 'report_only.py'), '--case-dir',
                   str(data_root / case['case_directory']), '--output', str(output)]
        if args.mode == 'replay':
            command += ['--replay', str(HERE / case['candidate']), '--candidate-origin', 'assistant_review']
        else:
            command += ['--allow-report-upload']
            if args.model: command += ['--model', args.model]
        proc = subprocess.run(command, capture_output=True, text=True)
        status_path = output / 'status.json'
        status = json.loads(status_path.read_text()) if status_path.exists() else {'formalization_status': 'runtime_failed'}
        missing = []
        if (output / 'stage3-spec.json').exists():
            missing = json.loads((output / 'stage3-spec.json').read_text())['missing_properties']
        rows.append({'id': ident, 'category': case['category'], 'exit_code': proc.returncode,
                     'formalization_status': status['formalization_status'], 'missing_properties': missing,
                     'candidate_origin': 'assistant_review' if args.mode == 'replay' else 'external_model',
                     'review_note': case['review_note'], 'consistency_verdict': 'not_evaluated'})
        summary = {'mode': args.mode, 'external_model_invocations': len(rows) if args.mode == 'extract' else 0,
                   'automatic_extraction_accuracy': None, 'cases': rows}
        (args.output / 'batch-summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2))
        print(json.dumps(rows[-1], ensure_ascii=False), flush=True)
    return 0 if all(x['formalization_status'] == 'formalized_candidate' for x in rows) else 2


if __name__ == '__main__': raise SystemExit(main())
