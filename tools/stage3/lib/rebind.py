"""Deterministic binding repair for compile-level stage-2 -> stage-3 misbinding.

The stage-3 injection model renders each symbol's ``solidity_expr`` verbatim
into a patched Solidity function. Two mechanical misbindings recur and are
silently downgraded to ``partial_binding`` by the compile retry:

* A scalar comparison against a tuple-returning call (``msg.value ==
  messenger.quoteUnstakeWithBuffer(x)``) cannot compile; the call must be
  destructured into a local scalar first.
* A signed-returning call (``accountant.totalBackingSigned()``) assigned to the
  default unsigned snapshot type ``uint256`` cannot compile; the snapshot must
  be typed ``int256``.

This module rewrites those cases deterministically from the flattened source so
they never reach the neutralizing retry. It is intentionally conservative: it
only touches an entry when the source declares the referenced function or
struct and the rewrite is unambiguous.
"""
from __future__ import annotations

import copy
import re
from pathlib import Path

from lib.solidity_scan import IDENT

# Return type tokens that need a signed snapshot declaration.
_SIGNED_TYPES = {
    'int', 'int8', 'int16', 'int24', 'int32', 'int40', 'int48', 'int56',
    'int64', 'int72', 'int80', 'int88', 'int96', 'int104', 'int112',
    'int120', 'int128', 'int136', 'int144', 'int152', 'int160', 'int168',
    'int176', 'int184', 'int192', 'int200', 'int208', 'int216', 'int224',
    'int232', 'int240', 'int248', 'int256',
}

_SIGNED_RE = re.compile(r'^int(?:8|16|24|32|40|48|56|64|72|80|88|96|104|112|'
                        r'120|128|136|144|152|160|168|176|184|192|200|208|216|'
                        r'224|232|240|248|256)?$')

_FUNC_RE = re.compile(
    rf'\bfunction\s+({IDENT})\s*\(([^)]*)\)[^{{}}]*?\breturns\s*'
    rf'\(([^)]*)\)', re.S)

_STRUCT_RE = re.compile(rf'\bstruct\s+({IDENT})\s*\{{([^{{}}]*)\}}', re.S)
_STRUCT_FIELD_RE = re.compile(
    rf'\b({IDENT}(?:\s*\[[^\]]*\])?)\s+({IDENT})\s*;')
_MAPPING_GETTER_RE = re.compile(
    rf'\bmapping\([^)]*\)\s+public\s+({IDENT})\s*;')
_MAPPING_TO_STRUCT_RE = re.compile(
    rf'\bmapping\([^)]*=>\s*({IDENT})\)\s+public\s+({IDENT})\s*;')

# A member call: `a.b(...)` possibly with nested parentheses in the args.
_CALL_RE = re.compile(
    rf'\b({IDENT}(?:\s*\.\s*{IDENT})*)\s*\(', re.M)


def _strip_type_name(type_text: str) -> str:
    """Return the bare type token, dropping a trailing return-var name."""
    text = type_text.strip()
    match = re.match(r'([A-Za-z_$][A-Za-z0-9_$]*(?:\s*\[[^\]]*\])*)', text)
    return match.group(1).strip() if match else text


def _return_types(returns: str) -> list[str]:
    if not returns.strip():
        return []
    depth = 0
    parts: list[str] = []
    current: list[str] = []
    for char in returns:
        if char == '(':
            depth += 1
        elif char == ')':
            depth -= 1
        if char == ',' and depth == 0:
            parts.append(''.join(current).strip())
            current = []
        else:
            current.append(char)
    if ''.join(current).strip():
        parts.append(''.join(current).strip())
    return [_strip_type_name(part) for part in parts if part]


