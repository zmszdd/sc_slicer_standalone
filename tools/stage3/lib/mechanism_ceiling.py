"""Explicit record for claims outside the automatic-assert mechanism."""
from __future__ import annotations

SCHEMA_VERSION = 'stage3-mechanism-ceiling/1'


def record(kind: str, reason: str, **details) -> dict:
    return {
        'schema_version': SCHEMA_VERSION,
        'kind': kind,
        'reason': reason,
        'automatic_assert_available': False,
        **details,
    }
