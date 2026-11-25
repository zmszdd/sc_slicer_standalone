#!/usr/bin/env python3
"""Authoritative mainline four-metric report on the stratified sample.

This is the single report that answers "what are the overall four metrics".
It consumes the deterministic ``mainline_sample_mini.json`` and the existing
stage-3 run artifacts, and always reports:

* completion over the sampled positive set;
* recall over the evaluated sampled positives only (unevaluated cases are
  excluded from the denominator and reported as a separate coverage field);
* a sample-wide lower-bound recall that still counts unevaluated cases as FN,
  kept only for transparency, never as the headline;
* automatic-recall over the evaluated sampled positives;
* precision over the sampled negatives, in both consistency and vuln口径,
  with Wilson 95% CI.

Full-set numbers from ``fullset_metrics.py`` stay separate: this file is the
sampled generalisation target and does not reuse the dev-105 denominator.
"""
from __future__ import annotations

import json
import math
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
STAGE3 = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(STAGE3))
from metrics_core import ci_interval, cluster_bootstrap_ci, f1
from fullset_metrics import RunIndex, _is_reproduced_summary
from current_denominator import classify_claim, consistency_effect_confirmed
from mainline_backlog import _stage2_failure_label, _stage2_status
from lib import claim_population, revert_witness
from lib.locked_eval import build as build_locked_eval

# Unevaluated positives count toward the completion denominator only when they
# carry one of these clearly-marked stage-2 failure reasons.  ``stage3_ready``
# (nothing attempted yet) and ``stage2_not_attempted`` (no marked cause) are
# excluded so an unrun backlog can never deflate completion.
EXPLICIT_FAILURE_LABELS = {
    'stage2_http_402',
    'core_piv_not_fully_formalized',
    'report_no_marked_impact_section',
    'stage2_failed',
}

MIN_PUBLISHABLE_CONSISTENCY_POSITIVES = 30
MIN_PUBLISHABLE_CONSISTENCY_NEGATIVES = 24
PUBLICATION_MAX_CONSISTENCY_FPR_UPPER_95 = 0.20

SAMPLE = HERE / 'mainline_sample_mini.json'
GT = HERE / 'judge_ground_truth.json'
CURRENT_DENOMINATOR = HERE / 'current_denominator.json'
OUT_JSON = HERE / 'mainline_metrics.json'
OUT_MD = HERE / 'mainline_metrics.md'
RUNS = HERE.parents[1] / 'runs'


def _claim_map() -> dict[str, list[str]]:
    population = claim_population.current_claim_ids(SAMPLE)
    return {case: sorted(ids) for case, ids in population.items()}


def _negative_labels(sample: dict) -> dict[str, dict]:
    labels: dict[str, dict] = {}
    source = sample.get('negative_source')
    if source:
        path = Path(source)
        if path.is_absolute():
            candidates = [path]
        else:
            candidates = [ROOT / path, HERE / path, path]
        pool = {}
        for candidate in candidates:
            if candidate.is_file():
                pool = json.loads(candidate.read_text())
                break
        if not pool:
            raise SystemExit(f'negative source not found: {source}')
        for row in pool.get('selected') or []:
            case = str(row.get('case') or '')
            if case:
                labels[case] = row
        if labels:
            return labels
    ground_truth = json.loads(GT.read_text())
    for row in ground_truth.get('cases') or []:
        if str(row.get('validity') or '').lower() == 'invalid':
            labels[str(row['case'])] = row
    return labels


def _fmt(v):
    return 'n/a' if v is None else f'{v:.4f}'


def _pct(v):
    return 'n/a' if v is None else f'{v:.1%}'


