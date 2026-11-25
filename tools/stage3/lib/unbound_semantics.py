"""Classify and deterministically repair semantic ``UNBOUND`` bindings.

Stage 3 must not ask the binding model to keep guessing an expression when the
symbol is semantically observable.  This module splits remaining ``UNBOUND``
symbols into recovery buckets and attempts only source-grounded, unique
repairs.  Anything it cannot resolve is reported with a route suggestion so the
caller can stop rebinding and fall back to stage-2 restatement or a reference
patch.
"""
from __future__ import annotations

import copy
import re

from lib.rebind import (complete_complementary_bindings,
                        parse_source_signatures)
from lib.solidity_scan import (contract_instances, function_owner,
                               poc_test_contract, state_var_owner)


SCHEMA_VERSION = 'unbound-semantics/1'
BUCKETS = (
    'semantic_time_window', 'semantic_cross_contract',
    'semantic_derived_boolean', 'semantic_mapping_or_struct_getter',
    'semantic_balance_or_allowance', 'semantic_effect_only',
    'genuinely_unobservable',
)
ROUTES = {
    'semantic_time_window': 'deterministic_time_window',
    'semantic_cross_contract': 'deterministic_receiver_qualification',
    'semantic_derived_boolean': 'deterministic_complement_or_scalar',
    'semantic_mapping_or_struct_getter': 'deterministic_getter',
    'semantic_balance_or_allowance': 'deterministic_token_call',
    'semantic_effect_only': 'effect_probe_optional',
    'genuinely_unobservable': 'stage2_restate_or_reference_patch',
}
TIME_WORDS = re.compile(
    r'(?:time|timestamp|deadline|duration|start|end|expir|window|epoch|warp|'
    r'valid.?until)', re.I)
CROSS_WORDS = re.compile(
    r'(?:other|external|oracle|vault|token|router|pool|manager|controller|'
    r'instance|contract)', re.I)
BALANCE_WORDS = re.compile(
    r'(?:balance|allowance|holding|shares|assets|deposit|withdraw)', re.I)
DERIVED_WORDS = re.compile(
    r'(?:not|without|unchanged|remains|completes|succeeds|fails|reverts|'
    r'blocked|paused|eligible|valid|authorized|privileged)', re.I)
NEGATORS = re.compile(r'(?:\bnot\b|\bwithout\b|\bunchanged\b|\bfails?\b|'
                      r'\bfailed\b|\breverts?\b|\bblocked\b|\bnever\b)', re.I)


def _tokens(value):
    result = set()
    for token in re.findall(r'[a-z0-9_]+', str(value or '').lower()):
        if len(token) >= 3:
            result.add(token)
    return result


def _name_parts(name):
    return {part.lower() for part in re.findall(r'[A-Z]?[a-z]+|[0-9]+', name)}


def _score(tokens, name):
    lower = name.lower()
    parts = _name_parts(name)
    score = sum(1 for token in tokens
                if token in parts or token == lower or
                (len(token) >= 4 and token in lower))
    return score


def _unique_best(options, tokens):
    scored = [(_score(tokens, name), name) for name in options]
    scored = [row for row in scored if row[0] > 0]
    if not scored:
        return None
    scored.sort(key=lambda row: (-row[0], row[1]))
    if len(scored) > 1 and scored[0][0] == scored[1][0]:
        return None
    return scored[0][1]


def _symbol_tokens(row):
    values = [str(row.get('meaning') or '')]
    values.extend(str(value) for value in (row.get('entity_ids') or []))
    values.append(str(row.get('symbol') or ''))
    return _tokens(' '.join(str(value) for value in values))


def _returns(sigs, name):
    overloads = (sigs.get('functions') or {}).get(name) or []
    for row in overloads:
        returns = row.get('returns') or []
        if returns:
            return returns[0]
    return None


def _member_type(sigs, name):
    if name in (sigs.get('state_vars') or {}):
        return sigs['state_vars'][name]
    return _returns(sigs, name)


def _qualify(name, sigs, source, instances, injection_contract):
    """Return a bare or receiver-qualified member expression when unambiguous."""
    owners = set()
    if name in (sigs.get('state_vars') or {}):
        owners = state_var_owner(source, name)
    elif name in (sigs.get('functions') or {}):
        owners = function_owner(source, name)
    if injection_contract and owners == {injection_contract}:
        return name
    member_type = _member_type(sigs, name)
    matching = [instance for instance, typ in (instances or {}).items()
                if member_type and typ == member_type]
    if len(matching) == 1:
        return matching[0] + '.' + name
    return name


