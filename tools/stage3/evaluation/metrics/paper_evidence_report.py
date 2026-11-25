#!/usr/bin/env python3
"""Build a development-only evidence report beside the authoritative metrics."""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
STAGE3 = HERE.parents[1]
MAINLINE_METRICS = HERE / 'mainline_metrics.json'
POS_EVAL = HERE / 'mainline_pos_eval_1_7_33.json'
NEG_EVAL = HERE / 'mainline_neg_eval_1_7_33.json'
DEV_MD = HERE / 'dev_metrics_252.md'
PROTOCOL = STAGE3 / 'mainline-protocol.json'
PROVENANCE = HERE / 'provenance_gate.json'
LOCKED = HERE / 'locked_eval_contract.json'
OUT_JSON = HERE / 'paper_evidence_report.json'
OUT_MD = HERE / 'paper_evidence_report.md'

SCHEMA_VERSION = 'paper-evidence/1'

FAILURE_GROUPS = {
    'stage2_review_required': (
        'stage2 contract blocked by feedback or review',
        ('stage2_review_required', 'stage2_restatement_required')),
    'binding_or_observability': (
        'P/I/V cannot be bound to code observables',
        ('binding_error', 'partial_binding', 'binding_failed',
         'preconditions_infeasible_on_code', 'unobservable')),
    'effect_witness': (
        'exploit action ran but independent effect was not witnessed',
        ('effect_not_witnessed', 'weak_effect_not_independent',
         'patch_no_effect')),
    'reference_or_external_route': (
        'needs reference patch or external-state witness',
        ('reference_patch_required', 'halt_witness_required')),
    'compile_or_harness': (
        'forge harness or injected project failed to compile',
        ('compile_error', 'compile_blocked')),
    'no_violation_observed': (
        'ran to completion without reproducing the claimed violation',
        ('effect_observed_invariant_holds', 'violation_not_reproduced',
         'not_dynamically_expressible', 'inconclusive')),
    'reproduced': (
        'claim reproduced',
        ('violation_reproduced',)),
}


def _load(path: Path) -> dict:
    return json.loads(Path(path).read_text(encoding='utf-8'))


def _extract(pattern: str, text: str, label: str) -> tuple[str, ...]:
    match = re.search(pattern, text)
    if match is None:
        raise ValueError(f'cannot extract {label} from dev metrics')
    return match.groups()


def _pct(value: float | None) -> str:
    return 'n/a' if value is None else f'{value * 100:.1f}%'


def _num(value: float | None) -> str:
    return 'n/a' if value is None else f'{value:.4f}'


def _f1(precision: float, recall: float) -> float | None:
    if precision is None or recall is None or precision + recall == 0:
        return None
    return 2 * precision * recall / (precision + recall)


def _authoritative() -> dict:
    report = _load(MAINLINE_METRICS)
    metrics = report['metrics']
    matrix = report['confusion_matrix']
    coverage = report['coverage']
    ci = report['confidence_intervals']
    headline = report.get('headline_metrics') or {}
    canonical_source = report.get('canonical_metrics') or {}
    canonical = {
        'accuracy': canonical_source.get(
            'accuracy', metrics['accuracy_consistency_conservative']),
        'recall_conservative': canonical_source.get(
            'recall', metrics['recall_consistency_conservative']),
        'precision': canonical_source.get(
            'precision', metrics['precision_consistency']),
        'f1_conservative': canonical_source.get(
            'f1', metrics['f1_consistency_conservative']),
    }
    canonical_ci95 = {
        'accuracy': ci['accuracy_consistency_conservative'],
        'recall_conservative': ci['recall_consistency_conservative'],
        'precision': ci['precision_consistency'],
        'f1_conservative': (
            ci.get('f1_consistency_cluster_bootstrap')
            or {'low': None, 'high': None}),
    }
    return {
        'source': str(MAINLINE_METRICS.relative_to(STAGE3.parents[1])),
        'protocol': _load(PROTOCOL)['version'],
        'metrics': {
            'accuracy': metrics['accuracy'],
            'recall': metrics['recall'],
            'precision_vuln': metrics['precision_vuln'],
            'f1_vuln': metrics['f1_vuln'],
            'recall_consistency': metrics['recall_consistency'],
            'precision_consistency': metrics['precision_consistency'],
            'f1_consistency': metrics['f1_consistency'],
        },
        'canonical_scope': canonical_source.get(
            'scope', 'source-code/report consistency'),
        'canonical_metrics': canonical,
        'canonical_ci95': canonical_ci95,
        'headline_metrics': headline,
        'ci95': {
            'accuracy': ci['accuracy'],
            'recall': ci['recall'],
            'precision_vuln': ci['precision_vuln'],
            'precision_consistency': ci['precision_consistency'],
        },
        'headline_ci95': {
            'recall_conservative': ci['recall_sample_wide'],
        },
        'confusion_matrix': {
            key: matrix.get(key)
            for key in ('tp', 'tp_consistency', 'fn', 'fn_consistency',
                        'unevaluated_positives', 'tn', 'fp_vuln', 'fp_raw',
                        'fp_impact_insufficient')
        },
        'coverage': {
            'positives_evaluated': coverage['positives_evaluated'],
            'positives_unevaluated': coverage['positives_unevaluated'],
            'negatives_evaluated': coverage['negatives_evaluated'],
            'negatives_witness_eligible': coverage.get(
                'negatives_witness_eligible'),
            'negatives_witness_ineligible': coverage.get(
                'negatives_witness_ineligible'),
            'sample_total_negatives': report['sample']['negatives'],
        },
        'consistency_gate': report.get('consistency_gate') or {},
        'effect_adjudication': report.get('effect_adjudication') or {},
    }


