#!/usr/bin/env python3
"""Freeze a stratified mainline positive subset without case outcomes."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
STAGE3 = HERE.parents[1]
if str(STAGE3) not in sys.path:
    sys.path.insert(0, str(STAGE3))
from lib import path_config
PARENT = HERE / 'mainline_sample.json'
GT = HERE / 'judge_ground_truth.json'
DEFAULT_OUT = HERE / 'mainline_sample_150.json'
DEFAULT_MD = HERE / 'mainline_sample_150.md'
DEFAULT_SALT = 'mainline/1.7.15/150'
NEGATIVE_FLATTEN_SUMMARY = path_config.negative_flatten_summary()


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def _allocate(total: int, weights: dict[str, int]) -> dict[str, int]:
    items = sorted((key, int(value)) for key, value in weights.items()
                   if int(value) > 0)
    weight_sum = sum(value for _, value in items)
    if not items or weight_sum <= 0:
        return {}
    exact = {key: total * value / weight_sum for key, value in items}
    result = {key: int(exact[key]) for key, _ in items}
    remainder = total - sum(result.values())
    order = sorted(items, key=lambda row: (-(exact[row[0]] - result[row[0]]),
                                           row[0]))
    for key, _ in order[:remainder]:
        result[key] += 1
    return result


def _subset_negatives(parent: dict, target: int, salt: str) -> tuple[list[str], int]:
    cases = [str(case) for case in parent.get('negative_cases') or []]
    if target < 1 or target > len(cases):
        raise SystemExit(f'negative target outside frozen negatives: {target}')
    by_project: dict[str, list[str]] = defaultdict(list)
    for case in cases:
        by_project[case.split('__')[0]].append(case)
    alloc = _allocate(target, {key: len(value)
                               for key, value in by_project.items()})
    selected: list[str] = []
    for project in sorted(by_project):
        ordered = sorted(
            by_project[project],
            key=lambda case: _sha256_text(f'{salt}:negative:{case}'))
        selected.extend(ordered[:alloc.get(project, 0)])
    selected = sorted(selected, key=lambda case: _sha256_text(
        f'{salt}:negative:{case}'))
    ready = 0
    if NEGATIVE_FLATTEN_SUMMARY.is_file():
        ready_cases = {
            str(row.get('case')) for row in json.loads(
                NEGATIVE_FLATTEN_SUMMARY.read_text()).get('rows') or []}
        ready = sum(case in ready_cases for case in selected)
    return selected, ready


def build(*, parent_path: Path, gt_path: Path, target: int, salt: str,
          negative_target: int | None = None) -> dict:
    parent = json.loads(Path(parent_path).read_text())
    ground_truth = json.loads(Path(gt_path).read_text())
    meta = {str(row.get('case')): row for row in ground_truth.get('cases', [])}
    parent_cases = [str(case) for case in parent.get('positive_cases', [])]
    if target < 1 or target > len(parent_cases):
        raise SystemExit(f'target outside frozen positives: {target}')

    by_project: dict[str, list[str]] = defaultdict(list)
    for case in parent_cases:
        row = meta.get(case, {})
        project = str(row.get('project') or case.split('__')[0])
        by_project[project].append(case)

    project_alloc = _allocate(target, {key: len(value)
                                       for key, value in by_project.items()})
    selected: list[str] = []
    strata: list[dict] = []
    for project in sorted(by_project):
        by_severity: dict[str, list[str]] = defaultdict(list)
        for case in by_project[project]:
            row = meta.get(case, {})
            severity = str(row.get('severity') or 'unknown')
            by_severity[severity].append(case)
        severity_alloc = _allocate(
            project_alloc.get(project, 0),
            {key: len(value) for key, value in by_severity.items()})
        severity_meta = {}
        for severity in sorted(by_severity):
            count = severity_alloc.get(severity, 0)
            ordered = sorted(
                by_severity[severity],
                key=lambda case: _sha256_text(f'{salt}:{case}'))
            selected.extend(ordered[:count])
            if count:
                severity_meta[severity] = count
        strata.append({
            'project': project,
            'population': len(by_project[project]),
            'selected': sum(severity_meta.values()),
            'severity': severity_meta,
        })
    selected = sorted(selected, key=lambda case: _sha256_text(f'{salt}:{case}'))
    if len(selected) != target or len(set(selected)) != target:
        raise SystemExit('deterministic subset allocation failed')

    negative_cases = [str(case) for case in parent.get('negative_cases') or []]
    negative_slice_ready = int(parent.get('negative_slice_ready') or 0)
    negative_strata = parent.get('negative_strata')
    if negative_target is not None:
        negative_cases, negative_slice_ready = _subset_negatives(
            parent, negative_target, salt)
        negative_strata = []
        by_project: dict[str, int] = defaultdict(int)
        for case in negative_cases:
            by_project[case.split('__')[0]] += 1
        negative_strata = [
            {'project': project, 'selected': count}
            for project, count in sorted(by_project.items())]

    out = {
        'schema_version': parent.get('schema_version', 'mainline-sample/1'),
        'seed': parent.get('seed'),
        'subset_salt': salt,
        'source': parent.get('source'),
        'strategy': str(parent.get('strategy') or '')
                    + '; deterministic stratified subset of the frozen sample',
        'target_positives': target,
        'selected_positives': len(selected),
        'positive_cases': selected,
        'target_negatives': negative_target or parent.get('target_negatives'),
        'selected_negatives': len(negative_cases),
        'negative_cases': negative_cases,
        'negative_count': len(negative_cases),
        'negative_shortfall': max(
            0, int(negative_target or parent.get('target_negatives') or 0)
            - len(negative_cases)),
        'negative_population': parent.get('negative_population'),
        'negative_report_ready': parent.get('negative_report_ready'),
        'negative_slice_ready': negative_slice_ready,
        'negative_source': parent.get('negative_source'),
        'negative_source_sha256': parent.get('negative_source_sha256'),
        'negative_label_rule': parent.get('negative_label_rule'),
        'negative_pool_policy': parent.get('negative_pool_policy'),
        'negative_pool_label_agreement': parent.get(
            'negative_pool_label_agreement'),
        'negative_max_project_share': parent.get('negative_max_project_share'),
        'negative_strata': negative_strata,
        'strata': strata,
        'population': parent.get('population'),
        'dev_exclusion': parent.get('dev_exclusion'),
        'negative_slice_source': parent.get('negative_slice_source'),
        'negative_slice_source_sha256': parent.get(
            'negative_slice_source_sha256'),
        'negative_slice_artifacts_sha256': parent.get(
            'negative_slice_artifacts_sha256'),
        'parent_sample': str(Path(parent_path).relative_to(ROOT)),
        'parent_sample_sha256': hashlib.sha256(
            Path(parent_path).read_bytes()).hexdigest(),
        'parent_positive_count': len(parent_cases),
    }
    return out


def markdown(payload: dict) -> str:
    lines = [
        '# 主口径冻结子集', '',
        f"- parent: `{payload['parent_sample']}` / "
        f"`{payload['parent_sample_sha256'][:12]}`",
        f"- salt: `{payload['subset_salt']}`",
        f"- seed: `{payload['seed']}`",
        f"- positives: `{payload['selected_positives']}` / "
        f"`{payload['parent_positive_count']}`",
        f"- negatives: `{payload['selected_negatives']}`", '',
        '| project | parent | selected | severity |',
        '| --- | ---: | ---: | --- |',
    ]
    for row in payload['strata']:
        severity = ', '.join(f'{key}={value}' for key, value
                             in sorted(row['severity'].items()))
        lines.append(f"| {row['project']} | {row['population']} | "
                     f"{row['selected']} | {severity} |")
    return '\n'.join(lines) + '\n'


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--parent', type=Path, default=PARENT)
    parser.add_argument('--ground-truth', type=Path, default=GT)
    parser.add_argument('--target-positives', type=int, default=150)
    parser.add_argument('--target-negatives', type=int, default=0)
    parser.add_argument('--salt', default=DEFAULT_SALT)
    parser.add_argument('--output', type=Path, default=DEFAULT_OUT)
    parser.add_argument('--markdown', type=Path, default=DEFAULT_MD)
    args = parser.parse_args(argv)
    payload = build(parent_path=args.parent, gt_path=args.ground_truth,
                    target=args.target_positives, salt=args.salt,
                    negative_target=(args.target_negatives or None))
    args.output.write_text(json.dumps(payload, ensure_ascii=False,
                                      indent=2) + '\n')
    args.markdown.write_text(markdown(payload))
    print(json.dumps({
        'output': str(args.output),
        'positives': payload['selected_positives'],
        'negatives': payload['selected_negatives'],
        'salt': payload['subset_salt'],
    }, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
