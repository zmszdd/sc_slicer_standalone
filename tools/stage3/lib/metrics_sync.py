"""Deterministic bridge from stage-3 run artifacts to authoritative metrics.

The stage-3 pipeline adjudicates each claim into a ``stage3-summary.json``;
the authoritative four-metric report currently reads a hand-maintained
``p2_auto_reproductions_*.json``. This module closes that gap:

* select the **latest** auto (non-reference-patch, non-negative) run per case;
* accept ``violation_reproduced`` only for judge-valid cases not already in the
  base TP set or the existing P2 auto list;
* rewrite the P2 auto file (preserving curated notes), then regenerate
  ``unified_metrics`` / ``independence_report`` / ``recall_recoverability`` /
  ``repro_failure_triage``.

Honesty guards: reference-patch runs (``refpatch``) and negative pilots
(``_neg``) are excluded from the automatic口径; only the latest run decides,
so a superseded historical reproduction cannot resurrect a case.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]  # tools/stage3
METRICS = ROOT / 'evaluation' / 'metrics'
P2_AUTO = METRICS / 'p2_auto_reproductions_20261110.json'
VALID_STATES = {'valid', 'fixed', 'wontfix'}


def project_of(case: str) -> str:
    return case.split('__')[0]


def _is_auto_dir(name: str, case: str) -> bool:
    if not name.startswith(case + '__'):
        return False
    if 'refpatch' in name or '_neg' in name:
        return False
    return True


def latest_run_summary(runs_dir: Path, case: str) -> dict | None:
    if not runs_dir.is_dir():
        return None
    dirs = [d for d in runs_dir.iterdir()
            if d.is_dir() and _is_auto_dir(d.name, case)]
    dirs.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    for d in dirs:
        summary = d / 'stage3-summary.json'
        if not summary.is_file():
            continue
        try:
            return json.loads(summary.read_text())
        except json.JSONDecodeError:
            continue
    return None


def discover_auto_reproductions(runs_dir: Path, judge_cases: list[dict],
                                base_tp: set[str],
                                existing_auto: set[str]) -> list[dict]:
    """Return auto reproductions not yet recorded in base TP or P2 auto."""
    valid = {row['case'] for row in judge_cases
             if row.get('validity') in VALID_STATES}
    out: list[dict] = []
    for case in sorted(valid):
        if case in base_tp or case in existing_auto:
            continue
        summary = latest_run_summary(runs_dir, case)
        if not summary or summary.get('consistency_verdict') != 'violation_reproduced':
            continue
        forge = summary.get('forge') or {}
        exploit = forge.get('exploit') or {}
        original = (exploit.get('original') or {}).get('status')
        patched = (exploit.get('patched') or {}).get('status')
        if original != 'Success' or patched != 'Failure':
            continue
        run_dir = runs_dir / (summary.get('run_id') or '')
        routing = summary.get('routing') or {}
        out.append({
            'case': case,
            'project': project_of(case),
            'route': routing.get('route') or 'auto',
            'stage2_batch': routing.get('stage2_batch'),
            'run_id': summary.get('run_id'),
            'claim_id': summary.get('claim_id'),
            'verdict': 'violation_reproduced',
            'fix_kind': 'auto_detected_from_run',
            'note': (f"latest auto run: original={original}, patched={patched} "
                     f"({(exploit.get('patched') or {}).get('reason') or ''})"),
        })
    return out


def read_json(path: Path):
    return json.loads(path.read_text())


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def run_metrics_scripts(python: str = sys.executable) -> list[tuple[str, int]]:
    scripts = ['unified_metrics.py', 'independence_report.py',
               'recall_recoverability.py', 'repro_failure_triage.py']
    results = []
    for name in scripts:
        proc = subprocess.run([python, str(METRICS / name)], cwd=str(METRICS),
                              capture_output=True, text=True)
        results.append((name, proc.returncode))
    return results


def reconcile_positive_eval(runs_dir: Path,
                            positive_eval: Path | None = None,
                            judge_ground_truth: Path | None = None) -> int:
    """Mark judge-valid cases whose latest auto run reproduced as reproduced=1.

    ``judge_anchor.py`` derives TP from ``positive_eval_105.json``; this closes
    the gap between latest run artifacts and the hand-maintained eval snapshot.
    """
    positive_eval = Path(positive_eval) if positive_eval else \
        METRICS / 'positive_eval_105.json'
    pe = read_json(positive_eval)
    judge_ground_truth = Path(judge_ground_truth) if judge_ground_truth else \
        METRICS / 'judge_ground_truth.json'
    gt = read_json(judge_ground_truth)
    valid = {row['case'] for row in gt.get('cases', [])
             if row.get('validity') in VALID_STATES}
    changed = 0
    for row in pe.get('cases', []):
        case = row.get('case')
        if case not in valid:
            continue
        summary = latest_run_summary(runs_dir, case)
        if not summary or summary.get('consistency_verdict') != 'violation_reproduced':
            continue
        exploit = ((summary.get('forge') or {}).get('exploit') or {})
        if (((exploit.get('original') or {}).get('status') != 'Success')
                or ((exploit.get('patched') or {}).get('status') != 'Failure')):
            continue
        if int(row.get('reproduced') or 0) == 1:
            continue
        row['reproduced'] = 1
        verdicts = [v for v in (row.get('verdicts') or []) if v]
        claim_id = summary.get('claim_id')
        claim_ids = row.get('claim_ids') or row.get('bound_claim_ids') or []
        if claim_id and claim_ids and len(claim_ids) == len(verdicts):
            try:
                verdicts[claim_ids.index(claim_id)] = 'violation_reproduced'
                row['verdicts'] = verdicts
                changed += 1
                continue
            except ValueError:
                pass
        if 'violation_reproduced' in verdicts:
            row['verdicts'] = verdicts
            changed += 1
            continue
        row['verdicts'] = ['violation_reproduced'] + [
            v for v in verdicts if v != 'violation_reproduced']
        changed += 1
    write_json(positive_eval, pe)
    return changed


def sync(runs_dir: Path | None = None) -> dict:
    runs_dir = Path(runs_dir) if runs_dir else ROOT / 'runs'
    judge = read_json(METRICS / 'judge_ground_truth.json')
    ja = read_json(METRICS / 'judge_anchored_metrics.json')
    p2 = read_json(P2_AUTO)

    base_tp = {row['case'] for row in ja.get('tp_rows', [])}
    existing_auto = {row['case'] for row in p2.get('cases', [])
                     if row.get('verdict') == 'violation_reproduced'}
    new_rows = discover_auto_reproductions(runs_dir, judge.get('cases', []),
                                           base_tp, existing_auto)

    cases = list(p2.get('cases', []))
    known = {row['case'] for row in cases}
    for row in new_rows:
        if row['case'] in known:
            continue
        cases.append(row)
    p2['cases'] = cases
    p2['count'] = len(cases)
    p2['generated'] = '2026-11-11'
    write_json(P2_AUTO, p2)

    reconciled = reconcile_positive_eval(runs_dir)

    judge_cmd = [sys.executable, str(METRICS / 'judge_anchor.py')]
    for blind in ('positive_eval_blind_invalid.json',
                  'positive_eval_blind_invalid_remaining.json',
                  'positive_eval_blind_invalid_sukukfi_p1.json'):
        judge_cmd += ['--blind-invalid-eval', str(METRICS / blind)]
    judge = subprocess.run(judge_cmd, cwd=str(METRICS),
                           capture_output=True, text=True)
    report = subprocess.run([
        sys.executable, '-m', 'cli.metrics_report',
        '--positive-eval', str(METRICS / 'positive_eval_105.json'),
        '--negative-results', str(METRICS / 'negative_results_merged_78.json'),
        '--judge-metrics', str(METRICS / 'judge_anchored_metrics.json'),
        '--out-json', str(METRICS / 'metrics_report_105.json'),
        '--out-md', str(METRICS / 'metrics_report_105.md'),
    ], cwd=str(ROOT), capture_output=True, text=True)

    script_results = run_metrics_scripts()
    return {
        'new_auto_cases': new_rows,
        'p2_auto_count': len(cases),
        'positive_eval_reconciled': reconciled,
        'judge_anchor_exit': judge.returncode,
        'metrics_report_exit': report.returncode,
        'metrics_scripts': [{'script': name, 'exit': code}
                            for name, code in script_results],
    }