def parse_source_signatures(source: str) -> dict:
    """Parse function returns, struct fields and public mapping getters.

    This is a best-effort lexical scan that supports the flattened single-file
    slices stage-3 receives; it does not claim a full Solidity parse.
    """
    functions: dict[str, list[dict]] = {}
    for match in _FUNC_RE.finditer(source):
        name = match.group(1)
        params = match.group(2)
        arity = len([p for p in _return_types(params) if p]) if params.strip() else 0
        returns = _return_types(match.group(3))
        functions.setdefault(name, []).append({'arity': arity, 'returns': returns})

    structs: dict[str, list[dict]] = {}
    for match in _STRUCT_RE.finditer(source):
        name = match.group(1)
        body = match.group(2)
        fields = []
        for field in _STRUCT_FIELD_RE.finditer(body):
            fields.append({'type': field.group(1).strip(),
                           'name': field.group(2)})
        structs.setdefault(name, fields)

    mapping_getters: dict[str, str] = {}
    for match in _MAPPING_TO_STRUCT_RE.finditer(source):
        struct_name = match.group(1)
        getter_name = match.group(2)
        if struct_name in structs:
            mapping_getters[getter_name] = struct_name
    for match in _MAPPING_GETTER_RE.finditer(source):
        name = match.group(1)
        mapping_getters.setdefault(name, '')

    return {'functions': functions, 'structs': structs,
            'mapping_getters': mapping_getters}


def _call_leaf(call_expr: str) -> str:
    head = call_expr.split('(', 1)[0]
    parts = [p.strip() for p in head.split('.')]
    return parts[-1] if parts else head


def _return_info(sigs: dict, call_expr: str) -> list[str] | None:
    leaf = _call_leaf(call_expr)
    if leaf in sigs['mapping_getters']:
        struct_name = sigs['mapping_getters'][leaf]
        fields = sigs['structs'].get(struct_name)
        if fields:
            return [field['type'] for field in fields]
        return None
    overloads = sigs['functions'].get(leaf) or []
    if not overloads:
        return None
    # Prefer the overload with the largest arity; the flattened PoC harness
    # nearly always calls the getter with all required arguments.
    return max(overloads, key=lambda o: o['arity'])['returns']


def _member_index(sigs: dict, call_expr: str, member: str) -> int | None:
    leaf = _call_leaf(call_expr)
    if leaf in sigs['mapping_getters']:
        struct_name = sigs['mapping_getters'][leaf]
        fields = sigs['structs'].get(struct_name) or []
        for index, field in enumerate(fields):
            if field['name'] == member:
                return index
        return None
    overloads = sigs['functions'].get(leaf) or []
    for overload in overloads:
        for index, typ in enumerate(overload['returns']):
            # Return names are not preserved by the parser; compare against the
            # named return values is unavailable, so member-by-name only works
            # for struct-backed mapping getters.
            pass
    return None


def _balanced_call_end(expr: str, start: int) -> int:
    depth = 0
    for i in range(start, len(expr)):
        if expr[i] == '(':
            depth += 1
        elif expr[i] == ')':
            depth -= 1
            if depth == 0:
                return i
    return -1


def _destructure_stmt(call_expr: str, ret_types: list[str],
                      prefix: str) -> tuple[str, str]:
    temps = [f'{prefix}_{i}' for i in range(len(ret_types))]
    decls = ', '.join(f'{typ} {name}' for typ, name in zip(ret_types, temps))
    return f'({decls}) = {call_expr};', temps


