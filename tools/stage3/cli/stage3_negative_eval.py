#!/usr/bin/env python3
"""Run stage-3 over any set of negative sample cases and emit a result file
that ``full_flow_metrics.py --negative-results`` accepts directly.

与正样本不同，负样本通常每个 case 只有一个 ``binding.json``（也可能有
``bindings/`` 多 claim）。本入口对任意 ``--cases-root``：

1. 找到每个 case（有 ``binding.json`` 或非空 ``bindings/``）；
2. 在独立子进程里跑 ``stage3_pipeline``，一例失败不影响其它；
3. 聚合为 ``--negative-results`` 可读的列表，**保留原始 verdict**（不把
   ``inconclusive`` 重写成 ``violation_not_reproduced``）。

输出：
  --out     负样本结果列表（每行 {case, claim, verdict, status}），可直接喂指标
  --summary 批量汇总（verdict 计数 + 每行明细）

用法（cwd = tools/stage3）：
    python -m cli.stage3_negative_eval \
        --cases-root evaluation/goldset_v2_neg01/cases \
        --out evaluation/goldset_v2_neg01/neg_results.json \
        --summary evaluation/goldset_v2_neg01/neg_batch_summary.json
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]  # tools/stage3
RUNS = ROOT / 'runs'

VERDICTS = {'violation_reproduced', 'violation_not_reproduced', 'inconclusive'}


def _binding_files(case_dir: Path) -> list[Path]:
    """Return the binding files that define claims inside this case."""
    single = case_dir / 'binding.json'
    if single.is_file():
        return [single]
    multi = case_dir / 'bindings'
    if multi.is_dir():
        files = sorted(p for p in multi.iterdir() if p.suffix == '.json')
        if files:
            return files
    return []


def _case_dirs(cases_root: Path, pattern: str | None) -> list[Path]:
    dirs = []
    for child in sorted(cases_root.iterdir()):
        if not child.is_dir():
            continue
        if not _binding_files(child):
            continue
        if pattern and pattern not in child.name:
            continue
        dirs.append(child)
    return dirs


def _existing_summary(case_dir: Path, claim_id: str | None) -> dict | None:
    """Reuse a cached stage3-summary.json for this case.

    优先选终端 verdict（violation_reproduced / violation_not_reproduced），
    避免拿到修复前的 ``inconclusive`` 旧缓存；同类里再取 mtime 最新的。
    """
    if not RUNS.is_dir():
        return None
    matches = []
    for run_dir in RUNS.iterdir():
        if not run_dir.is_dir():
            continue
        summary_path = run_dir / 'stage3-summary.json'
        if not summary_path.is_file():
            continue
        try:
            summary = json.loads(summary_path.read_text())
        except json.JSONDecodeError:
            continue
        if Path(summary.get('case', '')).name != case_dir.name:
            continue
        if claim_id and summary.get('claim_id') != claim_id:
            continue
        verdict = summary.get('consistency_verdict')
        rank = 0 if verdict in {'violation_reproduced', 'violation_not_reproduced'} else 1
        matches.append((rank, summary_path.stat().st_mtime, summary))
    if not matches:
        return None
    matches.sort(key=lambda pair: (pair[0], pair[1]), reverse=False)
    return matches[0][2]


def _run_pipeline(case_dir: Path, binding: Path | None) -> dict:
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')
    run_id = f'{case_dir.name}_{stamp}'
    cmd = [sys.executable, '-m', 'cli.stage3_pipeline',
           '--case-dir', str(case_dir.resolve()), '--run-id', run_id]
    if binding is not None:
        cmd += ['--binding', str(binding.resolve())]
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=str(ROOT))
    if proc.returncode != 0:
        return {
            'case': case_dir.name,
            'status': 'error',
            'claim': None,
            'verdict': None,
            'detail': (proc.stderr or proc.stdout or '').strip()[:600],
        }
    summary = json.loads(proc.stdout)
    return {
        'case': case_dir.name,
        'status': 'ok',
        'claim': summary.get('claim_id'),
        'verdict': summary.get('consistency_verdict'),
    }


def run_one(case_dir: Path, reuse: bool) -> dict:
    bindings = _binding_files(case_dir)
    rows = []
    for binding in bindings:
        claim_id = None
        if binding.name != 'binding.json':
            try:
                claim_id = json.loads(binding.read_text()).get('claim_id')
            except (json.JSONDecodeError, OSError):
                claim_id = None
        if reuse:
            cached = _existing_summary(case_dir, claim_id)
            if cached is not None:
                rows.append({
                    'case': case_dir.name,
                    'status': 'ok',
                    'claim': cached.get('claim_id'),
                    'verdict': cached.get('consistency_verdict'),
                })
                continue
        rows.append(_run_pipeline(case_dir, binding))
    # single-claim case keeps a flat row for readability
    if len(rows) == 1:
        return rows[0]
    return {
        'case': case_dir.name,
        'status': 'multi',
        'claims': rows,
    }


def aggregate(rows: list[dict]) -> dict:
    """Flatten per-case rows into the --negative-results list + batch summary."""
    results = []
    errors = []
    for row in rows:
        if row.get('status') == 'error':
            errors.append(row)
            results.append({
                'case': row['case'],
                'claim': row.get('claim'),
                'verdict': row.get('verdict'),
            })
            continue
        if row.get('status') == 'multi':
            for claim_row in row['claims']:
                results.append({
                    'case': row['case'],
                    'claim': claim_row.get('claim'),
                    'verdict': claim_row.get('verdict'),
                })
            continue
        results.append({
            'case': row['case'],
            'claim': row.get('claim'),
            'verdict': row.get('verdict'),
        })

    counts = {}
    for result in results:
        key = result.get('verdict') or 'unknown'
        counts[key] = counts.get(key, 0) + 1

    summary = {
        'schema_version': 'stage3-negative-eval-summary/1',
        'total_cases': len(rows),
        'total_claims': len(results),
        'errors': len(errors),
        'verdicts': counts,
        'cases': rows,
    }
    return {'results': results, 'summary': summary}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cases-root', required=True,
                        help='directory containing negative case directories')
    parser.add_argument('--out', default=None,
                        help='negative-results JSON path (default: <cases-root>/neg_results.json)')
    parser.add_argument('--summary', default=None,
                        help='batch summary JSON path (default: <cases-root>/neg_batch_summary.json)')
    parser.add_argument('--reuse', action='store_true',
                        help='reuse newest matching stage3-summary.json under tools/stage3/runs')
    parser.add_argument('--max-cases', type=int, default=0,
                        help='limit number of cases (0 = all)')
    parser.add_argument('--filter', dest='pattern',
                        help='only run case directory names containing this')
    args = parser.parse_args(argv)

    cases_root = Path(args.cases_root).resolve()
    if not cases_root.is_dir():
        raise SystemExit(f'--cases-root is not a directory: {cases_root}')
    dirs = _case_dirs(cases_root, args.pattern)
    if args.max_cases > 0:
        dirs = dirs[:args.max_cases]
    if not dirs:
        raise SystemExit('no negative cases found (need binding.json or bindings/)')

    rows = [run_one(d, args.reuse) for d in dirs]
    payload = aggregate(rows)

    out = (Path(args.out) if args.out
           else cases_root.with_name(cases_root.name + '.neg_results.json'))
    summary_path = (Path(args.summary) if args.summary
                    else cases_root.with_name(cases_root.name + '.neg_batch_summary.json'))
    out.parent.mkdir(parents=True, exist_ok=True)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload['results'], ensure_ascii=False, indent=2) + '\n')
    summary_path.write_text(json.dumps(payload['summary'], ensure_ascii=False, indent=2) + '\n')

    print(json.dumps(payload['summary'], ensure_ascii=False, indent=2))
    print(f'\nnegative-results -> {out}')
    print(f'batch-summary     -> {summary_path}')
    return 0 if payload['summary']['errors'] == 0 else 1


if __name__ == '__main__':
    raise SystemExit(main())
