#!/usr/bin/env python3
"""Long-tail project-prioritised positive sampling from the verified flatten pool.

The current 105-case goldset covers only ~20 projects because the original
sampling rule was "at most 5 per project". This script inverts that bias: it
prioritises projects with the fewest cases (the long tail) and takes at most
``--per-project`` cases from each, so the effective sample size (project count)
grows toward the statistical target instead of re-sampling the same families.

Run with cwd = tools/stage3:
    python evaluation/sample_longtail.py \\
        --index-csv /root/poc_repro_work/verified_flatten_pass_1568_exact_cases/index.csv \\
        --out evaluation/goldset_v2_pos_longtail/selection.json \\
        --name goldset_v2_pos_longtail --seed 20261109 --max-cases 50 \\
        --per-project 2
"""
from __future__ import annotations

import argparse
import csv
import json
import random
from collections import defaultdict
from pathlib import Path

SCHEMA = 'stage3-goldset-selection/1'


def sample_longtail(rows: list[dict], *, seed: int, max_cases: int,
                    per_project: int) -> list[dict]:
    """Return a long-tail-prioritised subset of index rows."""
    by_project: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        project = (row.get('project') or '').strip()
        if project:
            by_project[project].append(row)
    # Stable order inside each project: the input CSV order.
    rng = random.Random(seed)
    projects = sorted(by_project, key=lambda p: (len(by_project[p]), p))
    picked: list[dict] = []
    taken: dict[str, int] = defaultdict(int)
    # Round-robin over projects, long tail first, so every pass pulls one case
    # from as many distinct projects as possible.
    while len(picked) < max_cases:
        advanced = False
        for project in projects:
            if len(picked) >= max_cases:
                break
            if taken[project] >= per_project or taken[project] >= len(by_project[project]):
                continue
            rows_for_project = by_project[project]
            picked.append(rows_for_project[taken[project]])
            taken[project] += 1
            advanced = True
        if not advanced:
            break
    return picked


def _rows_from_csv(index_csv: Path) -> list[dict]:
    with index_csv.open(newline='') as handle:
        return list(csv.DictReader(handle))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--index-csv', required=True, type=Path)
    parser.add_argument('--out', required=True, type=Path)
    parser.add_argument('--name', default='goldset_v2_pos_longtail')
    parser.add_argument('--data-root', default=None,
                        help='flatten corpus root; default: index.csv parent')
    parser.add_argument('--seed', type=int, default=20261109)
    parser.add_argument('--max-cases', type=int, default=50)
    parser.add_argument('--per-project', type=int, default=2)
    parser.add_argument('--validity', default='valid,fixed,wontfix',
                        help='comma-separated validity values to include')
    args = parser.parse_args(argv)

    index_csv = Path(args.index_csv).resolve()
    if not index_csv.is_file():
        raise SystemExit(f'index csv not found: {index_csv}')
    allowed_validity = {v.strip() for v in args.validity.split(',') if v.strip()}
    rows = [r for r in _rows_from_csv(index_csv)
            if r.get('validity') in allowed_validity
            and (r.get('quality') or '') == 'sufficient']

    picked = sample_longtail(rows, seed=args.seed, max_cases=args.max_cases,
                             per_project=args.per_project)
    data_root = str((Path(args.data_root).resolve()
                     if args.data_root else index_csv.parent))
    cases = [{
        'case': row.get('key') or row.get('case_dir'),
        'project': row.get('project'),
        'finding_uid': row.get('finding_uid'),
        'severity': row.get('severity'),
        'title': row.get('title'),
    } for row in picked]
    projects = sorted({c['project'] for c in cases})
    selection = {
        'schema_version': SCHEMA,
        'name': args.name,
        'data_root': data_root,
        'kind': 'positive',
        'expected_verdict': 'violation_reproduced',
        'sampling': {
            'strategy': 'long_tail',
            'seed': args.seed,
            'per_project': args.per_project,
            'distinct_projects': len(projects),
        },
        'cases': cases,
    }
    out = Path(args.out).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(selection, ensure_ascii=False, indent=2) + '\n')
    print(f'sampled {len(cases)} cases across {len(projects)} projects '
          f'(pool={len(rows)} positive rows)')
    print(f'selection -> {out}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