def _member_expr(name, sigs, source, instances, injection_contract):
    base = _qualify(name, sigs, source, instances, injection_contract)
    if name in (sigs.get('functions') or {}):
        overloads = sigs['functions'][name]
        if not any(row.get('arity') == 0 for row in overloads):
            return None
        return base + '()'
    if name in (sigs.get('state_vars') or {}):
        return base
    return None


def _coerce(expr, kind, member_type):
    if kind != 'boolean_predicate' or not expr:
        return expr
    if member_type == 'bool':
        return expr
    if member_type and re.match(r'(?:u?int|uint|int|address|bytes|string)', member_type):
        return '((%s) != 0)' % expr
    return expr


def _time_repair(row, entry, sigs, source, instances, injection_contract):
    tokens = _symbol_tokens(row)
    names = (set(sigs.get('state_vars') or {}) |
             set(sigs.get('functions') or {}))
    start = _unique_best(
        {name for name in names if re.search(r'start|begin|since', name, re.I)},
        tokens | {'start', 'time'})
    duration = _unique_best(
        {name for name in names if re.search(r'duration|period|length|delay', name, re.I)},
        tokens | {'duration'})
    deadline = _unique_best(
        {name for name in names if re.search(
            r'deadline|expiry|expires|end|until|finish', name, re.I)},
        tokens | {'deadline', 'end', 'expiry'})
    start_expr = _member_expr(start, sigs, source, instances, injection_contract) if start else None
    duration_expr = _member_expr(duration, sigs, source, instances, injection_contract) if duration else None
    deadline_expr = _member_expr(deadline, sigs, source, instances, injection_contract) if deadline else None
    if entry.get('kind') == 'numeric_value':
        return deadline_expr or start_expr or duration_expr
    if start_expr and duration_expr:
        return 'block.timestamp < (%s + %s)' % (start_expr, duration_expr)
    if deadline_expr:
        return 'block.timestamp <= %s' % deadline_expr
    return None


def _cross_repair(row, entry, sigs, source, instances, injection_contract):
    tokens = _symbol_tokens(row)
    if not instances:
        return None
    instance = _unique_best(set(instances), tokens | _tokens(
        ' '.join(str(value) for value in instances.values())))
    if not instance:
        return None
    members = (set(sigs.get('state_vars') or {}) |
               set(sigs.get('functions') or {}) |
               set(sigs.get('mapping_getters') or {}) |
               set(sigs.get('struct_getters') or {}))
    member = _unique_best(members, tokens - {instance})
    if not member:
        return None
    if member in (sigs.get('mapping_getters') or {}) or \
            member in (sigs.get('struct_getters') or {}):
        # A mapping/struct getter needs a key or destructuring the lexer cannot
        # prove; leave it to the dedicated bucket instead of guessing.
        return None
    expr = _member_expr(member, sigs, source, instances, injection_contract)
    if not expr or not expr.startswith(instance + '.'):
        if member in (sigs.get('functions') or {}):
            overloads = sigs['functions'][member]
            if any(row.get('arity') == 0 for row in overloads):
                expr = instance + '.' + member + '()'
        elif member in (sigs.get('state_vars') or {}):
            expr = instance + '.' + member
    if not expr:
        return None
    return _coerce(expr, entry.get('kind'), _member_type(sigs, member))


def _balance_repair(row, entry, sigs, source, instances, injection_contract):
    if entry.get('kind') != 'numeric_value':
        return None
    tokens = _symbol_tokens(row)
    token = _unique_best(
        {name for name in (instances or {})
         if re.search(r'token|erc20|asset|vault|shares', name, re.I) or
         re.search(r'token|erc20', str(instances[name]), re.I)},
        tokens)
    if not token:
        return None
    address_names = {
        name for name, typ in (sigs.get('state_vars') or {}).items()
        if typ == 'address'}
    address_names |= {
        name for name, overloads in (sigs.get('functions') or {}).items()
        if any((row.get('returns') or [None])[0] == 'address' and
               row.get('arity') == 0 for row in overloads)}
    address = _unique_best(address_names, tokens - {token})
    if not address:
        return None
    address_expr = _member_expr(address, sigs, source, instances, injection_contract)
    functions = sigs.get('functions') or {}
    if 'balanceOf' in functions and any(
            row.get('arity') == 1 for row in functions['balanceOf']):
        return '%s.balanceOf(%s)' % (token, address_expr)
    return None


