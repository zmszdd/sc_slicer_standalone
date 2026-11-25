"""Parallel three-stage runner: stage1 || stage2 -> stage3.

Each stage is executed as a subprocess (stage-2 reuse is a fast inline copy that
still records its own timeline window). Stage 3 only starts after both branches
produce their expected artifacts, so the join is deterministic.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from lib.manifest import ManifestError, load_manifest, resolve_path

ROOT = Path(__file__).resolve().parents[3]
STAGE3_DIR = ROOT / 'tools' / 'stage3'
STAGE2_ARTIFACTS = ('stage3-spec.json', 'constraints.json', 'formalization.json')


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec='milliseconds')


def _write_json(path: Path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def _sha256(path: Path) -> str | None:
    if not path.is_file():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _overlap(a: dict, b: dict) -> bool:
    for start_key in ('start',):
        for end_key in ('end',):
            if start_key in a and end_key in a and start_key in b and end_key in b:
                return a[start_key] <= b[end_key] and b[start_key] <= a[end_key]
    return False


def _record(timeline: dict, stage: str, **fields):
    row = timeline['stages'].setdefault(stage, {})
    row.update(fields)
    return row


def _build_stage1_cmd(manifest: dict, output_slice: Path,
                      base_dir: Path | None = None) -> list[str]:
    stage1 = manifest['stage1']
    input_path = resolve_path(base_dir, stage1['input']) if base_dir else Path(stage1['input'])
    cmd = ['bash', str(ROOT / 'run.sh'), '--input', str(input_path),
           '--contract', stage1['contract'], '--variable', stage1['variable'],
           '--level', str(stage1['level']), '-o', str(output_slice),
           '--no-rerun-test']
    if stage1.get('function'):
        cmd += ['--fn', stage1['function']]
    if stage1.get('compile_guarantee'):
        cmd += ['--compile-guarantee']
    return cmd


def _build_stage2_cmd(manifest: dict, base_dir: Path) -> list[str]:
    stage2 = manifest['stage2']
    cmd = [sys.executable, str(ROOT / 'main.py'), 'run',
           '--report', str(resolve_path(base_dir, stage2['report'])),
           '--output', str(resolve_path(base_dir, stage2['output']))]
    cmd += stage2.get('args', [])
    return cmd


def _resolve_stage3_config(manifest: dict, base_dir: Path) -> dict:
    """Resolve every stage-3 field consumed by ``_run_stage3``.

    Keeping this in one place prevents manifest fields from being silently
    dropped while building the child-process configuration.
    """
    stage3 = manifest['stage3']
    binding_path = resolve_path(base_dir, stage3.get('binding'))
    test_path = resolve_path(base_dir, stage3.get('test'))
    case_dir = resolve_path(base_dir, stage3['case_dir'])
    if case_dir is None:
        raise ManifestError('stage3.case_dir is required')
    return {
        'binding': str(binding_path) if binding_path is not None else None,
        'binding_rounds': stage3.get('binding_rounds'),
        'test': str(test_path) if test_path is not None else None,
        'case_dir': str(case_dir),
        'run_id': stage3.get('run_id'),
    }


def _reuse_stage2(run_dir: Path, source_run: Path,
                  verify: bool = True) -> int:
    """Copy stage-2 artifacts and replay-verify them before the join.

    ``verify=False`` is an explicit legacy-fixture opt-out.  It is never the
    default and is recorded in the reuse log so the run cannot be mistaken for
    a current-protocol artifact.
    """
    verify_log = run_dir / 'stage2-verify.log'
    with verify_log.open('w') as log:
        if not verify:
            log.write('stage2 replay verification explicitly disabled by '
                      'manifest; legacy fixture is not current-protocol '
                      'evidence\n')
            rc = 0
        else:
            rc = subprocess.call([sys.executable, str(ROOT / 'main.py'), 'verify',
                                  str(source_run)], cwd=str(ROOT),
                                 stdout=log, stderr=subprocess.STDOUT)
    if rc != 0:
        raise ManifestError(
            f'stage2 reuse failed verification ({rc}): {source_run}')
    dest = run_dir / 'stage2'
    dest.mkdir(parents=True, exist_ok=True)
    for artifact in STAGE2_ARTIFACTS:
        shutil.copy2(source_run / artifact, dest / artifact)
    if not (dest / 'stage3-spec.json').is_file():
        raise ManifestError(f'stage2 reuse failed: {source_run}')
    return rc


def _write_verdicts(run_dir: Path, mode: str, verdicts: list) -> None:
    """Persist per-claim verdicts and derive the case-level verdict."""
    reproduced = sum(1 for row in verdicts
                     if row.get('verdict') == 'violation_reproduced')
    not_reproduced = sum(1 for row in verdicts
                         if row.get('verdict') == 'violation_not_reproduced')
    if reproduced > 0:
        case_verdict = 'violation_reproduced'
    elif not_reproduced > 0:
        case_verdict = 'violation_not_reproduced'
    else:
        case_verdict = 'inconclusive'
    _write_json(run_dir / 'stage3-verdicts.json', {
        'schema_version': 'stage3-run-verdicts/1',
        'mode': mode,
        'case_verdict': case_verdict,
        'reproduced': reproduced,
        'verdicts': verdicts,
    })


def _run_stage3(case_id: str, slice_path: Path, stage2_run: Path,
                stage3: dict, run_dir: Path, run_id: str | None) -> int:
    case_dir = Path(stage3['case_dir'])
    binding = stage3.get('binding')
    assemble = [sys.executable, '-m', 'cli.stage3_assemble',
                '--name', case_id, '--src', str(slice_path),
                '--stage2-run', str(stage2_run),
                '--out', str(case_dir), '--overwrite']
    if stage3.get('test'):
        assemble += ['--test', str(stage3['test'])]
    else:
        assemble += ['--default-foundry-toml']
    if binding:
        assemble += ['--binding', str(binding)]
    with (run_dir / 'stage3-assemble.log').open('w') as log:
        rc = subprocess.call(assemble, cwd=str(STAGE3_DIR),
                             stdout=log, stderr=subprocess.STDOUT)
    if rc != 0:
        _write_verdicts(run_dir, mode='assemble_failed', verdicts=[])
        return rc

    final_run_id = run_id or stage3.get('run_id')

    if binding:
        run_cmd = [sys.executable, '-m', 'cli.stage3_pipeline',
                   '--case-dir', str(case_dir)]
        if final_run_id:
            run_cmd += ['--run-id', final_run_id]
        proc = subprocess.run(run_cmd, cwd=str(STAGE3_DIR),
                              capture_output=True, text=True)
        (run_dir / 'stage3.log').write_text(proc.stdout + proc.stderr)
        verdict = None
        claim_id = None
        try:
            summary = json.loads(proc.stdout)
            verdict = summary.get('consistency_verdict')
            claim_id = summary.get('claim_id')
        except ValueError:
            pass
        _write_verdicts(run_dir, mode='single', verdicts=[
            {'claim_id': claim_id, 'verdict': verdict, 'run_id': final_run_id},
        ])
        return proc.returncode

    bind_cmd = [sys.executable, '-m', 'cli.stage3_bind',
                '--case-dir', str(case_dir),
                '--stage2-run', str(case_dir / 'stage2_run')]
    if stage3.get('binding_rounds'):
        bind_cmd += ['--binding-rounds', str(stage3['binding_rounds'])]
    bind_proc = subprocess.run(bind_cmd, cwd=str(STAGE3_DIR),
                               capture_output=True, text=True)
    (run_dir / 'stage3-bind.log').write_text(bind_proc.stdout + bind_proc.stderr)
    if bind_proc.returncode != 0:
        _write_verdicts(run_dir, mode='bind_failed', verdicts=[])
        return bind_proc.returncode

    multi_cmd = [sys.executable, '-m', 'cli.stage3_multi',
                 '--case-dir', str(case_dir),
                 '--bindings-dir', str(case_dir / 'bindings'),
                 '--stage2-run', str(case_dir / 'stage2_run'),
                 '--run-id-prefix', case_id]
    multi_proc = subprocess.run(multi_cmd, cwd=str(STAGE3_DIR),
                                capture_output=True, text=True)
    (run_dir / 'stage3.log').write_text(multi_proc.stdout + multi_proc.stderr)
    verdicts = []
    try:
        multi = json.loads(multi_proc.stdout)
        verdicts = [{'claim_id': row.get('claim_id'),
                     'verdict': row.get('consistency_verdict'),
                     'run_id': row.get('run_id')}
                    for row in multi.get('claims', [])]
    except ValueError:
        pass
    _write_verdicts(run_dir, mode='multi', verdicts=verdicts)
    return 0 if multi_proc.returncode == 0 else multi_proc.returncode


def run_pipeline(manifest_path: Path, run_dir: Path | None = None,
                 skip_stage1: bool = False, skip_stage2: bool = False,
                 serial: bool = False, run_id: str | None = None) -> tuple[int, Path]:
    """Run the three-stage pipeline and return ``(exit_code, run_dir)``.

    Callers read ``run_dir / 'pipeline-summary.json'`` for the authoritative
    case-level verdict instead of guessing paths under ``tools/stage3/runs``.
    """
    manifest_path = manifest_path.resolve()
    manifest = load_manifest(manifest_path)
    base_dir = manifest_path.parent
    case_id = manifest['case_id']
    run_dir = (run_dir or (base_dir / 'runs' / case_id)).resolve()
    run_dir.mkdir(parents=True, exist_ok=True)
    _write_json(run_dir / 'manifest.json', manifest)

    slice_path = resolve_path(base_dir, manifest['stage1']['output_slice'])
    stage2_run = resolve_path(base_dir, manifest['stage2']['output']
                              if manifest['stage2']['report'] is not None
                              else manifest['stage2']['run_dir'])

    timeline = {'schema_version': 'pipeline-timeline/1', 'case_id': case_id,
                'stages': {}, 'overlap': None}
    procs = {}

    # stage 1
    if not skip_stage1:
        slice_path.parent.mkdir(parents=True, exist_ok=True)
        cmd = _build_stage1_cmd(manifest, slice_path, base_dir)
        _record(timeline, 'stage1', start=_now(), mode='slice',
                command=' '.join(cmd))
        log = (run_dir / 'stage1.log').open('w')
        env = os.environ.copy()
        env['LOG_FILE'] = str(run_dir / 'stage1-slicer.log')
        env['BUILD_LOG_FILE'] = str(run_dir / 'stage1-build.log')
        env['FORGE_LOG_FILE'] = str(run_dir / 'stage1-forge.log')
        p1 = subprocess.Popen(cmd, cwd=str(ROOT), stdout=log,
                              stderr=subprocess.STDOUT, env=env)
        procs['stage1'] = (p1, log)
        if serial:
            _join_one(timeline, 'stage1', p1, log)
    else:
        if not slice_path.is_file():
            raise ManifestError(f'--skip-stage1 but slice missing: {slice_path}')
        _record(timeline, 'stage1', status='skipped', output=str(slice_path))

    # stage 2
    if not skip_stage2:
        _record(timeline, 'stage2', start=_now())
        if manifest['stage2']['report'] is None:
            stage2 = manifest['stage2']
            verify_rc = _reuse_stage2(
                run_dir, stage2_run,
                verify=bool(stage2.get('reuse_verify', True)))
            _record(timeline, 'stage2', end=_now(), mode='reuse', exit_code=0,
                    verify_exit_code=verify_rc,
                    verify_disabled=not bool(stage2.get('reuse_verify', True)),
                    run_dir=str(stage2_run))
        else:
            cmd = _build_stage2_cmd(manifest, base_dir)
            _record(timeline, 'stage2', mode='run', command=' '.join(cmd))
            log = (run_dir / 'stage2.log').open('w')
            p2 = subprocess.Popen(cmd, cwd=str(ROOT), stdout=log,
                                  stderr=subprocess.STDOUT)
            procs['stage2'] = (p2, log)
            if serial:
                _join_one(timeline, 'stage2', p2, log)
    else:
        for artifact in STAGE2_ARTIFACTS:
            if not (stage2_run / artifact).is_file():
                raise ManifestError(
                    f'--skip-stage2 but {artifact} missing: {stage2_run}')
        _record(timeline, 'stage2', status='skipped', run_dir=str(stage2_run))

    if not serial:
        for name, (proc, log) in procs.items():
            _join_one(timeline, name, proc, log)

    _record_stage1_metadata(timeline, slice_path)
    stage1_row = timeline['stages'].get('stage1', {})
    stage2_row = timeline['stages'].get('stage2', {})
    timeline['overlap'] = _overlap(stage1_row, stage2_row)

    failures = []
    if not slice_path.is_file():
        failures.append(f'stage1 slice missing: {slice_path}')
    if stage1_row.get('compile_success') is False:
        failures.append('stage1 slice did not compile (compile_success=false)')
    for artifact in STAGE2_ARTIFACTS:
        if not (stage2_run / artifact).is_file():
            failures.append(f'stage2 artifact missing: {stage2_run / artifact}')
    for name, row in timeline['stages'].items():
        if row.get('exit_code') not in (0, None):
            failures.append(f'{name} exited {row.get("exit_code")}')
    if failures:
        timeline['status'] = 'failed'
        timeline['failures'] = failures
        _write_json(run_dir / 'timeline.json', timeline)
        print(json.dumps(timeline, ensure_ascii=False, indent=2))
        return 1, run_dir

    stage3_resolved = _resolve_stage3_config(manifest, base_dir)
    _record(timeline, 'stage3', start=_now())
    stage3_run_id = run_id or manifest['stage3'].get('run_id') or \
        f'{case_id}_{datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")}'
    rc = _run_stage3(case_id, slice_path, stage2_run, stage3_resolved,
                     run_dir, stage3_run_id)
    _record(timeline, 'stage3', end=_now(), exit_code=rc, run_id=stage3_run_id)
    timeline['status'] = 'ok' if rc == 0 else 'failed'
    _write_json(run_dir / 'timeline.json', timeline)
    _write_evidence(run_dir, manifest, slice_path, stage2_run,
                    stage3_run_id, timeline)
    print(json.dumps(timeline, ensure_ascii=False, indent=2))
    return rc, run_dir


def _join_one(timeline: dict, name: str, proc, log):
    rc = proc.wait()
    log.close()
    _record(timeline, name, end=_now(), exit_code=rc)


def _record_stage1_metadata(timeline: dict, slice_path: Path):
    meta_path = Path(str(slice_path) + '.v2.json')
    if not meta_path.is_file():
        return
    meta = json.loads(meta_path.read_text())
    _record(timeline, 'stage1', compile_success=meta.get('compile_success'),
            slice_effective=meta.get('slice_effective'),
            output_lines=meta.get('output_lines'))


def _write_evidence(run_dir: Path, manifest: dict, slice_path: Path,
                    stage2_run: Path, stage3_run_id: str, timeline: dict):
    verdict = None
    verdicts_file = run_dir / 'stage3-verdicts.json'
    if verdicts_file.is_file():
        verdict = json.loads(verdicts_file.read_text()).get('case_verdict')
    if verdict is None:
        stage3_summary = STAGE3_DIR / 'runs' / stage3_run_id / 'stage3-summary.json'
        if stage3_summary.is_file():
            verdict = json.loads(stage3_summary.read_text()).get('consistency_verdict')
    evidence = {
        'schema_version': 'pipeline-evidence/1',
        'case_id': manifest['case_id'],
        'overlap': timeline.get('overlap'),
        'status': timeline.get('status'),
        'stage1': {
            'slice': str(slice_path),
            'slice_sha256': _sha256(slice_path),
            'compile_success': (timeline.get('stages', {}).get('stage1', {})
                                .get('compile_success')),
        },
        'stage2': {
            'run_dir': str(stage2_run),
            'artifacts': {name: _sha256(stage2_run / name)
                          for name in STAGE2_ARTIFACTS},
        },
        'stage3': {
            'run_id': stage3_run_id,
            'consistency_verdict': verdict,
        },
        'timeline': str(run_dir / 'timeline.json'),
    }
    _write_json(run_dir / 'pipeline-summary.json', evidence)
