"""Generate a binding.json skeleton from a stage-2 run's binding_contract.

The skeleton is intentionally non-compiling until a human fills the
``solidity_expr`` / ``patch`` / ``probe`` placeholders. It removes the
mechanical JSON typing, symbol enumeration and checkpoint derivation, and now
keeps the stage-2 semantic hints (``meaning`` / ``appears_in`` / ``unit`` /
``entity_ids``) plus, when Solidity sources are provided, a ``candidates`` list
of source identifiers whose names match the symbol's entity/meaning tokens.
Semantic binding itself remains explicit and human-owned.
"""
from __future__ import annotations

import re
from pathlib import Path

from lib.spec_loader import SpecError, claim_binding_contract, load_stage2_run
from lib.solidity_scan import (IDENT, scan_src, contract_visible_state_vars,
                               function_owner, poc_test_contract,
                               state_var_owner)


def _checkpoint(symbol: dict) -> str:
    text = str(symbol.get('checkpoint') or '')
    if 'before' in text:
        return 'before'
    if 'after' in text:
        return 'after'
    return 'input'


def _hint_tokens(symbol: dict) -> set[str]:
    """Normalize entity ids and meaning words into lowercase match tokens."""
    tokens: set[str] = set()
    for key in ('entity_ids',):
        for value in symbol.get(key) or []:
            for tok in re.findall(r'[a-z0-9_]+', str(value).lower()):
                if len(tok) >= 3:
                    tokens.add(tok)
    for word in re.findall(r'[a-z0-9_]+', str(symbol.get('meaning') or '').lower()):
        if len(word) >= 4:
            tokens.add(word)
    return tokens


def _entity_tokens(symbol: dict) -> set[str]:
    tokens: set[str] = set()
    for value in symbol.get('entity_ids') or []:
        for tok in re.findall(r'[a-z0-9_]+', str(value).lower()):
            if len(tok) >= 3:
                tokens.add(tok)
    return tokens


def _candidate_analysis(symbol: dict, declared: set[str],
                        scope: set[str] | None = None,
                        state_vars: set[str] | None = None) -> tuple[list[str], str]:
    """Return ``(candidates, observability)`` for one binding symbol.

    ``observability`` is ``high`` when an entity-id token matches a declared
    identifier inside ``scope``, ``medium`` when only meaning words match, and
    ``low`` when no in-scope identifier matches at all. When ``scope`` is given
    (the injection contract's transitive inheritance closure), candidates that
    live outside that scope are dropped so cross-contract state variables are
    never suggested as bindable identifiers.
    """
    entity_tokens = _entity_tokens(symbol)
    tokens = _hint_tokens(symbol)
    scored: list[tuple[int, bool, str]] = []
    for name in declared:
        if len(name) < 3:
            continue
        if (scope is not None and state_vars is not None
                and name in state_vars and name not in scope):
            continue
        lower = name.lower()
        if '_' in lower:
            parts = set(re.findall(r'[a-z0-9_]+', lower))
        else:
            parts = set(re.findall(r'[a-z0-9]+', lower))
        entity_hit = any(tok in parts or tok in lower for tok in entity_tokens)
        score = sum(1 for tok in tokens
                    if tok in parts or tok in lower or lower in tok)
        if score:
            scored.append((score, entity_hit, name))
    scored.sort(key=lambda pair: (-pair[0], not pair[1], pair[2]))
    candidates = [name for _, _, name in scored[:6]]
    if candidates and any(hit for _, hit, _ in scored):
        observability = 'high'
    elif candidates:
        observability = 'medium'
    else:
        observability = 'low'
    return candidates, observability


