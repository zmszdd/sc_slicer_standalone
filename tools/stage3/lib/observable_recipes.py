"""Deterministic recipes for turning Stage-2 business facts into code facts.

The observable IR enumerates identifiers that are visible at an injection
point.  This module adds the missing *shape* layer: a state snapshot, a
before/after transition, an authorization predicate, or a call-outcome plan.
It never invokes a model and never invents an identifier that is absent from
the source or from the IR candidate list.
"""
from __future__ import annotations

import hashlib
import re

from lib.solidity_scan import function_owner

SCHEMA_VERSION = 'stage3-observable-recipes/3'

_TRANSITION_SUFFIXES = {
    'changed': '!=',
    'unchanged': '==',
    'drained': '>',
}
_CHECKPOINT_WORDS = {'before', 'after', 'post', 'pre', 'entry', 'completion',
                     'input', 'output'}
_SUCCESS_WORDS = re.compile(
    r'\b(?:succeed|succeeds|succeeded|success|complete|completes|'
    r'completed|execute|executes|executed|return|returns)\b', re.I)
_FAILURE_WORDS = re.compile(
    r'\b(?:revert|reverts|reverted|fail|fails|failed|reject|rejects|'
    r'rejected|blocked|frozen|paused)\b', re.I)
_AUTH_WORDS = re.compile(
    r'\b(?:authorized|authorised|permission|privileged|owner|role|admin)\b',
    re.I)
_AGGREGATE_WORDS = re.compile(
    r'\b(?:size|count|length|number|total|balance|supply|liquidity|'
    r'orders|queue|depth|price|level)\b', re.I)


def _tokens(value: str | None) -> set[str]:
    return {token.lower() for token in re.findall(r'[A-Za-z0-9_]+',
                                                   str(value or ''))
            if len(token) >= 3}


def _split_identifier(value: str) -> set[str]:
    return {part.lower() for part in re.findall(r'[A-Z]?[a-z]+|[0-9]+', value)}


def _base_tokens(name: str, meaning: str | None = None) -> set[str]:
    tokens = _split_identifier(name)
    if meaning:
        tokens |= _tokens(meaning)
    return tokens - _CHECKPOINT_WORDS - {
        'change', 'changed', 'unchanged', 'drained', 'succeeds', 'succeeded',
        'success', 'fails', 'failed', 'failure', 'reverts', 'reverted',
    }


def _checkpoint(value: str | None) -> str:
    text = str(value or '').lower()
    for marker in ('before', 'input', 'after'):
        if marker in text:
            return marker
    return 'input'


def _expected_kind(row: dict) -> str:
    explicit = row.get('binding_kind') or row.get('expected_kind')
    if explicit:
        return str(explicit)
    sort = str(row.get('sort') or '').strip().lower()
    if sort == 'bool':
        return 'boolean_predicate'
    if sort == 'address':
        return 'address_value'
    if sort.startswith(('uint', 'int')):
        return 'numeric_value'
    return 'boolean_predicate'


def _suffix(name: str) -> str | None:
    lower = name.lower()
    for suffix in ('changed', 'unchanged', 'drained'):
        if lower.endswith('_' + suffix) or lower.endswith(suffix):
            return suffix
    return None


def _recipe(*, recipe_id: str, kind: str, expression: str | None,
            checkpoint: str, executable: bool, confidence: str,
            evidence: list[str], solidity_type: str | None = None,
            solidity_stmts: list[str] | None = None,
            required_inputs: list[str] | None = None,
            visible_at_injection: bool | None = None,
            source_grounded: bool | None = None,
            ambiguous: bool | None = None) -> dict:
    return {
        'recipe_id': recipe_id,
        'kind': kind,
        'expression': expression,
        'checkpoint': checkpoint,
        'executable': bool(executable and expression),
        'confidence': confidence,
        'solidity_type': solidity_type,
        'solidity_stmts': list(solidity_stmts or []),
        'required_inputs': list(required_inputs or []),
        'evidence': list(evidence),
        'visible_at_injection': visible_at_injection,
        'source_grounded': source_grounded,
        'ambiguous': ambiguous,
    }


