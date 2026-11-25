"""Deterministic code-observable intermediate representation for binding.

Stage 2 reasons from report text only.  Its symbols are therefore semantic
facts such as ``tree_size_before_post`` or ``paths_fee_mismatch``; they are
not guaranteed to be identifiers in the flattened Solidity slice.  Stage 3
previously asked a model to invent an expression for those facts, which made
``UNBOUND`` and compile errors the dominant failure modes.

This module builds the missing bridge: for each claim symbol it enumerates
code facts that are actually visible at the injection point (state variables,
zero-arg getters, and receiver-qualified fields), with type/scope/checkpoint
metadata.  Binding can then select a candidate instead of guessing.

The scanner is deliberately lexical, matching the rest of stage 3.  It is a
candidate generator, not a semantic proof; every selected expression still
goes through binding lint and forge.
"""
from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

from lib.rebind import parse_source_signatures
from lib import observable_recipes
from lib.solidity_scan import (
    IDENT,
    _matching_brace,
    _strip_comments_and_strings,
    base_identifiers,
    clean_source,
    contract_instances,
    contract_span,
    contract_visible_functions,
    inheritance_bases,
    poc_test_contract,
)
from lib.spec_loader import claim_binding_contract, load_stage2_run

SCHEMA_VERSION = 'stage3-observable-ir/4'

_CHECKPOINT_WORDS = {
    'before': 'before',
    'input': 'input',
    'after': 'after',
}

_STATE_DECL_RE = re.compile(
    r'(?m)^\s*([A-Za-z_$][A-Za-z0-9_$]*(?:\s*\[[^\]]*\])?)\s+'
    r'(?:(?:public|private|internal|constant|immutable|override)\s+)*'
    r'([A-Za-z_$][A-Za-z0-9_$]*)\s*(?:=[^;]*|;)'
)

_STATE_STMT_RE = re.compile(
    r'^\s*((?:mapping\([^;]+?\)|[A-Za-z_$][A-Za-z0-9_$.]*'
    r'(?:\s*\[[^\]]*\])?))\s+'
    r'(?:(?:public|private|internal|constant|immutable|override|transient)\s+)*'
    r'([A-Za-z_$][A-Za-z0-9_$]*)\s*(?:=[\s\S]*|;)\s*$'
)

_SCOPE_TYPE_MODIFIERS = (
    'memory', 'storage', 'calldata', 'indexed', 'payable',
    'public', 'private', 'internal', 'external', 'constant', 'immutable',
    'override', 'transient', 'virtual',
)

_LOCAL_STMT_RE = re.compile(
    rf'^\s*((?:mapping\([^;]+?\)|[A-Za-z_$][A-Za-z0-9_$.]*'
    rf'(?:\s*\[[^\]]*\])?))\s+'
    rf'(?:(?:{"|".join(_SCOPE_TYPE_MODIFIERS)})\s+)*'
    rf'({IDENT})\s*(?:=[\s\S]*|;)\s*$', re.S)

_SOURCE_CHAIN_RE = re.compile(
    r'(?<![A-Za-z0-9_$.])(?:[A-Za-z_$][A-Za-z0-9_$]*\.){1,4}'
    r'[A-Za-z_$][A-Za-z0-9_$]*(?:\([^()\n;]{0,120}\))?'
)

# Generic report/source words that are useful only when accompanied by a more
# specific business token.  They are deliberately not removed from expressions;
# they simply cannot make a candidate "high confidence" on their own.
_GENERIC_HINTS = {
    'after', 'amount', 'and', 'before', 'block', 'call', 'callback', 'change',
    'changed', 'complete', 'completed', 'count', 'current', 'data', 'effect',
    'failed', 'failure', 'false', 'for', 'from', 'held', 'input', 'level',
    'number', 'output', 'post', 'price', 'result', 'return', 'returns', 'side',
    'size', 'state', 'success', 'succeeds', 'the', 'token', 'total', 'true',
    'value', 'with',
}

_FORBIDDEN_ROOTS = {
    'abi', 'block', 'blockhash', 'chain', 'chainalias', 'chainid', 'msg',
    'tx', 'type', 'super', 'this',
}
_FORBIDDEN_MEMBERS = {
    'blockhash', 'blocknumber', 'chainid', 'cumulativegasused', 'endgas',
    'effectivegasprice', 'false', 'gasprice', 'gaslimit', 'timestamp',
    'transaction', 'transactionhash', 'transactionindex', 'true',
}
_TEST_CONTRACT_RE = re.compile(
    r'\b(?:abstract\s+)?(?:contract|interface|library)\s+'
    r'([A-Za-z_$][A-Za-z0-9_$]*)(?:\s+is\s+[^\{]+)?\s*\{'
)
_CONTRACT_DECL_RE = re.compile(
    r'\b(?:abstract\s+)?(?:contract|interface|library)\s+'
    r'([A-Za-z_$][A-Za-z0-9_$]*)')
_FUNCTION_DECL_RE = re.compile(r'\bfunction\s+([A-Za-z_$][A-Za-z0-9_$]*)\s*\(')


def _read_sources(src: Path, test_dir: Path | None = None) -> tuple[str, str]:
    src = Path(src)
    if src.is_file():
        business = src.read_text()
    else:
        business = '\n'.join(path.read_text()
                             for path in sorted(src.glob('**/*.sol')))
    if test_dir is None:
        candidate = src.parent / 'test'
        test_dir = candidate if candidate.is_dir() else None
    tests = ''
    if test_dir is not None and Path(test_dir).is_dir():
        tests = '\n'.join(path.read_text()
                          for path in sorted(Path(test_dir).glob('**/*.sol')))
    return business, tests


@lru_cache(maxsize=128)
def _contract_span(source: str, contract: str | None) -> tuple[int, int] | None:
    if not contract:
        return None
    return contract_span(clean_source(source), contract)


def _contract_body_pair(source: str, contract: str | None
                        ) -> tuple[str, str] | None:
    """Return ``(source_body, cleaned_body)`` with identical offsets.

    Structural scans must use ``cleaned_body`` for braces and semicolons:
    flattened Solidity files routinely contain braces inside comments and
    string literals, which otherwise desynchronise every top-level statement
    after the first such literal.
    """
    span = _contract_span(source, contract) if contract else None
    if span is None:
        return None
    open_idx, close_idx = span
    body = source[open_idx + 1:close_idx]
    return body, clean_source(source)[open_idx + 1:close_idx]


def _without_contract(source: str, contract: str | None) -> str:
    span = _contract_span(source, contract)
    if span is None:
        return source
    open_idx, close_idx = span
    return source[:open_idx] + (' ' * (close_idx - open_idx + 1)) + source[close_idx + 1:]