def _rewrite_entry(entry: dict, sigs: dict, changes: list[str],
                    seq: list[int]) -> None:
    expr = str(entry.get('solidity_expr') or '')
    if not expr.strip() or expr.strip() == 'UNBOUND':
        return
    stmts = list(entry.get('solidity_stmts') or [])
    if isinstance(stmts, str):
        stmts = [stmts]

    # Signed snapshot typing for before-checkpoint numeric symbols.
    if (entry.get('checkpoint') == 'before'
            and entry.get('kind') == 'numeric_value'
            and not entry.get('solidity_type')):
        calls = list(_CALL_RE.finditer(expr))
        signed = None
        for call in calls:
            end = _balanced_call_end(expr, call.end() - 1)
            call_expr = expr[call.start():end + 1]
            rets = _return_info(sigs, call_expr)
            if not rets or len(rets) != 1:
                continue
            if _SIGNED_RE.match(rets[0]):
                signed = signed or rets[0]
        if signed:
            entry['solidity_type'] = signed
            changes.append(f'signed snapshot type {signed} for '
                           f'{expr[:60]}')

    # Tuple-returning calls: scalar comparison -> destructure first component;
    # member access -> destructure and reference the matching component.
    replaced = False
    for call in _CALL_RE.finditer(expr):
        open_idx = call.end() - 1
        end = _balanced_call_end(expr, open_idx)
        if end < 0:
            continue
        call_expr = expr[call.start():end + 1]
        rets = _return_info(sigs, call_expr)
        if not rets or len(rets) <= 1:
            continue
        member_match = re.match(r'\s*\.\s*(' + IDENT + r')\b',
                                expr[end + 1:])
        if member_match:
            member = member_match.group(1)
            index = _member_index(sigs, call_expr, member)
            if index is None:
                continue
            prefix = f'__stage3_{seq[0]}'
            seq[0] += 1
            stmt, temps = _destructure_stmt(call_expr, rets, prefix)
            token = f'{call_expr}.{member}'
            if token not in expr:
                continue
            expr = expr.replace(token, temps[index], 1)
            stmts.append(stmt)
            changes.append(f'tuple member {call_expr}.{member} -> '
                           f'{temps[index]}')
            replaced = True
        else:
            # Scalar comparison against a tuple-returning call. Only rewrite
            # when the call is an operand of a binary comparison.
            before = expr[:call.start()]
            after = expr[end + 1:]
            if not re.search(r'(==|!=|>=|<=|>|<)\s*$', before) and \
                    not re.match(r'^\s*(==|!=|>=|<=|>|<)', after):
                continue
            prefix = f'__stage3_{seq[0]}'
            seq[0] += 1
            stmt, temps = _destructure_stmt(call_expr, rets, prefix)
            expr = expr.replace(call_expr, temps[0], 1)
            stmts.append(stmt)
            changes.append(f'tuple call {call_expr} -> {temps[0]}')
            replaced = True

    if replaced or stmts != (entry.get('solidity_stmts') or []):
        entry['solidity_expr'] = expr
        if stmts:
            entry['solidity_stmts'] = stmts


def _rewrite_zero_arg_length(entry: dict, sigs: dict, changes: list[str]) -> None:
    """Repair ``instance.fn.length`` when ``fn`` is a zero-arg array getter."""
    expr = str(entry.get('solidity_expr') or '')
    if '.length' not in expr:
        return
    pattern = re.compile(
        rf'\b((?:{IDENT}\s*\.\s*)*({IDENT}))\s*\.\s*length\b')
    def repl(match):
        full = match.group(1)
        leaf = match.group(2)
        overloads = sigs['functions'].get(leaf) or []
        zero_arg_array = any(
            o['arity'] == 0 and o['returns'] and
            o['returns'][0].startswith(('address', 'uint', 'int', 'bytes'))
            and '[' in o['returns'][0]
            for o in overloads)
        if zero_arg_array:
            changes.append(f'zero-arg getter {full}.length -> {full}().length')
            return f'{full}().length'
        return match.group(0)
    new_expr = pattern.sub(repl, expr)
    if new_expr != expr:
        entry['solidity_expr'] = new_expr


def load_source(src) -> str:
    """Read all Solidity under ``src`` into one text block."""
    src_path = Path(src)
    if src_path.is_file():
        return src_path.read_text()
    parts = []
    for sol in sorted(src_path.glob('**/*.sol')):
        try:
            parts.append(sol.read_text())
        except OSError:
            continue
    return '\n'.join(parts)


def rebind_binding(binding: dict, source: str) -> tuple[dict, list[str]]:
    """Return ``(repaired_binding, changes)`` for one claim binding.

    ``binding`` is deep-copied; the input is never mutated.
    """
    result = copy.deepcopy(binding)
    changes: list[str] = []
    try:
        sigs = parse_source_signatures(source)
    except Exception:
        return result, changes
    seq = [0]
    for entry in (result.get('bindings') or {}).values():
        if not isinstance(entry, dict):
            continue
        _rewrite_entry(entry, sigs, changes, seq)
        _rewrite_zero_arg_length(entry, sigs, changes)
    return result, changes