def _mapping_repair(row, entry, sigs, source, instances, injection_contract):
    tokens = _symbol_tokens(row)
    getters = set(sigs.get('mapping_getters') or {}) | \
        set(sigs.get('struct_getters') or {})
    getter = _unique_best(getters, tokens)
    if getter and getter in (sigs.get('functions') or {}):
        overloads = sigs['functions'][getter]
        zero_arg = [row for row in overloads if row.get('arity') == 0]
        if zero_arg:
            expr = _member_expr(getter, sigs, source, instances, injection_contract)
            return _coerce(expr, entry.get('kind'), _returns(sigs, getter))
    return None


def _opposite_meaning(left, right):
    left_text = NEGATORS.sub(' ', str(left or '').lower())
    right_text = NEGATORS.sub(' ', str(right or '').lower())
    left_text = ' '.join(sorted(_tokens(left_text)))
    right_text = ' '.join(sorted(_tokens(right_text)))
    if left_text != right_text:
        return False
    return bool(NEGATORS.search(str(left or ''))) != \
        bool(NEGATORS.search(str(right or '')))


def _derived_repair(name, binding, contract, assigned):
    result, changes = complete_complementary_bindings(binding, contract)
    entry = (result.get('bindings') or {}).get(name) or {}
    if changes and str(entry.get('solidity_expr') or '').strip() != 'UNBOUND':
        return entry.get('solidity_expr'), changes
    row = next((item for item in contract.get('symbols', [])
                if item.get('symbol') == name), {})
    for other, meta in (binding.get('bindings') or {}).items():
        if other == name or other in assigned or not isinstance(meta, dict):
            continue
        if meta.get('kind') != 'boolean_predicate':
            continue
        expr = str(meta.get('solidity_expr') or '').strip()
        if expr == 'UNBOUND':
            continue
        other_row = next((item for item in contract.get('symbols', [])
                          if item.get('symbol') == other), {})
        if _opposite_meaning(row.get('meaning'), other_row.get('meaning')):
            return '!(%s)' % expr, ['%s: !%s (complementary meaning)' % (name, other)]
    return None, []


def _expression_grounded(expr, source):
    """A repaired expression must use identifiers present in the source."""
    if not expr:
        return False
    for identifier in re.findall(r'[A-Za-z_][A-Za-z0-9_]*', expr):
        if identifier in {'block', 'timestamp', 'true', 'false'}:
            continue
        if not re.search(r'\b' + re.escape(identifier) + r'\b', source):
            return False
    return True