def _test_like_contracts(source: str) -> set[str]:
    clean = clean_source(source)
    result: set[str] = set()
    for match in _TEST_CONTRACT_RE.finditer(clean):
        name = match.group(1)
        span = contract_span(clean, name)
        if span is None:
            continue
        open_idx, close_idx = span
        body = clean[open_idx + 1:close_idx]
        if (re.search(r'\bfunction\s+test[A-Za-z0-9_]*\s*\(', body)
                or 'C4PoC' in name or name.endswith('Test')
                or name.startswith('Mock')):
            result.add(name)
    return result


def _without_test_contracts(source: str) -> str:
    spans = []
    for name in sorted(_test_like_contracts(source)):
        span = _contract_span(source, name)
        if span is not None:
            spans.append(span)
    out = source
    for open_idx, close_idx in sorted(spans, reverse=True):
        out = (out[:open_idx] + (' ' * (close_idx - open_idx + 1))
               + out[close_idx + 1:])
    return out


@lru_cache(maxsize=128)
def _direct_state_decls(source: str, contract: str) -> dict[str, str]:
    pair = _contract_body_pair(source, contract)
    if pair is None:
        return {}
    _body, clean_body = pair
    result: dict[str, str] = {}
    depth = 0
    start = 0
    for index, char in enumerate(clean_body):
        if char == '{':
            depth += 1
        elif char == '}':
            depth = max(0, depth - 1)
        elif char == ';' and depth == 0:
            stmt = clean_body[start:index + 1].strip()
            start = index + 1
            match = _STATE_STMT_RE.match(stmt)
            if not match:
                continue
            type_name = re.sub(r'\s+', '', match.group(1))
            name = match.group(2)
            if type_name in {'event', 'error', 'using'}:
                continue
            result.setdefault(name, type_name)
    return result


@lru_cache(maxsize=128)
def _contract_bases(source: str, contract: str) -> list[str]:
    return list(inheritance_bases(clean_source(source), contract))


def _visible_state_decls(source: str, contract: str | None) -> dict[str, str]:
    if not contract:
        return {}
    seen: set[str] = set()
    queue = [contract]
    result: dict[str, str] = {}
    while queue:
        name = queue.pop(0)
        if name in seen:
            continue
        seen.add(name)
        result.update(_direct_state_decls(source, name))
        queue.extend(base for base in _contract_bases(source, name)
                     if base not in seen)
    return result


_FUNCTION_DECL_RE = re.compile(
    rf'\bfunction\s+({IDENT})(?:\s*\(([^)]*)\))')
_PARAM_DECL_RE = re.compile(
    rf'^\s*(.+?)\s+(?:(?:memory|storage|calldata|indexed|payable)\s+)*'
    rf'({IDENT})\s*$', re.S)


def _split_decl_list(text: str) -> list[str]:
    parts, current, depth = [], [], 0
    for char in text:
        if char in '([{':
            depth += 1
        elif char in ')]}':
            depth -= 1
        if char == ',' and depth == 0:
            parts.append(''.join(current).strip())
            current = []
        else:
            current.append(char)
    if ''.join(current).strip():
        parts.append(''.join(current).strip())
    return parts


def _function_scope_decls(source: str, contract: str | None, *,
                          include_all: bool = False) -> list[dict]:
    """Return typed parameters/locals declared by functions in one contract.

    A single PoC test function is the common case.  When a contract has several
    test functions the scanner still records each name with ``function`` so a
    consumer never treats a function-local as contract state.  Business
    functions are included only when ``include_all`` is set; callers use the
    resulting rows to type receiver chains such as ``ds.askTree.size()``.
    """
    pair = _contract_body_pair(source, contract)
    if pair is None:
        return []
    body, clean_body = pair
    rows: list[dict] = []
    for match in _FUNCTION_DECL_RE.finditer(clean_body):
        function = match.group(1)
        if (not include_all and function != 'setUp'
                and not function.startswith('test')):
            continue
        params = match.group(2) or ''
        for part in _split_decl_list(params):
            decl = _PARAM_DECL_RE.match(part)
            if decl:
                rows.append({
                    'name': decl.group(2),
                    'type': _normal_type(decl.group(1)),
                    'kind': 'parameter', 'function': function,
                    'contract': contract,
                })
        brace = clean_body.find('{', match.end())
        if brace < 0:
            continue
        end = _matching_brace(clean_body, brace)
        function_body = clean_body[brace + 1:end]
        depth = 0
        stmt_start = 0
        for index, char in enumerate(function_body):
            if char == '{':
                depth += 1
            elif char == '}':
                depth = max(0, depth - 1)
            elif char == ';' and depth == 0:
                stmt = function_body[stmt_start:index + 1].strip()
                stmt_start = index + 1
                local = _LOCAL_STMT_RE.match(stmt)
                if (local and local.group(2) not in
                        {'return', 'emit', 'delete', 'revert'}):
                    rows.append({
                        'name': local.group(2),
                        'type': _normal_type(local.group(1)),
                        'kind': 'function_local', 'function': function,
                        'contract': contract,
                    })
    return rows


@lru_cache(maxsize=512)
def _normal_type(type_name: str | None) -> str:
    """Normalize a Solidity type while preserving array dimensions."""
    text = re.sub(r'\s+', '', str(type_name or ''))
    return text


def _bare_type(type_name: str | None) -> str:
    """Return the base struct/contract name for member-type resolution."""
    text = _normal_type(type_name)
    text = text.split('[', 1)[0]
    return text.rsplit('.', 1)[-1]


def _all_function_scopes(source: str) -> list[dict]:
    """Return typed parameter/local rows for every business function.

    The scanner is only used to ground source expressions that already occur
    in business code.  It does not synthesize identifiers and keeps the
    function/contract owner on every row for injection-scope auditing.
    """
    clean = clean_source(source)
    names = []
    for match in _CONTRACT_DECL_RE.finditer(clean):
        name = match.group(1)
        if name not in names:
            names.append(name)
    rows: list[dict] = []
    for contract in names:
        rows.extend(_function_scope_decls(source, contract, include_all=True))
    return rows


def _scope_type_index(rows: list[dict]) -> dict[tuple[str, str, str], str]:
    """Map ``(contract, function, receiver)`` to its declared Solidity type."""
    index: dict[tuple[str, str, str], str] = {}
    for row in rows:
        key = (str(row.get('contract') or ''), str(row.get('function') or ''),
               str(row.get('name') or ''))
        index.setdefault(key, str(row.get('type') or ''))
    return index


