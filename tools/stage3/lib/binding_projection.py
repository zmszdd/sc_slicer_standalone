"""Deterministically project report-derived symbols onto code observables.

Stage 2 remains report-only: it never reads source code and it remains the
authority for P/I/V semantics.  This module runs on the Stage-3 side and only
fills ``UNBOUND`` binding entries with expressions that are already present in
the observable IR built from the case source.  It never invents an identifier
or weakens the claim.

Every candidate is verified against the full binding lint before it is used.
Ambiguous or unverifiable candidates stay ``UNBOUND`` and remain unresolved.
"""
from __future__ import annotations

import copy

from lib import observable_recipes

SCHEMA_VERSION = 'stage3-binding-projection/1'


def candidate_options(ir: dict, symbol: str) -> list[dict]:
    """Return source-grounded, patch-visible candidates in priority order."""
    row = ((ir or {}).get('symbols') or {}).get(symbol)
    if not isinstance(row, dict):
        return []
    expected_kind = observable_recipes.expected_kind(row)
    seen: set[str] = set()
    options: list[dict] = []
    for candidate in row.get('candidates') or []:
        if not isinstance(candidate, dict) or candidate.get('ambiguous'):
            continue
        if not candidate.get('visible_at_injection', True):
            continue
        expression = str(candidate.get('expression') or '').strip()
        if not expression or expression in seen:
            continue
        if observable_recipes.type_compatible(
                expected_kind, candidate.get('solidity_type')) is False:
            continue
        seen.add(expression)
        options.append(candidate)
    options.sort(key=lambda item: (
        not bool(item.get('ready_eligible')),
        -int(item.get('match_score') or 0),
        str(item.get('candidate_id') or ''),
        str(item.get('expression') or ''),
    ))
    return options


def project_binding(binding: dict, ir: dict, *, validate=None
                    ) -> tuple[dict, list[dict]]:
    """Fill verifiable UNBOUND entries from code-visible IR candidates.

    ``validate`` receives a trial binding and returns a list of error strings.
    When absent, only unique top candidates are accepted so the caller remains
    deterministic without a source lint.
    """
    result = copy.deepcopy(binding)
    entries = result.get('bindings')
    if not isinstance(entries, dict):
        return result, []
    changes: list[dict] = []
    for symbol, entry in sorted(entries.items()):
        if not isinstance(entry, dict):
            continue
        if str(entry.get('solidity_expr') or '').strip() != 'UNBOUND':
            continue
        options = candidate_options(ir, symbol)
        if not options:
            continue
        candidate = None
        if validate is None:
            if len(options) == 1:
                candidate = options[0]
        else:
            for option in options:
                trial = copy.deepcopy(result)
                trial_entry = trial['bindings'][symbol]
                trial_entry['solidity_expr'] = str(option['expression'])
                errors = validate(trial)
                if not errors:
                    candidate = option
                    break
        if candidate is None:
            continue
        entry['solidity_expr'] = str(candidate['expression'])
        metadata = {
            'schema_version': SCHEMA_VERSION,
            'candidate_id': candidate.get('candidate_id'),
            'kind': candidate.get('kind'),
            'checkpoint': candidate.get('checkpoint'),
            'visible_at_injection': bool(
                candidate.get('visible_at_injection', True)),
            'match_score': candidate.get('match_score'),
            'evidence': list(candidate.get('evidence') or []),
        }
        entry['binding_projection'] = metadata
        if candidate.get('solidity_stmts'):
            entry['solidity_stmts'] = list(candidate['solidity_stmts'])
        if candidate.get('solidity_type') and not entry.get('solidity_type'):
            entry['solidity_type'] = candidate['solidity_type']
        changes.append({
            'symbol': symbol,
            'expression': candidate['expression'],
            'candidate_id': candidate.get('candidate_id'),
            'match_score': candidate.get('match_score'),
            'options_considered': len(options),
        })
    return result, changes
