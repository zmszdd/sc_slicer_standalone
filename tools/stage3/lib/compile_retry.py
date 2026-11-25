"""Compile-failure diagnostics for stage-3 patched projects.

When a patched project fails to compile, this module extracts the identifiers
forge reports (preferring the ``^^^`` caret-annotated source lines). It does
**not** neutralize bindings to constants: a constant safety binding vacates
the differential witness and turns a compile error into a silent false
negative, so the pipeline now records the reported identifiers and stops with
``compile_error`` for the outer binding-repair loop to fix.
"""
from __future__ import annotations

import re

from lib.solidity_scan import IDENT, KEYWORDS

_ERROR_LINE_RE = re.compile(
    r'(?:Undeclared identifier|Identifier not found|not found or not visible|'
    r'not visible|is not declared|not a member|Member .* not found|'
    r'not implicitly convertible|Invalid type)', re.IGNORECASE)

_CLASS_PATTERNS = (
    ('undeclared_identifier', re.compile(
        r'Undeclared identifier|Identifier not found|not found or not visible|'
        r'is not declared|not visible', re.I)),
    ('error_keyword', re.compile(r'\berror\b.*(?:warning|reserved)|'
                                 r'warning.*\berror\b', re.I)),
    ('stack_too_deep', re.compile(r'too deep in the stack|stack too deep', re.I)),
    ('tuple_shape', re.compile(
        r'tuple|component|not implicitly convertible.*\(\s*\w+\s*,', re.I)),
    ('type_mismatch', re.compile(
        r'not implicitly convertible|Invalid type|Type .* is not', re.I)),
    ('visibility', re.compile(
        r'not visible|visibility|private|internal', re.I)),
)


def _tokens(line: str) -> set[str]:
    return {token for token in re.findall(IDENT, line)
            if token not in KEYWORDS and len(token) > 2}


def error_identifiers(stderr: str) -> set[str]:
    """Identifiers forge complained about, preferring caret-marked source lines."""
    lines = stderr.splitlines()
    seen: set[str] = set()
    for i, line in enumerate(lines):
        if '^' not in line:
            continue
        if i > 0:
            seen |= _tokens(lines[i - 1])
    if not seen:
        for line in lines:
            if _ERROR_LINE_RE.search(line):
                seen |= _tokens(line)
    return seen


def failure_classes(stderr: str | None) -> list[str]:
    """Classify deterministic compile diagnostics for routing/audit."""
    text = str(stderr or '')
    if not text.strip():
        return []
    return [name for name, pattern in _CLASS_PATTERNS
            if pattern.search(text)]
