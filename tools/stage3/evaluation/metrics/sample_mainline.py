#!/usr/bin/env python3
"""Deterministic stratified mainline sample for the four-metric report.

The dev 105 set is not a random sample of ``judge_ground_truth.json``; it was
built from cases the pipeline already worked on.  This script draws the
mainline evaluation sample directly from the full judge ground truth:

* positives: stratified by project (20 projects) and then by severity inside
  each project, proportional allocation, ``--target-positives`` total;
* negatives: the complete invalid set (precision is cheap to measure and the
  invalid population is only 91 cases).

The output ``mainline_sample.json`` is the single input for
``mainline_metrics.py``, so the same case list drives both execution and the
final report instead of relying on ad-hoc dev selections.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
GT = HERE / 'judge_ground_truth.json'
OUT_JSON = HERE / 'mainline_sample.json'
OUT_MD = HERE / 'mainline_sample.md'
DEFAULT_TARGET = 350
DEFAULT_SEED = 20261115
DEFAULT_TARGET_NEGATIVES = 60
MAX_PROJECT_SHARE = 0.25
EXCLUDE_DEV = HERE / 'positive_eval_161.json'
FROZEN_DEV252 = HERE.parents[1] / 'evaluation' / 'frozen' / 'dev252_20261117.json'
FROZEN_DEV24 = HERE.parents[1] / 'evaluation' / 'frozen' / 'dev24_20261117.json'
DEV_NEGATIVE_FILES = tuple(sorted(
    (HERE / name for name in (
        'positive_eval_blind_invalid.json',
        'positive_eval_blind_invalid_remaining.json',
        'positive_eval_blind_invalid_sukukfi_p1.json',
    )),
))

VALID_STATES = {'valid', 'fixed', 'wontfix'}
SEVERITY_ORDER = ['high', 'medium', 'low']


def _alloc_proportional(pop_sizes: dict[str, int], total: int,
                        minimum: int = 1) -> dict[str, int]:
    """Proportional allocation with a floor per non-empty stratum.

    ``minimum`` only applies when every non-empty stratum has at least one
    member; a stratum smaller than the floor gets its whole population and the
    remainder is redistributed so the allocation never exceeds a stratum size.
    """
    if total <= 0:
        return {k: 0 for k in pop_sizes}

    alloc = {k: min(size, minimum) if size else 0 for k, size in pop_sizes.items()}
    remaining = total - sum(alloc.values())
    if remaining <= 0:
        return alloc

    room = {k: pop_sizes[k] - alloc[k] for k in pop_sizes if pop_sizes[k] > alloc[k]}
    total_room = sum(room.values())
    if total_room <= 0:
        return alloc

    quotas = {k: remaining * room[k] / total_room for k in room}
    floors = {k: int(q) for k, q in quotas.items()}
    used = sum(floors.values())
    order = sorted(quotas, key=lambda k: quotas[k] - floors[k], reverse=True)
    i = 0
    while used < remaining and i < len(order):
        key = order[i % len(order)]
        if alloc[key] + floors[key] < pop_sizes[key]:
            floors[key] += 1
            used += 1
        i += 1
    for key in pop_sizes:
        alloc[key] = min(pop_sizes[key], alloc[key] + floors.get(key, 0))
    return alloc


def _draw(values: list[dict], k: int, rng: random.Random) -> list[dict]:
    return rng.sample(values, k)


def _sha256(path: Path) -> str | None:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return None


def _alloc_capped(pop_sizes: dict[str, int], total: int, *,
                  max_share: float = MAX_PROJECT_SHARE) -> tuple[dict[str, int], int]:
    """Proportional allocation with a per-project ceiling.

    Returns ``(allocation, shortfall)``.  The ceiling is derived from the
    requested total so one project cannot dominate the precision sample.
    """
    if total <= 0:
        return {name: 0 for name in pop_sizes}, 0
    cap = max(1, int(total * max_share))
    capacities = {name: min(size, cap) for name, size in pop_sizes.items()}
    available = sum(capacities.values())
    target = min(total, available)
    alloc = _alloc_proportional(capacities, target, minimum=1)
    return alloc, total - sum(alloc.values())


def frozen_dev_case_ids() -> set[str]:
    """Every case id used by the frozen development contracts.

    ``positive_eval_161.json`` only covers the original dev anchor.  The
    frozen dev252 list contains 96 additional cases, and the blind-invalid
    files contain the negative cases used during development.  All of them
    must be excluded from an evaluation sample.
    """
    ids: set[str] = set()
    for path in (FROZEN_DEV252, FROZEN_DEV24):
        if not path.is_file():
            continue
        data = json.loads(path.read_text())
        rows = (data.get('case_list') or {}).get('cases') or []
        if not rows:
            rows = data.get('cases') or []
        for row in rows:
            if not isinstance(row, dict):
                continue
            case = row.get('case_id') or row.get('case')
            if case:
                ids.add(str(case))
    for path in DEV_NEGATIVE_FILES:
        if not path.is_file():
            continue
        data = json.loads(path.read_text())
        for row in data.get('cases') or []:
            case = row.get('case') if isinstance(row, dict) else None
            if case:
                ids.add(str(case))
    return ids


def official_negative_pool(path: Path) -> dict:
    """Load and validate a frozen official-judge negative pool."""
    path = Path(path)
    data = json.loads(path.read_text())
    if str(data.get('schema_version') or '').split('/')[0] != 'official-negative-pool':
        raise SystemExit(f'unsupported official negative pool: {path}')
    cases = [str(row.get('case') or '') for row in data.get('selected') or []]
    if not cases or len(cases) != len(set(cases)):
        raise SystemExit(f'official negative pool has empty or duplicate cases: {path}')
    if cases != [str(case) for case in data.get('selected_cases') or []]:
        raise SystemExit(f'official negative pool case lists disagree: {path}')
    invalid = [row for row in data.get('selected') or []
               if str(row.get('validity') or '').lower() == 'invalid']
    if len(invalid) != len(cases):
        raise SystemExit(f'official negative pool contains non-invalid labels: {path}')
    return data


def _select_negatives(rows: list[dict], *, target: int, max_share: float,
                      rng: random.Random) -> tuple[list[dict], list[dict], int]:
    by_project: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        project = str(row.get('project')
                      or str(row.get('case') or '').split('__')[0]
                      or 'unknown')
        by_project[project].append(row)
    alloc, shortfall = _alloc_capped(
        {name: len(items) for name, items in by_project.items()},
        max(0, target), max_share=max_share)
    selected: list[dict] = []
    strata: list[dict] = []
    for project in sorted(by_project):
        items = by_project[project]
        count = min(alloc.get(project, 0), len(items))
        if count:
            selected.extend(_draw(items, count, rng))
        strata.append({'project': project, 'population': len(items),
                       'selected': count})
    rng.shuffle(selected)
    return selected, strata, shortfall


def main(argv=None) -> dict:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--target-positives', type=int, default=DEFAULT_TARGET)
    parser.add_argument('--target-negatives', type=int,
                        default=DEFAULT_TARGET_NEGATIVES)
    parser.add_argument('--max-project-share', type=float,
                        default=MAX_PROJECT_SHARE)
    parser.add_argument('--seed', type=int, default=DEFAULT_SEED)
    parser.add_argument('--ground-truth', default=str(GT))
    parser.add_argument('--output', default=str(OUT_JSON))
    parser.add_argument('--markdown', default=str(OUT_MD))
    parser.add_argument('--exclude-dev', default=str(EXCLUDE_DEV),
                        help='dev anchor file; its case ids are excluded from '
                             'the eval sampling frame to keep dev/eval disjoint')
    parser.add_argument('--official-negative-pool', default=None,
                        help='frozen official-judge negative pool; replaces '
                             'the judge_ground_truth negative frame')
    args = parser.parse_args(argv)

    gt = json.loads(Path(args.ground_truth).read_text())
    positives = [c for c in gt['cases'] if c.get('validity') in VALID_STATES]
    excluded = frozen_dev_case_ids()
    exclude_dev_path = Path(args.exclude_dev)
    if exclude_dev_path.is_file():
        excluded |= {str(r.get('case')) for r in
                     json.loads(exclude_dev_path.read_text()).get('cases', [])
                     if r.get('case')}
    positives = [c for c in positives if c.get('case') not in excluded]
    gt_cases = {str(c.get('case')) for c in gt['cases']}

    negative_source = str(GT)
    negative_source_sha256 = _sha256(Path(args.ground_truth))
    negative_label_rule = 'judge_ground_truth.json validity == invalid'
    negative_pool_policy = None
    negative_pool_agreement = None
    if args.official_negative_pool:
        pool_path = Path(args.official_negative_pool)
        pool = official_negative_pool(pool_path)
        negative_source = str(pool_path)
        negative_source_sha256 = _sha256(pool_path)
        negative_label_rule = pool.get('label_rule')
        negative_pool_policy = pool.get('policy')
        negative_pool_agreement = pool.get('label_agreement')
        negatives = list(pool.get('selected') or [])
        negative_population = len(pool.get('candidates') or [])
    else:
        negatives = [c for c in gt['cases']
                     if c.get('validity') == 'invalid']
        negative_population = len(negatives)
    negatives = [c for c in negatives
                 if str(c.get('case')) not in excluded
                 and (not args.official_negative_pool
                      or str(c.get('case')) not in gt_cases)]

    by_project: dict[str, list[dict]] = defaultdict(list)
    for c in positives:
        by_project[c.get('project') or 'unknown'].append(c)

    target = args.target_positive = min(args.target_positives, len(positives))
    alloc = _alloc_proportional({k: len(v) for k, v in by_project.items()}, target)

    rng = random.Random(args.seed)
    sample = []
    strata_meta = []
    for project, rows in sorted(by_project.items()):
        count = alloc.get(project, 0)
        if count <= 0:
            continue
        by_sev: dict[str, list[dict]] = defaultdict(list)
        for c in rows:
            sev = c.get('severity') or 'unknown'
            if sev not in SEVERITY_ORDER:
                sev = 'unknown'
            by_sev[sev].append(c)
        sev_alloc = _alloc_proportional(
            {k: len(v) for k, v in by_sev.items()}, count, minimum=0)
        sev_alloc = {k: v for k, v in sev_alloc.items() if v > 0}
        project_sample = []
        for sev, sev_rows in sorted(by_sev.items(),
                                    key=lambda kv: SEVERITY_ORDER.index(kv[0])
                                    if kv[0] in SEVERITY_ORDER else 999):
            n = min(sev_alloc.get(sev, 0), len(sev_rows))
            if n:
                project_sample.extend(_draw(sev_rows, n, rng))
        sample.extend(project_sample)
        strata_meta.append({
            'project': project,
            'population': len(rows),
            'selected': len(project_sample),
            'severity': {k: len(v) for k, v in by_sev.items()},
        })

    rng.shuffle(sample)
    sample_ids = [c['case'] for c in sample]

    negative_sample, negative_strata, negative_shortfall = _select_negatives(
        negatives, target=args.target_negatives,
        max_share=args.max_project_share, rng=rng)
    negative_ids = [c['case'] for c in negative_sample]

    out = {
        'schema_version': 'mainline-sample/1',
        'seed': args.seed,
        'source': 'judge_ground_truth.json',
        'strategy': 'stratified by project, severity-proportional inside project',
        'target_positives': target,
        'selected_positives': len(sample_ids),
        'positive_cases': sample_ids,
        'target_negatives': max(0, args.target_negatives),
        'selected_negatives': len(negative_ids),
        'negative_cases': negative_ids,
        'negative_count': len(negative_ids),
        'negative_shortfall': negative_shortfall,
        'negative_population': negative_population,
        'negative_report_ready': sum(
            1 for row in negative_sample if row.get('report_ready')),
        'negative_slice_ready': sum(
            1 for row in negative_sample if row.get('slice_ready')),
        'negative_source': negative_source,
        'negative_source_sha256': negative_source_sha256,
        'negative_label_rule': negative_label_rule,
        'negative_pool_policy': negative_pool_policy,
        'negative_pool_label_agreement': negative_pool_agreement,
        'negative_max_project_share': args.max_project_share,
        'negative_strata': negative_strata,
        'strata': strata_meta,
        'population': {
            'positives': len(positives),
            'negatives': len(negatives),
            'projects': len(by_project),
            'dev_excluded': len(excluded),
        },
        'dev_exclusion': {
            'sources': [str(FROZEN_DEV252), str(FROZEN_DEV24),
                        str(exclude_dev_path)]
                       + [str(path) for path in DEV_NEGATIVE_FILES],
            'excluded_cases': len(excluded),
        },
    }
    out_path = Path(args.output)
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2) + '\n')

    md = f"""# 主口径分层抽样