def _development_retrospective() -> dict:
    text = DEV_MD.read_text(encoding='utf-8')
    recall_pct, recall_tp, recall_den = _extract(
        r'\|\s*端到端召回率\s*\|\s*\*\*([\d.]+)%\s*\*\*\s*\|\s*(\d+)\s*/\s*(\d+)',
        text, 'dev recall')
    judged_pct, judged_num, judged_left, judged_right = _extract(
        r'\|\s*判例锚定精确率\s*\|\s*\*\*([\d.]+)%\s*\*\*\s*\|\s*(\d+)'
        r'\s*/\s*\((\d+)\+(\d+)\)',
        text, 'dev judged precision')
    vuln_pct = _extract(
        r'\|\s*漏洞级精确率\s*\|\s*\*\*([\d.]+)%',
        text, 'dev vulnerability precision')[0]
    f1_value = _extract(
        r'\|\s*F1（端到端×判例精确率）\s*\|\s*\*\*([\d.]+)\*\*',
        text, 'dev F1')[0]
    completion_pct, completion_done, completion_total = _extract(
        r'\|\s*全量完成率\s*\|\s*\*\*([\d.]+)%\s*\*\*\s*\|\s*(\d+)\s*/\s*(\d+)',
        text, 'dev completion')
    full_pool = _extract(
        r'“相关/有效”.+?=\s*\*\*(\d+)\*\*', text, 'dev full pool')[0]

    recall_tp = int(recall_tp)
    full_pool = int(full_pool)
    judged_den = int(judged_left) + int(judged_right)
    judged_precision = int(judged_num) / judged_den
    full_pool_recall = recall_tp / full_pool
    return {
        'source': str(DEV_MD.relative_to(STAGE3.parents[1])),
        'status': 'development-only; not authoritative; not a locked test',
        'dev_denominator_is_primary': True,
        'conditional_recall': recall_tp / int(recall_den),
        'conditional_recall_pct': f'{float(recall_pct):.1f}%',
        'conditional_recall_ratio': f'{recall_tp}/{recall_den}',
        'full_pool_recall': full_pool_recall,
        'full_pool_metric_scope': (
            'coverage-aware lower bound over all relevant positive '
            'candidates; not dev252 recall'),
        'full_pool_recall_ratio': f'{recall_tp}/{full_pool}',
        'judged_precision': judged_precision,
        'judged_precision_pct': f'{float(judged_pct):.1f}%',
        'judged_precision_ratio': (
            f'{judged_num}/({judged_left}+{judged_right})'),
        'vulnerability_precision': float(vuln_pct) / 100,
        'conditional_f1': float(f1_value),
        'full_pool_f1_ratio': _f1(judged_precision, full_pool_recall),
        'completion': int(completion_done) / int(completion_total),
        'completion_pct': f'{float(completion_pct):.1f}%',
        'completion_ratio': f'{completion_done}/{completion_total}',
    }


