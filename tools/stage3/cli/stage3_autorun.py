#!/usr/bin/env python3
"""End-to-end stage-3 automation: assemble -> bind -> differential -> gate.

One entry point over a goldset + flatten corpus:

1. ``stage3_eval_run`` assembles cases, proposes bindings with bounded repair
   (partial/UNBOUND bindings are accepted and flow through to ``partial_binding``
   verdicts), then runs the Foundry differential pipeline per claim.
2. ``stage3_verdict_loop`` (optional, ``--repair-loop``) re-proposes bindings
   for binding-repairable verdicts using the replan diagnostic.
3. ``stage3_acceptance`` emits reproduction/terminal metrics and gates on
   optional thresholds (non-zero exit on failure).
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]  # tools/stage3

from lib.verdict_loop import REPAIR_LOOP_VERDICTS


def _run(args: list[str]) -> int:
    proc = subprocess.run([sys.executable, '-m'] + args, cwd=str(ROOT))
    return proc.returncode


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--goldset-root', required=True)
    parser.add_argument('--flatten-root', required=True)
    parser.add_argument('--cases-root', required=True)
    parser.add_argument('--out', required=True, help='final summary JSON path')
    parser.add_argument('--cases', default=None,
                        help='comma-separated case ids; default: all')
    parser.add_argument('--max-binding-rounds', type=int, default=3)
    parser.add_argument('--repair-loop', action='store_true',
                        help='run verdict_loop on binding-repairable cases after eval')
    parser.add_argument('--max-verdict-rounds', type=int, default=2)
    parser.add_argument('--min-reproduction-rate', type=float, default=None)
    parser.add_argument('--min-terminal-rate', type=float, default=None)
    parser.add_argument('--sync-metrics', action='store_true',
                        help='refresh authoritative four metrics after acceptance')
    args = parser.parse_args(argv)

    eval_out = Path(args.out).with_suffix('.eval.json')
    eval_cmd = ['cli.stage3_eval_run',
                '--goldset-root', args.goldset_root,
                '--flatten-root', args.flatten_root,
                '--cases-root', args.cases_root,
                '--out', str(eval_out),
                '--max-binding-rounds', str(args.max_binding_rounds)]
    if args.cases:
        eval_cmd += ['--cases', args.cases]
    code = _run(eval_cmd)
    if code != 0:
        raise SystemExit(f'stage3_eval_run failed with exit code {code}')

    if args.repair_loop:
        summary = json.loads(eval_out.read_text())
        cases_root = Path(args.cases_root).resolve()
        for row in summary.get('cases', []):
            if row.get('status') != 'done':
                continue
            verdicts = [v for v in (row.get('verdicts') or []) if v]
            if not any(v in REPAIR_LOOP_VERDICTS for v in verdicts):
                continue
            case_dir = cases_root / row['case']
            if not case_dir.is_dir():
                continue
            _run(['cli.stage3_verdict_loop', '--case-dir', str(case_dir),
                  '--max-rounds', str(args.max_verdict_rounds)])

    acceptance_cmd = ['cli.stage3_acceptance', '--summary', str(eval_out)]
    if args.sync_metrics:
        acceptance_cmd += ['--sync-metrics']
    if args.min_reproduction_rate is not None:
        acceptance_cmd += ['--min-reproduction-rate', str(args.min_reproduction_rate)]
    if args.min_terminal_rate is not None:
        acceptance_cmd += ['--min-terminal-rate', str(args.min_terminal_rate)]
    return _run(acceptance_cmd)


if __name__ == '__main__':
    raise SystemExit(main())
