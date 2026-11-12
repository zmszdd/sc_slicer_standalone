"""Expressibility classification for stage-3 safety invariants.

The stage-3 pipeline turns each claim's safety invariant (I) into a boolean
Solidity expression injected at the PoC test function. That only works when
the invariant's symbols are *observable* at the injection point. Two otherwise
distinct failure modes have been conflated by the outer verdict loop:

* ``observable_but_misbound`` -- the code computes the value but the binding
  names the wrong identifier/contract (fixable: rebind).
* ``not_dynamically_expressible`` -- the code never computes the value at the
  injection point, or the invariant lives in another contract that is not in
  the injection point's visibility closure (NOT fixable by rebinding; only a
  reference patch or an explicit "not verifiable" terminal matters).

This module turns the deterministic source-visibility analysis already in
``binding_validate.lint_binding`` into a routing gate, so the loop stops
retrying claims whose invariants cannot be expressed and the evaluation
exposes the true dynamic-verification ceiling.
"""
from __future__ import annotations

import re
from pathlib import Path

from lib.binding_validate import lint_binding

# Ordered by severity: the most specific, least fixable category wins.
CROSS_CONTRACT = 'cross_contract_reference'
UNOBSERVABLE = 'unobservable'
BINDING_ERROR = 'binding_error'
EXPRESSIBLE = 'expressible'

_SYMBOL_RE = re.compile(r'^bindings\.([^.]+)\.solidity_expr$')


def _symbol_of(where: str) -> str | None:
    match = _SYMBOL_RE.match(where or '')
    return match.group(1) if match else None


def _category(message: str) -> str:
    if message.startswith('cross-contract reference:'):
        return CROSS_CONTRACT
    if 'not declared in src' in message:
        return UNOBSERVABLE
    return BINDING_ERROR


def classify_lint(lint: dict, safety_symbols: set[str] | None = None) -> dict:
    """Classify a binding from an existing ``lint_binding`` record.

    ``safety_symbols`` scopes the *structural* ceiling to I (safety) symbols
    only. A cross-contract/unobservable reference on a P or V symbol is a
    rebindable binding error, not ``reference_patch_required``, because the
    assertion only needs I to be expressible at the injection point.
    When ``safety_symbols`` is ``None`` the conservative historical behaviour
    is kept (any cross-contract symbol is a ceiling).
    """
    problems = lint.get('problems') or []
    symbol_rows: dict[str, dict] = {}
    other_problems: list[dict] = []
    for problem in problems:
        symbol = _symbol_of(problem.get('where') or '')
        category = _category(problem.get('message') or '')
        if symbol is not None and category in (CROSS_CONTRACT, UNOBSERVABLE):
            row = symbol_rows.setdefault(symbol, {
                'symbol': symbol, 'category': category, 'problems': []})
            if category != row['category']:
                # Most specific wins within one symbol.
                order = [CROSS_CONTRACT, UNOBSERVABLE]
                if order.index(category) < order.index(row['category']):
                    row['category'] = category
            row['problems'].append({
                'where': problem.get('where'),
                'message': problem.get('message'),
            })
        else:
            other_problems.append(problem)

    expressible_symbols: list[str] = []
    cross_contract_symbols: list[str] = []
    unobservable_symbols: list[str] = []
    for symbol, row in sorted(symbol_rows.items()):
        structural = (safety_symbols is None or symbol in safety_symbols)
        if not structural:
            for problem in row['problems']:
                other_problems.append({
                    'where': problem.get('where'),
                    'message': (problem.get('message', '') + ' '
                                '(non-safety symbol: rebindable)').strip(),
                    'severity': 'error',
                })
            continue
        if row['category'] == CROSS_CONTRACT:
            cross_contract_symbols.append(symbol)
        else:
            unobservable_symbols.append(symbol)

    if cross_contract_symbols:
        expressibility = CROSS_CONTRACT
    elif unobservable_symbols:
        expressibility = UNOBSERVABLE
    elif any(p.get('severity') == 'error' for p in other_problems):
        expressibility = BINDING_ERROR
    else:
        expressibility = EXPRESSIBLE

    reference_patch_required = expressibility == CROSS_CONTRACT
    return {
        'schema_version': 'stage3-expressibility/1',
        'expressibility': expressibility,
        'reference_patch_required': reference_patch_required,
        'dynamically_expressible': expressibility == EXPRESSIBLE,
        'expressible_symbols': sorted(set(expressible_symbols)),
        'cross_contract_symbols': sorted(set(cross_contract_symbols)),
        'unobservable_symbols': sorted(set(unobservable_symbols)),
        'other_problems': other_problems,
    }


def classify(binding: dict, src: Path, *, test_dir: Path | None = None,
             strict: bool = True, safety_symbols: set[str] | None = None) -> dict:
    """Classify a binding directly from ``binding.json`` + Solidity sources."""
    lint = lint_binding(binding, src, test_dir=test_dir, strict=strict,
                        safety_symbols=safety_symbols)
    result = classify_lint(lint, safety_symbols=safety_symbols)
    result['lint'] = {
        'schema_version': lint.get('schema_version'),
        'summary': lint.get('summary'),
    }
    return result
