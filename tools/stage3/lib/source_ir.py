#!/usr/bin/env python3
"""A bounded, source-grounded index shared by binding and observability.

This is deliberately a lightweight IR rather than a full Solidity parser: it
normalizes declarations that the mainline repeatedly asks for (contracts,
functions, state, modifiers, visibility and return types) so observable
candidates can be checked against one consistent view instead of independent
ad-hoc scans.
"""
from __future__ import annotations

import re
from pathlib import Path

SCHEMA_VERSION = 'stage3-source-ir/1'

_COMMENT_RE = re.compile(r'/\*.*?\*/|//[^\n]*', re.S)
_CONTRACT_RE = re.compile(
    r'\b(contract|library|interface)\s+([A-Za-z_]\w*)'
    r'(?:\s+is\s+([^{;]+))?\s*\{', re.M)
_FUNCTION_RE = re.compile(
    r'\bfunction\s+([A-Za-z_]\w*)\s*\(([^)]*)\)\s*([^{;]*)[\{;]', re.M)
_STATE_RE = re.compile(
    r'^\s*((?:mapping\s*\([^)]*\)|[A-Za-z_]\w*(?:\[[^\]]*\])*))'
    r'\s+(public|internal|private)\s+([A-Za-z_]\w*)\s*(?:=|;)', re.M)
_MODIFIER_RE = re.compile(r'\bmodifier\s+([A-Za-z_]\w*)\s*(?:\([^)]*\))?\s*\{')
_IDENT_RE = re.compile(r'[A-Za-z_]\w*')


def _sources(src: Path, test_dir: Path | None) -> list[tuple[str, str]]:
    src = Path(src)
    paths: list[Path]
    if src.is_dir():
        paths = sorted(src.glob('*.sol'))
    elif src.is_file():
        paths = [src]
    else:
        paths = []
    if test_dir is not None:
        test_dir = Path(test_dir)
        if test_dir.is_dir():
            paths.extend(sorted(test_dir.glob('*.sol')))
        elif test_dir.is_file():
            paths.append(test_dir)
    out = []
    for path in paths:
        try:
            text = path.read_text(encoding='utf-8', errors='replace')
        except OSError:
            continue
        out.append((path.as_posix(), _COMMENT_RE.sub(' ', text)))
    return out


def _returns(tail: str) -> list[str]:
    match = re.search(r'\breturns\s*\(([^)]*)\)', tail)
    if not match:
        return []
    out = []
    for part in match.group(1).split(','):
        tokens = [token for token in _IDENT_RE.findall(part)
                  if token not in {'memory', 'calldata', 'storage'}]
        if tokens:
            out.append(tokens[0])
    return out


def build(src: Path, *, test_dir: Path | None = None) -> dict:
    """Build a normalized declaration index from the mainline source files."""
    contracts: list[dict] = []
    functions: list[dict] = []
    state: list[dict] = []
    modifiers: list[dict] = []
    by_file = _sources(src, test_dir)

    for file_name, text in by_file:
        for match in _CONTRACT_RE.finditer(text):
            bases = [base.strip() for base in (match.group(3) or '').split(',')
                     if base.strip()]
            contracts.append({
                'name': match.group(2),
                'kind': match.group(1),
                'bases': bases,
                'file': file_name,
            })
        for match in _FUNCTION_RE.finditer(text):
            tail = match.group(3) or ''
            visibility = next((word for word in ('external', 'public',
                                                 'internal', 'private')
                               if re.search(r'\b' + word + r'\b', tail)),
                              'internal')
            functions.append({
                'name': match.group(1),
                'parameters': [token for token in _IDENT_RE.findall(
                    match.group(2) or '')],
                'visibility': visibility,
                'returns': _returns(tail),
                'modifiers': [token for token in _IDENT_RE.findall(tail)
                              if token not in {'external', 'public',
                                               'internal', 'private',
                                               'returns', 'view', 'pure',
                                               'payable', 'virtual',
                                               'override'}],
                'file': file_name,
            })
        for match in _STATE_RE.finditer(text):
            state.append({
                'name': match.group(3),
                'type': match.group(1),
                'visibility': match.group(2),
                'file': file_name,
            })
        for match in _MODIFIER_RE.finditer(text):
            modifiers.append({'name': match.group(1), 'file': file_name})

    symbols: dict[str, list[dict]] = {}
    for kind, rows in (('contract', contracts), ('function', functions),
                       ('state', state), ('modifier', modifiers)):
        for row in rows:
            symbols.setdefault(row['name'], []).append({'kind': kind, **row})

    return {
        'schema_version': SCHEMA_VERSION,
        'sources': [name for name, _ in by_file],
        'contracts': contracts,
        'functions': functions,
        'state': state,
        'modifiers': modifiers,
        'symbols': symbols,
        'summary': {
            'contracts': len(contracts),
            'functions': len(functions),
            'state_vars': len(state),
            'modifiers': len(modifiers),
            'ambiguous_symbols': sorted(
                name for name, rows in symbols.items() if len(rows) > 1),
        },
    }


def annotate_observable_ir(observable: dict, source: dict) -> dict:
    """Attach SourceIR declarations to observable candidates in place."""
    result = dict(observable)
    result['source_ir'] = {
        'schema_version': SCHEMA_VERSION,
        'summary': source.get('summary', {}),
    }
    declared = set(source.get('symbols') or {})
    for row in ((result.get('symbols') or {}).values()):
        for candidate in row.get('candidates') or []:
            identifiers = set(_IDENT_RE.findall(str(candidate.get('expression') or '')))
            candidate['source_ir_grounded'] = bool(identifiers & declared)
            candidate['source_ir_refs'] = sorted(identifiers & declared)
    return result
