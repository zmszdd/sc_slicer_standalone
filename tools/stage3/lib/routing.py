"""Deterministic claim-level verification routing for the stage-2 -> stage-3 handoff.

Stage 2 emits a report-grounded safety invariant (I) per claim; stage 3 must
decide *how* that invariant can be dynamically verified. Two dimensions decide
the route:

* bindability  -- from ``lib.anchor_resolver``: do the I/V symbols live in one
  contract (``single_anchor``), at file scope (``file_level``), across several
  contracts (``multi_contract``), or nowhere observable (``no_anchor``)?
* observability -- per symbol: does the code actually compute the value the
  report claims, or is it a should-be semantic the code never materializes?

The routes:

* ``auto_assert``                     -- single_anchor/file_level. The existing
  ``assert(I)`` injection + Foundry differential works.
* ``reference_patch_cross_contract``  -- multi_contract. A single injection
  point cannot see all anchors; needs an M1 reference patch (``case/patched/``).
* ``reference_patch_should_be``       -- no_anchor. The invariant has no
  observable code anchor (should-be semantic); only a reference patch can
  express it, never ``assert(I)``.
* ``unbound_feedback``                -- reserved for symbols whose candidate
  analysis yields no declared identifier and no low-observability candidates;
  routed back to stage 2 for refinement.

``auto_verifiable`` is True only for ``auto_assert``: every other route is
excluded from the automatic reproduction denominator so that the measured
recall decomposes by route instead of hiding multi_contract/should-be losses
inside one opaque recall number.

Routing is *advisory*. The bindability class is a conservative upper bound over
the code anchors of the report symbols; it does NOT decide whether a claim can
be injected as ``assert(I)``. That decision belongs to the actual binding's
expressibility lint (``lib.expressibility``): a claim whose symbols span two
contracts can still bind to one injection point and reproduce. Callers must
gate the reference-patch path on the binding lint, never on ``route`` alone.
"""
from __future__ import annotations

from pathlib import Path

from lib.anchor_resolver import resolve_anchors

ROUTING_SCHEMA = 'stage3-routing/1'

AUTO_ASSERT = 'auto_assert'
REFERENCE_PATCH_CROSS_CONTRACT = 'reference_patch_cross_contract'
REFERENCE_PATCH_SHOULD_BE = 'reference_patch_should_be'
UNBOUND_FEEDBACK = 'unbound_feedback'

_REQUIRES_REFERENCE_PATCH = {
    REFERENCE_PATCH_CROSS_CONTRACT,
    REFERENCE_PATCH_SHOULD_BE,
}


def _route_for_anchors(anchors: dict) -> tuple[str, str, bool]:
    """Reduce an anchor-resolver record to (route, reason, auto_verifiable)."""
    bindability = anchors.get('bindability')
    if bindability in ('single_anchor', 'file_level'):
        return AUTO_ASSERT, f'{bindability} injectable', True
    if bindability == 'multi_contract':
        return (REFERENCE_PATCH_CROSS_CONTRACT,
                'safety anchors span multiple contracts; '
                'assert(I) at one injection point cannot observe them all',
                False)
    # no_anchor: the invariant has no observable code anchor.
    return (REFERENCE_PATCH_SHOULD_BE,
            'no observable code anchor for the safety/effect symbols; '
            'the invariant is a should-be semantic that only a reference '
            'patch can express',
            False)


def classify_route(stage2_dir: Path, claim_id: str, src: Path,
                   candidates_fn=None) -> dict:
    """Classify one claim's verification route deterministically.

    Returns a dict with ``route``, ``auto_verifiable`` and
    ``requires_reference_patch`` plus the underlying anchor record. Raises the
    same errors as ``resolve_anchors`` when the stage-2 run or sources are
    missing; callers that want legacy fallback should catch those themselves.
    """
    anchors = resolve_anchors(stage2_dir, claim_id, src,
                              candidates_fn=candidates_fn)
    route, reason, auto_verifiable = _route_for_anchors(anchors)
    return {
        'schema_version': ROUTING_SCHEMA,
        'claim_id': claim_id,
        'bindability': anchors['bindability'],
        'route': route,
        'reason': reason,
        'auto_verifiable': auto_verifiable,
        'requires_reference_patch': route in _REQUIRES_REFERENCE_PATCH,
        'suggested_patch_contract': anchors.get('suggested_patch_contract'),
        'anchor': anchors,
    }
