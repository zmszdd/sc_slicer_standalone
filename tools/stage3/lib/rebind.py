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

from lib.solidity_scan import (IDENT, KEYWORDS, _matching_brace,
                               _strip_comments_and_strings)

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
_STRUCT_STATE_RE = re.compile(
    rf'\b({IDENT})\s+public\s+({IDENT})\s*;')

_STATE_VAR_RE = re.compile(
    rf'(?m)^\s*({IDENT}(?:\s*\[[^\]]*\])?)'
    rf'(?:\s+(?:public|private|internal|constant|immutable|override))*'
    rf'\s+({IDENT})\s*(?:=[^;]*;|;)')
_SCALAR_TYPE_RE = re.compile(
    rf'^(?:u?int(?:8|16|24|32|40|48|56|64|72|80|88|96|104|112|120|128|'
    rf'136|144|152|160|168|176|184|192|200|208|216|224|232|240|248|256)?|'
    rf'address|bool|bytes(?:1|2|3|4|5|6|7|8|9|10|11|12|13|14|15|16|17|18|'
    rf'19|20|21|22|23|24|25|26|27|28|29|30|31|32)?)$')

# A member call: `a.b(...)` possibly with nested parentheses in the args.
_CALL_RE = re.compile(
    rf'\b({IDENT}(?:\s*\.\s*{IDENT})*)\s*\(', re.M)

_RECEIVER_CALL_RE = re.compile(
    rf'(?P<receiver>(?:{IDENT}\s*\([^()]*\)|{IDENT})'
    rf'(?:\s*\.\s*{IDENT})*)\s*\.\s*(?P<method>{IDENT})\s*\(')


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
    """Parse function params/returns, struct fields and public getters.

    This is a best-effort lexical scan that supports the flattened single-file
    slices stage-3 receives; it does not claim a full Solidity parse.
    """
    functions: dict[str, list[dict]] = {}
    for match in _FUNC_RE.finditer(source):
        name = match.group(1)
        params = match.group(2)
        param_types = [p for p in _return_types(params) if p] if params.strip() else []
        arity = len(param_types)
        returns = _return_types(match.group(3))
        functions.setdefault(name, []).append({
            'arity': arity, 'param_types': param_types, 'returns': returns,
        })

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

    struct_getters: dict[str, str] = {}
    for match in _STRUCT_STATE_RE.finditer(source):
        type_name = match.group(1)
        var_name = match.group(2)
        if type_name in structs and var_name not in mapping_getters:
            struct_getters[var_name] = type_name

    state_vars: dict[str, str] = {}
    for match in _STATE_VAR_RE.finditer(source):
        type_name = match.group(1).strip()
        var_name = match.group(2)
        # Ignore keyword-prefixed statements (return/delete/emit) that the
        # permissive line regex otherwise misreads as "<type> <name>;".
        if type_name in KEYWORDS or var_name in KEYWORDS:
            continue
        # First declaration wins for a name; contract state is declared before
        # function-local shadows in the flattened slices stage-3 receives.
        state_vars.setdefault(var_name, type_name)

    return {'functions': functions, 'structs': structs,
            'mapping_getters': mapping_getters,
            'struct_getters': struct_getters, 'state_vars': state_vars}


def _call_leaf(call_expr: str) -> str:
    head = call_expr.split('(', 1)[0]
    parts = [p.strip() for p in head.split('.')]
    return parts[-1] if parts else head


