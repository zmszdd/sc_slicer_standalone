#!/usr/bin/env python3
"""主线客观指标报告：漏斗 + 覆盖损失 + 项目级指标 + 四指标（多口径）。

与 full_flow_metrics.py 互补：本报告把被单一数字掩盖的三件事摊开——
1) 主线漏斗各阶段通过率；2) 未到动态终态的覆盖损失按原因分层；
3) 项目级/聚类口径（案例数 ≠ 独立样本数）。

输出：
  --out-json  结构化指标
  --out-md    可给老师看的人类可读报告
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from lib.verdict_loop import TERMINAL_VERDICTS

ROOT = Path(__file__).resolve().parents[1]

DYNAMIC = tuple(TERMINAL_VERDICTS)
BLOCKED_STATUSES = {'no_stage2_run', 'stage2_blocked', 'zero_claims',
                    'no_flatten', 'no_bound_claims'}
VERDICT_ALIASES = {
    'effect_observed_invariant_holds': 'invariant_holds_on_exploit_path',
    'preconditions_infeasible_on_code': 'poc_not_witnessed',
    'patch_no_effect': 'patch_no_effect',
}


def _wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    d = 1 + z * z / n
    center = p + z * z / (2 * n)
    m = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((center - m) / d, (center + m) / d)


def _project(case: str) -> str:
    return case.split('__')[0]


def _claim_bucket(verdict: str) -> str:
    """Map one claim verdict to a concrete root-cause bucket."""
    if verdict in DYNAMIC:
        return 'dynamic'
    if verdict in VERDICT_ALIASES:
        return VERDICT_ALIASES[verdict]
    return verdict


def _claim_breakdown(row: dict) -> dict[str, list[str]]:
    """Split a case's per-claim verdicts into ``{bucket: [claim_id, ...]}``."""
    verdicts = row.get('verdicts') or []
    claim_ids = (row.get('claim_ids') or row.get('bound_claim_ids') or [])
    if claim_ids and len(claim_ids) == len(verdicts):
        pairs = list(zip(claim_ids, verdicts))
    else:
        pairs = [(f'claim-{i}', v) for i, v in enumerate(verdicts, 1)]
    out: dict[str, list[str]] = {}
    for claim_id, verdict in pairs:
        bucket = _claim_bucket(verdict)
        out.setdefault(bucket, []).append(claim_id)
    return out


def _done_class(row: dict) -> str:
    vs = row.get('verdicts') or []
    dyn = [v for v in vs if v in DYNAMIC]
    if dyn:
        return 'dynamic'
    if vs and all(v == 'not_dynamically_expressible' for v in vs):
        return 'not_dynamically_expressible'
    if vs and all(v == 'reference_patch_required' for v in vs):
        return 'reference_patch_required'
    if vs and all(v == 'halt_witness_required' for v in vs):
        return 'halt_witness_required'
    if vs and all(v == 'compile_blocked' for v in vs):
        return 'compile_blocked'
    if vs and all(v == 'compile_error' for v in vs):
        return 'compile_error'
    if vs and all(v == 'partial_binding' for v in vs):
        return 'partial_binding'
    if vs and all(v == 'inconclusive' for v in vs):
        return 'inconclusive'
    return 'mixed_non_dynamic'