def _type_compatible(expected: str | None, solidity_type: str | None):
    """Return True/False when a type is known; None when it is not provable."""
    expected = str(expected or '')
    actual = re.sub(r'\s+', '', str(solidity_type or ''))
    if not actual:
        return None
    if actual in {'bool'}:
        return True if expected == 'boolean_predicate' else False
    if actual.startswith(('uint', 'int')):
        return False if expected in {'address_value', 'boolean_predicate'} \
            else True if expected == 'numeric_value' else None
    if actual == 'address':
        return False if expected in {'numeric_value', 'boolean_predicate'} \
            else True if expected == 'address_value' else None
    # Contract and struct values are not scalar snapshots.  A contract handle
    # can stand in for an address binding, but never for a numeric/boolean one.
    if actual:
        if expected in {'numeric_value', 'boolean_predicate'}:
            return False
        if expected == 'address_value' and actual[:1].isupper():
            return True
    return None


def type_compatible(expected: str | None, solidity_type: str | None):
    """Public alias used by the IR candidate selector."""
    return _type_compatible(expected, solidity_type)


def expected_kind(row: dict) -> str:
    """Public alias for the binding-kind inferred from a symbol row."""
    return _expected_kind(row)


def _direct_recipes(symbol: str, row: dict, candidates: list[dict]) -> list[dict]:
    recipes = []
    checkpoint = _checkpoint(row.get('checkpoint'))
    for index, candidate in enumerate(candidates[:8]):
        kind = candidate.get('kind') or 'observable'
        expression_parts = _split_identifier(str(candidate.get('expression') or ''))
        symbol_parts = _split_identifier(symbol) - {'the', 'and', 'for', 'with',
                                                    'before', 'after', 'post'}
        exact_symbol_member = bool(expression_parts) and expression_parts <= symbol_parts
        recipe_kind = 'state_snapshot'
        if kind in {'getter', 'cross_contract_getter'}:
            recipe_kind = 'call_return'
        elif kind == 'cross_contract_state':
            recipe_kind = 'cross_contract_fact'
        structural = int(candidate.get('structural_hits') or 0)
        score = int(candidate.get('match_score') or 0)
        source_expr = candidate.get('kind') == 'source_expr'
        if 'ready_eligible' in candidate:
            strong = bool(candidate.get('ready_eligible'))
        else:
            strong = bool(
                candidate.get('source_grounded', True)
                and (exact_symbol_member
                     or (not source_expr and structural >= 2)
                     or (candidate.get('entity_hit') and score >= 3)
                     or (source_expr and candidate.get('receiver_known')
                         and structural >= 2)
                     or (source_expr
                         and int(candidate.get('chain_depth') or 0) >= 2
                         and structural >= 2)))
        scope_ok = (
            bool(candidate.get('ready_eligible'))
            or candidate.get('scope') in {'single_contract', 'cross_contract',
                                          'function_scope'}
            or (source_expr and (candidate.get('receiver_known')
                                 or int(candidate.get('chain_depth') or 0) >= 2)))
        type_ok = _type_compatible(_expected_kind(row),
                                   candidate.get('solidity_type'))
        confidence = ('high' if strong and scope_ok and type_ok is True
                      else 'medium')
        if candidate.get('ambiguous'):
            confidence = 'medium'
        recipes.append(_recipe(
            recipe_id=f'{symbol}:direct:{index}',
            kind=recipe_kind,
            expression=candidate.get('expression'),
            checkpoint=checkpoint,
            executable=True,
            confidence=confidence,
            solidity_type=candidate.get('solidity_type'),
            evidence=([candidate.get('evidence') or 'IR candidate'] +
                      (['ambiguous candidate: multiple equally scored '
                        'code facts'] if candidate.get('ambiguous') else [])),
            visible_at_injection=(candidate.get('visible_at_injection')
                                  if 'visible_at_injection' in candidate
                                  else None),
            source_grounded=(candidate.get('source_grounded')
                             if 'source_grounded' in candidate else None),
            ambiguous=bool(candidate.get('ambiguous')),
        ))
    return recipes