def _return_info(sigs: dict, call_expr: str) -> list[str] | None:
    leaf = _call_leaf(call_expr)
    for key in ('mapping_getters', 'struct_getters'):
        struct_name = sigs.get(key, {}).get(leaf)
        if struct_name:
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
    for key in ('mapping_getters', 'struct_getters'):
        struct_name = sigs.get(key, {}).get(leaf)
        if struct_name:
            fields = sigs['structs'].get(struct_name) or []
            for index, field in enumerate(fields):
                if field['name'] == member:
                    return index
            return None
    # Common tuple-returning getters do not expose named return values in the
    # lexical signature, but their public component names are fixed by the
    # interface (notably Uniswap V2/V3 reserve/tick getters).  Only map names
    # that are unambiguous and whose position exists in the return list.
    common_members = {
        'reserve0': 0, 'reserve1': 1, 'blockTimestampLast': 2,
        'amount0': 0, 'amount1': 1, 'liquidity': 2,
    }
    overloads = sigs['functions'].get(_call_leaf(call_expr)) or []
    max_returns = max((len(row.get('returns') or []) for row in overloads),
                      default=0)
    index = common_members.get(member)
    if index is not None and index < max_returns:
        return index
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

    # Scalar snapshot typing for before-checkpoint symbols. The kind-derived
    # default declaration type (uint256/address/bool) only compiles when the
    # expression actually widens to that type. Infer the exact Solidity type
    # from a single-return call or a bare state-variable identifier so signed /
    # unsigned subtypes, bytesN and other scalars no longer surface as forge
    # "not implicitly convertible" compile errors.
    if entry.get('checkpoint') == 'before' and not entry.get('solidity_type'):
        inferred = None
        if re.fullmatch(IDENT, expr.strip()):
            inferred = sigs.get('state_vars', {}).get(expr.strip())
        else:
            calls = list(_CALL_RE.finditer(expr))
            if len(calls) == 1:
                end = _balanced_call_end(expr, calls[0].end() - 1)
                if end == len(expr) - 1:
                    call_expr = expr[calls[0].start():end + 1]
                    rets = _return_info(sigs, call_expr)
                    if rets and len(rets) == 1 and rets[0]:
                        inferred = rets[0]
        if inferred and _SCALAR_TYPE_RE.match(inferred):
            entry['solidity_type'] = inferred
            changes.append(f'snapshot type {inferred} for {expr[:60]}')

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


def complete_complementary_bindings(binding: dict, contract: dict) -> tuple[dict, list[str]]:
    """Deterministically complete complementary boolean predicates.

    A very common partial binding is a revert/completion pair: the model binds
    the effect side ``X_reverts`` to a boolean expression but leaves the
    safety side ``X_completes`` as UNBOUND because "completes without
    reverting" is a control-flow fact rather than a state expression.  Those
    two symbols are complements, so the unbound side can be derived exactly
    as ``!(bound_expr)`` instead of blocking the differential as
    ``partial_binding``.

    Symbols are paired by their shared name prefix up to the trailing role
    token (``_completes`` / ``_reverts...``), which is stable across the
    stage-2 symbol naming convention and keeps the derivation claim-scoped.
    """
    result = copy.deepcopy(binding)
    changes: list[str] = []
    symbols = [
        row for row in contract.get('symbols', [])
        if isinstance(row, dict) and row.get('appears_in')
    ]
    entries = result.get('bindings') or {}
    if not isinstance(entries, dict):
        return result, changes

    _COMPLETE = {'completes', 'completed', 'complete'}
    _REVERT = {'reverts', 'reverted', 'reverting', 'revert'}

    def expr_of(name: str) -> str:
        entry = entries.get(name)
        if not isinstance(entry, dict):
            return ''
        return str(entry.get('solidity_expr') or '').strip()

    def role_prefix(name: str) -> tuple[str | None, str]:
        lower = name.lower()
        best = None
        best_start = -1
        for token in _COMPLETE | _REVERT:
            for match in re.finditer(rf'_{re.escape(token)}(?:_|$)', lower):
                if match.start() > best_start:
                    best = token
                    best_start = match.start()
        if best is None:
            return None, name
        return best, name[:best_start]

    # Index bound boolean symbols by role+prefix.
    by_prefix: dict[tuple[str, str], list[tuple[str, str]]] = {}
    for row in symbols:
        name = row.get('symbol') or ''
        if row.get('binding_kind') != 'boolean_predicate':
            continue
        other_expr = expr_of(name)
        if not other_expr or other_expr == 'UNBOUND':
            continue
        role, prefix = role_prefix(name)
        if role is None:
            continue
        by_prefix.setdefault((prefix, role), []).append((name, other_expr))

    for row in symbols:
        name = row.get('symbol') or ''
        entry = entries.get(name)
        if not isinstance(entry, dict):
            continue
        if expr_of(name) != 'UNBOUND':
            continue
        if row.get('binding_kind') != 'boolean_predicate':
            continue
        role, prefix = role_prefix(name)
        if role is None:
            continue
        if role in _COMPLETE:
            mates = by_prefix.get((prefix, 'revert'), []) + \
                by_prefix.get((prefix, 'reverts'), []) + \
                by_prefix.get((prefix, 'reverted'), []) + \
                by_prefix.get((prefix, 'reverting'), [])
        elif role in _REVERT:
            mates = by_prefix.get((prefix, 'complete'), []) + \
                by_prefix.get((prefix, 'completes'), []) + \
                by_prefix.get((prefix, 'completed'), [])
        else:
            continue
        if not mates:
            continue
        mate_name, mate_expr = mates[0]
        entry['solidity_expr'] = f'!({mate_expr})'
        changes.append(
            f'complement {name} = !{mate_name} ({mate_expr})')

    return result, changes


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


