"""Deterministic stage-2 -> stage-3 code-anchor resolution.

The stage-2 -> stage-3 handoff is lossy by construction: stage 2 only reads the
report, never the code, so its P/I/V symbols are report-grounded abstractions
(``c331795dd_time_window_bound_to_owner_signature``) that stage 3 must map to
concrete Solidity identifiers and an injection contract. That mapping has been
delegated to the LLM as a free-form guess, which is the root cause of the
ambiguous-anchor (25.4%), cross-contract-reference and unbound-symbol failures
that cap end-to-end reproduction.

This module replaces the guess with deterministic source-scope analysis: for a
claim it (1) scores candidate code identifiers per symbol by token overlap with
the symbol's entity/meaning hints, (2) resolves the *owning contract* of every
candidate using ``function_owner`` / ``state_var_owner``, and (3) reduces the
safety/effect symbols to one bindability class:

* ``single_anchor``   -- every anchoring symbol's owners agree on one contract.
* ``file_level``      -- anchors are file-level functions/constants (visible
                         everywhere, so the PoC injection point works).
* ``multi_contract``  -- anchors span multiple contracts; an assert at one
                         injection point cannot see them all.
* ``no_anchor``       -- no token overlap to any declared identifier; the
                         invariant has no observable code anchor.

The class is a deterministic upper bound on dynamic expressibility: only
``single_anchor`` / ``file_level`` can become an ``assert(I)`` patch.
``multi_contract`` needs a reference patch (M1); ``no_anchor`` is
``not_dynamically_expressible``.
"""
from __future__ import annotations

from pathlib import Path

from lib.spec_loader import SpecError, claim_binding_contract, load_stage2_run
from lib.solidity_scan import (scan_src, function_owner, state_var_owner,
                              poc_test_contract, contract_decl_kind)

ANCHOR_SCHEMA = 'stage3-anchor-resolver/1'

# Role symbols used to pick the injection point. Safety (I) is the invariant we
# assert; when a claim has no I symbols we fall back to the effect (V) symbols,
# which are what the PoC actually observes.
_ANCHOR_ROLES = ('I', 'V')


def _read_source(src: Path) -> str:
    if src.is_file():
        return src.read_text()
    parts = []
    for sol in sorted(src.glob('**/*.sol')):
        try:
            parts.append(sol.read_text())
        except OSError:
            continue
    return '\n'.join(parts)


def _identifier_owners(raw: str, identifier: str, index) -> set:
    """Owning contracts for one identifier, ``None`` marking file-level.

    Solidity resolves a bare identifier to a state variable before a function,
    so when the same name exists as both (for example ``address public escrow``
    in one contract and ``function escrow()`` in another), the function owner
    is noise and must not be merged into the anchor set. State-variable owners
    win whenever the identifier is declared as a state variable anywhere.

    The raw owner set is returned because a file-level anchor (``{None}``) must
    be distinguishable from a contract-scoped anchor (``{Contract}``) when
    choosing the injection point.
    """
    if identifier in index.all_state_vars():
        return state_var_owner(raw, identifier)
    functions = set().union(*(set(f.functions) for f in index.files.values()))
    if identifier in functions:
        return function_owner(raw, identifier)
    return set()


def _strong_anchors(raw: str, candidates: list[str], index) -> list[dict]:
    """Keep only candidates that are declared functions/state vars.

    ``_candidate_analysis`` scores by fuzzy token overlap, so it also returns
    contract names, custom-error names and parameter names that have no stable
    owning contract. Those are dropped here; the remaining candidates carry a
    non-empty owner set (possibly ``{None}`` for file-level declarations).
    """
    functions = set().union(*(set(f.functions) for f in index.files.values()))
    state_vars = index.all_state_vars()
    out: list[dict] = []
    for cand in candidates:
        if cand not in functions and cand not in state_vars:
            continue
        owners = _identifier_owners(raw, cand, index)
        if owners:
            out.append({'identifier': cand, 'owners': owners})
    return out


