"""Translate a stage-2 P/I/V AST into a Solidity boolean expression.

Supports the stage-2 DSL: var, const (bool/int), and ops
and/or/not/implies/eq/ne/lt/le/gt/ge/add/sub.
"""
from __future__ import annotations

BINARY_OPS = {
    'and': '&&', 'or': '||',
    'eq': '==', 'ne': '!=', 'lt': '<', 'le': '<=', 'gt': '>', 'ge': '>=',
    'add': '+', 'sub': '-', 'mul': '*', 'div': '/', 'mod': '%',
}


def expr_to_solidity(expr: dict, bindings: dict[str, str]) -> str:
    if not isinstance(expr, dict):
        raise ValueError(f'expression node must be an object, got {expr!r}')
    if 'var' in expr:
        name = expr['var']
        if name not in bindings:
            raise ValueError(f'unbound symbol: {name}')
        return bindings[name]
    if 'const' in expr:
        value = expr['const']
        if isinstance(value, bool):
            return 'true' if value else 'false'
        if isinstance(value, int):
            return str(value)
        raise ValueError(f'unsupported const: {value!r}')
    op = expr.get('op')
    args = expr.get('args')
    if op == 'not':
        if not isinstance(args, list) or len(args) != 1:
            raise ValueError('not expects one argument')
        return f'!({expr_to_solidity(args[0], bindings)})'
    if op == 'implies':
        if not isinstance(args, list) or len(args) != 2:
            raise ValueError('implies expects two arguments')
        left = expr_to_solidity(args[0], bindings)
        right = expr_to_solidity(args[1], bindings)
        return f'(!({left}) || ({right}))'
    if op in BINARY_OPS:
        if not isinstance(args, list) or len(args) < 2:
            raise ValueError(f'{op} expects at least two arguments')
        parts = [f'({expr_to_solidity(arg, bindings)})' for arg in args]
        return f' {BINARY_OPS[op]} '.join(parts)
    raise ValueError(f'unsupported operator: {op!r}')
