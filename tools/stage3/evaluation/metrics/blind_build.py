#!/usr/bin/env python3
"""Blind-set PoC skeleton build status.

The blind set is blocked by missing PoC skeletons (``test/`` + ``src/``).
This script reports, and optionally drives, the resurrection step that turns a
``sorted_flatten_path`` slice into a Foundry harness.  It records compile status
per case so stage-5 progress is observable without guessing.

Run with cwd = tools/stage3/evaluation/metrics:
    python blind_build.py                 # report current status only
    python blind_build.py --build --limit 3   # resurrect up to 3 slices
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BLIND = HERE / 'blind_set.json'
OUT_JSON = HERE / 'blind_build_status.json'
OUT_MD = HERE / 'blind_build_status.md'
REPO = Path(__file__).resolve().parents[4]
RESURRECT = REPO / 'run_sol_resurrect.sh'
PILOT_ROOT = REPO / 'runs' / 'sol_resurrect' / 'blind_pilot'


def case_output_dir(case: str) -> Path:
    return PILOT_ROOT / case


def compile_status(case_dir: Path) -> dict:
    """Return compile status for a resurrected case dir, if present."""
    test_file = case_dir / 'test' / 'Resurrected.t.sol'
    if not test_file.is_file():
        return {'built': False, 'compile': 'missing_test'}
    proc = subprocess.run(
        ['forge', 'build'], cwd=str(case_dir), capture_output=True, text=True)
    log = (proc.stdout or '') + (proc.stderr or '')
    return {
        'built': True,
        'compile': 'ok' if proc.returncode == 0 else 'failed',
        'exit': proc.returncode,
        'log_tail': log[-800:],
    }


def resurrect(case: dict) -> dict:
    case_dir = case_output_dir(case['case'])
    slice_path = case.get('sorted_flatten_path')
    if not slice_path or not Path(slice_path).is_file():
        return {'built': False, 'compile': 'missing_slice'}
    output = case_dir / 'Resurrected.t.sol'
    cmd = [str(RESURRECT), slice_path, '--config',
           str(REPO / 'config' / 'llm.env'), '--output', str(output)]
    proc = subprocess.run(cmd, capture_output=True, text=True,
                          cwd=str(REPO), timeout=600)
    status = compile_status(case_dir)
    status['resurrect_exit'] = proc.returncode
    status['resurrect_tail'] = ((proc.stdout or '') + (proc.stderr or ''))[-800:]
    return status


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', action='store_true')
    parser.add_argument('--limit', type=int, default=0,
                        help='max slices to resurrect (0 = all missing)')
    parser.add_argument('--cases', default=None,
                        help='comma-separated case ids to restrict to')
    args = parser.parse_args()

    blind = json.loads(BLIND.read_text())
    wanted = set(args.cases.split(',')) if args.cases else None
    rows = []
    built = 0
    for item in blind['cases']:
        case = item['case']
        case_dir = case_output_dir(case)
        in_scope = wanted is None or case in wanted
        if (case_dir / 'Resurrected.t.sol').is_file():
            status = compile_status(case_dir)
        elif in_scope and args.build and (args.limit == 0 or built < args.limit):
            status = resurrect(item)
            built += 1
        else:
            status = {'built': False, 'compile': 'pending_resurrection'}
        rows.append({'case': case, 'project': item['project'], **status})

    ok = sum(1 for r in rows if r.get('compile') == 'ok')
    report = {
        'schema_version': 'blind-build-status/1',
        'generated': '2026-11-13',
        'total': len(rows),
        'built': sum(1 for r in rows if r.get('built')),
        'compile_ok': ok,
        'rows': rows,
    }
    OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')

    lines = [
        '# 盲测 PoC 骨架构建状态',
        '',
        f'盲测样本 **{len(rows)}**；已重建 **{report["built"]}**；'
        f'编译通过 **{ok}**。',
        '',
        '| case | project | 状态 | forge |',
        '| --- | --- | --- | --- |',
    ]
    for r in rows:
        state = 'built' if r.get('built') else 'pending'
        lines.append(f"| {r['case']} | {r['project']} | {state} | "
                     f"{r.get('compile')} |")
    OUT_MD.write_text('\n'.join(lines) + '\n')

    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
