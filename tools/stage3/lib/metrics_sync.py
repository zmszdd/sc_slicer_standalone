"""Deterministic bridge from stage-3 run artifacts to authoritative metrics.

The stage-3 pipeline adjudicates each claim into a ``stage3-summary.json``.
The authoritative four-metric report is the stratified-sample
``mainline_metrics`` (``sample_mainline.py`` + ``mainline_metrics.py``), which
is gated in CI by ``verify_consistency``. The fullset/unified/105 reports stay
as diagnostic对照. This module closes the runs->artifacts gap:

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
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]  # tools/stage3
METRICS = ROOT / 'evaluation' / 'metrics'
P2_AUTO = METRICS / 'p2_auto_reproductions_20261110.json'
REFPATCH = METRICS / 'reference_patch_reproductions_20261110.json'
VALID_STATES = {'valid', 'fixed', 'wontfix'}
_RUN_STAMP_RE = re.compile(r'(?<!\d)(\d{8}T\d{6}Z)(?!\d)')


def _stamp_key(value: str) -> str | None:
    try:
        return datetime.strptime(value, '%Y%m%dT%H%M%SZ').replace(
            tzinfo=timezone.utc).isoformat()
    except (TypeError, ValueError):
        return None


def _created_at_key(value: str) -> str | None:
    try:
        parsed = datetime.fromisoformat(str(value).replace('Z', '+00:00'))
    except (TypeError, ValueError):
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).isoformat()


def _run_sort_key(run_dir: Path) -> tuple[int, str, str]:
    """Order runs by recorded time, never by filesystem mtime.

    A new-style run manifest is authoritative.  Legacy run ids contain a UTC
    stamp and remain usable; runs with neither are explicitly unordered.
    """
    manifest = run_dir / 'run-manifest.json'
    if manifest.is_file():
        try:
            record = json.loads(manifest.read_text())
            created = _created_at_key(record.get('created_at'))
            if created is not None:
                return (2, created, run_dir.name)
        except (OSError, ValueError):
            pass
    match = _RUN_STAMP_RE.search(run_dir.name)
    if match:
        stamp = _stamp_key(match.group(1))
        if stamp is not None:
            return (1, stamp, run_dir.name)
    return (0, '', run_dir.name)


def _sorted_runs(dirs: list[Path]) -> list[Path]:
    return sorted(dirs, key=_run_sort_key, reverse=True)


def project_of(case: str) -> str:
    return case.split('__')[0]


def _is_auto_dir(name: str, case: str) -> bool:
    if not name.startswith(case + '__'):
        return False
    if 'refpatch' in name or '_neg_' in name:
        return False
    return True


def _is_refpatch_dir(name: str, case: str) -> bool:
    return (name.startswith(case + '__')
            and 'refpatch' in name
            and '_neg_' not in name)


def latest_run_summary(runs_dir: Path, case: str) -> dict | None:
    if not runs_dir.is_dir():
        return None
    dirs = [d for d in runs_dir.iterdir()
            if d.is_dir() and _is_auto_dir(d.name, case)]
    for d in _sorted_runs(dirs):
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
    for d in _sorted_runs(dirs):
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
    for d in _sorted_runs(dirs):
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


def _any_current_reproduction(runs_dir: Path, case: str,
                              claim_ids: list[str]) -> bool:
    """Whether any current mainline run (auto or reference patch) reproduces.

    Prefers the per-claim latest-run lookup so mixed cases keep partial
    recoveries visible; falls back to case-level lookups for legacy dirs whose
    naming omits the claim id.
    """
    for claim_id in claim_ids:
        if _is_reproduced(latest_claim_run_summary(runs_dir, case, claim_id)):
            return True
    if _is_reproduced(latest_run_summary(runs_dir, case)):
        return True
    if _is_reproduced(latest_refpatch_run_summary(runs_dir, case)):
        return True
    return False


def revalidate_p2_auto(runs_dir: Path, judge_cases: list[dict],
                       positive_eval_cases: list[dict],
                       p2_cases: list[dict]) -> int:
    """Downgrade stale P2 auto rows that no current run backs.

    ``p2_auto_reproductions_*.json`` is a historical snapshot; after a rebind
    the case's bound claims can change, so a row whose reproduction only
    existed for a superseded claim must stop counting.  Rows are marked
    ``superseded_by_rebind`` instead of deleted so the audit trail survives.
    """
    valid = {row['case'] for row in judge_cases
             if row.get('validity') in VALID_STATES}
    claim_map: dict[str, list[str]] = {}
    for row in positive_eval_cases:
        case = row.get('case')
        claim_ids = row.get('bound_claim_ids') or row.get('claim_ids') or []
        if case and claim_ids:
            claim_map[case] = claim_ids
    changed = 0
    for row in p2_cases:
        if row.get('verdict') != 'violation_reproduced':
            continue
        case = row.get('case')
        if case not in valid:
            row['verdict'] = 'superseded_by_rebind'
            row['note'] = (row.get('note') or '').strip() + \
                ' [revalidated: case no longer judge-valid]'
            changed += 1
            continue
        if _any_current_reproduction(runs_dir, case, claim_map.get(case, [])):
            continue
        row['verdict'] = 'superseded_by_rebind'
        row['note'] = (row.get('note') or '').strip() + \
            ' [revalidated: no current reproduction]'
        changed += 1
    return changed


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
    scripts = ['sample_mainline.py', 'mainline_metrics.py',
               'mainline_stage2_triage.py', 'effect_witness_reaudit.py',
               'fullset_metrics.py', 'unified_metrics.py',
               'independence_report.py', 'recall_recoverability.py',
               'repro_failure_triage.py', 'stage2_trigger_audit.py',
               'fn_work_queue.py']
    results = []
    for name in scripts:
        args = [str(METRICS / name)]
        if name == 'sample_mainline.py':
            # The frozen authoritative sample uses the official negative pool.
            # Running without it silently falls back to the 9 GT negatives and
            # rewrites the 60-negative sample.
            args += ['--target-negatives', '60', '--seed', '20261115',
                     '--official-negative-pool',
                     'official_negative_pool_20261121.json']
        proc = subprocess.run([python, *args], cwd=str(METRICS),
                              capture_output=True, text=True)
        results.append((name, proc.returncode))
    return results


def reconcile_positive_eval(runs_dir: Path,
                            positive_eval: Path | None = None,
                            judge_ground_truth: Path | None = None) -> int:
    """Mark judge-valid cases with any claim-level end-to-end reproduction.

    ``judge_anchor.py`` derives TP from ``positive_eval_161.json``.  The
    per-claim latest-run lookup keeps partial recoveries visible in mixed cases
    (some claims dynamic, others stuck), which the previous case-level lookup
    silently swallowed whenever the last-run claim was not reproduced.
    Reference-patch reproductions are included because they are a mainline
    stage-3 differential route (``case/patched``), not a separate pipeline.
    """
    positive_eval = Path(positive_eval) if positive_eval else \
        METRICS / 'positive_eval_161.json'
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

    for name in ('sample_mainline.py', 'mainline_metrics.py',
                 'mainline_stage2_triage.py', 'effect_witness_reaudit.py',
                 'fullset_metrics.py',
                 'unified_metrics.py', 'independence_report.py',
                 'recall_recoverability.py', 'repro_failure_triage.py',
                 'stage2_trigger_audit.py', 'fn_work_queue.py'):
        if not (METRICS / name).is_file():
            problems.append(f'{name}: required metrics generator is missing')

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

    def load_optional(name: str) -> dict:
        path = METRICS / name
        if not path.is_file():
            return {}
        try:
            value = read_json(path)
        except (OSError, json.JSONDecodeError) as exc:
            problems.append(f'{name}: {exc}')
            return {}
        return value

    mainline = load_optional('mainline_metrics.json')
    if mainline:
        ml_cm = mainline.get('confusion_matrix') or {}
        ml_coverage = mainline.get('coverage') or {}
        ml_sample = mainline.get('sample') or {}
        positives_evaluated = ml_cm.get('positives_evaluated', 0)
        if ml_cm.get('tp', 0) + ml_cm.get('fn', 0) != positives_evaluated:
            problems.append('tp+fn != positives_evaluated in mainline_metrics')
        if (ml_cm.get('tp', 0) + ml_cm.get('fn', 0)
                + ml_cm.get('unevaluated_positives', 0)
                != ml_sample.get('positives', 0)):
            problems.append('tp+fn+unevaluated != sample positives in mainline_metrics')
        if ml_cm.get('fp_raw', 0) + ml_cm.get('tn', 0) != ml_cm.get(
                'negatives_evaluated'):
            problems.append('fp_raw+tn != negatives_evaluated in mainline_metrics')
        if ml_cm.get('fp_vuln', 0) + ml_cm.get('fp_impact_insufficient', 0) != ml_cm.get('fp_raw'):
            problems.append('fp_vuln+fp_impact_insufficient != fp_raw in mainline_metrics')
        ml_metrics = mainline.get('metrics') or {}
        denominator = (ml_coverage.get('positives_evaluated', 0)
                       + ml_coverage.get('positives_explicit_failure', 0))
        expected_completion = (ml_coverage.get('positives_evaluated', 0)
                               / denominator) if denominator else 0
        actual_completion = ml_metrics.get('completion_rate')
        if actual_completion is None:
            if expected_completion is not None or 'completion_rate' not in ml_metrics:
                problems.append('completion_rate disagrees with coverage in mainline_metrics')
        elif expected_completion is None or round(float(actual_completion), 4) != round(expected_completion, 4):
            problems.append('completion_rate disagrees with coverage in mainline_metrics')
        if (ml_coverage.get('positives_evaluated', 0)
                + ml_coverage.get('positives_explicit_failure', 0)
                + ml_coverage.get('positives_not_attributable', 0)
                != ml_sample.get('positives', 0)):
            problems.append('evaluated+explicit_failure+not_attributable != positives in mainline_metrics')
        for key in ('completion_rate', 'completion_sample_wide', 'accuracy',
                    'accuracy_consistency', 'recall', 'recall_consistency',
                    'accuracy_consistency_conservative',
                    'recall_consistency_conservative',
                    'recall_sample_wide', 'recall_automatic',
                    'precision_consistency', 'precision_vuln',
                    'f1_consistency', 'f1_consistency_conservative', 'f1_vuln'):
            value = ml_metrics.get(key)
            if value is not None and not (0 <= value <= 1):
                problems.append(f'{key} out of range in mainline_metrics')
        ml_cim = mainline.get('confidence_intervals') or {}
        for key in ('recall_cluster_bootstrap',
                    'precision_vuln_cluster_bootstrap'):
            ci = ml_cim.get(key)
            if not isinstance(ci, dict) or 'low' not in ci or 'high' not in ci:
                problems.append(f'{key} missing in mainline_metrics')
            elif ci['low'] is not None and ci['high'] is not None \
                    and ci['low'] > ci['high']:
                problems.append(f'{key} has inverted interval')
        refresh_gate = mainline.get('refresh_gate') or {}
        if 'refresh_ready' not in refresh_gate:
            problems.append('refresh_gate.refresh_ready missing in mainline_metrics')

    report = load('metrics_report_161.json')
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
    positive_eval = read_json(METRICS / 'positive_eval_161.json')

    stale_p2 = revalidate_p2_auto(runs_dir, judge.get('cases', []),
                                  positive_eval.get('cases', []),
                                  p2.get('cases', []))

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

    refpatch = read_json(REFPATCH)
    refpatch_rows = discover_reference_patch_reproductions(
        runs_dir, judge.get('cases', []))
    refpatch_cases = list(refpatch.get('cases', []))
    refpatch_known = {row['case'] for row in refpatch_cases}
    for row in refpatch_rows:
        if row['case'] in refpatch_known:
            continue
        refpatch_cases.append(row)
    refpatch['cases'] = refpatch_cases
    refpatch['count'] = len(refpatch_cases)
    refpatch['generated'] = '2026-11-13'
    write_json(REFPATCH, refpatch)

    reconciled = reconcile_positive_eval(runs_dir)

    judge_cmd = [sys.executable, str(METRICS / 'judge_anchor.py')]
    for blind in ('positive_eval_blind_invalid.json',
                  'positive_eval_blind_invalid_remaining.json',
                  'positive_eval_blind_invalid_sukukfi_p1.json'):
        if (METRICS / blind).is_file():
            judge_cmd += ['--blind-invalid-eval', str(METRICS / blind)]
    judge = subprocess.run(judge_cmd, cwd=str(METRICS),
                           capture_output=True, text=True)
    report = subprocess.run([
        sys.executable, '-m', 'cli.metrics_report',
        '--positive-eval', str(METRICS / 'positive_eval_161.json'),
        '--negative-results', str(METRICS / 'negative_results_merged_78.json'),
        '--judge-metrics', str(METRICS / 'judge_anchored_metrics.json'),
        '--out-json', str(METRICS / 'metrics_report_161.json'),
        '--out-md', str(METRICS / 'metrics_report_161.md'),
    ], cwd=str(ROOT), capture_output=True, text=True)

    script_results = run_metrics_scripts()
    script_failures = [name for name, code in script_results if code != 0]
    if judge.returncode != 0:
        script_failures.append('judge_anchor.py')
    if report.returncode != 0:
        script_failures.append('metrics_report')
    return {
        'new_auto_cases': new_rows,
        'new_refpatch_cases': refpatch_rows,
        'p2_auto_count': len(cases),
        'refpatch_count': len(refpatch_cases),
        'positive_eval_reconciled': reconciled,
        'p2_auto_stale': stale_p2,
        'judge_anchor_exit': judge.returncode,
        'metrics_report_exit': report.returncode,
        'metrics_scripts': [{'script': name, 'exit': code}
                            for name, code in script_results],
        'generation_ok': not script_failures,
        'generation_failures': script_failures,
    }
