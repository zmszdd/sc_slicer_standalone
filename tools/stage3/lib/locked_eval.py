#!/usr/bin/env python3
"""Build and check the locked evaluation contract for the mainline.

This module does not manufacture metrics.  It records whether the current
protocol, sample, provenance gate and metric denominator are strong enough to
refresh the authoritative four metrics.  Historical or diagnostic results stay
visible, but they can never set ``ready=true``.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

STAGE3_DIR = Path(__file__).resolve().parents[1]
ROOT = STAGE3_DIR.parents[1]
METRICS_DIR = STAGE3_DIR / 'evaluation' / 'metrics'
DEFAULT_SAMPLE = METRICS_DIR / 'mainline_sample_mini.json'
DEFAULT_DENOMINATOR = METRICS_DIR / 'current_denominator.json'
DEFAULT_PROVENANCE = METRICS_DIR / 'provenance_gate.json'
DEFAULT_GROUND_TRUTH = METRICS_DIR / 'judge_ground_truth.json'
DEFAULT_CONSISTENCY_METRICS = METRICS_DIR / 'mainline_metrics.json'
DEFAULT_JSON = METRICS_DIR / 'locked_eval_contract.json'
DEFAULT_MD = METRICS_DIR / 'locked_eval_contract.md'

SCHEMA_VERSION = 'stage3-locked-eval/1'
MIN_POSITIVES = 30
MIN_NEGATIVES = 8
RECOMMENDED_POSITIVES = 40
RECOMMENDED_NEGATIVES = 40
MIN_PROJECTS = 5
MIN_NEGATIVE_PROJECTS = 5
MAX_NEGATIVE_PROJECT_SHARE = 0.25
MIN_NEGATIVE_SLICE_READY = MIN_NEGATIVES
MIN_PUBLISHABLE_POSITIVES = 30
MIN_PUBLISHABLE_POSITIVE_COVERAGE = 0.80
PUBLICATION_MAX_FPR_UPPER_95 = 0.12


def fpr_upper_95(eligible_negative: int) -> float:
    """Clopper-Pearson one-sided 95% FPR upper bound when FP_vuln=0."""
    if eligible_negative <= 0:
        return 1.0
    return 1.0 - 0.05 ** (1.0 / eligible_negative)


def _min_negatives_for_fpr_upper(target: float) -> int:
    if not 0 < target < 1:
        raise ValueError('target FPR upper bound must be between 0 and 1')
    return math.ceil(math.log(0.05) / math.log(1.0 - target))


MIN_PUBLISHABLE_NEGATIVES = _min_negatives_for_fpr_upper(
    PUBLICATION_MAX_FPR_UPPER_95)


def _load(path: Path) -> dict:
    try:
        payload = json.loads(Path(path).read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _sha256(path: Path) -> str | None:
    try:
        return hashlib.sha256(Path(path).read_bytes()).hexdigest()
    except OSError:
        return None


def _dataset_counts(denominator: dict) -> dict:
    out = {}
    for name in ('dev252', 'dev24', 'negative5', 'mainline'):
        row = denominator.get(name)
        if not isinstance(row, dict):
            datasets = denominator.get('datasets') or {}
            row = (datasets.get(name) if isinstance(datasets, dict) else None)
        row = row if isinstance(row, dict) else {}
        counts = (row.get('case_counts') or row.get('counts') or {})
        if name == 'mainline':
            eligible = (int(counts.get('eligible_positive') or 0)
                        + int(counts.get('eligible_negative') or 0))
            out[name] = {
                'eligible_current': eligible,
                'eligible_positive': int(
                    counts.get('eligible_positive') or 0),
                'eligible_negative': int(
                    counts.get('eligible_negative') or 0),
                'excluded_retry': int(counts.get('excluded_retry') or 0),
                'unresolved': int(counts.get('unresolved') or 0),
            }
            continue
        else:
            eligible = int(counts.get('eligible_current') or 0)
        out[name] = {
            'eligible_current': eligible,
            'excluded_retry': int(counts.get('excluded_retry') or 0),
            'unresolved': int(counts.get('unresolved') or 0),
        }
    return out


def build(*, sample_path: Path | None = None,
          denominator_path: Path | None = None,
          provenance_path: Path | None = None,
          ground_truth_path: Path | None = None,
          label_review_path: Path | None = None,
          consistency_metrics_path: Path | None = None,
          root: Path | None = None) -> dict:
    """Return the current locked-evaluation readiness contract."""
    root = Path(root) if root is not None else ROOT
    sample_path = Path(sample_path) if sample_path else DEFAULT_SAMPLE
    denominator_path = (Path(denominator_path) if denominator_path
                        else DEFAULT_DENOMINATOR)
    provenance_path = (Path(provenance_path) if provenance_path
                       else DEFAULT_PROVENANCE)
    ground_truth_path = (Path(ground_truth_path) if ground_truth_path
                         else DEFAULT_GROUND_TRUTH)
    consistency_metrics_path = (
        Path(consistency_metrics_path) if consistency_metrics_path
        else DEFAULT_CONSISTENCY_METRICS)
    label_review_path = (Path(label_review_path) if label_review_path
                         else (Path(root) / 'tools' / 'stage3' / 'evaluation'
                               / 'metrics' / 'label_review_gate.json'))

    from lib import mainline_protocol

    protocol = mainline_protocol.current()
    sample = _load(sample_path)
    denominator = _load(denominator_path)
    provenance = _load(provenance_path)
    label_review = _load(label_review_path)

    positives = list(sample.get('positive_cases') or [])
    negatives = list(sample.get('negative_cases') or [])
    negative_strata = [
        row for row in (sample.get('negative_strata') or [])
        if isinstance(row, dict)]
    projects = {
        str(row.get('project'))
        for row in (sample.get('strata') or [])
        if isinstance(row, dict) and row.get('project')
    }
    negative_project_counts: dict[str, int] = {}
    if negative_strata:
        for row in negative_strata:
            selected = int(row.get('selected') or 0)
            project = str(row.get('project') or '')
            if project and selected:
                negative_project_counts[project] = (
                    negative_project_counts.get(project, 0) + selected)
    else:
        for case in negatives:
            project = str(case).split('__')[0] or 'unknown'
            negative_project_counts[project] = (
                negative_project_counts.get(project, 0) + 1)
    negative_projects = len(negative_project_counts)
    negative_slice_ready = sample.get('negative_slice_ready')
    max_negative_share = (
        max(negative_project_counts.values()) / len(negatives)
        if negatives else 0.0)
    counts = _dataset_counts(denominator)
    refresh_ready = bool(denominator.get('refresh_ready'))
    refresh_allowed = bool(provenance.get('refresh_allowed'))
    mainline_counts = counts.get('mainline') or {}
    eligible_positive = int(mainline_counts.get('eligible_positive') or 0)
    eligible_negative = int(mainline_counts.get('eligible_negative') or 0)
    positive_coverage = (
        eligible_positive / len(positives) if positives else 0.0)
    negative_coverage = (
        eligible_negative / len(negatives) if negatives else 0.0)
    negative_fpr_upper = fpr_upper_95(eligible_negative)
    negative_coverage_floor = (
        MIN_PUBLISHABLE_NEGATIVES / len(negatives) if negatives else 1.0)
    label_review_cases = sorted({
        str(row.get('case')) for row in (label_review.get('cases') or [])
        if isinstance(row, dict)
        and row.get('status') == 'label_review_required'
        and row.get('case')
    })

    blockers = []
    if len(positives) < MIN_POSITIVES:
        blockers.append(
            f'positive sample below floor: {len(positives)} < {MIN_POSITIVES}')
    if len(negatives) < MIN_NEGATIVES:
        blockers.append(
            f'negative sample below floor: {len(negatives)} < {MIN_NEGATIVES}')
    if len(projects) < MIN_PROJECTS:
        blockers.append(
            f'project coverage below floor: {len(projects)} < {MIN_PROJECTS}')
    if negative_projects < MIN_NEGATIVE_PROJECTS:
        blockers.append(
            f'negative project coverage below floor: '
            f'{negative_projects} < {MIN_NEGATIVE_PROJECTS}')
    if max_negative_share > MAX_NEGATIVE_PROJECT_SHARE + 1e-9:
        blockers.append(
            f'negative project concentration above cap: '
            f'{max_negative_share:.2%} > {MAX_NEGATIVE_PROJECT_SHARE:.0%}')
    if negative_slice_ready is not None:
        ready = int(negative_slice_ready)
        if ready < MIN_NEGATIVE_SLICE_READY:
            blockers.append(
                f'negative source slices below floor: '
                f'{ready} < {MIN_NEGATIVE_SLICE_READY}')
    if not refresh_ready:
        blockers.append('current denominator is not refresh_ready')
    if not refresh_allowed:
        blockers.append('provenance gate does not allow a metric refresh')
    eligible = sum(row['eligible_current'] for row in counts.values())
    if eligible <= 0:
        blockers.append('no current-protocol eligible claims in denominator')

    publication_blockers = list(blockers)
    if eligible_positive < MIN_PUBLISHABLE_POSITIVES:
        publication_blockers.append(
            'eligible positives below publication floor: '
            f'{eligible_positive} < {MIN_PUBLISHABLE_POSITIVES}')
    if eligible_negative < MIN_PUBLISHABLE_NEGATIVES:
        publication_blockers.append(
            'eligible negatives below publication floor: '
            f'{eligible_negative} < {MIN_PUBLISHABLE_NEGATIVES} '
            f'(FPR upper95 {negative_fpr_upper:.1%} > '
            f'{PUBLICATION_MAX_FPR_UPPER_95:.0%})')
    if positive_coverage < MIN_PUBLISHABLE_POSITIVE_COVERAGE - 1e-9:
        publication_blockers.append(
            'positive evaluated coverage below publication floor: '
            f'{eligible_positive}/{len(positives)} = {positive_coverage:.1%} '
            f'< {MIN_PUBLISHABLE_POSITIVE_COVERAGE:.0%}')
    if label_review_cases:
        publication_blockers.append(
            f'label review required for {len(label_review_cases)} negative '
            'case(s): ' + ', '.join(label_review_cases[:5])
            + (' ...' if len(label_review_cases) > 5 else ''))
    publishable = not publication_blockers
    publication_status = ('publishable' if publishable else
                          'coverage-limited' if not blockers else
                          'blocked')
    consistency_gate = _load(consistency_metrics_path).get(
        'consistency_gate') or {}
    primary_publishable = bool(
        consistency_gate.get('publishable', publishable))
    primary_status = str(
        consistency_gate.get('publication_status', publication_status))
    primary_blockers = list(
        consistency_gate.get('publication_blockers') or publication_blockers)

    return {
        'schema_version': SCHEMA_VERSION,
        'protocol': protocol,
        'source_hashes': {
            'sample': _sha256(sample_path),
            'denominator': _sha256(denominator_path),
            'provenance': _sha256(provenance_path),
            'ground_truth': _sha256(ground_truth_path),
            'consistency_metrics': _sha256(consistency_metrics_path),
        },
        'sample': {
            'positives': len(positives),
            'negatives': len(negatives),
            'projects': len(projects),
            'recommended_positives': RECOMMENDED_POSITIVES,
            'recommended_negatives': RECOMMENDED_NEGATIVES,
            'negative_projects': negative_projects,
            'max_negative_project_share': round(max_negative_share, 4),
            'negative_slice_ready': negative_slice_ready,
            'negative_shortfall': int(
                sample.get('negative_shortfall') or 0),
        },
        'gates': {
            'refresh_ready': refresh_ready,
            'refresh_allowed': refresh_allowed,
            'eligible_current': eligible,
            'eligible_positive': eligible_positive,
            'eligible_negative': eligible_negative,
            'positive_coverage': round(positive_coverage, 4),
            'negative_coverage': round(negative_coverage, 4),
            'negative_fpr_upper95': round(negative_fpr_upper, 4),
            'publishable': publishable,
            'publication_status': publication_status,
        },
        'coverage': {
            'positives': len(positives),
            'eligible_positive': eligible_positive,
            'positive_coverage': round(positive_coverage, 4),
            'positive_floor': MIN_PUBLISHABLE_POSITIVE_COVERAGE,
            'negative_floor': round(negative_coverage_floor, 4),
            'negatives': len(negatives),
            'eligible_negative': eligible_negative,
            'negative_coverage': round(negative_coverage, 4),
            'eligible_positive_floor': MIN_PUBLISHABLE_POSITIVES,
            'eligible_negative_floor': MIN_PUBLISHABLE_NEGATIVES,
            'negative_fpr_upper95': round(negative_fpr_upper, 4),
            'publication_max_fpr_upper95': PUBLICATION_MAX_FPR_UPPER_95,
        },
        'label_review': {
            'source': str(label_review_path),
            'status': ('label_review_required' if label_review_cases
                       else 'clear'),
            'cases': label_review_cases,
        },
        'primary_gate': {
            'scope': 'source-code/report consistency',
            'source': str(consistency_metrics_path),
            'publishable': primary_publishable,
            'publication_status': primary_status,
            'publication_blockers': primary_blockers,
            'eligible_positive': consistency_gate.get(
                'eligible_positive'),
            'witness_eligible_negative': consistency_gate.get(
                'witness_eligible_negative'),
            'fpr_upper95': consistency_gate.get('fpr_upper95'),
        },
        'denominator': counts,
        'blockers': blockers,
        'publication_blockers': publication_blockers,
        'publishable': publishable,
        'publication_status': publication_status,
        'primary_publishable': primary_publishable,
        'primary_publication_status': primary_status,
        'ready': not blockers,
        'policy': ('ready means the frozen current-protocol denominator and '
                   'provenance may refresh metrics. publishable reports the '
                   'vulnerability-level companion gate; primary_publishable '
                   'reports the consistency main-table gate from '
                   'mainline_metrics.json.'),
    }


def markdown(report: dict) -> str:
    sample = report['sample']
    gates = report['gates']
    lines = [
        '# Locked evaluation contract', '',
        f"- protocol: `{report['protocol']['version']}` / "
        f"`{report['protocol']['sha256'][:12]}`",
        f"- ready: **{str(report['ready']).lower()}**",
        f"- publishable: **{str(report['publishable']).lower()}**",
        f"- publication status: `{report['publication_status']}`", '',
        f"- primary publishable: **{str(report['primary_publishable']).lower()}**",
        f"- primary publication status: `{report['primary_publication_status']}`", '',
        '| item | value | floor | recommended |',
        '| --- | ---: | ---: | ---: |',
        f"| positives | {sample['positives']} | {MIN_POSITIVES} | "
        f"{RECOMMENDED_POSITIVES} |",
        f"| negatives | {sample['negatives']} | {MIN_NEGATIVES} | "
        f"{RECOMMENDED_NEGATIVES} |",
        f"| projects | {sample['projects']} | {MIN_PROJECTS} | - |", '',
        '| negative sampling | value | floor | cap |',
        '| --- | ---: | ---: | ---: |',
        f"| negative projects | {sample['negative_projects']} | "
        f"{MIN_NEGATIVE_PROJECTS} | - |",
        f"| max project share | {sample['max_negative_project_share']:.2%} | "
        f"- | {MAX_NEGATIVE_PROJECT_SHARE:.0%} |",
        f"| negative target shortfall | {sample['negative_shortfall']} | "
        f"- | - |", '',
        f"| negative source slices | {sample['negative_slice_ready']} | "
        f"{MIN_NEGATIVE_SLICE_READY} | - |", '',
        '| gate | value |', '| --- | --- |',
        f"| `refresh_ready` | {str(gates['refresh_ready']).lower()} |",
        f"| `refresh_allowed` | {str(gates['refresh_allowed']).lower()} |",
        f"| `eligible_current` | {gates['eligible_current']} |", '',
        '| coverage | value | floor |', '| --- | ---: | ---: |',
        f"| eligible positives | {report['coverage']['eligible_positive']} | "
        f"{report['coverage']['eligible_positive_floor']} |",
        f"| eligible negatives | {report['coverage']['eligible_negative']} | "
        f"{report['coverage']['eligible_negative_floor']} |",
        f"| positive | {report['coverage']['eligible_positive']}/"
        f"{report['coverage']['positives']} = "
        f"{report['coverage']['positive_coverage']:.1%} | "
        f"{report['coverage']['positive_floor']:.0%} |",
        f"| negative | {report['coverage']['eligible_negative']}/"
        f"{report['coverage']['negatives']} = "
        f"{report['coverage']['negative_coverage']:.1%} | "
        f"{report['coverage']['negative_floor']:.0%} |", '',
        '| publication quality | value | cap |', '| --- | ---: | ---: |',
        f"| negative FPR upper95 | "
        f"{report['coverage']['negative_fpr_upper95']:.1%} | "
        f"{report['coverage']['publication_max_fpr_upper95']:.0%} |",
        f"| label review | {report['label_review']['status']} | - |", '',
        '## Blockers', '',
    ]
    lines += [f'- {item}' for item in report['publication_blockers']]
    if not report['publication_blockers']:
        lines.append('- none')
    return '\n'.join(lines) + '\n'


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sample', type=Path, default=DEFAULT_SAMPLE)
    parser.add_argument('--denominator', type=Path, default=DEFAULT_DENOMINATOR)
    parser.add_argument('--provenance', type=Path, default=DEFAULT_PROVENANCE)
    parser.add_argument('--ground-truth', type=Path, default=DEFAULT_GROUND_TRUTH)
    parser.add_argument('--label-review', type=Path, default=None)
    parser.add_argument('--out-json', type=Path, default=DEFAULT_JSON)
    parser.add_argument('--out-md', type=Path, default=DEFAULT_MD)
    parser.add_argument('--strict', action='store_true',
                        help='exit non-zero when the locked set is not ready')
    args = parser.parse_args(argv)
    report = build(sample_path=args.sample, denominator_path=args.denominator,
                   provenance_path=args.provenance,
                   ground_truth_path=args.ground_truth,
                   label_review_path=args.label_review)
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + '\n',
        encoding='utf-8')
    args.out_md.write_text(markdown(report), encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if args.strict and not report['ready'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
