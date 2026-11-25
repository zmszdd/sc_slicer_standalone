#!/usr/bin/env python3
"""Read-only audit of the proposed revert-witness effect policy.

A revert-expected PoC asserts the hazard with ``vm.expectRevert``.  The current
execution gate still asks for a separate effect probe and therefore records
``effect_not_witnessed``.  This audit identifies existing runs that would flip
to ``violation_reproduced`` under the proposed rule:

* raw verdict was ``violation_reproduced``;
* the PoC originally passed (the expected revert was observed);
* the patched project failed with the invariant marker;
* the patched source contains the revert-witness injection
  (``stage3_ok`` / ``stage3_ret``);
* the recorded witness says ``invariant_contradicted``;
* the reverting call is the claim's patched vulnerable operation itself;
* the run is vulnerability-metric eligible.

A revert used as a setup guard, a safe-behaviour check, or a downstream effect
is rejected.  It never rewrites run summaries or authoritative metrics.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
STAGE3 = HERE.parents[1]
if str(STAGE3) not in sys.path:
    sys.path.insert(0, str(STAGE3))

from fullset_metrics import RunIndex  # noqa: E402
from lib import revert_witness  # noqa: E402
from mainline_metrics import (  # noqa: E402
    GT, RUNS, SAMPLE, _claim_map, _negative_labels)

OUT_JSON = HERE / 'effect_witness_reaudit.json'
OUT_MD = HERE / 'effect_witness_reaudit.md'
METRICS = HERE / 'mainline_metrics.json'


def candidate(summary: dict, run_dir: Path) -> dict | None:
    """Return an evidence row when the run applies to the revert policy."""
    decision = revert_witness.evaluate(summary, run_dir=run_dir)
    if not decision.get('applies'):
        return None
    gate = summary.get('execution_gate') or {}
    eligibility = (summary.get('metric_eligibility')
                   or gate.get('metric_eligibility') or {})
    metric_eligible = bool(eligibility.get('vulnerability'))
    return {
        'case': summary.get('case'),
        'run_id': summary.get('run_id'),
        'claim_id': summary.get('claim_id'),
        'current_verdict': summary.get('consistency_verdict'),
        'raw_verdict': summary.get('raw_consistency_verdict'),
        'impact_class': summary.get('impact_class'),
        'impact_sufficiency': summary.get('impact_sufficiency'),
        'metric_eligible': metric_eligible,
        'policy_eligible': bool(decision.get('eligible')),
        'eligible': bool(decision.get('eligible')) and metric_eligible,
        'reason': decision.get('reason'),
        'evidence': decision.get('evidence') or {},
    }


def _metrics_digest() -> str | None:
    try:
        return hashlib.sha256(METRICS.read_bytes()).hexdigest()
    except OSError:
        return None


def build(sample_path: Path = SAMPLE, runs_dir: Path = RUNS) -> dict:
    sample = json.loads(sample_path.read_text())
    gt = {row['case']: row for row in
          json.loads(GT.read_text()).get('cases') or []}
    positives = [case for case in sample.get('positive_cases') or []
                 if case in gt]
    negatives = [case for case in sample.get('negative_cases') or []
                 if case in _negative_labels(sample)]
    index = RunIndex(runs_dir, set(positives) | set(negatives))
    claims = _claim_map()
    rows = []
    for case in positives:
        seen_claims: set[str] = set()
        claim_ids = set(claims.get(case) or [])
        for latest in index.iter_auto(case):
            claim_id = str(latest.get('claim_id') or '')
            if claim_ids and claim_id not in claim_ids:
                continue
            if claim_id in seen_claims:
                continue
            seen_claims.add(claim_id)
            run_dir = Path(runs_dir) / str(latest.get('run_id') or '')
            row = candidate(latest, run_dir)
            if row is not None:
                row['case'] = case
                rows.append(row)

    metrics = {}
    if METRICS.is_file():
        metrics = json.loads(METRICS.read_text())
    matrix = metrics.get('confusion_matrix') or {}
    effective_tp = int(matrix.get('tp') or 0)
    fn = int(matrix.get('fn') or 0)
    tn = int(matrix.get('tn') or 0)
    fp_vuln = int(matrix.get('fp_vuln') or 0)
    tp_revert_witness = int((metrics.get('coverage') or {}).get(
        'tp_revert_witness') or 0)
    raw_tp = max(0, effective_tp - tp_revert_witness)
    positives_evaluated = int(matrix.get('positives_evaluated')
                              or (effective_tp + fn))
    vuln_negatives = fp_vuln + tn
    eligible_rows = [row for row in rows if row['eligible']]
    eligible_cases = sorted({row['case'] for row in eligible_rows})
    flips = len(eligible_cases)
    projected_tp = raw_tp + flips
    projected_recall_den = positives_evaluated
    projected_accuracy_den = positives_evaluated + vuln_negatives
    return {
        'schema_version': 'effect-witness-reaudit/2',
        'policy': revert_witness.POLICY,
        'policy_description': (
            'a revert-expected effect witness is accepted only when the '
            'reverting call is the patched vulnerable operation itself and '
            'the run is vulnerability-metric eligible'),
        'authoritative_metrics_untouched': True,
        'metrics_sha256_before': _metrics_digest(),
        'candidates': rows,
        'candidate_count': len(rows),
        'policy_eligible_count': sum(1 for row in rows
                                     if row['policy_eligible']),
        'eligible_candidate_count': len(eligible_rows),
        'eligible_case_count': flips,
        'eligible_cases': eligible_cases,
        'projection': {
            'raw_tp_before_policy': raw_tp,
            'effective_tp_in_metrics': effective_tp,
            'tp_already_adjudicated': tp_revert_witness,
            'eligible_cases_to_adjudicate': flips,
            'projected_tp': projected_tp,
            'raw_recall_before_policy': (raw_tp / projected_recall_den
                                         if projected_recall_den else None),
            'projected_recall': (projected_tp / projected_recall_den
                                 if projected_recall_den else None),
            'raw_accuracy_before_policy': ((raw_tp + tn)
                                           / projected_accuracy_den
                                           if projected_accuracy_den else None),
            'projected_accuracy': ((projected_tp + tn)
                                   / projected_accuracy_den
                                   if projected_accuracy_den else None),
            'precision_vuln': 1.0 if fp_vuln == 0 else None,
            'projection_matches_integrated_metrics': (
                effective_tp == projected_tp),
        },
        'next_step': ('The metric layer now integrates this report-only '
                      'policy.  Moving the same adjudication into execution '
                      'requires a PROTOCOL_VERSION bump and rerun.'),
    }


def markdown(report: dict) -> str:
    rows = report['candidates']
    proj = report['projection']
    lines = [
        '# Revert-witness effect policy re-audit', '',
        '> Read-only.  Authoritative metrics are not rewritten by this audit.',
        '',
        f"- applied candidates: **{report['candidate_count']}**",
        f"- policy-eligible: **{report['policy_eligible_count']}**",
        f"- metric-eligible candidates: **{report['eligible_candidate_count']}**",
        f"- eligible cases (TP projection): **{report['eligible_case_count']}**",
        f"- raw TP before policy: {proj['raw_tp_before_policy']}",
        f"- TP already adjudicated in metrics: {proj['tp_already_adjudicated']}",
        f"- projected TP: {proj['projected_tp']} "
        f"(matches integrated metrics: "
        f"{proj['projection_matches_integrated_metrics']})",
        f"- recall: {proj['raw_recall_before_policy']:.1%} -> "
        f"{proj['projected_recall']:.1%}",
        f"- accuracy: {proj['raw_accuracy_before_policy']:.1%} -> "
        f"{proj['projected_accuracy']:.1%}", '',
        '| case | claim | impact | metric eligible | policy | reason |',
        '| --- | --- | --- | --- | --- | --- |',
    ]
    for row in rows:
        lines.append(
            f"| {row['case']} | `{row['claim_id']}` | "
            f"`{row.get('impact_class') or 'unknown'}` | "
            f"{'yes' if row['metric_eligible'] else 'no'} | "
            f"{'eligible' if row['policy_eligible'] else 'rejected'} | "
            f"`{row['reason']}` |")
    if not rows:
        lines.append('| - | - | - | - | - | none |')
    lines += ['', f"Next: {report['next_step']}", '']
    return '\n'.join(lines)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out-json', type=Path, default=OUT_JSON)
    parser.add_argument('--out-md', type=Path, default=OUT_MD)
    args = parser.parse_args(argv)
    before = _metrics_digest()
    report = build()
    after = _metrics_digest()
    report['metrics_sha256_after'] = after
    report['authoritative_metrics_untouched'] = before == after
    args.out_json.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    args.out_md.write_text(markdown(report))
    print(json.dumps({
        'candidate_count': report['candidate_count'],
        'policy_eligible_count': report['policy_eligible_count'],
        'eligible_candidate_count': report['eligible_candidate_count'],
        'eligible_case_count': report['eligible_case_count'],
        'projection': report['projection'],
        'authoritative_metrics_untouched': report[
            'authoritative_metrics_untouched'],
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