def _pair_index(symbols: dict[str, dict]) -> list[tuple[str, str, set[str]]]:
    before: dict[str, set[str]] = {}
    after: dict[str, set[str]] = {}
    for name, row in symbols.items():
        if _suffix(name) is not None:
            continue
        tokens = _base_tokens(name)
        checkpoint = _checkpoint(row.get('checkpoint'))
        if checkpoint == 'before' and 'after' not in _tokens(
                row.get('checkpoint')):
            before[name] = tokens
        if checkpoint == 'after' or 'after' in _tokens(row.get('checkpoint')):
            after[name] = tokens
    pairs = []
    for left, left_tokens in before.items():
        for right, right_tokens in after.items():
            if left_tokens == right_tokens:
                pairs.append((left, right, left_tokens))
    return sorted(pairs)


def _derived_transition(symbol: str, row: dict,
                        symbols: dict[str, dict],
                        candidates: dict[str, list[dict]]) -> list[dict]:
    suffix = _suffix(symbol)
    if suffix is None:
        return []
    base_tokens = _base_tokens(symbol)
    matched = [pair for pair in _pair_index(symbols)
               if base_tokens <= pair[2]]
    if len(matched) != 1:
        return []
    before, after, _tokens_value = matched[0]
    before_rows = candidates.get(before) or []
    after_rows = candidates.get(after) or []
    if not before_rows or not after_rows:
        return []
    before_expr = before_rows[0].get('expression')
    after_expr = after_rows[0].get('expression')
    if not before_expr or not after_expr:
        return []
    visibility = [
        item.get('visible_at_injection')
        for item in (before_rows[0], after_rows[0])
    ]
    visible = (all(item is True for item in visibility)
               if any(item is not None for item in visibility) else None)
    op = _TRANSITION_SUFFIXES[suffix]
    expression = f'stage3_{before} {op} ({after_expr})'
    confidence = ('high' if (symbols.get(before, {}).get('observability') ==
                             'high' and symbols.get(after, {}).get(
                                 'observability') == 'high') else 'medium')
    return [_recipe(
        recipe_id=f'{symbol}:transition',
        kind='state_before_after',
        expression=expression,
        checkpoint='after',
        executable=True,
        confidence=confidence,
        solidity_type='bool',
        evidence=[f'paired transition {before} -> {after}',
                  f'direct candidates {before_expr} / {after_expr}'],
        visible_at_injection=visible,
        source_grounded=True,
        ambiguous=any(bool(item.get('ambiguous'))
                      for item in (before_rows[0], after_rows[0])),
    )]


def _authorization_recipe(symbol: str, row: dict, source: str,
                          signatures: dict, candidates: list[dict]) -> list[dict]:
    meaning = str(row.get('meaning') or '')
    if not _AUTH_WORDS.search(meaning) and 'authorized' not in symbol.lower():
        return []
    functions = signatures.get('functions') or {}
    owner_getters = [name for name in ('owner', 'admin', 'governance')
                     if name in functions and any(
                         item.get('arity') == 0 for item in functions[name])]
    getter = owner_getters[0] if len(owner_getters) == 1 else None
    candidate_getters = [
        item.get('expression') for item in candidates
        if item.get('kind') in {'getter', 'cross_contract_getter'}
        and re.search(r'\b(?:owner|admin|governance)\s*\(', 
                      str(item.get('expression') or ''), re.I)]
    candidate_getters = list(dict.fromkeys(candidate_getters))
    expression = None
    evidence = []
    if len(candidate_getters) == 1:
        expression = f'msg.sender == {candidate_getters[0]}'
        evidence = [f'unique authorization getter {candidate_getters[0]}']
    elif getter and re.search(r'\b' + re.escape(getter) + r'\b', source):
        expression = f'msg.sender == {getter}()'
        evidence = [f'unique authorization getter {getter}()']
    if expression:
        return [_recipe(
            recipe_id=f'{symbol}:authorization:owner',
            kind='authorization_context',
            expression=expression,
            checkpoint=_checkpoint(row.get('checkpoint')),
            executable=True,
            confidence='medium',
            evidence=evidence,
            solidity_type='bool',
            **_candidate_metadata(candidate_getters[0] if len(candidate_getters) == 1
                                  else getter + '()' if getter else None,
                                  candidates),
        )]
    if 'onlyOwner' in source or 'hasRole' in source:
        return [_recipe(
            recipe_id=f'{symbol}:authorization:role',
            kind='authorization_context',
            expression=None,
            checkpoint=_checkpoint(row.get('checkpoint')),
            executable=False,
            confidence='low',
            evidence=['source uses onlyOwner/hasRole authorization'],
            required_inputs=('role',) if 'hasRole' in source else ('caller',),
        )]
    return []


