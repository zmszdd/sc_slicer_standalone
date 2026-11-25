#!/usr/bin/env python3
"""Refresh only the negative slice-readiness metadata of a frozen sample.

The case list, seed, labels and strata are copied through unchanged. This is
needed because the original pool marks raw ``flatten_sorted`` availability,
while the locked gate needs mainline stage-1 witness artifacts.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STAGE3 = HERE.parents[1]
if str(STAGE3) not in sys.path:
    sys.path.insert(0, str(STAGE3))
from lib import path_config

DEFAULT_SAMPLE = HERE / 'mainline_sample_mini.json'
DEFAULT_STATUS = (path_config.c4_output_root()
                  / 'objective_negative_flatten_1_7_13' / 'merged-status.json')
READY_ROUTES = {
    'negative_witness',
    'neutral_entrypoint',
    'self_contained_flatten',
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def refresh(sample_path: Path, status_path: Path, output: Path) -> dict:
    sample = json.loads(sample_path.read_text(encoding='utf-8'))
    status = json.loads(status_path.read_text(encoding='utf-8'))
    before_cases = list(sample.get('negative_cases') or [])
    before_positives = list(sample.get('positive_cases') or [])
    frozen_keys = (
        'schema_version', 'seed', 'source', 'strategy', 'target_positives',
        'selected_positives', 'positive_cases', 'target_negatives',
        'selected_negatives', 'negative_cases', 'negative_count',
        'negative_shortfall', 'negative_population', 'negative_report_ready',
        'negative_source', 'negative_source_sha256', 'negative_label_rule',
        'negative_pool_policy', 'negative_pool_label_agreement',
        'negative_max_project_share', 'negative_strata', 'strata',
        'population', 'dev_exclusion',
    )
    before = {key: sample.get(key) for key in frozen_keys}

    negative_cases = set(before_cases)
    ready = {}
    for row in status.get('rows', []):
        case = str(row.get('case') or '')
        artifact = Path(str(row.get('artifact') or ''))
        if (case in negative_cases and row.get('status') == 'flatten_pass'
                and row.get('route') in READY_ROUTES
                and artifact.is_file()):
            ready[case] = str(row.get('artifact_sha256') or '')

    sample['negative_slice_ready'] = len(ready)
    sample['negative_slice_source'] = str(status_path)
    sample['negative_slice_source_sha256'] = _sha256(status_path)
    sample['negative_slice_artifacts_sha256'] = hashlib.sha256(
        json.dumps(ready, sort_keys=True).encode('utf-8')).hexdigest()

    if list(sample.get('negative_cases') or []) != before_cases:
        raise SystemExit('negative case list changed')
    if list(sample.get('positive_cases') or []) != before_positives:
        raise SystemExit('positive case list changed')
    if any(sample.get(key) != value for key, value in before.items()):
        raise SystemExit('frozen sample field changed')

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(sample, ensure_ascii=False, indent=2) + '\n',
                      encoding='utf-8')
    return {
        'schema_version': 'negative-slice-readiness-refresh/1',
        'negative_cases': len(before_cases),
        'negative_slice_ready': len(ready),
        'sample': str(output),
        'status': str(status_path),
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sample', type=Path, default=DEFAULT_SAMPLE)
    parser.add_argument('--status', type=Path, default=DEFAULT_STATUS)
    parser.add_argument('--output', type=Path, default=None)
    args = parser.parse_args(argv)
    result = refresh(args.sample, args.status, args.output or args.sample)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
