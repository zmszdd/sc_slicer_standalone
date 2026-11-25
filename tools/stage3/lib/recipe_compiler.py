"""Deterministically compile ready observable recipes into binding entries.

The binding model may leave a symbol ``UNBOUND`` even when the typed
observable IR already contains a unique, type-compatible executable recipe.
This module closes that gap without inventing source facts: it only selects
recipes emitted by ``lib.observable_recipes`` and records which recipe was used.
"""
from __future__ import annotations

import copy

from lib import observable_recipes


SCHEMA_VERSION = 'stage3-recipe-compile/1'


def ready_recipes(ir: dict, symbol: str) -> list[dict]:
    row = ((ir or {}).get('symbols') or {}).get(symbol) or {}
    plan = row.get('recipe_plan') or {}
    recipes = [recipe for recipe in plan.get('recipes') or []
               if observable_recipes.is_compile_ready(
                   recipe, observable_recipes.expected_kind(row),
                   row.get('checkpoint'))]
    if not recipes:
        return []
    # A high-confidence recipe always wins over a merely compilable medium
    # one.  Mixing confidence levels would let a weak fallback mask a unique
    # strong recipe.
    best = 'high' if any(row.get('confidence') == 'high' for row in recipes) \
        else 'medium'
    return [recipe for recipe in recipes if recipe.get('confidence') == best]


def compile_binding(binding: dict, ir: dict, *, only_unbound: bool = True
                    ) -> tuple[dict, list[dict]]:
    """Return ``(binding, changes)`` with deterministic recipe bindings.

    A recipe is used only when it is unique after deduplication.  Competing
    executable recipes stay unresolved rather than silently picking one.
    """
    result = copy.deepcopy(binding)
    changes: list[dict] = []
    entries = result.get('bindings')
    if not isinstance(entries, dict):
        return result, changes
    for symbol, entry in sorted(entries.items()):
        if not isinstance(entry, dict):
            continue
        current = str(entry.get('solidity_expr') or '').strip()
        if only_unbound and current and current != 'UNBOUND':
            continue
        recipes = ready_recipes(ir, symbol)
        expressions = {str(recipe['expression']) for recipe in recipes}
        if len(expressions) != 1:
            continue
        recipe = next(row for row in recipes
                      if row['expression'] in expressions)
        entry['solidity_expr'] = recipe['expression']
        statements = list(recipe.get('solidity_stmts') or [])
        if statements:
            entry['solidity_stmts'] = statements
        if recipe.get('solidity_type'):
            entry['solidity_type'] = recipe['solidity_type']
        if recipe.get('checkpoint') and not entry.get('checkpoint'):
            entry['checkpoint'] = recipe['checkpoint']
        entry['recipe_compile'] = {
            'schema_version': SCHEMA_VERSION,
            'recipe_id': recipe.get('recipe_id'),
            'kind': recipe.get('kind'),
            'confidence': recipe.get('confidence'),
            'checkpoint': recipe.get('checkpoint'),
            'visible_at_injection': recipe.get('visible_at_injection'),
            'evidence': list(recipe.get('evidence') or []),
        }
        changes.append({
            'symbol': symbol,
            'expression': recipe['expression'],
            'recipe_id': recipe.get('recipe_id'),
            'confidence': recipe.get('confidence'),
        })
    return result, changes