def _matching_receivers(symbol: str, row: dict, candidates: list[dict],
                        function_name: str) -> list[str]:
    receivers: list[str] = []
    for item in candidates:
        expression = str(item.get('expression') or '').strip()
        if not expression or item.get('kind') not in {
                'source_expr', 'getter', 'cross_contract_getter',
                'state_var', 'cross_contract_state'}:
            continue
        leaf = expression.rstrip(')').rsplit('(', 1)[0].rsplit('.', 1)[-1]
        if leaf != function_name:
            continue
        receiver = expression.rsplit('.', 1)[0] if '.' in expression else ''
        if receiver and receiver not in receivers:
            receivers.append(receiver)
    return receivers


def _call_outcome_plan(symbol: str, row: dict, signatures: dict,
                       candidates: list[dict]) -> list[dict]:
    meaning = str(row.get('meaning') or '')
    if not (_SUCCESS_WORDS.search(meaning) or _FAILURE_WORDS.search(meaning)):
        return []
    action_tokens = _base_tokens(symbol, meaning)
    functions = signatures.get('functions') or {}
    matches = [name for name in functions
               if action_tokens & _split_identifier(name)]
    if len(matches) != 1:
        return []
    match = matches[0]
    overloads = functions.get(match) or []
    zero_arg = any(item.get('arity') == 0 for item in overloads)
    receivers = _matching_receivers(symbol, row, candidates, match)
    receiver = receivers[0] if len(receivers) == 1 else None
    local = 'stage3_' + re.sub(r'[^A-Za-z0-9_]+', '_', symbol) + '_succeeds'
    expression = local if zero_arg and receiver else None
    statements = []
    if expression:
        statements = [
            f'bool {local} = false',
            (f'try {receiver}.{match}() {{ {local} = true; }} '
             f'catch {{ {local} = false; }}'),
        ]
    return [_recipe(
        recipe_id=f'{symbol}:call-outcome',
        kind='call_outcome',
        expression=expression,
        checkpoint=_checkpoint(row.get('checkpoint')),
        executable=bool(expression),
        confidence=('high' if expression and
                    _expected_kind(row) == 'boolean_predicate' else
                    'medium' if expression else 'low'),
        evidence=[f'unique callable candidate {match}',
                  f'receiver={receiver}' if receiver else 'receiver unresolved'],
        solidity_stmts=statements,
        solidity_type='bool',
        **_candidate_metadata(
            next((item.get('expression') for item in candidates
                  if receiver and str(item.get('expression') or '').startswith(
                      str(receiver) + '.') and match in str(item.get('expression') or '')),
                 None),
            candidates),
        required_inputs=([] if expression else
                         ['receiver', 'call_arguments', 'success_or_revert_signal']),
    )]


def _candidate_metadata(expression: str | None,
                        candidates: list[dict]) -> dict:
    item = next((row for row in candidates
                 if row.get('expression') == expression), None) if expression else None
    if item is None:
        return {}
    return {
        'visible_at_injection': item.get('visible_at_injection'),
        'source_grounded': item.get('source_grounded'),
        'ambiguous': bool(item.get('ambiguous')),
    }


