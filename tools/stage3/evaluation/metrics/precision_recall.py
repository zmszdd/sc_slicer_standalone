#!/usr/bin/env python3
"""Merge positive + negative stage-3 eval results into precision/recall/F1.

Usage (cwd = tools/stage3):
    python evaluation/metrics/precision_recall.py \
        --positive /tmp/eval30.json \
        --negative evaluation/goldset_v2_neg01/pilot_results.json
"""
from __future__ import annotations
import argparse
import json
from collections import Counter


def load_positive(path):
    d = json.load(open(path))
    verdicts = Counter()
    for c in d['cases']:
        for v in (c.get('verdicts') or []):
            verdicts[v if v is not None else 'binding_failed'] += 1
    tp = verdicts.get('violation_reproduced', 0)
    total = sum(verdicts.values())
    verifiable = (tp + verdicts.get('violation_not_reproduced', 0)
                  + verdicts.get('inconclusive', 0))
    return tp, total, verifiable, verdicts


def load_negative(path):
    rows = json.load(open(path))
    fp = sum(1 for r in rows if r.get('verdict') == 'violation_reproduced')
    tn = len(rows) - fp
    return fp, tn, rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--positive', required=True)
    ap.add_argument('--negative', required=True)
    a = ap.parse_args()

    tp, total, verifiable, pos_v = load_positive(a.positive)
    fp, tn, neg_rows = load_negative(a.negative)

    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall_full = tp / total if total else 0.0
    recall_ver = tp / verifiable if verifiable else 0.0
    f1_full = 2 * precision * recall_full / (precision + recall_full) if (precision + recall_full) else 0.0
    f1_ver = 2 * precision * recall_ver / (precision + recall_ver) if (precision + recall_ver) else 0.0

    print('=' * 64)
    print('准确率 / 召回率（正负样本合并）')
    print('=' * 64)
    print(f'正样本: TP={tp}, 总claim={total}, 可验证子集={verifiable}')
    print(f'负样本: FP={fp}, TN={tn} (共 {len(neg_rows)})')
    print()
    print(f'precision(准确率)          = {tp}/{tp+fp} = {precision:.1%}')
    print(f'recall(全分母)             = {tp}/{total} = {recall_full:.1%}')
    print(f'recall(可验证子集)         = {tp}/{verifiable} = {recall_ver:.1%}')
    print(f'F1(全分母)                 = {f1_full:.3f}')
    print(f'F1(可验证子集)             = {f1_ver:.3f}')
    print()
    print('正样本 verdict 分布:')
    for k, v in pos_v.most_common():
        print(f'  {k}: {v}')
    print()
    print('负样本 verdict 分布:')
    for k, v in Counter(r.get('verdict') for r in neg_rows).most_common():
        print(f'  {k}: {v}')


if __name__ == '__main__':
    main()
