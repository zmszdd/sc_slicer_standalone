#!/usr/bin/env python3
"""Record verified negative stage-1 slice readiness on the frozen sample.

The script only updates slice-readiness metadata.  It validates that every
passing case belongs to ``mainline_sample_150.json`` and that the artifact hash in
the stage-1 status report still matches the file on disk.  Case ids, labels,
order, ground truth and denominators are never changed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parents[1]
SAMPLE_DEFAULT = (ROOT / 'tools' / 'stage3' / 'evaluation' / 'metrics'
                  / 'mainline_sample_150.json')
CASES_DEFAULT = (ROOT / 'tools' / 'stage3' / 'evaluation' / 'metrics'
                 / 'official_negative_stage1_cases_20261121.json')
STATUS_DEFAULT = (ROOT / 'c4_pipeline_output'
                  / 'official_negative_neutral_entrypoints_20261121_v2'
                  / 'neutral_entrypoint_status.json')
AUDIT_DEFAULT = (ROOT / 'c4_pipeline_output'
                 / 'negative_slice_readiness_audit_20261121.json')


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sample', type=Path, default=SAMPLE_DEFAULT)
    parser.add_argument('--cases-file', type=Path, default=CASES_DEFAULT)
    parser.add_argument('--status-file', type=Path, default=STATUS_DEFAULT)
    parser.add_argument('--audit', type=Path, default=AUDIT_DEFAULT)
    parser.add_argument('--minimum', type=int, default=40)
    args = parser.parse_args(argv)

    sample = json.loads(args.sample.read_text())
    status = json.loads(args.status_file.read_text())
    negative_ids = [str(case) for case in sample['negative_cases']]
    cases = json.loads(args.cases_file.read_text())['cases']
    stage1_ids = [str(row['case']) for row in cases]
    if set(stage1_ids) != set(negative_ids):
        raise SystemExit('stage-1 case file does not match frozen negatives')

    passed_rows = [row for row in status['rows']
                   if row.get('status') == 'flatten_pass']
    passed_ids = [str(row['case']) for row in passed_rows]
    if len(passed_ids) != len(set(passed_ids)):
        raise SystemExit('duplicate passing case ids in status report')
    if not set(passed_ids).issubset(negative_ids):
        raise SystemExit('passing case outside the frozen negative sample')
    if len(passed_ids) < args.minimum:
        raise SystemExit(f'only {len(passed_ids)} slices pass; '
                         f'minimum is {args.minimum}')

    artifact_records = []
    for row in passed_rows:
        artifact = Path(row['artifact'])
        if not artifact.is_file() or _sha256(artifact) != row['artifact_sha256']:
            raise SystemExit(f'artifact hash mismatch: {row["case"]}')
        artifact_records.append({
            'case': str(row['case']),
            'artifact': str(artifact.resolve()),
            'artifact_sha256': row['artifact_sha256'],
        })
    artifact_records.sort(key=lambda row: negative_ids.index(row['case']))
    artifact_index = hashlib.sha256(json.dumps(
        artifact_records, sort_keys=True, ensure_ascii=False
    ).encode()).hexdigest()

    before = {
        'negative_cases': sample['negative_cases'],
        'positive_cases': sample['positive_cases'],
        'negative_label_rule': sample.get('negative_label_rule'),
        'negative_source_sha256': sample.get('negative_source_sha256'),
    }
    sample['negative_slice_ready'] = len(passed_ids)
    sample['negative_slice_source'] = str(args.status_file.resolve())
    sample['negative_slice_source_sha256'] = _sha256(args.status_file)
    sample['negative_slice_artifacts_sha256'] = artifact_index
    after = {
        'negative_cases': sample['negative_cases'],
        'positive_cases': sample['positive_cases'],
        'negative_label_rule': sample.get('negative_label_rule'),
        'negative_source_sha256': sample.get('negative_source_sha256'),
    }
    if before != after:
        raise SystemExit('sample identity changed unexpectedly')

    args.sample.write_text(json.dumps(sample, ensure_ascii=False, indent=2)
                           + '\n')
    args.audit.parent.mkdir(parents=True, exist_ok=True)
    args.audit.write_text(json.dumps({
        'schema_version': 'negative-slice-readiness/1',
        'sample': str(args.sample.resolve()),
        'negative_slice_ready': len(passed_ids),
        'unresolved': [case for case in negative_ids
                       if case not in set(passed_ids)],
        'artifacts': artifact_records,
    }, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({
        'negative_slice_ready': len(passed_ids),
        'unresolved': len(negative_ids) - len(passed_ids),
    }, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
