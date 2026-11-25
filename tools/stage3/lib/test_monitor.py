"""Test-level monitor route for cross-contract stage-3 claims.

The fast path injects one ``assert(!P || I)`` into a business function.  That
is deliberately conservative: a symbol owned by another contract is invisible
from that function even when the PoC test can see both contracts.  This module
relocates the probe to the PoC test function instead, where the harness has
the deployment handles and can observe the same trace after the exploit.

It is a deterministic source-level transformation, not a semantic weakening:
the assertion and snapshots are unchanged; only the observation point moves.
"""
from __future__ import annotations

import copy
import os
from pathlib import Path

from lib.spec_loader import SpecError
from lib.patch import _function_body, relocate_before_snapshots

SCHEMA_VERSION = 'stage3-test-monitor/1'


def _candidate_files(case_dir: Path):
    seen = set()
    for root in (case_dir / 'test', case_dir / 'src'):
        if not root.is_dir():
            continue
        for path in sorted(root.rglob('*.sol')):
            resolved = path.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            yield path


def find_test_location(case_dir: Path, probe: dict) -> tuple[Path, str] | None:
    """Find the source file containing ``probe.exploit_test``.

    Returns ``(path, patch_file)`` where ``patch_file`` is relative to
    ``case_dir/src`` so ``inject_patched_sources`` can resolve it from a copied
    project root (including ``../test/...``).
    """
    test_name = str((probe or {}).get('exploit_test') or '').strip()
    if not test_name:
        return None
    contract = (probe or {}).get('contract')
    for path in _candidate_files(Path(case_dir)):
        try:
            source = path.read_text()
            _function_body(source, test_name, contract)
        except (OSError, SpecError):
            continue
        rel = os.path.relpath(path, Path(case_dir) / 'src')
        return path, rel.replace(os.sep, '/')
    return None


def build_monitor_binding(binding: dict, case_dir: Path) -> tuple[dict | None, dict]:
    """Return a test-level binding candidate plus a routing record.

    ``None`` means the binding is already injected at the test function, or no
    unique test location was found.  In either case the caller keeps the
    existing fast/reference route.
    """
    case_dir = Path(case_dir)
    probe = binding.get('probe') or {}
    patch = binding.get('patch') or {}
    functions = patch.get('functions') or []
    current = functions[0] if functions else None
    current_name = current.get('name') if isinstance(current, dict) else current
    current_file = (current.get('file') if isinstance(current, dict)
                    else patch.get('file')) or patch.get('file')
    current_contract = (current.get('contract') if isinstance(current, dict)
                        else None) or patch.get('contract')

    location = find_test_location(case_dir, probe)
    if location is None:
        return None, {
            'schema_version': SCHEMA_VERSION,
            'status': 'unavailable',
            'reason': 'probe exploit test could not be located in src/test',
        }
    path, patch_file = location
    test_name = probe.get('exploit_test')
    if (current_name == test_name and current_file == patch_file
            and current_contract == probe.get('contract')):
        return None, {
            'schema_version': SCHEMA_VERSION,
            'status': 'already_test_level',
            'test_file': str(path),
            'patch_file': patch_file,
        }

    candidate = copy.deepcopy(binding)
    candidate_patch = candidate.setdefault('patch', {})
    candidate_patch['file'] = patch_file
    if probe.get('contract'):
        candidate_patch['contract'] = probe['contract']
    candidate_functions = candidate_patch.get('functions') or []
    if not candidate_functions:
        candidate_functions = [{'name': test_name}]
    first = candidate_functions[0]
    if isinstance(first, dict):
        first = dict(first)
        first.update({'name': test_name, 'file': patch_file})
        if probe.get('contract'):
            first['contract'] = probe['contract']
        candidate_functions[0] = first
    else:
        candidate_functions[0] = {
            'name': test_name,
            'file': patch_file,
            **({'contract': probe['contract']} if probe.get('contract') else {}),
        }
    candidate_patch['functions'] = candidate_functions

    candidate, anchors = relocate_before_snapshots(candidate, path.read_text())
    return candidate, {
        'schema_version': SCHEMA_VERSION,
        'status': 'candidate',
        'reason': 'relocated observation to the PoC test frame',
        'test_file': str(path),
        'patch_file': patch_file,
        'probe_contract': probe.get('contract'),
        'probe_test': test_name,
        'original_target': {
            'file': current_file,
            'contract': current_contract,
            'function': current_name,
        },
        'snapshot_anchors': sorted(anchors),
    }
