#!/usr/bin/env python3
"""Frozen experiment contract for development and held-out evaluation.

This module does not run cases.  It binds a metric snapshot to one frozen
manifest, computes the four headline metrics from that snapshot, and records
which cases are reserved for later evaluation.  It also exposes a project-level
cluster bootstrap so clustered findings are not treated as independent.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from metrics_core import (accuracy_rate, cluster_bootstrap_ci, f1,
                          precision_rate, recall, wilson_ci)

DEFAULT_JUDGE = HERE / 'judge_anchored_252.json'
DEFAULT_TRIAGE = HERE / 'repro_failure_triage_252.json'
DEFAULT_GT = HERE / 'judge_ground_truth.json'
DEFAULT_FROZEN = HERE.parent / 'frozen' / 'dev252_20261117.json'
DEFAULT_OUT = HERE / 'dev252_contract_20261117.json'
DEFAULT_SPLIT = HERE.parent / 'frozen' / 'experiment_split_20261117.json'

SCHEMA_VERSION = 'experiment-contract/1'
SPLIT_SCHEMA_VERSION = 'experiment-split/1'
VALID_STATES = {'valid', 'fixed', 'wontfix'}


def _load(path: Path) -> dict:
    return json.loads(path.read_text())


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _project(case: str) -> str:
    return case.split('__', 1)[0]


def _ci(k: int, n: int) -> dict:
    low, high = wilson_ci(k, n)
    return {
        'low': round(low, 4) if low is not None else None,
        'high': round(high, 4) if high is not None else None,
    }


def _round(value: float | None) -> float | None:
    return round(value, 4) if value is not None else None


def build_split(*, total_positives: int = 1465, dev_positives: int = 252,
                locked_test_target: dict | None = None) -> dict:
    """Describe the current split without inventing held-out cases.

    The 1213 cases left in the judge pool come from the same 20 projects as
    dev252, so they are explicitly a reserve/diagnostic pool, not an
    independent test set.  The locked test set must be supplied later from new
    projects and is intentionally represented as ``not_assigned`` here.
    """
    target = locked_test_target or {
        'positives_min': 80,
        'positives_preferred': 150,
        'negatives_min': 40,
        'negatives_preferred': 60,
        'projects_min': 5,
    }
    reserve = max(0, total_positives - dev_positives)
    return {
        'schema_version': SPLIT_SCHEMA_VERSION,
        'name': 'experiment_split_20261117',
        'policy': {
            'dev_can_tune': True,
            'reserve_is_not_test': True,
            'locked_test_must_be_new_projects': True,
            'locked_test_run_once_after_freeze': True,
        },
        'dev': {
            'source': 'frozen/dev252_20261117.json',
            'positives': dev_positives,
            'projects': 20,
            'note': 'development and regression only; not the paper test set',
        },
        'reserve_same_project': {
            'positives': reserve,
            'projects': 20,
            'use': 'diagnostic only; never label it as independent test',
        },
        'locked_test': {
            'status': 'not_assigned',
            'target': target,
            'rule': ('assign only after code, prompts, binding rules, gates '
                     'and reference patches are frozen'),
        },
        'metrics': {
            'headline': ['accuracy', 'precision', 'recall', 'f1'],
            'completion_is_separate_funnel_metric': True,
            'project_level_cluster_bootstrap_required': True,
        },
    }


def build_contract(judge_path: Path = DEFAULT_JUDGE,
                   triage_path: Path = DEFAULT_TRIAGE,
                   frozen_path: Path = DEFAULT_FROZEN,
                   ground_truth_path: Path | None = DEFAULT_GT) -> dict:
    judge = _load(judge_path)
    triage = _load(triage_path)
    frozen = _load(frozen_path)

    tp_rows = [row for row in judge.get('tp_rows', []) if row.get('case')]
    fn_rows = [row for row in triage.get('rows', []) if row.get('case')]
    fp_rows = [
        row for row in (judge.get('fp_in_pool_rows', [])
                        + judge.get('fp_blind_rows', []))
        if row.get('case')
    ]
    tp = len(tp_rows)
    fn = len(fn_rows)
    fp = len(fp_rows)
    negative_evaluated = int(judge.get('judge_invalid_evaluated_total') or 0)
    negative_total = negative_evaluated
    if ground_truth_path and Path(ground_truth_path).is_file():
        ground_truth = _load(Path(ground_truth_path))
        negative_total = sum(
            1 for row in ground_truth.get('cases', [])
            if row.get('validity') == 'invalid')
    tn = max(0, negative_evaluated - fp)
    positives = int(judge.get('positive_cases') or len(frozen['case_list']['cases']))

    manifest_count = int(frozen['case_list']['count'])
    manifest_tp = int(frozen['case_list']['tp'])
    manifest_fn = int(frozen['case_list']['fn'])
    problems = []
    if positives != manifest_count:
        problems.append(f'positive_cases {positives} != frozen count {manifest_count}')
    if tp + fn != positives:
        problems.append(f'tp+fn {tp + fn} != positives {positives}')
    if tp != manifest_tp or fn != manifest_fn:
        problems.append(
            f'tp/fn {tp}/{fn} != frozen tp/fn {manifest_tp}/{manifest_fn}')
    if fp + tn != negative_evaluated:
        problems.append('fp+tn != evaluated negatives')

    precision = precision_rate(tp, tp + fp)
    recall_value = recall(tp, tp + fn)
    accuracy = accuracy_rate(tp, fp, fn, tn)
    f1_value = f1(precision, recall_value)

    positive_rows = [
        {**row, 'project': row.get('project') or _project(row['case']),
         'outcome': 'tp'} for row in tp_rows
    ] + [
        {**row, 'project': row.get('project') or _project(row['case']),
         'outcome': 'fn'} for row in fn_rows
    ]
    predicted_rows = [
        {**row, 'project': row.get('project') or _project(row['case']),
         'outcome': 'tp'} for row in tp_rows
    ] + [
        {**row, 'project': row.get('project') or _project(row['case']),
         'outcome': 'fp'} for row in fp_rows
    ]

    def _recall_metric(rows):
        return (sum(row.get('outcome') == 'tp' for row in rows) / len(rows)
                if rows else None)

    def _precision_metric(rows):
        return (sum(row.get('outcome') == 'tp' for row in rows) / len(rows)
                if rows else None)

    recall_low, recall_high = cluster_bootstrap_ci(
        positive_rows, _recall_metric, samples=2000, seed=13)
    precision_low, precision_high = cluster_bootstrap_ci(
        predicted_rows, _precision_metric, samples=2000, seed=17)

    return {
        'schema_version': SCHEMA_VERSION,
        'snapshot': 'dev252_20261117',
        'sources': {
            'judge_anchored': {'path': str(judge_path), 'sha256': _sha(judge_path)},
            'failure_triage': {'path': str(triage_path), 'sha256': _sha(triage_path)},
            'frozen_manifest': {'path': str(frozen_path), 'sha256': _sha(frozen_path)},
            **({'judge_ground_truth': {
                'path': str(ground_truth_path),
                'sha256': _sha(Path(ground_truth_path)),
            }} if ground_truth_path and Path(ground_truth_path).is_file() else {}),
        },
        'denominator': {
            'positive': positives,
            'negative_evaluated': negative_evaluated,
            'negative_total': negative_total,
            'negative_unevaluated': max(0, negative_total - negative_evaluated),
            'note': ('same frozen confusion matrix; accuracy, precision and '
                     'recall use their standard, different denominators'),
        },
        'confusion_matrix': {
            'tp': tp, 'fp': fp, 'fn': fn, 'tn': tn,
        },
        'metrics': {
            'accuracy': _round(accuracy),
            'precision': _round(precision),
            'recall': _round(recall_value),
            'f1': _round(f1_value),
            'completion': _round(
                int(frozen['case_list']['count']) / int(frozen['case_list']['count'])),
        },
        'confidence_intervals': {
            'accuracy_wilson': _ci(tp + tn, tp + fp + fn + tn),
            'precision_wilson': _ci(tp, tp + fp),
            'recall_wilson': _ci(tp, tp + fn),
            'precision_cluster_bootstrap': {
                'low': _round(precision_low), 'high': _round(precision_high),
                'clusters': len({row['project'] for row in predicted_rows}),
                'samples': 2000,
            },
            'recall_cluster_bootstrap': {
                'low': _round(recall_low), 'high': _round(recall_high),
                'clusters': len({row['project'] for row in positive_rows}),
                'samples': 2000,
            },
        },
        'diagnostics': {
            'fp_projects': judge.get('fp_project_counts') or {},
            'fp_impact_insufficient': judge.get('fp_impact_insufficient_count'),
            'fp_remaining': judge.get('fp_remaining_count'),
            'recoverable_fn': judge.get('recoverable_fn_count'),
            'mechanism_ceiling': judge.get('ceiling_count'),
            'completion_scope': ('dev252 is already selected; 100% here is '
                                 'not full-pool coverage'),
        },
        'validation': {'ok': not problems, 'problems': problems},
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--judge', type=Path, default=DEFAULT_JUDGE)
    parser.add_argument('--triage', type=Path, default=DEFAULT_TRIAGE)
    parser.add_argument('--frozen', type=Path, default=DEFAULT_FROZEN)
    parser.add_argument('--out', type=Path, default=DEFAULT_OUT)
    parser.add_argument('--split-out', type=Path, default=DEFAULT_SPLIT)
    args = parser.parse_args(argv)

    contract = build_contract(args.judge, args.triage, args.frozen)
    split = build_split(total_positives=1465, dev_positives=252)
    args.out.write_text(json.dumps(contract, ensure_ascii=False, indent=2) + '\n')
    args.split_out.write_text(json.dumps(split, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({
        'ok': contract['validation']['ok'],
        'metrics': contract['metrics'],
        'confusion_matrix': contract['confusion_matrix'],
        'problems': contract['validation']['problems'],
    }, ensure_ascii=False, indent=2))
    return 0 if contract['validation']['ok'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
