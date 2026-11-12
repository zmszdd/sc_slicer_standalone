#!/usr/bin/env python3
"""Aggregate stage-3 runs into route-aware recall/precision + loss buckets.

Two inputs are supported:

* ``--runs-dir``  -- scan for ``stage3-summary.json`` (+ ``routing.json``
  sidecar) and bucket per-claim verdicts by verification route.
* ``--eval-run``  -- read a ``stage3-eval-run/1`` summary (per-case verdict
  lists) and compute the classic positive-set metrics.

Run with cwd = tools/stage3:
    python -m cli.eval_report --runs-dir runs --out /tmp/metrics.json
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

ROUTE_BUCKETS = {
    'auto_assert',
    'reference_patch_cross_contract',
    'reference_patch_should_be',
    'unbound_feedback',
}

LOSS_VERDICTS = (
    'reference_patch_required',
    'compile_blocked',
    'compile_error',
    'binding_error',
    'binding_failed',
    'partial_binding',
    'not_dynamically_expressible',
    'halt_witness_required',
    'inconclusive',
)


def _read_json(path: Path):
    return json.loads(path.read_text())


def _routes_from_runs(runs_dir: Path):
    for summary_path in sorted(runs_dir.glob('**/stage3-summary.json')):
        try:
            summary = _read_json(summary_path)
        except (OSError, json.JSONDecodeError):
            continue
        routing_path = summary_path.with_name('routing.json')
        routing = {}
        if routing_path.is_file():
            try:
                routing = _read_json(routing_path)
            except (OSError, json.JSONDecodeError):
                routing = {}
        yield summary, routing


def analyze_runs(runs_dir: Path) -> dict:
    verdicts = Counter()
    route_verdicts = Counter()
    total = 0
    routed_total = 0
    auto_verifiable = 0
    auto_reproduced = 0
    reproduced = 0
    reference_required = 0
    for summary, routing in _routes_from_runs(runs_dir):
        total += 1
        verdict = summary.get('consistency_verdict')
        verdicts[verdict if verdict else 'missing'] += 1
        has_routing = 'schema_version' in routing
        route = routing.get('route') or 'unknown'
        if has_routing:
            routed_total += 1
            route_verdicts[(route, verdict if verdict else 'missing')] += 1
            if routing.get('auto_verifiable'):
                auto_verifiable += 1
                if verdict == 'violation_reproduced':
                    auto_reproduced += 1
            if routing.get('requires_reference_patch'):
                reference_required += 1
        if verdict == 'violation_reproduced':
            reproduced += 1
    losses = {name: verdicts.get(name, 0) for name in LOSS_VERDICTS}
    losses['missing'] = verdicts.get('missing', 0)
    return {
        'schema_version': 'stage3-eval-report/1',
        'source': str(runs_dir),
        'total_claims': total,
        'routed_claims': routed_total,
        'verdict_histogram': dict(verdicts),
        'reproduced': reproduced,
        'auto_verifiable_claims': auto_verifiable,
        'auto_verifiable_reproduced': auto_reproduced,
        'reference_patch_required_claims': reference_required,
        'recall_auto_verifiable': (auto_reproduced / auto_verifiable
                                   if auto_verifiable else 0.0),
        'recall_full': reproduced / total if total else 0.0,
        'loss_buckets': losses,
        'route_verdict_histogram': {
            f'{route}:{verdict}': count
            for (route, verdict), count in sorted(route_verdicts.items())
        },
    }


def analyze_eval_run(path: Path) -> dict:
    summary = _read_json(path)
    cases = [row for row in summary.get('cases', []) if row.get('status') == 'done']
    verdicts = Counter()
    for row in cases:
        for verdict in (row.get('verdicts') or []):
            verdicts[verdict if verdict else 'binding_failed'] += 1
    total = sum(verdicts.values())
    reproduced = verdicts.get('violation_reproduced', 0)
    verifiable = (reproduced + verdicts.get('violation_not_reproduced', 0)
                  + verdicts.get('inconclusive', 0))
    losses = {name: verdicts.get(name, 0) for name in LOSS_VERDICTS}
    losses['binding_failed'] = verdicts.get('binding_failed', 0)
    return {
        'schema_version': 'stage3-eval-report/1',
        'source': str(path),
        'total_claims': total,
        'verdict_histogram': dict(verdicts),
        'reproduced': reproduced,
        'auto_verifiable_claims': None,
        'reference_patch_required_claims': verdicts.get('reference_patch_required', 0),
        'recall_auto_verifiable': None,
        'recall_full': reproduced / total if total else 0.0,
        'recall_verifiable': reproduced / verifiable if verifiable else 0.0,
        'loss_buckets': losses,
    }


def _fmt_rate(value) -> str:
    if value is None:
        return 'n/a'
    return f'{value:.1%}'


def _print_table(metrics: dict):
    print('=' * 68)
    print('阶段三评测汇总（按主线路由分桶）')
    print('=' * 68)
    print(f'claims 总数            : {metrics["total_claims"]}')
    print(f'violation_reproduced   : {metrics["reproduced"]}')
    print(f'recall(全分母)         : {_fmt_rate(metrics["recall_full"])}')
    if metrics.get('recall_verifiable') is not None:
        print(f'recall(可验证子集)     : {_fmt_rate(metrics["recall_verifiable"])}')
    if metrics.get('recall_auto_verifiable') is not None:
        print(f'recall(auto_assert)    : {_fmt_rate(metrics["recall_auto_verifiable"])}')
    print()
    print('verdict 分布:')
    for verdict, count in sorted(metrics['verdict_histogram'].items(),
                                 key=lambda kv: -kv[1]):
        print(f'  {verdict}: {count}')
    print()
    print('损失分桶:')
    for name, count in sorted(metrics['loss_buckets'].items(), key=lambda kv: -kv[1]):
        if count:
            print(f'  {name}: {count}')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--runs-dir', type=Path)
    group.add_argument('--eval-run', type=Path)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args(argv)

    metrics = (analyze_runs(args.runs_dir) if args.runs_dir
               else analyze_eval_run(args.eval_run))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(metrics, ensure_ascii=False, indent=2) + '\n')
    _print_table(metrics)
    print(f'\nmetrics -> {args.out}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
