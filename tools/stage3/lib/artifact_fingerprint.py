"""Stable fingerprints for Stage-3 inputs and protocol versions."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from lib import mainline_protocol


def _sha256(path: Path) -> str | None:
    try:
        return hashlib.sha256(Path(path).read_bytes()).hexdigest()
    except OSError:
        return None


def _version(module_name: str, attr: str) -> str | None:
    try:
        module = __import__(module_name, fromlist=[attr])
        return str(getattr(module, attr))
    except Exception:
        return None


def build(stage2_dir: Path, binding_path: Path | None = None) -> dict:
    stage2_dir = Path(stage2_dir)
    return {
        'schema_version': 'stage3-artifact-fingerprint/1',
        'mainline_protocol': mainline_protocol.current(),
        'stage2': {
            name: _sha256(stage2_dir / name)
            for name in ('stage3-spec.json', 'constraints.json',
                         'formalization.json')
        },
        'binding_sha256': (_sha256(Path(binding_path))
                           if binding_path is not None else None),
        'protocol_versions': {
            'observable_ir': _version('lib.observable_ir', 'SCHEMA_VERSION'),
            'observable_recipes': _version('lib.observable_recipes',
                                           'SCHEMA_VERSION'),
            'binding_lint': _version('lib.binding_validate', 'LINT_SCHEMA'),
            'execution_gate': _version('lib.execution_gate', 'SCHEMA_VERSION'),
            'witness_protocol': _version('lib.witness_protocol',
                                         'SCHEMA_VERSION'),
            'stage2_restate': _version('lib.stage2_restate', 'SCHEMA_VERSION'),
        },
    }


def write(path: Path, stage2_dir: Path,
          binding_path: Path | None = None) -> dict:
    record = build(stage2_dir, binding_path)
    Path(path).write_text(json.dumps(record, ensure_ascii=False,
                                     indent=2) + '\n')
    return record


def write_run_manifest(
    path: Path,
    *,
    run_id: str,
    created_at: str,
    stage2_dir: Path,
    binding_path: Path | None = None,
    case_dir: Path | None = None,
    claim_id: str | None = None,
    protocol: dict | None = None,
) -> dict:
    """Persist a non-mtime ordering and provenance record for one claim run."""
    stage2_dir = Path(stage2_dir)
    record = {
        'schema_version': 'stage3-run-manifest/1',
        'run_id': run_id,
        'created_at': created_at,
        'claim_id': claim_id,
        'case_dir': str(case_dir) if case_dir is not None else None,
        'mainline_protocol': protocol or mainline_protocol.current(),
        'stage2': {
            name: _sha256(stage2_dir / name)
            for name in ('stage3-spec.json', 'constraints.json',
                         'formalization.json')
        },
        'binding_sha256': (_sha256(Path(binding_path))
                           if binding_path is not None else None),
    }
    Path(path).write_text(
        json.dumps(record, ensure_ascii=False, indent=2) + '\n',
        encoding='utf-8')
    return record
