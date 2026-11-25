#!/usr/bin/env python3
"""Per-case readiness audit for the frozen mainline sample.

This report answers one question for every sampled case: if it is not in the
authoritative confusion matrix, why not?  It is read-only and deliberately
uses the same evidence rule as ``mainline_metrics.py``.

Status vocabulary
-----------------
eligible
    At least one current-protocol, metric-eligible claim run exists.
not_run
    No Stage-3 summary exists for the case.  For negatives, ``reason``
    distinguishes the actionable blocker: ``no_slice``,
    ``zero_claim_stage2`` or ``stage3_ready``.
stage2_blocked
    No Stage-3 summary exists and Stage-2 recorded an explicit blocker.
stale_only
    Runs exist, but every claim is stale or lacks a current fingerprint.
run_unresolved
    A current Stage-3 run exists, but binding/compile/effect evidence is
    insufficient, so the case cannot enter the confusion matrix.
run_nonterminal
    A current Stage-3 run exists but has no terminal verdict.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
STAGE3 = HERE.parents[1]
REPO_ROOT = STAGE3.parents[1]
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
if str(STAGE3) not in sys.path:
    sys.path.insert(0, str(STAGE3))

from current_denominator import classify_claim  # noqa: E402
from fullset_metrics import RunIndex  # noqa: E402
from lib import path_config  # noqa: E402
from mainline_metrics import (  # noqa: E402
    RUNS, SAMPLE, _case_evidence, _claim_map, _negative_labels,
    _stage2_failure_label, _stage2_status)

OUT_JSON = HERE / 'case_readiness.json'
OUT_MD = HERE / 'case_readiness.md'
NEGATIVE_FLATTEN = path_config.negative_flatten_root()
NEGATIVE_GOLDSET = HERE / 'mainline_goldset_1_7_31_neg'


def _next_action(status: str, reason: str) -> str:
    if status == 'eligible':
        return 'none'
    if status == 'not_run':
        if reason == 'no_slice':
            return 'build_negative_witness_slice'
        if reason == 'zero_claim_stage2':
            return 'repair_stage2_zero_claims'
        if reason == 'stage2_needs_impact_review':
            return 'restore_marked_impact_then_rerun_stage2'
        if reason == 'awaiting_stage2':
            return 'run_stage2'
        if reason == 'stage3_ready':
            return 'run_stage3'
        return 'run_stage3'
    if status == 'stage2_blocked':
        return f'fix_stage2_{reason}'
    if status == 'stale_only':
        return 'rerun_with_current_protocol'
    if reason in ('binding_error', 'binding_failed', 'partial_binding'):
        return 'rebind'
    if reason in ('compile_error', 'compile_blocked'):
        return 'repair_harness_then_rerun'
    if reason in ('effect_not_witnessed', 'weak_effect_not_independent',
                  'patch_no_effect'):
        return 'resolve_effect_witness_then_rerun'
    if reason == 'negative_witness_ineligible':
        return 'restore_negative_witness_then_rerun'
    if reason in ('reference_patch_required', 'not_dynamically_expressible'):
        return 'provide_reference_patch'
    if reason.startswith('metric_ineligible:'):
        return 'triage_metric_eligibility'
    if reason.startswith('stage2_'):
        return 'fix_stage2'
    return 'triage_individually'


def _summaries(index: RunIndex, case: str) -> list[dict]:
    return index.iter_auto(case) + index.iter_refpatch(case)


def _negative_slice_ready(case: str, flatten_root: Path) -> bool:
    return (Path(flatten_root) / case / 'contract.flattened.t.sol').is_file()


def _negative_stage2_dir(case: str, goldset_root: Path) -> Path | None:
    """Return the frozen negative Stage-2 directory for *case*, if present."""
    for run_dir in sorted(Path(goldset_root).glob('runs_*')):
        candidate = run_dir / case
        if (candidate / 'stage3-spec.json').is_file():
            return candidate
    return None


def _negative_stage2_source_root(goldset_root: Path) -> Path | None:
    """Resolve the Stage-2 source recorded by the negative goldset manifest."""
    manifest_path = Path(goldset_root) / 'manifest.json'
    try:
        manifest = json.loads(manifest_path.read_text())
    except (OSError, json.JSONDecodeError):
        return None
    source = str(manifest.get('source') or '')
    if not source:
        return None
    source = Path(source)
    if not source.is_absolute():
        source = REPO_ROOT / source
    return source if source.is_dir() else None


def _negative_stage2_reason(case: str, goldset_root: Path) -> str | None:
    """Explain why a sliced negative is not Stage-3 ready.

    A missing slice is upstream of Stage-2 and therefore dominates.  Once a
    slice exists, a present spec with no claims is a Stage-2 repair problem,
    not a missing Stage-3 run.  Keeping these separate prevents a single
    ``no_stage3_run`` bucket from hiding upstream slice/Impact failures behind
    the same label as zero-claim cases that can be retried.
    """
    stage2_dir = _negative_stage2_dir(case, goldset_root)
    if stage2_dir is None:
        source_root = _negative_stage2_source_root(goldset_root)
        if source_root is not None:
            candidate = source_root / case
            try:
                status = json.loads((candidate / 'status.json').read_text())
            except (OSError, json.JSONDecodeError):
                status = {}
            impact_source = status.get('impact_source_status')
            if impact_source and impact_source != 'marked_section_present':
                return 'stage2_needs_impact_review'
        return 'awaiting_stage2'
    try:
        spec = json.loads((stage2_dir / 'stage3-spec.json').read_text())
    except (OSError, json.JSONDecodeError):
        return 'stage2_spec_unreadable'
    claims = spec.get('claims') or []
    if not claims:
        status_path = stage2_dir / 'status.json'
        try:
            status = json.loads(status_path.read_text())
        except (OSError, json.JSONDecodeError):
            status = {}
        if (status.get('impact_source_status')
                and status.get('impact_source_status') != 'marked_section_present'):
            return 'stage2_needs_impact_review'
        return 'zero_claim_stage2'
    eligible = [row for row in claims if isinstance(row, dict)
                and row.get('formalization_status') == 'formalized_candidate']
    if not eligible:
        return 'no_formalized_claim_stage2'
    return 'stage3_ready'


def _classify_unready(case: str, label: str, index: RunIndex) -> tuple[str, str]:
    summaries = _summaries(index, case)
    if not summaries:
        if index.done(case):
            # A run directory exists but no parseable stage3-summary.json was
            # produced.  This is not "not run"; it is an unreadable/stale
            # artifact that must be regenerated under the current protocol.
            return 'stale_only', 'missing_stage3_summary'
        status = _stage2_status(case)
        if status is not None and status.get('stage2_can_continue') is False:
            return 'stage2_blocked', _stage2_failure_label(status)
        if label == 'negative':
            if not _negative_slice_ready(case, NEGATIVE_FLATTEN):
                return 'not_run', 'no_slice'
            reason = _negative_stage2_reason(case, NEGATIVE_GOLDSET)
            if reason is not None:
                return 'not_run', reason
        return 'not_run', 'no_stage3_run'

    verdicts = []
    all_stale = True
    for summary in summaries:
        verdict = str(summary.get('consistency_verdict') or 'missing_verdict')
        verdicts.append(verdict)
        decision = classify_claim({
            'consistency_verdict': verdict,
            'summary': summary,
            'label': label,
        })
        if decision['bucket'] != 'excluded_retry' or not str(
                decision.get('reason') or '').startswith((
                    'stale', 'summary_missing')):
            all_stale = False
        if decision['bucket'] == 'unresolved':
            return 'run_unresolved', decision.get('reason') or verdict
        if decision['bucket'] == 'eligible_current':
            eligibility = decision.get('metric_eligibility') or {}
            if eligibility.get('consistency'):
                return 'eligible', decision.get('reason') or verdict
            return ('run_unresolved',
                    'metric_ineligible:' + str(
                        eligibility.get('exclusion_reason')
                        or verdict or 'unknown'))
    if all_stale:
        return 'stale_only', 'stale_mainline_protocol'
    latest = verdicts[0] if verdicts else 'missing_verdict'
    if latest.startswith('nonterminal_verdict:'):
        return 'run_nonterminal', latest.split(':', 1)[1]
    return 'run_nonterminal', latest


def build(sample_path: Path = SAMPLE, runs_dir: Path = RUNS) -> dict:
    sample = json.loads(sample_path.read_text())
    negative_labels = _negative_labels(sample)
    gt = json.loads((HERE / 'judge_ground_truth.json').read_text())
    gt_by_case = {row['case']: row for row in gt.get('cases') or []}
    positives = [case for case in sample.get('positive_cases') or []
                 if case in gt_by_case]
    negatives = [case for case in sample.get('negative_cases') or []
                 if case in negative_labels]
    claims = _claim_map()
    index = RunIndex(runs_dir, set(positives) | set(negatives))

    rows = []
    for label, cases in (('positive', positives), ('negative', negatives)):
        for case in cases:
            evidence = _case_evidence(index, case, claims.get(case, []), label)
            qualifying = [
                row for row in evidence
                if row.get('effect_confirmed')
                or (row.get('negative_witness')
                    and not row.get('effect_confirmed'))
            ]
            if evidence and label == 'negative' and not qualifying:
                status = 'run_unresolved'
                reason = 'negative_witness_ineligible'
            elif qualifying:
                status = 'eligible'
                reason = str(qualifying[0].get('verdict')
                             or 'metric_eligible')
            else:
                status, reason = _classify_unready(case, label, index)
            rows.append({
                'case': case,
                'label': label,
                'status': status,
                'reason': reason,
                'next_action': _next_action(status, reason),
                'evaluated': status == 'eligible',
                'run_present': index.done(case),
            })

    counts = {
        label: dict(Counter(row['status'] for row in rows
                            if row['label'] == label))
        for label in ('positive', 'negative')
    }
    totals = {
        label: sum(1 for row in rows if row['label'] == label)
        for label in ('positive', 'negative')
    }
    for label in counts:
        counts[label].setdefault('eligible', 0)
    blockers = {
        label: dict(Counter(row['reason'] for row in rows
                            if row['label'] == label
                            and row['status'] != 'eligible'))
        for label in ('positive', 'negative')
    }
    coverage = {
        label: {
            'eligible': counts[label]['eligible'],
            'total': totals[label],
            'coverage': (counts[label]['eligible'] / totals[label]
                         if totals[label] else 0.0),
        }
        for label in ('positive', 'negative')
    }
    return {
        'schema_version': 'case-readiness/2',
        'sample': 'mainline_sample_mini.json',
        'totals': totals,
        'counts': counts,
        'blockers': blockers,
        'coverage': coverage,
        'rows': rows,
        'policy': ('eligible uses the same current-protocol metric evidence as '
                   'mainline_metrics, including negative witness and '
                   'independent effect-witness rules; '
                   'not_run, stage2_blocked, stale_only, '
                   'run_unresolved and run_nonterminal are distinct and none '
                   'of them enter the confusion matrix. Negative not_run '
                   'reasons separate missing slices from Stage-2 zero-claim '
                   'failures and Stage-3-ready cases.'),
    }


def markdown(report: dict) -> str:
    lines = [
        '# 主口径逐例可评测状态审计', '',
        '- 样本：`mainline_sample_mini.json`，40 正例 + 40 负例。',
        '- 判定与 `mainline_metrics.py` 使用同一 current-protocol evidence 规则。',
        '- 未评测案例绝不进入混淆矩阵；这里只解释“为什么未评测”。', '',
        '| 标签 | eligible | total | coverage |',
        '| --- | ---: | ---: | ---: |',
    ]
    for label in ('positive', 'negative'):
        cov = report['coverage'][label]
        lines.append(f"| {label} | {cov['eligible']} | {cov['total']} | "
                     f"{cov['coverage']:.1%} |")
    lines += ['', '| 标签 | status | cases |', '| --- | --- | ---: |']
    for label in ('positive', 'negative'):
        for status, count in sorted(report['counts'][label].items()):
            lines.append(f'| {label} | `{status}` | {count} |')
    lines += ['', '## 未评测阻塞原因', '',
              '| 标签 | reason | cases |', '| --- | --- | ---: |']
    for label in ('positive', 'negative'):
        for reason, count in sorted(report['blockers'][label].items()):
            lines.append(f'| {label} | `{reason}` | {count} |')
    lines += ['', '## 逐例明细', '',
              '| case | label | status | reason | next_action |',
              '| --- | --- | --- | --- | --- |']
    for row in report['rows']:
        lines.append(
            f"| {row['case']} | {row['label']} | `{row['status']}` | "
            f"`{row['reason']}` | `{row['next_action']}` |")
    return '\n'.join(lines) + '\n'


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out-json', type=Path, default=OUT_JSON)
    parser.add_argument('--out-md', type=Path, default=OUT_MD)
    args = parser.parse_args(argv)
    report = build()
    args.out_json.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    args.out_md.write_text(markdown(report))
    print(json.dumps({
        'totals': report['totals'],
        'counts': report['counts'],
        'coverage': report['coverage'],
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