def classify_expressibility(stage2_dir: Path, claim_id: str, *,
                                src: Path) -> dict:
    """Classify whether a claim's safety invariant is dynamically expressible.

    This is the stage-3 root-cause gate: an invariant is only assert-able when
    its safety (I) symbols can be written as a boolean expression over
    identifiers declared inside a *single* contract (the injection point).
    Claims that are not expressible must be routed to a reference patch or
    marked not_dynamically_verifiable instead of being retried as a binding
    failure.
    """
    stage2 = load_stage2_run(stage2_dir)
    contract = claim_binding_contract(stage2['spec'], claim_id)
    symbols = [row for row in contract.get('symbols', [])
               if row.get('appears_in') and 'I' in (row.get('appears_in') or [])]
    if not symbols:
        return {'claim_id': claim_id, 'expressibility': 'expressible',
                'reason': 'no_safety_symbols', 'symbols': []}

    source_text = src.read_text() if src.is_file() else         '\n'.join(p.read_text() for p in sorted(src.glob('*.sol')))
    index = scan_src(src)
    declared = index.all_observable()
    functions = set().union(*(set(f.functions) for f in index.files.values()))
    anchor_space = functions | index.all_state_vars()

    symbol_rows = []
    owner_contracts: set[str] = set()
    any_unobservable = False
    for sym in symbols:
        candidates, observability = _candidate_analysis(sym, declared, None, None)
        anchors = [c for c in candidates if c in anchor_space]
        owners: set = set()
        for c in anchors:
            owners |= function_owner(source_text, c) | state_var_owner(source_text, c)
        contracts = {o for o in owners if o is not None}
        if not anchors or observability == 'low':
            any_unobservable = True
        owner_contracts |= contracts
        symbol_rows.append({
            'symbol': sym['symbol'], 'observability': observability,
            'candidates': candidates[:6], 'owner_contracts': sorted(contracts),
        })

    if any_unobservable:
        kind = 'unobservable'
    elif len(owner_contracts) > 1:
        kind = 'multi_contract'
    else:
        kind = 'expressible'
    return {'claim_id': claim_id, 'expressibility': kind,
            'reason': ('safety symbols span multiple contracts'
                       if kind == 'multi_contract' else
                       ('some safety symbols have no code anchor'
                        if kind == 'unobservable' else 'ok')),
            'owner_contracts': sorted(owner_contracts),
            'symbols': symbol_rows}


def build_skeleton(stage2_dir: Path, claim_id: str, *, src: Path | None = None) -> dict:
    stage2 = load_stage2_run(stage2_dir)
    contract = claim_binding_contract(stage2['spec'], claim_id)
    symbols = [row for row in contract.get('symbols', []) if row.get('appears_in')]
    if not symbols:
        raise SpecError(f'claim {claim_id} has no bindable symbols')

    declared: set[str] = set()
    state_vars: set[str] = set()
    scope: set[str] | None = None
    if src is not None:
        try:
            index = scan_src(src)
            declared = index.all_observable()
            state_vars = index.all_state_vars()
        except FileNotFoundError:
            declared = set()
            state_vars = set()
        try:
            src_path = Path(src)
            if src_path.is_file():
                source_text = src_path.read_text()
            else:
                sources = sorted(src_path.glob('*.sol'))
                source_text = '\n'.join(p.read_text() for p in sources)
            poc = poc_test_contract(source_text)
            if poc:
                scope = contract_visible_state_vars(source_text, poc)
        except (OSError, FileNotFoundError):
            scope = None

    bindings = {}
    for row in symbols:
        symbol = row['symbol']
        entry = {
            'kind': row.get('binding_kind') or 'boolean_predicate',
            'solidity_expr': f'TODO_BIND_{symbol}',
            'checkpoint': _checkpoint(row),
            'source': 'Contract.sol:functionName',
            'hints': {
                'meaning': row.get('meaning'),
                'appears_in': row.get('appears_in'),
                'unit': row.get('unit'),
                'entity_ids': row.get('entity_ids'),
            },
        }
        candidates, observability = _candidate_analysis(row, declared, scope,
                                                       state_vars)
        entry['observability'] = observability
        if candidates:
            entry['candidates'] = candidates
        bindings[symbol] = entry
    return {
        'schema_version': 'stage3-binding/1',
        'claim_id': claim_id,
        'bindings': bindings,
        'patch': {
            'file': 'Contract.sol',
            'contract': 'ContractName',
            'functions': [{'name': 'functionName'}],
        },
        'probe': {
            'contract': 'ContractName',
            'exploit_test': 'test_exploit',
            'safety_test': 'test_safety',
        },
    }