def analyze(positive: dict, negative: list[dict],
            judge_precision: float | None = None,
            judge_metrics: dict | None = None) -> dict:
    cases = positive.get('cases', [])
    total = len(cases)
    done = [r for r in cases if r.get('status') == 'done']
    stage2_ok = [r for r in cases
                 if r.get('status') in ('done', 'no_bound_claims')]
    dynamic = [r for r in done
               if any(v in DYNAMIC for v in (r.get('verdicts') or []))]
    tp = [r for r in done if int(r.get('reproduced') or 0) > 0]

    # 覆盖损失分层（案例级）
    loss = {}
    for r in cases:
        if r.get('status') == 'done':
            cls = _done_class(r)
            if cls != 'dynamic':
                loss[f'stage3:{cls}'] = loss.get(f'stage3:{cls}', 0) + 1
        else:
            loss[f'stage2:{r.get("status")}'] = (
                loss.get(f'stage2:{r.get("status")}', 0) + 1)

    # 覆盖损失分层（claim 级）：把多 claim 案例的状态按 claim 摊开，
    # 不让 mixed_non_dynamic 吞掉可恢复的 partial_binding / compile_error。
    claim_loss: dict[str, int] = {}
    mixed_claim_cases: list[dict] = []
    for r in done:
        breakdown = _claim_breakdown(r)
        non_dynamic = {b: ids for b, ids in breakdown.items() if b != 'dynamic'}
        if len(non_dynamic) > 1:
            mixed_claim_cases.append({
                'case': r['case'],
                'bucket': _done_class(r),
                'claim_breakdown': non_dynamic,
            })
        for bucket, ids in non_dynamic.items():
            key = f'stage3:{bucket}'
            claim_loss[key] = claim_loss.get(key, 0) + len(ids)
    claim_loss = dict(sorted(claim_loss.items(), key=lambda x: -x[1]))
    mixed_claim_cases.sort(key=lambda x: (x['bucket'], x['case']))

    # 项目级
    proj_cases: dict[str, list] = {}
    for r in cases:
        proj_cases.setdefault(_project(r['case']), []).append(r)
    proj_rows = []
    for proj, rows in sorted(proj_cases.items()):
        p_done = [r for r in rows if r.get('status') == 'done']
        p_dyn = [r for r in p_done
                 if any(v in DYNAMIC for v in (r.get('verdicts') or []))]
        p_tp = [r for r in p_done if int(r.get('reproduced') or 0) > 0]
        proj_rows.append({
            'project': proj,
            'cases': len(rows),
            'done': len(p_done),
            'dynamic': len(p_dyn),
            'reproduced': len(p_tp),
            'recalled': len(p_tp) > 0,
        })
    proj_total = len(proj_rows)
    proj_recalled = sum(1 for p in proj_rows if p['recalled'])

    # 准确率（构造负样本口径）
    fp = sum(1 for n in negative if n.get('verdict') == 'violation_reproduced')
    tn = len(negative) - fp

    tp_n = len(tp)
    eval_n = len(dynamic)
    recall_proj = proj_recalled / proj_total if proj_total else 0.0
    precision_constructed = tp_n / (tp_n + fp) if (tp_n + fp) else 0.0

    def _f1(prec: float, rec: float) -> float:
        return (2 * prec * rec / (prec + rec)) if (prec + rec) else 0.0

    if judge_metrics:
        # 权威混淆矩阵：相关样本 = 判例 valid/fixed/wontfix 的 finding。
        # TP=判例净化复现，FN=其余相关样本，FP=判例 invalid 且复现，
        # TN=判例 invalid 可评测但未复现。召回、准确率、F1 三者同源。
        tp_clean = int(judge_metrics.get('tp_clean', tp_n))
        relevant = int(judge_metrics.get('judge_valid_cases', 0))
        relevant_dynamic = int(judge_metrics.get('judge_valid_dynamic', 0))
        fp_judge = int(judge_metrics.get('fp_from_judge_invalid', 0))
        tn_judge = int(judge_metrics.get('tn_invalid', 0))
        fn_judge = int(judge_metrics.get('fn_judge_valid',
                                         max(0, relevant - tp_clean)))
        ceiling_count = int(judge_metrics.get('ceiling_count', 0))
        recoverable_fn = int(judge_metrics.get(
            'recoverable_fn_count', max(0, fn_judge - ceiling_count)))
        recall_ceiling = judge_metrics.get('recall_end_to_end_ceiling')
        if recall_ceiling is None:
            recall_ceiling = ((relevant - ceiling_count) / relevant
                              if relevant else 0.0)
        judge_prec = judge_metrics.get('precision')
        vuln_prec = judge_metrics.get('precision_vuln_level')
        vuln_prec_ci = judge_metrics.get('precision_vuln_level_ci')
        fp_impact = int(judge_metrics.get('fp_impact_insufficient_count', 0))
        fp_remaining = int(judge_metrics.get('fp_remaining_count',
                                              max(0, fp_judge - fp_impact)))
        recall_e2e = tp_clean / relevant if relevant else 0.0
        recall_e2e_ci = (tuple(judge_metrics['recall_end_to_end_ci'])
                         if judge_metrics.get('recall_end_to_end_ci')
                         else _wilson(tp_clean, relevant))
        recall_eval = tp_clean / relevant_dynamic if relevant_dynamic else 0.0
        recall_eval_ci = (tuple(judge_metrics['recall_evaluable_ci'])
                          if judge_metrics.get('recall_evaluable_ci')
                          else _wilson(tp_clean, relevant_dynamic))
        precision_judge = judge_prec
        precision_judge_ci = (tuple(judge_metrics['precision_ci'])
                              if judge_metrics.get('precision_ci')
                              else _wilson(tp_clean, tp_clean + fp_judge))
        precision_for_f1 = (judge_prec if judge_prec is not None
                            else (judge_precision if judge_precision is not None
                                  else precision_constructed))
        f1_evaluable = _f1(precision_for_f1, recall_eval)
        f1_end_to_end = _f1(precision_for_f1, recall_e2e)
        f1_vuln_e2e = _f1(vuln_prec, recall_e2e) if vuln_prec is not None else None
        f1_vuln_eval = _f1(vuln_prec, recall_eval) if vuln_prec is not None else None
        judge_anchored = {
            'tp_judge_clean': tp_clean,
            'fn_judge_valid': fn_judge,
            'fp_judge_invalid': fp_judge,
            'tn_judge_invalid': tn_judge,
            'judge_valid_cases': relevant,
            'judge_valid_dynamic': relevant_dynamic,
            'recall_end_to_end': recall_e2e,
            'recall_end_to_end_ci': recall_e2e_ci,
            'recall_evaluable': recall_eval,
            'recall_evaluable_ci': recall_eval_ci,
            'recall_end_to_end_ceiling': recall_ceiling,
            'ceiling_count': ceiling_count,
            'recoverable_fn_count': recoverable_fn,
            'precision': precision_judge,
            'precision_ci': precision_judge_ci,
            'f1_evaluable': f1_evaluable,
            'f1_end_to_end': f1_end_to_end,
            'precision_vuln_level': vuln_prec,
            'precision_vuln_level_ci': vuln_prec_ci,
            'fp_impact_insufficient_count': fp_impact,
            'fp_remaining_count': fp_remaining,
            'f1_vuln_end_to_end': f1_vuln_e2e,
            'f1_vuln_evaluable': f1_vuln_eval,
        }
    else:
        recall_e2e = tp_n / total if total else 0.0
        recall_eval = tp_n / eval_n if eval_n else 0.0
        precision_for_f1 = (judge_precision if judge_precision is not None
                            else precision_constructed)
        f1_evaluable = _f1(precision_for_f1, recall_eval)
        f1_end_to_end = _f1(precision_for_f1, recall_e2e)
        judge_anchored = {}

    return {
        'schema_version': 'stage3-metrics-report/1',
        'funnel': {
            'stage1_flatten': {'n': total, 'rate': 1.0},
            'stage2_spec_nonempty': {'n': len(stage2_ok),
                                     'rate': len(stage2_ok) / total if total else 0.0},
            'stage3_dynamic': {'n': len(dynamic),
                               'rate': len(dynamic) / total if total else 0.0},
            'stage3_reproduced': {'n': tp_n,
                                  'rate': tp_n / total if total else 0.0},
            'stage3_dynamic_not_reproduced': {'n': len(dynamic) - tp_n,
                                              'rate': (len(dynamic) - tp_n) / total if total else 0.0},
        },
        'coverage_loss': {k: v for k, v in sorted(loss.items(), key=lambda x: -x[1])},
        'coverage_loss_total': total - len(dynamic),
        'coverage_loss_claims': claim_loss,
        'coverage_loss_claims_total': sum(claim_loss.values()),
        'mixed_claim_cases': mixed_claim_cases,
        'project_level': {
            'total_projects': proj_total,
            'recalled_projects': proj_recalled,
            'recall': recall_proj,
            'recall_ci': _wilson(proj_recalled, proj_total),
            'rows': proj_rows,
        },
        'metrics': {
            'completion_rate': len(done) / total if total else 0.0,
            'completion_rate_ci': _wilson(len(done), total),
            'stage2_pass_rate': len(stage2_ok) / total if total else 0.0,
            'dynamic_terminal_rate': len(dynamic) / total if total else 0.0,
            'recall_end_to_end': recall_e2e,
            'recall_end_to_end_ci': _wilson(tp_n, total) if not judge_metrics else recall_e2e_ci,
            'recall_evaluable': recall_eval,
            'recall_evaluable_ci': _wilson(tp_n, eval_n) if not judge_metrics else recall_eval_ci,
            'recall_project_level': recall_proj,
            'precision_constructed_negatives': precision_constructed,
            'precision_judge_anchored': (judge_anchored.get('precision')
                                         if judge_anchored else judge_precision),
            'tp_cases': tp_n,
            'fp_cases': fp,
            'tn_cases': tn,
            'precision_constructed_ci': _wilson(tp_n, tp_n + fp),
            'f1_evaluable': f1_evaluable,
            'f1_end_to_end': f1_end_to_end,
            'judge_anchored': judge_anchored,
        },
    }


