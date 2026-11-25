#!/usr/bin/env python3
"""Build a fresh official-judge negative pool from raw Code4rena findings.

The existing ``judge_ground_truth.json`` and all frozen dev negative files are
excluded.  Validity is the latest validity evaluation for the same finding,
which matches all 1308 overlapping rows in the current ground truth.
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
STAGE3 = HERE.parents[1]
ROOT = STAGE3.parents[1]
for path in (STAGE3, HERE):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))
from lib import path_config

FINDINGS = path_config.c4_output_root()
REPORTS = path_config.code4rena_reports_root()
GROUND_TRUTH = HERE / 'judge_ground_truth.json'
DEFAULT_OUT = HERE / 'official_negative_pool_20261121.json'
DEFAULT_MD = HERE / 'official_negative_pool_20261121.md'
DEFAULT_TARGET = 60
DEFAULT_MAX_SHARE = 0.25
DEFAULT_SEED = 20261121


def finding_uids(row: dict) -> list[str]:
    evaluations = (row.get('raw') or {}).get('evaluations') or []
    return sorted({str(item.get('findingUid')) for item in evaluations
                   if item.get('findingUid')})


def latest_validity(row: dict) -> str:
    evaluations = (row.get('raw') or {}).get('evaluations') or []
    values = [item for item in evaluations
              if item.get('type') == 'validity' and item.get('findingUid')]
    if not values:
        return str(row.get('validity') or '').lower()
    values.sort(key=lambda item: item.get('createdAt') or '')
    return str(values[-1].get('value') or '').lower()


def project_for_dir(dirname: str, known_projects: set[str]) -> str:
    if dirname in known_projects:
        return dirname
    for project in sorted(known_projects):
        if project.endswith('_' + dirname):
            return project
    for path in sorted(REPORTS.iterdir()):
        if path.is_dir() and path.name.endswith('_' + dirname):
            return path.name.replace(' ', '_')
    return dirname.replace(' ', '_')


def runtime_index(findings_root: Path) -> tuple[set[tuple[str, str]], set[tuple[str, str]]]:
    reports: set[tuple[str, str]] = set()
    slices: set[tuple[str, str]] = set()
    for path in findings_root.glob('*/*/reports/*.md'):
        reports.add((path.parents[2].name, path.stem))
    for path in findings_root.glob('*/*/flatten_sorted/*__*.sorted.sol'):
        number = path.name.split('__', 1)[0]
        slices.add((path.parents[2].name, number))
    return reports, slices


def annotate_runtime(row: dict, reports: set[tuple[str, str]],
                     slices: set[tuple[str, str]]) -> dict:
    project_dir = Path(row['source']).parent.parent.name
    number = str(row.get('submission_number') or '')
    key = (project_dir, number)
    row['report_ready'] = key in reports
    row['slice_ready'] = key in slices
    return row


def collect(*, findings_root: Path = FINDINGS,
            ground_truth: Path = GROUND_TRUTH,
            known_projects: set[str] | None = None) -> tuple[dict[str, dict], dict]:
    gt = json.loads(ground_truth.read_text())
    gt_rows = gt.get('cases') or []
    if known_projects is None:
        known_projects = {str(row.get('project'))
                          for row in gt_rows if row.get('project')}

    records: dict[str, dict] = {}
    stats: Counter[str] = Counter()
    for path in sorted(findings_root.glob('*/????????_??????/findings.json')):
        try:
            rows = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError):
            stats['unreadable_files'] += 1
            continue
        if not isinstance(rows, list):
            continue
        project = project_for_dir(path.parent.parent.name, known_projects)
        stamp = path.parent.name
        try:
            source = str(path.relative_to(ROOT))
        except ValueError:
            source = str(path)
        for row in rows:
            if not isinstance(row, dict):
                continue
            submission_uid = str(row.get('uid') or '')
            ids = finding_uids(row)
            if not submission_uid or not ids:
                stats['missing_ids'] += 1
                continue
            validity = latest_validity(row)
            for finding_uid in ids:
                case = f'{project}__{finding_uid}__{submission_uid}'
                record = {
                    'case': case,
                    'project': project,
                    'validity': validity,
                    'submission_number': str(row.get('submission_index')
                                             or row.get('number') or ''),
                    'severity': row.get('severity'),
                    'title': row.get('title'),
                    'source': source,
                    'snapshot': stamp,
                }
                if case not in records or stamp > records[case]['snapshot']:
                    records[case] = record
                stats['rows'] += 1

    by_case = {str(row.get('case')): str(row.get('validity'))
               for row in gt_rows}
    agreement = total = 0
    for case, record in records.items():
        if case not in by_case or not record['validity']:
            continue
        total += 1
        agreement += record['validity'] == by_case[case]
    stats['ground_truth_overlap'] = total
    stats['label_agreement'] = agreement
    return records, dict(stats)


def build(*, target: int = DEFAULT_TARGET,
          max_share: float = DEFAULT_MAX_SHARE,
          seed: int = DEFAULT_SEED,
          findings_root: Path = FINDINGS,
          ground_truth: Path = GROUND_TRUTH) -> dict:
    from lib.mainline_protocol import current
    from sample_mainline import _alloc_capped, frozen_dev_case_ids

    records, stats = collect(findings_root=findings_root,
                             ground_truth=ground_truth)
    gt = json.loads(ground_truth.read_text())
    gt_cases = {str(row.get('case')) for row in gt.get('cases') or []}
    dev_cases = frozen_dev_case_ids()
    invalid = {case: row for case, row in records.items()
               if row['validity'] == 'invalid'}
    candidates = {case: row for case, row in invalid.items()
                  if case not in gt_cases and case not in dev_cases}
    reports, slices = runtime_index(findings_root)
    for row in candidates.values():
        annotate_runtime(row, reports, slices)
    stats['candidates_report_ready'] = sum(
        1 for row in candidates.values() if row['report_ready'])
    stats['candidates_slice_ready'] = sum(
        1 for row in candidates.values() if row['slice_ready'])

    by_project: dict[str, list[dict]] = defaultdict(list)
    for row in candidates.values():
        by_project[row['project']].append(row)
    alloc, shortfall = _alloc_capped(
        {name: len(rows) for name, rows in by_project.items()},
        max(0, target), max_share=max_share)
    rng = random.Random(seed)
    selected: list[dict] = []
    strata: list[dict] = []
    for project in sorted(by_project):
        rows = by_project[project]
        count = min(alloc.get(project, 0), len(rows))
        selected.extend(rng.sample(rows, count) if count else [])
        strata.append({'project': project, 'population': len(rows),
                       'selected': count})
    rng.shuffle(selected)
    stats['selected_report_ready'] = sum(
        1 for row in selected if row['report_ready'])
    stats['selected_slice_ready'] = sum(
        1 for row in selected if row['slice_ready'])

    return {
        'schema_version': 'official-negative-pool/1',
        'protocol': current(),
        'seed': seed,
        'policy': ('Official final invalid findings from raw Code4rena data; '
                   'excludes judge_ground_truth and every frozen dev case.'),
        'label_rule': 'latest validity evaluation for the same finding uid',
        'label_agreement': {
            'matched_ground_truth_rows': stats['ground_truth_overlap'],
            'agreements': stats['label_agreement'],
        },
        'source_stats': stats,
        'counts': {
            'unique_findings': len(records),
            'official_invalid': len(invalid),
            'candidates_outside_dev': len(candidates),
            'target': max(0, target),
            'selected': len(selected),
            'shortfall': shortfall,
            'projects': len(by_project),
        },
        'max_project_share': max_share,
        'strata': strata,
        'selected_cases': [row['case'] for row in selected],
        'selected': selected,
        'candidates': sorted(candidates.values(), key=lambda row: row['case']),
    }


def markdown(report: dict) -> str:
    counts = report['counts']
    agreement = report['label_agreement']
    lines = [
        '# Official negative pool', '',
        f"- protocol: `{report['protocol']['version']}`",
        f"- label rule: `{report['label_rule']}`",
        f"- label agreement: {agreement['agreements']}/"
        f"{agreement['matched_ground_truth_rows']}", '',
        '| item | value |', '| --- | ---: |',
        f"| unique findings | {counts['unique_findings']} |",
        f"| official invalid | {counts['official_invalid']} |",
        f"| candidates outside dev | {counts['candidates_outside_dev']} |",
        f"| selected | {counts['selected']} / {counts['target']} |",
        f"| shortfall | {counts['shortfall']} |",
        f"| projects | {counts['projects']} |", '',
        '| runtime readiness | candidates | selected |',
        '| --- | ---: | ---: |',
        f"| report ready | {report['source_stats']['candidates_report_ready']} | "
        f"{report['source_stats']['selected_report_ready']} |",
        f"| source slice ready | {report['source_stats']['candidates_slice_ready']} | "
        f"{report['source_stats']['selected_slice_ready']} |", '',
        '| project | candidates | selected |', '| --- | ---: | ---: |',
    ]
    for row in report['strata']:
        lines.append(f"| {row['project']} | {row['population']} | "
                     f"{row['selected']} |")
    return '\n'.join(lines) + '\n'


def main(argv=None) -> dict:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--target', type=int, default=DEFAULT_TARGET)
    parser.add_argument('--max-project-share', type=float,
                        default=DEFAULT_MAX_SHARE)
    parser.add_argument('--seed', type=int, default=DEFAULT_SEED)
    parser.add_argument('--findings-root', type=Path, default=FINDINGS)
    parser.add_argument('--ground-truth', type=Path, default=GROUND_TRUTH)
    parser.add_argument('--output', type=Path, default=DEFAULT_OUT)
    parser.add_argument('--markdown', type=Path, default=DEFAULT_MD)
    args = parser.parse_args(argv)
    report = build(target=args.target, max_share=args.max_project_share,
                   seed=args.seed, findings_root=args.findings_root,
                   ground_truth=args.ground_truth)
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    args.markdown.write_text(markdown(report))
    print(json.dumps(report['counts'], ensure_ascii=False, indent=2))
    return report


if __name__ == '__main__':
    main()
