#!/usr/bin/env python3
"""Rebuild the current evaluation denominator without mixing stale runs.

The four metrics use different standard denominators, but all four must draw
from the same claim population: completed current-protocol runs with resolved
evidence.  Stale, retryable, or unresolved claims are reported in separate
buckets and never converted into TN/FN.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
STAGE3 = HERE.parents[1]
if str(STAGE3) not in sys.path:
    sys.path.insert(0, str(STAGE3))
from lib import claim_population
from fullset_metrics import _is_reproduced_summary

DEFAULT_LEDGER = HERE / 'failure_ledger_252.json'
DEFAULT_DEV24 = HERE / 'dev24_results.json'
DEFAULT_NEGATIVE5 = HERE / 'negative_5_results.json'
DEFAULT_SAMPLE = HERE / 'mainline_sample_mini.json'
DEFAULT_RUNS = STAGE3 / 'runs'
DEFAULT_JSON = HERE / 'current_denominator.json'
DEFAULT_MD = HERE / 'current_denominator.md'

MIN_MAINLINE_POSITIVES = 30
MIN_MAINLINE_NEGATIVES = 8

TERMINAL_VERDICTS = {
    'violation_reproduced',
    'violation_not_reproduced',
    'effect_observed_invariant_holds',
    'invariant_holds_on_exploit_path',
}
UNRESOLVED_VERDICTS = {
    'binding_error', 'binding_failed', 'compile_error', 'partial_binding',
    'inconclusive', 'effect_not_witnessed', 'weak_effect_not_independent',
    'impact_insufficient', 'coding_recipe_required', 'summary_missing',
    'binding_stale', 'reference_patch_required', 'not_dynamically_expressible',
    'poc_not_witnessed', 'preconditions_infeasible_on_code',
    'halt_witness_required', 'patch_no_effect', 'compile_blocked',
    'stage2_restatement_required', 'stage2_review_required',
    'stage2_repair_required', 'stage2_reference_patch_candidate',
}

NEXT_ACTIONS = {
    'stale_or_missing_fingerprint': 'rerun_with_current_mainline_protocol',
    'binding_error': 'repair_binding_then_rerun',
    'partial_binding': 'repair_binding_then_rerun',
    'compile_error': 'repair_harness_then_rerun',
    'compile_blocked': 'repair_harness_then_rerun',
    'stage2_restatement_required': 'restate_stage2_invariant_then_rerun',
    'stage2_review_required': 'provide_stage2_evidence_then_rerun',
    'impact_insufficient': 'trusted_negative_witness_required',
}


def _next_action(bucket: str, reason: str | None) -> str:
    reason = str(reason or '')
    if reason.startswith('stale_protocol_version:'):
        return 'rerun_with_current_mainline_protocol'
    if reason.startswith('nonterminal_verdict:'):
        return 'complete_run_then_rerun'
    return NEXT_ACTIONS.get(reason, (
        'rerun_with_current_mainline_protocol'
        if bucket == 'excluded_retry' else 'resolve_evidence_then_rerun'))


def _execution_gate(summary: dict | None) -> dict:
    summary = summary or {}
    return (summary.get('execution_gate') or
            summary.get('post_execution_gate') or {})


def consistency_effect_confirmed(summary: dict | None) -> bool:
    """Whether an independent probe witnessed the report-claimed effect V.

    The consistency question is whether the source exhibits the effect the
    natural-language report claims.  ``I`` is the report-derived safety
    property used for the vulnerability-level verdict; it must not decide
    whether ``V`` was observed.  A raw differential or an accepted
    revert-witness still counts, and an effect probe counts when it ran on a
    witnessed precondition/transition path.
    """
    summary = summary or {}
    verdict = summary.get('consistency_verdict')
    if verdict not in {'violation_reproduced',
                       'effect_observed_invariant_holds',
                       'invariant_holds_on_exploit_path'}:
        return False
    queries = summary.get('code_query_results')
    if not isinstance(queries, dict):
        witness = summary.get('witness')
        queries = (witness.get('queries') if isinstance(witness, dict)
                   else None) or {}
    effect_probe = ((summary.get('forge') or {}).get('effect') or {})
    witness = summary.get('witness') or {}
    effect_witnessed = (
        str(queries.get('P_and_T') or '').lower() == 'sat'
        and str(queries.get('P_and_T_and_V') or '').lower() == 'sat'
        and (effect_probe.get('status') == 'Success'
             or (isinstance(witness, dict)
                 and bool(witness.get('effect_witnessed')))))
    return bool(_is_reproduced_summary(summary) or effect_witnessed)


def _metric_eligibility(*, summary: dict | None, verdict: str | None,
                        bucket: str) -> dict:
    """Split a consistency result from vulnerability-level eligibility.

    A claim can reproduce the code mechanism while the trusted judge says the
    reported impact is invalid.  That is a consistency false positive, not a
    vulnerability false positive, and it must never be folded into TN.
    """
    gate = _execution_gate(summary)
    eligibility = gate.get('metric_eligibility') or {}
    gated_consistency = bool(eligibility.get('consistency'))
    consistency = gated_consistency
    consistency_override = None
    vulnerability = bool(eligibility.get('vulnerability'))
    negative_witness = bool((gate.get('negative_witness') or {}).get(
        'eligible'))
    reproduced = bool(_is_reproduced_summary(summary))
    effect_confirmed = consistency_effect_confirmed(summary)
    if bucket == 'eligible_current' and not eligibility:
        # Legacy current summaries did not carry the split.  Terminal claims
        # remain consistency-eligible; vulnerability eligibility is granted
        # only to the explicit non-impact-insufficient terminal verdicts.
        consistency = verdict in TERMINAL_VERDICTS
        vulnerability = verdict in TERMINAL_VERDICTS
    elif (bucket == 'eligible_current'
          and verdict in TERMINAL_VERDICTS
          and not consistency):
        # Impact sufficiency is a vulnerability-level gate.  A terminal
        # consistency verdict with an independent V witness is still
        # evidence about report/source agreement, even when the report itself
        # describes a low-impact or donation-only scenario.
        consistency = True
        consistency_override = (eligibility.get('consistency_exclusion_reason')
                                or eligibility.get('exclusion_reason')
                                or 'impact_gate_overridden')
    if bucket != 'eligible_current':
        consistency = False
        vulnerability = False
        negative_witness = False
        reproduced = False
        effect_confirmed = False
        consistency_override = None
    return {
        'consistency': consistency,
        'consistency_override': consistency_override,
        'vulnerability': vulnerability,
        'consistency_only': consistency and not vulnerability,
        'negative_witness_eligible': negative_witness,
        'reproduced': reproduced,
        'effect_confirmed': effect_confirmed,
        'exclusion_reason': eligibility.get('exclusion_reason'),
        'gate_status': gate.get('status'),
        'gate_category': gate.get('category'),
    }


def _load(path: Path) -> dict:
    try:
        return json.loads(Path(path).read_text())
    except (OSError, ValueError):
        return {}


def _current_versions() -> dict[str, str]:
    try:
        from lib import execution_gate, observable_ir, observable_recipes
        return {
            'execution_gate': execution_gate.SCHEMA_VERSION,
            'observable_ir': observable_ir.SCHEMA_VERSION,
            'observable_recipes': observable_recipes.SCHEMA_VERSION,
        }
    except Exception:
        return {}


def _fingerprint(summary: dict | None) -> tuple[bool, str]:
    fingerprint = ((summary or {}).get('artifact_fingerprint') or {})
    if not fingerprint.get('schema_version'):
        return False, 'stale_or_missing_fingerprint'
    from lib import mainline_protocol

    protocol = fingerprint.get('mainline_protocol') or {}
    if not mainline_protocol.is_current_run(protocol):
        return False, 'stale_mainline_protocol'
    current = _current_versions()
    actual = fingerprint.get('protocol_versions') or {}
    stale = [name for name, version in current.items()
             if actual.get(name) != version]
    if stale:
        return False, 'stale_protocol_version:' + ','.join(sorted(stale))
    return True, 'current_protocol'


def classify_claim(claim: dict) -> dict:
    verdict = claim.get('consistency_verdict')
    summary = claim.get('summary')
    label = str(claim.get('label') or '')
    if summary is None and claim.get('summary_path'):
        summary = _load(Path(claim['summary_path']))
    current, provenance_reason = _fingerprint(summary)
    if not current:
        return {
            'bucket': 'excluded_retry',
            'reason': provenance_reason,
            'next_action': _next_action('excluded_retry', provenance_reason),
            'verdict': verdict,
            'metric_eligibility': _metric_eligibility(
                summary=summary, verdict=verdict, bucket='excluded_retry'),
        }
    if verdict in UNRESOLVED_VERDICTS or not verdict:
        if label == 'positive':
            return {
                'bucket': 'eligible_current',
                'reason': 'positive_unresolved_counted_fn',
                'next_action': None,
                'verdict': verdict or 'missing_verdict',
                'metric_eligibility': {
                    'consistency': True,
                    'consistency_override': None,
                    'vulnerability': True,
                    'consistency_only': False,
                    'negative_witness_eligible': True,
                    'reproduced': False,
                    'effect_confirmed': False,
                    'exclusion_reason': None,
                    'gate_status': None,
                    'gate_category': None,
                },
            }
        return {
            'bucket': 'unresolved',
            'reason': verdict or 'missing_verdict',
            'next_action': _next_action('unresolved',
                                        verdict or 'missing_verdict'),
            'verdict': verdict,
            'metric_eligibility': _metric_eligibility(
                summary=summary, verdict=verdict, bucket='unresolved'),
        }
    if verdict not in TERMINAL_VERDICTS:
        return {
            'bucket': 'excluded_retry',
            'reason': f'nonterminal_verdict:{verdict}',
            'next_action': _next_action('excluded_retry',
                                        f'nonterminal_verdict:{verdict}'),
            'verdict': verdict,
            'metric_eligibility': _metric_eligibility(
                summary=summary, verdict=verdict, bucket='excluded_retry'),
        }
    return {
        'bucket': 'eligible_current',
        'reason': 'fingerprinted_terminal_result',
        'next_action': None,
        'verdict': verdict,
        'metric_eligibility': _metric_eligibility(
            summary=summary, verdict=verdict, bucket='eligible_current'),
    }


def _ledger_claims(ledger: dict) -> list[dict]:
    rows = []
    for row in ledger.get('rows') or []:
        summary = _load(Path(row['summary_path'])) if row.get('summary_path') else None
        rows.append({
            'case': row.get('case'),
            'project': row.get('project'),
            'claim_id': row.get('claim_id'),
            'label': 'positive',
            'consistency_verdict': row.get('verdict'),
            'retryable': bool(row.get('retryable')),
            'summary': summary,
            'summary_path': row.get('summary_path'),
        })
    return rows


def _dev24_claims(results: dict) -> list[dict]:
    rows = []
    for case in results.get('results') or []:
        summary = case.get('summary') or {}
        for claim in summary.get('claims') or []:
            run_id = claim.get('run_id')
            summary_path = (STAGE3 / 'runs' / str(run_id) /
                            'stage3-summary.json') if run_id else None
            claim_summary = (_load(summary_path)
                             if summary_path is not None else summary)
            rows.append({
                'case': case.get('case_id'),
                'project': case.get('project'),
                'claim_id': claim.get('claim_id'),
                'label': case.get('label'),
                'consistency_verdict': claim.get('consistency_verdict'),
                'summary': claim.get('summary') or claim_summary,
                'summary_path': str(summary_path) if summary_path else None,
                'case_status': case.get('status'),
            })
    return rows


def _negative5_claims(results: dict) -> list[dict]:
    return _dev24_claims(results)


def _runs_claims(sample: dict, runs_dir: Path,
                 population: dict[str, frozenset[str]] | None = None
                 ) -> list[dict]:
    positive = {str(case) for case in sample.get('positive_cases') or []}
    negative = {str(case) for case in sample.get('negative_cases') or []}
    wanted = positive | negative
    best: dict[tuple[str, str], tuple[float, dict]] = {}
    for summary_path in sorted((Path(runs_dir)).glob('*/stage3-summary.json'),
                               key=lambda path: path.stat().st_mtime):
        summary = _load(summary_path)
        case = Path(str(summary.get('case') or '')).name
        if case not in wanted:
            continue
        claim_id = str(summary.get('claim_id') or '')
        if not claim_allowed(population, case, claim_id):
            continue
        key = (case, claim_id)
        best[key] = (summary_path.stat().st_mtime, {
            'case': case,
            'project': case.split('__')[0],
            'claim_id': claim_id,
            'label': 'positive' if case in positive else 'negative',
            'consistency_verdict': summary.get('consistency_verdict'),
            'summary': summary,
            'summary_path': str(summary_path),
        })
    return [row for _, row in best.values()]


def claim_allowed(population: dict[str, frozenset[str]] | None,
                  case: str, claim_id: str) -> bool:
    """Whether a run claim belongs to the frozen sample claim population.

    Empty or missing frozen claim sets mean this sample case was never
    attempted before.  Its first current-protocol attempt still makes the case
    evaluated; unresolved positives count as FN.  Once a non-empty frozen set
    exists, it is an allowlist and later runs cannot add claims.
    """
    frozen = (population or {}).get(case)
    return not frozen or claim_id in frozen


def metric_eligible_cases(eligible: list[dict]) -> dict[str, set[str]]:
    """Return cases that contribute to the consistency confusion matrix.

    A negative case needs a terminal consistency result and either an eligible
    negative witness or a reproduced effect.  Impact-insufficient terminal
    claims stay visible as eligible_current claims but are not evaluated cases.
    """
    def case_eligible(row: dict, label: str) -> bool:
        eligibility = row.get('metric_eligibility') or {}
        if not eligibility.get('consistency'):
            return False
        if label == 'positive':
            return True
        if eligibility.get('reproduced') or eligibility.get('effect_confirmed'):
            return True
        return (bool(eligibility.get('negative_witness_eligible'))
                and not eligibility.get('effect_confirmed'))

    eligible_cases = {
        label: {row['case'] for row in eligible
                if row.get('label') == label and case_eligible(row, label)}
        for label in ('positive', 'negative')
    }
    return eligible_cases


def build_mainline(sample_path: Path = DEFAULT_SAMPLE,
                   runs_dir: Path = DEFAULT_RUNS) -> dict:
    sample = _load(Path(sample_path))
    population = claim_population.current_claim_ids(Path(sample_path))
    audited = audit(_runs_claims(sample, Path(runs_dir), population))
    eligible = audited['sets']['eligible_current']
    eligible_cases = metric_eligible_cases(eligible)
    stale_claims = sum(
        row['claims'] for row in audited['reasons']
        if row['bucket'] == 'excluded_retry'
        and (row['reason'].startswith('stale')
             or row['reason'] == 'summary_missing'))
    positive_ready = len(eligible_cases['positive']) >= MIN_MAINLINE_POSITIVES
    negative_ready = len(eligible_cases['negative']) >= MIN_MAINLINE_NEGATIVES
    return {
        'sample': str(Path(sample_path)),
        'runs_dir': str(Path(runs_dir)),
        'claims': audited['claims'],
        'counts': audited['counts'],
        'case_counts': {
            'eligible_positive': len(eligible_cases['positive']),
            'eligible_negative': len(eligible_cases['negative']),
            'excluded_stale_claims': stale_claims,
        },
        'reasons': audited['reasons'],
        'refresh_ready': bool(positive_ready and negative_ready),
        'policy': ('Mainline claims are current only when a frozen sample case '
                   'has a fingerprinted terminal stage-3 summary under the '
                   'current protocol; stale runs never enter any metric.'),
    }


def audit(rows: list[dict]) -> dict:
    sets = {'eligible_current': [], 'excluded_retry': [], 'unresolved': []}
    reasons = Counter()
    for row in rows:
        decision = classify_claim(row)
        entry = {**row, **decision}
        entry.pop('summary', None)
        sets[decision['bucket']].append(entry)
        reasons[(decision['bucket'], decision['reason'],
                 decision.get('next_action'))] += 1
    by_case: dict[str, list[dict]] = {}
    for entry in sets['eligible_current'] + sets['excluded_retry'] + \
            sets['unresolved']:
        by_case.setdefault(str(entry.get('case')), []).append(entry)
    case_rows = []
    for case, claims in sorted(by_case.items()):
        buckets = {row['bucket'] for row in claims}
        if 'excluded_retry' in buckets:
            bucket = 'excluded_retry'
        elif 'unresolved' in buckets:
            bucket = 'unresolved'
        else:
            bucket = 'eligible_current'
        case_rows.append({
            'case': case,
            'project': claims[0].get('project'),
            'label': claims[0].get('label'),
            'bucket': bucket,
            'claims': len(claims),
        })
    case_counts = Counter(row['bucket'] for row in case_rows)
    metric_counts = {
        'consistency_eligible': sum(
            row.get('metric_eligibility', {}).get('consistency', False)
            for row in sets['eligible_current']),
        'vulnerability_eligible': sum(
            row.get('metric_eligibility', {}).get('vulnerability', False)
            for row in sets['eligible_current']),
        'consistency_only': sum(
            row.get('metric_eligibility', {}).get('consistency_only', False)
            for row in sets['eligible_current']),
    }
    return {
        'claims': len(rows),
        'cases': len(case_rows),
        'counts': {name: len(values) for name, values in sets.items()},
        'metric_counts': metric_counts,
        'case_counts': {
            name: case_counts.get(name, 0)
            for name in ('eligible_current', 'excluded_retry', 'unresolved')},
        'reasons': [
            {'bucket': bucket, 'reason': reason, 'claims': count,
             'next_action': action}
            for (bucket, reason, action), count in sorted(
                reasons.items(), key=lambda item: (
                    item[0][0], item[0][1], item[0][2] or ''))
        ],
        'sets': sets,
        'case_sets': {
            name: [row for row in case_rows if row['bucket'] == name]
            for name in ('eligible_current', 'excluded_retry', 'unresolved')},
    }


def build(ledger_path: Path, dev24_path: Path, negative5_path: Path,
          sample_path: Path = DEFAULT_SAMPLE,
          runs_dir: Path = DEFAULT_RUNS) -> dict:
    ledger = _ledger_claims(_load(ledger_path))
    dev24 = _dev24_claims(_load(dev24_path))
    negative5 = _negative5_claims(_load(negative5_path))
    mainline_report = build_mainline(Path(sample_path), Path(runs_dir))
    return {
        'schema_version': 'current-denominator/1',
        'inputs': {
            'dev252_ledger': str(ledger_path),
            'dev24_results': str(dev24_path),
            'negative5_results': str(negative5_path),
            'mainline_sample': str(sample_path),
            'stage3_runs': str(runs_dir),
        },
        'policy': {
            'eligible_current': ('fingerprinted current claims: terminal '
                                 'results plus unresolved positives counted '
                                 'as FN; unresolved negatives stay unresolved'),
            'excluded_retry': ('stale provenance, nonterminal, or cases that '
                               'must be rerun; excluded from every standard '
                               'metric denominator'),
            'unresolved': ('binding/compile/impact/evidence gaps; never TN'),
            'metric_rule': ('accuracy, precision, recall and F1 keep their '
                            'standard different denominators, but all draw '
                            'from the same eligible_current claim sets'),
        },
        'dev252': audit(ledger),
        'dev24': audit(dev24),
        'negative5': audit(negative5),
        'mainline': mainline_report,
        'refresh_ready': bool(mainline_report['refresh_ready']),
    }


def markdown(report: dict) -> str:
    lines = ['# 当前分母审计（2026-11-18）', '',
             '四指标仍使用各自标准分母，但分子/样本必须来自同一个 '
             '`eligible_current` 集合。', '',
             '| 数据集 | cases | eligible_current | excluded_retry | unresolved |',
             '| --- | ---: | ---: | ---: | ---: |']
    for name in ('dev252', 'dev24', 'negative5'):
        row = report[name]
        counts = row['case_counts']
        lines.append(
            f"| {name} | {row['cases']} | {counts['eligible_current']} | "
            f"{counts['excluded_retry']} | {counts['unresolved']} |")
    mainline = report.get('mainline') or {}
    mainline_counts = mainline.get('case_counts') or {}
    lines.append(
        f"| mainline | - | {mainline_counts.get('eligible_positive', 0)}"
        f"+{mainline_counts.get('eligible_negative', 0)} | "
        f"{mainline_counts.get('excluded_stale_claims', 0)} | - |")
    lines += ['', f"`refresh_ready`: **{report['refresh_ready']}**", '',
              '## 排除原因', '',
              '| 数据集 | bucket | reason | next_action | claims |',
              '| --- | --- | --- | --- | ---: |']
    for name in ('dev252', 'dev24', 'negative5'):
        for row in report[name]['reasons']:
            lines.append(f"| {name} | {row['bucket']} | `{row['reason']}` | "
                         f"`{row.get('next_action') or '-'}` | "
                         f"{row['claims']} |")
    return '\n'.join(lines) + '\n'


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ledger', type=Path, default=DEFAULT_LEDGER)
    parser.add_argument('--dev24', type=Path, default=DEFAULT_DEV24)
    parser.add_argument('--negative5', type=Path, default=DEFAULT_NEGATIVE5)
    parser.add_argument('--sample', type=Path, default=DEFAULT_SAMPLE)
    parser.add_argument('--runs-dir', type=Path, default=DEFAULT_RUNS)
    parser.add_argument('--out-json', type=Path, default=DEFAULT_JSON)
    parser.add_argument('--out-md', type=Path, default=DEFAULT_MD)
    args = parser.parse_args(argv)
    report = build(args.ledger, args.dev24, args.negative5,
                   sample_path=args.sample, runs_dir=args.runs_dir)
    args.out_json.write_text(json.dumps(report, ensure_ascii=False,
                                        indent=2) + '\n')
    args.out_md.write_text(markdown(report))
    print(json.dumps({name: {
        'cases': report[name]['cases'],
        'case_counts': report[name]['case_counts'],
        'claim_counts': report[name]['counts'],
    }
                      for name in ('dev252', 'dev24', 'negative5')}
                      | {'mainline': report['mainline']['case_counts'],
                         'refresh_ready': report['refresh_ready']},
                     ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
