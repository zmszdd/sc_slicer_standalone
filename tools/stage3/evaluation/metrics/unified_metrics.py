#!/usr/bin/env python3
"""统一口径四指标：同一张判例锚定混淆矩阵上算完成率/召回/准确率/F1。

只读权威数据文件，不再混用“可评测召回(57)”“构造负样本 FP=0”等历史口径。

新增（2026-11-10）：
* 自动口径并入 P2 的语句锚点快照/rebind 复现（不修改合约，仍是 assert 注入）。
* 参考补丁（M1 人工修复）复现单列为上限，不并入自动口径。
"""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
JUDGE = HERE / 'judge_anchored_metrics.json'
FULLFLOW = HERE / 'fullflow_metrics_105_p2b.json'
REFPATCH = HERE / 'reference_patch_reproductions_20261110.json'
P2_AUTO = HERE / 'p2_auto_reproductions_20261110.json'

VALID_STATES = {'valid', 'fixed', 'wontfix'}


def _cases(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    return json.loads(path.read_text()).get('cases', [])


def _f1(precision: float, recall: float) -> float:
    return (2 * precision * recall / (precision + recall)
            if (precision + recall) else 0.0)


def main() -> dict:
    judge = json.loads(JUDGE.read_text())
    ff = json.loads(FULLFLOW.read_text())

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

    # P2 自动复现（语句锚点快照 + rebind，仍走 assert 注入，不修改合约）。
    p2_auto_cases = [r for r in _cases(P2_AUTO)
                     if r.get('verdict') == 'violation_reproduced']
    # judge tp_clean 已经来自 positive_eval_105.json；当 metrics_sync 已把
    # P2 自动复现回填进该快照时，这里只补计尚未回填的案例，避免 double-count。
    tp_rows = {row['case'] for row in judge.get('tp_rows', [])}
    p2_auto_tp = sum(1 for r in p2_auto_cases
                     if r.get('case') in judge_valid_cases
                     and r.get('case') not in tp_rows)

    # M1 参考补丁复现（人工修复合约），单列上限。
    refpatch_cases = [r for r in _cases(REFPATCH)
                      if r.get('verdict') == 'violation_reproduced']
    refpatch_tp = sum(1 for r in refpatch_cases if r.get('case') in judge_valid_cases)

    tp = tp_base + p2_auto_tp
    fn = positives - tp

    completed_rate = float(ff.get('completion_rate', 0.0))
    recall = tp / positives if positives else 0.0
    precision_consistency = tp / (tp + fp) if (tp + fp) else 0.0
    precision_vuln = tp / (tp + fp_vuln) if (tp + fp_vuln) else 0.0
    f1_consistency = _f1(precision_consistency, recall)
    f1_vuln = _f1(precision_vuln, recall)

    # 对外主口径：漏洞级准确率/F1（影响门已剔除 impact-insufficient FP）。
    precision = precision_vuln
    f1 = f1_vuln

    recall_ref = (tp + refpatch_tp) / positives if positives else 0.0
    f1_ref = _f1(precision, recall_ref)

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
        },
        'metrics': {
            'completion_rate': round(completed_rate, 4),
            'recall': round(recall, 4),
            'precision': round(precision, 4),
            'precision_consistency': round(precision_consistency, 4),
            'precision_vuln': round(precision_vuln, 4),
            'f1': round(f1, 4),
            'f1_consistency': round(f1_consistency, 4),
            'f1_vuln': round(f1_vuln, 4),
        },
        'reference_patch_ceiling': {
            'cases': refpatch_cases,
            'tp_added': refpatch_tp,
            'recall': round(recall_ref, 4),
            'f1': round(f1_ref, 4),
        },
    }
    out_path = HERE / 'unified_metrics.json'
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2) + '\n')

    print('混淆矩阵（统一口径，含 P2 自动复现）')
    print(f"  判例有效(+)  : TP={tp}（基线 {tp_base} + P2 {p2_auto_tp}）  FN={fn}  (合计 {positives})")
    print(f"  判例无效(-)  : FP={fp}（影响不足 {fp_impact_insufficient}，漏洞级 {fp_vuln}）  TN={tn}  (可评测 {invalid_evaluated})")
    print('四指标（对外主口径 = 漏洞级准确率/F1）')
    print(f"  完成率 = {completed_rate:.1%}")
    print(f"  召回率 = {recall:.1%}  (TP / 判例有效 = {tp}/{positives})")
    print(f"  准确率 = {precision:.1%}  (漏洞级 TP/(TP+FP_vuln) = {tp}/{tp+fp_vuln})")
    print(f"  F1     = {f1:.3f}")
    print('机制一致性口径（自检）')
    print(f"  一致性准确率 = {precision_consistency:.1%}  (TP/(TP+FP_raw) = {tp}/{tp+fp})")
    print(f"  一致性 F1    = {f1_consistency:.3f}")
    if refpatch_cases:
        print('参考补丁上限（M1 人工修复，单列）')
        print(f"  召回率 = {recall_ref:.1%}  ((TP+{refpatch_tp}) / 判例有效 = {tp+refpatch_tp}/{positives})")
        print(f"  F1     = {f1_ref:.3f}")
    print(f'已写出: {out_path}')
    return out


if __name__ == '__main__':
    main()
