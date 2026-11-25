#!/usr/bin/env python3
"""Bounded repair-loop recovery for the dev-105 positive eval.

``positive_eval_105.json`` rows carry ``bound_claim_ids`` (not ``claim_ids``),
so this module maps verdicts to claims through that field and re-runs the
binding-repairable claims through ``cli.stage3_verdict_loop``. It writes a new
eval snapshot so the mainline metrics can be regenerated without mutating the
original artifact.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STAGE3 = HERE.parents[1]
POSITIVE = HERE / 'positive_eval_105.json'
OUT_DEFAULT = HERE / 'positive_eval_105_recovered.json'

FIXABLE_VERDICTS = {
    'partial_binding', 'compile_error', 'binding_error',
    'effect_observed_invariant_holds', 'inconclusive', 'binding_failed',
}


def _fixable_claims(row: dict) -> list[tuple[str, str]]:
    claim_ids = row.get('bound_claim_ids') or row.get('claim_ids') or []
    verdicts = row.get('verdicts') or []
    return [(cid, verdict) for cid, verdict in zip(claim_ids, verdicts)
            if verdict in FIXABLE_VERDICTS]


def _parse_payload(stdout: str) -> dict | None:
    payload = None
    for line in (stdout or '').splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            candidate = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(candidate, dict) and isinstance(candidate.get('claims'), list):
            payload = candidate
    return payload


def _recount(row: dict) -> dict:
    verdicts = row.get('verdicts') or []
    row['reproduced'] = verdicts.count('violation_reproduced')
    row['compile_blocked'] = verdicts.count('compile_blocked')
    row['compile_error'] = verdicts.count('compile_error')
    row['not_dynamically_expressible'] = verdicts.count(
        'not_dynamically_expressible')
    row['reference_patch_required'] = verdicts.count(
        'reference_patch_required')
    row['halt_witness_required'] = verdicts.count('halt_witness_required')
    return row


def recover_case(case: str, row: dict, max_rounds: int = 2) -> dict:
    fixable = _fixable_claims(row)
    if row.get('status') != 'done' or not fixable:
        return row
    case_dir = STAGE3 / 'cases' / case
    if not (case_dir / 'stage2_run').is_dir():
        return row
    argv = ['cli.stage3_verdict_loop', '--case-dir', str(case_dir),
            '--stage2-run', str(case_dir / 'stage2_run'),
            '--max-rounds', str(max_rounds),
            '--claims', ','.join(cid for cid, _ in fixable)]
    proc = subprocess.run([sys.executable, '-m'] + argv, cwd=str(STAGE3),
                          text=True)
    if proc.returncode != 0:
        return row
    payload = _parse_payload(proc.stdout)
    if payload is None:
        return row
    recovered = {}
    for claim_row in payload.get('claims', []):
        cid = claim_row.get('claim_id')
        verdict = claim_row.get('verdict')
        if cid and verdict:
            recovered[cid] = verdict
    if not recovered:
        return row
    claim_ids = row.get('bound_claim_ids') or row.get('claim_ids') or []
    verdicts = row.get('verdicts') or []
    updated = [recovered.get(cid, verdict)
               for cid, verdict in zip(claim_ids, verdicts)]
    row['verdicts'] = updated
    return _recount(row)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--positive-eval', type=Path, default=POSITIVE)
    parser.add_argument('--out', type=Path, default=OUT_DEFAULT)
    parser.add_argument('--max-cases', type=int, default=0)
    parser.add_argument('--max-rounds', type=int, default=2)
    args = parser.parse_args(argv)

    positive = json.loads(args.positive_eval.read_text())
    rows = positive.get('cases', [])
    fixable_cases = [r for r in rows if _fixable_claims(r) and r.get('status') == 'done']
    if args.max_cases > 0:
        fixable_cases = fixable_cases[:args.max_cases]
    print(f'recovering {len(fixable_cases)} cases '
          f'({sum(len(_fixable_claims(r)) for r in fixable_cases)} claims)')

    by_case = {r['case']: r for r in rows}
    for index, row in enumerate(fixable_cases, 1):
        before = dict(row)
        after = recover_case(row['case'], row, max_rounds=args.max_rounds)
        by_case[row['case']] = after
        print(f'[{index}/{len(fixable_cases)}] {row["case"]}: '
              f'{before.get("verdicts")} -> {after.get("verdicts")}',
              flush=True)

    positive['cases'] = [by_case[r['case']] for r in rows]
    positive['schema_version'] = 'stage3-positive-eval/recovered/1'
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(positive, ensure_ascii=False, indent=2) + '\n')
    print(f'json -> {args.out}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
