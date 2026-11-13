#!/usr/bin/env python3
"""Check cross-project blind-sample readiness before a stage1->2->3 run.

The only hard blocker is the missing PoC test skeleton: flatten_sorted slices
contain contracts but no ``test_*`` harness, so each case must first be rebuilt
by ``tools/sol_resurrect_tool``.  This script reports that gap per project.
"""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
BLIND = HERE / 'blind_set.json'
ROOT = HERE.parents[4]
STAGE3 = ROOT / 'tools' / 'stage3'


def main() -> int:
    data = json.loads(BLIND.read_text())
    rows = []
    for case in data['cases']:
        flat = Path(case.get('sorted_flatten_path') or '')
        has_slice = flat.is_file()
        case_dir = STAGE3 / 'cases' / case['case']
        has_stage2 = (case_dir / 'stage2_run' / 'stage3-spec.json').is_file()
        has_poc_src = (case_dir / 'src').is_dir()
        has_poc_test = (case_dir / 'test').is_dir()
        rows.append({
            'case': case['case'],
            'project': case['project'],
            'slice': has_slice,
            'stage2_run': has_stage2,
            'poc_src': has_poc_src,
            'poc_test': has_poc_test,
            'ready': has_slice and has_stage2 and has_poc_src and has_poc_test,
        })
    ready = sum(1 for r in rows if r['ready'])
    missing_poc = sum(1 for r in rows if r['slice'] and not r['poc_test'])
    print(f'blind cases: {len(rows)}')
    print(f'fully ready: {ready}')
    print(f'have slice but missing PoC skeleton: {missing_poc}')
    for r in rows[:12]:
        print(' ', 'READY ' if r['ready'] else 'BLOCK', r['case'])
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