- 来源：`judge_ground_truth.json` 全量判例，seed `{args.seed}`。
- 策略：20 个项目分层，项目内按 severity 比例分配；总 positive 目标 `{target}`。
- 抽样总体已排除冻结 dev252/dev24 与开发负例，共 `{len(excluded)}` 例，保证 dev/eval 不相交。
- negative 来源：`{negative_source}`，标签规则 `{negative_label_rule}`。
- negative 总体：排除 dev/GT 后的 `{negative_population}` 例。

| 项目 | 总体 | 抽中 | severity 分布 |
| --- | ---: | ---: | --- |
"""
    for s in strata_meta:
        sev = ', '.join(f'{k}={v}' for k, v in sorted(s['severity'].items()))
        md += f"| {s['project']} | {s['population']} | {s['selected']} | {sev} |\n"
    md += '\n## 负样本\n\n'
    md += (f"- 目标 `{args.target_negatives}`，可选总体 `{len(negatives)}`，"
           f"实际选中 `{len(negative_ids)}`，缺口 `{negative_shortfall}`。\n")
    md += (f"- 按项目分层，单项目上限 "
           f"`{args.max_project_share:.0%}`。\n\n")
    md += (f"- 运行就绪：报告 `{sum(1 for row in negative_sample if row.get('report_ready'))}`，"
           f"源码切片 `{sum(1 for row in negative_sample if row.get('slice_ready'))}`。\n\n")
    md += '| 项目 | 总体 | 抽中 |\n| --- | ---: | ---: |\n'
    for row in negative_strata:
        md += (f"| {row['project']} | {row['population']} | "
               f"{row['selected']} |\n")
    md += f"\n共选中 positive `{len(sample_ids)}`，negative `{len(negative_ids)}`。\n"
    Path(args.markdown).write_text(md)

    print(
        f'分层抽样完成: positive {len(sample_ids)}/{len(positives)}，'
        f'negative {len(negative_ids)}/{len(negatives)} '
        f'(target {args.target_negatives}, shortfall {negative_shortfall})')
    print(f'输出: {out_path}')
    return out


if __name__ == '__main__':
    main()
