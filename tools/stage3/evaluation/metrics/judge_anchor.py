#!/usr/bin/env python3
"""判例锚定（judge-anchored）准确率。

主线阶段三裁决的是“代码是否违反报告形式化不变量 I”，不是“报告是不是真漏洞”。
因此对于判例 ``invalid``（报告误写/设计取舍）的 finding，主线会忠实地复现“错误不变量
违背”，在“真漏洞”口径下应计为假阳性 FP。

本脚本把判例真值与评测结果对齐，给出“报告口径”之外的“真漏洞口径”准确率：

* TP_clean：判例 valid/fixed/wontfix 且主线复现（violation_reproduced）。
* FP_judge_invalid：判例 invalid 且主线复现。
* 判例锚定准确率 = TP_clean / (TP_clean + FP_judge_invalid)。

--blind-invalid-eval 可重复传入，用于把独立盲测（全部为判例 invalid 的负样本）中
新出现的 FP 合并进同一口径。
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from lib.verdict_loop import TERMINAL_VERDICTS

VALID_STATES = {'valid', 'fixed', 'wontfix'}
DYNAMIC = tuple(TERMINAL_VERDICTS)
CEILING_VERDICTS = {'reference_patch_required', 'not_dynamically_expressible'}


def _wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    d = 1 + z * z / n
    center = p + z * z / (2 * n)
    m = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((center - m) / d, (center + m) / d)


def load_eval(path: Path | None) -> list[dict]:
    if path is None or not path.is_file():
        return []
    return json.loads(path.read_text()).get('cases', [])


def judge_map(gt_path: Path) -> dict[str, dict]:
    gt = json.loads(gt_path.read_text())
    return {row['case']: row for row in gt.get('cases', [])}


def load_impact_gate(path: Path) -> set[str]:
    """Load auditable case ids whose reproduced invariant violation is judged
    impact-insufficient (e.g. dust/donation griefing DoS), not a mechanical FP."""
    if path is None or not path.is_file():
        return set()
    data = json.loads(path.read_text())
    return {str(c) for c in data.get('cases', [])}


def split_fp(rows: list[dict], impact_gate: set[str]) -> tuple[list[dict], list[dict]]:
    """Split judge-invalid reproduced findings into impact-insufficient vs remaining."""
    impact = [r for r in rows if r.get('case') in impact_gate]
    remaining = [r for r in rows if r.get('case') not in impact_gate]
    return impact, remaining


def ceiling_rows(positive: list[dict], judges: dict[str, dict]) -> list[dict]:
    """Judge-valid FN cases that are pure mechanism-ceiling cases.

    A case is a hard end-to-end ceiling only when *every* claim verdict is
    ``reference_patch_required`` or ``not_dynamically_expressible``. Mixed cases
    that also carry a recoverable claim (``partial_binding``, ``compile_error``,
    ``binding_error``, ``inconclusive``, ...) are recoverable at the case level:
    reproducing any one claim flips the case to TP, so they must not be
    subtracted from ``recoverable_fn``.
    """
    out = []
    for row in positive:
        case = row.get('case')
        if judges.get(case, {}).get('validity') not in VALID_STATES:
            continue
        if int(row.get('reproduced') or 0) > 0:
            continue
        verdicts = [v for v in (row.get('verdicts') or []) if v]
        if not verdicts or any(v in DYNAMIC for v in verdicts):
            continue
        ceiling = sum(1 for v in verdicts if v in CEILING_VERDICTS)
        if ceiling == len(verdicts):
            out.append({'case': case, 'verdicts': verdicts})
    return out


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--judge-ground-truth', type=Path,
                        default=Path(__file__).with_name('judge_ground_truth.json'))
    parser.add_argument('--positive-eval', type=Path,
                        default=Path(__file__).with_name('positive_eval_105.json'))
    parser.add_argument('--blind-invalid-eval', type=Path, action='append', default=[])
    parser.add_argument('--impact-gate', type=Path,
                        default=Path(__file__).with_name('impact_insufficient_cases.json'),
                        help='JSON {"cases": [...]} of impact-insufficient FP case ids.')
    parser.add_argument('--out', type=Path,
                        default=Path(__file__).with_name('judge_anchored_metrics.json'))
    parser.add_argument('--reconcile-runs', action='store_true',
                        help='reconcile positive-eval snapshot against the latest '
                             'stage-3 runs before computing metrics')
    args = parser.parse_args(argv)

    impact_gate = load_impact_gate(args.impact_gate)

    if args.reconcile_runs:
        from lib.metrics_sync import reconcile_positive_eval
        reconcile_positive_eval(Path(__file__).resolve().parents[2] / 'runs',
                                args.positive_eval, args.judge_ground_truth)

    judges = judge_map(args.judge_ground_truth)
    positive = load_eval(args.positive_eval)

    tp_clean = []
    fp_in_pool = []
    invalid_evaluated = []
    invalid_evaluated_blind = []
    for row in positive:
        case = row.get('case')
        j = judges.get(case)
        if j is None:
            continue
        if j.get('validity') == 'invalid' and row.get('reproduced') is not None:
            invalid_evaluated.append(row)
        reproduced = int(row.get('reproduced') or 0) > 0
        if not reproduced:
            continue
        if j.get('validity') == 'invalid':
            fp_in_pool.append({'case': case, 'title': j.get('title')})
        else:
            tp_clean.append({'case': case, 'validity': j.get('validity'),
                             'severity': j.get('severity'),
                             'title': j.get('title')})

    fp_blind = []
    for path in args.blind_invalid_eval:
        for row in load_eval(path):
            if row.get('case') and row.get('reproduced') is not None:
                invalid_evaluated_blind.append(row)
            if int(row.get('reproduced') or 0) > 0:
                fp_blind.append({'case': row.get('case'),
                                 'title': judges.get(row.get('case'), {}).get('title')})

    fp_total = len(fp_in_pool) + len(fp_blind)
    denom = len(tp_clean) + fp_total
    precision = len(tp_clean) / denom if denom else 0.0
    invalid_evaluated_total = len(
        {row['case'] for row in invalid_evaluated + invalid_evaluated_blind
         if row.get('case')})

    # 召回与 F1 必须和精度同一混淆矩阵：相关样本 = 判例 valid/fixed/wontfix 的
    # finding，TP = 判例净化后复现，FN = 其余相关样本。
    judge_valid = [row for row in positive
                   if judges.get(row.get('case'), {}).get('validity') in VALID_STATES]
    judge_valid_dynamic = [row for row in judge_valid
                           if any(v in DYNAMIC for v in (row.get('verdicts') or []))]
    relevant = len(judge_valid)
    relevant_dynamic = len(judge_valid_dynamic)
    recall_e2e = len(tp_clean) / relevant if relevant else 0.0
    recall_evaluable = len(tp_clean) / relevant_dynamic if relevant_dynamic else 0.0
    fn_judge_valid = max(0, relevant - len(tp_clean))
    tn_invalid = max(0, invalid_evaluated_total - fp_total)
    ceiling = ceiling_rows(positive, judges)
    ceiling_count = len(ceiling)
    recoverable_fn = max(0, fn_judge_valid - ceiling_count)
    recall_end_to_end_ceiling = (
        (relevant - ceiling_count) / relevant if relevant else 0.0)
    fp_project_counts = dict(Counter(
        (row['case'].split('__')[0] if '__' in row['case'] else row['case'])
        for row in fp_in_pool + fp_blind))

    fp_impact_insufficient, fp_remaining = split_fp(
        fp_in_pool + fp_blind, impact_gate)
    vuln_denom = len(tp_clean) + len(fp_remaining)
    precision_vuln_level = len(tp_clean) / vuln_denom if vuln_denom else 0.0

    report = {
        'schema_version': 'judge-anchored-metrics/3',
        'positive_cases': len(positive),
        'judge_invalid_evaluated': len(invalid_evaluated),
        'judge_invalid_evaluated_blind': len(invalid_evaluated_blind),
        'judge_invalid_evaluated_total': invalid_evaluated_total,
        'judge_invalid_reproduced_in_pool': len(fp_in_pool),
        'judge_invalid_reproduced_blind': len(fp_blind),
        'tp_clean': len(tp_clean),
        'fp_from_judge_invalid': fp_total,
        'fp_rate_over_invalid_evaluated': (
            fp_total / invalid_evaluated_total if invalid_evaluated_total else 0.0),
        'fp_project_counts': fp_project_counts,
        'precision': precision,
        'precision_ci': _wilson(len(tp_clean), denom),
        'judge_valid_cases': relevant,
        'judge_valid_dynamic': relevant_dynamic,
        'fn_judge_valid': fn_judge_valid,
        'tn_invalid': tn_invalid,
        'recall_end_to_end_ceiling': recall_end_to_end_ceiling,
        'ceiling_count': ceiling_count,
        'ceiling_rows': ceiling,
        'recoverable_fn_count': recoverable_fn,
        'recall_end_to_end': recall_e2e,
        'recall_end_to_end_ci': _wilson(len(tp_clean), relevant),
        'recall_evaluable': recall_evaluable,
        'recall_evaluable_ci': _wilson(len(tp_clean), relevant_dynamic),
        'fp_impact_insufficient_count': len(fp_impact_insufficient),
        'fp_remaining_count': len(fp_remaining),
        'precision_vuln_level': precision_vuln_level,
        'precision_vuln_level_ci': _wilson(len(tp_clean), vuln_denom),
        'tp_rows': tp_clean,
        'fp_in_pool_rows': fp_in_pool,
        'fp_blind_rows': fp_blind,
        'fp_impact_insufficient_rows': fp_impact_insufficient,
        'fp_remaining_rows': fp_remaining,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(f"TP_clean={len(tp_clean)}  FN_judge_valid={fn_judge_valid}  "
          f"FP_judge_invalid={fp_total} (pool={len(fp_in_pool)}, "
          f"blind={len(fp_blind)})  TN_invalid={tn_invalid}")
    print(f"相关样本(判例valid/fixed/wontfix)={relevant}，动态相关={relevant_dynamic}")
    print(f"召回端到端={recall_e2e:.3f} 95%CI=({report['recall_end_to_end_ci'][0]:.3f}, "
          f"{report['recall_end_to_end_ci'][1]:.3f})  可评测={recall_evaluable:.3f}")
    print(f"端到端天花板={recall_end_to_end_ceiling:.3f}  "
          f"(机制天花板 {ceiling_count} 例，可恢复 FN {recoverable_fn})")
    print(f"判例锚定准确率={precision:.3f}  95% CI=({report['precision_ci'][0]:.3f}, "
          f"{report['precision_ci'][1]:.3f})")
    print(f"漏洞级准确率={precision_vuln_level:.3f}  (排除影响不足 FP "
          f"{len(fp_impact_insufficient)}, 剩余 FP {len(fp_remaining)})  "
          f"95% CI=({report['precision_vuln_level_ci'][0]:.3f}, "
          f"{report['precision_vuln_level_ci'][1]:.3f})")
    print(f"json -> {args.out}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