def _function_body_text(source: str, name: str,
                        contract: str | None = None) -> str:
    clean = _strip_comments_and_strings(source)
    start, end = 0, len(clean)
    if contract:
        marker = re.search(
            rf'\b(?:abstract\s+)?(?:contract|interface|library)\s+'
            rf'{re.escape(contract)}\b', clean)
        if marker is None:
            return ''
        open_idx = clean.find('{', marker.end())
        if open_idx < 0:
            return ''
        start = open_idx + 1
        end = _matching_brace(clean, open_idx)
    marker = re.search(rf'\bfunction\s+{re.escape(name)}\s*\(', clean[start:end])
    if marker is None:
        return ''
    fn_start = start + marker.end()
    open_idx = clean.find('{', fn_start)
    if open_idx < 0 or open_idx >= end:
        return ''
    return clean[open_idx + 1:_matching_brace(clean, open_idx)]


def qualify_unqualified_calls(binding: dict,
                              source: str) -> tuple[dict, list[str]]:
    """Qualify an unqualified call when the probe test has one receiver.

    Binding expressions are evaluated in the PoC test after injection-point
    relocation, but the model sometimes emits ``validatePrice(0)`` when the
    test only ever calls ``oracle.validatePrice(0)``. Rewrite only when the
    probe test body contains exactly one receiver for that declared method;
    ambiguous receiver sets are left untouched and continue to the normal
    compile-repair path.
    """
    result = copy.deepcopy(binding)
    changes: list[str] = []
    probe = result.get('probe') or {}
    test_name = probe.get('exploit_test')
    test_contract = probe.get('contract')
    if not test_name:
        return result, changes
    body = _function_body_text(source, test_name, test_contract)
    if not body:
        return result, changes
    sigs = parse_source_signatures(source)
    declared = (set(sigs.get('functions') or {}) |
                set(sigs.get('state_vars') or {}) |
                set(sigs.get('mapping_getters') or {}) |
                set(sigs.get('struct_getters') or {}))
    # ``state_vars`` intentionally skips keyword-shaped type names (notably
    # ``address``); public address getters are still valid call targets.
    declared |= {match.group(2) for match in _STATE_VAR_RE.finditer(source)}
    receivers: dict[str, set[str]] = {}
    for match in _RECEIVER_CALL_RE.finditer(body):
        method = match.group('method')
        if method not in declared:
            continue
        receiver = re.sub(r'\s+', ' ', match.group('receiver')).strip()
        receivers.setdefault(method, set()).add(receiver)
    if not receivers:
        return result, changes
    for symbol, entry in (result.get('bindings') or {}).items():
        if not isinstance(entry, dict):
            continue
        expr = str(entry.get('solidity_expr') or '')
        if not expr or expr == 'UNBOUND':
            continue
        updated = expr
        for method, found in receivers.items():
            if len(found) != 1:
                continue
            receiver = next(iter(found))
            pattern = re.compile(rf'(?<![.\w$]){re.escape(method)}\s*\(')
            if not pattern.search(updated):
                continue
            replacement = f'{receiver}.{method}('
            updated = pattern.sub(replacement, updated)
            changes.append(f'{symbol}: {method}() -> {receiver}.{method}()')
        if updated != expr:
            entry['solidity_expr'] = updated
    return result, changes


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


