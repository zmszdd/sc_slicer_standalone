"""Minimal forge runner and result parser."""
from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path


FORGE_BIN = os.environ.get('FORGE', 'forge')


class CompileError(RuntimeError):
    """forge compiled nothing (no JSON on stdout) but exited non-zero."""

    def __init__(self, stderr: str, project_root: Path):
        self.stderr = stderr
        self.project_root = Path(project_root)
        super().__init__(f'forge compile failed for {self.project_root}')


def run_forge(project_root: Path) -> dict:
    proc = subprocess.run(
        [FORGE_BIN, 'test', '--root', str(project_root), '--json'],
        capture_output=True, text=True)
    if proc.returncode != 0 and not proc.stdout.strip():
        raise CompileError(proc.stderr.strip()[:2000], project_root)
    try:
        parsed = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f'forge returned invalid JSON for {project_root}: {exc}') from exc
    return parsed


_ERROR_START_RE = re.compile(r'^\s*(Error\s*\(|ParserError|TypeError|DeclarationError|SyntaxError)')


def _summarize_compile_error(stderr: str, head_chars: int = 400,
                             tail_chars: int = 6000) -> str:
    """Keep the actual compiler errors, not the warning flood that precedes them.

    Forge prints hundreds of warnings before the first real ``Error (…)``, so a
    naive head-truncation hides the identifier that ``error_identifiers`` needs.
    We return a short head plus every ``Error …`` block (5 lines each), falling
    back to head+tail when no error block is found.
    """
    lines = stderr.splitlines()
    blocks: list[str] = []
    for index, line in enumerate(lines):
        if _ERROR_START_RE.match(line):
            blocks.extend(lines[index:index + 5])
    if blocks:
        return '\n'.join([stderr[:head_chars], '...', '\n'.join(blocks)])[:tail_chars + head_chars + 100]
    return (stderr[:head_chars] + '\n...\n' + stderr[-tail_chars:])[:tail_chars + head_chars + 100]


def run_forge_safe(project_root: Path) -> dict:
    """Return either ``{"ok": True, "result": <forge json>}`` or
    ``{"ok": False, "compile_error": <stderr>, "project": str}``.

    Unlike ``run_forge`` this never raises for a compile failure, so callers
    can persist a ``compile-error.json`` record instead of silently losing a
    verdict.
    """
    proc = subprocess.run(
        [FORGE_BIN, 'test', '--root', str(project_root), '--json'],
        capture_output=True, text=True)
    if proc.returncode != 0 and not proc.stdout.strip():
        return {
            'ok': False,
            'project': str(project_root),
            'compile_error': _summarize_compile_error(proc.stderr),
        }
    try:
        parsed = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        return {
            'ok': False,
            'project': str(project_root),
            'compile_error': f'forge returned invalid JSON: {exc}',
        }
    return {'ok': True, 'result': parsed}


def _find_test(parsed: dict, test_name: str) -> dict | None:
    for suite in parsed.values():
        if not isinstance(suite, dict):
            continue
        results = suite.get('test_results', {})
        for key, value in results.items():
            normalized = key.removesuffix('()')
            if normalized == test_name or key == test_name:
                return value
    return None


def test_result(parsed: dict, test_name: str) -> dict | None:
    if not test_name:
        return None
    result = _find_test(parsed, test_name)
    if result is None:
        return None
    return {
        'name': test_name,
        'status': result.get('status'),
        'reason': result.get('reason'),
    }


def first_failure_reason(parsed: dict) -> str | None:
    """Return ``<test>: <reason>`` for the first failed test (often ``setUp``).

    When a harness ``setUp`` fails, the exploit test never appears in the forge
    output, so callers need this to explain why no verdict could be produced.
    """
    for suite in parsed.values():
        if not isinstance(suite, dict):
            continue
        results = suite.get('test_results', {})
        for key, value in results.items():
            if isinstance(value, dict) and value.get('status') == 'Failure':
                return f'{key}: {value.get("reason") or "failure"}'
    return None
