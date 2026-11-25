#!/usr/bin/env python3
"""Prepare official negative cases for objective stage-2/stage-3 evaluation.

Only cases from the frozen mainline negative sample with a verified neutral
stage-1 slice are prepared.  Labels come from the frozen official negative
pool; this script never relabels, resamples or drops a case.
"""
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parents[1]
METRICS = ROOT / 'tools' / 'stage3' / 'evaluation' / 'metrics'
SAMPLE = METRICS / 'mainline_sample_150.json'
SUBMISSIONS = METRICS / 'official_negative_submissions_20261121.json'
READINESS = (ROOT / 'c4_pipeline_output'
             / 'negative_slice_readiness_audit_20261121.json')
INPUTS = (ROOT / 'c4_pipeline_output'
          / 'objective_negative_stage2_inputs_20261121')
FLATTEN = (ROOT / 'c4_pipeline_output'
           / 'objective_negative_flatten_20261121')
GOLDSET = (ROOT / 'c4_pipeline_output'
           / 'objective_negative_goldset_20261121')
STAGE2_ARTIFACTS = ('stage3-spec.json', 'constraints.json', 'formalization.json')


def _load(path: Path) -> dict:
    return json.loads(Path(path).read_text())


def _negative_ids() -> list[str]:
    sample = _load(SAMPLE)
    return [str(case) for case in sample['negative_cases']]


def _artifacts() -> list[dict]:
    rows = _load(READINESS)['artifacts']
    return sorted(rows, key=lambda row: _negative_ids().index(row['case'])
                  if row['case'] in _negative_ids() else len(_negative_ids()))


def prepare(args: argparse.Namespace) -> int:
    submissions = _load(SUBMISSIONS)
    by_uid = {str(row.get('uid')): row for row in submissions}
    artifacts = _artifacts()
    cases = []
    for record in artifacts:
        case = str(record['case'])
        parts = case.split('__')
        if len(parts) != 3:
            raise SystemExit(f'unexpected negative case id: {case}')
        submission = by_uid.get(parts[2])
        if submission is None:
            raise SystemExit(f'official submission missing: {case}')
        body = str(submission.get('body') or '').strip()
        if not body:
            raise SystemExit(f'official submission has no report body: {case}')
        report_dir = args.inputs / case
        report_dir.mkdir(parents=True, exist_ok=True)
        (report_dir / 'report.json').write_text(json.dumps({
            'schema_version': 'official-negative-report/1',
            'case': case,
            'project': parts[0],
            'submission_uid': parts[2],
            'finding_uid': parts[1],
            'title': str(submission.get('title') or ''),
            'body': body,
            'validity': 'invalid',
            'source': str(SUBMISSIONS.relative_to(ROOT)),
        }, ensure_ascii=False, indent=2) + '\n')
        source = Path(record['artifact'])
        if not source.is_file():
            raise SystemExit(f'slice artifact missing: {source}')
        flatten_dir = args.flatten / case
        flatten_dir.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, flatten_dir / 'contract.flattened.t.sol')
        cases.append({'id': case, 'case_directory': case})
    (args.inputs / 'stage2_manifest.json').write_text(json.dumps({
        'data_root': str(args.inputs.resolve()),
        'cases': cases,
    }, ensure_ascii=False, indent=2) + '\n')
    (args.inputs / 'cases.json').write_text(json.dumps(
        [row['id'] for row in cases], ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'prepared': len(cases),
                      'inputs': str(args.inputs),
                      'flatten': str(args.flatten)}, indent=2))
    return 0


def assemble(args: argparse.Namespace) -> int:
    cases = _load(args.inputs / 'cases.json')
    runs = args.goldset / 'runs_01'
    runs.mkdir(parents=True, exist_ok=True)
    ready = []
    for case in cases:
        source = args.stage2 / case
        if not all((source / name).is_file() for name in STAGE2_ARTIFACTS):
            continue
        target = runs / case
        target.mkdir(parents=True, exist_ok=True)
        for name in STAGE2_ARTIFACTS:
            shutil.copyfile(source / name, target / name)
        ready.append({'case': case})
    (args.goldset / 'selection.json').write_text(json.dumps({
        'schema_version': 'official-negative-goldset/1',
        'cases': ready,
    }, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'stage2_ready': len(ready),
                      'requested': len(cases),
                      'goldset': str(args.goldset)}, indent=2))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    prepare_parser = sub.add_parser('prepare')
    prepare_parser.set_defaults(handler=prepare)
    prepare_parser.add_argument('--inputs', type=Path, default=INPUTS)
    prepare_parser.add_argument('--flatten', type=Path, default=FLATTEN)
    assemble_parser = sub.add_parser('assemble')
    assemble_parser.set_defaults(handler=assemble)
    assemble_parser.add_argument('--inputs', type=Path, default=INPUTS)
    assemble_parser.add_argument('--stage2', type=Path)
    assemble_parser.add_argument('--goldset', type=Path, default=GOLDSET)
    args = parser.parse_args(argv)
    if args.command == 'assemble' and args.stage2 is None:
        parser.error('assemble requires --stage2')
    return args.handler(args)


if __name__ == '__main__':
    raise SystemExit(main())
