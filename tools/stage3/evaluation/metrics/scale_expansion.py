#!/usr/bin/env python3
"""扩样就绪性核对：把 scale_expansion.json 的 18 项目队列与本地产物对齐。

扩样的唯一硬瓶颈是 ``flatten_sorted/*.sorted.sol`` 为合约切片、不含 PoC 测试骨架，
需要 ``tools/sol_resurrect_tool`` 重建为可编译 ``.t.sol`` 后再接 stage2 -> stage3。
本脚本只做确定性核对：每个队列项目是否已有 flatten_sorted 切片与 submission
转储，并输出可复现的就绪清单，避免手工维护 scale_expansion.json 漂移。
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
STAGE3 = ROOT / 'tools' / 'stage3'
METRICS = STAGE3 / 'evaluation' / 'metrics'
DEFAULT_EXPANSION = METRICS / 'scale_expansion.json'
DEFAULT_OUT = METRICS / 'scale_expansion_ready.json'
DEFAULT_FLATTEN_ROOT = ROOT / 'c4_pipeline_output'
DEFAULT_REPORTS_ROOT = ROOT / 'code4rena_reports'


def _find_flatten_dirs(flatten_root: Path, project_id: str,
                       project: str) -> list[Path]:
    return [d for d in flatten_root.iterdir() if d.is_dir()
            and (project_id in d.name or project in d.name)]


def verify(expansion: dict, flatten_root: Path,
           reports_root: Path) -> list[dict]:
    rows = []
    for item in expansion.get('queue', []):
        project_id = item.get('project_id')
        project = item.get('project')
        dirs = _find_flatten_dirs(flatten_root, project_id, project)
        sorted_sols = sorted(
            p for d in dirs for p in d.rglob('*.sorted.sol'))
        submissions = sorted(
            p for p in reports_root.glob(f'*{project_id}*/submission_*.json'))
        submissions += sorted(
            p for p in reports_root.glob(f'*{project_id}*/raw_submissions.json'))
        rows.append({
            'project_id': project_id,
            'project': project,
            'flatten_out_dirs': len(dirs),
            'sorted_sol_count': len(sorted_sols),
            'submissions_count': len(submissions),
            'ready': len(sorted_sols) > 0 and len(submissions) > 0,
            'blocker': (None if len(sorted_sols) > 0 and len(submissions) > 0
                        else 'missing flatten_sorted or submission dumps'),
        })
    return rows


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--expansion', type=Path, default=DEFAULT_EXPANSION)
    parser.add_argument('--flatten-root', type=Path, default=DEFAULT_FLATTEN_ROOT)
    parser.add_argument('--reports-root', type=Path, default=DEFAULT_REPORTS_ROOT)
    parser.add_argument('--out', type=Path, default=DEFAULT_OUT)
    args = parser.parse_args(argv)

    expansion = json.loads(args.expansion.read_text())
    rows = verify(expansion, args.flatten_root, args.reports_root)
    ready = [r for r in rows if r['ready']]
    payload = {
        'schema_version': 'scale-expansion-ready/1',
        'source': str(args.expansion),
        'target_independent_projects': expansion.get('target_independent_projects'),
        'current_projects': expansion.get('current_projects'),
        'ready_projects': len(ready),
        'gap_projects': max(0, int(expansion.get('target_independent_projects', 0))
                            - int(expansion.get('current_projects', 0)) - len(ready)),
        'rows': rows,
    }
    args.out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n')
    print(f"ready={len(ready)}/{len(rows)}  gap_projects={payload['gap_projects']}")
    for r in rows:
        print(f"  {'READY' if r['ready'] else 'MISS '} {r['project_id']} "
              f"sorted_sol={r['sorted_sol_count']} "
              f"submissions={r['submissions_count']}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
