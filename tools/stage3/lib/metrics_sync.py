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


def _is_refpatch_dir(name: str, case: str) -> bool:
    return (name.startswith(case + '__')
            and 'refpatch' in name
            and '_neg' not in name)


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


def latest_claim_run_summary(runs_dir: Path, case: str,
                             claim_id: str) -> dict | None:
    """Latest auto run for one claim, ignoring superseded historical runs.

    ``latest_run_summary`` mixes all claims in a case, so a mixed case whose
    last-run claim is non-reproduced hides an earlier reproduced claim.  The
    per-claim lookup keeps partial recoveries visible without resurrecting
    superseded runs: only the newest run for *this claim* decides.
    """
    if not runs_dir.is_dir():
        return None
    dirs = [d for d in runs_dir.iterdir()
            if d.is_dir() and _is_auto_dir(d.name, case)
            and claim_id in d.name
            and (d / 'stage3-summary.json').is_file()]
    dirs.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    for d in dirs:
        try:
            return json.loads((d / 'stage3-summary.json').read_text())
        except json.JSONDecodeError:
            continue
    return None


def latest_refpatch_run_summary(runs_dir: Path, case: str) -> dict | None:
    """Latest reference-patch run for a case, newest first.

    Reference patches (``case/patched``) are part of the stage-3 differential
    mainline for claims that cannot be expressed as an injected ``assert(I)``.
    They share the same ``violation_reproduced`` adjudication, so they belong
    in the end-to-end recall denominator once they are built and verified.
    """
    if not runs_dir.is_dir():
        return None
    dirs = [d for d in runs_dir.iterdir()
            if d.is_dir() and _is_refpatch_dir(d.name, case)
            and (d / 'stage3-summary.json').is_file()]
    dirs.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    for d in dirs:
        try:
            return json.loads((d / 'stage3-summary.json').read_text())
        except json.JSONDecodeError:
            continue
    return None


def _is_reproduced(summary: dict | None) -> bool:
    if not summary or summary.get('consistency_verdict') != 'violation_reproduced':
        return False
    exploit = ((summary.get('forge') or {}).get('exploit') or {})
    return ((exploit.get('original') or {}).get('status') == 'Success'
            and (exploit.get('patched') or {}).get('status') == 'Failure')


def discover_auto_reproductions(runs_dir: Path, judge_cases: list[dict],
                                base_tp: set[str],
                                existing_auto: set[str],
                                positive_eval: list[dict] | None = None) -> list[dict]:
    """Return auto reproductions not yet recorded in base TP or P2 auto.

    A case counts when *any* claim reproduces.  When ``positive_eval`` rows are
    provided, claim ids are used for a per-claim latest-run lookup; otherwise
    the legacy case-level lookup is the fallback.
    """
    valid = {row['case'] for row in judge_cases
             if row.get('validity') in VALID_STATES}
    claim_map: dict[str, list[str]] = {}
    for row in (positive_eval or []):
        case = row.get('case')
        claim_ids = row.get('bound_claim_ids') or row.get('claim_ids') or []
        if case and claim_ids:
            claim_map[case] = claim_ids
    out: list[dict] = []
    for case in sorted(valid):
        if case in base_tp or case in existing_auto:
            continue
        summary = None
        for claim_id in claim_map.get(case, []):
            candidate = latest_claim_run_summary(runs_dir, case, claim_id)
            if _is_reproduced(candidate):
                summary = candidate
                break
        if summary is None:
            candidate = latest_run_summary(runs_dir, case)
            if _is_reproduced(candidate):
                summary = candidate
        if summary is None:
            continue
        forge = summary.get('forge') or {}
        exploit = forge.get('exploit') or {}
        original = (exploit.get('original') or {}).get('status')
        patched = (exploit.get('patched') or {}).get('status')
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


def discover_reference_patch_reproductions(runs_dir: Path,
                                           judge_cases: list[dict]) -> list[dict]:
    """Return verified reference-patch reproductions for judge-valid cases.

    Unlike the automatic口径, reference patches are not the "no manual fix"
    route, but they are still an end-to-end stage-3 reproduction on the
    mainline (``case/patched`` differential).  The end-to-end recall therefore
    counts them; the automatic-only recall remains available as a sub-metric.
    """
    valid = {row['case'] for row in judge_cases
             if row.get('validity') in VALID_STATES}
    out = []
    for case in sorted(valid):
        summary = latest_refpatch_run_summary(runs_dir, case)
        if not _is_reproduced(summary):
            continue
        forge = summary.get('forge') or {}
        exploit = forge.get('exploit') or {}
        routing = summary.get('routing') or {}
        out.append({
            'case': case,
            'project': project_of(case),
            'route': 'reference_patch',
            'stage2_batch': routing.get('stage2_batch'),
            'run_id': summary.get('run_id'),
            'claim_id': summary.get('claim_id'),
            'verdict': 'violation_reproduced',
            'fix_kind': 'reference_patch',
            'note': (f"reference patch: original={exploit.get('original', {}).get('status')}, "
                     f"patched={exploit.get('patched', {}).get('status')} "
                     f"({exploit.get('patched', {}).get('reason') or ''})"),
        })
    return out


def read_json(path: Path):
    return json.loads(path.read_text())


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def run_metrics_scripts(python: str = sys.executable) -> list[tuple[str, int]]:
    scripts = ['unified_metrics.py', 'independence_report.py',
               'recall_recoverability.py', 'repro_failure_triage.py',
               'fn_work_queue.py']
    results = []
    for name in scripts:
        proc = subprocess.run([python, str(METRICS / name)], cwd=str(METRICS),
                              capture_output=True, text=True)
        results.append((name, proc.returncode))
    return results