def _resolve_typed_chain(expression: str, *, scope_types: dict[str, str],
                         signatures: dict) -> dict | None:
    """Resolve a simple receiver chain using declared struct/function types.

    Only zero-argument final calls are accepted.  A call is typed only when a
    declared overload returns exactly one stable type and, when present, its
    first parameter matches the receiver type (the common library extension
    shape ``function size(RedBlackTree storage tree) returns (uint256)``).
    """
    text = re.sub(r'\s+', '', str(expression or ''))
    if not text or '[' in text or text.startswith('('):
        return None
    is_call = text.endswith(')')
    head = text
    if is_call:
        open_idx = text.rfind('(')
        if open_idx < 0 or text[open_idx + 1:].strip(')'):
            return None
        head = text[:open_idx]
    parts = [part for part in head.split('.') if part]
    if len(parts) < 2:
        return None
    root = parts[0]
    current_type = scope_types.get(root)
    if not current_type:
        return None
    structs = signatures.get('structs') or {}
    functions = signatures.get('functions') or {}
    chain_types = [current_type]
    for index, member in enumerate(parts[1:]):
        base = _bare_type(current_type)
        if index == len(parts) - 2 and is_call:
            overloads = functions.get(member) or []
            returns = {_return_type_from_row(row) for row in overloads}
            returns.discard(None)
            if len(returns) != 1:
                return None
            receiver_matches = [
                row for row in overloads
                if not row.get('param_types')
                or _bare_type((row.get('param_types') or [None])[0]) == base
            ]
            if not receiver_matches:
                return None
            current_type = str(next(iter(returns)))
        else:
            fields = structs.get(base) or []
            field = next((row for row in fields
                          if row.get('name') == member), None)
            if field is None:
                return None
            current_type = str(field.get('type') or '')
        if not current_type:
            return None
        chain_types.append(current_type)
    return {
        'root_type': scope_types.get(root),
        'solidity_type': current_type,
        'member_types': chain_types,
        'chain_depth': len(parts) - 1,
        'leaf': parts[-1],
        'is_call': is_call,
    }


def _return_type_from_row(row: dict) -> str | None:
    returns = row.get('returns') or []
    if len(returns) == 1:
        return _normal_type(returns[0])
    return None


def _source_expressions(source: str, contract: str | None) -> list[str]:
    business = _without_test_contracts(source)
    business = _without_contract(business, contract)
    expressions: list[str] = []
    seen: set[str] = set()
    for match in _SOURCE_CHAIN_RE.finditer(business):
        expression = match.group(0).strip()
        if not expression or expression in seen:
            continue
        if expression.endswith('.sol') or '(' in expression:
            call = expression.rsplit('(', 1)[1].rstrip(')').strip() \
                if '(' in expression else ''
            if not expression.endswith(')') or call:
                continue
        root = expression.split('.', 1)[0]
        if root[:1].isupper() or root in {'vm', 'console', 'assert', 'require'}:
            continue
        roots = _split_identifier(expression) | _tokens(expression)
        if roots & _FORBIDDEN_ROOTS:
            continue
        leaf = expression.rstrip(')')
        leaf = leaf.rsplit('(', 1)[0].rsplit('.', 1)[-1].lower()
        if leaf in _FORBIDDEN_MEMBERS:
            continue
        if len(expression) > 180:
            continue
        seen.add(expression)
        expressions.append(expression)
    return expressions


@lru_cache(maxsize=128)
def _function_bodies(source: str, contract: str | None) -> list[tuple[str, str]]:
    pair = _contract_body_pair(source, contract)
    if pair is None:
        return []
    body, clean_body = pair
    rows: list[tuple[str, str]] = []
    for match in _FUNCTION_DECL_RE.finditer(clean_body):
        brace = clean_body.find('{', match.end())
        if brace < 0:
            continue
        end = _matching_brace(clean_body, brace)
        rows.append((match.group(1), body[brace + 1:end]))
    return rows


def _function_body_source(source: str, contract: str, function: str) -> str:
    """Return one function body from a contract, or an empty string."""
    return _function_body_map(source, contract).get(function, '')


@lru_cache(maxsize=128)
def _function_body_map(source: str, contract: str) -> dict[str, str]:
    rows: dict[str, str] = {}
    for name, body in _function_bodies(source, contract):
        rows.setdefault(name, body)
    return rows


@lru_cache(maxsize=512)
def _mutation_regex(name: str):
    return re.compile(
        rf'(?:\bdelete\s+{re.escape(name)}\b|'
        rf'\b{re.escape(name)}\b\s*(?:\[[^\]]*\]\s*)?'
        rf'(?:\+\+|--|\+=|-=|\*=|/=|=(?!=))|'
        rf'\b{re.escape(name)}\s*\.\s*(?:push|pop|push_back)\s*\()')


def _typed_symbol_table(*, full_source: str, business_source: str,
                        injection_contract: str | None,
                        injection_is_test: bool) -> dict:
    target_source = full_source if injection_is_test else business_source
    contracts: list[str] = []
    if injection_contract:
        contracts.append(injection_contract)
    instances = (contract_instances(full_source, injection_contract)
                 if injection_contract else {})
    for typ in instances.values():
        if typ not in contracts:
            contracts.append(typ)
    declared = set(_CONTRACT_DECL_RE.findall(clean_source(target_source)))
    state_rows = []
    function_rows = []
    mutation_sites: dict[str, list[dict]] = {}
    for contract in contracts:
        if contract not in declared:
            continue
        visible = _visible_state_decls(target_source, contract)
        direct = _direct_state_decls(target_source, contract)
        for name, typ in sorted(visible.items()):
            state_rows.append({
                'contract': contract,
                'name': name,
                'solidity_type': typ,
                'declared_in': contract if name in direct else None,
                'injected_scope': True,
            })
        for function, body in _function_bodies(target_source, contract):
            function_rows.append({'contract': contract, 'name': function})
            clean_body = clean_source(body)
            for name in visible:
                if _mutation_regex(name).search(clean_body):
                    mutation_sites.setdefault(name, []).append({
                        'contract': contract,
                        'function': function,
                    })
    state_types = {row['name']: row['solidity_type'] for row in state_rows}
    function_scopes = _all_function_scopes(business_source)
    return {
        'schema_version': 'stage3-typed-symbol-table/1',
        'contracts': sorted(set(contracts)),
        'state_vars': state_rows,
        'functions': function_rows,
        'instances': [
            {'receiver': receiver, 'contract': typ,
             'receiver_known': True}
            for receiver, typ in sorted(instances.items())
        ],
        'state_types': state_types,
        'instance_types': instances,
        'function_scopes': function_scopes,
        'scope_type_count': len({
            (row.get('contract'), row.get('function'), row.get('name'))
            for row in function_scopes
        }),
        'mutation_sites': mutation_sites,
    }