def _aggregate_plan(symbol: str, row: dict, signatures: dict,
                    candidates: list[dict]) -> list[dict]:
    meaning = str(row.get('meaning') or '')
    if not _AGGREGATE_WORDS.search(meaning) and not _AGGREGATE_WORDS.search(symbol):
        return []
    action_tokens = _base_tokens(symbol, meaning)
    functions = signatures.get('functions') or {}
    matches = [name for name in functions
               if action_tokens & _split_identifier(name)]
    if len(matches) != 1:
        return []
    match = matches[0]
    receivers = _matching_receivers(symbol, row, candidates, match)
    receiver = receivers[0] if len(receivers) == 1 else None
    expression = f'{receiver}.{match}()' if receiver else None
    return [_recipe(
        recipe_id=f'{symbol}:aggregate',
        kind='aggregate_fact',
        expression=expression,
        checkpoint=_checkpoint(row.get('checkpoint')),
        executable=bool(expression),
        confidence='medium' if expression else 'low',
        evidence=[f'unique aggregate function candidate {match}',
                  f'receiver={receiver}' if receiver else 'receiver unresolved'],
        required_inputs=[] if expression else ['receiver', 'arguments'],
    )]


def _declared_function(name: str, source: str) -> bool:
    return bool(re.search(r'\bfunction\s+' + re.escape(name) + r'\b', source))


def _overload(signatures: dict, name: str, arity: int | None = None) -> dict | None:
    rows = (signatures.get('functions') or {}).get(name) or []
    if arity is None:
        return rows[0] if rows else None
    return next((row for row in rows if row.get('arity') == arity), None)


def _unique_receiver(function_names: tuple[str, ...],
                     candidates: list[dict] | None, source: str,
                     signatures: dict) -> str | None:
    receivers: set[str] | None = None
    for name in function_names:
        marker = '.' + name + '('
        found = set()
        for item in candidates or []:
            expression = str(item.get('expression') or '')
            if marker in expression:
                receiver = expression.split(marker, 1)[0]
                if receiver and '(' not in receiver:
                    found.add(receiver)
        if not found:
            return None
        receivers = found if receivers is None else receivers & found
        if not receivers:
            return None
    return next(iter(receivers)) if receivers and len(receivers) == 1 else None


def _receiver_from_state(function_names: tuple[str, ...],
                         candidates: list[dict] | None, source: str,
                         signatures: dict) -> str | None:
    owners: set[str] = set()
    for name in function_names:
        owners |= set(function_owner(source, name))
    if not owners:
        return None
    receivers = {
        str(name) for name, typ in (signatures.get('state_vars') or {}).items()
        if typ in owners
    }
    visible = set()
    for item in candidates or []:
        expression = str(item.get('expression') or '')
        if '.' not in expression:
            continue
        root = expression.split('.', 1)[0]
        if root in receivers:
            visible.add(root)
    return next(iter(visible)) if len(visible) == 1 else None


def _resolve_receiver(function_names: tuple[str, ...],
                      candidates: list[dict] | None, source: str,
                      signatures: dict) -> str | None:
    return (_unique_receiver(function_names, candidates, source, signatures)
            or _receiver_from_state(function_names, candidates, source,
                                    signatures))


def _local_expr(candidates: list[dict] | None, name: str, fallback: str) -> str:
    for item in candidates or []:
        if (item.get('expression') == name
                and item.get('kind') in {'function_local', 'parameter'}):
            return name
    return fallback


