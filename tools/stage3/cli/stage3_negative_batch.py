#!/usr/bin/env python3
"""Batch-build negative samples for every reproduced positive claim.

Inputs:
  --positive-eval   stage3-eval-run/1 summary (status + reproduced per case)
  --cases-root      positive case directories (tools/stage3/cases)
  --flatten-root    verified flatten root (report.json + contract.flattened.t.sol)
  --out-root        where negative case directories are created
  --fixes-dir       optional directory of precomputed <case>.fix.json
  --runs-dir        stage-3 runs dir used to recover claim_id -> verdict

For each positive case that reproduced at least one claim, recover the exact
claim ids whose terminal verdict is ``violation_reproduced``, then run
``stage3_negative_build`` per claim. Precomputed fix.json is reused when
present; otherwise DeepSeek proposes the fix. Built cases are NOT validated
here (validation is run separately via ``stage3_negative_eval``).
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from lib.verdict_loop import TERMINAL_VERDICTS

ROOT = Path(__file__).resolve().parents[1]  # tools/stage3

TERMINAL = TERMINAL_VERDICTS


def _reproduced_claims(case_name: str, runs_dir: Path) -> list[str]:
    """Return claim ids whose newest terminal summary is violation_reproduced."""
    best: dict[str, tuple[int, bool]] = {}
    for run_dir in runs_dir.iterdir():
        if not run_dir.is_dir():
            continue
        summary_path = run_dir / 'stage3-summary.json'
        if not summary_path.is_file():
            continue
        try:
            summary = json.loads(summary_path.read_text())
        except (json.JSONDecodeError, OSError):
            continue
        if Path(summary.get('case', '')).name != case_name:
            continue
        claim_id = summary.get('claim_id')
        verdict = summary.get('consistency_verdict')
        if not claim_id:
            continue
        terminal = verdict in TERMINAL
        mtime = summary_path.stat().st_mtime
        if claim_id not in best or terminal or mtime > best[claim_id][0]:
            best[claim_id] = (mtime, verdict == 'violation_reproduced')
    return sorted(cid for cid, (_mt, reproduced) in best.items() if reproduced)


def _single_claim_fallback(case_dir: Path) -> list[str]:
    bindings = case_dir / 'bindings'
    if bindings.is_dir():
        files = sorted(p for p in bindings.iterdir() if p.suffix == '.json')
        if len(files) == 1:
            try:
                return [json.loads(files[0].read_text()).get('claim_id')]
            except (json.JSONDecodeError, OSError):
                return []
    single = case_dir / 'binding.json'
    if single.is_file():
        try:
            return [json.loads(single.read_text()).get('claim_id')]
        except (json.JSONDecodeError, OSError):
            return []
    return []


def _build_negative(case_dir: Path, claim_id: str, flatten_root: Path,
                    fixes_dir: Path | None, out_root: Path, validate: bool):
    cid = case_dir.name
    binding = case_dir / 'bindings' / f'{claim_id}.json'
    if not binding.is_file():
        print(f'skip {cid}/{claim_id}: missing binding', flush=True)
        return
    report = flatten_root / cid / 'report.json'
    if not report.is_file():
        print(f'skip {cid}/{claim_id}: missing report.json', flush=True)
        return
    out = out_root / f'{cid}__{claim_id}_neg'
    if out.exists():
        print(f'exists {out.name}', flush=True)
        return
    cmd = [sys.executable, '-m', 'cli.stage3_negative_build',
           '--positive-case', str(case_dir),
           '--binding', str(binding),
           '--report', str(report),
           '--out', str(out)]
    if fixes_dir and (fixes_dir / f'{cid}.fix.json').is_file():
        cmd += ['--fix-json', str(fixes_dir / f'{cid}.fix.json')]
    if validate:
        cmd.append('--validate')
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=str(ROOT))
    tail = (proc.stdout or proc.stderr or '').strip()
    if proc.returncode != 0:
        print(f'FAIL {cid}/{claim_id}: {tail[-400:]}', flush=True)
    else:
        print(f'OK   {cid}/{claim_id} -> {out.name} {tail[-120:]}', flush=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--positive-eval', type=Path, default=None)
    parser.add_argument('--cases-root', type=Path, required=True)
    parser.add_argument('--flatten-root', type=Path, required=True)
    parser.add_argument('--out-root', type=Path, required=True)
    parser.add_argument('--fixes-dir', type=Path,
                        help='directory of precomputed <case>.fix.json')
    parser.add_argument('--runs-dir', type=Path, default=ROOT / 'runs')
    parser.add_argument('--cases', default=None,
                        help='comma-separated case ids; bypass positive-eval '
                             'and recover reproduced claims from --runs-dir')
    parser.add_argument('--validate', action='store_true')
    parser.add_argument('--max-cases', type=int, default=0)
    args = parser.parse_args(argv)

    cases_root = Path(args.cases_root).resolve()
    flatten_root = Path(args.flatten_root).resolve()
    out_root = Path(args.out_root).resolve()
    out_root.mkdir(parents=True, exist_ok=True)
    fixes_dir = Path(args.fixes_dir).resolve() if args.fixes_dir else None

    if args.cases:
        ids = [x.strip() for x in args.cases.split(',') if x.strip()]
        rows = []
        for cid in ids:
            case_dir = cases_root / cid
            claims = _reproduced_claims(cid, args.runs_dir)
            if not claims:
                claims = _single_claim_fallback(case_dir) if case_dir.is_dir() else []
            rows.append({'case': cid, 'reproduced': len(claims)})
    else:
        positive = json.loads(Path(args.positive_eval).read_text())
        rows = [r for r in positive.get('cases', [])
                if r.get('status') == 'done' and int(r.get('reproduced') or 0) > 0]
    if args.max_cases > 0:
        rows = rows[:args.max_cases]

    built = 0
    for row in rows:
        cid = row['case']
        case_dir = cases_root / cid
        if not case_dir.is_dir():
            print(f'skip {cid}: no case dir', flush=True)
            continue
        claims = _reproduced_claims(cid, args.runs_dir)
        if not claims and int(row.get('reproduced') or 0) > 0:
            claims = _single_claim_fallback(case_dir)
        if not claims:
            print(f'skip {cid}: no reproduced claim recovered', flush=True)
            continue
        for claim_id in claims:
            _build_negative(case_dir, claim_id, flatten_root, fixes_dir,
                            out_root, args.validate)
            built += 1
    print(f'\nbuilt/attempted negatives: {built} -> {out_root}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