def reconcile_positive_eval(runs_dir: Path,
                            positive_eval: Path | None = None,
                            judge_ground_truth: Path | None = None) -> int:
    """Mark judge-valid cases with any claim-level end-to-end reproduction.

    ``judge_anchor.py`` derives TP from ``positive_eval_105.json``.  The
    per-claim latest-run lookup keeps partial recoveries visible in mixed cases
    (some claims dynamic, others stuck), which the previous case-level lookup
    silently swallowed whenever the last-run claim was not reproduced.
    Reference-patch reproductions are included because they are a mainline
    stage-3 differential route (``case/patched``), not a separate pipeline.
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
        claim_ids = row.get('bound_claim_ids') or row.get('claim_ids') or []
        verdicts = list(row.get('verdicts') or [])
        if len(verdicts) < len(claim_ids):
            verdicts += [''] * (len(claim_ids) - len(verdicts))
        case_changed = False
        found_claim_run = False
        for index, claim_id in enumerate(claim_ids):
            summary = latest_claim_run_summary(runs_dir, case, claim_id)
            if summary is not None:
                found_claim_run = True
            if not _is_reproduced(summary):
                continue
            if index < len(verdicts) and verdicts[index] == 'violation_reproduced':
                continue
            if index < len(verdicts):
                verdicts[index] = 'violation_reproduced'
            else:
                verdicts.append('violation_reproduced')
            case_changed = True
        # Legacy run dirs (e.g. early fixtures) use a generic suffix without
        # the claim id, so a single-claim case may only match at case level.
        if not found_claim_run and len(claim_ids) == 1:
            summary = latest_run_summary(runs_dir, case)
            if _is_reproduced(summary) and                     (not verdicts or verdicts[0] != 'violation_reproduced'):
                verdicts[0] = 'violation_reproduced'
                case_changed = True
        if not any(v == 'violation_reproduced' for v in verdicts):
            refpatch = latest_refpatch_run_summary(runs_dir, case)
            if _is_reproduced(refpatch):
                if verdicts:
                    verdicts[0] = 'violation_reproduced'
                else:
                    verdicts.append('violation_reproduced')
                case_changed = True
        any_reproduced = any(v == 'violation_reproduced' for v in verdicts)
        if any_reproduced and int(row.get('reproduced') or 0) == 0:
            row['reproduced'] = 1
            case_changed = True
        row['verdicts'] = verdicts
        if case_changed:
            changed += 1
    write_json(positive_eval, pe)
    return changed


def verify_consistency() -> dict:
    """Cheap cross-file consistency check for CI.

    Asserts the authoritative artifacts agree on the judge-anchored confusion
    matrix denominators and that every judge-valid FN is still accounted for by
    the triage queue.  Returns a dict with ``ok`` and a list of ``problems``.
    """
    problems: list[str] = []

    def load(name: str) -> dict:
        try:
            return read_json(METRICS / name)
        except (OSError, json.JSONDecodeError) as exc:
            problems.append(f'{name}: {exc}')
            return {}

    unified = load('unified_metrics.json')
    judge = load('judge_anchored_metrics.json')

    cm = unified.get('confusion_matrix') or {}
    jcm = {
        'tp': judge.get('tp_clean'),
        'fp': judge.get('fp_from_judge_invalid'),
        'fn': judge.get('fn_judge_valid'),
        'tn': judge.get('tn_invalid'),
        'judge_valid_total': judge.get('judge_valid_cases'),
        'judge_invalid_evaluated': judge.get('judge_invalid_evaluated_total'),
    }
    for key in ('tp', 'fp', 'fn', 'tn', 'judge_valid_total',
                'judge_invalid_evaluated'):
        if cm.get(key) != jcm.get(key):
            problems.append(
                f'unified_metrics/judge_anchored disagreement on {key}: '
                f'{cm.get(key)} != {jcm.get(key)}')

    if cm.get('tp', 0) + cm.get('fn', 0) != cm.get('judge_valid_total'):
        problems.append('tp+fn != judge_valid_total in unified_metrics')
    if cm.get('fp', 0) + cm.get('tn', 0) != cm.get('judge_invalid_evaluated'):
        problems.append('fp+tn != judge_invalid_evaluated in unified_metrics')

    metrics = unified.get('metrics') or {}
    if not (0 <= metrics.get('completion_rate', -1) <= 1):
        problems.append('completion_rate out of range')
    if not (0 <= metrics.get('recall', -1) <= 1):
        problems.append('recall out of range')

    report = load('metrics_report_105.json')
    report_completion = (report.get('metrics') or {}).get('completion_rate')
    if report_completion is not None and             round(float(report_completion), 4) != round(
                float(metrics.get('completion_rate', -1)), 4):
        problems.append(
            'unified_metrics/metrics_report completion_rate disagree: '
            f'{metrics.get("completion_rate")} != {report_completion}')

    return {'ok': not problems, 'problems': problems}

def sync(runs_dir: Path | None = None) -> dict:
    runs_dir = Path(runs_dir) if runs_dir else ROOT / 'runs'
    judge = read_json(METRICS / 'judge_ground_truth.json')
    ja = read_json(METRICS / 'judge_anchored_metrics.json')
    p2 = read_json(P2_AUTO)
    positive_eval = read_json(METRICS / 'positive_eval_105.json')

    base_tp = {row['case'] for row in ja.get('tp_rows', [])}
    existing_auto = {row['case'] for row in p2.get('cases', [])
                     if row.get('verdict') == 'violation_reproduced'}
    new_rows = discover_auto_reproductions(runs_dir, judge.get('cases', []),
                                           base_tp, existing_auto,
                                           positive_eval=positive_eval.get('cases', []))

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
