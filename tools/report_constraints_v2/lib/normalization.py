#!/usr/bin/env python3
"""Explicit normalization boundary for stage-2 model output.

Why this module exists
----------------------
The lib layer aborts a run from 228 distinct places (`require(...)` plus direct
``raise``), and before this module **none of them was classified**.  An
unclassified boundary is not a boundary: it is a minefield where any single
shape slip silently discards an otherwise correct run.  The gold-v1 blind run
showed this directly -- `intuition_pause_escrow` died with
``invalid report-readiness fields`` although all four screening dimensions were
present, correctly judged, and backed by real evidence IDs.

The criterion
-------------
**Normalization may change how a fact is written down, never what is claimed.**

    NORMALIZE  a mechanical fix preserves every semantic assertion
               (position, naming, redundant telemetry, bookkeeping)
    WARN       the claim is unchanged; only our confidence in it changes
               (declared ambiguity / limitation / coverage gaps)
    REJECT     fixing it would change what the P/I/V assert about the report

Two layers, do not conflate them
--------------------------------
WARN is currently EMPTY *by design*.  The validators collected below only check
whether a declaration is **well-formed**; a malformed declaration list is a
shape error and stays REJECT.  The "declared uncertainty does not veto a claim"
semantics already live one layer up, in ``semantic_core.compile_bundle`` under
the ``signals`` verdict policy (S12).  Keeping them separate is what makes each
layer testable on its own.

Enforcement
-----------
``tests/test_normalization_boundary.py`` re-derives every rejection point from
the source with ``ast`` and fails if one is missing from ``BOUNDARY``.  The
boundary therefore cannot drift silently when someone adds a ``require(...)``.

No model call, no network, no artifact is read or written by this module.
"""
from __future__ import annotations

NORMALIZE = 'normalize'
REJECT = 'reject'
WARN = 'warn'