def resolve_anchors(stage2_dir: Path, claim_id: str, src: Path,
                    candidates_fn=None) -> dict:
    """Resolve the bindability class + suggested injection contract for a claim.

    ``candidates_fn`` defaults to ``binding_skeleton._candidate_analysis`` and
    may be swapped in tests to avoid importing the LLM-free skeleton module.
    """
    if candidates_fn is None:
        from lib.binding_skeleton import _candidate_analysis
        candidates_fn = _candidate_analysis

    stage2 = load_stage2_run(stage2_dir)
    contract = claim_binding_contract(stage2['spec'], claim_id)
    symbols = [row for row in contract.get('symbols', []) if row.get('appears_in')]

    raw = _read_source(src)
    index = scan_src(src)
    declared = index.all_declared()
    # The default injection point is the PoC test harness (the last contract
    # that declares a ``test_*`` function). When a candidate is owned by that
    # harness it is the correct anchor for an assert, even if the same name is
    # also declared as a state variable in a business contract.
    poc = poc_test_contract(raw)

    symbol_rows = []
    for sym in symbols:
        candidates, observability = candidates_fn(sym, declared)
        anchors = _strong_anchors(raw, candidates, index)
        # A PoC ``test_*`` function is a probe, never an invariant anchor:
        # choosing it pulls the injection point into the test harness even
        # though the invariant lives in a business contract.
        anchors = [a for a in anchors
                   if not a['identifier'].startswith('test_')]
        if anchors:
            # Prefer a business anchor over one owned only by the PoC test
            # harness. Name collisions between a business state variable and a
            # harness-local identifier must resolve to the business contract.
            business = [a for a in anchors
                        if not (poc and poc in a['owners']
                                and len(a['owners']) == 1)]
            anchor = business[0] if business else anchors[0]
        else:
            anchor = None
        contract_owners = ({o for o in anchor['owners'] if o is not None}
                           if anchor else set())
        file_level = bool(anchor and None in anchor['owners'])
        symbol_rows.append({
            'symbol': sym.get('symbol'),
            'appears_in': sym.get('appears_in') or [],
            'observability': observability,
            'candidates': candidates,
            'anchors': [
                {'identifier': a['identifier'],
                 'owner_contracts': sorted(o for o in a['owners'] if o is not None),
                 'file_level': None in a['owners']}
                for a in anchors
            ],
            'anchor': ({'identifier': anchor['identifier'],
                        'owner_contracts': sorted(contract_owners),
                        'file_level': file_level} if anchor else None),
        })

    anchor_symbols = [
        row for row in symbol_rows
        if any(role in (row['appears_in'] or []) for role in _ANCHOR_ROLES)
    ] or symbol_rows

    # Any anchoring symbol with no declared function/state-var anchor ->
    # nothing to observe at any injection point.
    if any(row['anchor'] is None for row in anchor_symbols):
        bindability = 'no_anchor'
        suggested = None
    else:
        owner_sets = [set(row['anchor']['owner_contracts'])
                      for row in anchor_symbols]
        non_empty = [s for s in owner_sets if s]
        if not non_empty:
            bindability = 'file_level'
            suggested = None
        else:
            # An interface and its implementation declare the same function:
            # they are one logical owner, not a cross-contract reference. Use
            # the intersection of every anchor's owner set; pick the most
            # concrete contract when several share the anchor identifier.
            common = set(non_empty[0])
            for owners in non_empty[1:]:
                common &= owners
            if common:
                def _kind_rank(contract: str) -> int:
                    kind = contract_decl_kind(raw, contract)
                    return {'contract': 0, 'abstract contract': 1,
                            'library': 2, 'interface': 3}.get(kind, 4)
                bindability = 'single_anchor'
                suggested = sorted(common, key=_kind_rank)[0]
            else:
                bindability = 'multi_contract'
                suggested = None

    dynamically_expressible = bindability in ('single_anchor', 'file_level')
    return {
        'schema_version': ANCHOR_SCHEMA,
        'claim_id': claim_id,
        'bindability': bindability,
        'dynamically_expressible': dynamically_expressible,
        'suggested_patch_contract': suggested,
        'anchor_roles': list(_ANCHOR_ROLES),
        'symbols': symbol_rows,
    }
