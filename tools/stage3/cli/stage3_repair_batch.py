#!/usr/bin/env python3
"""批量收口 LLM 修复闭环：对可恢复 FN 案例逐个跑 ``stage3_verdict_loop``。

默认只产出可复现的修复队列（``repair_queue.json``）；传 ``--run`` 才真正执行。
执行支持 ``--limit`` 分批推进，避免一次跑满 38 例、也便于断点续跑。
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]  # tools/stage3
DEFAULT_TRIAGE = ROOT / 'evaluation' / 'metrics' / 'repro_failure_triage.json'
DEFAULT_CASES = ROOT / 'cases'
DEFAULT_OUT = ROOT / 'evaluation' / 'metrics' / 'repair_queue.json'

# 可恢复桶：不含机制天花板（not_dynamically_expressible /
# reference_patch_required）与阶段二前置失败。
RECOVERABLE_BUCKETS = {
    'invariant_holds_on_exploit_path',
    'mixed_non_dynamic',
    'dynamic:other',
    'poc_not_witnessed',
    'inconclusive',
    'partial_binding',
}


def recoverable_cases(triage: dict, cases_root: Path) -> list[dict]:
    rows = []
    for row in triage.get('rows', []):
        if row.get('bucket') not in RECOVERABLE_BUCKETS:
            continue
        case = row.get('case')
        case_dir = cases_root / case
        if not (case_dir / 'stage2_run' / 'stage3-spec.json').is_file():
            continue
        rows.append({
            'case': case,
            'bucket': row.get('bucket'),
            'case_dir': str(case_dir),
            'command': ['cli.stage3_verdict_loop', '--case-dir', str(case_dir),
                        '--max-rounds', '2'],
        })
    return rows


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--triage', type=Path, default=DEFAULT_TRIAGE)
    parser.add_argument('--cases-root', type=Path, default=DEFAULT_CASES)
    parser.add_argument('--out', type=Path, default=DEFAULT_OUT)
    parser.add_argument('--run', action='store_true',
                        help='实际执行 stage3_verdict_loop（默认只产出队列）')
    parser.add_argument('--limit', type=int, default=0,
                        help='执行上限；0=全部')
    parser.add_argument('--max-rounds', type=int, default=2)
    args = parser.parse_args(argv)

    triage = json.loads(args.triage.read_text())
    rows = recoverable_cases(triage, args.cases_root)
    for row in rows:
        row['command'][-1] = str(args.max_rounds)
    args.out.write_text(json.dumps({
        'schema_version': 'stage3-repair-queue/1',
        'source': str(args.triage),
        'count': len(rows),
        'cases': rows,
    }, ensure_ascii=False, indent=2) + '\n')

    if not args.run:
        print(f'queue={len(rows)} -> {args.out}')
        for row in rows[:10]:
            print('  ', row['bucket'], row['case'])
        if len(rows) > 10:
            print(f'  ... and {len(rows) - 10} more')
        return 0

    todo = rows[:args.limit] if args.limit else rows
    for index, row in enumerate(todo, 1):
        print(f'[{index}/{len(todo)}] {row["case"]}', flush=True)
        proc = subprocess.run(
            [sys.executable, '-m'] + row['command'], cwd=str(ROOT))
        if proc.returncode != 0:
            print(f'  verdict_loop exit={proc.returncode}', file=sys.stderr)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