def _checkpoint(value: str | None) -> str:
    text = str(value or '').lower()
    for marker, result in _CHECKPOINT_WORDS.items():
        if marker in text:
            return result
    return 'input'


def _tokens(value: str | None) -> set[str]:
    return {token.lower() for token in re.findall(r'[A-Za-z0-9_]+',
                                                   str(value or ''))
            if len(token) >= 3}


def _split_identifier(value: str) -> set[str]:
    text = re.sub(r'([a-z0-9])([A-Z])', r'\1 \2', str(value or ''))
    parts = [part.lower() for part in re.split(r'[^A-Za-z0-9]+', text)
             if part]
    result = set(parts)
    # Report prose commonly uses a past participle (``buffered``) while the
    # code uses the noun stem (``feeBufferBPS``).  Keep the original token and
    # add the conservative stem so a direct getter is not tied with an
    # unrelated function that merely shares a generic word such as ``fee``.
    for part in parts:
        if len(part) > 4 and part.endswith('ed'):
            result.add(part[:-2])
    for left, right in zip(parts, parts[1:]):
        if len(left) + len(right) >= 4:
            result.add(left + right)
    return result


def _score(symbol: dict, expression: str, name: str) -> tuple[int, bool, int]:
    meaning_hints = _tokens(symbol.get('meaning'))
    symbol_hints = (_tokens(symbol.get('symbol')) |
                    _split_identifier(str(symbol.get('symbol') or '')))
    symbol_hints -= _GENERIC_HINTS
    entity_hints: set[str] = set()
    for entity in symbol.get('entity_ids') or []:
        entity_hints |= _tokens(entity)
    meaning_hints |= entity_hints
    parts = _split_identifier(name) | _tokens(name)
    lower_name = name.lower()
    short_name = len(lower_name) < 4
    # Entity ids are stronger evidence than prose words, but a single lexical
    # scorer keeps the result deterministic and easy to audit.
    semantic_hints = meaning_hints - _GENERIC_HINTS
    entity_hit = any(
        len(hint) >= 3
        and hint not in _GENERIC_HINTS
        and (hint in parts or (not short_name and hint in lower_name))
        for hint in entity_hints)
    structural_hits = sum(
        1 for hint in symbol_hints
        if len(hint) >= 3
        and (hint in parts
             or (hint.endswith('ed') and hint[:-2] in parts)))
    score = structural_hits * 5 + sum(
        3 if hint in parts else 1
        for hint in semantic_hints
        if len(hint) >= 3
        and (hint in parts
             or (not short_name and (hint in lower_name
                                     or lower_name in hint))))
    return score, entity_hit, structural_hits


def _return_type(signatures: dict, name: str) -> str | None:
    overloads = (signatures.get('functions') or {}).get(name) or []
    for row in overloads:
        returns = row.get('returns') or []
        if len(returns) == 1:
            return returns[0]
    return None


def _candidate(*, candidate_id: str, expression: str, kind: str,
               checkpoint: str, contract: str | None, scope: str,
               evidence: str, solidity_type: str | None = None,
               receiver: str | None = None,
               source_grounded: bool = True,
               receiver_known: bool = False,
               chain_depth: int = 0,
               function: str | None = None,
               visible_at_injection: bool = True,
               visible_at_probe: bool = True,
               member_types: list[str] | None = None) -> dict:
    return {
        'candidate_id': candidate_id,
        'expression': expression,
        'kind': kind,
        'checkpoint': checkpoint,
        'contract': contract,
        'scope': scope,
        'receiver': receiver,
        'solidity_type': solidity_type,
        'evidence': evidence,
        'source_grounded': source_grounded,
        'receiver_known': receiver_known,
        'chain_depth': chain_depth,
        'function': function,
        'visible_at_injection': bool(visible_at_injection),
        'visible_at_probe': bool(visible_at_probe),
        'member_types': list(member_types or []),
    }


