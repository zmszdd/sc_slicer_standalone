#!/usr/bin/env python3
"""Build the canonical metric alignment companion report."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

try:
    from . import paper_evidence_report as evidence
except ImportError:
    import paper_evidence_report as evidence

HERE = Path(__file__).resolve().parent
STAGE3 = HERE.parents[1]
MAINLINE_METRICS = HERE / 'mainline_metrics.json'
APLUS_REPORT = HERE / 'aplus_hardened_report.md'
OUT_JSON = HERE / 'metric_alignment_report.json'
OUT_MD = HERE / 'metric_alignment_report.md'

SCHEMA_VERSION = 'metric-alignment/1'

CANONICAL = (
    (
        'mainline_accuracy_consistency_conservative',
        'Accuracy (consistency, conservative)',
        'accuracy',
        '(TP_consistency + TN) / (all sampled positives + evaluated negatives)',
        'paper main table',
    ),
    (
        'mainline_recall_consistency_conservative',
        'Recall (consistency, conservative)',
        'recall',
        'TP_consistency / all sampled positives; unevaluated as FN',
        'paper main table',
    ),
    (
        'mainline_precision_consistency_evaluated',
        'Precision (consistency, evaluated)',
        'precision',
        'TP_consistency / (TP_consistency + FP_consistency)',
        'paper main table',
    ),
    (
        'mainline_f1_consistency_conservative',
        'F1 (consistency, conservative)',
        'f1',
        'derived from precision_consistency and conservative recall_consistency',
        'paper main table',
    ),
)

DIAGNOSTICS = (
    ('diagnostic_completion_rate', 'Completion rate', 'completion_rate',
     'evaluated cases + explicit failures'),
    ('diagnostic_completion_sample_wide', 'Completion lower bound',
     'completion_sample_wide', 'all sampled cases'),
    ('diagnostic_recall_vuln_evaluated', 'Recall (vuln, evaluated)',
     'recall', 'evaluated positives only'),
    ('diagnostic_recall_sample_wide', 'Recall lower bound',
     'recall_sample_wide', 'all sampled positives, unevaluated as FN'),
    ('diagnostic_recall_automatic', 'Recall (automatic route)',
     'recall_automatic', 'evaluated positives, automatic route'),
    ('diagnostic_accuracy_vuln_evaluated', 'Accuracy (vuln, evaluated)',
     'accuracy', 'vuln matrix'),
    ('diagnostic_recall_vuln_conservative', 'Recall (vuln, conservative)',
     'recall_sample_wide', 'all sampled positives, unevaluated as FN'),
    ('diagnostic_precision_vuln_evaluated', 'Precision (vuln, evaluated)',
     'precision_vuln', 'TP / (TP + FP_vuln)'),
    ('diagnostic_f1_vuln_conservative', 'F1 (vuln, conditional)',
     'f1_vuln', 'derived from precision_vuln and evaluated recall'),
    ('diagnostic_accuracy_consistency_evaluated',
     'Accuracy (consistency, evaluated)',
     'accuracy_consistency', 'consistency matrix; evaluated denominator'),
    ('diagnostic_precision_consistency', 'Precision (consistency, evaluated)',
     'precision_consistency', 'TP / (TP + FP_consistency)'),
    ('diagnostic_f1_consistency_evaluated', 'F1 (consistency, evaluated)',
     'f1_consistency', 'derived from precision_consistency and recall'),
    ('diagnostic_f1_vuln_evaluated', 'F1 (vuln, evaluated)',
     'f1_vuln', 'derived from precision_vuln and evaluated recall'),
    ('diagnostic_recall_cluster_bootstrap', 'Recall cluster CI',
     'recall_cluster_bootstrap', 'project cluster bootstrap'),
    ('diagnostic_precision_vuln_cluster_bootstrap', 'Precision cluster CI',
     'precision_vuln_cluster_bootstrap', 'project cluster bootstrap'),
)

APLUS_METRICS = {
    'accuracy': 'accuracy',
    'recall': 'recall',
    'precision_vuln': 'precision_vuln',
    'precision_consistency': 'precision_consistency',
    'F1_vuln': 'f1_vuln',
}

NAMING_RULES = (
    ('accuracy', 'mainline_accuracy_consistency_conservative',
     'must state consistency level and conservative denominator'),
    ('recall', 'mainline_recall_consistency_conservative',
     'must state consistency level and conservative denominator'),
    ('precision', 'mainline_precision_consistency_evaluated',
     'must state whether consistency, vuln, judged, or smoke'),
    ('F1', 'mainline_f1_consistency_conservative',
     'must state which precision and recall denominators are paired'),
    ('vuln precision', 'diagnostic_precision_vuln_evaluated',
     'vuln-level precision is a companion diagnostic, not the paper main table'),
    ('dev252 recall', 'dev252_conditional_recall',
     'must state the frozen 252-case conditional denominator'),
    ('173/1465', 'dev252_full_pool_recall_lower_bound',
     'must not be named dev252 recall'),
    ('A+/hardened recall', 'smoke_aplus_hardened_recall',
     'must carry reportable=false and old-protocol status'),
    ('completion rate', 'diagnostic_completion_rate',
     'must not be used as accuracy, recall, or precision'),
)

FORBIDDEN_COMPARISONS = (
    {
        'id': 'dev252_vs_mainline_recall',
        'pair': ['dev252_conditional_recall',
                 'diagnostic_recall_vuln_conservative'],
        'decision': 'conditional-only-with-explicit-labels',
        'reason': 'different sample, protocol, tuning history, and negative pool',
    },
    {
        'id': 'full_pool_as_dev252_recall',
        'pair': ['dev252_full_pool_recall_lower_bound', 'dev252 recall'],
        'decision': 'forbidden',
        'reason': '173/1465 answers coverage, not the dev252 denominator',
    },
    {
        'id': 'smoke_vs_mainline',
        'pair': ['smoke_aplus_hardened_metrics',
                 'mainline canonical four'],
        'decision': 'forbidden',
        'reason': 'old protocol, resolved-only smoke, reportable=false',
    },
    {
        'id': 'precision_flavors',
        'pair': ['diagnostic_precision_vuln_evaluated',
                 'mainline_precision_consistency_evaluated',
                 'dev252_judged_precision',
                 'dev252_vulnerability_precision'],
        'decision': 'forbidden-without-explicit-name',
        'reason': 'different FP semantics and denominators',
    },
    {
        'id': 'completion_as_performance',
        'pair': ['diagnostic_completion_rate',
                 'mainline_accuracy_consistency_conservative',
                 'mainline_recall_consistency_conservative'],
        'decision': 'forbidden',
        'reason': 'completion measures execution, not vulnerability detection',
    },
    {
        'id': 'claim_case_unit',
        'pair': ['claim-level verdicts', 'case-level confusion matrix'],
        'decision': 'forbidden-without-unit-label',
        'reason': 'one case can contribute multiple claims',
    },
    {
        'id': 'stage2_quality_as_end_to_end',
        'pair': ['stage2 faithfulness/formalization rates',
                 'mainline canonical four'],
        'decision': 'forbidden',
        'reason': 'stage2 quality is not stage3 reproduction',
    },
    {
        'id': 'historical_snapshot_as_current',
        'pair': ['2026-11-23 historical metrics', 'current mainline metrics'],
        'decision': 'forbidden',
        'reason': 'revert-witness re-adjudication changed TP/FN',
    },
)

PAPER_CONTRACT = (
    'Main table contains only the four canonical consistency metrics with CI, '
    'coverage, protocol, and publishable status.',
    'Vulnerability-level metrics appear only as explicitly named companion '
    'diagnostics and never replace the consistency main table.',
    'dev252 appears only as a development retrospective; 68.7% is conditional '
    'recall over 252 cases and 11.8% is a separate coverage-aware lower bound.',
    'A+/hardened smoke appears only as an appendix diagnostic and must carry '
    'reportable=false and protocol mainline/1.6.1.',
    'Precision must be named as consistency, vuln, judged, or smoke; bare '
    '"precision" is not acceptable.',
    'Completion, stage2 quality, and claim-level verdicts must not be '
    'presented as end-to-end case-level performance.',
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _ratio(numerator: int, denominator: int) -> str:
    return f'{numerator}/{denominator}'


def _aplus_smoke() -> dict:
    text = APLUS_REPORT.read_text(encoding='utf-8')
    protocol = re.search(r'- protocol: `([^`]+)`', text)
    reportable = re.search(r'- reportable: \*\*(true|false)\*\*', text)
    if protocol is None or reportable is None:
        raise ValueError('cannot parse A+/hardened report header')
    metrics = {}
    for line in text.splitlines():
        columns = [column.strip() for column in line.split('|')
                   if column.strip()]
        if len(columns) != 3:
            continue
        key = APLUS_METRICS.get(columns[0])
        if key is None:
            continue
        metrics[key] = float(columns[2])
    missing = set(APLUS_METRICS.values()) - set(metrics)
    if missing:
        raise ValueError('A+/hardened report missing metrics: '
                         + ', '.join(sorted(missing)))
    return {
        'source': str(APLUS_REPORT.relative_to(HERE.parents[3])),
        'protocol': protocol.group(1),
        'reportable': reportable.group(1) == 'true',
        'scope': 'resolved-only 64-case smoke; blind-invalid negative pool',
        'metrics': metrics,
        'allowed_use': 'appendix diagnostic only',
    }


def _canonical_rows(report: dict, matrix: dict, ci: dict) -> list[dict]:
    positive_total = (matrix['tp_consistency'] + matrix['fn_consistency']
                      + matrix['unevaluated_positives'])
    negative_total = matrix['fp_raw'] + matrix['tn']
    numerators = {
        'mainline_accuracy_consistency_conservative':
            _ratio(matrix['tp_consistency'] + matrix['tn'],
                   positive_total + negative_total),
        'mainline_recall_consistency_conservative':
            _ratio(matrix['tp_consistency'], positive_total),
        'mainline_precision_consistency_evaluated':
            _ratio(matrix['tp_consistency'],
                   matrix['tp_consistency'] + matrix['fp_raw']),
        'mainline_f1_consistency_conservative': 'derived',
    }
    ci_keys = {
        'accuracy': 'accuracy_consistency_conservative',
        'recall': 'recall_consistency_conservative',
        'precision': 'precision_consistency',
        'f1': 'f1_consistency_cluster_bootstrap',
    }
    rows = []
    for name, label, source_key, denominator, allowed_use in CANONICAL:
        interval = ci.get(ci_keys.get(source_key, source_key))
        value = report.get('canonical_metrics', {}).get(source_key)
        if value is None:
            value = report['metrics'][source_key]
        rows.append({
            'name': name,
            'label': label,
            'value': value,
            'ci95': interval,
            'formula': denominator,
            'ratio': numerators[name],
            'allowed_use': allowed_use,
            'source': str(MAINLINE_METRICS.relative_to(HERE.parents[3])),
        })
    return rows


def build() -> dict:
    mainline = evidence._load(MAINLINE_METRICS)
    evidence_report = evidence.build()
    authoritative = evidence_report['authoritative']
    dev = evidence_report['development_retrospective']
    gates = evidence_report['gate_evidence']
    matrix = mainline['confusion_matrix']
    ci = mainline['confidence_intervals']

    diagnostics = []
    for name, label, source_key, denominator in DIAGNOSTICS:
        diagnostics.append({
            'name': name,
            'label': label,
            'value': mainline['metrics'].get(source_key),
            'ci95': ci.get(source_key),
            'denominator': denominator,
            'allowed_use': 'diagnostic only; not paper main table',
            'source': str(MAINLINE_METRICS.relative_to(HERE.parents[2])),
        })

    development = {
        'source': dev['source'],
        'status': dev['status'],
        'metrics': [
            {
                'name': 'dev252_conditional_recall',
                'value': dev['conditional_recall'],
                'ratio': dev['conditional_recall_ratio'],
                'allowed_use': 'development retrospective with denominator',
            },
            {
                'name': 'dev252_full_pool_recall_lower_bound',
                'value': dev['full_pool_recall'],
                'ratio': dev['full_pool_recall_ratio'],
                'allowed_use': 'coverage-only; not dev252 recall',
            },
            {
                'name': 'dev252_completion',
                'value': dev['completion'],
                'ratio': dev['completion_ratio'],
                'allowed_use': 'coverage-only; not performance',
            },
            {
                'name': 'dev252_judged_precision',
                'value': dev['judged_precision'],
                'ratio': dev['judged_precision_ratio'],
                'allowed_use': 'development retrospective only',
            },
            {
                'name': 'dev252_vulnerability_precision',
                'value': dev['vulnerability_precision'],
                'ratio': None,
                'allowed_use': 'development retrospective only',
            },
            {
                'name': 'dev252_conditional_f1',
                'value': dev['conditional_f1'],
                'ratio': None,
                'allowed_use': 'development retrospective only',
            },
            {
                'name': 'dev252_full_pool_f1_rough',
                'value': dev['full_pool_f1_ratio'],
                'ratio': None,
                'allowed_use': 'rough lower bound only',
            },
        ],
    }

    return {
        'schema_version': SCHEMA_VERSION,
        'purpose': 'canonical metric names, denominators, and comparison '
                   'boundaries; authoritative metrics remain '
                   'mainline_metrics.json',
        'source_of_truth': str(MAINLINE_METRICS.relative_to(HERE.parents[3])),
        'canonical_main_table': _canonical_rows(
            mainline, matrix, ci),
        'same_protocol_diagnostics': diagnostics,
        'development_retrospective': development,
        'aplus_hardened_smoke': _aplus_smoke(),
        'naming_rules': [
            {'ambiguous_name': name,
             'canonical_name': canonical,
             'rule': rule}
            for name, canonical, rule in NAMING_RULES
        ],
        'forbidden_comparisons': list(FORBIDDEN_COMPARISONS),
        'paper_contract': list(PAPER_CONTRACT),
        'gate_evidence': {
            'protocol_version': gates['protocol_version'],
            'locked_ready': gates['locked_ready'],
            'locked_publishable': gates['locked_publishable'],
            'primary_publishable': gates['primary_publishable'],
            'publication_status': gates['publication_status'],
            'primary_publication_status': gates[
                'primary_publication_status'],
            'publication_blockers': gates['publication_blockers'],
            'primary_gate': gates['primary_gate'],
            'dev252_eligible_current': gates['dev252_eligible_current'],
            'mainline_current_only': gates['mainline_current_only'],
            'coverage': gates['coverage'],
            'consistency_gate': mainline.get('consistency_gate') or {},
        },
        'report_does_not_rewrite_authoritative_metrics': True,
        'sources': [
            {'path': str(path.relative_to(HERE.parents[3])),
             'sha256': _sha256(path)}
            for path in (MAINLINE_METRICS, APLUS_REPORT)
        ],
    }


def _pct(value: float | None) -> str:
    return 'n/a' if value is None else f'{value * 100:.1f}%'


def _num(value: float | None) -> str:
    return 'n/a' if value is None else f'{value:.4f}'


def _ci_text(interval: dict | None) -> str:
    if not interval:
        return '—'
    return f"{_pct(interval['low'])}–{_pct(interval['high'])}"


def markdown(report: dict) -> str:
    canonical = report['canonical_main_table']
    diagnostics = report['same_protocol_diagnostics']
    dev = report['development_retrospective']
    smoke = report['aplus_hardened_smoke']
    gates = report['gate_evidence']
    lines = [
        '# 指标对齐报告（companion，不改写权威指标）', '',
        '> 权威来源始终是 '
        '`tools/stage3/evaluation/metrics/mainline_metrics.json`。'
        '本报告只固定命名、分母和禁止比较项。', '',
        f"protocol: `{gates['protocol_version']}`；"
        f"locked_ready={str(gates['locked_ready']).lower()}；"
        f"vuln_companion_publishable={str(gates['locked_publishable']).lower()}；"
        f"vuln_companion_status=`{gates['publication_status']}`。", '',
        f"主表一致性发布状态：publishable="
        f"{str(gates['primary_publishable']).lower()}；"
        f"status=`{gates['primary_publication_status']}`。", '',
        f"覆盖：正例 {gates['coverage']['eligible_positive']}"
        f"/{gates['coverage']['positives']}；"
        f"负例 {gates['coverage']['eligible_negative']}"
        f"/{gates['coverage']['negatives']}。", '',
        '## 1. 论文主表：仅以下四项', '',
        '| canonical key | 名称 | 值 | 95% CI | 分母/公式 | 允许用途 |',
        '| --- | --- | ---: | --- | --- | --- |',
    ]
    for row in canonical:
        lines.append(
            f"| `{row['name']}` | {row['label']} | "
            f"{_num(row['value'])} | {_ci_text(row['ci95'])} | "
            f"{row['ratio']}：{row['formula']} | {row['allowed_use']} |")
    lines += [
        '',
        '发布阻塞：', '',
    ]
    lines += [f'- {item}' for item in gates['publication_blockers']]
    consistency_gate = gates.get('consistency_gate') or {}
    lines += [
        '',
        f"一致性发布状态：`{consistency_gate.get('publication_status')}`；"
        f"publishable={str(consistency_gate.get('publishable')).lower()}。",
        f"一致性覆盖：正例 {consistency_gate.get('eligible_positive')}/30；"
        f"witness 负例 {consistency_gate.get('witness_eligible_negative')}/24。",
        '',
        '一致性发布阻塞：', '',
    ]
    lines += [f'- {item}' for item in (
        consistency_gate.get('publication_blockers') or [])]
    lines += [
        '',
        '## 2. 同协议诊断指标（不得进入主表）', '',
        '| canonical key | 名称 | 值 | 95% CI | 分母/范围 |',
        '| --- | --- | ---: | --- | --- |',
    ]
    for row in diagnostics:
        lines.append(
            f"| `{row['name']}` | {row['label']} | "
            f"{_num(row['value'])} | {_ci_text(row['ci95'])} | "
            f"{row['denominator']} |")
    lines += [
        '',
        '## 3. dev252 开发集回顾（不得作为权威主表）', '',
        f"status: `{dev['status']}`", '',
        '| canonical key | 值 | 分子/分母 | 允许用途 |',
        '| --- | ---: | --- | --- |',
    ]
    for row in dev['metrics']:
        lines.append(
            f"| `{row['name']}` | {_num(row['value'])} | "
            f"{row['ratio'] or '—'} | {row['allowed_use']} |")
    lines += [
        '',
        '关键点：`173/252 = 68.7%` 是 dev252 条件 recall；'
        '`173/1465 = 11.8%` 是全正例覆盖感知下界，不是 dev252 recall。', '',
        '## 4. A+/hardened/top3 smoke（不得与主线比较）', '',
        f"protocol: `{smoke['protocol']}`；"
        f"reportable={str(smoke['reportable']).lower()}；"
        f"scope: {smoke['scope']}。", '',
        '| metric | 值 |',
        '| --- | ---: |',
    ]
    for name, value in smoke['metrics'].items():
        lines.append(f'| `{name}` | {_num(value)} |')
    lines += [
        '',
        '## 5. 命名规则', '',
        '| 歧义写法 | canonical key | 规则 |',
        '| --- | --- | --- |',
    ]
    for row in report['naming_rules']:
        lines.append(
            f"| `{row['ambiguous_name']}` | `{row['canonical_name']}` | "
            f"{row['rule']} |")
    lines += [
        '',
        '## 6. 禁止比较', '',
        '| id | 对象 | 判定 | 原因 |',
        '| --- | --- | --- | --- |',
    ]
    for row in report['forbidden_comparisons']:
        lines.append(
            f"| `{row['id']}` | {', '.join(row['pair'])} | "
            f"{row['decision']} | {row['reason']} |")
    lines += [
        '',
        '## 7. 论文写作合同', '',
    ]
    lines += [f'- {item}' for item in report['paper_contract']]
    lines += [
        '',
        '## 8. 数据来源', '',
        '| path | sha256 |',
        '| --- | --- |',
    ]
    for row in report['sources']:
        lines.append(f"| `{row['path']}` | `{row['sha256']}` |")
    return '\n'.join(lines) + '\n'


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out-json', type=Path, default=OUT_JSON)
    parser.add_argument('--out-md', type=Path, default=OUT_MD)
    args = parser.parse_args(argv)
    report = build()
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + '\n',
        encoding='utf-8')
    args.out_md.write_text(markdown(report), encoding='utf-8')
    print(f'metric alignment: {args.out_json}')
    print(f'metric alignment: {args.out_md}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
