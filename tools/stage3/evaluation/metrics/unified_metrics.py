#!/usr/bin/env python3
"""统一口径四指标：同一张判例锚定混淆矩阵上算完成率/召回/准确率/F1。

只读权威数据文件，不再混用“可评测召回(57)”“构造负样本 FP=0”等历史口径。

新增（2026-11-10）：
* 自动口径并入 P2 的语句锚点快照/rebind 复现（不修改合约，仍是 assert 注入）。
* 参考补丁（M1 人工修复）复现已并入端到端召回（主线 case/patched 差分路由）；
  ``recall_automatic`` 单列自动口径，便于观察机制差异。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from metrics_core import confusion_metrics, completion_rate, recall

JUDGE = HERE / 'judge_anchored_metrics.json'
FULLFLOW = HERE / 'fullflow_metrics_105_p2b.json'
REFPATCH = HERE / 'reference_patch_reproductions_20261110.json'
P2_AUTO = HERE / 'p2_auto_reproductions_20261110.json'

VALID_STATES = {'valid', 'fixed', 'wontfix'}


def _cases(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    return json.loads(path.read_text()).get('cases', [])


def main() -> dict:
    judge = json.loads(JUDGE.read_text())
    positive_eval = json.loads((HERE / 'positive_eval_161.json').read_text())

    tp_base = int(judge['tp_clean'])
    fp = int(judge['fp_from_judge_invalid'])
    positives = int(judge['judge_valid_cases'])
    invalid_evaluated = int(judge.get('judge_invalid_evaluated_total', 0))
    tn = int(judge.get('tn_invalid', invalid_evaluated - fp))
    fp_impact_insufficient = int(judge.get('fp_impact_insufficient_count', 0))
    fp_vuln = max(0, fp - fp_impact_insufficient)

    ground_truth = json.loads((HERE / 'judge_ground_truth.json').read_text())
    judge_valid_cases = {
        row['case'] for row in ground_truth.get('cases', [])
        if row.get('validity') in VALID_STATES
    }

    # P2/参考补丁产物只用于自动口径诊断。 主混淆矩阵的样本资格必须来自
    # positive_eval_161；未进入该快照的案例不能只加 TP 而不加分母。
    p2_auto_cases = [r for r in _cases(P2_AUTO)
                     if r.get('verdict') == 'violation_reproduced']
    positive_eval_cases = {
        row.get('case') for row in positive_eval.get('cases', [])
    }
    tp_rows = {row['case'] for row in judge.get('tp_rows', [])}
    p2_auto_pending = sum(
        1 for r in p2_auto_cases
        if r.get('case') in judge_valid_cases
        and r.get('case') not in positive_eval_cases)
    p2_auto_tp = 0

    # 参考补丁复现已包含在 judge 的 tp_clean 中。 这里只统计其中有多少 TP
    # 来自参考补丁，用于自动口径扣减，不能再次加到主矩阵。
    refpatch_cases = [r for r in _cases(REFPATCH)
                      if r.get('verdict') == 'violation_reproduced']
    refpatch_tp = sum(1 for r in refpatch_cases if r.get('case') in tp_rows)

    tp = tp_base + p2_auto_tp
    fn = positives - tp

    positive_cases = positive_eval.get('cases', [])
    total_input = len(positive_cases)
    done_cases = sum(1 for row in positive_cases if row.get('status') == 'done')
    completed_rate = completion_rate(done_cases, total_input)

    automatic_tp = max(0, tp - refpatch_tp)
    block = confusion_metrics(
        tp=tp, fp=fp, fn=fn, tn=tn,
        fp_impact_insufficient=fp_impact_insufficient, fp_vuln=fp_vuln,
        automatic_tp=automatic_tp,
    )
    recall_e2e = block['recall']
    precision = block['precision']
    precision_consistency = block['precision_consistency']
    precision_vuln = block['precision_vuln']
    f1 = block['f1']
    f1_consistency = block['f1_consistency']
    f1_vuln = block['f1_vuln']
    recall_auto = block['recall_automatic']
    f1_auto = block['f1_automatic']

    out = {
        'schema_version': 'unified-metrics/2',
        'fp口径': {
            'note': ('同一判例锚定混淆矩阵上的双口径：'
                     'consistency=机制一致性(含影响不足FP)，'
                     'vuln=漏洞级(剔除影响不足FP，作为对外主口径)'),
            'fp_raw': fp,
            'fp_impact_insufficient': fp_impact_insufficient,
            'fp_vuln': fp_vuln,
        },
        'confusion_matrix': {
            'tp': tp, 'fp': fp, 'fn': fn, 'tn': tn,
            'judge_valid_total': positives,
            'judge_invalid_evaluated': invalid_evaluated,
            'predicted_positive': tp + fp,
            'tp_base': tp_base,
            'tp_p2_auto_added': p2_auto_tp,
            'tp_p2_auto_pending_snapshot': p2_auto_pending,
            'tp_reference_patch_added': refpatch_tp,
        },
        'metrics': {
            'completion_rate': round(completed_rate, 4),
            'accuracy': block['accuracy'],
            'recall': round(recall_e2e, 4),
            'recall_automatic': round(recall_auto, 4),
            'precision': round(precision, 4),
            'precision_consistency': round(precision_consistency, 4),
            'precision_vuln': round(precision_vuln, 4),
            'f1': round(f1, 4),
            'f1_consistency': round(f1_consistency, 4),
            'f1_vuln': round(f1_vuln, 4),
            'f1_automatic': round(f1_auto, 4),
        },
        'reference_patch_ceiling': {
            'cases': refpatch_cases,
            'tp_added': refpatch_tp,
            'recall_automatic': round(recall_auto, 4),
            'f1_automatic': round(f1_auto, 4),
        },
    }
    out_path = HERE / 'unified_metrics.json'
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2) + '\n')

    print('混淆矩阵（统一口径，含自动 + 参考补丁）')
    print(f"  判例有效(+)  : TP={tp}（基线 {tp_base} + P2 {p2_auto_tp}；参考补丁 {refpatch_tp} 已并入基线）  FN={fn}  (合计 {positives})")
    print(f"  判例无效(-)  : FP={fp}（影响不足 {fp_impact_insufficient}，漏洞级 {fp_vuln}）  TN={tn}  (可评测 {invalid_evaluated})")
    print('四指标（标准分母；精确率/F1 使用漏洞级口径）')
    print(f"  完成率 = {completed_rate:.1%}")
    print(f"  准确率 = {block['accuracy']:.1%}  ((TP+TN)/(TP+FP+FN+TN) = {tp + tn}/{tp + fp + fn + tn})")
    print(f"  召回率 = {recall_e2e:.1%}  (端到端，含参考补丁：{tp}/{positives}；自动口径 {recall_auto:.1%})")
    print(f"  精确率 = {precision:.1%}  (漏洞级 TP/(TP+FP_vuln) = {tp}/{tp+fp_vuln})")
    print(f"  F1     = {f1:.3f}")
    print('机制一致性口径（自检）')
    print(f"  一致性准确率 = {precision_consistency:.1%}  (TP/(TP+FP_raw) = {tp}/{tp+fp})")
    print(f"  一致性 F1    = {f1_consistency:.3f}")
    if refpatch_cases:
        print('参考补丁（已并入端到端召回）')
        print(f"  自动口径召回 = {recall_auto:.1%}  ({(tp-refpatch_tp)}/{positives})")
        print(f"  自动口径 F1  = {f1_auto:.3f}")
    print(f'已写出: {out_path}')
    return out


if __name__ == '__main__':
    main()
