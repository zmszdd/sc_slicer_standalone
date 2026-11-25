#!/usr/bin/env python3
"""Pre-flight qualification for report-derived Foundry harnesses."""
from __future__ import annotations

import re
from pathlib import Path

SCHEMA_VERSION = 'pipeline-harness-qualification/1'
_TEST_RE = re.compile(r'\bfunction\s+(?:test\w*|invariant\w*)\s*\(')
_LIVE_RE = re.compile(r'\bvm\.createFork\b|\bcreateFork\b|RPC_URL|forkUrl')


def qualify(src: Path, *, test_name: str | None = None) -> dict:
    """Return a machine-readable harness qualification record."""
    src = Path(src)
    blockers = []
    warnings = []
    try:
        text = src.read_text(encoding='utf-8', errors='replace')
    except OSError:
        text = ''
        blockers.append('no source file')
    if text and not test_name and not _TEST_RE.search(text):
        blockers.append('no test entrypoint')
    if text and _LIVE_RE.search(text):
        blockers.append('harness forks live RPC')
    if text and 'contract ' not in text:
        blockers.append('no contract skeleton')
    if text and '#include' in text:
        blockers.append('non-Solidity include directive')
    if text and len(text.strip()) < 80:
        warnings.append('harness is unusually small; compile check required')
    return {
        'schema_version': SCHEMA_VERSION,
        'status': 'needs_input' if blockers else 'runnable',
        'source': str(src),
        'test_name': test_name,
        'blockers': blockers,
        'warnings': warnings,
    }