_BOOL_COMPARISON_RE = re.compile(r'==|!=|<=|>=|<|>')
_BOOL_LOGICAL_RE = re.compile(r'&&|\|\||(?<![=!<>])!(?!=)')


def _looks_boolean(expr: str) -> bool:
    """Best-effort check that *expr* is already a boolean expression.

    Conservative: only returns True for shapes that are certainly boolean
    (comparison / logical operators / bare boolean literal). Everything else
    is treated as non-boolean so a ``boolean_predicate`` symbol bound to a
    scalar call/state var can be coerced with ``!= 0``.
    """
    text = expr.strip()
    if text in ('true', 'false'):
        return True
    if _BOOL_COMPARISON_RE.search(text):
        return True
    if _BOOL_LOGICAL_RE.search(text):
        return True
    return False


def _single_call_expr(expr: str):
    """Return the matched call string when *expr* is exactly one call."""
    stripped = expr.strip()
    while stripped.startswith('(') and stripped.endswith(')'):
        inner = stripped[1:-1].strip()
        if not (inner.startswith('(') and inner.endswith(')')):
            stripped = inner
            break
        stripped = inner
    match = _CALL_RE.match(stripped)
    if match is None:
        return None
    end = _balanced_call_end(stripped, match.end() - 1)
    if end != len(stripped) - 1:
        return None
    return stripped


def coerce_boolean_predicates(binding: dict, source: str) -> tuple[dict, list[str]]:
    """Coerce ``boolean_predicate`` symbols bound to scalar expressions.

    Stage-2 marks flow facts such as "distribution performed" as
    ``boolean_predicate``. The binding model occasionally binds them to a
    scalar-returning call (``minter.update_period()``) or scalar state var;
    rendering that as ``!I`` / ``I`` under ``assert`` fails with
    ``unary operator ! cannot be applied to uint256``. The deterministic,
    semantic-preserving coercion for "nonzero means the event happened" is
    ``(expr) != 0``, which keeps the differential honest: the verdict is still
    decided by forge, not by this rewrite.
    """
    result = copy.deepcopy(binding)
    changes: list[str] = []
    try:
        sigs = parse_source_signatures(source)
    except Exception:
        return result, changes
    for name, entry in (result.get('bindings') or {}).items():
        if not isinstance(entry, dict):
            continue
        if entry.get('kind') != 'boolean_predicate':
            continue
        expr = str(entry.get('solidity_expr') or '').strip()
        if not expr or expr == 'UNBOUND' or _looks_boolean(expr):
            continue
        scalar = None
        call = _single_call_expr(expr)
        if call is not None:
            rets = _return_info(sigs, call) or []
            if (len(rets) == 1 and rets[0]
                    and rets[0] != 'bool'
                    and _SCALAR_TYPE_RE.match(rets[0])):
                scalar = rets[0]
        elif re.fullmatch(IDENT, expr):
            inferred = sigs.get('state_vars', {}).get(expr)
            if (inferred and inferred != 'bool'
                    and _SCALAR_TYPE_RE.match(inferred)):
                scalar = inferred
        if scalar is None:
            continue
        entry['solidity_expr'] = f'(({expr}) != 0)'
        changes.append(
            f'boolean predicate {name}: ({expr}) coerced to != 0 '
            f'(scalar type {scalar})')
    return result, changes


def _meaning_tokens(row: dict) -> set[str]:
    """Lowercase semantic tokens from entity_ids + meaning for name matching."""
    tokens: set[str] = set()
    for value in row.get('entity_ids') or []:
        for tok in re.findall(r'[a-z0-9_]+', str(value).lower()):
            if len(tok) >= 3:
                tokens.add(tok)
    for word in re.findall(r'[a-z0-9_]+', str(row.get('meaning') or '').lower()):
        if len(word) >= 4:
            tokens.add(word)
    return tokens