def _build_candidates(*, full_source: str, business_source: str,
                      probe_contract: str | None,
                      probe_is_test: bool,
                      probe_function: str | None,
                      patch_contract: str | None,
                      patch_is_test: bool,
                      patch_functions: set[str],
                      signatures: dict,
                      symbol_table: dict | None = None) -> list[dict]:
    candidates: list[dict] = []
    instances: dict[str, str] = {}
    probe_vars: dict[str, str] = {}
    patch_vars: dict[str, str] = {}
    same_target = bool(probe_contract and probe_contract == patch_contract)

    # Direct facts belong to the patch target.  The probe may be a PoC test
    # contract while the program slice (and therefore the assertion) targets a
    # business function.  Keeping the two scopes separate prevents business
    # variables from being declared invisible merely because the PoC cannot
    # reference them by name.
    if patch_contract and not patch_is_test:
        visible = _visible_state_decls(business_source, patch_contract)
        patch_vars = visible
        for name, typ in sorted(visible.items()):
            candidates.append(_candidate(
                candidate_id=f'state:{patch_contract}.{name}',
                expression=name, kind='state_var', checkpoint='input',
                contract=patch_contract, scope='single_contract',
                solidity_type=typ,
                visible_at_probe=same_target,
                evidence=f'state variable declared in {patch_contract}'))
        for name in sorted(contract_visible_functions(business_source,
                                                      patch_contract)):
            overloads = (signatures.get('functions') or {}).get(name) or []
            if not any(row.get('arity') == 0 for row in overloads):
                continue
            candidates.append(_candidate(
                candidate_id=f'getter:{patch_contract}.{name}',
                expression=f'{name}()', kind='getter', checkpoint='input',
                contract=patch_contract, scope='single_contract',
                solidity_type=_return_type(signatures, name),
                visible_at_probe=same_target,
                evidence=f'zero-argument function in {patch_contract}'))

    if probe_contract and probe_is_test:
        probe_vars = _visible_state_decls(full_source, probe_contract)
        for row in _function_scope_decls(full_source, probe_contract):
            visible = bool(same_target and row.get('function') in patch_functions)
            candidates.append(_candidate(
                candidate_id=(f'{row["kind"]}:{probe_contract}.'
                              f'{row["function"]}.{row["name"]}'),
                expression=row['name'], kind=row['kind'], checkpoint='input',
                contract=probe_contract, scope='function_scope',
                solidity_type=row['type'],
                function=row.get('function'),
                visible_at_injection=visible,
                visible_at_probe=True,
                evidence=(f'{row["kind"]} {row["name"]}:{row["type"]} in '
                          f'{probe_contract}.{row["function"]}')))

    # Receiver-qualified cross-contract state.  Keep these candidates separate
    # so a single business-contract assertion is never silently treated as
    # multi-contract expressible.
    if probe_contract:
        probe_vars = probe_vars or _visible_state_decls(full_source,
                                                        probe_contract)
        for receiver, typ in contract_instances(full_source,
                                                probe_contract).items():
            if receiver in probe_vars:
                instances.setdefault(receiver, typ)
    if patch_contract and not patch_is_test:
        patch_vars = patch_vars or _visible_state_decls(business_source,
                                                        patch_contract)
        for receiver, typ in contract_instances(business_source,
                                                patch_contract).items():
            if receiver in patch_vars:
                instances.setdefault(receiver, typ)
    if instances:
        for receiver, typ in sorted(instances.items()):
            visible = (same_target and receiver in probe_vars) or (
                receiver in patch_vars)
            target_vars = _visible_state_decls(business_source, typ)
            for name, solidity_type in sorted(target_vars.items()):
                candidates.append(_candidate(
                    candidate_id=f'cross:{receiver}.{name}',
                    expression=f'{receiver}.{name}', kind='cross_contract_state',
                    checkpoint='input', contract=typ, scope='cross_contract',
                    receiver=receiver,
                    solidity_type=solidity_type,
                    visible_at_injection=visible,
                    visible_at_probe=(same_target and receiver in probe_vars),
                    evidence=f'state variable visible on {receiver}:{typ}'))
            for name in sorted(contract_visible_functions(business_source, typ)):
                overloads = (signatures.get('functions') or {}).get(name) or []
                if not any(row.get('arity') == 0 for row in overloads):
                    continue
                candidates.append(_candidate(
                    candidate_id=f'cross-getter:{receiver}.{name}',
                    expression=f'{receiver}.{name}()', kind='getter',
                    checkpoint='input', contract=typ, scope='cross_contract',
                    receiver=receiver,
                    solidity_type=_return_type(signatures, name),
                    visible_at_injection=visible,
                    visible_at_probe=(same_target and receiver in probe_vars),
                    evidence=f'zero-argument function visible on {receiver}:{typ}'))
            # One additional receiver hop captures the common PoC shape
            # ``harness.vault.token.totalSupply()`` without pretending that an
            # arbitrary cross-contract chain is visible from a single anchor.
            target_vars = _visible_state_decls(business_source, typ)
            nested_instances = {
                nested: nested_type
                for nested, nested_type in contract_instances(
                    business_source, typ).items()
                if nested in target_vars
            }
            for nested, nested_type in sorted(nested_instances.items()):
                for name, solidity_type in sorted(
                        _visible_state_decls(business_source,
                                             nested_type).items()):
                    candidates.append(_candidate(
                        candidate_id=f'cross2:{receiver}.{nested}.{name}',
                        expression=f'{receiver}.{nested}.{name}',
                        kind='cross_contract_state',
                        checkpoint='input', contract=nested_type,
                        scope='cross_contract', receiver=f'{receiver}.{nested}',
                        solidity_type=solidity_type,
                        visible_at_injection=visible,
                        visible_at_probe=(same_target and receiver in probe_vars),
                        evidence=(f'state variable visible on '
                                  f'{receiver}.{nested}:{nested_type}')))
                for name in sorted(contract_visible_functions(business_source,
                                                              nested_type)):
                    overloads = ((signatures.get('functions') or {})
                                 .get(name) or [])
                    if not any(row.get('arity') == 0 for row in overloads):
                        continue
                    candidates.append(_candidate(
                        candidate_id=f'cross2-getter:{receiver}.{nested}.{name}',
                        expression=f'{receiver}.{nested}.{name}()',
                        kind='getter', checkpoint='input',
                        contract=nested_type, scope='cross_contract',
                        receiver=f'{receiver}.{nested}',
                        solidity_type=_return_type(signatures, name),
                        visible_at_injection=visible,
                        visible_at_probe=(same_target and receiver in probe_vars),
                        evidence=(f'zero-argument function visible on '
                                  f'{receiver}.{nested}:{nested_type}')))

    # Source-grounded member/call chains capture facts that are not direct
    # state variables, for example ``ds.bidTree.size()`` or
    # ``burner.swapRouter``.  They are extracted only from business source and
    # are never synthesized from a test/PoC body.
    known_receivers = set(instances) | set(probe_vars) | set(patch_vars)
    patch_receivers = set(patch_vars)
    if patch_contract and not patch_is_test:
        patch_receivers |= {
            receiver for receiver in contract_instances(business_source,
                                                        patch_contract)
            if receiver in patch_vars
        }
    for expression in _source_expressions(business_source, None):
        root = expression.split('.', 1)[0]
        candidates.append(_candidate(
            candidate_id=f'source:{expression}',
            expression=expression, kind='source_expr', checkpoint='input',
            contract=instances.get(root) if probe_contract else None,
            scope='source_grounded', receiver=root,
            receiver_known=root in known_receivers,
            chain_depth=expression.count('.'),
            visible_at_injection=root in patch_receivers,
            visible_at_probe=root in known_receivers,
            evidence=f'source-grounded member/call chain {expression}'))

    # Business function parameters/locals are a separate visibility domain.
    # ``ds.askTree.size()`` is typed and observable inside the function that
    # declares ``Book storage ds``; it is not automatically observable from a
    # PoC test frame.  Keep the owner on every candidate so readiness and the
    # binding audit can require an explicit patch-function match.
    scopes_by_function: dict[tuple[str, str], dict[str, str]] = {}
    for scope in (symbol_table or {}).get('function_scopes') or []:
        contract = str(scope.get('contract') or '')
        function = str(scope.get('function') or '')
        scope_name = str(scope.get('name') or '')
        if contract and function and scope_name:
            scopes_by_function.setdefault((contract, function), {}).setdefault(
                scope_name, str(scope.get('type') or ''))
    for (contract, function), scope_types in sorted(
            scopes_by_function.items()):
        visible = bool(patch_contract == contract
                       and function in patch_functions
                       and not patch_is_test)
        function_body = _function_body_source(
            business_source, contract, function)
        if not function_body:
            continue
        for expression in _source_expressions(function_body, None):
            scope_name = expression.split('.', 1)[0]
            if scope_name not in scope_types:
                continue
            resolved = _resolve_typed_chain(
                expression, scope_types=scope_types, signatures=signatures)
            if resolved is None:
                continue
            candidates.append(_candidate(
                candidate_id=(f'business-scope:{contract}.{function}:'
                              f'{expression}'),
                expression=expression, kind='source_expr', checkpoint='input',
                contract=contract, scope='business_function_scope',
                receiver=scope_name, receiver_known=True,
                chain_depth=resolved['chain_depth'],
                solidity_type=resolved['solidity_type'],
                function=function, visible_at_injection=visible,
                visible_at_probe=bool(
                    same_target and probe_contract == contract
                    and function in patch_functions),
                member_types=resolved.get('member_types'),
                evidence=(f'source-grounded typed chain {expression} in '
                          f'{contract}.{function}; receiver {scope_name}:'
                          f'{resolved["root_type"]}')))

    table = symbol_table or {}
    instance_types = table.get('instance_types') or {}
    state_types = table.get('state_types') or {}
    mutation_sites = table.get('mutation_sites') or {}
    for candidate in candidates:
        expression = str(candidate.get('expression') or '')
        root = expression.split('.', 1)[0].rstrip('()')
        leaf = expression.rstrip(')').rsplit('(', 1)[0].rsplit('.', 1)[-1]
        receiver_type = candidate.get('receiver_type')
        if (not receiver_type
                and candidate.get('scope') == 'business_function_scope'):
            member_types = candidate.get('member_types') or []
            receiver_type = member_types[0] if member_types else None
        receiver_type = (receiver_type or instance_types.get(root)
                         or state_types.get(root))
        if candidate.get('kind') in {'state_var', 'getter'}:
            receiver_type = candidate.get('contract') or receiver_type
        if candidate.get('kind') in {'cross_contract_state', 'getter'}:
            receiver_type = receiver_type or candidate.get('contract')
        candidate['receiver_type'] = receiver_type
        candidate['receiver_known'] = bool(
            candidate.get('receiver_known') or receiver_type)
        candidate['declared_in'] = (
            candidate.get('declared_in') or
            (candidate.get('contract')
             if candidate.get('kind') in {'state_var', 'getter'} else None))
        candidate['mutation_sites'] = list(mutation_sites.get(leaf) or [])
        if not candidate.get('solidity_type'):
            candidate['solidity_type'] = (
                'uint256' if leaf == 'length'
                else _return_type(signatures, leaf))
        chain_depth = int(candidate.get('chain_depth') or
                          expression.count('.'))
        candidate['chain_depth'] = chain_depth
        candidate['typed'] = bool(candidate.get('solidity_type')
                                  and (receiver_type or
                                       candidate.get('kind') != 'source_expr'
                                       or leaf == 'length'))
        candidate['evidence_level'] = (
            'typed_code_fact' if candidate['typed'] else
            'source_chain' if candidate.get('kind') == 'source_expr' else
            'lexical_candidate')
        source_expr = candidate.get('kind') == 'source_expr'
        candidate['ready_eligible'] = bool(
            candidate.get('source_grounded', True)
            and candidate.get('visible_at_injection', True)
            and (candidate.get('receiver_known', True) or leaf == 'length')
            and (not source_expr or
                 (receiver_type and chain_depth >= 1)
                 or chain_depth >= 2
                 or (leaf == 'length' and chain_depth >= 1))
            and (not source_expr or
                 (leaf == 'length'
                  and int(candidate.get('structural_hits') or 0) >= 1)
                 or int(candidate.get('structural_hits') or 0) >= 2)
            and (candidate['typed'] or not source_expr))
    return candidates