def _verdict_counts(path: Path) -> Counter:
    counts: Counter = Counter()
    for row in _load(path).get('cases', []):
        values = row.get('verdicts') or []
        counts.update(str(value) for value in values if value)
    return counts


def _failure_buckets() -> dict:
    positive = _verdict_counts(POS_EVAL)
    negative = _verdict_counts(NEG_EVAL)
    total = positive + negative
    rows = []
    for group, (description, verdicts) in FAILURE_GROUPS.items():
        selected = tuple(dict.fromkeys(verdicts))
        rows.append({
            'group': group,
            'description': description,
            'verdicts': selected,
            'claims': sum(total[verdict] for verdict in selected),
            'positive_claims': sum(positive[verdict] for verdict in selected),
            'negative_claims': sum(negative[verdict] for verdict in selected),
        })
    rows.sort(key=lambda row: (-row['claims'], row['group']))
    return {
        'unit': 'claim-level verdicts in current-protocol eval files; '
                'not case-level confusion matrix',
        'positive_claims': sum(positive.values()),
        'negative_claims': sum(negative.values()),
        'rows': rows,
    }


def _gate_evidence() -> dict:
    protocol = _load(PROTOCOL)
    provenance = _load(PROVENANCE)
    locked = _load(LOCKED)
    dev_eligible = provenance['denominator']['dev252']['cases'][
        'eligible_current']
    return {
        'protocol_version': protocol['version'],
        'protocol_sha256': protocol['sha256'],
        'locked_ready': bool(locked.get('ready')),
        'locked_publishable': bool(locked.get('publishable')),
        'primary_publishable': bool(locked.get(
            'primary_publishable', locked.get('publishable'))),
        'publication_status': locked.get('publication_status'),
        'primary_publication_status': locked.get(
            'primary_publication_status', locked.get('publication_status')),
        'primary_gate': locked.get('primary_gate') or {},
        'publication_blockers': list(
            locked.get('publication_blockers') or []),
        'coverage': locked.get('coverage') or {},
        'dev252_eligible_current': dev_eligible,
        'dev252_in_authoritative_denominator': bool(dev_eligible),
        'mainline_current_only': bool(provenance['mainline']['current_only']),
        'legacy_diagnostics_gating': bool(
            provenance['legacy_diagnostics']['gating']),
        'report_rewrites_authoritative_metrics': False,
    }


def build() -> dict:
    authoritative = _authoritative()
    metrics = authoritative['metrics']
    canonical = authoritative['canonical_metrics']
    matrix = authoritative['confusion_matrix']
    coverage = authoritative['coverage']
    evaluated = coverage['positives_evaluated']
    total = evaluated + coverage['positives_unevaluated']
    recall_value = canonical['recall_conservative']
    recall_pct = f"{recall_value * 100:.1f}%"
    conditional_pct = f"{metrics['recall'] * 100:.1f}%"
    return {
        'schema_version': SCHEMA_VERSION,
        'purpose': 'paper evidence companion; authoritative metrics remain '
                   'mainline_metrics.json',
        'authoritative': authoritative,
        'vuln_companion': {
            'accuracy': metrics['accuracy'],
            'recall': metrics['recall'],
            'precision_vuln': metrics['precision_vuln'],
            'f1_vuln': metrics['f1_vuln'],
            'ci95': {
                'precision_vuln': authoritative['ci95']['precision_vuln'],
            },
            'allowed_use': 'vulnerability-label companion diagnostic only',
        },
        'development_retrospective': _development_retrospective(),
        'failure_buckets': _failure_buckets(),
        'gate_evidence': _gate_evidence(),
        'interpretation': [
            'dev252 recall 68.7% is correctly computed on the frozen 252 '
            'development cases; cases outside dev252 are not part of that '
            'denominator.',
            '173/1465 is not dev252 recall; it is a separate coverage-aware '
            'lower bound over all relevant positive candidates because only '
            '252/1465 candidates had completed stage3 when dev252 was frozen.',
            f'current authoritative consistency recall is {recall_pct} over '
            f"{matrix['tp_consistency']}/{total} sampled locked positives with unevaluated "
            f'cases counted as FN; conditional recall over evaluated cases '
            f'is {conditional_pct} over {matrix["tp_consistency"]}/{evaluated}.',
            f'the conditional-vs-conditional gap (68.7% dev vs {conditional_pct} '
            'locked) remains real and is attributable to development tuning, '
            'older protocol, semantic observability and distribution shift, '
            'not merely denominator choice.',
            'the main technical bottleneck is semantic observability and '
            'effect witness, not a single compile/API failure; negative '
            'cases without an eligible witness remain unresolved and do not '
            'become TN.',
        ],
        'solution_status': {
            'phase_a_evidence_closure': 'executed by this report',
            'phase_b_protocol_upgrade_and_full_rerun': 'not executed; '
                'requires explicit quota approval because prior bounded '
                'repairs produced 0 TP',
            'dev252_negative_substitution': 'rejected',
        },
    }