def _camel_parts(name: str) -> set[str]:
    lower = name.lower()
    if '_' in lower:
        return set(re.findall(r'[a-z0-9_]+', lower))
    return set(re.findall(r'[a-z0-9]+', lower))


def complete_unbound_by_name(binding: dict, contract: dict, sigs: dict) -> tuple[dict, list[str]]:
    """Deterministically bind UNBOUND symbols to a single unambiguous code name.

    Many UNBOUND symbols carry a ``meaning``/``entity_ids`` that literally
    names the state variable or zero-arg getter (e.g. ``minWithdrawalShares``).
    The binding model frequently returns UNBOUND for those anyway. This
    fallback binds only when exactly one declared name wins the token match,
    and never invents an identifier; the existing lint/expressibility gates
    still reject a cross-contract or wrong-type result downstream.
    """
    result = copy.deepcopy(binding)
    changes: list[str] = []
    entries = result.get('bindings') or {}
    if not isinstance(entries, dict):
        return result, changes

    state_vars = sigs.get('state_vars') or {}
    functions = sigs.get('functions') or {}
    mapping_getters = sigs.get('mapping_getters') or {}
    struct_getters = sigs.get('struct_getters') or {}

    def declared_names() -> set[str]:
        names = set(state_vars) | set(functions) | set(mapping_getters) | set(struct_getters)
        return names

    for row in contract.get('symbols', []):
        if not isinstance(row, dict):
            continue
        name = row.get('symbol') or ''
        entry = entries.get(name)
        if not isinstance(entry, dict):
            continue
        if str(entry.get('solidity_expr') or '').strip() != 'UNBOUND':
            continue
        tokens = _meaning_tokens(row)
        if not tokens:
            continue
        scored = []
        for cand in declared_names():
            if len(cand) < 3:
                continue
            parts = _camel_parts(cand)
            score = sum(1 for tok in tokens if tok in parts or tok in cand or cand in tok)
            if score:
                scored.append((score, cand))
        if not scored:
            continue
        scored.sort(key=lambda pair: (-pair[0], pair[1]))
        if len(scored) > 1 and scored[0][0] == scored[1][0]:
            continue  # ambiguous: two names with the same top score
        cand = scored[0][1]
        kind = row.get('binding_kind') or entry.get('kind')
        expr = None
        if cand in functions:
            overloads = functions[cand]
            zero_arg = [o for o in overloads if o.get('arity') == 0]
            if not zero_arg:
                continue
            rets = zero_arg[0].get('returns') or []
            if kind == 'boolean_predicate':
                if rets and rets[0] == 'bool':
                    expr = f'{cand}()'
                elif rets and _SCALAR_TYPE_RE.match(rets[0]):
                    expr = f'({cand}()) != 0'
                else:
                    continue
            else:
                if rets and _SCALAR_TYPE_RE.match(rets[0]):
                    expr = f'{cand}()'
                else:
                    continue
        elif cand in mapping_getters or cand in struct_getters:
            struct_name = mapping_getters.get(cand) or struct_getters.get(cand)
            fields = sigs.get('structs', {}).get(struct_name) or []
            if kind == 'boolean_predicate':
                continue
            if len(fields) == 1:
                expr = f'{cand}()'
            else:
                continue
        elif cand in state_vars:
            typ = state_vars[cand]
            if kind == 'boolean_predicate':
                if typ == 'bool':
                    expr = cand
                elif _SCALAR_TYPE_RE.match(typ):
                    expr = f'({cand}) != 0'
                else:
                    continue
            else:
                if _SCALAR_TYPE_RE.match(typ) or typ == 'bool':
                    expr = cand
                else:
                    continue
        if expr is None:
            continue
        entry['solidity_expr'] = expr
        changes.append(f'{name} -> {expr} (from {cand})')

    return result, changes