def _order_book_recipe(symbol: str, row: dict, source: str, signatures: dict,
                       all_candidates: list[dict] | None) -> list[dict]:
    if _expected_kind(row) != 'numeric_value':
        return []
    text = f'{symbol} {row.get("meaning") or ""}'.lower()
    checkpoint = _checkpoint(row.get('checkpoint'))
    side_anchor = 'args.side' in source and 'Side.BUY' in source
    side_expr = _local_expr(all_candidates, 'side', 'args.side')
    price_expr = _local_expr(all_candidates, 'price', 'args.price')
    suffix = hashlib.sha1(symbol.encode('utf-8')).hexdigest()[:8]

    is_tree_size = bool(re.search(
        r'\b(?:tree[_ ]size|price[_ ]levels?|number of price levels)\b', text)
        and not re.search(r'\bnumber of orders\b|\borders? at\b', text))
    is_lowest_price = bool(re.search(r'\b(?:lowest|worst|minimum)\b', text)
                           and 'price' in text)
    is_price_orders = bool(re.search(r'\borders?\b', text)
                           and re.search(r'price level', text))

    if is_tree_size and side_anchor:
        bid = _overload(signatures, 'getNumBids', 0)
        ask = _overload(signatures, 'getNumAsks', 0)
        if (bid and ask and _declared_function('getNumBids', source)
                and _declared_function('getNumAsks', source)):
            receiver = _resolve_receiver(
                ('getNumBids', 'getNumAsks'), all_candidates, source,
                signatures)
            prefix = receiver + '.' if receiver else ''
            expression = (f'{side_expr} == Side.BUY ? {prefix}getNumBids() '
                          f': {prefix}getNumAsks()')
            return [_recipe(
                recipe_id=f'{symbol}:order_book:tree_size',
                kind='order_book_aggregate',
                expression=expression,
                checkpoint=checkpoint,
                executable=True,
                confidence='medium',
                solidity_type='uint256',
                evidence=['source-declared getNumBids()/getNumAsks()',
                          'side selected by args.side at injection point'],
                visible_at_injection=True,
                source_grounded=True,
                ambiguous=False,
            )]

    if is_lowest_price and side_anchor:
        top = _overload(signatures, 'getTOB', 0)
        if (top and len(top.get('returns') or []) == 2
                and _declared_function('getTOB', source)):
            receiver = _resolve_receiver(('getTOB',), all_candidates, source,
                                         signatures)
            prefix = receiver + '.' if receiver else ''
            max_name = f'stage3_max_bid_{suffix}'
            min_name = f'stage3_min_ask_{suffix}'
            return [_recipe(
                recipe_id=f'{symbol}:order_book:top_of_book',
                kind='order_book_aggregate',
                expression=f'{side_expr} == Side.BUY ? {max_name} : {min_name}',
                solidity_stmts=[
                    f'(uint256 {max_name}, uint256 {min_name}) = '
                    f'{prefix}getTOB();'],
                checkpoint=checkpoint,
                executable=True,
                confidence='medium',
                solidity_type='uint256',
                evidence=['source-declared getTOB() returns (maxBid, minAsk)',
                          'side selected by args.side at injection point'],
                visible_at_injection=True,
                source_grounded=True,
                ambiguous=False,
            )]

    if is_price_orders and 'args.price' in source and side_anchor:
        limit = _overload(signatures, 'getLimit', 2)
        if (limit and (limit.get('returns') or [None])[0]
                and _declared_function('getLimit', source)
                and re.search(r'\bnumOrders\b', source)):
            receiver = _resolve_receiver(('getLimit',), all_candidates, source,
                                         signatures)
            prefix = receiver + '.' if receiver else ''
            return [_recipe(
                recipe_id=f'{symbol}:order_book:price_orders',
                kind='order_book_aggregate',
                expression=f'{prefix}getLimit({price_expr}, {side_expr}).numOrders',
                checkpoint=checkpoint,
                executable=True,
                confidence='medium',
                solidity_type='uint64',
                evidence=['source-declared getLimit(uint256, Side).numOrders'],
                visible_at_injection=True,
                source_grounded=True,
                ambiguous=False,
            )]
    return []


