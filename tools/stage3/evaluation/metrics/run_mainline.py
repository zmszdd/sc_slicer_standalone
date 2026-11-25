#!/usr/bin/env python3
"""Deterministic mainline executor for the stratified four-metric sample.

This is the executable half of the mainline contract: given the stratified
``mainline_sample_mini.json`` and the verified flatten corpus, it

1. runs stage-2 report->P/I/V for every positive case that lacks a
   ``stage3-spec.json`` (batches of five via the official DeepSeek entry);
2. assembles a goldset from the produced stage-2 runs;
3. runs stage-3 eval per case with resume (existing bindings are reused, so
   re-running never burns fresh binding LLM calls for completed cases);
4. writes ``mainline_eval.json`` and regenerates the mainline metrics.

Pass ``--include-negatives`` to execute the sampled negative lane as well.  A
negative case only reaches Stage-3 when it has both a witness/neutral flatten
slice and a Stage-2 spec with formalized claims.  Cases without a slice stay
``no_slice``; cases whose Stage-2 needs impact review stay blocked; zero-claim
cases get one bounded Stage-2 retry and still remain excluded if claims stay
empty.  Negative execution is explicit so the default positive-only behaviour
of existing automation is unchanged.

Pass ``--max-cases`` to run a bounded pilot; omit it (or pass 0) for the full
sample.  The script is safe to interrupt and re-run.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from threading import Lock
from pathlib import Path

HERE = Path(__file__).resolve().parent
STAGE3 = HERE.parents[1]
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
if str(STAGE3) not in sys.path:
    sys.path.insert(0, str(STAGE3))
from lib import claim_population, mainline_protocol, path_config
from lib.spec_loader import SpecError, load_stage2_run
from mainline_backlog import _stage2_failure_label
from current_denominator import _runs_claims, audit, metric_eligible_cases
import negative_recovery_gate as recovery_gate

STAGE3_TIMEOUT_SECONDS = 1800

SAMPLE = HERE / 'mainline_sample_mini.json'
FLATTEN_DEFAULT = path_config.verified_flatten_root()
STAGE2_OUT_DEFAULT = HERE / 'mainline_stage2_out'
GOLDSET_DEFAULT = HERE / 'mainline_goldset'
CASES_DEFAULT = STAGE3 / 'cases'
EVAL_OUT_DEFAULT = HERE / 'mainline_eval.json'
METRICS_OUT = HERE / 'mainline_metrics.json'
RUNS = STAGE3 / 'runs'

NEGATIVE_FLATTEN_DEFAULT = path_config.negative_flatten_root()
NEGATIVE_STAGE2_INPUT_DEFAULT = (
    path_config.c4_output_root() / 'objective_negative_stage2_inputs_20261121')
NEGATIVE_STAGE2_OUT_DEFAULT = HERE / 'mainline_negative_stage2_out'
NEGATIVE_GOLDSET_DEFAULT = HERE / 'mainline_goldset_1_7_31_neg'
NEGATIVE_CASES_DEFAULT = (
    path_config.c4_output_root() / 'objective_negative_cases_1_7_16')
NEGATIVE_EVAL_OUT_DEFAULT = HERE / 'mainline_neg_eval_1_7_33.json'
NEGATIVE_CANDIDATE_GOLDSET_DEFAULT = HERE / 'mainline_negative_candidate_goldset'
NEGATIVE_CANDIDATE_STAGE2_DEFAULT = HERE / 'mainline_negative_candidate_stage2'
NEGATIVE_CANDIDATE_EVAL_DEFAULT = HERE / 'mainline_negative_candidate_eval.json'
NEGATIVE_REJECTED_RUNS_DEFAULT = HERE / 'mainline_negative_rejected_runs'
NEGATIVE_BACKUP_ROOT_DEFAULT = (
    path_config.c4_output_root() / 'negative_recovery_backup')


def _run(argv: list[str], cwd: Path, check: bool = True) -> subprocess.CompletedProcess:
    proc = subprocess.run([sys.executable, '-m'] + argv, cwd=str(cwd),
                          text=True)
    if check and proc.returncode != 0:
        raise SystemExit(f'command failed ({proc.returncode}): {" ".join(argv)}')
    return proc


def _load(path: Path):
    return json.loads(path.read_text()) if path.is_file() else None


def _save(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')


def _has_stage2(out: Path, case: str) -> bool:
    return (out / case / 'stage3-spec.json').is_file()


def _clear_failed_stage2(out: Path, case: str, *, only_402: bool = False) -> None:
    """Make a previously-failed stage-2 case retryable under --resume.

    The batch command skips any case whose ``status.json`` already exists, so a
    deterministic stage-2 fix would otherwise never reach already-failed
    sample cases.  Only the status marker is removed; the evidence directory
    is kept and the batch will park it before re-running.

    ``only_402`` scopes the retry to DeepSeek HTTP 402 (billing/quota)
    failures, leaving genuine formalization failures untouched so a later
    resume pass does not re-burn LLM calls on cases that need a stage-2 fix.
    """
    status = out / case / 'status.json'
    if not status.is_file():
        return
    try:
        data = json.loads(status.read_text())
    except (json.JSONDecodeError, OSError):
        return
    if data.get('stage2_can_continue') is True:
        return
    error = data.get('error') or ''
    if only_402 and 'HTTP 402' not in error:
        return
    status.unlink()
    print(f'stage2 retry cleared: {case}', flush=True)


def _run_stage2_batch(cases: list[str], flatten: Path, out: Path,
                      provider: str = 'deepseek',
                      model: str | None = None,
                      prompt_version: str = (
                          mainline_protocol.STAGE2_PROMPT_VERSION),
                      continue_on_review: bool = False) -> None:
    """Run stage-2 in a five-case manifest; individual failures do not abort."""
    manifest = {
        'data_root': str(flatten),
        'cases': [{'id': c, 'case_directory': c} for c in cases],
    }
    tmp = out / '.manifest.json'
    _save(tmp, manifest)
    root = STAGE3.parents[1]
    proc = subprocess.run(
        [sys.executable, str(root / 'main.py'), 'batch',
         '--manifest', str(tmp), '--allow-report-upload',
         '--output', str(out), '--resume', '--provider', provider]
        + (['--model', model] if model else [])
        + (['--continue-on-review'] if continue_on_review else [])
        + ['--prompt-version', prompt_version],
        cwd=str(root), text=True)
    print(proc.stdout, flush=True)
    if proc.returncode != 0:
        print(proc.stderr, flush=True)


def _build_goldset(sample: dict, stage2_out: Path, goldset: Path) -> list[str]:
    ready = []
    runs_dir = goldset / 'runs_01'
    runs_dir.mkdir(parents=True, exist_ok=True)
    for case in sample.get('positive_cases', []):
        if _has_stage2(stage2_out, case):
            dst = runs_dir / case
            if not (dst / 'stage3-spec.json').is_file():
                if dst.exists():
                    continue
                src = stage2_out / case
                # reflink unavailable across /tmp and repo; copy only the
                # stage-3 inputs instead of the whole stage-2 tree.
                dst.mkdir(parents=True, exist_ok=True)
                for name in ('stage3-spec.json', 'constraints.json',
                             'formalization.json'):
                    if (src / name).is_file():
                        (dst / name).write_bytes((src / name).read_bytes())
            ready.append(case)
    _save(goldset / 'selection.json', {
        'schema_version': 'mainline-goldset/1',
        'cases': [{'case': c} for c in ready],
    })
    return ready


def _has_negative_slice(case: str, flatten_root: Path) -> bool:
    return (Path(flatten_root) / case / 'contract.flattened.t.sol').is_file()


def _negative_source_root(goldset: Path) -> Path | None:
    manifest = _load(Path(goldset) / 'manifest.json') or {}
    source = str(manifest.get('source') or '')
    if not source:
        return None
    source = Path(source)
    if not source.is_absolute():
        source = STAGE3.parents[1] / source
    return source if source.is_dir() else None


def _negative_stage2_candidates(case: str, goldset: Path,
                                stage2_out: Path) -> list[Path]:
    candidates = [Path(stage2_out) / case]
    for run_dir in sorted(Path(goldset).glob('runs_*')):
        candidates.append(run_dir / case)
    source = _negative_source_root(goldset)
    if source is not None:
        candidates.append(source / case)
    found: list[Path] = []
    seen: set[Path] = set()
    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved in seen or not candidate.is_dir():
            continue
        seen.add(resolved)
        found.append(candidate)
    return found


def _stage2_spec(stage2_dir: Path) -> dict | None:
    path = Path(stage2_dir) / 'stage3-spec.json'
    if not path.is_file():
        return None
    try:
        spec = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return None
    return spec if isinstance(spec, dict) else None


def _formalized_claims(stage2_dir: Path) -> list[str]:
    try:
        loaded = load_stage2_run(Path(stage2_dir))
    except (OSError, SpecError):
        return []
    return [str(row['claim_id']) for row in loaded['spec'].get('claims') or []
            if isinstance(row, dict) and row.get('claim_id')]


def _negative_stage2_status(case: str, candidates: list[Path]) -> dict:
    for candidate in candidates:
        path = candidate / 'status.json'
        if not path.is_file():
            continue
        try:
            status = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(status, dict):
            return status
    return {}


def _has_stage3_run(case: str, runs_dir: Path) -> bool:
    root = Path(runs_dir)
    if not root.is_dir():
        return False
    prefix = case + '__'
    return any(entry.is_dir() and entry.name.startswith(prefix)
               for entry in root.iterdir())


def _negative_plan(cases: list[str], flatten_root: Path, goldset: Path,
                   stage2_out: Path, stage2_input_root: Path,
                   runs_dir: Path = STAGE3 / 'runs') -> list[dict]:
    """Explain the executable negative lane before spending model/forge work."""
    rows = []
    for case in cases:
        candidates = _negative_stage2_candidates(case, goldset, stage2_out)
        claims: list[str] = []
        stage2_dir = None
        for candidate in candidates:
            found = _formalized_claims(candidate)
            if found:
                claims = found
                stage2_dir = candidate
                break
        status = _negative_stage2_status(case, candidates)
        specs = [_stage2_spec(candidate) for candidate in candidates]
        spec_claims = next((spec.get('claims') or [] for spec in specs if spec),
                           [])
        spec_seen = any(spec is not None for spec in specs)
        stage2_out_attempted = (Path(stage2_out) / case / 'stage3-spec.json').is_file()
        report_ready = (Path(stage2_input_root) / case / 'report.json').is_file()
        prior_run = _has_stage3_run(case, runs_dir)

        needs_stage2 = False
        if not _has_negative_slice(case, flatten_root):
            reason = 'no_slice'
        elif claims:
            reason = 'stage3_ready'
        elif (status.get('impact_source_status')
              and status.get('impact_source_status') != 'marked_section_present'):
            reason = 'stage2_needs_impact_review'
        elif spec_seen and not spec_claims:
            reason = 'zero_claim_stage2'
            needs_stage2 = not stage2_out_attempted and not prior_run
        elif spec_seen:
            reason = 'no_formalized_claim_stage2'
        elif status.get('stage2_can_continue') is False:
            reason = 'stage2_blocked:' + _stage2_failure_label(status)
        elif not spec_seen and not report_ready:
            reason = 'no_stage2_input'
        else:
            reason = 'awaiting_stage2'
            needs_stage2 = True
        rows.append({
            'case': case,
            'reason': reason,
            'stage2_dir': str(stage2_dir) if stage2_dir is not None else None,
            'claims': len(claims),
            'needs_stage2': needs_stage2,
            'prior_run': prior_run,
            'slice_ready': reason != 'no_slice',
        })
    return rows


def _build_negative_goldset(sample: dict, ready: list[str], goldset: Path,
                            stage2_out: Path) -> list[str]:
    """Refresh only executable negative Stage-2 artifact trios in the goldset."""
    runs_dir = Path(goldset) / 'runs_01'
    runs_dir.mkdir(parents=True, exist_ok=True)
    installed = []
    for case in ready:
        candidates = _negative_stage2_candidates(case, goldset, stage2_out)
        source = next((candidate for candidate in candidates
                       if _formalized_claims(candidate)), None)
        if source is None:
            continue
        dst = runs_dir / case
        dst.mkdir(parents=True, exist_ok=True)
        for name in ('stage3-spec.json', 'constraints.json',
                     'formalization.json'):
            src_path = source / name
            dst_path = dst / name
            if not src_path.is_file():
                break
            if src_path.resolve() != dst_path.resolve():
                dst_path.write_bytes(src_path.read_bytes())
        else:
            installed.append(case)

    selection_path = Path(goldset) / 'selection.json'
    selection = _load(selection_path) or {'schema_version': 'mainline-goldset/1',
                                           'cases': []}
    existing = [str(row.get('case')) for row in selection.get('cases') or []
                if isinstance(row, dict) and row.get('case')]
    ordered = []
    wanted = set(installed) | set(existing)
    for case in list(sample.get('negative_cases') or []) + sorted(wanted):
        if case in wanted and case not in ordered:
            ordered.append(case)
    selection['cases'] = [{'case': case} for case in ordered]
    _save(selection_path, selection)
    return installed


def _run_dir_names(runs_dir: Path = RUNS) -> set[str]:
    root = Path(runs_dir)
    if not root.is_dir():
        return set()
    return {entry.name for entry in root.iterdir() if entry.is_dir()}


def _eligible_negative_cases(goldset: Path, candidate_cases: set[str],
                             runs_dir: Path = RUNS,
                             sample_path: Path = SAMPLE) -> set[str]:
    """Return candidate cases whose new runs are metric-eligible negatives."""
    original_roots = claim_population.GOLDSET_ROOTS
    try:
        claim_population.GOLDSET_ROOTS = (Path(goldset),)
        population = claim_population.current_claim_ids(sample_path)
    finally:
        claim_population.GOLDSET_ROOTS = original_roots
    sample = _load(sample_path) or {}
    rows = [row for row in _runs_claims(sample, Path(runs_dir), population)
            if row.get('case') in candidate_cases]
    eligible = metric_eligible_cases(audit(rows)['sets']['eligible_current'])
    return set(eligible['negative'])


def _prepare_stage2_subset(cases: list[str], stage2_root: Path,
                           subset_root: Path) -> list[str]:
    """Expose only promotable candidate Stage-2 dirs to the recovery gate."""
    subset_root = Path(subset_root)
    if subset_root.exists():
        shutil.rmtree(subset_root)
    subset_root.mkdir(parents=True)
    installed = []
    for case in cases:
        source = Path(stage2_root) / case
        if not (source / 'stage3-spec.json').is_file():
            continue
        os.symlink(source.resolve(), subset_root / case,
                   target_is_directory=True)
        installed.append(case)
    return installed


def _archive_rejected_runs(before: set[str], candidate_cases: set[str],
                           keep: set[str], archive_root: Path) -> list[str]:
    """Move un-promoted candidate runs out of the authoritative run index."""
    archive_root = Path(archive_root)
    moved = []
    for name in sorted(_run_dir_names() - before):
        case = next((candidate for candidate in candidate_cases
                     if name.startswith(candidate + '__')), None)
        if case is None or case in keep:
            continue
        archive_root.mkdir(parents=True, exist_ok=True)
        target = archive_root / name
        if target.exists():
            target = archive_root / f'{name}__{time.time_ns()}'
        shutil.move(str(RUNS / name), str(target))
        moved.append(name)
    return moved


def _already_eval(eval_out: Path, case: str) -> bool:
    data = _load(eval_out)
    if not data:
        return False
    for row in data.get('cases', []):
        if row.get('case') == case and row.get('status') == 'done':
            return True
    return False


FIXABLE_VERDICTS = {
    'partial_binding', 'compile_error', 'binding_error',
    'effect_observed_invariant_holds', 'inconclusive', 'binding_failed',
}


def _recount_verdicts(row: dict) -> dict:
    verdicts = row.get('verdicts') or []
    row['reproduced'] = verdicts.count('violation_reproduced')
    row['compile_blocked'] = verdicts.count('compile_blocked')
    row['compile_error'] = verdicts.count('compile_error')
    row['not_dynamically_expressible'] = verdicts.count(
        'not_dynamically_expressible')
    row['reference_patch_required'] = verdicts.count(
        'reference_patch_required')
    row['halt_witness_required'] = verdicts.count('halt_witness_required')
    row['automatic_reproduced'] = (
        row['reproduced'] - int(row.get('reference_patch_reproduced') or 0))
    return row


def _parse_claims_payload(stdout: str) -> dict | None:
    """Return the final claims payload from a verdict-loop stdout.

    ``stage3_verdict_loop`` prints one JSON object per claim as it finishes,
    then the aggregate payload (the only object carrying a ``claims`` list) at
    the end, so the stream cannot be parsed as a single JSON document. Scan
    each non-empty line and keep the last aggregate payload.
    """
    payload = None
    for line in (stdout or '').splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            candidate = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(candidate, dict) and isinstance(candidate.get('claims'), list):
            payload = candidate
    return payload


def _recover_fixable(case: str, row: dict, cases_root: Path,
                     max_rounds: int = 2) -> dict:
    """Re-run the bounded verdict loop for binding-fixable claims only."""
    claims = row.get('claim_ids') or []
    verdicts = row.get('verdicts') or []
    fixable = [cid for cid, verdict in zip(claims, verdicts)
               if verdict in FIXABLE_VERDICTS]
    if row.get('status') != 'done' or not fixable:
        return row
    case_dir = cases_root / case
    if not (case_dir / 'stage2_run').is_dir():
        return row
    argv = ['cli.stage3_verdict_loop', '--case-dir', str(case_dir),
            '--stage2-run', str(case_dir / 'stage2_run'),
            '--max-rounds', str(max_rounds),
            '--claims', ','.join(fixable)]
    try:
        proc = subprocess.run([sys.executable, '-m'] + argv, cwd=str(STAGE3),
                              text=True, timeout=STAGE3_TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired:
        return {'case': case, 'status': 'error',
                'detail': f'stage3_eval_run timeout after {STAGE3_TIMEOUT_SECONDS}s'}
    if proc.returncode != 0:
        return row
    payload = _parse_claims_payload(proc.stdout)
    if payload is None:
        return row
    recovered = {}
    for claim_row in payload.get('claims', []):
        cid = claim_row.get('claim_id')
        verdict = claim_row.get('verdict')
        if cid and verdict:
            recovered[cid] = verdict
    if not recovered:
        return row
    updated = [recovered.get(cid, verdict)
               for cid, verdict in zip(claims, verdicts)]
    row['verdicts'] = updated
    return _recount_verdicts(row)


def _run_stage3_case(case: str, goldset: Path, flatten: Path,
                     cases_root: Path, skip_llm: bool) -> dict:
    tmp_out = goldset / f'eval_{case}.json'
    argv = ['cli.stage3_eval_run', '--goldset-root', str(goldset),
            '--flatten-root', str(flatten), '--cases-root', str(cases_root),
            '--out', str(tmp_out), '--cases', case]
    if skip_llm:
        argv.append('--skip-llm')
    proc = subprocess.Popen([sys.executable, '-m'] + argv, cwd=str(STAGE3),
                            text=True, start_new_session=True,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        stdout, stderr = proc.communicate(timeout=STAGE3_TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired:
        import os
        import signal
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        proc.kill()
        proc.wait()
        return {'case': case, 'status': 'error',
                'detail': f'stage3_eval_run timeout after {STAGE3_TIMEOUT_SECONDS}s'}
    if proc.returncode != 0:
        print(stdout, flush=True)
        print(stderr, flush=True)
        return {'case': case, 'status': 'error',
                'detail': (stderr or stdout or '').strip()[:600]}
    data = _load(tmp_out)
    row = (data or {}).get('cases', [{}])[0] if data else {}
    return row or {'case': case, 'status': 'error', 'detail': 'empty eval'}


def _run_stage3_parallel(ready: list[str], goldset: Path, flatten: Path,
                         cases_root: Path, eval_out: Path,
                         concurrency: int) -> None:
    """Run stage-3 eval per case with bounded process-level parallelism."""
    eval_rows = (_load(eval_out) or {}).get('cases', [])
    by_case = {r['case']: r for r in eval_rows}
    pending = [c for c in ready if by_case.get(c, {}).get('status') != 'done']
    print(f'stage3: {len(ready) - len(pending)} done, '
          f'{len(pending)} pending, concurrency={concurrency}', flush=True)
    if not pending:
        return

    lock = Lock()

    def work(case):
        case_dir = cases_root / case
        bindings = case_dir / 'bindings'
        skip_llm = bindings.is_dir() and any(bindings.iterdir())
        print(f'eval {case} {"(reuse)" if skip_llm else "(fresh)"}',
              flush=True)
        row = _run_stage3_case(case, goldset, flatten, cases_root, skip_llm)
        row = _recover_fixable(case, row, cases_root)
        with lock:
            by_case[case] = row
            rows = [by_case[k] for k in by_case]
            _save(eval_out, {
                'schema_version': 'mainline-eval/1',
                'cases': rows,
                'total_cases': len(rows),
                'done': sum(1 for r in rows if r.get('status') == 'done'),
            })
        print(json.dumps(row, ensure_ascii=False), flush=True)
        return row

    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        futures = [pool.submit(work, c) for c in pending]
        for future in as_completed(futures):
            future.result()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sample', type=Path, default=SAMPLE)
    parser.add_argument('--flatten-root', type=Path, default=FLATTEN_DEFAULT)
    parser.add_argument('--stage2-out', type=Path, default=STAGE2_OUT_DEFAULT)
    parser.add_argument('--goldset-root', type=Path, default=GOLDSET_DEFAULT)
    parser.add_argument('--cases-root', type=Path, default=CASES_DEFAULT)
    parser.add_argument('--eval-out', type=Path, default=EVAL_OUT_DEFAULT)
    parser.add_argument('--max-cases', type=int, default=0,
                        help='bounded pilot (0 = whole sample)')
    parser.add_argument('--retry-402', action='store_true',
                        help='only clear stage-2 failures caused by DeepSeek HTTP 402')
    parser.add_argument('--stage2-provider',
                        default=mainline_protocol.STAGE2_PROVIDER,
                        choices=('opencode', 'opencode_api', 'deepseek'),
                        help='stage-2 model transport for missing cases')
    parser.add_argument('--stage2-model',
                        default=mainline_protocol.STAGE2_MODEL,
                        help='optional explicit stage-2 model id')
    parser.add_argument('--stage2-prompt-version',
                        default=mainline_protocol.STAGE2_PROMPT_VERSION,
                        help='frozen stage-2 prompt version recorded by the protocol')
    parser.add_argument('--stage3-concurrency', type=int, default=4,
                        help='parallel stage-3 eval workers (forge/LLM heavy)')
    parser.add_argument('--only-positives', action='store_true',
                        help='legacy compatibility flag; its behaviour is the default')
    parser.add_argument('--only-negatives', action='store_true',
                        help='skip the positive lane; requires --include-negatives')
    parser.add_argument('--include-negatives', action='store_true',
                        help='execute slice-ready negative cases through stage2/stage3')
    parser.add_argument('--negative-cases', default=None,
                        help='comma-separated negative case ids for a bounded retry')
    parser.add_argument('--negative-max-cases', type=int, default=0,
                        help='bounded negative pilot (0 = all selected negatives)')
    parser.add_argument('--negative-flatten-root', type=Path,
                        default=NEGATIVE_FLATTEN_DEFAULT)
    parser.add_argument('--negative-stage2-input-root', type=Path,
                        default=NEGATIVE_STAGE2_INPUT_DEFAULT)
    parser.add_argument('--negative-stage2-out', type=Path,
                        default=NEGATIVE_STAGE2_OUT_DEFAULT)
    parser.add_argument('--negative-goldset-root', type=Path,
                        default=NEGATIVE_GOLDSET_DEFAULT)
    parser.add_argument('--negative-cases-root', type=Path,
                        default=NEGATIVE_CASES_DEFAULT)
    parser.add_argument('--negative-eval-out', type=Path,
                        default=NEGATIVE_EVAL_OUT_DEFAULT)
    parser.add_argument('--negative-candidate-goldset-root', type=Path,
                        default=NEGATIVE_CANDIDATE_GOLDSET_DEFAULT)
    parser.add_argument('--negative-candidate-stage2-root', type=Path,
                        default=NEGATIVE_CANDIDATE_STAGE2_DEFAULT)
    parser.add_argument('--negative-candidate-eval-out', type=Path,
                        default=NEGATIVE_CANDIDATE_EVAL_DEFAULT)
    parser.add_argument('--negative-rejected-runs-root', type=Path,
                        default=NEGATIVE_REJECTED_RUNS_DEFAULT)
    parser.add_argument('--negative-backup-root', type=Path,
                        default=NEGATIVE_BACKUP_ROOT_DEFAULT)
    parser.add_argument('--negative-continue-on-review',
                        action=argparse.BooleanOptionalAction, default=True,
                        help='preserve review-warning claims during zero-claim retry')
    parser.add_argument('--no-metrics', action='store_true',
                        help='skip the authoritative metric refresh; use for gated reruns')
    args = parser.parse_args(argv)

    if args.only_negatives and not args.include_negatives:
        parser.error('--only-negatives requires --include-negatives')

    sample = _load(args.sample)
    if not sample:
        raise SystemExit('sample not found: ' + str(args.sample))

    positives = sample.get('positive_cases', [])
    if args.max_cases > 0:
        positives = positives[:args.max_cases]

    if not args.only_negatives:
        stage2_out = args.stage2_out
        stage2_out.mkdir(parents=True, exist_ok=True)
        for case in positives:
            if not _has_stage2(stage2_out, case):
                _clear_failed_stage2(stage2_out, case, only_402=args.retry_402)
        missing_stage2 = [c for c in positives if not _has_stage2(stage2_out, c)]
        print(f'stage2: {len(positives) - len(missing_stage2)} ready, '
              f'{len(missing_stage2)} to run', flush=True)
        for i in range(0, len(missing_stage2), 5):
            chunk = missing_stage2[i:i + 5]
            print('stage2 chunk: ' + ','.join(chunk), flush=True)
            _run_stage2_batch(chunk, args.flatten_root, stage2_out,
                              args.stage2_provider, args.stage2_model,
                              args.stage2_prompt_version)

        ready = _build_goldset(sample, stage2_out, args.goldset_root)
        print(f'goldset ready: {len(ready)} cases', flush=True)

        _run_stage3_parallel(ready, args.goldset_root, args.flatten_root,
                             args.cases_root, args.eval_out,
                             args.stage3_concurrency)

    if args.include_negatives:
        negatives = list(sample.get('negative_cases') or [])
        if args.negative_cases:
            wanted = {case.strip() for case in args.negative_cases.split(',')
                      if case.strip()}
            unknown = wanted - set(negatives)
            if unknown:
                raise SystemExit('unknown negative cases: ' + ','.join(sorted(unknown)))
            negatives = [case for case in negatives if case in wanted]
        if args.negative_max_cases > 0:
            negatives = negatives[:args.negative_max_cases]

        negative_stage2_out = args.negative_stage2_out
        negative_stage2_out.mkdir(parents=True, exist_ok=True)
        plan = _negative_plan(
            negatives, args.negative_flatten_root,
            args.negative_goldset_root, negative_stage2_out,
            args.negative_stage2_input_root)
        reasons = Counter(row['reason'] for row in plan)
        print('negative plan: ' + json.dumps(reasons, ensure_ascii=False),
              flush=True)

        needs_stage2 = [row['case'] for row in plan if row['needs_stage2']]
        for case in needs_stage2:
            _clear_failed_stage2(negative_stage2_out, case,
                                 only_402=args.retry_402)
        print(f'negative stage2: {len(negatives) - len(needs_stage2)} '
              f'already ready/blocked, {len(needs_stage2)} to run', flush=True)
        for i in range(0, len(needs_stage2), 5):
            chunk = needs_stage2[i:i + 5]
            print('negative stage2 chunk: ' + ','.join(chunk), flush=True)
            _run_stage2_batch(chunk, args.negative_stage2_input_root,
                              negative_stage2_out, args.stage2_provider,
                              args.stage2_model, args.stage2_prompt_version,
                              args.negative_continue_on_review)

        plan = _negative_plan(
            negatives, args.negative_flatten_root,
            args.negative_goldset_root, negative_stage2_out,
            args.negative_stage2_input_root)
        final_reasons = Counter(row['reason'] for row in plan)
        print('negative plan after stage2: '
              + json.dumps(final_reasons, ensure_ascii=False), flush=True)
        stage2_out_resolved = negative_stage2_out.resolve()
        candidate_cases = []
        for row in plan:
            if row['reason'] != 'stage3_ready' or not row['stage2_dir']:
                continue
            stage2_dir = Path(row['stage2_dir']).resolve()
            if stage2_dir == stage2_out_resolved / row['case']:
                candidate_cases.append(row['case'])
        print(f'negative stage3-ready: '
              f'{sum(1 for row in plan if row["reason"] == "stage3_ready")} '
              f'cases; new candidates: {len(candidate_cases)}', flush=True)

        if candidate_cases:
            candidate_goldset = args.negative_candidate_goldset_root
            installed = _build_negative_goldset(
                sample, candidate_cases, candidate_goldset, negative_stage2_out)
            if args.negative_candidate_eval_out.is_file():
                args.negative_candidate_eval_out.unlink()
            before = _run_dir_names()
            _run_stage3_parallel(
                installed, candidate_goldset, args.negative_flatten_root,
                args.negative_cases_root, args.negative_candidate_eval_out,
                args.stage3_concurrency)

            eligible = _eligible_negative_cases(
                candidate_goldset, set(candidate_cases), sample_path=args.sample)
            promote_cases = sorted(eligible)
            promoted = set()
            if promote_cases:
                subset = _prepare_stage2_subset(
                    promote_cases, negative_stage2_out,
                    args.negative_candidate_stage2_root)
                report = recovery_gate.evaluate(
                    args.sample, args.negative_goldset_root, RUNS,
                    args.negative_candidate_stage2_root)
                print('negative recovery gate: ' + json.dumps({
                    'promote_allowed': report['promote_allowed'],
                    'new_eligible_negative': report['new_eligible_negative'],
                    'errors': report['errors'],
                }, ensure_ascii=False), flush=True)
                if report['promote_allowed']:
                    stamp = datetime.now(timezone.utc).strftime(
                        'negative_recovery_backup_%Y%m%dT%H%M%SZ')
                    backup = args.negative_backup_root / stamp
                    recovery_gate.promote(
                        args.sample, args.negative_goldset_root, RUNS,
                        args.negative_candidate_stage2_root, backup)
                    promoted = set(subset)
                    print('negative candidates promoted: '
                          + ','.join(sorted(promoted)), flush=True)
            else:
                print('negative recovery gate: no new eligible negative',
                      flush=True)

            archived = _archive_rejected_runs(
                before, set(candidate_cases), promoted,
                args.negative_rejected_runs_root)
            if archived:
                print(f'negative un-promoted runs archived: {len(archived)}',
                      flush=True)
        print('negative eval summary: '
              + str(args.negative_candidate_eval_out), flush=True)

    print('eval summary: ' + str(args.eval_out), flush=True)
    if args.no_metrics:
        print('metrics refresh skipped (--no-metrics)', flush=True)
    else:
        subprocess.run([sys.executable, str(HERE / 'mainline_metrics.py')],
                       cwd=str(HERE))
        print('metrics: ' + str(METRICS_OUT), flush=True)


if __name__ == '__main__':
    main()