def _case_evidence(index: RunIndex, case: str,
                   claim_ids: list[str], label: str) -> list[dict]:
    """Return only terminal, current-protocol, metric-eligible claim runs.

    Merely having a run directory is not evidence: binding errors, compile
    errors, stale fingerprints and stage-2 gates must stay unresolved.  selecting
    them here would silently turn them into FN/TN.
    """
    by_claim: dict[str, dict] = {}
    for route, summaries in (
            ('auto', index.iter_auto(case)),
            ('refpatch', index.iter_refpatch(case))):
        for summary in summaries:
            claim_id = str(summary.get('claim_id') or '')
            if claim_ids and claim_id not in claim_ids:
                continue
            classified = classify_claim({
                'consistency_verdict': summary.get('consistency_verdict'),
                'summary': summary,
                'label': label,
            })
            if classified['bucket'] != 'eligible_current':
                continue
            eligibility = classified['metric_eligibility']
            if not eligibility.get('consistency'):
                continue
            key = claim_id or f'{route}:{len(by_claim)}'
            raw_reproduced = _is_reproduced_summary(summary)
            evidence = None
            reproduced = raw_reproduced
            gate = (summary.get('execution_gate')
                    or summary.get('post_execution_gate') or {})
            witness = gate.get('negative_witness') or {}
            if (not raw_reproduced
                    and summary.get('consistency_verdict')
                    == 'effect_not_witnessed'):
                run_id = str(summary.get('run_id') or '')
                run_dir = (RUNS / run_id) if run_id else None
                evidence = revert_witness.evaluate(summary, run_dir=run_dir)
                gate_eligibility = (summary.get('metric_eligibility')
                                    or gate.get('metric_eligibility') or {})
                if (evidence.get('eligible')
                        and gate_eligibility.get('vulnerability') is True):
                    reproduced = True
            basis = ('raw' if raw_reproduced else
                     'revert_witness' if reproduced else None)
            effect_confirmed = bool(reproduced or consistency_effect_confirmed(
                summary))
            row = {
                'claim_id': claim_id,
                'route': route,
                'summary': summary,
                'verdict': summary.get('consistency_verdict'),
                'reproduced': reproduced,
                'reproduced_raw': raw_reproduced,
                'reproduction_basis': basis,
                'effect_confirmed': effect_confirmed,
                'revert_witness': evidence,
                'consistency': bool(eligibility.get('consistency')),
                'consistency_override': eligibility.get(
                    'consistency_override'),
                'vulnerability': bool(eligibility.get('vulnerability')),
                'negative_witness': bool(witness.get('eligible')),
            }
            if key not in by_claim or route == 'refpatch':
                by_claim[key] = row
    return list(by_claim.values())


def _project(case: str, gt_row: dict) -> str:
    return str(gt_row.get('project') or case.split('__')[0])


def _bootstrap_ci(rows: list[dict], metric_fn) -> dict:
    low, high = cluster_bootstrap_ci(rows, metric_fn)
    return {
        'low': round(low, 4) if low is not None else None,
        'high': round(high, 4) if high is not None else None,
    }


def _ratio(numerator: int, denominator: int):
    return numerator / denominator if denominator else None


def consistency_fpr_upper_95(false_positives: int, negatives: int) -> float:
    """One-sided Clopper-Pearson upper bound for consistency FP rate."""
    if negatives <= 0:
        return 1.0
    low = 0.0
    high = 1.0
    for _ in range(60):
        midpoint = (low + high) / 2
        tail = sum(
            math.comb(negatives, count)
            * midpoint ** count
            * (1 - midpoint) ** (negatives - count)
            for count in range(false_positives + 1))
        if tail > 0.05:
            low = midpoint
        else:
            high = midpoint
    return (low + high) / 2


