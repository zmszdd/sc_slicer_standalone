"""Generic reference-patch materialization for the stage-3 M1 differential route.

The stage-3 pipeline reproduces a claim through ``case/patched`` (see
``lib.patch.build_projects``) when the safety invariant cannot be injected as a
single ``assert(!P || I)``.  This module defines the mainline data sources for
that route, in priority order:

* ``case/patched/``             -- a verbatim patched source tree.
* ``case/patched.diff``         -- a unified diff against ``case/src``.
* ``case/reference_sources.json`` -- a manifest pointing at an external source:
    - ``{"patched_src": "<path>"}`` copy a patched source tree verbatim;
    - ``{"diff": "<path>"}`` apply a unified diff from the given file;
    - ``{"repo": "<git repo>", "base": "<ref>", "fix": "<ref>"}`` generate the
      diff with ``git diff base..fix`` and apply it.

The manifest is deterministic and makes no model calls; it exists so the
25-case ``reference_patch_required`` bucket can be recovered once the audit
fixes are collected, without changing the rest of the pipeline.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
from pathlib import Path

PATCHED_DIR = 'patched'
PATCHED_DIFF = 'patched.diff'
REFERENCE_SOURCES = 'reference_sources.json'
REFERENCE_PATCH_MANIFEST = 'reference-patch-manifest.json'
FORGE_BIN = os.environ.get('FORGE', 'forge')
FORGE_TIMEOUT_SECONDS = int(os.environ.get('FORGE_TIMEOUT_SECONDS', '1800'))
_DIFF_TARGET_RE = re.compile(r'^\+\+\+\s+b/(.+)$', re.M)
_FUNCTION_RE_CACHE: dict[str, re.Pattern] = {}


class ReferencePatchError(RuntimeError):
    """Raised when a reference patch cannot be materialized deterministically."""


def _load_sources(case_dir: Path) -> dict:
    path = case_dir / REFERENCE_SOURCES
    if not path.is_file():
        return {}
    try:
        value = json.loads(path.read_text())
    except json.JSONDecodeError:
        return {}
    return value if isinstance(value, dict) else {}


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def _sha256_tree(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(root.rglob('*'), key=lambda item: str(item)):
        if path.is_file():
            digest.update(str(path.relative_to(root)).encode())
            digest.update(b'\0')
            digest.update(path.read_bytes())
            digest.update(b'\0')
    return digest.hexdigest()


def _file_overrides(sources: dict) -> dict:
    value = sources.get('files') or sources.get('file_overrides') or {}
    return dict(value) if isinstance(value, dict) else {}


def has_reference_patch(case_dir: Path) -> bool:
    """True when a supported patched source exists in ``case_dir``."""
    case_dir = Path(case_dir)
    if (case_dir / PATCHED_DIR).is_dir() or (case_dir / PATCHED_DIFF).is_file():
        return True
    sources = _load_sources(case_dir)
    return bool(sources.get('patched_src') or sources.get('diff')
                or _file_overrides(sources)
                or (sources.get('repo') and sources.get('base')
                    and sources.get('fix')))


def _apply_diff(case_dir: Path, patched: Path, diff: Path) -> Path:
    src = case_dir / 'src'
    if not src.is_dir():
        raise ReferencePatchError(
            f'missing case/src before applying {diff}')
    if not diff.is_file():
        raise ReferencePatchError(f'patch source not found: {diff}')
    shutil.copytree(src, patched)
    proc = subprocess.run(
        ['patch', '-p1', '-d', str(patched), '-i', str(diff.resolve()),
         '--forward', '--batch', '--reject-file=-'],
        capture_output=True, text=True)
    if proc.returncode != 0:
        shutil.rmtree(patched, ignore_errors=True)
        detail = (proc.stderr or proc.stdout or '').strip()
        raise ReferencePatchError(
            f'patch -p1 failed ({proc.returncode}): {detail}')
    return patched


def _git_diff(case_dir: Path, patched: Path, sources: dict) -> Path | None:
    repo = Path(sources['repo'])
    base = str(sources['base'])
    fix = str(sources['fix'])
    if not repo.is_dir() or not (repo / '.git').is_dir():
        raise ReferencePatchError(f'git repo not available: {repo}')
    proc = subprocess.run(
        ['git', '-C', str(repo), 'diff', f'{base}..{fix}', '--'],
        capture_output=True, text=True)
    if proc.returncode != 0:
        raise ReferencePatchError(
            f'git diff {base}..{fix} failed: '
            f'{(proc.stderr or "").strip()[:400]}')
    tmp = case_dir / '.reference.diff'
    tmp.write_text(proc.stdout)
    try:
        return _apply_diff(case_dir, patched, tmp)
    finally:
        tmp.unlink(missing_ok=True)


def materialize_reference_patch(case_dir: Path) -> Path:
    """Return ``case/patched``, materializing it from a supported source.

    Idempotent: an existing ``case/patched`` tree is returned untouched.
    On failure the partial tree is removed and ``ReferencePatchError`` is
    raised, so no half-built project is left behind.
    """
    case_dir = Path(case_dir)
    patched = case_dir / PATCHED_DIR
    if patched.is_dir():
        return patched

    sources = _load_sources(case_dir)
    patched_src = sources.get('patched_src')
    if patched_src:
        source = Path(str(patched_src))
        if not source.is_dir():
            raise ReferencePatchError(f'patched_src not found: {source}')
        shutil.copytree(source, patched)
        return patched

    diff = sources.get('diff')
    if diff:
        return _apply_diff(case_dir, patched, Path(str(diff)))

    if sources.get('repo') and sources.get('base') and sources.get('fix'):
        return _git_diff(case_dir, patched, sources)

    local_diff = case_dir / PATCHED_DIFF
    if local_diff.is_file():
        return _apply_diff(case_dir, patched, local_diff)

    if _file_overrides(sources):
        source = case_dir / 'src'
        if not source.is_dir():
            raise ReferencePatchError(
                f'missing case/src before applying file overrides: {case_dir}')
        shutil.copytree(source, patched)
        return patched

    raise ReferencePatchError(
        f'no {PATCHED_DIR}/ tree, {PATCHED_DIFF} or {REFERENCE_SOURCES} '
        f'source in {case_dir}')


def _source_plan(case_dir: Path) -> dict:
    patched = case_dir / PATCHED_DIR
    sources = _load_sources(case_dir)
    if patched.is_dir():
        return {'kind': 'patched_tree', 'sha256': _sha256_tree(patched),
                'target_files': sorted(
                    str(path.relative_to(patched))
                    for path in patched.rglob('*') if path.is_file())}
    if sources.get('patched_src'):
        root = Path(str(sources['patched_src']))
        if not root.is_absolute():
            root = case_dir / root
        return {'kind': 'patched_src', 'sha256': _sha256_tree(root),
                'target_files': sorted(
                    str(path.relative_to(root))
                    for path in root.rglob('*') if path.is_file())}
    if sources.get('diff'):
        path = Path(str(sources['diff']))
        if not path.is_absolute():
            path = case_dir / path
        return {'kind': 'diff', 'sha256': _sha256_file(path),
                'target_files': sorted(set(_DIFF_TARGET_RE.findall(
                    path.read_text(errors='replace'))))}
    if sources.get('repo') and sources.get('base') and sources.get('fix'):
        return {'kind': 'git_diff',
                'sha256': hashlib.sha256(
                    f"{sources['repo']}|{sources['base']}|{sources['fix']}"
                    .encode()).hexdigest(),
                'target_files': []}
    local_diff = case_dir / PATCHED_DIFF
    if local_diff.is_file():
        return {'kind': 'local_diff', 'sha256': _sha256_file(local_diff),
                'target_files': sorted(set(_DIFF_TARGET_RE.findall(
                    local_diff.read_text(errors='replace'))))}
    overrides = _file_overrides(sources)
    if overrides:
        digest = hashlib.sha256()
        for target in sorted(overrides):
            source = Path(str(overrides[target]))
            if not source.is_absolute():
                source = case_dir / source
            digest.update(target.encode() + b'\0')
            digest.update(source.read_bytes() if source.is_file() else b'')
        return {'kind': 'file_overrides', 'sha256': digest.hexdigest(),
                'target_files': sorted(overrides)}
    return {'kind': 'none', 'sha256': None, 'target_files': []}


def _function_pattern(name: str) -> re.Pattern:
    if name not in _FUNCTION_RE_CACHE:
        _FUNCTION_RE_CACHE[name] = re.compile(
            r'\bfunction\s+' + re.escape(name) + r'\s*\(')
    return _FUNCTION_RE_CACHE[name]


def _target_function_present(root: Path, name: str | None) -> bool | None:
    if not name:
        return None
    pattern = _function_pattern(name)
    for path in root.rglob('*.sol'):
        if path.is_file() and pattern.search(path.read_text(errors='replace')):
            return True
    return False


def _apply_overrides(case_dir: Path, patched: Path, sources: dict) -> list[str]:
    applied = []
    target_root = patched.resolve()
    for target, raw_source in sorted(_file_overrides(sources).items()):
        source = Path(str(raw_source))
        if not source.is_absolute():
            source = case_dir / source
        if not source.is_file():
            raise ReferencePatchError(f'override source not found: {source}')
        destination = (patched / target).resolve()
        if destination != target_root and target_root not in destination.parents:
            raise ReferencePatchError(f'override target escapes patched tree: {target}')
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        applied.append(target)
    return applied


def _validate_compile(patched: Path) -> dict:
    try:
        proc = subprocess.run(
            [FORGE_BIN, 'build', '--root', str(patched)],
            capture_output=True, text=True,
            timeout=FORGE_TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired:
        return {'ok': False,
                'reason': f'forge build timed out after {FORGE_TIMEOUT_SECONDS}s'}
    except OSError as exc:
        return {'ok': False, 'reason': f'forge build unavailable: {exc}'}
    log = (proc.stdout or '') + (proc.stderr or '')
    return {'ok': proc.returncode == 0, 'exit': proc.returncode,
            'log_tail': log[-2000:]}


def build_reference_patch(case_dir: Path, *, dry_run: bool = False,
                          target_function: str | None = None,
                          validate_compile: bool = False) -> dict:
    """Return a deterministic reference-patch plan or materialized record.

    A dry run never writes ``case/patched``.  Non-dry runs record source
    hashes, applied file overrides, target-function presence and an optional
    ``forge build`` validation in ``reference-patch-manifest.json``.
    """
    case_dir = Path(case_dir)
    sources = _load_sources(case_dir)
    plan = _source_plan(case_dir)
    record = {
        'schema_version': 'stage1-reference-patch/1',
        'case': case_dir.name,
        'source_kind': plan['kind'],
        'source_sha256': plan['sha256'],
        'target_files': plan['target_files'],
        'target_function': target_function,
        'dry_run': bool(dry_run),
        'overrides': sorted(_file_overrides(sources)),
        'blockers': [],
        'accepted': False,
    }
    if not has_reference_patch(case_dir):
        record['blockers'].append('no_reference_patch_source')
        return record
    if dry_run:
        record['accepted'] = not record['blockers']
        return record

    try:
        patched = materialize_reference_patch(case_dir)
        record['overrides_applied'] = _apply_overrides(
            case_dir, patched, sources)
    except ReferencePatchError as exc:
        record['blockers'].append(str(exc))
        return record
    record['patched'] = str(patched)
    present = _target_function_present(patched, target_function)
    record['target_function_present'] = present
    if present is False:
        record['blockers'].append('target_function_not_in_patch')
    if validate_compile:
        record['compile_validation'] = _validate_compile(patched)
        if not record['compile_validation']['ok']:
            record['blockers'].append('reference_patch_compile_failed')
    record['accepted'] = not record['blockers']
    (case_dir / REFERENCE_PATCH_MANIFEST).write_text(
        json.dumps(record, ensure_ascii=False, indent=2) + '\n')
    return record