#: ``(message, mode, note?)``.  Matched by exact equality first, then by prefix,
#: so dynamic messages such as ``f'unknown evidence ID {x}'`` (which the guard
#: test sees as the literal prefix ``'unknown evidence ID '``) also resolve.
#: Order matters only for prefix matches: NORMALIZE entries come first.
BOUNDARY = (
    # ---- NORMALIZE: a mechanical fix preserves every semantic assertion ----
    ('invalid report-readiness fields', NORMALIZE,
     'readiness telemetry nested one level too deep; hoisted by normalize_readiness()'),
    ('missing report-readiness summary', NORMALIZE,
     'readiness telemetry nested one level too deep; hoisted by normalize_readiness()'),

    # ---- REJECT: fixing these would change what the P/I/V claim ----
    ('P predicate symbol not grounded by its own source', REJECT),
    ('P predicate symbol not grounded by selected preconditions', REJECT),
    ('P term source not selected', REJECT),
    ('P terms must cover selected preconditions exactly once', REJECT),
    ('attack step must reference action', REJECT),
    ('bounded relation type/unit mismatch', REJECT),
    ('catalog does not match this report', REJECT),
    ('classified relation has no core observables', REJECT),
    ('classified relation uses unknown core observable', REJECT),
    ('conservation type/unit mismatch', REJECT),
    ('core relation observable has unknown source', REJECT),
    ('core relation observables lack intent/impact grounding', REJECT),
    ('correspondence type/unit mismatch', REJECT),
    ('coverage lacks effect expression/source', REJECT),
    ('derived definition target must be integer symbol', REJECT),
    ('derived definition type/unit mismatch', REJECT),
    ('derived definitions may reference base symbols only', REJECT),
    ('distinct P sources reuse identical predicate', REJECT),
    ('duplicate ', REJECT),
    ('duplicate attack step', REJECT),
    ('duplicate derived definition', REJECT),
    ('effect source outside claim', REJECT),
    ('empty conjunction', REJECT),
    ('empty disjunction', REJECT),
    ('empty report description/impact after filtering', REJECT),
    ('evidence absent from input', REJECT),
    ('expanded relation template mismatch', REJECT),
    ('fixed relation template mismatch', REJECT),
    ('formal property lacks evidence/derivation', REJECT),
    ('formal property missing source', REJECT),
    ('formula path absent', REJECT),
    ('impact context source not selected', REJECT),
    ('impact context symbol not grounded by its own source', REJECT),
    ('impact coverage missing or duplicate', REJECT),
    ('impact qualifier missing from formal plan: ', REJECT),
    ('invalid ', REJECT),
    ('invalid AST fields', REJECT),
    ('invalid ambiguities', REJECT),
    ('invalid arity', REJECT),
    ('invalid attack steps', REJECT),
    ('invalid authorization guard pattern', REJECT),
    ('invalid authorization pattern', REJECT),
    ('invalid bounded relation pattern', REJECT),
    ('invalid caveat list', REJECT),
    ('invalid claim impacts', REJECT),
    ('invalid claim modality', REJECT),
    ('invalid classified relation pattern', REJECT),
    ('invalid comparison binding', REJECT),
    ('invalid comparison types/units', REJECT),
    ('invalid compound predicate', REJECT),
    ('invalid condition pattern', REJECT),
    ('invalid conservation pattern', REJECT),
    ('invalid constant', REJECT),
    ('invalid correspondence pattern', REJECT),
    ('invalid coverage status', REJECT),
    ('invalid derived definition', REJECT),
    ('invalid derived definition sources', REJECT),
    ('invalid derived definitions', REJECT),
    ('invalid divisibility binding', REJECT),
    ('invalid divisibility type/unit', REJECT),
    ('invalid entity', REJECT),
    ('invalid exact power-of-two operand', REJECT),
    ('invalid formal plan', REJECT),
    ('invalid formula path', REJECT),
    ('invalid formula sources', REJECT),
    ('invalid impact context term', REJECT),
    ('invalid impact context terms', REJECT),
    ('invalid impact qualifier types', REJECT),
    ('invalid kind/modality', REJECT),
    ('invalid limitations', REJECT),
    ('invalid monotonicity pattern', REJECT),
    ('invalid plan P term', REJECT),
    ('invalid plan P terms', REJECT),
    ('invalid plan caveats', REJECT),
    ('invalid plan impact IDs', REJECT),
    ('invalid plan intent ID', REJECT),
    ('invalid plan precondition IDs', REJECT),
    ('invalid plan symbol', REJECT),
    ('invalid plan symbol entities', REJECT),
    ('invalid plan symbol sort', REJECT),
    ('invalid plan symbol sources', REJECT),
    ('invalid plan symbols', REJECT),
    ('invalid predicate binding', REJECT),
    ('invalid predicate operand', REJECT),
    ('invalid preservation pattern', REJECT),
    ('invalid property explanation', REJECT),
    ('invalid proportional relation pattern', REJECT),
    ('invalid quantity binding', REJECT),
    ('invalid quantity expression', REJECT),
    ('invalid quantity expression types', REJECT),
    ('invalid quantity relation', REJECT),
    ('invalid quantity relation types/units', REJECT),
    ('invalid relation obligation pattern', REJECT),
    ('invalid report-readiness decision', REJECT),
    ('invalid report-readiness dimension fields', REJECT),
    ('invalid report-readiness dimension status', REJECT),
    ('invalid report-readiness dimensions', REJECT),
    ('invalid report-readiness missing_dimensions', REJECT),
    ('invalid required effect pattern', REJECT),
    ('invalid scope', REJECT),
    ('invalid sort', REJECT),
    ('invalid structured unresolved blocking flag', REJECT),
    ('invalid structured unresolved category', REJECT),
    ('invalid structured unresolved item', REJECT),
    ('invalid structured unresolved list', REJECT),
    ('invalid structured unresolved sources', REJECT),
    ('invalid subformula sources', REJECT),
    ('invalid symbol count', REJECT),
    ('invalid symbols', REJECT),
    ('invalid temporal order pattern', REJECT),
    ('invalid truth binding', REJECT),
    ('invalid/deep AST', REJECT),
    ('invalid/duplicate evidence IDs', REJECT),
    ('invalid/reserved symbol name', REJECT),
    ('missing claim scope', REJECT),
    ('missing coverage reason', REJECT),
    ('missing evidence quotes', REJECT),
    ('missing plan quantity unit', REJECT),
    ('missing plan symbol semantics', REJECT),
    ('missing quantity unit', REJECT),
    ('missing report-readiness dimension must not cite evidence', REJECT),
    ('missing report-readiness reason', REJECT),
    ('missing scope', REJECT),
    ('missing statement text', REJECT),
    ('missing structured unresolved description', REJECT),
    ('missing symbol semantics', REJECT),
    ('model must return IDs, not quotes', REJECT),
    ('monotonicity type/unit mismatch', REJECT),
    ('non-quantity plan unit', REJECT),
    ('non-quantity unit', REJECT),
    ('null property has formula paths', REJECT),
    ('plan P source role mismatch', REJECT),
    ('plan symbol lacks evidence', REJECT),
    ('potential impact upgraded to asserted effect', REJECT),
    ('predicate lacks source mapping', REJECT),
    ('present report-readiness dimension lacks evidence', REJECT),
    ('property evidence absent from report', REJECT),
    ('property is not Boolean', REJECT),
    ('property quote not linked to source', REJECT),
    ('property source role mismatch: ', REJECT),
    ('proportional relation type/unit mismatch', REJECT),
    ('quantity expression requires integer', REJECT),
    ('recursive derived definition', REJECT),
    ('referenced derived symbol lacks definition', REJECT),
    ('relation alignment requires plan schema v3', REJECT),
    ('relation class and pattern mismatch', REJECT),
    ('relation repeats cancellable observable on both sides', REJECT),
    ('report JSON must be an object', REJECT),
    ('report JSON requires a nonempty body string', REJECT),
    ('report JSON title must be a nonempty string when present', REJECT),
    ('report-readiness decision/dimensions mismatch', REJECT),
    ('stage-2 DeepSeek API key is missing or malformed', REJECT),
    ('stage-2 DeepSeek key file missing; see config/stage2_deepseek.local.env.example', REJECT),
    ('stage-2 DeepSeek key file must be private (chmod 600)', REJECT),
    ('state preservation type/unit mismatch', REJECT),
    ('structured unresolved requires plan schema v2', REJECT),
    ('symbol evidence absent from report', REJECT),
    ('synthesized property is not Boolean', REJECT),
    ('temporal order type/unit mismatch', REJECT),
    ('too many claims', REJECT),
    ('tool use/model error; rejected', REJECT),
    ('trivial self-comparison predicate', REJECT),
    ('truth binding requires bool symbol', REJECT),
    ('type/unit mismatch', REJECT),
    ('unexpected claim fields', REJECT),
    ('unexpected coverage fields', REJECT),
    ('unexpected elements fields', REJECT),
    ('unexpected entity fields', REJECT),
    ('unexpected formal plan fields', REJECT),
    ('unexpected formalization fields', REJECT),
    ('unexpected formula source fields', REJECT),
    ('unexpected observable fields', REJECT),
    ('unexpected properties', REJECT),
    ('unexpected property fields', REJECT),
    ('unexpected statement fields', REJECT),
    ('unexpected symbol fields', REJECT),
    ('unknown ID elements schema', REJECT),
    ('unknown ID formalization schema', REJECT),
    ('unknown comparison symbol', REJECT),
    ('unknown correspondence symbol', REJECT),
    ('unknown elements schema', REJECT),
    ('unknown entity reference', REJECT),
    ('unknown evidence ID', REJECT),
    ('unknown formal plan schema', REJECT),
    ('unknown formalization schema', REJECT),
    ('unknown monotonicity symbol', REJECT),
    ('unknown observable entity', REJECT),
    ('unknown or duplicate report-readiness evidence ID', REJECT),
    ('unknown predicate symbol', REJECT),
    ('unknown preservation symbol', REJECT),
    ('unknown property source', REJECT),
    ('unknown relation class', REJECT),
    ('unknown report input policy version', REJECT),
    ('unknown report-readiness schema', REJECT),
    ('unknown synthesis pattern', REJECT),
    ('unknown temporal order symbol', REJECT),
    ('unsupported multiplication types', REJECT),
    ('unsupported official DeepSeek model identifier', REJECT),
    ('unsupported operator/types', REJECT),
    ('unsupported proxy : use "environment", "direct", or an http(s):// URL (urllib has no SOCKS support)', REJECT),

    # ---- transport failures: not a semantic boundary, still listed for coverage ----
    ('DeepSeek HTTP ; response body not saved', REJECT),
    ('DeepSeek JSON response must be an object', REJECT),
    ('DeepSeek network failure; details not saved', REJECT),
    ('DeepSeek response content missing', REJECT),
    ('DeepSeek response did not finish normally', REJECT),
    ('DeepSeek response envelope invalid; raw body not saved', REJECT),
    ('DeepSeek response exceeds local size limit', REJECT),
    ('model runtime exit ; category=; no fallback', REJECT),
)