def build_contract(stage2_dir: Path, claim_id: str, src: Path, *,
                   injection_contract: str | None = None,
                   injection_function: str | None = None,
                   probe_contract: str | None = None,
                   probe_function: str | None = None,
                   patch_contract: str | None = None,
                   patch_function: str | None = None,
                   patch_functions: list[str] | None = None,
                   test_dir: Path | None = None) -> dict:
    stage2 = load_stage2_run(Path(stage2_dir))
    contract = claim_binding_contract(stage2['spec'], claim_id)
    business_source, test_source = _read_sources(Path(src), test_dir)
    full_source = business_source + ('\n' + test_source if test_source else '')
    detected_test = poc_test_contract(full_source)
    test_like = _test_like_contracts(full_source)
    if probe_contract is None:
        probe_contract = (injection_contract
                          if injection_contract is not None else detected_test)
    if probe_function is None:
        probe_function = injection_function
    if patch_contract is None:
        patch_contract = (injection_contract if injection_contract is not None
                          else probe_contract)
    if patch_functions is None:
        if patch_function is not None:
            patch_functions = [patch_function]
        elif injection_contract is not None and injection_function is not None:
            patch_functions = [injection_function]
        elif patch_contract == probe_contract and probe_function is not None:
            patch_functions = [probe_function]
        else:
            patch_functions = []
    patch_function_set = {
        str(name) for name in patch_functions if str(name or '').strip()
    }
    probe_is_test = bool(
        probe_contract
        and (detected_test == probe_contract or probe_contract in test_like))
    patch_is_test = bool(
        patch_contract
        and (detected_test == patch_contract or patch_contract in test_like))
    candidate_business = (_without_test_contracts(business_source)
                          if probe_is_test or patch_is_test
                          else business_source)
    signatures = parse_source_signatures(candidate_business)
    symbol_table = _typed_symbol_table(
        full_source=full_source, business_source=candidate_business,
        injection_contract=patch_contract,
        injection_is_test=patch_is_test)
    symbol_table['signatures'] = signatures
    candidates = _build_candidates(
        full_source=full_source, business_source=candidate_business,
        probe_contract=probe_contract,
        probe_is_test=probe_is_test,
        probe_function=probe_function,
        patch_contract=patch_contract,
        patch_is_test=patch_is_test,
        patch_functions=patch_function_set,
        signatures=signatures,
        symbol_table=symbol_table)

    symbols: dict[str, dict] = {}
    candidate_rows: dict[str, list[dict]] = {}
    for row in contract.get('symbols') or []:
        if not isinstance(row, dict) or not row.get('appears_in'):
            continue
        symbol = row['symbol']
        checkpoint = _checkpoint(row.get('checkpoint'))
        expected_kind = row.get('binding_kind') or 'boolean_predicate'
        scored = []
        best_high = False
        for candidate in candidates:
            score, entity_hit, structural_hits = _score(
                row, candidate['expression'], candidate['expression'])
            if (score <= 0
                    and candidate.get('kind') in {'parameter',
                                                  'function_local'}
                    and candidate.get('expression', '').lower()
                    in _split_identifier(symbol)):
                # Function-scope names are concrete even when the shared token
                # is generic (``amount``).  Keep them as medium-confidence
                # candidates; they are not allowed to become ready unless the
                # normal structural checks also succeed.
                score = 1
            if score <= 0:
                continue
            strong = (candidate.get('source_grounded')
                      and candidate.get('visible_at_injection', True)
                      and (candidate.get('receiver_known')
                           or int(candidate.get('chain_depth') or 0) >= 2
                           or candidate.get('kind') != 'source_expr')
                      and (structural_hits > 0 or entity_hit)
                      and (entity_hit and score >= 3 or score >= 4))
            best_high = best_high or strong
            candidate['structural_hits'] = structural_hits
            candidate['_strong'] = strong
            scored.append((score, entity_hit, candidate))
        scored.sort(key=lambda item: (-item[0], not item[1],
                                      item[2]['candidate_id']))
        selected = []
        for _score_value, _entity_hit, candidate in scored[:20]:
            item = dict(candidate)
            item['checkpoint'] = checkpoint
            item['match_score'] = _score_value
            item['entity_hit'] = _entity_hit
            selected.append(item)
        # Readiness is evaluated at the patch target.  A higher-scoring fact
        # that exists only in the PoC/probe frame must not mask a slightly
        # lower-scoring fact that is actually visible where the assertion is
        # injected.
        visible_selected = [item for item in selected
                            if item.get('visible_at_injection')]
        top_pool = select_typed_top(visible_selected or selected, row)
        top_score = top_pool[0]['match_score'] if top_pool else 0
        def _priority(item: dict) -> int:
            if item.get('scope') in {'single_contract', 'cross_contract',
                                     'function_scope'}:
                return 3
            if item.get('scope') == 'business_function_scope':
                return 2
            return 1

        top_items = [item for item in top_pool
                     if item['match_score'] == top_score]
        top_priority = max((_priority(item) for item in top_items), default=0)
        top_items = [item for item in top_items
                     if _priority(item) == top_priority]
        top_expressions = {item['expression'] for item in top_items}
        ambiguous = len(top_expressions) > 1
        best_high = (not ambiguous and
                     any(item.get('_strong') for item in selected))
        for item in selected:
            item['ambiguous'] = bool(
                ambiguous and item.get('match_score') == top_score
                and _priority(item) == top_priority)
            base_ready = bool(item.get('ready_eligible'))
            if item.get('scope') == 'business_function_scope':
                base_ready = bool(
                    item.get('typed')
                    and item.get('visible_at_injection')
                    and int(item.get('chain_depth') or 0) >= 1
                    and (int(item.get('structural_hits') or 0) > 0
                         or item.get('entity_hit')))
            item['ready_eligible'] = bool(
                base_ready and not item['ambiguous']
                and item.get('match_score') == top_score
                and _priority(item) == top_priority)
            item.pop('_strong', None)
        symbols[symbol] = {
            'symbol': symbol,
            'roles': list(row.get('appears_in') or []),
            'sort': row.get('sort'),
            'unit': row.get('unit'),
            'meaning': row.get('meaning'),
            'expected_kind': expected_kind,
            'checkpoint': checkpoint,
            'candidates': selected,
            'ambiguous': ambiguous,
            'top_candidate_expressions': sorted(top_expressions),
            'observability': ('high' if selected and best_high else
                              'medium' if selected else 'low'),
            'unobservable_reason': None if selected else (
                'no visible state variable, getter, or receiver-qualified '
                'field matches the symbol semantics'),
        }
        candidate_rows[symbol] = selected

    recipe_plans = observable_recipes.build(
        symbols, candidate_rows, source=candidate_business,
        signatures=signatures, all_candidates=candidates)
    for symbol, plan in recipe_plans.items():
        symbols[symbol]['recipe_plan'] = plan
        symbols[symbol]['recipes'] = plan['recipes']
    return {
        'schema_version': SCHEMA_VERSION,
        'claim_id': claim_id,
        'injection_contract': patch_contract,
        'probe_contract': probe_contract,
        'probe_function': probe_function,
        'patch_contract': patch_contract,
        'patch_function': (sorted(patch_function_set)[0]
                           if len(patch_function_set) == 1 else None),
        'patch_functions': sorted(patch_function_set),
        'symbol_table': symbol_table,
        'symbols': symbols,
        'summary': {
            'symbols': len(symbols),
            'with_candidates': sum(bool(row['candidates'])
                                   for row in symbols.values()),
            'unobservable': sum(not row['candidates']
                                for row in symbols.values()),
            'candidate_count': sum(len(row['candidates'])
                                   for row in symbols.values()),
            'typed_candidates': sum(
                bool(candidate.get('typed'))
                for row in symbols.values()
                for candidate in row['candidates']),
            'scoped_candidates': sum(
                candidate.get('scope') == 'business_function_scope'
                for row in symbols.values()
                for candidate in row['candidates']),
            'visible_candidates': sum(
                bool(candidate.get('visible_at_injection', True))
                for row in symbols.values()
                for candidate in row['candidates']),
            'typed_state_vars': len(symbol_table.get('state_vars') or []),
            'function_scope_vars': len(symbol_table.get('function_scopes')
                                       or []),
            'mutation_symbols': len(symbol_table.get('mutation_sites') or {}),
            'recipe_ready': sum(
                (row.get('recipe_plan') or {}).get('status') == 'ready'
                for row in symbols.values()),
            'recipe_compilable': sum(
                bool((row.get('recipe_plan') or {}).get('compile_ready_count'))
                for row in symbols.values()),
            'recipe_planned': sum(
                (row.get('recipe_plan') or {}).get('status') == 'planned'
                for row in symbols.values()),
            'recipe_unobservable': sum(
                (row.get('recipe_plan') or {}).get('status') == 'unobservable'
                for row in symbols.values()),
            'recipe_count': sum(len(row.get('recipes') or [])
                                for row in symbols.values()),
        },
    }