def build(symbols: dict[str, dict], candidates: dict[str, list[dict]],
          *, source: str, signatures: dict,
          all_candidates: list[dict] | None = None) -> dict[str, dict]:
    """Return per-symbol recipe plans.

    ``symbols`` is keyed by symbol name and contains the binding contract row.
    ``candidates`` is keyed by the same names and contains IR candidates.
    """
    result: dict[str, dict] = {}
    for symbol, row in symbols.items():
        expected = _expected_kind(row)
        recipes = _direct_recipes(symbol, row, candidates.get(symbol) or [])
        recipes += _derived_transition(symbol, row, symbols, candidates)
        recipes += _authorization_recipe(symbol, row, source, signatures,
                                         candidates.get(symbol) or [])
        recipes += _call_outcome_plan(symbol, row, signatures,
                                      candidates.get(symbol) or [])
        recipes += _aggregate_plan(symbol, row, signatures,
                                   candidates.get(symbol) or [])
        recipes += _order_book_recipe(symbol, row, source, signatures,
                                      all_candidates)
        if any(item['executable'] and item.get('confidence') == 'high'
               for item in recipes):
            status = 'ready'
        elif any(recipe_executable(item)
                 and is_compile_ready(item, expected, row.get('checkpoint'))
                 and item.get('visible_at_injection') is True
                 for item in recipes):
            status = 'ready'
        elif recipes:
            status = 'planned'
        else:
            status = 'unobservable'
        ready = [item for item in recipes
                 if item['executable'] and item.get('confidence') == 'high']
        compilable = [item for item in recipes
                      if recipe_executable(item)
                      and is_compile_ready(item, expected,
                                           row.get('checkpoint'))]
        result[symbol] = {
            'schema_version': SCHEMA_VERSION,
            'symbol': symbol,
            'status': status,
            'recipes': recipes,
            'ready_count': len(ready),
            'planned_count': len(recipes) - len(ready),
            'compile_ready_count': len(compilable),
            'compile_ready_ids': [item['recipe_id'] for item in compilable],
        }
    return result


def recipe_executable(recipe: dict) -> bool:
    return bool(recipe.get('executable') and recipe.get('expression'))


def is_compile_ready(recipe: dict, expected_kind: str | None = None,
                     checkpoint: str | None = None) -> bool:
    """True when a recipe is safe for deterministic binding compilation.

    The old ``high`` confidence label was too coarse: medium recipes can be
    deterministic when they are typed, checkpoint-consistent, unique and
    visible at the actual injection point.  Missing metadata is treated as
    unknown (legacy/offline input) rather than as a positive assertion.
    """
    if not recipe_executable(recipe):
        return False
    if recipe.get('confidence') not in {'high', 'medium'}:
        return False
    if recipe.get('visible_at_injection') is False:
        return False
    if recipe.get('source_grounded') is False:
        return False
    if recipe.get('ambiguous') is True:
        return False
    if checkpoint and recipe.get('checkpoint'):
        if _checkpoint(checkpoint) != _checkpoint(recipe.get('checkpoint')):
            return False
    expected = expected_kind or recipe.get('expected_kind')
    solidity_type = recipe.get('solidity_type')
    if expected and solidity_type:
        compatible = _type_compatible(expected, recipe.get('solidity_type'))
        if compatible is not True:
            return False
    return True


def audit(binding: dict, recipes: dict[str, dict]) -> dict:
    """Check that non-UNBOUND expressions select a ready recipe.

    The audit is advisory: legacy bindings may still be valid even when the
    recipe layer has no matching candidate.  New binding prompts and offline
    replay reports consume the result, while the existing source lint remains
    the final structural gate.
    """
    problems = []
    for symbol, entry in (binding.get('bindings') or {}).items():
        if not isinstance(entry, dict):
            continue
        expression = str(entry.get('solidity_expr') or '').strip()
        if not expression or expression == 'UNBOUND':
            continue
        plan = recipes.get(symbol) or {}
        ready = [item for item in plan.get('recipes') or []
                 if item.get('executable') and
                 item.get('confidence') == 'high']
        if not ready:
            continue
        roots = set(re.findall(r'[A-Za-z_][A-Za-z0-9_]*', expression))
        matched = False
        for item in ready:
            recipe_roots = set(re.findall(
                r'[A-Za-z_][A-Za-z0-9_]*', str(item.get('expression') or '')))
            if roots & recipe_roots:
                matched = True
                break
        if not matched:
            problems.append({
                'symbol': symbol,
                'code': 'RECIPE_NOT_SELECTED',
                'severity': 'warning',
                'message': 'expression does not use any ready observable recipe',
            })
    return {
        'schema_version': 'stage3-observable-recipe-audit/1',
        'ok': not any(row['severity'] == 'error' for row in problems),
        'problems': problems,
    }