def exact_entry_for(message):
    """The entry whose declared text equals this message exactly, or None.

    The coverage guard must use THIS, not ``entry_for``: prefix fallback would
    let a truncated entry keep "covering" the message it was meant to declare,
    which is how a boundary silently loses a point.
    """
    for entry in BOUNDARY:
        if entry[0] == message:
            return entry
    return None


def entry_for(message):
    """Entry governing this message: exact first, then declared-prefix fallback.

    The prefix pass exists for dynamic messages: an f-string such as
    ``f'unknown evidence ID {x}'`` is declared (and statically discovered) as the
    literal prefix ``'unknown evidence ID '``, which the runtime message extends.
    """
    entry = exact_entry_for(message)
    if entry is not None:
        return entry
    for entry in BOUNDARY:
        if message.startswith(entry[0]):
            return entry
    return None


def classify(message):
    """Mode for this rejection message; unlisted messages default to REJECT.

    The default is deliberately the historical behaviour, so an unclassified
    point can never silently start normalizing.
    """
    entry = entry_for(message)
    return entry[1] if entry else REJECT


def normalize_readiness(candidate):
    """Hoist readiness telemetry the model nested one level too deep.

    Observed on a real run: the response carried ``missing_dimensions`` and
    ``summary`` *inside* ``dimensions`` instead of beside it.  Every dimension
    was correct and ``decision`` was right, so this is a pure positional slip --
    moving the two keys up changes nothing the response asserts.

    Returns ``(candidate, changes)``; ``changes`` is empty when nothing applied.
    """
    if not isinstance(candidate, dict):
        return candidate, []
    dimensions = candidate.get('dimensions')
    if not isinstance(dimensions, dict):
        return candidate, []
    hoisted = {key: dimensions[key] for key in ('missing_dimensions', 'summary')
               if key not in candidate and key in dimensions}
    if not hoisted:
        return candidate, []
    normalized = {**candidate, **hoisted,
                  'dimensions': {key: value for key, value in dimensions.items()
                                 if key not in hoisted}}
    return normalized, [f'hoisted {key} out of dimensions' for key in hoisted]