def resolve_unbound(binding, contract, source, *, injection_contract=None):
    """Return ``(binding, changes, report)`` with deterministic repairs applied.

    Only unique, source-grounded repairs are applied.  The input binding is
    never mutated.
    """
    result = copy.deepcopy(binding)
    sigs = parse_source_signatures(source)
    if not injection_contract:
        injection_contract = poc_test_contract(source)
    try:
        instances = contract_instances(source, injection_contract) if injection_contract else {}
    except Exception:
        instances = {}
    rows = {row.get('symbol'): row for row in (contract.get('symbols') or [])
            if isinstance(row, dict)}
    entries = result.get('bindings') or {}
    items = {}
    changes = []
    assigned = set()
    for name in sorted(entries):
        entry = entries[name]
        if not isinstance(entry, dict):
            continue
        if str(entry.get('solidity_expr') or '').strip() != 'UNBOUND':
            continue
        row = rows.get(name) or {}
        role = row.get('appears_in') or []
        meaning = str(row.get('meaning') or '')
        tokens = _symbol_tokens(row)
        bucket = 'genuinely_unobservable'
        evidence = []
        candidate = None
        if role and all(value == 'V' for value in role):
            bucket = 'semantic_effect_only'
            evidence.append('symbol appears only in V; optional effect probe')
        elif row.get('scope') == 'cross_contract':
            bucket = 'semantic_cross_contract'
            candidate = _cross_repair(
                row, entry, sigs, source, instances, injection_contract)
            evidence.append('explicit cross-contract scope')
        elif row.get('observable_kind') in ('mapping', 'struct_field'):
            bucket = 'semantic_mapping_or_struct_getter'
            candidate = _mapping_repair(
                row, entry, sigs, source, instances, injection_contract)
            evidence.append('explicit mapping/struct observable')
        elif row.get('observable_kind') == 'timestamp':
            bucket = 'semantic_time_window'
            candidate = _time_repair(
                row, entry, sigs, source, instances, injection_contract)
            evidence.append('explicit timestamp observable')
        elif row.get('observable_kind') == 'balance':
            bucket = 'semantic_balance_or_allowance'
            candidate = _balance_repair(
                row, entry, sigs, source, instances, injection_contract)
            evidence.append('explicit balance observable')
        elif row.get('observable_kind') == 'derived':
            bucket = 'semantic_derived_boolean'
            candidate, derived_changes = _derived_repair(
                name, result, contract, assigned)
            evidence.extend(derived_changes)
        elif TIME_WORDS.search(meaning) or any(
                re.search(r'time|deadline|duration|start|end|window|expir',
                          token, re.I) for token in tokens):
            bucket = 'semantic_time_window'
            candidate = _time_repair(
                row, entry, sigs, source, instances, injection_contract)
            evidence.append('time-window wording or time-shaped symbol name')
        elif (row.get('receiver') or
                CROSS_WORDS.search(meaning) or
                any(instance.lower() in token for instance in instances
                    for token in tokens)):
            bucket = 'semantic_cross_contract'
            candidate = _cross_repair(
                row, entry, sigs, source, instances, injection_contract)
            evidence.append('cross-contract wording, scope, or receiver')
        elif BALANCE_WORDS.search(meaning) or any(
                re.search(r'balance|allowance|share|asset|token', token, re.I)
                for token in tokens):
            bucket = 'semantic_balance_or_allowance'
            candidate = _balance_repair(
                row, entry, sigs, source, instances, injection_contract)
            evidence.append('balance/allowance/token wording')
        elif _unique_best(set(sigs.get('mapping_getters') or {}) |
                          set(sigs.get('struct_getters') or {}), tokens):
            bucket = 'semantic_mapping_or_struct_getter'
            candidate = _mapping_repair(
                row, entry, sigs, source, instances, injection_contract)
            evidence.append('mapping/struct getter candidate')
        elif entry.get('kind') == 'boolean_predicate' and (
                DERIVED_WORDS.search(meaning) or
                any(_opposite_meaning(meaning, other.get('meaning'))
                    for other in rows.values() if isinstance(other, dict))):
            bucket = 'semantic_derived_boolean'
            candidate, derived_changes = _derived_repair(
                name, result, contract, assigned)
            evidence.extend(derived_changes)
            if candidate and not _expression_grounded(candidate, source):
                candidate = None
        item = {
            'symbol': name,
            'bucket': bucket,
            'route': ROUTES[bucket],
            'evidence': evidence,
            'resolved_expr': None,
        }
        if candidate and _expression_grounded(candidate, source):
            entries[name]['solidity_expr'] = candidate
            item['resolved_expr'] = candidate
            assigned.add(name)
            changes.append('%s: UNBOUND -> %s (%s)' % (name, candidate, bucket))
        items[name] = item
    counts = {bucket: 0 for bucket in BUCKETS}
    for item in items.values():
        counts[item['bucket']] += 1
    unresolved = {name: item for name, item in items.items()
                  if not item['resolved_expr']}
    terminal_buckets = {'genuinely_unobservable', 'semantic_effect_only'}
    meaningful_unresolved = [
        item for item in unresolved.values()
        if item['bucket'] != 'semantic_effect_only']
    terminal_unresolved = bool(meaningful_unresolved) and all(
        item['bucket'] == 'genuinely_unobservable'
        for item in meaningful_unresolved)
    report = {
        'schema_version': SCHEMA_VERSION,
        'claim_id': binding.get('claim_id'),
        'counts': counts,
        'items': items,
        'unresolved': sorted(unresolved),
        'unresolved_buckets': sorted({item['bucket']
                                      for item in unresolved.values()}),
        'resolved': sorted(name for name, item in items.items()
                           if item['resolved_expr']),
        'terminal_unresolved': terminal_unresolved,
        'terminal_buckets': sorted(terminal_buckets),
        'route_suggestion': ('stage2_restate_or_reference_patch'
                             if terminal_unresolved
                             else 'continue_stage3'),
    }
    return result, changes, report
