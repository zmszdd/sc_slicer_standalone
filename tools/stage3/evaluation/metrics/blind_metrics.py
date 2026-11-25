#!/usr/bin/env python3
"""Blind-set four-metric aggregation on the mainline stage-3 eval snapshot.

Same metric semantics as ``unified_metrics.py``, applied to the runnable blind
subset (``blind_goldset/selection.json``, all judge-valid positives):

* completion_rate = stage-3 ``done`` rows / selected runnable cases
* recall          = case-level reproduced / judge-valid positives
* recall_automatic = reproduced without reference-patch routing (assert-injection)
* precision / F1  = undefined until a blind negative set exists (reported null)

The input is the stage-3 eval JSON written by ``cli.stage3_eval_run`` over
``blind_goldset`` + ``blind_flatten_root``.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from metrics_core import completion_rate, f1, recall
SEL = HERE / 'blind_goldset' / 'selection.json'
DEFAULT_EVAL = HERE / 'blind_stage3_eval_20261118.json'
DEFAULT_FULL_SET = HERE / 'blind_set.json'
DEFAULT_HARNESS = HERE / 'blind_poc_harness_status.json'
DEFAULT_NEGATIVE_EVAL = HERE / 'positive_eval_blind_invalid.json'
OUT_JSON = HERE / 'blind_metrics.json'
OUT_MD = HERE / 'blind_metrics.md'


def compute_metrics(rows, selected, full_positives=None,
                   in_scope_positives=None, negative_rows=None):
    """Aggregate recall-side blind metrics on runnable and full-set denominators.

    ``selected`` is the runnable judge-valid subset; ``full_positives`` is the
    full blind judge-valid set (``blind_set.json``).  The runnable-subset recall
    is a conditional metric (only cases that reached stage3); the full-set
    recall is the honest end-to-end metric over every judge-valid blind case,
    including the ones that never became runnable.
    """
    positives = len(selected)
    done = sum(1 for r in rows if r.get('status') == 'done')
    reproduced_cases = {
        r['case'] for r in rows
        if r.get('status') == 'done' and int(r.get('reproduced') or 0) > 0
    }
    reproduced_cases &= set(selected)
    tp = len(reproduced_cases)
    fn = positives - tp
    automatic_cases = {
        r['case'] for r in rows
        if r.get('status') == 'done'
        and int(r.get('automatic_reproduced',
                     r.get('reproduced') or 0) or 0) > 0
    }
    automatic_cases &= set(selected)
    tp_automatic = len(automatic_cases)

    claims_total = sum(r.get('claims', 0) for r in rows)
    claims_reproduced = sum(int(r.get('reproduced') or 0) for r in rows)
    claim_recall = recall(claims_reproduced, claims_total)

    no_stage2 = sum(1 for r in rows if r.get('status') == 'no_stage2_run')
    zero_claims = sum(1 for r in rows if r.get('status') == 'zero_claims')
    stage2_blocked = sum(1 for r in rows if r.get('status') == 'stage2_blocked')

    completion = completion_rate(done, positives)
    runnable_recall = recall(tp, positives)
    recall_full_set = (tp / full_positives
                       if full_positives else None)
    fn_full_set = (full_positives - tp if full_positives is not None else None)
    recall_in_scope = (tp / in_scope_positives
                       if in_scope_positives else None)
    fn_in_scope = (in_scope_positives - tp
                   if in_scope_positives is not None else None)

    fp = None
    tn = None
    precision_vuln = None
    if negative_rows is not None:
        negative_done = [r for r in negative_rows
                         if r.get('status') == 'done']
        fp = sum(1 for r in negative_done
                 if int(r.get('reproduced') or 0) > 0)
        tn = len(negative_done) - fp
        if tp + fp > 0:
            precision_vuln = tp / (tp + fp)
    return {
        'selected_runnable_cases': positives,
        'full_set_positives': full_positives,
        'positives': positives,
        'stage3_done': done,
        'no_stage2_run': no_stage2,
        'zero_claims': zero_claims,
        'stage2_blocked': stage2_blocked,
        'reproduced_cases': sorted(reproduced_cases),
        'automatic_cases': sorted(automatic_cases),
        'tp': tp,
        'tp_automatic': tp_automatic,
        'fn': fn,
        'fn_full_set': fn_full_set,
        'negative_eval_done': (len([r for r in negative_rows
                                      if r.get('status') == 'done'])
                              if negative_rows is not None else None),
        'fp': fp,
        'tn': tn,
        'in_scope_positives': in_scope_positives,
        'recall_in_scope': (round(recall_in_scope, 4)
                            if recall_in_scope is not None else None),
        'fn_in_scope': fn_in_scope,
        'claims_total': claims_total,
        'claims_reproduced': claims_reproduced,
        'claim_recall': round(claim_recall, 4),
        'recall_full_set': (round(recall_full_set, 4)
                            if recall_full_set is not None else None),
        'metrics': {
            'completion_rate': round(completion, 4),
            'recall': round(runnable_recall, 4),
            'recall_automatic': round(recall(tp_automatic, positives), 4),
            'recall_full_set': (round(recall_full_set, 4)
                                if recall_full_set is not None else None),
            'recall_in_scope': (round(recall_in_scope, 4)
                                if recall_in_scope is not None else None),
            'precision_vuln': (round(precision_vuln, 4)
                                if precision_vuln is not None else None),
            'f1': (round(f1(precision_vuln, runnable_recall), 4)
                   if precision_vuln is not None else None),
        },
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--eval', type=Path, default=DEFAULT_EVAL)
    parser.add_argument('--selection', type=Path, default=SEL)
    parser.add_argument('--full-set', type=Path, default=DEFAULT_FULL_SET)
    parser.add_argument('--harness-status', type=Path, default=DEFAULT_HARNESS)
    parser.add_argument('--negative-eval', type=Path,
                        default=DEFAULT_NEGATIVE_EVAL)
    args = parser.parse_args(argv)

    selection = json.loads(args.selection.read_text())
    selected = [row['case'] for row in selection['cases']]

    full_set = json.loads(args.full_set.read_text())
    full_positives = len(full_set['cases'])

    harness = json.loads(args.harness_status.read_text())
    negative_rows = None
    if args.negative_eval.is_file():
        negative_rows = json.loads(args.negative_eval.read_text()).get('cases', [])
    by_action = harness.get('by_action') or {}
    out_of_scope = int(by_action.get('no_poc_code') or 0) \
        + int(by_action.get('fork_rpc') or 0)
    in_scope_positives = full_positives - out_of_scope

    eval_data = json.loads(args.eval.read_text())
    rows = eval_data.get('cases', [])

    agg = compute_metrics(rows, selected, full_positives=full_positives,
                          in_scope_positives=in_scope_positives,
                          negative_rows=negative_rows)
    positives = agg['selected_runnable_cases']
    tp = agg['tp']
    tp_automatic = agg['tp_automatic']
    done = agg['stage3_done']
    runnable_recall = agg['metrics']['recall']
    completion = agg['metrics']['completion_rate']
    claim_recall = agg['claim_recall']
    precision_vuln = agg['metrics']['precision_vuln']
    f1_vuln = agg['metrics']['f1']
    claims_reproduced = agg['claims_reproduced']
    claims_total = agg['claims_total']
    recall_full_set = agg['recall_full_set']
    recall_in_scope = agg['recall_in_scope']

    out = {
        'schema_version': 'blind-metrics/1',
        **agg,
        'note': ('recall is the runnable-subset conditional metric; '
                 'recall_full_set is the end-to-end metric over the full '
                 'blind judge-valid set; recall_in_scope excludes only '
                 'no_poc_code and fork_rpc (mechanically un-runnable). '
                 'precision/F1 are computed over judge-invalid blind cases that '
                 'reached stage3 (see negative_eval_done/fp/tn).'),
        'rows': rows,
    }
    OUT_JSON.write_text(json.dumps(out, ensure_ascii=False, indent=2) + '\n')

    full_recall_txt = (f'{recall_full_set:.1%}（{tp}/{full_positives}）'
                       if recall_full_set is not None else 'n/a')
    in_scope_recall_txt = (f'{recall_in_scope:.1%}（{tp}/{in_scope_positives}）'
                           if recall_in_scope is not None else 'n/a')
    md = [
        '# 盲测指标（可运行子集 + 全量口径）',
        '',
        f'可运行案例 **{positives}**；可复活子集 **{in_scope_positives}**；'
        f'全量盲测 judge-valid 正例 **{full_positives}**；'
        f'stage3 完成 **{done}**；案例级复现 **{tp}**。',
        '',
        '| 指标 | 值 |',
        '| --- | ---: |',
        f'| completion_rate（可运行子集） | {completion:.1%} |',
        f'| recall（可运行子集，案例级） | {runnable_recall:.1%}（{tp}/{positives}） |',
        f'| recall_full_set（端到端，全量） | {full_recall_txt} |',
        f'| recall_in_scope（可复活子集） | {in_scope_recall_txt} |',
        f'| recall_automatic | {tp_automatic / positives:.1%}（{tp_automatic}/{positives}） |',
        f'| precision_vuln | {precision_vuln:.1%}（{tp}/{tp + (agg["fp"] or 0)}） |'
        if precision_vuln is not None else
        '| precision_vuln | n/a（无盲测负样本） |',
        f'| F1 | {f1_vuln:.3f} |' if f1_vuln is not None else
        '| F1 | n/a（无盲测负样本） |',
        f'| claim 级召回 | {claim_recall:.1%}（{claims_reproduced}/{claims_total}） |',
        '',
        '## 结论',
        '',
        'recall（可运行子集）是条件指标，只覆盖进入 stage3 的案例；'
        'recall_in_scope 覆盖可复活子集（排除 no_poc_code 与 fork_rpc）；'
        'recall_full_set 才是覆盖全部盲测 judge-valid 正例的端到端指标。'
        'precision_vuln/F1 基于已跑通 stage3 的 judge-invalid 盲测负样本'
        '（negative_eval_done）计算，随负样本覆盖扩大而更新。',
    ]
    OUT_MD.write_text('\n'.join(md) + '\n')
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
