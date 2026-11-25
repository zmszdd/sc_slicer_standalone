"""Deterministic Stage-1 harness readiness manifest.

Stage 1 may produce a self-contained Foundry flatten, a resurrected harness, or
a PoC that still depends on a live RPC fork.  This module records the route and
its blockers from the artifacts on disk; it never runs a model and never
pretends an unverified or fork-dependent harness is locally runnable.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

SCHEMA_VERSION = 'stage1-harness-manifest/1'

_TEST_RE = re.compile(r'\bfunction\s+(?:test|invariant)[A-Za-z0-9_]*\s*\(')
_IMPORT_RE = re.compile(r'''(?m)^\s*import\s+["']([^"']+)["']''')
_FORK_RE = re.compile(
    r'vm\.createFork\s*\(|vm\.forkUrl\s*\(|forkUrl\s*[:=]|'
    r'FORGE_RPC_URL|RPC_URL|createFork\s*\(', re.I)
_FIXED_BLOCK_RE = re.compile(
    r'createFork\s*\([^,]+,\s*(?:0x[0-9a-f]+|[0-9]{3,})', re.I)
_FORK_BLOCK_RE = re.compile(
    r'createFork\s*\([^,]+,\s*(0x[0-9a-f]+|[0-9]{3,})', re.I)
_FLATTEN_RE = re.compile(r'^// ---- Begin flattened source:', re.M)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def _source_files(case_dir: Path) -> list[Path]:
    files = []
    for folder in ('src', 'test'):
        root = case_dir / folder
        if root.is_dir():
            files.extend(path for path in root.rglob('*.sol')
                         if path.is_file())
    return sorted(files, key=lambda path: str(path.relative_to(case_dir)))


def _compile_hash(case_dir: Path, files: list[Path]) -> str:
    digest = hashlib.sha256()
    for path in files:
        digest.update(str(path.relative_to(case_dir)).encode())
        digest.update(b'\0')
        digest.update(path.read_bytes())
        digest.update(b'\0')
    toml = case_dir / 'foundry.toml'
    if toml.is_file():
        digest.update(b'foundry.toml\0')
        digest.update(toml.read_bytes())
    return digest.hexdigest()


def build(case_dir: Path, *, compile_status: str | None = None,
          blockers: list[str] | None = None) -> dict:
    """Inspect an assembled case and return its harness route contract."""
    case_dir = Path(case_dir)
    files = _source_files(case_dir)
    text = '\n'.join(path.read_text(errors='replace') for path in files)
    has_source = bool(files)
    has_test = bool(_TEST_RE.search(text))
    has_fork = bool(_FORK_RE.search(text))
    fixed_block = bool(_FIXED_BLOCK_RE.search(text))
    block_match = _FORK_BLOCK_RE.search(text)
    fork_block = block_match.group(1) if block_match else None
    imports = sorted(set(_IMPORT_RE.findall(text)))
    external_imports = sorted(path for path in imports
                              if not path.startswith('.'))
    vendored = (not external_imports
                or (case_dir / 'lib').is_dir()
                or (case_dir / 'remappings.txt').is_file())
    is_flatten = any(path.name == 'contract.flattened.t.sol'
                     for path in files) or bool(_FLATTEN_RE.search(text))

    if not has_source:
        route = 'no_poc_code'
    elif has_fork:
        route = 'fixed_block_anvil' if fixed_block else 'live_rpc_ceiling'
    elif has_test:
        route = 'self_contained_flatten' if is_flatten else 'local_harness'
    else:
        route = 'needs_harness'

    local = list(blockers or [])
    if not has_source:
        local.append('no_poc_code')
    if has_source and not has_test:
        local.append('no_test_entrypoint')
    if has_fork and not fixed_block:
        local.append('live_rpc_no_fixed_block')
    status = str(compile_status or 'unverified')
    if status and status not in {'ok', 'unverified'}:
        local.append(f'compile_{status}')
    local = list(dict.fromkeys(local))
    return {
        'schema_version': SCHEMA_VERSION,
        'case': case_dir.name,
        'route': route,
        'test_entrypoint': has_test,
        'forge_command': f'forge test --root {case_dir.name}',
        'compile_status': status,
        'compile_hash': _compile_hash(case_dir, files),
        'source_files': [str(path.relative_to(case_dir)) for path in files],
        'fixed_block': fixed_block,
        'fork_block': fork_block,
        'external_imports': external_imports,
        'dependencies_vendored': vendored,
        'next_action': (
            'pin_fork_block' if has_fork and not fixed_block else
            'vendor_dependencies' if external_imports and not vendored else
            'add_test_entrypoint' if has_source and not has_test else
            'supply_poc_code' if not has_source else None),
        'data_ceiling': (
            'live RPC fork without a fixed block is not a local differential '
            'evidence source' if has_fork and not fixed_block else None),
        'blockers': local,
        'local_runnable': not local,
    }


def write(case_dir: Path, *, compile_status: str | None = None,
          blockers: list[str] | None = None) -> dict:
    manifest = build(case_dir, compile_status=compile_status,
                     blockers=blockers)
    path = Path(case_dir) / 'harness-manifest.json'
    if path.is_file():
        try:
            previous = json.loads(path.read_text(encoding='utf-8'))
        except (OSError, ValueError):
            previous = {}
        if (previous.get('route') == 'negative_witness'
                and previous.get('local_runnable')
                and manifest.get('local_runnable')):
            manifest['route'] = 'negative_witness'
            manifest['test_entrypoint'] = False
            manifest['exploit_test'] = previous.get('exploit_test')
            manifest['forge_command'] = previous.get('forge_command') or (
                f"forge test --match-test {previous.get('exploit_test')}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    return manifest
