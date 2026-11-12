#!/usr/bin/env python3
"""One-command full-flow four-metric run: positive eval -> negative build (on
demand) -> judge anchoring -> objective metrics report.

The mainline still runs stage-1 flatten (external) and stage-2 rule extraction
separately; this entry owns the *measurement* tail so the four metrics and the
judge-anchored FP attribution are produced by a single command instead of being
hand-assembled from scattered scripts.

Usage (cwd = tools/stage3):
    python -m cli.stage3_fullflow \\
        --goldset-root evaluation/goldset_v2_pos91 \\
        --flatten-root /root/poc_repro_work/verified_flatten_pass_1568_exact_cases \\
        --cases-root cases --out-dir /tmp/fullflow \\
        --judge-ground-truth evaluation/metrics/judge_ground_truth.json

Pass ``--negative`` to rebuild negative samples from reproduced positives, or
``--negative-results`` to reuse an existing negative-results JSON.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]  # tools/stage3
DEFAULT_JUDGE_GT = ROOT / 'evaluation' / 'metrics' / 'judge_ground_truth.json'

from lib.verdict_loop import REPAIR_LOOP_VERDICTS


def _run(args: list[str]) -> int:
    proc = subprocess.run([sys.executable, '-m'] + args, cwd=str(ROOT))
    return proc.returncode


def _read(path: Path) -> dict | list:
    return json.loads(Path(path).read_text())


def select_negative_targets(positive_eval: dict, cases_root: Path,
                            max_negatives: int = 0) -> list[dict]:
    """Return ``{case, binding, report, claim_id}`` for reproduced positives.

    Only rows that reached a dynamic ``violation_reproduced`` verdict are used,
    and only claims whose binding file exists under ``cases/<case>/bindings/``.
    """
    targets = []
    for row in positive_eval.get('cases', []):
        if row.get('status') != 'done' or int(row.get('reproduced') or 0) <= 0:
            continue
        verdicts = row.get('verdicts') or []
        claim_ids = row.get('bound_claim_ids') or []
        for claim_id, verdict in zip(claim_ids, verdicts):
            if verdict != 'violation_reproduced':
                continue
            binding = cases_root / row['case'] / 'bindings' / f'{claim_id}.json'
            if not binding.is_file():
                single = cases_root / row['case'] / 'binding.json'
                if single.is_file():
                    binding = single
                else:
                    continue
            targets.append({
                'case': row['case'],
                'claim_id': claim_id,
                'binding': str(binding),
            })
            if max_negatives and len(targets) >= max_negatives:
                return targets
    return targets


def build_negatives(targets: list[dict], flatten_root: Path,
                    cases_root: Path, neg_cases_root: Path,
                    max_fix_rounds: int = 3) -> dict:
    """Build one validated negative sample per reproduced positive claim."""
    neg_cases_root.mkdir(parents=True, exist_ok=True)
    accepted = []
    discarded = []
    for target in targets:
        out_dir = neg_cases_root / f"{target['case']}_{target['claim_id']}_neg"
        report = flatten_root / target['case'] / 'report.json'
        if not report.is_file():
            discarded.append({'case': target['case'],
                              'reason': 'report_missing'})
            continue
        cmd = ['cli.stage3_negative_build',
               '--positive-case', str(cases_root / target['case']),
               '--binding', target['binding'],
               '--report', str(report),
               '--out', str(out_dir),
               '--validate',
               '--max-fix-rounds', str(max_fix_rounds)]
        proc = subprocess.run([sys.executable, '-m'] + cmd, cwd=str(ROOT))
        if proc.returncode == 0 and (out_dir / 'verdict.json').is_file():
            accepted.append(out_dir.name)
        else:
            discarded.append({'case': target['case'],
                              'reason': 'negative_build_failed'})
    return {
        'targets': len(targets),
        'accepted': accepted,
        'discarded': discarded,
    }


def compose_report(positive: dict, negative: list[dict],
                   judge_metrics: dict | None,
                   negative_build: dict | None) -> dict:
    """Merge the three measurement layers into one authoritative report."""
    from cli.metrics_report import analyze as metrics_analyze
    metrics = metrics_analyze(positive, negative, judge_metrics=judge_metrics)
    return {
        'schema_version': 'stage3-fullflow-report/1',
        'metrics': metrics,
        'judge_anchored': judge_metrics,
        'negative_build': negative_build,
    }


def _run_positive(goldset_root: Path, flatten_root: Path, cases_root: Path,
                  out: Path, cases: str | None, max_binding_rounds: int,
                  repair_loop: bool, max_verdict_rounds: int) -> int:
    eval_cmd = ['cli.stage3_eval_run',
                '--goldset-root', str(goldset_root),
                '--flatten-root', str(flatten_root),
                '--cases-root', str(cases_root),
                '--out', str(out),
                '--max-binding-rounds', str(max_binding_rounds)]
    if cases:
        eval_cmd += ['--cases', cases]
    code = _run(eval_cmd)
    if code != 0:
        return code
    if repair_loop:
        summary = _read(out)
        for row in summary.get('cases', []):
            if row.get('status') != 'done':
                continue
            verdicts = [v for v in (row.get('verdicts') or []) if v]
            if not any(v in REPAIR_LOOP_VERDICTS for v in verdicts):
                continue
            case_dir = cases_root / row['case']
            if case_dir.is_dir():
                _run(['cli.stage3_verdict_loop', '--case-dir', str(case_dir),
                      '--max-rounds', str(max_verdict_rounds)])
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--goldset-root', type=Path, required=True)
    parser.add_argument('--flatten-root', type=Path, required=True)
    parser.add_argument('--cases-root', type=Path, required=True)
    parser.add_argument('--out-dir', type=Path, required=True)
    parser.add_argument('--judge-ground-truth', type=Path,
                        default=DEFAULT_JUDGE_GT)
    parser.add_argument('--positive-eval', type=Path, default=None,
                        help='reuse an existing positive eval instead of running one')
    parser.add_argument('--negative-results', type=Path, default=None,
                        help='reuse an existing negative-results JSON')
    parser.add_argument('--negative', action='store_true',
                        help='build validated negatives on demand from reproduced positives')
    parser.add_argument('--max-negatives', type=int, default=0)
    parser.add_argument('--max-fix-rounds', type=int, default=3)
    parser.add_argument('--cases', default=None)
    parser.add_argument('--max-binding-rounds', type=int, default=3)
    parser.add_argument('--repair-loop', action='store_true')
    parser.add_argument('--max-verdict-rounds', type=int, default=2)
    parser.add_argument('--min-reproduction-rate', type=float, default=None,
                        help='gate: minimum reproduced/total_claims ratio')
    parser.add_argument('--min-terminal-rate', type=float, default=None,
                        help='gate: minimum terminal-verdict/verdicts ratio')
    parser.add_argument('--max-fp-rate', type=float, default=None,
                        help='gate: maximum judge-anchored FP rate')
    args = parser.parse_args(argv)

    out_dir = Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    positive_path = (Path(args.positive_eval).resolve()
                     if args.positive_eval else out_dir / 'positive_eval.json')
    if args.positive_eval:
        positive = _read(positive_path)
    else:
        code = _run_positive(args.goldset_root, args.flatten_root,
                             args.cases_root, positive_path, args.cases,
                             args.max_binding_rounds, args.repair_loop,
                             args.max_verdict_rounds)
        if code != 0:
            raise SystemExit(f'positive eval failed with exit code {code}')
        positive = _read(positive_path)

    negative_build = None
    if args.negative_results:
        negative = _read(Path(args.negative_results).resolve())
    elif args.negative:
        cases_root = Path(args.cases_root).resolve()
        targets = select_negative_targets(positive, cases_root,
                                          args.max_negatives)
        neg_cases_root = out_dir / 'neg_cases'
        negative_build = build_negatives(targets, Path(args.flatten_root).resolve(),
                                         cases_root, neg_cases_root,
                                         args.max_fix_rounds)
        neg_eval_out = out_dir / 'negative_results.json'
        if negative_build['accepted']:
            _run(['cli.stage3_negative_eval',
                  '--cases-root', str(neg_cases_root),
                  '--out', str(neg_eval_out),
                  '--summary', str(out_dir / 'neg_batch_summary.json')])
            negative = _read(neg_eval_out)
        else:
            negative = []
    else:
        negative = []

    judge_out = out_dir / 'judge_anchored_metrics.json'
    _run([str(ROOT / 'evaluation' / 'metrics' / 'judge_anchor.py'),
          '--judge-ground-truth', str(args.judge_ground_truth),
          '--positive-eval', str(positive_path),
          '--out', str(judge_out)])
    judge_metrics = _read(judge_out) if judge_out.is_file() else None

    report = compose_report(positive, negative, judge_metrics, negative_build)
    report_out = out_dir / 'fullflow_report.json'
    report_out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print(f'\nfullflow report -> {report_out}')

    failures = []
    acceptance = None
    if args.min_reproduction_rate is not None or args.min_terminal_rate is not None:
        acceptance_cmd = ['cli.stage3_acceptance', '--summary', str(positive_path)]
        if args.min_reproduction_rate is not None:
            acceptance_cmd += ['--min-reproduction-rate',
                               str(args.min_reproduction_rate)]
        if args.min_terminal_rate is not None:
            acceptance_cmd += ['--min-terminal-rate', str(args.min_terminal_rate)]
        acceptance_rc = _run(acceptance_cmd)
        if acceptance_rc != 0:
            failures.append('stage3_acceptance gate failed')
    if (args.max_fp_rate is not None and judge_metrics is not None
            and judge_metrics.get('fp_rate_over_invalid_evaluated', 0.0)
            > args.max_fp_rate):
        failures.append(f"fp_rate {judge_metrics['fp_rate_over_invalid_evaluated']:.3f} "
                        f'> {args.max_fp_rate}')
    if failures:
        print('FULLFLOW: FAIL - ' + '; '.join(failures))
        return 1
    print('FULLFLOW: PASS')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
