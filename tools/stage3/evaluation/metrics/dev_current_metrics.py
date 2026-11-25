#!/usr/bin/env python3
"""Compute dev-current four metrics from a resolved-only regression replay."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
from metrics_core import ci_interval, f1  # noqa: E402

DEFAULT_RESULTS = HERE / 'dev_current_mini_results.json'
DEFAULT_OUT = HERE / 'dev_current_metrics.json'
DEFAULT_MD = HERE / 'dev_current_metrics.md'


def build(results: dict, *, label: str = 'dev-current/1',
          resolved_only: bool = True) -> dict:
    rows = results.get('results') or []
    positive_rows = [row for row in rows if row.get('label') == 'positive']
    negative_rows = [row for row in rows if row.get('label') == 'negative']
    tp = sum(row.get('classification', {}).get('outcome') == 'tp'
             for row in positive_rows)
    fn_resolved = sum(
        row.get('classification', {}).get('outcome') == 'fn'
        for row in positive_rows)
    fn_unresolved = sum(
        row.get('classification', {}).get('outcome') in {
            'fn_unresolved', 'unresolved'}
        for row in positive_rows)
    fp_vuln = sum(row.get('classification', {}).get('outcome') == 'fp'
                  for row in negative_rows)
    fp_consistency = fp_vuln + sum(
        row.get('classification', {}).get('outcome') == 'consistency_fp'
        for row in negative_rows)
    tn = sum(row.get('classification', {}).get('outcome') == 'tn'
             for row in negative_rows)
    unresolved_negative = sum(
        row.get('classification', {}).get('outcome') == 'unresolved'
        for row in negative_rows)
    fn = fn_resolved if resolved_only else fn_resolved + fn_unresolved
    resolved_pos = tp + fn_resolved
    resolved_neg = tn + fp_consistency
    resolved = resolved_pos + resolved_neg
    unresolved = fn_unresolved + unresolved_negative
    recall_denominator = resolved_pos if resolved_only else len(positive_rows)
    accuracy_denominator = resolved if resolved_only else len(rows)

    recall = tp / recall_denominator if recall_denominator else None
    precision_vuln = tp / (tp + fp_vuln) if tp + fp_vuln else None
    precision_consistency = (tp / (tp + fp_consistency)
                             if tp + fp_consistency else None)
    accuracy = ((tp + tn) / accuracy_denominator
                if accuracy_denominator else None)
    completion = (len(rows) - unresolved) / len(rows) if rows else None
    policy = (
        'Development-only current-protocol result. Unresolved cases are '
        'excluded from the four-metric matrix and reported as coverage loss.'
        if resolved_only else
        'Full-sample result: unevaluated positives count as FN and unresolved '
        'negatives reduce accuracy; abstention never becomes TN.')
    return {
        'schema_version': 'dev-current-metrics/1',
        'label': label,
        'manifest': results.get('manifest'),
        'replay_protocol': results.get('protocol'),
        'reporter_schema_version': 'dev-current-metrics/2',
        'metric_mode': 'resolved_only' if resolved_only else 'full_sample',
        'resolved_only': resolved_only,
        'coverage': {
            'cases': len(rows),
            'resolved_positive': resolved_pos,
            'resolved_negative': resolved_neg,
            'unresolved_or_timeout': unresolved,
            'unresolved_positive': fn_unresolved,
            'unresolved_negative': unresolved_negative,
            'completion_rate': round(completion, 4)
            if completion is not None else None,
        },
        'confusion_matrix': {
            'tp': tp, 'fn': fn, 'fp_vuln': fp_vuln,
            'fp_consistency': fp_consistency, 'tn': tn,
            'fn_resolved': fn_resolved, 'fn_unresolved': fn_unresolved,
        },
        'metrics': {
            'accuracy': round(accuracy, 4) if accuracy is not None else None,
            'recall': round(recall, 4) if recall is not None else None,
            'precision_vuln': round(precision_vuln, 4)
            if precision_vuln is not None else None,
            'precision_consistency': round(precision_consistency, 4)
            if precision_consistency is not None else None,
            'f1_vuln': round(f1(precision_vuln, recall), 4)
            if precision_vuln is not None and recall is not None else None,
        },
        'ci95': {
            'recall': ci_interval(tp, recall_denominator),
            'precision_vuln': ci_interval(tp, tp + fp_vuln),
        },
        'reportable': unresolved == 0 and resolved_pos > 0 and resolved_neg > 0,
        'policy': policy + ' Never relabel as mainline.',
    }


def markdown(report: dict) -> str:
    metrics = report['metrics']
    matrix = report['confusion_matrix']
    coverage = report['coverage']
    return '\n'.join([
        '# dev-current 四指标', '',
        f"- label: `{report['label']}`",
        f"- metric mode: `{report.get('metric_mode', 'resolved_only')}`",
        f"- reportable: **{str(report['reportable']).lower()}**",
        f"- replay protocol: `{report.get('replay_protocol') or 'n/a'}`", '',
        '| metric | value |', '| --- | ---: |',
        f"| accuracy | {metrics['accuracy']} |",
        f"| recall | {metrics['recall']} |",
        f"| precision_vuln | {metrics['precision_vuln']} |",
        f"| precision_consistency | {metrics['precision_consistency']} |",
        f"| f1_vuln | {metrics['f1_vuln']} |", '',
        '| coverage | value |', '| --- | ---: |',
        f"| cases | {coverage['cases']} |",
        f"| resolved positive | {coverage['resolved_positive']} |",
        f"| resolved negative | {coverage['resolved_negative']} |",
        f"| unresolved/timeout | {coverage['unresolved_or_timeout']} |", '',
        f"| completion rate | {coverage['completion_rate']} |", '',
        '| confusion | value |', '| --- | ---: |',
        f"| TP | {matrix['tp']} |",
        f"| FN | {matrix['fn']} |",
        f"| FP_vuln | {matrix['fp_vuln']} |",
        f"| FP_consistency | {matrix['fp_consistency']} |",
        f"| TN | {matrix['tn']} |", '',
    ]) + '\n'


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--results', type=Path, default=DEFAULT_RESULTS)
    parser.add_argument('--manifest', type=Path)
    parser.add_argument('--out-json', type=Path, default=DEFAULT_OUT)
    parser.add_argument('--out-md', type=Path, default=DEFAULT_MD)
    parser.add_argument('--full-sample', action='store_true',
                        help='count unevaluated positives as FN and keep '
                             'unresolved negatives outside TN')
    args = parser.parse_args(argv)
    results = json.loads(args.results.read_text())
    if args.manifest:
        manifest = json.loads(args.manifest.read_text())
        results['manifest'] = str(args.manifest)
        results['protocol'] = manifest.get('protocol')
    report = build(results, resolved_only=not args.full_sample)
    args.out_json.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    args.out_md.write_text(markdown(report))
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
