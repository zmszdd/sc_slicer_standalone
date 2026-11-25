#!/usr/bin/env python3
"""Collect the latest stage-3 run summary per claim into an eval snapshot.

This is a deterministic read-only join.  It never runs forge or a model; it
only consolidates ``tools/stage3/runs/<prefix>__<case>__<claim>__*`` outputs
into the same ``stage3-eval-run/1`` shape consumed by ``blind_stage3_summary``
and ``blind_metrics``.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
STAGE3 = HERE.parents[1]
ROOT = STAGE3.parents[1]
RUNS = STAGE3 / 'runs'
CASES = STAGE3 / 'cases'
DEFAULT_SELECTION = HERE / 'blind_goldset' / 'selection.json'

NEXT_ACTION_BY_VERDICT = {
    'stage2_restatement_required': 'stage2_restate',
    'stage2_review_required': 'stage2_review',
    'stage2_repair_required': 'stage2_repair',
    'stage2_reference_patch_candidate': 'reference_patch',
    'binding_error': 'binding_repair',
    'binding_failed': 'binding_repair',
    'partial_binding': 'binding_repair',
    'compile_error': 'compile_repair',
    'compile_blocked': 'compile_repair',
    'reference_patch_required': 'reference_patch',
    'effect_observed_invariant_holds': 'invariant_restate',
    'effect_not_witnessed': 'evidence_repair',
    'violation_not_reproduced': 'evidence_repair',
    'violation_reproduced': 'none',
}


def _load(path: Path) -> dict:
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return {}


def _next_action(verdict: str | None) -> str:
    if not verdict:
        return 'rerun'
    return NEXT_ACTION_BY_VERDICT.get(verdict, 'triage')


def _latest_run(case: str, claim_id: str, prefix: str) -> dict:
    pattern = f'{prefix}_{case}__{claim_id}__'
    candidates = [
        path for path in RUNS.glob(f'{pattern}*')
        if path.is_dir() and (path / 'stage3-summary.json').is_file()
    ]
    if not candidates:
        return {}
    latest = max(candidates, key=lambda path: path.stat().st_mtime)
    return _load(latest / 'stage3-summary.json')


def _case_row(case: str, prefix: str) -> dict:
    spec = _load(CASES / case / 'stage2_run' / 'stage3-spec.json')
    claims = [row.get('claim_id') for row in spec.get('claims') or []
              if isinstance(row, dict) and row.get('claim_id')]
    verdicts = []
    next_actions = []
    reproduced = 0
    automatic = 0
    reference = 0
    compile_blocked = 0
    compile_error = 0
    failed = 0
    for claim_id in claims:
        summary = _latest_run(case, claim_id, prefix)
        if not summary:
            failed += 1
            verdicts.append(None)
            continue
        verdict = summary.get('consistency_verdict')
        verdicts.append(verdict)
        next_actions.append(_next_action(verdict))
        if verdict == 'violation_reproduced':
            reproduced += 1
            if summary.get('reference_patch_used'):
                reference += 1
            else:
                automatic += 1
        if verdict == 'compile_blocked':
            compile_blocked += 1
        if verdict == 'compile_error':
            compile_error += 1
    return {
        'case': case,
        'status': 'done' if claims and not failed else 'failed',
        'claims': len(claims),
        'claim_ids': claims,
        'verdicts': verdicts,
        'reproduced': reproduced,
        'automatic_reproduced': automatic,
        'reference_patch_reproduced': reference,
        'compile_blocked': compile_blocked,
        'compile_error': compile_error,
        'failed_claims': failed,
        'verdict_counts': {
            key: verdicts.count(key) for key in sorted(set(verdicts))
        },
        'next_actions': {
            key: next_actions.count(key) for key in sorted(set(next_actions))
        },
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--selection', type=Path, default=DEFAULT_SELECTION)
    parser.add_argument('--prefix', default='mainline_gate')
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--cases', default=None,
                        help='comma-separated case ids; default: selection')
    args = parser.parse_args(argv)
    selection = _load(args.selection)
    wanted = set(args.cases.split(',')) if args.cases else None
    rows = []
    for item in selection.get('cases') or []:
        case = item.get('case')
        if not case or (wanted is not None and case not in wanted):
            continue
        rows.append(_case_row(case, args.prefix))
    payload = {
        'schema_version': 'stage3-eval-run/1',
        'source': f'runs/{args.prefix}_*',
        'cases': rows,
        'total_cases': len(rows),
        'done': sum(1 for row in rows if row['status'] == 'done'),
        'zero_claims': sum(1 for row in rows if not row['claims']),
        'reproduced_total': sum(row['reproduced'] for row in rows),
        'automatic_reproduced_total': sum(
            row['automatic_reproduced'] for row in rows),
        'reference_patch_reproduced_total': sum(
            row['reference_patch_reproduced'] for row in rows),
        'compile_blocked_total': sum(row['compile_blocked'] for row in rows),
        'compile_error_total': sum(row['compile_error'] for row in rows),
        'verdict_counts': {
            key: sum(row['verdict_counts'].get(key, 0) for row in rows)
            for key in sorted({key for row in rows
                               for key in row['verdict_counts']})
        },
        'next_actions': {
            key: sum(row['next_actions'].get(key, 0) for row in rows)
            for key in sorted({key for row in rows
                               for key in row['next_actions']})
        },
    }
    args.out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({key: payload[key] for key in (
        'total_cases', 'done', 'zero_claims', 'reproduced_total',
        'automatic_reproduced_total', 'reference_patch_reproduced_total',
        'compile_blocked_total', 'compile_error_total',
        'next_actions')}, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