def main() -> dict:
    locked = build_locked_eval(
        sample_path=SAMPLE,
        denominator_path=CURRENT_DENOMINATOR,
        provenance_path=HERE / 'provenance_gate.json',
        ground_truth_path=GT,
        root=ROOT)
    if not locked['ready']:
        blockers = '; '.join(locked.get('blockers') or [])
        raise SystemExit(
            'locked evaluation gate is not ready; refusing to refresh '
            f'mainline_metrics: {blockers}')
    sample = json.loads(SAMPLE.read_text())
    gt = json.loads(GT.read_text())
    gt_by_case = {c['case']: c for c in gt['cases']}
    negative_by_case = _negative_labels(sample)
    case_meta = {**negative_by_case, **gt_by_case}
    claims = _claim_map()

    pos_cases = [c for c in sample['positive_cases'] if gt_by_case.get(c)]
    neg_cases = [c for c in sample['negative_cases']
                 if c in negative_by_case]
    index = RunIndex(RUNS, set(pos_cases) | set(neg_cases))

    tp = tp_consistency = tp_auto = tp_refpatch = done = 0
    tp_revert_witness = 0
    status_counter: Counter[str] = Counter()
    pos_evidence: dict[str, list[dict]] = {}
    for case in pos_cases:
        evidence = _case_evidence(index, case, claims.get(case, []), 'positive')
        pos_evidence[case] = evidence
        if evidence:
            done += 1
            if any(row['effect_confirmed'] and row['consistency']
                   for row in evidence):
                tp_consistency += 1
            if any(row['reproduced'] and row['vulnerability']
                   for row in evidence):
                tp += 1
                tp_auto += 1 if any(
                    row['reproduced'] and row['vulnerability']
                    and row['route'] == 'auto' for row in evidence) else 0
                tp_refpatch += 1 if any(
                    row['reproduced'] and row['vulnerability']
                    and row['route'] == 'refpatch' for row in evidence) else 0
                if not any(row.get('reproduced_raw')
                           and row['vulnerability'] for row in evidence):
                    tp_revert_witness += 1
                    status_counter['reproduced_by_revert_witness'] += 1
                status_counter['reproduced'] += 1
            else:
                status_counter['not_reproduced'] += 1
        else:
            status_counter['unevaluated'] += 1

    fp_raw = fp_vuln = neg_done = 0
    negative_witness_eligible = negative_witness_ineligible = 0
    negative_effect_witnessed = 0
    negative_consistency_override = 0
    neg_evidence: dict[str, list[dict]] = {}
    for case in neg_cases:
        evidence = _case_evidence(index, case, claims.get(case, []), 'negative')
        if not evidence:
            continue
        reproduced = any(row['effect_confirmed'] and row['consistency']
                         for row in evidence)
        negative_consistency_override += 1 if any(
            row.get('consistency_override') for row in evidence) else 0
        negative_effect_witnessed += 1 if reproduced else 0
        witnessed = any(row['negative_witness']
                        and not row['effect_confirmed'] for row in evidence)
        if not reproduced and not witnessed:
            negative_witness_ineligible += 1
            continue
        neg_done += 1
        negative_witness_eligible += 1 if witnessed else 0
        neg_evidence[case] = evidence
        if reproduced:
            fp_raw += 1
            fp_vuln += 1 if any(row['reproduced'] and row['vulnerability']
                                for row in evidence) else 0
    fp_impact = fp_raw - fp_vuln
    tn = neg_done - fp_raw

    total = len(pos_cases)
    unevaluated = total - done
    fn = done - tp
    fn_consistency = done - tp_consistency

    explicit_fail_counter: Counter[str] = Counter()
    for case in pos_cases:
        if pos_evidence[case]:
            continue
        status = _stage2_status(case)
        if status is None or status.get('stage2_can_continue') is True:
            continue
        label = _stage2_failure_label(status)
        if label in EXPLICIT_FAILURE_LABELS:
            explicit_fail_counter[label] += 1
    explicit_fail = sum(explicit_fail_counter.values())
    attributable = done + explicit_fail

    recall_e2e = _ratio(tp, done)
    recall_consistency = _ratio(tp_consistency, done)
    recall_sample_wide = _ratio(tp, total)
    recall_auto = _ratio(tp_auto, done)
    precision_consistency = _ratio(tp_consistency, tp_consistency + fp_raw)
    precision_vuln = _ratio(tp, tp + fp_vuln)
    f1_consistency = f1(precision_consistency, recall_consistency)
    recall_consistency_conservative = _ratio(tp_consistency, total)
    f1_consistency_conservative = f1(precision_consistency,
                                     recall_consistency_conservative)
    f1_vuln = f1(precision_vuln, recall_e2e)
    f1_conservative = f1(precision_vuln, recall_sample_wide)
    # The vuln-level matrix excludes impact-insufficient negatives from both
    # the numerator and denominator.  The consistency matrix keeps them as FP.
    accuracy = _ratio(tp + tn, done + neg_done - fp_impact)
    accuracy_consistency = _ratio(tp_consistency + tn, done + neg_done)
    accuracy_consistency_conservative = _ratio(
        tp_consistency + tn, total + neg_done)

    cluster_rows = [
        {
            'case': case,
            'project': _project(case, case_meta[case]),
            'label': 'positive',
            'tp': any(row['reproduced'] and row['vulnerability']
                      for row in pos_evidence[case]),
        }
        for case in pos_cases if pos_evidence[case]
    ]
    cluster_rows += [
        {
            'case': case,
            'project': _project(case, case_meta[case]),
            'label': 'negative',
            'fp': any(row['reproduced'] and row['vulnerability']
                      for row in neg_evidence[case]),
        }
        for case in neg_cases if neg_evidence.get(case)
    ]
    recall_cluster = _bootstrap_ci(
        cluster_rows,
        lambda rows: _ratio(
            sum(1 for row in rows if row['label'] == 'positive' and row['tp']),
            sum(1 for row in rows if row['label'] == 'positive')))
    precision_cluster = _bootstrap_ci(
        cluster_rows,
        lambda rows: _ratio(
            sum(1 for row in rows
                if row['label'] == 'positive' and row['tp']),
            sum(1 for row in rows
                if (row['label'] == 'positive' and row['tp'])
                or (row['label'] == 'negative' and row['fp']))))
    conservative_rows = [
        {
            'case': case,
            'project': _project(case, case_meta[case]),
            'label': 'positive',
            'tp': bool(pos_evidence[case]) and any(
                row['reproduced'] and row['vulnerability']
                for row in pos_evidence[case]),
        }
        for case in pos_cases
    ]
    conservative_rows += [
        {
            'case': case,
            'project': _project(case, case_meta[case]),
            'label': 'negative',
            'fp': any(row['reproduced'] and row['vulnerability']
                      for row in neg_evidence[case]),
        }
        for case in neg_cases if neg_evidence.get(case)
    ]

    def conservative_f1(rows: list[dict]):
        tp_count = sum(1 for row in rows
                       if row['label'] == 'positive' and row['tp'])
        fp_count = sum(1 for row in rows
                       if row['label'] == 'negative' and row['fp'])
        positive_count = sum(1 for row in rows
                             if row['label'] == 'positive')
        return f1(_ratio(tp_count, tp_count + fp_count),
                  _ratio(tp_count, positive_count))

    f1_cluster = _bootstrap_ci(conservative_rows, conservative_f1)

    consistency_rows = [
        {
            'case': case,
            'project': _project(case, case_meta[case]),
            'label': 'positive',
            'tp': any(row['reproduced'] and row['consistency']
                      for row in pos_evidence[case]),
        }
        for case in pos_cases
    ]
    consistency_rows += [
        {
            'case': case,
            'project': _project(case, case_meta[case]),
            'label': 'negative',
            'fp': any(row['reproduced'] and row['consistency']
                      for row in neg_evidence[case]),
        }
        for case in neg_cases if neg_evidence.get(case)
    ]

    def consistency_ratio(rows: list[dict], kind: str):
        positives = [row for row in rows if row['label'] == 'positive']
        negatives = [row for row in rows if row['label'] == 'negative']
        matched = sum(1 for row in positives if row['tp'])
        false_positives = sum(1 for row in negatives if row['fp'])
        true_negatives = len(negatives) - false_positives
        if kind == 'precision':
            return _ratio(matched, matched + false_positives)
        if kind == 'recall':
            return _ratio(matched, len(positives))
        if kind == 'accuracy':
            return _ratio(matched + true_negatives, len(rows))
        return f1(_ratio(matched, matched + false_positives),
                  _ratio(matched, len(positives)))

    precision_consistency_cluster = _bootstrap_ci(
        consistency_rows, lambda rows: consistency_ratio(rows, 'precision'))
    recall_consistency_cluster = _bootstrap_ci(
        consistency_rows, lambda rows: consistency_ratio(rows, 'recall'))
    accuracy_consistency_cluster = _bootstrap_ci(
        consistency_rows, lambda rows: consistency_ratio(rows, 'accuracy'))
    f1_consistency_cluster = _bootstrap_ci(
        consistency_rows, lambda rows: consistency_ratio(rows, 'f1'))

    denominator = {}
    if CURRENT_DENOMINATOR.is_file():
        denominator = json.loads(CURRENT_DENOMINATOR.read_text())
    stale_positive = sum(
        1 for case in pos_cases
        if not pos_evidence[case] and index.done(case))
    stale_negative = sum(
        1 for case in neg_cases
        if not neg_evidence.get(case) and index.done(case))

    consistency_blockers: list[str] = []
    if done < MIN_PUBLISHABLE_CONSISTENCY_POSITIVES:
        consistency_blockers.append(
            'eligible positives below consistency floor: '
            f'{done} < {MIN_PUBLISHABLE_CONSISTENCY_POSITIVES}')
    if neg_done < MIN_PUBLISHABLE_CONSISTENCY_NEGATIVES:
        consistency_blockers.append(
            'evaluated negatives below consistency floor: '
            f'{neg_done} < {MIN_PUBLISHABLE_CONSISTENCY_NEGATIVES}')
    consistency_fpr_upper = consistency_fpr_upper_95(fp_raw, neg_done)
    if (consistency_fpr_upper
            > PUBLICATION_MAX_CONSISTENCY_FPR_UPPER_95 + 1e-9):
        consistency_blockers.append(
            'consistency FPR upper95 above publication cap: '
            f'{consistency_fpr_upper:.1%} > '
            f'{PUBLICATION_MAX_CONSISTENCY_FPR_UPPER_95:.0%}')
    label_review_cases = list((locked.get('label_review') or {}).get('cases')
                              or [])
    if label_review_cases:
        consistency_blockers.append(
            f'label review required for {len(label_review_cases)} negative '
            'case(s)')
    consistency_publishable = not consistency_blockers

    adjudicated_claims = [
        {
            'case': case,
            'claim_id': row.get('claim_id'),
            'verdict': row.get('verdict'),
            'route': row.get('route'),
            'reason': (row.get('revert_witness') or {}).get('reason'),
            'evidence': (row.get('revert_witness') or {}).get('evidence') or {},
        }
        for case in pos_cases for row in pos_evidence[case]
        if row.get('reproduction_basis') == 'revert_witness'
    ]
    out = {
        'schema_version': 'mainline-metrics/5',
        'sample': {
            'source': 'mainline_sample_mini.json',
            'seed': sample.get('seed'),
            'positives': total,
            'negatives': len(neg_cases),
        },
        'coverage': {
            'positives_evaluated': done,
            'positives_unevaluated': unevaluated,
            'positives_stale_runs_excluded': stale_positive,
            'positives_explicit_failure': explicit_fail,
            'positives_explicit_failure_distribution': dict(explicit_fail_counter),
            'positives_not_attributable': total - done - explicit_fail,
            'negatives_evaluated': neg_done,
            'negatives_consistency_eligible': neg_done,
            'negatives_terminal_current': (
                neg_done + negative_witness_ineligible),
            'negatives_witness_eligible': negative_witness_eligible,
            'negatives_witness_ineligible': negative_witness_ineligible,
            'negatives_effect_witnessed': negative_effect_witnessed,
            'negatives_consistency_override': negative_consistency_override,
            'negatives_stale_runs_excluded': stale_negative,
            'tp_auto': tp_auto,
            'tp_reference_patch': tp_refpatch,
            'tp_revert_witness': tp_revert_witness,
        },
        'confusion_matrix': {
            'tp': tp,
            'tp_consistency': tp_consistency,
            'fn': fn,
            'fn_consistency': fn_consistency,
            'unevaluated_positives': unevaluated,
            'fp_raw': fp_raw,
            'fp_vuln': fp_vuln,
            'fp_impact_insufficient': fp_impact,
            'tn': tn,
            'positives_evaluated': done,
            'negatives_evaluated': neg_done,
        },
        'metrics': {
            'completion_rate': round(c, 4) if (c := _ratio(done, attributable)) is not None else None,
            'completion_sample_wide': round(cw, 4) if (cw := _ratio(done, total)) is not None else None,
            'accuracy': round(accuracy, 4) if accuracy is not None else None,
            'accuracy_consistency': round(accuracy_consistency, 4) if accuracy_consistency is not None else None,
            'accuracy_consistency_conservative': (
                round(accuracy_consistency_conservative, 4)
                if accuracy_consistency_conservative is not None else None),
            'recall': round(recall_e2e, 4) if recall_e2e is not None else None,
            'recall_consistency': round(recall_consistency, 4) if recall_consistency is not None else None,
            'recall_consistency_conservative': (
                round(recall_consistency_conservative, 4)
                if recall_consistency_conservative is not None else None),
            'recall_sample_wide': round(recall_sample_wide, 4) if recall_sample_wide is not None else None,
            'recall_automatic': round(recall_auto, 4) if recall_auto is not None else None,
            'precision_consistency': round(precision_consistency, 4) if precision_consistency is not None else None,
            'precision_vuln': round(precision_vuln, 4) if precision_vuln is not None else None,
            'f1_consistency': round(f1_consistency, 4) if f1_consistency is not None else None,
            'f1_consistency_conservative': (
                round(f1_consistency_conservative, 4)
                if f1_consistency_conservative is not None else None),
            'f1_vuln': round(f1_vuln, 4) if f1_vuln is not None else None,
        },
        'canonical_metrics': {
            'scope': 'source-code/report consistency',
            'accuracy': (
                round(accuracy_consistency_conservative, 4)
                if accuracy_consistency_conservative is not None else None),
            'recall': (
                round(recall_consistency_conservative, 4)
                if recall_consistency_conservative is not None else None),
            'precision': (
                round(precision_consistency, 4)
                if precision_consistency is not None else None),
            'f1': (
                round(f1_consistency_conservative, 4)
                if f1_consistency_conservative is not None else None),
            'policy': ('conservative accuracy and recall count unevaluated '
                       'positives as errors/FN; precision is evaluated on '
                       'consistency matrix; TP requires an independent V '
                       'witness; TN requires a negative witness without V'),
        },
        'headline_metrics': {
            'accuracy': round(accuracy, 4) if accuracy is not None else None,
            'recall_conservative': (
                round(recall_sample_wide, 4)
                if recall_sample_wide is not None else None),
            'recall_evaluated': (
                round(recall_e2e, 4) if recall_e2e is not None else None),
            'precision_vuln': (
                round(precision_vuln, 4) if precision_vuln is not None else None),
            'f1_conservative': (
                round(f1_conservative, 4)
                if f1_conservative is not None else None),
            'f1_evaluated': (
                round(f1_vuln, 4) if f1_vuln is not None else None),
            'status': 'legacy vuln companion; canonical_metrics is the paper main table',
            'policy': ('conservative recall counts unevaluated positives as '
                       'FN; evaluated recall stays as a conditional diagnostic'),
        },
        'confidence_intervals': {
            'accuracy': ci_interval(tp + tn, done + neg_done - fp_impact),
            'accuracy_consistency': ci_interval(tp_consistency + tn,
                                                done + neg_done),
            'accuracy_consistency_conservative': ci_interval(
                tp_consistency + tn, total + neg_done),
            'accuracy_consistency_cluster_bootstrap': accuracy_consistency_cluster,
            'recall': ci_interval(tp, done),
            'recall_consistency': ci_interval(tp_consistency, done),
            'recall_consistency_conservative': ci_interval(
                tp_consistency, total),
            'recall_consistency_cluster_bootstrap': recall_consistency_cluster,
            'recall_sample_wide': ci_interval(tp, total),
            'recall_automatic': ci_interval(tp_auto, done),
            'precision_consistency': ci_interval(tp_consistency,
                                                tp_consistency + fp_raw),
            'precision_consistency_cluster_bootstrap': precision_consistency_cluster,
            'precision_vuln': ci_interval(tp, tp + fp_vuln),
            'f1_consistency_cluster_bootstrap': f1_consistency_cluster,
            'recall_cluster_bootstrap': recall_cluster,
            'precision_vuln_cluster_bootstrap': precision_cluster,
            'f1_conservative': f1_cluster,
            'f1_conservative_cluster_bootstrap': f1_cluster,
        },
        'refresh_gate': {
            'source': 'current_denominator.json',
            'refresh_ready': bool(denominator.get('refresh_ready')),
            'locked_ready': bool(locked.get('ready')),
            'publishable': bool(locked.get('publishable')),
            'publication_status': locked.get('publication_status'),
            'publication_blockers': list(
                locked.get('publication_blockers') or []),
            'coverage_gate': locked.get('coverage') or {},
            'dev252_eligible_current': (
                (denominator.get('dev252') or {}).get('counts') or {}).get(
                    'eligible_current'),
        },
        'consistency_gate': {
            'eligible_positive': done,
            'witness_eligible_negative': neg_done,
            'fp_consistency': fp_raw,
            'fpr_upper95': round(consistency_fpr_upper, 4),
            'positive_floor': MIN_PUBLISHABLE_CONSISTENCY_POSITIVES,
            'negative_floor': MIN_PUBLISHABLE_CONSISTENCY_NEGATIVES,
            'publication_max_fpr_upper95': (
                PUBLICATION_MAX_CONSISTENCY_FPR_UPPER_95),
            'publishable': consistency_publishable,
            'publication_status': (
                'publishable' if consistency_publishable
                else 'coverage-limited'),
            'publication_blockers': consistency_blockers,
        },
        'metric_contract': {
            'primary_scope': 'consistency between natural-language claim and source effect',
            'ground_truth_policy': (
                'frozen positive labels are accepted findings; frozen negative '
                'labels are official invalid findings and must additionally '
                'carry a negative witness, or an independent V witness that '
                'constitutes a consistency FP, to enter the matrix'),
            'confusion_matrix': 'consistency-level matrix',
            'accuracy_denominator': ('all sampled positives + evaluated '
                                     'negatives; unevaluated positives are errors'),
            'recall_denominator': 'all sampled positives; unevaluated as FN',
            'precision_denominator': 'TP_consistency + FP_consistency',
            'f1_pairing': 'precision_consistency + conservative recall_consistency',
            'effect_criterion': ('an independent V witness decides consistency; '
                                 'I only decides vulnerability-level outcome'),
            'negative_tn_requires_witness': True,
            'vuln_level_metrics_are_companion_diagnostics': True,
            'coverage_is_separate': True,
        },
        'eligibility_policy': (
            'only fingerprinted, terminal, metric-eligible claim runs enter '
            'the confusion matrix; unresolved and stale runs are excluded. '
            'A negative case without either an eligible negative witness or '
            'an independent V witness stays unresolved and never becomes TN. '
            'A revert-expected effect witness is re-adjudicated only when the '
            'revert is on the exploit path; raw verdicts stay unchanged'),
        'effect_adjudication': {
            'schema_version': revert_witness.SCHEMA_VERSION,
            'policy': revert_witness.POLICY,
            'tp_revert_witness': tp_revert_witness,
            'claims': adjudicated_claims,
            'raw_verdicts_preserved': True,
        },
        'status_distribution': dict(status_counter),
    }
    OUT_JSON.write_text(json.dumps(out, ensure_ascii=False, indent=2) + '\n')

    m = out['metrics']
    headline = out['headline_metrics']
    canonical = out['canonical_metrics']
    cim = out['confidence_intervals']
    consistency_gate = out['consistency_gate']
    md = f"""# 主口径四指标（分层随机抽样）

- 抽样：`mainline_sample_mini.json`，salt `{sample.get('subset_salt')}`；dev252/dev24 与开发负例已排除。
- 入组：仅 fingerprint 匹配当前协议、终态且 `metric_eligibility` 为真的 claim；过期 run 正例 `{stale_positive}`、负例 `{stale_negative}` 已排除。
- refresh gate：`refresh_ready={out['refresh_gate']['refresh_ready']}`，dev252 `eligible_current={out['refresh_gate']['dev252_eligible_current']}`。
- 完成率分母：已评测 `{done}` + 有明确失败归因 `{explicit_fail}`（未跑 `stage3_ready` / 无归因不计入）。
- 召回分母：已评测 positive `{done}`（未评测 `{unevaluated}` 不计入）；negative 已评测 `{neg_done}/{len(neg_cases)}`。
- 一致性发布状态：`{consistency_gate['publication_status']}`；publishable=`{consistency_gate['publishable']}`。
- 一致性 FPR 上界（{consistency_gate['fp_consistency']}/{consistency_gate['witness_eligible_negative']}）：
  {consistency_gate['fpr_upper95']:.1%}，发布上限 {consistency_gate['publication_max_fpr_upper95']:.0%}。
- 负例证据：V witness FP `{negative_effect_witnessed}` / TN witness `{negative_witness_eligible}`。
- 漏洞级伴生发布状态：`{out['refresh_gate']['publication_status']}`；publishable=`{out['refresh_gate']['publishable']}`。
- Revert-witness 重新裁决：{tp_revert_witness} 个 case / {len(adjudicated_claims)} 个 claim；仅接受 revert 发生在漏洞利用路径上的证据，原始 verdict 不变。

| 指标 | 数值 | 95% CI |
| --- | ---: | --- |
| 完成率（已评测+明确失败） | {_pct(m['completion_rate'])} | — |
| 完成率（样本内下界，全部 sampled positives） | {_pct(m['completion_sample_wide'])} | — |
| 准确率（vuln） | {_pct(m['accuracy'])} | {_pct(cim['accuracy']['low'])}–{_pct(cim['accuracy']['high'])} |
| 准确率（consistency） | {_pct(m['accuracy_consistency'])} | {_pct(cim['accuracy_consistency']['low'])}–{_pct(cim['accuracy_consistency']['high'])} |
| 召回率（已评测口径） | {_pct(m['recall'])} | {_pct(cim['recall']['low'])}–{_pct(cim['recall']['high'])} |
| 召回率（项目聚类 bootstrap） | — | {_pct(cim['recall_cluster_bootstrap']['low'])}–{_pct(cim['recall_cluster_bootstrap']['high'])} |
| 召回率（样本内下界，未评测计 FN） | {_pct(m['recall_sample_wide'])} | {_pct(cim['recall_sample_wide']['low'])}–{_pct(cim['recall_sample_wide']['high'])} |
| 召回率（自动口径，已评测） | {_pct(m['recall_automatic'])} | {_pct(cim['recall_automatic']['low'])}–{_pct(cim['recall_automatic']['high'])} |
| 精确率（vuln，对外主口径） | {_pct(m['precision_vuln'])} | {_pct(cim['precision_vuln']['low'])}–{_pct(cim['precision_vuln']['high'])} |
| 精确率（项目聚类 bootstrap） | — | {_pct(cim['precision_vuln_cluster_bootstrap']['low'])}–{_pct(cim['precision_vuln_cluster_bootstrap']['high'])} |
| 精确率（consistency，机制一致性） | {_pct(m['precision_consistency'])} | {_pct(cim['precision_consistency']['low'])}–{_pct(cim['precision_consistency']['high'])} |
| F1（vuln，已评测口径） | {_fmt(m['f1_vuln'])} | — |
| F1（保守，项目聚类 bootstrap） | — | {_pct(cim['f1_conservative_cluster_bootstrap']['low'])}–{_pct(cim['f1_conservative_cluster_bootstrap']['high'])} |

## 主表推荐四指标（保守口径）

| 指标 | 数值 | 95% CI |
| --- | ---: | --- |
| 准确率（consistency，保守） | {_pct(canonical['accuracy'])} | {_pct(cim['accuracy_consistency_conservative']['low'])}–{_pct(cim['accuracy_consistency_conservative']['high'])} |
| 召回率（consistency，保守） | {_pct(canonical['recall'])} | {_pct(cim['recall_consistency_conservative']['low'])}–{_pct(cim['recall_consistency_conservative']['high'])} |
| 精确率（consistency，已评测） | {_pct(canonical['precision'])} | {_pct(cim['precision_consistency']['low'])}–{_pct(cim['precision_consistency']['high'])} |
| F1（consistency，保守） | {_fmt(canonical['f1'])} | {_pct(cim['f1_consistency_cluster_bootstrap']['low'])}–{_pct(cim['f1_consistency_cluster_bootstrap']['high'])} |

## 漏洞级伴生四指标（诊断）

| 指标 | 数值 | 95% CI |
| --- | ---: | --- |
| 准确率（vuln，已评测） | {_pct(headline['accuracy'])} | {_pct(cim['accuracy']['low'])}–{_pct(cim['accuracy']['high'])} |
| 召回率（vuln，保守） | {_pct(headline['recall_conservative'])} | {_pct(cim['recall_sample_wide']['low'])}–{_pct(cim['recall_sample_wide']['high'])} |
| 精确率（vuln） | {_pct(headline['precision_vuln'])} | {_pct(cim['precision_vuln']['low'])}–{_pct(cim['precision_vuln']['high'])} |
| F1（vuln，保守） | {_fmt(headline['f1_conservative'])} | {_pct(cim['f1_conservative']['low'])}–{_pct(cim['f1_conservative']['high'])} |

> 一致性主表衡量“自然语言声称效果 ↔ 源码实际效果”；漏洞级四指标只作判例影响口径的伴生诊断。
> 已评测口径 consistency recall={_pct(m['recall_consistency'])}、F1={_fmt(m['f1_consistency'])}
> 保留为条件诊断值；主表采用未评测正例计 FN 的保守口径。
> 一致性 TP/FP 由独立 V witness 决定，I 只用于漏洞级伴生口径。
> 负例 TN 必须满足 `negative_witness.eligible=true` 且没有 V witness；
> 有 V witness 的负例记 consistency FP，无两类证据的终态负例留在 unresolved。

混淆矩阵（已评测口径）：TP {tp} / TP_consistency {tp_consistency} / FN {fn} / 未评测 {unevaluated} / FP_raw {fp_raw}（影响不足 {fp_impact}，vuln {fp_vuln}）/ TN {tn}。

> 口径说明：论文主表使用 `canonical_metrics` 的 consistency 四指标；
> vuln 级 `accuracy` / `recall` / `precision_vuln` / `f1_vuln` 仅作伴生诊断。
> consistency 准确率使用 `(TP_consistency+TN)/(全部 sampled positives+evaluated negatives)`；
> V witness 已见证的负例仍进入 consistency FP，不因影响不足或 I 成立转 TN。
> 完成率分母 = 已评测 `{done}` + 明确失败归因 `{explicit_fail}`；`stage3_ready`
> （未跑完）与 `stage2_not_attempted`（无失败原因）不计入分母。
> `completion_sample_wide` 是按全部 sampled positives 的样本内下界，仅作透明度对照。
> 主表召回与 F1 使用全部 sampled positives 作分母，未评测计 FN；
> `recall` / `f1_vuln` 是已评测 positive 的条件诊断口径，不能替代主表。
"""
    OUT_MD.write_text(md)

    print(f'一致性主表四指标: accuracy={_pct(canonical["accuracy"])} '
          f'recall={_pct(canonical["recall"])} '
          f'precision={_pct(canonical["precision"])} '
          f'F1={_fmt(canonical["f1"])}')
    print(f'漏洞级伴生四指标: completion={_pct(m["completion_rate"])} '
          f'(sample_wide={_pct(m["completion_sample_wide"])}) '
          f'accuracy={_pct(m["accuracy"])} '
          f'recall={_pct(m["recall"])} sample_wide={_pct(m["recall_sample_wide"])} '
          f'precision_vuln={_pct(m["precision_vuln"])}')
    print(f'覆盖: positive evaluated={done}/{total} explicit_fail={explicit_fail} '
          f'stale_excluded={stale_positive} '
          f'negative evaluated={neg_done}/{len(neg_cases)} '
          f'stale_excluded={stale_negative}')
    print(f'混淆: TP={tp} FN={fn} FP_raw={fp_raw} FP_vuln={fp_vuln} TN={tn}')
    return out


if __name__ == '__main__':
    main()
