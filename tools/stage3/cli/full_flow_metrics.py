#!/usr/bin/env python3
"""端到端全流程（case 级）四指标。

口径：每个输入案例走完 阶段一产物 -> 阶段二 run -> 阶段三差分，产出**一个**终态
verdict，在案例粒度上计算：

* 完成率 = 到达终态的案例 / 全部输入案例
* 召回率 = 正样本中至少复现一个 claim 的案例 / 正样本案例总数
* 准确率 = TP_cases / (TP_cases + FP_cases)，FP 来自负样本（判 violation_reproduced）
* F1 = 2*P*R/(P+R)

输入：
  --positive-eval         stage3-eval-run/1 汇总（含每案例 status + verdicts）
  --negative-results      负样本结果列表（每行 verdict），或
  --negative-cases-root   负样本 case 目录；缺 --negative-results 时按需生成
                          （调用 stage3_negative_eval，不进入主线流水线）
  --out                   输出 metrics.json

负样本按需生成：只有在本命令里显式传入 --negative-cases-root 且未提供
--negative-results 时才会触发，主线（stage1->stage2->stage3）不会调用。
"""
from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
from pathlib import Path

from lib.verdict_loop import TERMINAL_VERDICTS

ROOT = Path(__file__).resolve().parents[1]  # tools/stage3


