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


def project_id_from_dir_name(name: str) -> str:
    """Best-effort project id is the trailing underscore token of a dir name.

    Both ``c4_pipeline_output`` (``Recall_MW5DuS6ehpj``) and
    ``code4rena_reports`` (``88mph contest_8XSaD63X7RM``) name project
    directories as ``<slug>_<project_id>``, so the last underscore token is the
    stable join key across the two trees.
    """
    return name.rsplit('_', 1)[-1]


def discover_candidates(flatten_root: Path,
                        reports_root: Path) -> list[dict]:
    """Enumerate every project with both a flatten slice and a submission dump.

    This is the deterministic source of truth for scale-up: the queue should be
    derived from disk instead of maintained by hand. A project is only counted
    when it has at least one ``*.sorted.sol`` slice *and* at least one
    ``submission_*.json``/``raw_submissions.json`` dump.
    """
    submissions_by_id: dict[str, int] = {}
    for d in reports_root.iterdir():
        if not d.is_dir():
            continue
        count = len(list(d.glob('submission_*.json')))
        if (d / 'raw_submissions.json').is_file():
            count += 1
        if count <= 0:
            continue
        pid = project_id_from_dir_name(d.name)
        submissions_by_id[pid] = max(submissions_by_id.get(pid, 0), count)

    slices_by_id: dict[str, dict] = {}
    for d in flatten_root.iterdir():
        if not d.is_dir():
            continue
        sorted_sols = sorted(d.rglob('*.sorted.sol'))
        if not sorted_sols:
            continue
        pid = project_id_from_dir_name(d.name)
        current = slices_by_id.get(pid)
        if current is None or len(sorted_sols) > current['sorted_sol_count']:
            slices_by_id[pid] = {
                'project': d.name,
                'flatten_out_dirs': 1,
                'sorted_sol_count': len(sorted_sols),
            }

    rows = []
    for pid, flat in slices_by_id.items():
        submissions = submissions_by_id.get(pid, 0)
        rows.append({
            'project_id': pid,
            'project': flat['project'],
            'flatten_out_dirs': flat['flatten_out_dirs'],
            'sorted_sol_count': flat['sorted_sol_count'],
            'submissions_count': submissions,
            'ready': submissions > 0,
            'blocker': (None if submissions > 0
                        else 'has flatten slices but no submission dump'),
        })
    rows.sort(key=lambda row: (-row['submissions_count'],
                               -row['sorted_sol_count']))
    return rows


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


def _expand_exclude_ids(exclude: str | None) -> set[str]:
    ids: set[str] = set()
    if not exclude:
        return ids
    path = Path(exclude)
    if path.is_file():
        data = json.loads(path.read_text())
        if isinstance(data, dict):
            data = data.get('project_ids', data.get('cases', []))
        for item in data:
            if isinstance(item, str):
                ids.add(project_id_from_dir_name(item))
            elif isinstance(item, dict):
                for key in ('project_id', 'case'):
                    if item.get(key):
                        ids.add(str(item[key]).split('__')[0].rsplit('_', 1)[-1])
                        break
    else:
        for part in exclude.split(','):
            part = part.strip()
            if part:
                ids.add(part)
    return ids


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--expansion', type=Path, default=DEFAULT_EXPANSION)
    parser.add_argument('--flatten-root', type=Path, default=DEFAULT_FLATTEN_ROOT)
    parser.add_argument('--reports-root', type=Path, default=DEFAULT_REPORTS_ROOT)
    parser.add_argument('--out', type=Path, default=DEFAULT_OUT)
    parser.add_argument('--discover', action='store_true',
                        help='enumerate every project with flatten slices + '
                             'submission dumps into --discover-out (does NOT '
                             'overwrite the curated --expansion queue)')
    parser.add_argument('--discover-out', type=Path,
                        default=Path(__file__).with_name(
                            'scale_expansion_discovered.json'),
                        help='output file for --discover')
    parser.add_argument('--exclude', default=None,
                        help='comma-separated project ids, or a JSON file of '
                             '{"project_ids": [...]} to exclude from discovery')
    args = parser.parse_args(argv)

    expansion = json.loads(args.expansion.read_text())
    if args.discover:
        already_queued = {project_id_from_dir_name(item.get('project', ''))
                          for item in expansion.get('queue', [])}
        exclude = already_queued | _expand_exclude_ids(args.exclude)
        candidates = discover_candidates(args.flatten_root, args.reports_root)
        fresh = [r for r in candidates if r['project_id'] not in exclude]
        discovered = {
            'schema_version': 'scale-expansion-discovered/1',
            'source': str(args.expansion),
            'exclude': sorted(exclude),
            'count': len(fresh),
            'ready_count': sum(1 for r in fresh if r['ready']),
            'submissions_total': sum(r['submissions_count'] for r in fresh),
            'rows': fresh,
        }
        args.discover_out.write_text(
            json.dumps(discovered, ensure_ascii=False, indent=2) + '\n')
        print(f"discovered {len(fresh)} candidate(s) not already queued "
              f"({discovered['ready_count']} ready) -> {args.discover_out}")
        return 0

    rows = verify(expansion, args.flatten_root, args.reports_root)
    ready = [r for r in rows if r['ready']]
    gap = max(0, int(expansion.get('target_independent_projects', 0))
              - int(expansion.get('current_projects', 0)) - len(ready))
    payload = {
        'schema_version': 'scale-expansion-ready/1',
        'source': str(args.expansion),
        'target_independent_projects': expansion.get('target_independent_projects'),
        'current_projects': expansion.get('current_projects'),
        'ready_projects': len(ready),
        'gap_projects': gap,
        'rows': rows,
    }
    args.out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n')
    print(f"ready={len(ready)}/{len(rows)}  gap_projects={gap}")
    for r in rows:
        print(f"  {'READY' if r['ready'] else 'MISS '} {r['project_id']} "
              f"sorted_sol={r['sorted_sol_count']} "
              f"submissions={r['submissions_count']}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
