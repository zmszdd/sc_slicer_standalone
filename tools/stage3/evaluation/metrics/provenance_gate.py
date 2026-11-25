#!/usr/bin/env python3
"""Decide whether the frozen four metrics may be refreshed.

The gate is deliberately stricter than the historical metric generators.  A
claim is eligible only when its run summary carries an artifact fingerprint
from the current protocol.  Legacy summaries remain diagnostic evidence and
cannot contribute to the current confusion matrix.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

try:  # package import in tests, script import from the metrics directory
    from .current_denominator import (
        MIN_MAINLINE_NEGATIVES, _fingerprint, build as build_denominator,
    )
except ImportError:  # pragma: no cover - exercised by the CLI entry point
    from current_denominator import (
        MIN_MAINLINE_NEGATIVES, _fingerprint, build as build_denominator,
    )

try:  # package import in tests, script import from the metrics directory
    from ..lib import claim_population
except ImportError:  # pragma: no cover - script import
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from lib import claim_population

HERE = Path(__file__).resolve().parent
DEFAULT_LEDGER = HERE / 'failure_ledger_252.json'
DEFAULT_DEV24 = HERE / 'dev24_results.json'
DEFAULT_NEGATIVE5 = HERE / 'negative_5_results.json'
DEFAULT_RECIPE = HERE / 'observable_recipe_audit_10_v4.json'
DEFAULT_SAMPLE = HERE / 'mainline_sample_mini.json'
DEFAULT_RUNS = HERE.parents[1] / 'runs'
DEFAULT_JSON = HERE / 'provenance_gate.json'
DEFAULT_MD = HERE / 'provenance_gate.md'
SCHEMA_VERSION = 'stage3-provenance-gate/1'
PROVENANCE_MODE = 'mainline-only/1'


def _load(path: Path) -> dict:
    try:
        return json.loads(Path(path).read_text())
    except (OSError, ValueError):
        return {}


def _summary_provenance(summary_path: str | None) -> str:
    if not summary_path:
        return 'missing_summary'
    summary = _load(Path(summary_path))
    if not summary:
        return 'missing_summary'
    fingerprint = summary.get('artifact_fingerprint') or {}
    current, _reason = _fingerprint(summary)
    if current:
        return 'fingerprinted_run'
    if fingerprint.get('schema_version'):
        return 'stale_protocol_run'
    if any(key in summary for key in (
            'witness', 'execution_gate', 'execution_contract',
            'weak_invariant_risk')):
        return 'protocol_run_without_fingerprint'
    return 'legacy_unreplayed'


def build_mainline_gate(sample_path: Path = DEFAULT_SAMPLE,
                        runs_dir: Path = DEFAULT_RUNS,
                        denominator: dict | None = None) -> dict:
    sample = _load(Path(sample_path))
    population = claim_population.current_claim_ids(Path(sample_path))
    cases = ({str(case) for case in sample.get('positive_cases') or []}
             | {str(case) for case in sample.get('negative_cases') or []})
    provenance: Counter[str] = Counter()
    latest: dict[tuple[str, str], tuple[float, Path]] = {}
    for summary_path in sorted(Path(runs_dir).glob('*/stage3-summary.json'),
                               key=lambda path: path.stat().st_mtime):
        summary = _load(summary_path)
        case = Path(str(summary.get('case') or '')).name
        if case in cases:
            claim_id = str(summary.get('claim_id') or '')
            if case in population and claim_id not in population[case]:
                continue
            key = (case, claim_id)
            latest[key] = (summary_path.stat().st_mtime, summary_path)
    for _mtime, summary_path in latest.values():
        provenance[_summary_provenance(str(summary_path))] += 1
    fingerprinted = provenance.get('fingerprinted_run', 0)
    stale = sum(count for name, count in provenance.items()
                if name != 'fingerprinted_run')
    current_only = bool(fingerprinted > 0 and stale == 0)

    negative_source = sample.get('negative_source')
    negative_path = Path(negative_source) if negative_source else None
    if negative_path is not None and not negative_path.is_absolute():
        root = HERE.parents[3]
        candidates = (root / negative_path, HERE / negative_path, negative_path)
        negative_path = next((path for path in candidates if path.is_file()),
                             candidates[0])
    pool = _load(negative_path) if negative_path is not None else {}
    pool_cases = {str(row.get('case')) for row in pool.get('selected') or []}
    frozen_negative = {str(case) for case in sample.get('negative_cases') or []}
    labels_ok = bool(pool_cases) and frozen_negative <= pool_cases and all(
        str(row.get('validity') or '').lower() == 'invalid'
        for row in pool.get('selected') or []
        if str(row.get('case')) in frozen_negative)
    slices_ready = int(sample.get('negative_slice_ready') or 0)
    selected_negatives = int(sample.get('selected_negatives')
                             or len(frozen_negative))
    slice_floor = min(selected_negatives, MIN_MAINLINE_NEGATIVES)
    denominator_ok = bool((denominator or {}).get('mainline', {})
                          .get('refresh_ready'))
    refresh_allowed = bool(current_only and labels_ok
                           and slices_ready >= slice_floor
                           and denominator_ok)
    reasons = []
    if not current_only:
        reasons.append('mainline runs still contain stale/missing summaries')
    if not labels_ok:
        reasons.append('official negative pool no longer matches frozen labels')
    if slices_ready < slice_floor:
        reasons.append(f'fewer than {slice_floor} negative source slices '
                       'are ready')
    if not denominator_ok:
        reasons.append('mainline denominator is not refresh_ready')
    return {
        'runs_provenance': dict(provenance),
        'fingerprinted': fingerprinted,
        'legacy_or_missing': stale,
        'current_only': current_only,
        'negative_pool_labels_ok': labels_ok,
        'negative_slice_ready': slices_ready,
        'negative_slice_floor': slice_floor,
        'denominator_ready': denominator_ok,
        'refresh_allowed': refresh_allowed,
        'reasons': reasons,
    }


def build(ledger_path: Path, dev24_path: Path, recipe_path: Path,
          negative5_path: Path = DEFAULT_NEGATIVE5,
          sample_path: Path = DEFAULT_SAMPLE,
          runs_dir: Path = DEFAULT_RUNS) -> dict:
    ledger = _load(Path(ledger_path))
    rows = [row for row in ledger.get('rows') or []
            if row.get('claim_outcome') == 'fn']
    provenance = Counter(
        _summary_provenance(row.get('summary_path')) for row in rows)
    dev24 = _load(Path(dev24_path))
    dev_gate = dev24.get('gate') or {}
    negative5 = _load(Path(negative5_path))
    negative5_gate = negative5.get('gate') or {}
    recipe = _load(Path(recipe_path)).get('summary') or {}
    denominator = build_denominator(
        Path(ledger_path), Path(dev24_path), Path(negative5_path),
        sample_path=Path(sample_path), runs_dir=Path(runs_dir))
    fingerprinted = provenance.get('fingerprinted_run', 0)
    legacy = provenance.get('legacy_unreplayed', 0)
    missing = provenance.get('missing_summary', 0)
    current_only = fingerprinted > 0 and legacy == 0 and missing == 0
    dev24_negative_ok = bool(dev_gate.get('negative_fp_zero')) and bool(
        dev_gate.get('negative_consistency_fp_zero',
                      dev_gate.get('negative_fp_zero'))) and bool(
        dev_gate.get('negative_all_resolved'))
    negative5_required = bool(negative5)
    negative5_negative_ok = (not negative5_required or (
        bool(negative5_gate.get('negative_fp_zero')) and bool(
            negative5_gate.get('negative_consistency_fp_zero',
                               negative5_gate.get('negative_fp_zero'))) and
        bool(negative5_gate.get('negative_all_resolved'))))
    negative_ok = dev24_negative_ok and negative5_negative_ok
    recipe_ok = (recipe.get('recipe_ready', 0) > 0
                 and recipe.get('recipe_unobservable', 0) >= 0)
    mainline_gate = build_mainline_gate(
        Path(sample_path), Path(runs_dir), denominator)
    refresh_allowed = bool(mainline_gate['refresh_allowed'])
    reasons = list(mainline_gate.get('reasons') or [])
    return {
        'schema_version': SCHEMA_VERSION,
        'mode': PROVENANCE_MODE,
        'inputs': {
            'failure_ledger': str(ledger_path),
            'dev24_results': str(dev24_path),
            'negative5_results': str(negative5_path),
            'recipe_audit': str(recipe_path),
        },
        'dev252_fn_provenance': dict(provenance),
        'dev252_claim_eligibility': {
            'fingerprinted': fingerprinted,
            'legacy_or_missing': len(rows) - fingerprinted,
            'current_only': current_only,
        },
        'dev24_gate': dev_gate,
        'negative5_gate': negative5_gate,
        'negative5_required': negative5_required,
        'recipe_gate': {
            'ready': recipe.get('recipe_ready', 0),
            'planned': recipe.get('recipe_planned', 0),
            'unobservable': recipe.get('recipe_unobservable', 0),
            'ok': recipe_ok,
        },
        'mainline': mainline_gate,
        'legacy_diagnostics': {
            'dev252_current_only': bool(current_only),
            'negative_gate_ok': bool(negative_ok),
            'recipe_gate_ok': bool(recipe_ok),
            'gating': False,
        },
        'denominator': {
            'dev252': {
                'cases': denominator['dev252']['case_counts'],
                'claims': denominator['dev252']['counts']},
            'dev24': {
                'cases': denominator['dev24']['case_counts'],
                'claims': denominator['dev24']['counts']},
            'negative5': {
                'cases': denominator['negative5']['case_counts'],
                'claims': denominator['negative5']['counts'],
                'metric_counts': denominator['negative5']['metric_counts']},
            'refresh_ready': denominator['refresh_ready'],
        },
        'refresh_allowed': refresh_allowed,
        'reasons': reasons,
        'policy': ('Only fingerprinted, completed current-protocol runs may '
                   'enter the four-metric matrix. Legacy artifacts remain '
                   'diagnostic and are excluded from the current denominator.'),
    }


def markdown(report: dict) -> str:
    lines = ['# Provenance / metric refresh gate', '',
             '| item | value |', '| --- | --- |']
    lines.append(f"| mode | `{report.get('mode', 'legacy')}` |")
    for key, value in report['dev252_fn_provenance'].items():
        lines.append(f'| provenance `{key}` | {value} |')
    eligibility = report['dev252_claim_eligibility']
    lines += [
        f"| fingerprinted claims | {eligibility['fingerprinted']} |",
        f"| legacy or missing | {eligibility['legacy_or_missing']} |",
        f"| current only | {eligibility['current_only']} |",
        f"| refresh allowed | {report['refresh_allowed']} |", '',
        '## Current denominator', '',
        '| dataset | eligible | excluded/retry | unresolved |',
        '| --- | ---: | ---: | ---: |',
    ]
    for name in ('dev252', 'dev24', 'negative5'):
        counts = ((report.get('denominator') or {}).get(name) or {}).get(
            'cases') or {}
        lines.append(
            f"| {name} | {counts.get('eligible_current', 0)} | "
            f"{counts.get('excluded_retry', 0)} | "
            f"{counts.get('unresolved', 0)} |")
    lines += [
        '',
        '## Blocking reasons', '',
    ]
    lines += [f'- {reason}' for reason in report.get('reasons') or []]
    if not report.get('reasons'):
        lines.append('- none')
    lines += ['', '## dev24 gate', '', '| gate | value |', '| --- | --- |']
    for key, value in (report.get('dev24_gate') or {}).items():
        lines.append(f'| `{key}` | {value} |')
    if report.get('negative5_required'):
        lines += ['', '## negative-5 gate', '', '| gate | value |',
                  '| --- | --- |']
        for key, value in (report.get('negative5_gate') or {}).items():
            lines.append(f'| `{key}` | {value} |')
    return '\n'.join(lines) + '\n'


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ledger', type=Path, default=DEFAULT_LEDGER)
    parser.add_argument('--dev24', type=Path, default=DEFAULT_DEV24)
    parser.add_argument('--negative5', type=Path, default=DEFAULT_NEGATIVE5)
    parser.add_argument('--recipe', type=Path, default=DEFAULT_RECIPE)
    parser.add_argument('--sample', type=Path, default=DEFAULT_SAMPLE)
    parser.add_argument('--runs-dir', type=Path, default=DEFAULT_RUNS)
    parser.add_argument('--out-json', type=Path, default=DEFAULT_JSON)
    parser.add_argument('--out-md', type=Path, default=DEFAULT_MD)
    args = parser.parse_args(argv)
    report = build(args.ledger, args.dev24, args.recipe, args.negative5,
                   sample_path=args.sample, runs_dir=args.runs_dir)
    args.out_json.write_text(json.dumps(report, ensure_ascii=False,
                                        indent=2) + '\n')
    args.out_md.write_text(markdown(report))
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report['refresh_allowed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
