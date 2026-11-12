#!/usr/bin/env python3
"""全流程四指标：完成率 / 召回率 / 准确率 / F1。

口径（与 docs/ACCURACY_RECALL_MAINLINE_PLAN.md 一致）：

* 完成率 completion
  - stage2_candidate  = 阶段二产出 >=1 candidate 的报告占比
  - stage2_complete   = 阶段二完整 formalized 报告占比
  - stage3_verifiable = 进入 stage3 且真正跑通差分（reproduced+not_reproduced+inconclusive）的 claim 占比
* 召回率 recall
  - full        = reproduced / 全部正样本 claim
  - verifiable  = reproduced / 可验证子集
  - case_level  = 至少复现一个 claim 的案例 / done 案例
* 准确率 precision = TP / (TP + FP)，FP 来自负样本 goldset
* F1 = 2*P*R/(P+R)，按 full 与 verifiable 两口径各算一次

用法（cwd = tools/stage3）：
    python -m cli.full_metrics \
        --stage2-summary /path/goldset_v2_pos91/SUMMARY.json \
        --positive-eval /tmp/eval30.json \
        --negative-results evaluation/goldset_v2_neg01/neg_results_final.json \
        --out /tmp/full_metrics.json
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

TERMINAL = {'violation_reproduced', 'violation_not_reproduced'}
VERIFIABLE = TERMINAL | {'inconclusive'}


def _read_json(path: Path):
    return json.loads(Path(path).read_text())


def analyze(stage2_summary: Path, positive_eval: Path,
            negative_results: Path) -> dict:
    s2 = _read_json(stage2_summary)
    pos = _read_json(positive_eval)
    neg_rows = _read_json(negative_results)

    # 阶段二完成率
    n_reports = int(s2.get('n_reports') or 0)
    candidate = int(s2.get('at_least_one_candidate') or 0)
    complete = int(s2.get('complete_reports') or 0)

    # 正样本：claim 级与案例级
    verdicts = Counter()
    total_claims = 0
    reproduced_cases = 0
    done_cases = 0
    for row in pos.get('cases', []):
        total_claims += int(row.get('claims') or 0)
        if row.get('status') == 'done':
            done_cases += 1
        for verdict in (row.get('verdicts') or []):
            verdicts[verdict if verdict else 'binding_failed'] += 1
        if int(row.get('reproduced') or 0) > 0:
            reproduced_cases += 1

    tp = verdicts.get('violation_reproduced', 0)
    not_reproduced = verdicts.get('violation_not_reproduced', 0)
    inconclusive = verdicts.get('inconclusive', 0)
    verifiable = tp + not_reproduced + inconclusive

    # 负样本：violation_reproduced 才算 FP
    fp = sum(1 for row in neg_rows if row.get('verdict') == 'violation_reproduced')
    tn = len(neg_rows) - fp

    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall_full = tp / total_claims if total_claims else 0.0
    recall_verifiable = tp / verifiable if verifiable else 0.0
    recall_case = reproduced_cases / done_cases if done_cases else 0.0

    def f1(p, r):
        return 2 * p * r / (p + r) if (p + r) else 0.0

    return {
        'schema_version': 'stage3-full-metrics/1',
        'inputs': {
            'stage2_summary': str(stage2_summary),
            'positive_eval': str(positive_eval),
            'negative_results': str(negative_results),
        },
        'completion': {
            'stage2_candidate_rate': candidate / n_reports if n_reports else 0.0,
            'stage2_complete_rate': complete / n_reports if n_reports else 0.0,
            'stage2_candidate': candidate,
            'stage2_complete': complete,
            'n_reports': n_reports,
            'stage3_verifiable_claims': verifiable,
            'stage3_total_claims': total_claims,
            'stage3_verifiable_rate': verifiable / total_claims if total_claims else 0.0,
        },
        'recall': {
            'tp': tp,
            'total_positive_claims': total_claims,
            'verifiable_subset': verifiable,
            'reproduced_cases': reproduced_cases,
            'done_cases': done_cases,
            'full': recall_full,
            'verifiable': recall_verifiable,
            'case_level': recall_case,
        },
        'precision': {
            'tp': tp,
            'fp': fp,
            'tn': tn,
            'precision': precision,
        },
        'f1': {
            'full': f1(precision, recall_full),
            'verifiable': f1(precision, recall_verifiable),
        },
        'verdict_histogram': dict(verdicts),
    }


def _pct(value: float) -> str:
    return f'{value:.1%}'


def _print(metrics: dict):
    print('=' * 62)
    print('全流程四指标（30 正样本 + 10 负样本，基于已持久化结果）')
    print('=' * 62)
    c = metrics['completion']
    r = metrics['recall']
    p = metrics['precision']
    f = metrics['f1']
    print('完成率')
    print(f"  阶段二候选报告    {c['stage2_candidate']}/{c['n_reports']} = {_pct(c['stage2_candidate_rate'])}")
    print(f"  阶段二完整报告    {c['stage2_complete']}/{c['n_reports']} = {_pct(c['stage2_complete_rate'])}")
    print(f"  阶段三可判定 claim {c['stage3_verifiable_claims']}/{c['stage3_total_claims']} = {_pct(c['stage3_verifiable_rate'])}")
    print('召回率')
    print(f"  全分母       {r['tp']}/{r['total_positive_claims']} = {_pct(r['full'])}")
    print(f"  可验证子集   {r['tp']}/{r['verifiable_subset']} = {_pct(r['verifiable'])}")
    print(f"  案例级       {r['reproduced_cases']}/{r['done_cases']} = {_pct(r['case_level'])}")
    print('准确率')
    print(f"  TP={p['tp']} FP={p['fp']} TN={p['tn']} → precision = {_pct(p['precision'])}")
    print('F1')
    print(f"  全分母口径     {f['full']:.3f}")
    print(f"  可验证子集口径 {f['verifiable']:.3f}")
    print()
    print('正样本 verdict 分布:')
    for verdict, count in sorted(metrics['verdict_histogram'].items(), key=lambda kv: -kv[1]):
        print(f'  {verdict}: {count}')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage2-summary', type=Path, required=True)
    parser.add_argument('--positive-eval', type=Path, required=True)
    parser.add_argument('--negative-results', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args(argv)

    metrics = analyze(args.stage2_summary, args.positive_eval,
                      args.negative_results)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(metrics, ensure_ascii=False, indent=2) + '\n')
    _print(metrics)
    print(f'\nmetrics -> {args.out}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
