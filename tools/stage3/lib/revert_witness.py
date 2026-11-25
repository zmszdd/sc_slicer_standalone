"""Evidence policy for revert-expected exploit witnesses.

A ``vm.expectRevert`` PoC proves that one call reverted.  That is only an
effect witness when the reverting call is itself the patched vulnerable
operation.

A revert used as a setup guard, a normal-functionality check, or a downstream
consequence of another operation is not accepted.  This conservative rule
avoids turning ``expectRevert`` assertions of safe behaviour into vulnerability
witnesses.  The policy is deliberately report-only: it re-adjudicates existing
revert-witness artifacts and never rewrites a run's raw verdict.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from lib.patch import (_find_revert_exploit_call,
                       _strip_block_comments_and_strings,
                       _test_function_body)
from lib.spec_loader import SpecError

SCHEMA_VERSION = 'stage3-revert-witness-evidence/1'
POLICY = 'revert-call-is-vulnerable-operation/1'
_POST_GATE_CODE = 'REVERT_EFFECT_NOT_WITNESSED'


def _read(path: Path) -> str | None:
    try:
        return path.read_text(errors='ignore')
    except OSError:
        return None


def _patch_functions(binding: dict) -> list[str]:
    patch = binding.get('patch') if isinstance(binding, dict) else {}
    functions = patch.get('functions') if isinstance(patch, dict) else None
    names: list[str] = []
    for entry in functions or []:
        name = entry.get('name') if isinstance(entry, dict) else entry
        if isinstance(name, str) and name:
            names.append(name)
    return sorted(set(names))


def _binding_path(summary: dict, case_dir: Path | None) -> Path | None:
    claim_id = str(summary.get('claim_id') or '')
    if not claim_id:
        return None
    case = Path(case_dir or summary.get('case') or '')
    if not str(case):
        return None
    return case / 'bindings' / f'{claim_id}.json'


def _load_binding(summary: dict, case_dir: Path | None) -> tuple[dict | None, str]:
    path = _binding_path(summary, case_dir)
    if path is None or not path.is_file():
        return None, 'binding_missing'
    try:
        value = json.loads(path.read_text())
    except (OSError, ValueError):
        return None, 'binding_unreadable'
    return (value if isinstance(value, dict) else None,
            'binding_loaded' if isinstance(value, dict) else 'binding_unreadable')


def _test_source(src_dir: Path | None, test_fn: str,
                 contract: str | None) -> tuple[Path, str] | None:
    if src_dir is None or not src_dir.is_dir():
        return None
    for path in sorted(src_dir.rglob('*.sol')):
        text = _read(path)
        if text is None:
            continue
        try:
            _test_function_body(text, test_fn, contract)
        except SpecError:
            continue
        return path, text
    return None


def _revert_witness_injected(run_dir: Path | None) -> bool:
    if run_dir is None:
        return False
    src = run_dir / 'patched' / 'src'
    if not src.is_dir():
        return False
    return any(('stage3_ok' in (text or '') or 'stage3_ret' in (text or ''))
               for text in (_read(path) for path in src.rglob('*.sol')))


def _calls(text: str, name: str) -> bool:
    return bool(re.search(rf'(?<![A-Za-z0-9_$]){re.escape(name)}\s*\(', text))


def _result(*, applies: bool, eligible: bool, reason: str,
            evidence: dict | None = None) -> dict:
    return {
        'schema_version': SCHEMA_VERSION,
        'policy': POLICY,
        'applies': applies,
        'eligible': eligible,
        'reason': reason,
        'evidence': evidence or {},
    }


def evaluate(summary: dict, *, run_dir: Path | None = None,
             case_dir: Path | None = None) -> dict:
    """Classify an existing run under the revert-witness evidence policy.

    ``eligible`` means the revert is a valid effect witness for the claim's
    exploit path.  It does not by itself make the run vulnerability-eligible;
    callers must still require ``metric_eligibility.vulnerability``.
    """
    if str(summary.get('consistency_verdict') or '') != 'effect_not_witnessed':
        return _result(applies=False, eligible=False,
                       reason='not_effect_not_witnessed')
    post_gate = summary.get('post_execution_gate') or {}
    if str(post_gate.get('code') or '') != _POST_GATE_CODE:
        return _result(applies=False, eligible=False,
                       reason='not_revert_effect_gate')

    witness = summary.get('witness') or {}
    if witness.get('original_status') != 'Success':
        return _result(applies=True, eligible=False,
                       reason='original_not_success', evidence=witness)
    if witness.get('patched_status') != 'Failure':
        return _result(applies=True, eligible=False,
                       reason='patched_not_failure', evidence=witness)
    if not witness.get('invariant_contradicted'):
        return _result(applies=True, eligible=False,
                       reason='invariant_not_contradicted', evidence=witness)
    if not _revert_witness_injected(run_dir):
        return _result(applies=True, eligible=False,
                       reason='revert_witness_injection_missing',
                       evidence=witness)

    binding, binding_reason = _load_binding(summary, case_dir)
    if binding is None:
        return _result(applies=True, eligible=False,
                       reason=binding_reason, evidence=witness)
    patch_functions = _patch_functions(binding)
    if not patch_functions:
        return _result(applies=True, eligible=False,
                       reason='patch_functions_missing', evidence=witness)

    probe = summary.get('probe') or {}
    test_fn = str(probe.get('exploit_test') or '')
    if not test_fn:
        return _result(applies=True, eligible=False,
                       reason='exploit_test_missing', evidence=witness)
    source_dir = ((run_dir / 'original' / 'src') if run_dir is not None
                  else (Path(case_dir or summary.get('case') or '') / 'src'))
    found = _test_source(source_dir, test_fn, probe.get('contract'))
    if found is None:
        return _result(applies=True, eligible=False,
                       reason='exploit_test_source_missing', evidence=witness)
    _path, source = found
    open_idx, close_idx = _test_function_body(
        source, test_fn, probe.get('contract'))
    body = source[open_idx + 1:close_idx]
    cleaned = _strip_block_comments_and_strings(body)
    expected = list(re.finditer(r'vm\.expectRevert\s*\([^;]*\);', cleaned))
    found_call = _find_revert_exploit_call(body)
    if not expected or found_call is None:
        return _result(applies=True, eligible=False,
                       reason='revert_call_missing', evidence=witness)

    call = found_call[2]
    method = str(call.get('method') or '')
    before = cleaned[:expected[-1].start()]
    called_before = [name for name in patch_functions if _calls(before, name)]
    is_vulnerable_operation = method in patch_functions
    evidence = {
        **witness,
        'expected_revert_method': method,
        'patch_functions': patch_functions,
        'vulnerable_calls_before_revert': called_before,
        'revert_is_vulnerable_operation': is_vulnerable_operation,
    }
    if not is_vulnerable_operation:
        return _result(applies=True, eligible=False,
                       reason='revert_not_vulnerable_operation',
                       evidence=evidence)
    return _result(applies=True, eligible=True,
                   reason='revert_is_vulnerable_operation',
                   evidence=evidence)
