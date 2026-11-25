#!/usr/bin/env python3
"""Run the frozen 24-case development regression without LLM calls.

The runner reuses the case's existing stage-2 artifacts and bindings.  It is a
regression gate, not a metric refresh and not a held-out test.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
STAGE3 = HERE.parents[1]
ROOT = STAGE3.parents[1]
DEFAULT_MANIFEST = STAGE3 / 'evaluation' / 'frozen' / 'dev24_20261117.json'
DEFAULT_OUT = HERE / 'dev24_results.json'
UNRESOLVED_VERDICTS = {
    'stage2_restatement_required', 'stage2_review_required',
    'stage2_repair_required', 'stage2_reference_patch_candidate',
    'binding_error', 'binding_failed', 'compile_error', 'partial_binding',
    'inconclusive', 'effect_not_witnessed', 'weak_effect_not_independent',
    'impact_insufficient', 'coding_recipe_required', 'summary_missing',
    'binding_stale', 'reference_patch_required', 'not_dynamically_expressible',
    'poc_not_witnessed', 'preconditions_infeasible_on_code',
    'halt_witness_required', 'patch_no_effect',
}
EXPLICIT_NEGATIVE_VERDICTS = {
    'violation_not_reproduced', 'effect_observed_invariant_holds',
    'invariant_holds_on_exploit_path',
}
POSITIVE_TP_TARGET = 0.5


def _case_dir(row: dict) -> Path:
    path = Path(row['case_dir'])
    return path if path.is_absolute() else ROOT / path


def _load_run_summary(claim: dict) -> dict:
    run_id = claim.get('run_id')
    if not run_id:
        return {}
    path = STAGE3 / 'runs' / str(run_id) / 'stage3-summary.json'
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        return {}


def _claim_metric_eligibility(claim: dict) -> dict:
    summary = _load_run_summary(claim)
    gate = (summary.get('execution_gate') or
            summary.get('post_execution_gate') or {})
    eligibility = gate.get('metric_eligibility') or {}
    witness = gate.get('negative_witness') or {}
    return {
        'consistency': bool(eligibility.get('consistency')),
        'vulnerability': bool(eligibility.get('vulnerability')),
        'consistency_only': (bool(eligibility.get('consistency'))
                             and not bool(eligibility.get('vulnerability'))),
        'negative_witness': (bool(eligibility.get('negative'))
                             or bool(witness.get('eligible'))),
        'exclusion_reason': eligibility.get('exclusion_reason'),
        'consistency_exclusion_reason': eligibility.get(
            'consistency_exclusion_reason'),
        'report_impact_sufficiency': gate.get('report_impact_sufficiency'),
        'report_impact_class': gate.get('report_impact_class'),
        'gate_status': gate.get('status'),
        'gate_category': gate.get('category'),
    }


def classify(case: dict, summary: dict | None) -> dict:
    claims = (summary or {}).get('claims') or []
    verdicts = [row.get('consistency_verdict') for row in claims]
    eligibility = [_claim_metric_eligibility(row) for row in claims]
    reproduced = 'violation_reproduced' in verdicts
    consistency_reproduced = any(
        row.get('consistency_verdict') == 'violation_reproduced'
        and eligibility[index].get('consistency')
        for index, row in enumerate(claims))
    vulnerability_reproduced = any(
        row.get('consistency_verdict') == 'violation_reproduced'
        and eligibility[index].get('vulnerability')
        for index, row in enumerate(claims))
    # A negative case with any unresolved claim does not establish a true
    # negative.  In particular, binding/compile failures must never inflate TN.
    unresolved = (not verdicts
                  or any(verdict is None or verdict in UNRESOLVED_VERDICTS
                         for verdict in verdicts))
    witnessed_negative = False
    if case['label'] == 'positive':
        outcome = 'tp' if reproduced else 'fn_unresolved' if unresolved else 'fn'
    else:
        explicit_negative = bool(verdicts) and all(
            verdict in EXPLICIT_NEGATIVE_VERDICTS for verdict in verdicts)
        witnessed_negative = bool(eligibility) and all(
            row.get('negative_witness') for row in eligibility)
        outcome = ('fp' if vulnerability_reproduced else
                   'consistency_fp' if consistency_reproduced else
                   'tn' if (explicit_negative and witnessed_negative
                            and not unresolved) else
                   'unresolved')
    return {'outcome': outcome, 'verdicts': verdicts,
            'unresolved': unresolved, 'reproduced': reproduced,
            'consistency_reproduced': consistency_reproduced,
            'vulnerability_reproduced': vulnerability_reproduced,
            'negative_witness': witnessed_negative,
            'claim_metric_eligibility': eligibility}


def _run_case(case: dict, stamp: str, run_prefix: str = 'dev24',
              timeout: int = 900, stage2_gate_mode: str = 'aplus',
              claim_top_k: int = 3) -> dict:
    case_dir = _case_dir(case)
    bindings = case_dir / 'bindings'
    if not bindings.is_dir():
        return {**case, 'status': 'missing_bindings', 'claims': []}
    prefix = f"{run_prefix}__{case['case_id']}__{stamp}"
    argv = [sys.executable, '-m', 'cli.stage3_multi',
            '--case-dir', str(case_dir),
            '--bindings-dir', str(bindings),
            '--stage2-run', str(case_dir / 'stage2_run'),
            '--run-id-prefix', prefix,
            '--stage2-gate-mode', stage2_gate_mode,
            '--claim-top-k', str(claim_top_k)]
    try:
        proc = subprocess.run(argv, cwd=str(STAGE3), capture_output=True,
                              text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return {**case, 'status': 'timeout', 'claim_count': 0,
                'classification': {
                    'outcome': 'fn_unresolved' if case['label'] == 'positive'
                    else 'unresolved',
                    'verdicts': [], 'unresolved': True, 'reproduced': False,
                }, 'summary': {'ok': 0, 'failed': 1,
                               'detail': f'case timed out after {timeout}s'}}
    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError:
        payload = {'ok': 0, 'failed': 1,
                   'detail': (proc.stderr or proc.stdout or '')[-3000:]}
    classified = classify(case, payload)
    return {**case, 'status': 'done' if proc.returncode == 0 else 'error',
            'run_id_prefix': prefix, 'summary': payload,
            'classification': classified,
            'stderr_tail': (proc.stderr or '')[-1000:]}


def summarize(results: list[dict]) -> dict:
    positives = [row for row in results if row['label'] == 'positive']
    negatives = [row for row in results if row['label'] == 'negative']
    negative_unresolved = [
        row for row in negatives
        if row['classification']['outcome'] == 'unresolved']
    impact_insufficient = [
        row for row in negative_unresolved
        if 'impact_insufficient' in (row['classification'].get('verdicts') or [])]
    return {
        'positive': len(positives),
        'negative': len(negatives),
        'tp': sum(row['classification']['outcome'] == 'tp' for row in positives),
        'fn': sum(row['classification']['outcome'].startswith('fn') for row in positives),
        'fn_unresolved': sum(
            row['classification']['outcome'] == 'fn_unresolved'
            for row in positives),
        'fp': sum(row['classification']['outcome'] == 'fp' for row in negatives),
        'consistency_fp': sum(
            row['classification']['outcome'] == 'consistency_fp'
            for row in negatives),
        'tn': sum(row['classification']['outcome'] == 'tn' for row in negatives),
        'negative_unresolved': sum(
            row['classification']['outcome'] == 'unresolved'
            for row in negatives),
        'negative_impact_insufficient': len(impact_insufficient),
        'negative_other_unresolved': (len(negative_unresolved)
                                      - len(impact_insufficient)),
        'positive_tp_rate': (sum(
            row['classification']['outcome'] == 'tp' for row in positives)
            / len(positives) if positives else 0.0),
    }


def evaluate_gate(summary: dict, results: list[dict], *,
                  baseline_tp: int = 0) -> dict:
    """Evaluate regression safety separately from the absolute 50% target."""
    return {
        'negative_fp_zero': summary.get('fp', 0) == 0,
        'negative_consistency_fp_zero': summary.get('consistency_fp', 0) == 0,
        'negative_all_resolved': summary.get('negative_unresolved', 0) == 0,
        'positive_tp_not_below_baseline': summary.get('tp', 0) >= baseline_tp,
        'all_runs_done': all(row.get('status') == 'done' for row in results),
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument('--out', type=Path, default=DEFAULT_OUT)
    parser.add_argument('--run-id-prefix', default='dev24',
                        help='prefix for generated stage3 run ids')
    parser.add_argument('--no-gate-exit', action='store_true',
                        help='write results but always exit zero')
    parser.add_argument('--concurrency', type=int, default=1,
                        help='number of cases to run in parallel')
    parser.add_argument('--timeout', type=int, default=900,
                        help='per-case subprocess timeout in seconds')
    parser.add_argument('--stage2-gate-mode', choices=('legacy', 'strict', 'aplus'),
                        default='aplus')
    parser.add_argument('--claim-top-k', type=int, default=3,
                        help='top-k Stage-2 invariant claims to execute; 0 keeps all')
    args = parser.parse_args(argv)
    manifest = json.loads(args.manifest.read_text())
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    cases = list(manifest.get('cases', []))
    if args.concurrency <= 1:
        results = [_run_case(case, stamp, args.run_id_prefix, args.timeout,
                             args.stage2_gate_mode, args.claim_top_k)
                   for case in cases]
    else:
        indexed: dict[int, dict] = {}
        with ThreadPoolExecutor(max_workers=args.concurrency) as pool:
            futures = {
                pool.submit(_run_case, case, stamp, args.run_id_prefix,
                            args.timeout, args.stage2_gate_mode,
                            args.claim_top_k): index
                for index, case in enumerate(cases)}
            for future in as_completed(futures):
                indexed[futures[future]] = future.result()
        results = [indexed[index] for index in sorted(indexed)]
    summary = summarize(results)
    baseline_tp = int((manifest.get('baseline') or {}).get('positive_tp') or 0)
    record = {
        'schema_version': 'dev-regression-results/2',
        'manifest': str(args.manifest),
        'created_at': stamp,
        'case_count': len(results),
        'done': sum(row.get('status') == 'done' for row in results),
        'failed': sum(row.get('status') != 'done' for row in results),
        'summary': summary,
        'baseline': {
            'positive_tp': baseline_tp,
            'positive_tp_rate': (baseline_tp / summary['positive']
                                 if summary['positive'] else 0.0),
        },
        'gate': evaluate_gate(summary, results, baseline_tp=baseline_tp),
        'target': {
            'positive_tp_rate': POSITIVE_TP_TARGET,
            'positive_tp_rate_met': summary['positive_tp_rate'] >= POSITIVE_TP_TARGET,
        },
        'results': results,
    }
    args.out.write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({key: record[key] for key in
                      ('case_count', 'done', 'failed', 'summary', 'gate',
                       'target')},
                     ensure_ascii=False, indent=2))
    if args.no_gate_exit:
        return 0
    return 0 if all(record['gate'].values()) else 1


if __name__ == '__main__':
    raise SystemExit(main())