def candidate_expressions(ir: dict, symbol: str) -> list[str]:
    return [row['expression'] for row in
            ((ir.get('symbols') or {}).get(symbol) or {}).get('candidates', [])]


def select_typed_top(items: list[dict], symbol_row: dict) -> list[dict]:
    """Drop top candidates whose known Solidity type contradicts the symbol.

    Ambiguity must be judged among candidates that could actually bind the
    symbol.  A bool flag and a uint counter with the same lexical score are
    not ambiguous for a numeric symbol; the bool is type-incompatible.
    """
    kind = observable_recipes.expected_kind(symbol_row)
    compatible = [item for item in items
                  if observable_recipes.type_compatible(
                      kind, item.get('solidity_type')) is not False]
    return compatible or items


def candidate_identifiers(ir: dict, symbol: str) -> list[str]:
    """Identifiers introduced by candidates, for the binding prompt/lint."""
    result: list[str] = []
    for expression in candidate_expressions(ir, symbol):
        for root in base_identifiers(expression):
            if root not in result:
                result.append(root)
    return result


def ready_recipe_expressions(ir: dict, symbol: str) -> list[str]:
    plan = ((ir.get('symbols') or {}).get(symbol) or {}).get(
        'recipe_plan') or {}
    return [row['expression'] for row in plan.get('recipes') or []
            if row.get('executable') and row.get('confidence') == 'high'
            and row.get('expression')]


