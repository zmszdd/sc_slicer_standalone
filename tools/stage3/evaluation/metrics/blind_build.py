#!/usr/bin/env python3
"""Blind-set PoC skeleton build status.

The blind set is blocked by missing PoC skeletons (``test/`` + ``src/``).
This script reports, and optionally drives, the resurrection step that turns a
``sorted_flatten_path`` slice into a Foundry harness.  It records compile status
per case so stage-5 progress is observable without guessing.

Run with cwd = tools/stage3/evaluation/metrics:
    python blind_build.py                 # report current status only
    python blind_build.py --build --limit 3   # resurrect up to 3 slices
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BLIND = HERE / 'blind_set.json'
OUT_JSON = HERE / 'blind_build_status.json'
OUT_MD = HERE / 'blind_build_status.md'
REPO = Path(__file__).resolve().parents[4]
RESURRECT = REPO / 'run_sol_resurrect.sh'
PILOT_ROOT = REPO / 'runs' / 'sol_resurrect' / 'blind_pilot'
CANONICAL_ROOT = HERE / 'blind_flatten_root'
CASE_ROOT = REPO / 'tools' / 'stage3' / 'cases'


def case_output_dir(case: str) -> Path:
    return PILOT_ROOT / case


def canonical_artifact(case: str) -> Path | None:
    """Return the mainline stage-1 artifact when the flatten pass exists.

    ``blind_flatten_root`` is the canonical stage-1 contract used by
    ``manifest_gen``/``stage3_eval_run``.  The ``sol_resurrect`` pilot was a
    fallback skeleton builder and must not mask a verified flattened harness.
    """
    path = CANONICAL_ROOT / case / 'contract.flattened.t.sol'
    return path if path.is_file() else None


def artifact_path(case_dir: Path) -> Path:
    """Return the canonical resurrected file, tolerating both legacy layouts.

    ``sol_resurrect_tool`` historically wrote ``Resurrected.t.sol`` at the
    case root, while older audits looked only under ``test/``.  Treat both as
    the same stage-1 artifact so a successful build cannot be reported as
    ``missing_test``.
    """
    for candidate in (case_dir / 'test' / 'Resurrected.t.sol',
                      case_dir / 'Resurrected.t.sol'):
        if candidate.is_file():
            return candidate
    return case_dir / 'test' / 'Resurrected.t.sol'


def compile_status(case_dir: Path, artifact: Path | None = None,
                   build_dir: Path | None = None) -> dict:
    """Return compile status for one stage-1 artifact, if present."""
    test_file = Path(artifact) if artifact else artifact_path(case_dir)
    forge_dir = Path(build_dir) if build_dir else case_dir
    if not test_file.is_file():
        return {'built': False, 'compile': 'missing_test'}
    if not (forge_dir / 'foundry.toml').is_file():
        return {'built': True, 'compile': 'unverified',
                'artifact': str(test_file), 'test_entrypoint': False}
    proc = subprocess.run(
        ['forge', 'build'], cwd=str(forge_dir), capture_output=True, text=True)
    log = (proc.stdout or '') + (proc.stderr or '')
    text = test_file.read_text(errors='replace')
    status = {
        'built': True,
        'compile': 'ok' if proc.returncode == 0 else 'failed',
        'exit': proc.returncode,
        'artifact': str(test_file),
        'test_entrypoint': bool(re.search(r'\bfunction\s+test[A-Za-z0-9_]*\s*\(', text)),
        'log_tail': log[-800:],
    }
    if status['compile'] == 'failed':
        status['failure_class'] = compile_failure_class(log)
    return status


def compile_failure_class(log: str) -> str:
    """Classify a deterministic compile failure without case-specific rules."""
    text = log or ''
    if 'Stack too deep' in text or 'too deep in the stack' in text:
        return 'stack_too_deep'
    if ('Error (7858)' in text
            or 'Expected pragma, import directive or contract/' in text):
        return 'structural_parse'
    if ('Error (6651)' in text
            or 'Data location can only be specified' in text):
        return 'type_or_data_location'
    if ('Identifier not found' in text
            or 'not found or not visible' in text
            or 'not found or not unique' in text
            or 'Undeclared identifier' in text):
        return 'missing_symbol'
    if ('Error (2314)' in text or 'Expected \'{\'' in text
            or 'Expected \';\'' in text or 'Expected \',\'' in text
            or 'Expected \')\'' in text):
        return 'malformed_signature'
    return 'other'


def resurrect(case: dict) -> dict:
    case_dir = case_output_dir(case['case'])
    slice_path = case.get('sorted_flatten_path')
    if not slice_path or not Path(slice_path).is_file():
        return {'built': False, 'compile': 'missing_slice'}
    output = case_dir / 'Resurrected.t.sol'
    cmd = [str(RESURRECT), slice_path, '--config',
           str(REPO / 'config' / 'llm.env'), '--output', str(output)]
    proc = subprocess.run(cmd, capture_output=True, text=True,
                          cwd=str(REPO), timeout=600)
    status = compile_status(case_dir)
    status['resurrect_exit'] = proc.returncode
    status['resurrect_tail'] = ((proc.stdout or '') + (proc.stderr or ''))[-800:]
    return status


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', action='store_true')
    parser.add_argument('--limit', type=int, default=0,
                        help='max slices to resurrect (0 = all missing)')
    parser.add_argument('--cases', default=None,
                        help='comma-separated case ids to restrict to')
    args = parser.parse_args()

    blind = json.loads(BLIND.read_text())
    wanted = set(args.cases.split(',')) if args.cases else None
    rows = []
    built = 0
    for item in blind['cases']:
        case = item['case']
        case_dir = case_output_dir(case)
        in_scope = wanted is None or case in wanted
        canonical = canonical_artifact(case)
        if canonical is not None:
            status = compile_status(
                case_dir, artifact=canonical, build_dir=CASE_ROOT / case)
            status['stage1_route'] = 'flatten_root'
        elif artifact_path(case_dir).is_file():
            status = compile_status(case_dir)
            status['stage1_route'] = 'sol_resurrect'
        elif in_scope and args.build and (args.limit == 0 or built < args.limit):
            status = resurrect(item)
            status['stage1_route'] = 'sol_resurrect'
            built += 1
        else:
            status = {'built': False, 'compile': 'pending_resurrection'}
            status['stage1_route'] = None
        rows.append({'case': case, 'project': item['project'], **status})

    ok = sum(1 for r in rows if r.get('compile') == 'ok')
    entrypoints = sum(1 for r in rows if r.get('test_entrypoint'))
    report = {
        'schema_version': 'blind-build-status/1',
        'generated': '2026-11-13',
        'total': len(rows),
        'built': sum(1 for r in rows if r.get('built')),
        'compile_ok': ok,
        'test_entrypoints': entrypoints,
        'canonical_ready': sum(
            1 for r in rows
            if r.get('stage1_route') == 'flatten_root'
            and r.get('compile') == 'ok' and r.get('test_entrypoint')),
        'rows': rows,
    }
    OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')

    lines = [
        '# 盲测 PoC 骨架构建状态',
        '',
        '阶段一优先使用 `blind_flatten_root` 的正式 flatten 产物；'
        '`sol_resurrect` 仅作为骨架回退。',
        '',
        f'盲测样本 **{len(rows)}**；已重建 **{report["built"]}**；'
        f'编译通过 **{ok}**；有 test entrypoint **{entrypoints}**；'
        f'正式 flatten 就绪 **{report["canonical_ready"]}**。',
        '',
        '| case | project | 状态 | 阶段一路径 | forge | 失败类 | test entrypoint |',
        '| --- | --- | --- | --- | --- | --- | --- |',
    ]
    for r in rows:
        state = 'built' if r.get('built') else 'pending'
        lines.append(f"| {r['case']} | {r['project']} | {state} | "
                     f"{r.get('stage1_route') or '-'} | {r.get('compile')} | "
                     f"{r.get('failure_class') or '-'} | "
                     f"{bool(r.get('test_entrypoint'))} |")
    OUT_MD.write_text('\n'.join(lines) + '\n')

    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
