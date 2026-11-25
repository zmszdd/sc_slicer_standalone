#!/usr/bin/env python3
"""Read-only preflight for stable stage-3 execution.

The check distinguishes two runnable modes: ``online`` when the configured
LLM provider accepts a minimal JSON request, and ``offline`` when every
selected claim already has a complete binding and no provider is needed.
It never rewrites cases, bindings, samples, labels, runs or metrics.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STAGE3 = HERE.parents[1]
if str(STAGE3) not in sys.path:
    sys.path.insert(0, str(STAGE3))
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from evaluation.metrics import provider_probe  # noqa: E402
from lib.spec_loader import SpecError, load_stage2_run  # noqa: E402

SAMPLE = HERE / 'mainline_sample_mini.json'
GOLDSET = HERE / 'mainline_goldset_1_7_31_pos'
CASES = STAGE3 / 'cases'


def _stage2_dir(goldset_root: Path, case: str) -> Path | None:
    for run_dir in sorted(goldset_root.glob('runs_*')):
        candidate = run_dir / case
        if (candidate / 'stage3-spec.json').is_file():
            return candidate
    return None


def _binding_issues(case_dir: Path, claim_ids: list[str]) -> list[str]:
    issues: list[str] = []
    if not case_dir.is_dir():
        return ['case directory missing']
    bindings_dir = case_dir / 'bindings'
    if not bindings_dir.is_dir():
        return ['bindings directory missing']
    if not claim_ids:
        return ['stage2 has no executable claims']
    for claim_id in claim_ids:
        path = bindings_dir / f'{claim_id}.json'
        if not path.is_file():
            issues.append(f'{claim_id}: binding missing')
            continue
        try:
            binding = json.loads(path.read_text())
        except (OSError, ValueError) as exc:
            issues.append(f'{claim_id}: invalid binding JSON: {exc}')
            continue
        if not isinstance(binding, dict):
            issues.append(f'{claim_id}: binding is not an object')
            continue
        entries = binding.get('bindings')
        if not isinstance(entries, dict) or not entries:
            issues.append(f'{claim_id}: no binding entries')
            continue
        unbound = []
        for symbol, entry in sorted(entries.items()):
            expression = ''
            if isinstance(entry, dict):
                expression = str(entry.get('solidity_expr') or '').strip()
            if not expression or expression.upper() == 'UNBOUND':
                unbound.append(symbol)
        if unbound:
            issues.append(f'{claim_id}: unbound symbols: '
                          + ', '.join(unbound[:8]))
        if not isinstance(binding.get('patch'), dict) or not binding['patch']:
            issues.append(f'{claim_id}: patch descriptor missing')
        if not isinstance(binding.get('probe'), dict) or not binding['probe']:
            issues.append(f'{claim_id}: probe descriptor missing')
    return issues


def build(*, sample_path: Path = SAMPLE,
          goldset_root: Path = GOLDSET,
          cases_root: Path = CASES,
          cases: list[str] | None = None,
          scope: str = 'positive',
          check_provider: bool = True,
          provider_timeout: float = 15.0) -> dict:
    sample = json.loads(Path(sample_path).read_text())
    if scope == 'positive':
        selected = list(sample.get('positive_cases') or [])
    elif scope == 'negative':
        selected = list(sample.get('negative_cases') or [])
    elif scope == 'both':
        selected = list(sample.get('positive_cases') or []) + list(
            sample.get('negative_cases') or [])
    else:
        raise ValueError(f'unknown scope: {scope}')
    wanted = [str(case).strip() for case in (cases or selected)
              if str(case).strip()]

    rows = []
    for case in wanted:
        stage2_dir = _stage2_dir(Path(goldset_root), case)
        if stage2_dir is None:
            rows.append({'case': case, 'ready': False, 'claim_ids': [],
                         'issues': ['stage2 spec missing']})
            continue
        try:
            loaded = load_stage2_run(stage2_dir)
        except SpecError as exc:
            rows.append({'case': case, 'ready': False, 'claim_ids': [],
                         'issues': [f'stage2 spec blocked: {exc}']})
            continue
        claim_ids = [str(row['claim_id'])
                     for row in loaded['spec'].get('claims') or []
                     if isinstance(row, dict) and row.get('claim_id')]
        issues = _binding_issues(Path(cases_root) / case, claim_ids)
        rows.append({
            'case': case,
            'ready': not issues,
            'claim_ids': claim_ids,
            'issues': issues,
        })

    if check_provider:
        provider = provider_probe.probe(provider_timeout)
    else:
        provider = {
            'ok': False,
            'provider': None,
            'model': None,
            'status': None,
            'reason': 'skipped',
            'detail': 'provider check disabled',
            'elapsed_ms': 0,
        }

    incomplete = [row['case'] for row in rows if not row['ready']]
    online_ready = bool(provider['ok'])
    offline_ready = not incomplete
    ok = online_ready or offline_ready
    blockers = []
    if not ok:
        blockers.append(
            f'provider={provider["reason"]}; '
            f'{len(incomplete)} case(s) need LLM bindings')
    return {
        'schema_version': 'stage3-execution-preflight/1',
        'ok': ok,
        'mode': ('online' if online_ready else
                 'offline' if offline_ready else 'blocked'),
        'scope': scope,
        'cases': len(rows),
        'incomplete': incomplete,
        'provider': provider,
        'rows': rows,
        'blockers': blockers,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sample', type=Path, default=SAMPLE)
    parser.add_argument('--goldset-root', type=Path, default=GOLDSET)
    parser.add_argument('--cases-root', type=Path, default=CASES)
    parser.add_argument('--cases', default=None,
                        help='comma-separated case ids; default: sample scope')
    parser.add_argument('--scope', choices=('positive', 'negative', 'both'),
                        default='positive')
    parser.add_argument('--skip-provider', action='store_true')
    parser.add_argument('--provider-timeout', type=float, default=15.0)
    parser.add_argument('--out', type=Path, default=None)
    args = parser.parse_args(argv)

    cases = ([item.strip() for item in args.cases.split(',') if item.strip()]
             if args.cases else None)
    report = build(
        sample_path=args.sample,
        goldset_root=args.goldset_root,
        cases_root=args.cases_root,
        cases=cases,
        scope=args.scope,
        check_provider=not args.skip_provider,
        provider_timeout=args.provider_timeout)
    text = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
    print(text, end='')
    return 0 if report['ok'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
