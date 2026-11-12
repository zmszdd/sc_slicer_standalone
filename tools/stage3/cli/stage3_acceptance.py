#!/usr/bin/env python3
"""Stage-3 acceptance gate over an eval-run summary.

Flattens the per-case verdict lists of a ``stage3-eval-run/1`` summary into
reproduction / terminal rates, then optionally gates on configurable
thresholds (non-zero exit when a threshold is missed).
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from lib.verdict_loop import TERMINAL_VERDICTS


def evaluate(summary: dict) -> dict:
    cases = [row for row in summary.get('cases', []) if row.get('status') == 'done']
    verdicts = [verdict for row in cases for verdict in (row.get('verdicts') or [])
                if verdict]
    histogram = Counter(verdicts)
    total_claims = sum(int(row.get('claims') or 0) for row in cases)
    terminal = sum(count for verdict, count in histogram.items()
                   if verdict in TERMINAL_VERDICTS)
    reproduced = histogram.get('violation_reproduced', 0)
    not_reproduced = histogram.get('violation_not_reproduced', 0)
    not_expressible = histogram.get('not_dynamically_expressible', 0)
    inconclusive = histogram.get('inconclusive', 0)
    # 可动态验证子集：真正进入差分且 forge 跑通（能给出确定/不确定判定），
    # 排除 not_dynamically_expressible / compile_blocked / compile_error /
    # partial_binding / binding_blocked 这些「无法验证」的终态。
    verifiable = reproduced + not_reproduced + inconclusive
    return {
        'total_cases': len(cases),
        'total_claims': total_claims,
        'verdicts': len(verdicts),
        'reproduced': reproduced,
        'not_reproduced': not_reproduced,
        'not_dynamically_expressible': not_expressible,
        'inconclusive': inconclusive,
        'verifiable_claims': verifiable,
        'reproduction_rate': reproduced / total_claims if total_claims else 0.0,
        'verifiable_reproduction_rate':
            reproduced / verifiable if verifiable else 0.0,
        'terminal_rate': terminal / len(verdicts) if verdicts else 0.0,
        'histogram': dict(histogram),
        'binding_blocked': max(0, total_claims - len(verdicts)),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--summary', type=Path, required=True)
    parser.add_argument('--min-reproduction-rate', type=float, default=None,
                        help='gate: minimum reproduced/total_claims ratio')
    parser.add_argument('--min-terminal-rate', type=float, default=None,
                        help='gate: minimum terminal-verdict/verdicts ratio')
    parser.add_argument('--sync-metrics', action='store_true',
                        help='after evaluation, refresh the authoritative four metrics from runs')
    args = parser.parse_args(argv)

    summary = json.loads(Path(args.summary).read_text())
    metrics = evaluate(summary)
    print(json.dumps(metrics, ensure_ascii=False, indent=2))

    failures = []
    if (args.min_reproduction_rate is not None
            and metrics['reproduction_rate'] < args.min_reproduction_rate):
        failures.append(f'reproduction_rate {metrics["reproduction_rate"]:.3f} '
                        f'< {args.min_reproduction_rate}')
    if (args.min_terminal_rate is not None
            and metrics['terminal_rate'] < args.min_terminal_rate):
        failures.append(f'terminal_rate {metrics["terminal_rate"]:.3f} '
                        f'< {args.min_terminal_rate}')
    if failures:
        print('ACCEPTANCE: FAIL - ' + '; '.join(failures))
        return 1
    print('ACCEPTANCE: PASS')
    if args.sync_metrics:
        from lib.metrics_sync import sync
        print(json.dumps(sync(), ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