def markdown(report: dict) -> str:
    authoritative = report['authoritative']
    dev = report['development_retrospective']
    buckets = report['failure_buckets']
    gates = report['gate_evidence']
    metrics = authoritative['metrics']
    canonical = authoritative['canonical_metrics']
    ci = authoritative['ci95']
    canonical_ci = authoritative['canonical_ci95']
    cm = authoritative['confusion_matrix']
    coverage = authoritative['coverage']

    lines = [
        '# 论文指标证据表（development-only companion）', '',
        '> 本表解释权威四指标；权威数值只来自 '
        '`tools/stage3/evaluation/metrics/mainline_metrics.json`。', '',
        '## 1. 权威主表', '',
        f"- protocol: `{authoritative['protocol']}`",
        f"- scope: `{authoritative['canonical_scope']}`",
        f"- 正例已评测: {coverage['positives_evaluated']}/40",
        f"- 负例已评测: {coverage['negatives_evaluated']}/"
        f"{coverage['sample_total_negatives']} "
        f"(witness eligible {coverage['negatives_witness_eligible']})", '',
        '| 指标 | 数值 | 95% CI |',
        '| --- | ---: | --- |',
        f"| Accuracy（consistency，保守） | {_pct(canonical['accuracy'])} | "
        f"{_pct(canonical_ci['accuracy']['low'])}–"
        f"{_pct(canonical_ci['accuracy']['high'])} |",
        f"| Recall（consistency，保守，未评测计 FN） | "
        f"{_pct(canonical['recall_conservative'])} | "
        f"{_pct(canonical_ci['recall_conservative']['low'])}–"
        f"{_pct(canonical_ci['recall_conservative']['high'])} |",
        f"| Precision（consistency，已评测） | {_pct(canonical['precision'])} | "
        f"{_pct(canonical_ci['precision']['low'])}–"
        f"{_pct(canonical_ci['precision']['high'])} |",
        f"| F1（consistency，保守） | {_num(canonical['f1_conservative'])} | "
        f"{_pct(canonical_ci['f1_conservative']['low'])}–"
        f"{_pct(canonical_ci['f1_conservative']['high'])} |", '',
        f"> 已评测条件口径 recall={_pct(metrics['recall'])}、"
        f"F1={_num(metrics['f1_vuln'])} 只作诊断；"
        '主表口径与 `metric_alignment_report` 一致。', '',
        f"混淆矩阵：TP_consistency {cm['tp_consistency']} / FN_consistency {cm['fn_consistency']} / "
        f"未评测 {cm['unevaluated_positives']} / TN {cm['tn']} / "
        f"FP_vuln {cm['fp_vuln']} / FP_raw {cm['fp_raw']}"
        f"（影响不足 {cm['fp_impact_insufficient']}）。", '',
        '## 1a. 同协议漏洞级伴生口径', '',
        f"- Precision（vuln，诊断）：{_pct(metrics['precision_vuln'])} "
        f"95% CI {_pct(ci['precision_vuln']['low'])}–"
        f"{_pct(ci['precision_vuln']['high'])}",
        f"- Recall（vuln，诊断）：{_pct(metrics['recall'])}",
        f"- F1（vuln，诊断）：{_num(metrics['f1_vuln'])}", '',
        '## 1b. consistency 已评测条件口径', '',
        f"- Precision（consistency，条件）：{_pct(metrics['precision_consistency'])} "
        f"95% CI {_pct(ci['precision_consistency']['low'])}–"
        f"{_pct(ci['precision_consistency']['high'])}",
        f"- Recall（consistency，诊断）：{_pct(metrics['recall_consistency'])}",
        f"- F1（consistency，诊断）：{_num(metrics['f1_consistency'])}", '',
        '> 主表 consistency 口径由独立 V witness 决定 TP/FP；TN 必须有 '
        'eligible negative witness 且没有 V witness。漏洞级指标只作伴生诊断，'
        '不替代主表。', '',
    ]
    adjudication = authoritative.get('effect_adjudication') or {}
    if adjudication.get('tp_revert_witness'):
        lines += [
            f"- revert-witness 重新裁决：{adjudication['tp_revert_witness']} 个 "
            f"TP（policy `{adjudication.get('policy')}`，原始 verdict 保留）", '']
    lines += [
        '## 2. dev252 开发集对照（不得作为主表）', '',
        '| 口径 | 数值 | 分子/分母 | 说明 |',
        '| --- | ---: | ---: | --- |',
        f"| 条件 recall | {dev['conditional_recall_pct']} | "
        f"{dev['conditional_recall_ratio']} | 仅已跑完 252 例 |",
        f"| 覆盖感知下界（不是 dev252 recall） | "
        f"{_pct(dev['full_pool_recall'])} | "
        f"{dev['full_pool_recall_ratio']} | 全部相关正例候选，另一个问题 |",
        f"| 判例 precision | {dev['judged_precision_pct']} | "
        f"{dev['judged_precision_ratio']} | 开发期 blind-invalid 负例 |",
        f"| 漏洞级 precision | {_pct(dev['vulnerability_precision'])} | — | "
        '排除影响不足 FP |',
        f"| 条件 F1 | {_num(dev['conditional_f1'])} | — | "
        '使用条件 recall |',
        f"| 全正例 F1 粗算 | {_num(dev['full_pool_f1_ratio'])} | — | "
        '使用全正例 recall 下界 |',
        f"| 完成率 | {dev['completion_pct']} | {dev['completion_ratio']} | "
        'dev252 是已完成子集 |', '',
        '## 3. 当前失败根因（claim 级）', '',
        f"unit: {buckets['unit']}", '',
        '| 分组 | claims | 正例 | 负例 | 说明 |',
        '| --- | ---: | ---: | ---: | --- |',
    ]
    for row in buckets['rows']:
        lines.append(
            f"| `{row['group']}` | {row['claims']} | "
            f"{row['positive_claims']} | {row['negative_claims']} | "
            f"{row['description']} |")
    lines += [
        '',
        '## 4. 门禁证据', '',
        '| gate | value |',
        '| --- | --- |',
        f"| protocol | `{gates['protocol_version']}` |",
        f"| protocol sha256 | `{gates['protocol_sha256']}` |",
        f"| locked_ready | {str(gates['locked_ready']).lower()} |",
        f"| locked_publishable | "
        f"{str(gates.get('locked_publishable')).lower()} |",
        f"| publication status | `{gates.get('publication_status')}` |",
        f"| primary publishable | "
        f"{str(gates.get('primary_publishable')).lower()} |",
        f"| primary publication status | "
        f"`{gates.get('primary_publication_status')}` |",
        f"| positive coverage | "
        f"{(gates.get('coverage') or {}).get('eligible_positive')}/"
        f"{(gates.get('coverage') or {}).get('positives')} = "
        f"{_pct((gates.get('coverage') or {}).get('positive_coverage'))} |",
        f"| negative coverage | "
        f"{(gates.get('coverage') or {}).get('eligible_negative')}/"
        f"{(gates.get('coverage') or {}).get('negatives')} = "
        f"{_pct((gates.get('coverage') or {}).get('negative_coverage'))} |",
        f"| dev252 eligible_current | {gates['dev252_eligible_current']} |",
        f"| dev252 in authoritative denominator | "
        f"{str(gates['dev252_in_authoritative_denominator']).lower()} |",
        f"| mainline current-only | "
        f"{str(gates['mainline_current_only']).lower()} |",
        f"| legacy diagnostics gating | "
        f"{str(gates['legacy_diagnostics_gating']).lower()} |", '',
    ]
    blockers = gates.get('publication_blockers') or []
    if blockers:
        lines += ['### Publication blockers', '']
        lines += [f'- {item}' for item in blockers]
        lines.append('')
    lines += [
        '## 5. 解释', '',
    ]
    lines += [f'- {item}' for item in report['interpretation']]
    lines += ['', '## 6. 方案执行状态', '']
    for key, value in report['solution_status'].items():
        lines.append(f'- `{key}`: {value}')
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
    print(f'paper evidence: {args.out_json}')
    print(f'paper evidence: {args.out_md}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