def _pct(x: float) -> str:
    return f'{x:.1%}'


def render_md(r: dict) -> str:
    f = r['funnel']
    p = r['project_level']
    m = r['metrics']
    lines = []
    lines.append('# 主线客观指标报告（案例级 + 项目级）')
    lines.append('')
    lines.append('> 口径：四指标以判例锚定混淆矩阵为准（TP/FN 来自判例 valid/fixed/')
    lines.append('> wontfix 相关样本，FP/TN 来自判例 invalid 独立负样本）。')
    lines.append('> 构造负样本 100% 仅为内部一致性自检，不作为对外准确率/F1。')
    lines.append('')
    lines.append('## 1. 主线漏斗（案例级）')
    lines.append('')
    lines.append('| 阶段 | 数量 | 通过率 |')
    lines.append('| --- | ---: | ---: |')
    lines.append(f"| 阶段一 flatten | {f['stage1_flatten']['n']} | {_pct(f['stage1_flatten']['rate'])} |")
    lines.append(f"| 阶段二 spec 非空 | {f['stage2_spec_nonempty']['n']} | {_pct(f['stage2_spec_nonempty']['rate'])} |")
    lines.append(f"| 阶段三 动态终态 | {f['stage3_dynamic']['n']} | {_pct(f['stage3_dynamic']['rate'])} |")
    lines.append(f"| 阶段三 复现(机械) | {f['stage3_reproduced']['n']} | {_pct(f['stage3_reproduced']['rate'])} |")
    lines.append(f"| 阶段三 动态未复现 | {f['stage3_dynamic_not_reproduced']['n']} | {_pct(f['stage3_dynamic_not_reproduced']['rate'])} |")
    lines.append('')
    lines.append('## 2. 覆盖损失（未到动态终态的案例，按原因）')
    lines.append('')
    lines.append('| 原因 | 案例数 |')
    lines.append('| --- | ---: |')
    for k, v in r['coverage_loss'].items():
        lines.append(f'| {k} | {v} |')
    lines.append(f'| **合计** | **{r["coverage_loss_total"]}** |')
    lines.append('')
    lines.append('### 2.1 覆盖损失（claim 级，非动态 claim 按根因摊开）')
    lines.append('')
    lines.append('| 原因 | claim 数 |')
    lines.append('| --- | ---: |')
    for k, v in r['coverage_loss_claims'].items():
        lines.append(f'| {k} | {v} |')
    lines.append(f'| **合计** | **{r["coverage_loss_claims_total"]}** |')
    lines.append('')
    if r['mixed_claim_cases']:
        lines.append('### 2.2 多 claim 状态混杂明细（案例级桶与 claim 级根因并列）')
        lines.append('')
        lines.append('| case | 案例级桶 | claim 级拆分 |')
        lines.append('| --- | --- | --- |')
        for row in r['mixed_claim_cases']:
            breakdown = '; '.join(
                f'{k}:{len(v)}' for k, v in sorted(row['claim_breakdown'].items()))
            lines.append(f"| {row['case']} | {row['bucket']} | {breakdown} |")
        lines.append('')
    lines.append('## 3. 项目级指标')
    lines.append('')
    lines.append(f'- 项目总数：{p["total_projects"]}')
    lines.append(f"- 至少复现 1 个 finding 的项目：{p['recalled_projects']}")
    lines.append(f"- 项目级召回：{_pct(p['recall'])}（95% CI {_pct(p['recall_ci'][0])}–{_pct(p['recall_ci'][1])}）")
    lines.append('')
    lines.append('| 项目 | 案例 | done | 动态 | 复现 |')
    lines.append('| --- | ---: | ---: | ---: | ---: |')
    for row in p['rows']:
        lines.append(f"| {row['project']} | {row['cases']} | {row['done']} | {row['dynamic']} | {row['reproduced']} |")
    lines.append('')
    ja = m.get('judge_anchored') or {}
    lines.append('## 4. 四指标（判例锚定口径）')
    lines.append('')
    lines.append('| 指标 | 值 | 说明 |')
    lines.append('| --- | ---: | --- |')
    lines.append(f"| 完成率 | {_pct(m['completion_rate'])} | 到达 stage3 done / 全输入，95% CI {_pct(m['completion_rate_ci'][0])}–{_pct(m['completion_rate_ci'][1])} |")
    lines.append(f"| 动态终态率(覆盖率) | {_pct(m['dynamic_terminal_rate'])} | 到达复现/未复现终态 / 全输入 |")
    if ja:
        tp = ja['tp_judge_clean']
        fn = ja['fn_judge_valid']
        fpj = ja['fp_judge_invalid']
        tnj = ja['tn_judge_invalid']
        lines.append(f"| 召回(端到端) | {_pct(ja['recall_end_to_end'])} | TP={tp} / 判例相关样本 {ja['judge_valid_cases']}，95% CI {_pct(ja['recall_end_to_end_ci'][0])}–{_pct(ja['recall_end_to_end_ci'][1])} |")
        lines.append(f"| 召回(可评测) | {_pct(ja['recall_evaluable'])} | TP={tp} / 判例相关动态样本 {ja['judge_valid_dynamic']}，95% CI {_pct(ja['recall_evaluable_ci'][0])}–{_pct(ja['recall_evaluable_ci'][1])} |")
        lines.append(f"| 召回(端到端天花板) | {_pct(ja['recall_end_to_end_ceiling'])} | 判例相关样本扣除 {ja['ceiling_count']} 例机制天花板（缺参考补丁/不可动态表达）后可达上限 |")
        if ja.get('precision_vuln_level') is not None:
            lines.append(f"| 准确率(漏洞级·对外主口径) | {_pct(ja['precision_vuln_level'])} | TP={tp} / 剔除影响不足FP后的判复现 {tp+ja.get('fp_remaining_count', fpj)}，95% CI {_pct(ja['precision_vuln_level_ci'][0])}–{_pct(ja['precision_vuln_level_ci'][1])} |")
            lines.append(f"| F1(漏洞级/端到端) | {ja['f1_vuln_end_to_end']:.3f} | 漏洞级准确率 × 端到端召回 |")
            lines.append(f"| F1(漏洞级/可评测) | {ja['f1_vuln_evaluable']:.3f} | 漏洞级准确率 × 可评测召回 |")
        lines.append(f"| 准确率(机制一致性·自检) | {_pct(ja['precision'])} | TP={tp} FP={fpj}，95% CI {_pct(ja['precision_ci'][0])}–{_pct(ja['precision_ci'][1])} |")
        lines.append(f"| F1(机制一致性/端到端) | {ja['f1_end_to_end']:.3f} | 一致性准确率 × 端到端召回 |")
        lines.append(f"| F1(机制一致性/可评测) | {ja['f1_evaluable']:.3f} | 一致性准确率 × 可评测召回 |")
    else:
        lines.append(f"| 召回(端到端) | {_pct(m['recall_end_to_end'])} | TP / 全输入，95% CI {_pct(m['recall_end_to_end_ci'][0])}–{_pct(m['recall_end_to_end_ci'][1])} |")
        lines.append(f"| 召回(可评测) | {_pct(m['recall_evaluable'])} | TP / 动态终态案例，95% CI {_pct(m['recall_evaluable_ci'][0])}–{_pct(m['recall_evaluable_ci'][1])} |")
    lines.append(f"| 召回(项目级) | {_pct(m['recall_project_level'])} | 至少复现1个的项目占比，95% CI {_pct(p['recall_ci'][0])}–{_pct(p['recall_ci'][1])} |")
    lines.append(f"| 准确率(构造负样本·仅自检) | {_pct(m['precision_constructed_negatives'])} | 机械TP={m['tp_cases']} FP={m['fp_cases']} TN={m['tn_cases']}，FP=0 是设计使然，不对外 |")
    if ja:
        lines.append('')
        lines.append('### 4.1 判例锚定混淆矩阵')
        lines.append('')
        lines.append('| 判例真值 \\ 主线裁决 | 复现(+) | 未复现(-) | 合计 |')
        lines.append('| --- | ---: | ---: | ---: |')
        lines.append(f"| valid/fixed/wontfix(+) | TP={tp} | FN={fn} | {tp + fn} |")
        lines.append(f"| invalid(-) | FP={fpj} | TN={tnj} | {fpj + tnj} |")
        lines.append('')
        lines.append('> 说明：FP 采自判例 invalid 独立负样本池（75 例可评测），TP/FN 采自')
        lines.append('> 判例相关正样本池（101 例），两池患病率不同，混淆矩阵仅展示各池内的')
        lines.append('> 分子分母，不跨池假设等患病率。')
    return '\n'.join(lines) + '\n'


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--positive-eval', type=Path, required=True)
    parser.add_argument('--negative-results', type=Path, required=True)
    parser.add_argument('--judge-metrics', type=Path, default=None,
                        help='judge_anchored_metrics.json for authoritative F1/recall/precision')
    parser.add_argument('--out-json', type=Path, required=True)
    parser.add_argument('--out-md', type=Path, required=True)
    args = parser.parse_args(argv)

    pos = json.loads(Path(args.positive_eval).read_text())
    neg = json.loads(Path(args.negative_results).read_text())
    judge_metrics = None
    if args.judge_metrics:
        judge_metrics = json.loads(Path(args.judge_metrics).read_text())
    report = analyze(pos, neg, judge_metrics=judge_metrics)
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    md = render_md(report)
    args.out_md.write_text(md)
    print(md)
    print(f'\njson -> {args.out_json}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