def audit_recipes(binding: dict, ir: dict) -> dict:
    plans = {
        symbol: row.get('recipe_plan') or {}
        for symbol, row in (ir.get('symbols') or {}).items()
        if isinstance(row, dict)
    }
    return observable_recipes.audit(binding, plans)


def audit_binding(binding: dict, ir: dict,
                  declared_roots: set[str] | None = None) -> dict:
    """Check that each non-UNBOUND expression is grounded in an IR candidate.

    This is intentionally a soft check: a valid expression may combine a
    candidate with a builtin (``block.timestamp``) or a literal.  We report
    roots that are not in any candidate for the symbol, but leave the final
    decision to the existing source lint/forge.
    """
    problems: list[dict] = []
    declared_roots = set(declared_roots or set())
    signatures = ((ir.get('symbol_table') or {}).get('signatures') or {})
    functions = signatures.get('functions') or {}
    patch = binding.get('patch') if isinstance(binding.get('patch'), dict) else {}
    patch_contract = patch.get('contract')
    patch_functions = {
        str(row.get('name') if isinstance(row, dict) else row)
        for row in (patch.get('functions') or [])
        if (row.get('name') if isinstance(row, dict) else row)
    }
    ir_patch_functions = {str(name) for name in
                          (ir.get('patch_functions') or [])
                          if str(name or '').strip()}

    def _arity(text: str) -> int:
        text = text.strip()
        if not text:
            return 0
        depth = 0
        count = 1
        for char in text:
            if char in '([{':
                depth += 1
            elif char in ')]}':
                depth = max(0, depth - 1)
            elif char == ',' and depth == 0:
                count += 1
        return count

    def _normal(value: str) -> str:
        return re.sub(r'\s+', '', str(value or ''))

    for symbol, entry in (binding.get('bindings') or {}).items():
        if not isinstance(entry, dict):
            continue
        expr = str(entry.get('solidity_expr') or '').strip()
        if not expr or expr == 'UNBOUND':
            continue
        candidate_rows = (((ir.get('symbols') or {}).get(symbol) or {})
                          .get('candidates') or [])
        exact = [row for row in candidate_rows
                 if _normal(row.get('expression')) == _normal(expr)]
        expected = entry.get('kind') or entry.get('binding_kind')
        if exact:
            candidate = exact[0]
            if candidate.get('ambiguous'):
                problems.append({
                    'symbol': symbol,
                    'code': 'AMBIGUOUS_OBSERVABLE',
                    'severity': 'error',
                    'message': ('selected observable has equally scored code '
                                'facts; receiver or member is ambiguous'),
                })
            type_ok = observable_recipes._type_compatible(
                expected, candidate.get('solidity_type'))
            if type_ok is False:
                problems.append({
                    'symbol': symbol,
                    'code': 'BINDING_TYPE_MISMATCH',
                    'severity': 'error',
                    'message': (f'expected {expected or "unknown"} but candidate '
                                f'has Solidity type '
                                f'{candidate.get("solidity_type")}'),
                })
            if (candidate.get('kind') == 'source_expr'
                    and not candidate.get('receiver_known')
                    and expr.split('.', 1)[0] not in declared_roots):
                problems.append({
                    'symbol': symbol,
                    'code': 'BINDING_RECEIVER_UNKNOWN',
                    'severity': 'error',
                    'message': ('source chain receiver is not a typed state '
                                'variable, parameter, or local'),
                })
            if candidate.get('scope') == 'business_function_scope':
                mismatch = False
                allowed_functions = patch_functions or ir_patch_functions
                if (not allowed_functions
                        or candidate.get('function') not in allowed_functions):
                    mismatch = True
                if (patch_contract
                        and candidate.get('contract') != patch_contract):
                    mismatch = True
                if mismatch:
                    problems.append({
                        'symbol': symbol,
                        'code': 'BINDING_SCOPE_MISMATCH',
                        'severity': 'error',
                        'message': (
                            'observable is only typed inside '
                            f'{candidate.get("contract")}.'
                            f'{candidate.get("function")}, but the binding '
                            'patch target is '
                            f'{patch_contract or "unspecified"}.'
                            f'{sorted(patch_functions) or ["unspecified"]}'),
                    })
            if (candidate.get('kind') in {'state_var', 'source_expr'}
                    and not candidate.get('mutation_sites')
                    and 'changed' in symbol.lower()):
                problems.append({
                    'symbol': symbol,
                    'code': 'BINDING_MUTATION_SITE_MISSING',
                    'severity': 'warning',
                    'message': ('changed-state symbol has no deterministic '
                                'mutation site in the typed symbol table'),
                })
        for name, args in re.findall(
                r'([A-Za-z_][A-Za-z0-9_]*)\s*\(([^()]*)\)', expr):
            overloads = functions.get(name) or []
            if not overloads:
                continue
            arity = _arity(args)
            extension_ok = False
            member_types = (exact[0].get('member_types') or []) if exact else []
            exact_leaf = (str(exact[0].get('expression') or '')
                          .rstrip(')').rsplit('(', 1)[0].rsplit('.', 1)[-1]
                          if exact else '')
            if len(member_types) >= 2 and name == exact_leaf:
                receiver_type = _bare_type(member_types[-2])
                extension_ok = any(
                    row.get('arity') == arity + 1
                    and _bare_type((row.get('param_types') or [None])[0])
                    == receiver_type
                    for row in overloads)
            if (all(row.get('arity') != arity for row in overloads)
                    and not extension_ok):
                problems.append({
                    'symbol': symbol,
                    'code': 'BINDING_OVERLOAD_ARITY',
                    'severity': 'error',
                    'message': (f'call {name}() has arity {arity}, but no '
                                'declared overload matches'),
                })
        allowed = set(candidate_identifiers(ir, symbol))
        roots = set(base_identifiers(expr))
        unknown = sorted(root for root in roots
                         if root not in allowed and root not in declared_roots
                         and root not in {'msg', 'block', 'tx', 'true', 'false',
                                          'address', 'this'})
        if unknown:
            problems.append({
                'symbol': symbol,
                'code': 'EXPRESSION_NOT_IN_IR',
                'severity': 'warning',
                'message': 'expression roots not present in observable IR: '
                           + ', '.join(unknown),
            })
    return {
        'schema_version': 'stage3-observable-binding-audit/2',
        'ok': not any(row['severity'] == 'error' for row in problems),
        'problems': problems,
    }