def _wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Wilson 95% 置信区间，样本太小时给出可信区间而非点估计。"""
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    d = 1 + z * z / n
    center = p + z * z / (2 * n)
    m = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((center - m) / d, (center + m) / d)


DYNAMIC_VERDICTS = tuple(TERMINAL_VERDICTS)
NOT_EVALUABLE_VERDICTS = ('not_dynamically_expressible', 'halt_witness_required')

BLOCKED_STATUSES = {
    'no_stage2_run', 'stage2_blocked', 'zero_claims', 'no_flatten',
    'no_bound_claims',
}


def analyze(positive_eval: dict, negative_results: list[dict],
            judge_metrics: dict | None = None) -> dict:
    cases = positive_eval.get('cases', [])
    total = len(cases)
    completed = [r for r in cases if r.get('status') == 'done']
    tp_cases = sum(1 for r in completed if int(r.get('reproduced') or 0) > 0)
    fp_cases = sum(1 for row in negative_results
                   if row.get('verdict') == 'violation_reproduced')
    active_tn_cases = sum(1 for row in negative_results
                          if row.get('verdict') == 'violation_not_reproduced')
    inconclusive_cases = sum(1 for row in negative_results
                             if row.get('verdict') == 'inconclusive')
    tn_cases = len(negative_results) - fp_cases

    # 可复现性分母：只有产生了动态差分终态（复现/未复现）的案例才算“可评测”。
    # 阶段一/二阻塞（no_stage2_run/stage2_blocked/zero_claims/no_flatten/
    # no_bound_claims）与全部 claim 均为 not_dynamically_expressible /
    # halt_witness_required 的案例计入完成率/覆盖率，但不计入召回分母，避免把
    # “当前见证机制尚不能评测”误算成“漏召回”。
    blocked = [r for r in cases if r.get('status') in BLOCKED_STATUSES]
    evaluable = []
    not_expressible = []
    halt_required = []
    for r in completed:
        verdicts = r.get('verdicts') or []
        if any(v in DYNAMIC_VERDICTS for v in verdicts):
            evaluable.append(r)
        elif verdicts and all(v == 'not_dynamically_expressible' for v in verdicts):
            not_expressible.append(r)
        elif verdicts and all(v == 'halt_witness_required' for v in verdicts):
            halt_required.append(r)
        else:
            blocked.append(r)

    completion = len(completed) / total if total else 0.0
    recall_denominator = len(evaluable)
    recall = tp_cases / recall_denominator if recall_denominator else 0.0
    precision = tp_cases / (tp_cases + fp_cases) if (tp_cases + fp_cases) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    completion_ci = _wilson(len(completed), total)
    recall_ci = _wilson(tp_cases, recall_denominator)
    precision_ci = _wilson(tp_cases, tp_cases + fp_cases)
    evaluable_coverage = recall_denominator / total if total else 0.0

    # 判例锚定口径：用判例 valid/invalid 真值替换构造负样本 FP=0，使四指标同源。
    judge_anchored = None
    if judge_metrics:
        tp_clean = int(judge_metrics.get('tp_clean', tp_cases))
        fp_judge = int(judge_metrics.get('fp_from_judge_invalid', 0))
        judge_precision = judge_metrics.get('precision')
        judge_precision_ci = tuple(judge_metrics.get('precision_ci', ()))
        relevant = int(judge_metrics.get('judge_valid_cases', 0))
        relevant_dynamic = int(judge_metrics.get('judge_valid_dynamic', 0))
        recall_e2e = tp_clean / relevant if relevant else 0.0
        recall_eval = tp_clean / relevant_dynamic if relevant_dynamic else 0.0
        judge_anchored = {
            'tp_judge_clean': tp_clean,
            'fp_judge_invalid': fp_judge,
            'fn_judge_valid': int(judge_metrics.get('fn_judge_valid', 0)),
            'tn_judge_invalid': int(judge_metrics.get('tn_invalid', 0)),
            'judge_valid_cases': relevant,
            'judge_valid_dynamic': relevant_dynamic,
            'precision': judge_precision,
            'precision_ci': judge_precision_ci if judge_precision_ci
                            else _wilson(tp_clean, tp_clean + fp_judge),
            'recall_end_to_end': recall_e2e,
            'recall_end_to_end_ci': _wilson(tp_clean, relevant),
            'recall_evaluable': recall_eval,
            'recall_evaluable_ci': _wilson(tp_clean, relevant_dynamic),
            'f1_end_to_end': (2 * judge_precision * recall_e2e
                              / (judge_precision + recall_e2e)
                              if judge_precision is not None and (judge_precision + recall_e2e)
                              else 0.0),
            'f1_evaluable': (2 * judge_precision * recall_eval
                             / (judge_precision + recall_eval)
                             if judge_precision is not None and (judge_precision + recall_eval)
                             else 0.0),
        }

    # 样本量门槛：不足时给出显式警告，避免把小样本点估计当成可靠结论。
    # precision CI 在 FP=0 时 = Wilson(TP, TP)，只由 TP（复现正样本数）决定；
    # 纯 TN 负样本不直接收窄 precision CI，只负责抓 FP。
    warnings = []
    if total < 40:
        warnings.append(
            f'正样本仅 {total} 例（目标 >=40），召回率 95% CI 半宽仍会 >10pp，结论不可靠')
    if recall_denominator < 40:
        warnings.append(
            f'可评测正样本仅 {recall_denominator} 例（目标 >=40），召回率结论不可靠')
    if tp_cases < 40:
        warnings.append(
            f'复现正样本仅 {tp_cases} 例（目标 >=40），precision 在 FP=0 时下界 '
            f'约 {_wilson(tp_cases, tp_cases)[0]:.0%}，无法证明高精度')
    if len(negative_results) < 20:
        warnings.append(
            f'负样本仅 {len(negative_results)} 例（目标 >=40 个独立根因），FP 检测力不足')
    if active_tn_cases < 5:
        warnings.append(
            f'主动翻转的负样本仅 {active_tn_cases} 例（violation_not_reproduced），'
            f'其余多为 inconclusive 弃权，负样本证据偏弱')

    return {
        'schema_version': 'stage3-full-flow-metrics/1',
        'positive_total_cases': total,
        'positive_completed_cases': len(completed),
        'positive_evaluable_cases': recall_denominator,
        'positive_blocked_cases': len(blocked),
        'positive_not_dynamically_expressible_cases': len(not_expressible),
        'positive_halt_witness_required_cases': len(halt_required),
        'evaluable_coverage': evaluable_coverage,
        'negative_total_cases': len(negative_results),
        'negative_active_tn_cases': active_tn_cases,
        'negative_inconclusive_cases': inconclusive_cases,
        'tp_cases': tp_cases,
        'fp_cases': fp_cases,
        'tn_cases': tn_cases,
        'completion_rate': completion,
        'recall_rate': recall,
        'precision': precision,
        'f1': f1,
        'wilson95': {
            'completion': {'lower': completion_ci[0], 'upper': completion_ci[1]},
            'recall': {'lower': recall_ci[0], 'upper': recall_ci[1]},
            'precision': {'lower': precision_ci[0], 'upper': precision_ci[1]},
        },
        'judge_anchored': judge_anchored,
        'sample_warnings': warnings,
    }


def _print(metrics: dict):
    print('=' * 60)
    print('全流程 case 级四指标（连贯：阶段一产物→阶段二→阶段三）')
    print('=' * 60)
    print(f"输入正样本案例   : {metrics['positive_total_cases']}")
    print(f"完成案例         : {metrics['positive_completed_cases']}")
    print(f"可评测案例       : {metrics['positive_evaluable_cases']}（覆盖率 {metrics['evaluable_coverage']:.1%}）")
    print(f"阻塞案例         : {metrics['positive_blocked_cases']}（阶段一/二阻塞或不可动态表达）")
    w = metrics['wilson95']
    print(f"完成率           : {metrics['completion_rate']:.1%}  (95% CI {w['completion']['lower']:.1%}–{w['completion']['upper']:.1%})")
    print(f"召回率(案例级)   : {metrics['tp_cases']}/{metrics['positive_evaluable_cases']} = {metrics['recall_rate']:.1%}  (95% CI {w['recall']['lower']:.1%}–{w['recall']['upper']:.1%})")
    print(f"准确率           : TP={metrics['tp_cases']} FP={metrics['fp_cases']} TN={metrics['tn_cases']} = {metrics['precision']:.1%}  (95% CI {w['precision']['lower']:.1%}–{w['precision']['upper']:.1%})")
    print(f"  负样本细分     : 主动翻转 {metrics['negative_active_tn_cases']} / 弃权 inconclusive {metrics['negative_inconclusive_cases']}")
    print(f"F1               : {metrics['f1']:.3f}")
    if metrics.get('judge_anchored'):
        ja = metrics['judge_anchored']
        print(f"[判例锚定] 准确率 {ja['precision']:.1%} "
              f"(TP={ja['tp_judge_clean']} FP={ja['fp_judge_invalid']})")
        print(f"[判例锚定] 召回端到端 {ja['recall_end_to_end']:.1%} / "
              f"可评测 {ja['recall_evaluable']:.1%}")
        print(f"[判例锚定] F1 端到端 {ja['f1_end_to_end']:.3f} / "
              f"可评测 {ja['f1_evaluable']:.3f}")
    if metrics['sample_warnings']:
        print('\n[样本量警告]')
        for line in metrics['sample_warnings']:
            print(f'  - {line}')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--positive-eval', type=Path, required=True)
    parser.add_argument('--negative-results', type=Path,
                        help='负样本结果列表；缺省时用 --negative-cases-root 按需生成')
    parser.add_argument('--negative-cases-root', type=Path,
                        help='负样本 case 目录；仅在未提供 --negative-results 时按需生成')
    parser.add_argument('--negative-reuse', action='store_true',
                        help='按需生成负样本时复用缓存（优先终端 verdict）')
    parser.add_argument('--judge-metrics', type=Path, default=None,
                        help='judge_anchored_metrics.json，权威精度/F1 口径')
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args(argv)

    negative_results = args.negative_results
    if negative_results is None:
        if args.negative_cases_root is None:
            parser.error('需要 --negative-results 或 --negative-cases-root 之一')
        cases_root = args.negative_cases_root.resolve()
        negative_results = cases_root.with_name(cases_root.name + '.neg_results.json')
        cmd = [sys.executable, '-m', 'cli.stage3_negative_eval',
               '--cases-root', str(cases_root), '--out', str(negative_results)]
        if args.negative_reuse:
            cmd.append('--reuse')
        print(f'[按需生成负样本] {" ".join(cmd)}')
        proc = subprocess.run(cmd, cwd=str(ROOT))
        if proc.returncode != 0:
            raise SystemExit('按需生成负样本失败')

    pos = json.loads(Path(args.positive_eval).read_text())
    neg = json.loads(Path(negative_results).read_text())
    judge_metrics = None
    if args.judge_metrics:
        judge_metrics = json.loads(Path(args.judge_metrics).read_text())
    metrics = analyze(pos, neg, judge_metrics)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(metrics, ensure_ascii=False, indent=2) + '\n')
    _print(metrics)
    print(f'\nmetrics -> {args.out}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
