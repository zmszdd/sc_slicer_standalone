"""LLM-assisted binding proposal for stage-3 cases.

Given one stage-2 claim and the verified flattened source, propose a
``binding.json`` (symbol -> solidity_expr/patch/probe). The proposal is never
authoritative: it is written to ``binding.proposal.json`` and must pass the
deterministic ``lib.binding_validate`` lint before any forge run.

A proposal may be *partial*: symbols the model cannot confidently map to the
source are preserved with ``solidity_expr == "UNBOUND"`` and reported back with
``partial: true`` so a human only has to fill the remaining symbols. Partial
proposals are recorded but never run.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from lib import llm
from lib.spec_loader import (SpecError, claim_binding_contract, load_stage2_run,
                             precondition_symbols_for_claim,
                             safety_symbols_for_claim)
from lib.binding import CHECKPOINTS, KINDS, BINDING_SCHEMA
from lib.solidity_scan import (base_identifiers, contract_has_function,
                               contract_instances, function_owner,
                               poc_test_function)

PROPOSAL_SCHEMA = 'stage3-binding-proposal/1'
MAX_SOURCE_CHARS = 160000
TEST_TAIL_CHARS = 24000

_BEGIN = re.compile(r'^// ---- Begin flattened source: (.+) ----$', re.M)
_END = re.compile(r'^// ---- End flattened source: (.+) ----$', re.M)


def slice_flatten(source: str) -> str:
    """Drop forge-std fragments; keep header, business sources and tests.

    The PoC test fragment is essential for ``probe``/``patch``, so it is
    always kept whole; only the business sources are truncated on overflow.
    """
    lines = source.splitlines()
    header = []
    for line in lines:
        if line.startswith('// ---- Begin flattened source:'):
            break
        header.append(line)
    business: list[list[str]] = []
    tests: list[list[str]] = []
    current_path = None
    current: list[str] = []
    for line in lines:
        m = _BEGIN.match(line)
        if m:
            current_path = m.group(1)
            current = []
            continue
        e = _END.match(line)
        if e:
            if current_path and 'forge-std' not in current_path:
                (tests if ('/test/' in current_path or current_path.startswith('test/'))
                 else business).append(current)
            current_path = None
            current = []
            continue
        if current_path is not None:
            current.append(line)
    if current_path and 'forge-std' not in current_path:
        (tests if ('/test/' in current_path or current_path.startswith('test/'))
         else business).append(current)

    head = '\n'.join(header)
    test_text = '\n'.join('\n'.join(f) for f in tests)
    if len(test_text) > TEST_TAIL_CHARS:
        test_text = ('// ... test source head truncated (PoC usually near the end) ...\n'
                     + test_text[-TEST_TAIL_CHARS:])
    budget = MAX_SOURCE_CHARS - len(head) - len(test_text) - 100
    biz_text = '\n'.join('\n'.join(f) for f in business)
    if len(biz_text) > max(budget, 0):
        biz_text = biz_text[:max(budget, 0)] + '\n// ... business source truncated ...'
    return head + '\n' + biz_text + '\n' + test_text


def _symbols_payload(contract: dict, candidates: dict[str, list[str]] | None = None,
                     observability: dict[str, str] | None = None) -> list[dict]:
    rows = [r for r in contract.get('symbols', []) if r.get('appears_in')]
    payload = []
    for r in rows:
        row = {
            'symbol': r['symbol'],
            'sort': r.get('sort'),
            'unit': r.get('unit'),
            'meaning': r.get('meaning'),
            'checkpoint': r.get('checkpoint'),
            'entity_ids': r.get('entity_ids'),
            'appears_in': r.get('appears_in'),
            'binding_kind': r.get('binding_kind'),
        }
        if candidates and candidates.get(r['symbol']):
            row['candidate_identifiers'] = candidates[r['symbol']]
        if observability and observability.get(r['symbol']):
            row['observability'] = observability[r['symbol']]
        payload.append(row)
    return payload


_SYSTEM = (
    'You convert a natural-language P/I/V invariant claim into a stage-3 '
    'binding for Foundry differential testing. Output ONLY one JSON object '
    'matching the required_output_shape. Bind every listed symbol, observing '
    'it at the cited checkpoint using identifiers that actually exist in the '
    'source. Never invent identifiers and never reuse a symbol name as its own '
    'expression; if a symbol truly cannot be observed in the source, set its '
    'solidity_expr to the literal "UNBOUND" (keep the symbol entry, keep its '
    'kind/checkpoint/source).\n\n'
    'NUMERIC/LITERAL RULES\n'
    '- Numeric constants must be complete Solidity literals: write "1e18", '
    'not "e18"; write "100", not "hundred". Never emit a bare exponent or a '
    'unit name as an identifier.\n'
    'UNIT SCALING RULE\n'
    '- Each numeric symbol row carries a "unit" (e.g. "tokens", "USDC", '
    '"ETH"). Foundry storage/balances are usually wei-scaled (18 decimals), '
    'while the stage-2 formal constants are in the report\'s token unit. '
    'When binding a numeric symbol whose unit is a token-like count, divide '
    'the wei-scaled Solidity value by "1 ether" so the snapshot matches the '
    'formal constant: e.g. "creator.creatorAllowance(...) / 1 ether" for a '
    '"tokens" symbol, or "100" (not "100 ether") for a raw token count. '
    'Do NOT apply the division when the unit is already wei/1e18.\n\n'
    'FOCUS RULES\n'
    '- If the request carries a "focus_symbols" list and '
    '"keep_other_bindings_unchanged": true, output bindings ONLY for the '
    'symbols in focus_symbols (the other symbols were already bound and must '
    'stay unchanged). Return a minimal bindings object containing exactly '
    'those focus symbols.\n\n'
    'OBSERVABILITY RULES\n'
    '- Each symbol row carries an "observability" score: "high" means an '
    'entity-id token matches a declared identifier, "medium" means only '
    'meaning words match, "low" means no identifier matches. '
    '- For "low" observability symbols, or symbols with no '
    '"candidate_identifiers" list, do NOT guess an identifier: bind them as '
    '"UNBOUND" unless the source text itself shows an exact, unambiguous '
    'identifier. Prefer returning UNBOUND over fabricating a name.\n\n'
    'COMPOSITE EXPRESSION RULES\n'
    '- A symbol may be bound to a COMPOSITE Solidity expression, not only a '
    'single identifier. You may call real functions, compare values, combine '
    'booleans and use built-ins, as long as every root identifier exists in '
    'the source. Allowed example shapes:\n'
    '  * "token.totalSupply()" — public getter call\n'
    '  * "_extractValidUntil(sig) < block.timestamp" — function call + compare\n'
    '  * "balances[msg.sender] > 0" — mapping lookup + compare\n'
    '  * "owner == msg.sender" — address compare\n'
    '  * "amount * 1e18 / totalAssets" — numeric formula\n'
    '- For semantic invariants (e.g. "signature observable", "time window '
    'bound to owner"), construct a grounded composite expression from the '
    'candidate functions/state variables instead of returning "UNBOUND". '
    'Only fall back to "UNBOUND" when observability is "low" and no candidate '
    'identifier expresses the symbol.\n\n'
    'REPAIR HINT\n'
    '- If the request carries a "repair_hint", it lists what a previous '
    'attempt got wrong (lint errors, unbound symbols, or compile failures). '
    'Fix exactly those problems; keep every other binding unchanged unless it '
    'is part of the reported problem.\n\n'
    'CHECKPOINT RULES\n'
    '- Map the descriptive checkpoint to one of before/after/input. '
    '"before ..." -> "before"; "after ..."/an outcome -> "after"; an explicit '
    'input/parameter -> "input"; "during ..." -> "before" if it gates entry '
    'state, else "after" if it observes a resulting state.\n'
    '- For checkpoint "before", the pipeline auto-declares a snapshot '
    '``stage3_<symbol> = <your solidity_expr>`` at the function entry. So '
    'write the *entry-time* expression itself (a state getter such as '
    '``rewardsPool.totalShares()``, a public storage variable, or a call '
    'argument). Do NOT write ``stage3_`` yourself.\n'
    '- Boolean preconditions that hold on the exploit path may be bound to the '
    'literal "true". An effect that is the negation of the safety property may '
    'use "!".\n'
    '- NEVER bind a SAFETY (I-side) symbol to a bare "true"/"false" literal: a '
    'constant invariant is vacuous and the binding will be REJECTED. For an '
    'unobservable I-side symbol, emit "UNBOUND". A bare "true" is allowed ONLY '
    'for a P-side precondition that genuinely holds on the exploit path.\n'
    '- For numeric values, prefer a public getter or public storage variable; '
    'do not invent a comparison you cannot ground in the source.\n\n'
    'PATCH/PROBE RULES\n'
    '- patch.file and every "source" field must equal SOURCE_FILE_ON_DISK.\n'
    '- probe.contract and probe.exploit_test are the PoC test contract and '
    'function from INJECTION_POINT_ON_DISK (the harness that runs the exploit).\n'
    '- patch.contract is the contract that OWNS the invariant\'s referenced '
    'functions / state variables (normally the business contract the PoC test '
    'calls, NOT the test harness). patch.functions[0].name is the function in '
    'that contract which the invariant constrains and which the PoC test '
    'actually calls (e.g. the business function invoked during the exploit).\n'
    '- If every referenced symbol is visible inside the PoC test contract '
    'itself, patch.contract may equal probe.contract. Otherwise choose the '
    'business contract so the injected assertion is actually executed.\n'
    '- probe.safety_test is always null.\n\n'
    'FEW-SHOT EXAMPLE 1 (boolean + negation)\n'
    'symbols: two_floats_supplied_to_le (bool, before), le_returns_true '
    '(bool, after), le_returns_false_for_equal_floats (bool, after). '
    'Binding: two_floats_supplied_to_le -> {"kind":"boolean_predicate", '
    '"solidity_expr":"true","checkpoint":"before"}; le_returns_true -> '
    '{"solidity_expr":"isEqual","checkpoint":"after"}; '
    'le_returns_false_for_equal_floats -> {"solidity_expr":"!isEqual",'
    '"checkpoint":"after"}.\n\n'
    'FEW-SHOT EXAMPLE 2 (numeric before snapshot)\n'
    'symbols: balance_before (numeric, before), balance_after (numeric, '
    'after), amount (numeric, input) in a withdraw function. Binding: '
    'balance_before -> {"kind":"numeric_value","solidity_expr":'
    '"balances[msg.sender]","checkpoint":"before"}; balance_after -> '
    '{"solidity_expr":"balances[msg.sender]","checkpoint":"after"}; amount -> '
    '{"solidity_expr":"amount","checkpoint":"input"}.\n\n'
    'FEW-SHOT EXAMPLE 3 (composite expression for a semantic invariant)\n'
    'symbols: userop_expired (bool, after), valid_until (numeric, before), '
    'signature_observable (bool, input). Binding: userop_expired -> '
    '{"kind":"boolean_predicate","solidity_expr":'
    '"_extractValidUntil(sig) < block.timestamp","checkpoint":"after"}; '
    'valid_until -> {"kind":"numeric_value","solidity_expr":'
    '"_extractValidUntil(sig)","checkpoint":"before"}; signature_observable -> '
    '{"kind":"boolean_predicate","solidity_expr":"sig.length > 0",'
    '"checkpoint":"input"}.'
)


def _user_prompt(claim_id: str, symbols: list[dict], source: str,
                 hint: str | None = None,
                 focus: list[str] | None = None) -> str:
    payload = {
        'claim_id': claim_id,
        'symbols': symbols,
        'source': source,
        'required_output_shape': {
            'schema_version': BINDING_SCHEMA,
            'claim_id': claim_id,
            'bindings': {
                '<symbol>': {
                    'kind': 'boolean_predicate|address_value|numeric_value',
                    'solidity_expr': '<solidity expression or the literal "UNBOUND">',
                    'checkpoint': 'before|after|input',
                    'source': 'File.sol:functionName',
                },
            },
            'patch': {'file': '<file>', 'contract': '<contract>',
                      'functions': [{'name': '<test fn>'}]},
            'probe': {'contract': '<contract>',
                      'exploit_test': '<test fn>', 'safety_test': None},
        },
    }
    if hint:
        payload['repair_hint'] = hint
    if focus:
        payload['focus_symbols'] = focus
        payload['keep_other_bindings_unchanged'] = True
    return json.dumps(payload, ensure_ascii=False)


def _analyze(proposal: dict, claim_id: str, required: set[str]) -> tuple[list[str], list[str]]:
    """Return (hard_problems, unbound_symbols).

    ``hard_problems`` invalidate the proposal outright. ``unbound_symbols`` are
    symbols the model marked UNBOUND; the proposal shape is still valid and can
    be kept as a partial binding for later manual completion.
    """
    hard: list[str] = []
    unbound: list[str] = []
    if proposal.get('schema_version') != BINDING_SCHEMA:
        hard.append('schema_version mismatch')
    if proposal.get('claim_id') != claim_id:
        hard.append('claim_id mismatch')
    entries = proposal.get('bindings')
    if not isinstance(entries, dict):
        hard.append('bindings missing')
        return hard, unbound
    if set(entries) != required:
        hard.append(f'bindings do not cover symbols: {sorted(required ^ set(entries))}')
    for name, entry in entries.items():
        if not isinstance(entry, dict):
            hard.append(f'bad entry {name}')
            continue
        if entry.get('kind') not in KINDS:
            hard.append(f'bad kind for {name}')
        expr = str(entry.get('solidity_expr') or '')
        if entry.get('checkpoint') not in CHECKPOINTS:
            hard.append(f'bad checkpoint for {name}')
        if not str(entry.get('source') or '').strip():
            hard.append(f'bad source for {name}')
        if not expr.strip():
            hard.append(f'empty solidity_expr for {name}')
        elif expr.strip() == 'UNBOUND':
            unbound.append(name)
        elif 'TODO_BIND_' in expr or expr.strip() == name:
            hard.append(f'placeholder solidity_expr for {name}')
    return hard, unbound


def _test_function_calls(raw_source: str, test_function: str) -> set[str]:
    """Return the function-call identifiers inside one named function body."""
    marker = re.search(rf'\bfunction\s+{re.escape(test_function)}\s*\(', raw_source)
    if not marker:
        return set()
    open_idx = raw_source.find('{', marker.end())
    if open_idx < 0:
        return set()
    depth = 0
    close_idx = open_idx
    for i in range(open_idx, len(raw_source)):
        if raw_source[i] == '{':
            depth += 1
        elif raw_source[i] == '}':
            depth -= 1
            if depth == 0:
                close_idx = i
                break
    body = raw_source[open_idx + 1:close_idx]
    return set(re.findall(r'(?<![0-9])([A-Za-z_$][A-Za-z0-9_$]*)\s*\(', body))


def _migrate_patch_contract(raw_source: str, binding: dict, anchor: dict | None,
                              poc_contract: str | None,
                              src_file_name: str,
                              poc_function: str | None = None) -> dict | None:
    """Deterministically move ``patch.contract`` to the invariant owner.

    ``anchor_resolver`` already reduced the claim to ``single_anchor`` and named
    the owning contract. When the LLM still leaves ``patch.contract`` at the PoC
    test harness, this function moves it to the owning contract only when exactly
    one candidate function is declared by that contract: either a function root
    in the binding expressions, or (fallback) a function the PoC exploit test
    actually calls. The assert is then injected at the business function that
    owns the invariant instead of surfacing later as a forge ``compile_error``.
    Ambiguous or unknown cases are left untouched and reported instead of
    guessed.
    """
    if not (anchor and anchor.get('bindability') == 'single_anchor'):
        return None
    suggested = anchor.get('suggested_patch_contract')
    if not suggested or suggested == poc_contract:
        return None
    patch = binding.get('patch')
    if not isinstance(patch, dict):
        return None
    current = patch.get('contract')
    if current and current != poc_contract:
        return None

    owned_functions: set[str] = set()
    for entry in (binding.get('bindings') or {}).values():
        if not isinstance(entry, dict):
            continue
        expr = str(entry.get('solidity_expr') or '')
        for root in base_identifiers(expr):
            if suggested in function_owner(raw_source, root):
                owned_functions.add(root)
    if not owned_functions and poc_function:
        for call in _test_function_calls(raw_source, poc_function):
            if suggested in function_owner(raw_source, call):
                owned_functions.add(call)
    if len(owned_functions) != 1:
        return {'skipped': True, 'reason': 'ambiguous_owner_function',
                'candidates': sorted(owned_functions)}
    target_fn = next(iter(owned_functions))
    if not contract_has_function(raw_source, suggested, target_fn):
        return {'skipped': True, 'reason': 'function_not_in_owner_contract',
                'candidates': [target_fn]}

    patch['contract'] = suggested
    functions = patch.setdefault('functions', [])
    if functions:
        functions[0]['name'] = target_fn
        functions[0]['file'] = src_file_name
    else:
        functions.append({'name': target_fn, 'file': src_file_name})

    # The invariant is now injected inside ``suggested``, so any expression
    # that reached members through the PoC harness instance variable (for
    # example ``liquidRon.operator(msg.sender)``) must be re-anchored to the
    # bare member visible inside the owning contract (``operator(msg.sender)``).
    # Only rewrite when exactly one harness variable has the owning type; with
    # multiple instances the bare-name rewrite would be ambiguous.
    if poc_contract:
        instances = contract_instances(raw_source, poc_contract)
        matching = [name for name, typ in instances.items()
                    if typ == suggested]
        if len(matching) == 1:
            instance = matching[0]
            pattern = re.compile(r'\b' + re.escape(instance) + r'\.')
            for entry in (binding.get('bindings') or {}).values():
                if isinstance(entry, dict):
                    expr = str(entry.get('solidity_expr') or '')
                    entry['solidity_expr'] = pattern.sub('', expr)
    return {'migrated_to': suggested, 'function': target_fn}


def propose_binding(stage2_dir: Path, claim_id: str, src_dir: Path,
                    out_dir: Path, *, model: str = llm.MODEL,
                    hint: str | None = None,
                    existing: dict | None = None) -> dict:
    stage2 = load_stage2_run(stage2_dir)
    contract = claim_binding_contract(stage2['spec'], claim_id)
    required = {r['symbol'] for r in contract.get('symbols', []) if r.get('appears_in')}
    if not required:
        raise SpecError(f'claim {claim_id} has no bindable symbols')

    existing_bindings = None
    focus = None
    if isinstance(existing, dict) and isinstance(existing.get('bindings'), dict):
        existing_bindings = existing['bindings']
        focus = [sym for sym in required
                 if str(existing_bindings.get(sym, {}).get('solidity_expr') or '')
                 .strip() == 'UNBOUND']
        if not focus:
            return {
                'schema_version': PROPOSAL_SCHEMA,
                'claim_id': claim_id,
                'ok': True,
                'partial': False,
                'problems': [],
                'unbound': [],
                'binding': existing,
            }

    source_parts = []
    src_files = sorted(Path(src_dir).glob('*.sol'))
    for sol in src_files:
        source_parts.append(slice_flatten(sol.read_text()))
    source = '\n\n'.join(source_parts)
    src_file_name = src_files[0].name if src_files else 'Contract.sol'

    injection = None
    raw_source = ''
    if src_files:
        try:
            raw_source = '\n'.join(sol.read_text() for sol in src_files)
            injection = poc_test_function(raw_source)
        except (OSError, FileNotFoundError):
            injection = None

    try:
        from lib.binding_skeleton import build_skeleton
        skeleton = build_skeleton(stage2_dir, claim_id, src=src_dir)
        candidates = {
            sym: entry.get('candidates', [])
            for sym, entry in skeleton.get('bindings', {}).items()
        }
        observability = {
            sym: entry.get('observability', 'low')
            for sym, entry in skeleton.get('bindings', {}).items()
        }
    except Exception:
        candidates = {}
        observability = {}

    anchor = None
    try:
        from lib.anchor_resolver import resolve_anchors
        anchor = resolve_anchors(stage2_dir, claim_id, src_dir)
    except Exception:
        anchor = None

    symbols = _symbols_payload(contract, candidates, observability)
    analyze_required = required
    if focus is not None:
        analyze_required = set(focus)
        symbols = [row for row in symbols if row['symbol'] in analyze_required]

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    user = _user_prompt(claim_id, symbols, source, hint=hint, focus=focus)
    if anchor and anchor.get('suggested_patch_contract'):
        user += ('\n\nSUGGESTED_PATCH_CONTRACT: '
                 + anchor['suggested_patch_contract']
                 + ' (deterministic code-scope owner of the invariant '
                   'symbols; use it as patch.contract unless you have a '
                   'concrete, verifiable reason to choose another contract).')
    if injection:
        user += ('\n\nINJECTION_POINT_ON_DISK: contract ' + injection[0] +
                 ', test function ' + injection[1] +
                 '. Set probe.contract to this contract and '
                 'probe.exploit_test to this function exactly. Do NOT use this '
                 'contract for patch.contract when SUGGESTED_PATCH_CONTRACT is '
                 'present: patch.contract must be the business owner.')
        try:
            from lib.solidity_scan import contract_instances
            raw_source = '\n'.join(sol.read_text() for sol in src_files)
            instances = contract_instances(raw_source, injection[0])
        except Exception:
            instances = {}
        if instances:
            table = '\n'.join(
                f'  - {name} -> {typ}' for name, typ in sorted(instances.items()))
            user += (
                '\n\nCROSS_CONTRACT_INSTANCES: the PoC test harness declares '
                'these contract-typed state variables (instance name -> contract '
                'type):\n' + table +
                '\nWhen SUGGESTED_PATCH_CONTRACT is present, bind each symbol '
                'with a bare identifier declared inside that business contract '
                '(for example operator(msg.sender), not liquidRon.operator(...)). '
                'Only bind as <instance>.<member> (for example snft.owner()) '
                'when SUGGESTED_PATCH_CONTRACT is absent and the injection point '
                'is the harness itself.')
    user += ('\n\nSOURCE_FILE_ON_DISK: ' + src_file_name +
             '\nUse SOURCE_FILE_ON_DISK as patch.file and the file part of every '
             '"source" field, and set patch.functions[].file to SOURCE_FILE_ON_DISK.')
    raw = llm.chat_json(_SYSTEM, user, model=model)
    (out_dir / 'model-claim.json').write_text(
        json.dumps(raw, ensure_ascii=False, indent=2) + '\n')
    hard, unbound = _analyze(raw, claim_id, analyze_required)
    if not hard and unbound:
        safety_symbols = safety_symbols_for_claim(stage2['formal'], claim_id)
        precondition_symbols = precondition_symbols_for_claim(
            stage2['formal'], claim_id)
        bindings = raw.get('bindings') or {}
        remaining = []
        for sym in unbound:
            entry = bindings.get(sym)
            if (isinstance(entry, dict)
                    and entry.get('kind') == 'boolean_predicate'
                    and entry.get('checkpoint') == 'before'
                    and sym not in safety_symbols
                    and sym in precondition_symbols):
                entry['solidity_expr'] = 'true'
            else:
                remaining.append(sym)
        unbound = remaining
    if hard:
        return {
            'schema_version': PROPOSAL_SCHEMA,
            'claim_id': claim_id,
            'ok': False,
            'partial': False,
            'problems': hard,
            'unbound': unbound,
            'binding': None,
        }
    patch = raw.setdefault('patch', {})
    if existing_bindings is not None:
        merged = dict(existing_bindings)
        merged.update(raw.get('bindings') or {})
        raw['bindings'] = merged
    patch['file'] = src_file_name
    probe = raw.setdefault('probe', {})
    if injection:
        poc_contract, poc_function = injection
        probe['contract'] = poc_contract
        probe['exploit_test'] = poc_function
        proposed_contract = patch.get('contract')
        functions = patch.setdefault('functions', [])
        proposed_fn = functions[0].get('name') if functions else None
        valid_patch = (isinstance(proposed_contract, str) and proposed_contract
                       and isinstance(proposed_fn, str) and proposed_fn
                       and contract_has_function(raw_source, proposed_contract,
                                                 proposed_fn))
        if not valid_patch:
            patch['contract'] = poc_contract
            if not functions:
                functions.append({})
            functions[0]['name'] = poc_function
            functions[0]['file'] = src_file_name
        else:
            for fn in functions:
                if isinstance(fn, dict):
                    fn.setdefault('file', src_file_name)
    for fn in patch.get('functions') or []:
        if isinstance(fn, dict) and fn.get('file'):
            fn['file'] = src_file_name
    poc_contract = injection[0] if injection else None
    poc_function = injection[1] if injection else None
    migration = _migrate_patch_contract(raw_source, raw, anchor, poc_contract,
                                        src_file_name, poc_function)
    (out_dir / 'binding.proposal.json').write_text(
        json.dumps(raw, ensure_ascii=False, indent=2) + '\n')
    unbound_detail = {
        sym: {'observability': observability.get(sym, 'low'),
              'candidates': candidates.get(sym, [])}
        for sym in unbound
    }
    return {
        'schema_version': PROPOSAL_SCHEMA,
        'claim_id': claim_id,
        'ok': not bool(unbound),
        'partial': bool(unbound),
        'problems': [],
        'unbound': unbound,
        'unbound_detail': unbound_detail,
        'anchor': (anchor or None),
        'migration': (migration or None),
        'binding': raw,
    }
