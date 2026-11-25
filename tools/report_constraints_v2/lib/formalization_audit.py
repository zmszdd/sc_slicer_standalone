"""Deterministic Stage-2 formalization contract.

Stage 2 already validates evidence grounding and symbolic feasibility.  This
module adds the missing handoff contract: every P/I/V symbol must carry a
checkpoint and observable type, I and V must be independently observable, and
claims that cannot be safely auto-asserted are routed before Stage 3.

The audit is intentionally descriptive and deterministic.  It does not call a
model and does not rewrite report claims.
"""
from __future__ import annotations

import re

from lib.piv_contract import PIV_PROPERTY_NAMES

SCHEMA_VERSION = 'stage2-formalization-contract/2'

_QUALITATIVE_IMPACT_RE = re.compile(
    r'(?i)\b(bloat\w*|spam\w*|accumulat\w*|remain\w*|persist\w*|'
    r'blocked|unavailable|revert\w*|fail\w*)\b')


def _vars(node) -> set[str]:
    if not isinstance(node, dict):
        return set()
    if 'var' in node:
        return {node['var']}
    found: set[str] = set()
    for value in node.values():
        if isinstance(value, dict):
            found |= _vars(value)
        elif isinstance(value, list):
            for item in value:
                found |= _vars(item)
    return found


def _has_numeric_comparison(node) -> bool:
    if not isinstance(node, dict):
        return False
    if node.get('op') in {'lt', 'le', 'gt', 'ge'}:
        return True
    for value in node.values():
        if isinstance(value, dict) and _has_numeric_comparison(value):
            return True
        if isinstance(value, list) and any(
                isinstance(item, dict) and _has_numeric_comparison(item)
                for item in value):
            return True
    return False


def _const(node):
    if isinstance(node, dict) and set(node) == {'const'}:
        return node.get('const')
    return None


def _negation_of(left, right) -> bool:
    return (isinstance(left, dict) and left.get('op') == 'not' and
            isinstance(left.get('args'), list) and len(left['args']) == 1 and
            left['args'][0] == right) or (
                isinstance(right, dict) and right.get('op') == 'not' and
                isinstance(right.get('args'), list) and len(right['args']) == 1 and
                right['args'][0] == left)


def _opposite_vars(left: set[str], right: set[str]) -> bool:
    """Conservative complement check.

    Two claims over the same symbols are only considered independent when they
    have different expressions.  A bare polarity flip still needs a separate
    observable in Stage 3, so it is flagged as a warning rather than accepted
    as a full independent witness.
    """
    return bool(left) and left == right


def _contains(node, target) -> bool:
    if node == target:
        return True
    if not isinstance(node, dict):
        return False
    for key, value in node.items():
        if key in {'var', 'const'}:
            continue
        if isinstance(value, dict) and _contains(value, target):
            return True
        if isinstance(value, list) and any(
                isinstance(item, dict) and _contains(item, target)
                for item in value):
            return True
    return False


_OPPOSITE_OPS = {
    'lt': 'ge', 'ge': 'lt', 'le': 'gt', 'gt': 'le', 'eq': 'neq', 'neq': 'eq',
}


def _negates(node, target) -> bool:
    if (isinstance(target, dict) and target.get('op') == 'not'
            and len(target.get('args') or []) == 1
            and node == target['args'][0]):
        return True
    if (isinstance(node, dict) and node.get('op') == 'not'
            and len(node.get('args') or []) == 1
            and node['args'][0] == target):
        return True
    if not isinstance(node, dict) or not isinstance(target, dict):
        return False
    if (node.get('op') in _OPPOSITE_OPS
            and node.get('op') == _OPPOSITE_OPS.get(target.get('op'))
            and node.get('args') == target.get('args')):
        return True
    if node.get('op') == 'and':
        return any(_negates(child, target) for child in node.get('args') or [])
    return False


def _effect_is_implication_counterexample(i_expr, v_expr) -> bool:
    """True for ``P1 => (P2 => C)`` / ``P1 && P2 && !C`` witnesses too."""
    antecedents = []
    node = i_expr
    consequents = []
    while isinstance(node, dict) and node.get('op') == 'implies':
        args = node.get('args') or []
        if len(args) != 2:
            return False
        antecedents.append(args[0])
        node = args[1]
        consequents.append(node)
    if not antecedents:
        return False
    if not all(_contains(v_expr, antecedent) for antecedent in antecedents):
        return False
    return any(_negates(v_expr, consequent) for consequent in consequents)


def _effect_is_complement(i_expr, v_expr) -> bool:
    """Backward-compatible name for the implication-counterexample check."""
    return _effect_is_implication_counterexample(i_expr, v_expr)


def _effect_is_polarity_only(i_expr, v_expr) -> bool:
    """Reject only an exact polarity flip, not a conjunction with a witness.

    A V such as ``P && !I && independent_hazard`` contains the negation of I
    but is a legitimate effect witness.  Treating any nested negation as
    ``polarity only`` falsely routes this common shape to review.
    """
    if i_expr is None or v_expr is None:
        return False
    if _negation_of(i_expr, v_expr):
        return True
    if (isinstance(i_expr, dict) and isinstance(v_expr, dict)
            and i_expr.get('op') in _OPPOSITE_OPS
            and v_expr.get('op') == _OPPOSITE_OPS.get(i_expr.get('op'))
            and i_expr.get('args') == v_expr.get('args')):
        return True
    if _vars(v_expr) - _vars(i_expr):
        return False
    return _negates(i_expr, v_expr) or _negates(v_expr, i_expr)


def _effect_restates_invariant(i_expr, v_expr) -> bool:
    if i_expr is None or v_expr is None:
        return False
    if _vars(v_expr) - _vars(i_expr):
        return False
    return _contains(v_expr, i_expr) or _contains(i_expr, v_expr)


def _symbol_meta(formal: dict, observability: dict | None, symbol: str) -> dict:
    declared = (formal.get('symbols') or {}).get(symbol) or {}
    extra = ((observability or {}).get('symbols') or {}).get(symbol) or {}
    return {**declared, **extra}


def _observability_active(observability: dict | None) -> bool:
    return (isinstance(observability, dict)
            and observability.get('contract_present') is not False)


def _checkpoint(meta: dict) -> str:
    return str(meta.get('checkpoint') or '').strip().lower()


def _checkpoint_layer(value: str) -> str:
    """Coarse checkpoint layer used for transition checks.

    Report checkpoints are descriptive (``before init call`` / ``after init
    call``); stage-3 bindings use only before/after/input.  The audit compares
    layers, not exact labels, so a transition is visible even when the report
    uses prose.
    """
    if not value:
        return ''
    if any(marker in value for marker in (
            'before', 'entry', 'input', 'at ', 'during', 'invocation',
            'triggered', 'pre-')):
        return 'before'
    if any(marker in value for marker in (
            'after', 'completion', 'post', 'completed', 'occurred',
            'attempt', 'output', 'result')):
        return 'after'
    return 'other'


def _always_true(node) -> bool:
    """Conservative structural tautology check.

    This deliberately proves only identities such as ``x == x`` and
    ``A -> A``.  It does not guess whether a report predicate happens to hold
    on every code path; that requires the Stage-3 code-fact audit.
    """
    if not isinstance(node, dict):
        return False
    if _const(node) is True:
        return True
    op = node.get('op')
    args = node.get('args') or []
    if op in {'eq', 'le', 'ge'} and len(args) == 2 and args[0] == args[1]:
        return True
    if op == 'implies' and len(args) == 2 and args[0] == args[1]:
        return True
    if op == 'or' and len(args) == 2 and _negation_of(args[0], args[1]):
        return True
    if op == 'and' and args and all(_always_true(arg) for arg in args):
        return True
    if op == 'not' and len(args) == 1 and _always_false(args[0]):
        return True
    if op == 'implies' and len(args) == 2:
        return _always_false(args[0]) or _always_true(args[1])
    return False


def _always_false(node) -> bool:
    if not isinstance(node, dict):
        return False
    if _const(node) is False:
        return True
    op = node.get('op')
    args = node.get('args') or []
    if op in {'neq', 'lt', 'gt'} and len(args) == 2 and args[0] == args[1]:
        return True
    if op == 'not' and len(args) == 1 and _always_true(args[0]):
        return True
    if op == 'and' and any(_always_false(arg) for arg in args):
        return True
    if op == 'or' and args and all(_always_false(arg) for arg in args):
        return True
    return False


def _semantic_profile(formal: dict, claim: dict,
                      observability: dict | None) -> dict:
    properties = claim.get('properties') or {}
    i_expr = (properties.get('safety') or {}).get('expression')
    v_expr = (properties.get('effects') or {}).get('expression')
    p_expr = (properties.get('preconditions') or {}).get('expression')
    i_symbols = _vars(i_expr)
    v_symbols = _vars(v_expr)
    p_symbols = _vars(p_expr)
    i_layers = {
        _checkpoint_layer(_checkpoint(_symbol_meta(
            formal, observability, symbol)))
        for symbol in i_symbols
        if _checkpoint(_symbol_meta(formal, observability, symbol))
    }
    v_layers = {
        _checkpoint_layer(_checkpoint(_symbol_meta(
            formal, observability, symbol)))
        for symbol in v_symbols
        if _checkpoint(_symbol_meta(formal, observability, symbol))
    }
    transition = bool(
        'before' in (i_layers | v_layers)
        and 'after' in (i_layers | v_layers))
    if _always_true(i_expr):
        bucket = 'tautological'
    elif _always_false(i_expr):
        bucket = 'contradictory'
    elif i_expr is not None and i_expr == v_expr:
        bucket = 'effect_restatement'
    elif p_expr is not None and i_expr == p_expr:
        bucket = 'precondition_restatement'
    elif i_symbols and i_symbols <= p_symbols:
        bucket = 'precondition_only'
    elif transition:
        bucket = 'transition'
    elif i_layers and len(i_layers) == 1:
        bucket = 'snapshot_only'
    else:
        bucket = 'unclassified'
    code_fact_symbols = sorted(
        symbol for symbol in i_symbols | v_symbols
        if _symbol_meta(formal, observability, symbol).get('observable_kind')
        and not any(_symbol_meta(formal, observability, symbol).get(key)
                    for key in ('source_entity', 'code_fact', 'mutation_site')))
    numeric_i = _has_numeric_comparison(i_expr)
    qualitative_impact_shadow = sorted(
        symbol for symbol in v_symbols - i_symbols
        if numeric_i
        and str(_symbol_meta(formal, observability, symbol).get('sort') or '').lower()
        == 'bool'
        and _QUALITATIVE_IMPACT_RE.search(
            symbol + ' ' + str(_symbol_meta(
                formal, observability, symbol).get('meaning') or '')))
    return {
        'bucket': bucket,
        'i_shape': (i_expr.get('op') if isinstance(i_expr, dict) else None),
        'v_shape': (v_expr.get('op') if isinstance(v_expr, dict) else None),
        'applicability_condition': bool(
            isinstance(i_expr, dict) and i_expr.get('op') == 'implies'),
        'has_before_after': transition,
        'i_layers': sorted(i_layers),
        'v_layers': sorted(v_layers),
        'shared_layers': sorted(i_layers & v_layers),
        'p_symbols': sorted(p_symbols),
        'i_symbols': sorted(i_symbols),
        'v_symbols': sorted(v_symbols),
        'requires_code_fact': code_fact_symbols,
        'qualitative_impact_shadow': qualitative_impact_shadow,
    }


def _add(problems: list[dict], code: str, severity: str, message: str,
         symbol: str | None = None):
    row = {'code': code, 'severity': severity, 'message': message}
    if symbol:
        row['symbol'] = symbol
    problems.append(row)


def audit_claim(formal: dict, claim: dict,
                observability: dict | None = None) -> dict:
    """Audit one claim and return a machine-readable handoff contract."""
    properties = claim.get('properties') or {}
    expressions = {
        name: (properties.get(name) or {}).get('expression')
        for name in PIV_PROPERTY_NAMES
    }
    roles = {name: _vars(expressions.get(name)) for name in PIV_PROPERTY_NAMES}
    p_symbols = roles['preconditions']
    i_symbols = roles['safety']
    v_symbols = roles['effects']
    observability_active = _observability_active(observability)
    semantic_profile = _semantic_profile(formal, claim, observability)
    problems: list[dict] = []

    if expressions.get('safety') is None:
        _add(problems, 'I_MISSING', 'error', 'safety/invariant expression is absent')
    if expressions.get('effects') is None:
        _add(problems, 'V_MISSING', 'error', 'effect/violation expression is absent')
    if not i_symbols:
        _add(problems, 'I_EMPTY', 'error', 'invariant references no observable symbols')
    if not v_symbols:
        _add(problems, 'V_EMPTY', 'error', 'effect references no observable symbols')

    i_expr_early = expressions.get('safety')
    v_expr_early = expressions.get('effects')
    if i_expr_early is not None and _always_true(i_expr_early) \
            and _const(i_expr_early) is not True:
        _add(problems, 'I_TAUTOLOGY', 'error',
             'invariant is a structural tautology and cannot be falsified')
    if i_expr_early is not None and _always_false(i_expr_early):
        _add(problems, 'I_CONTRADICTION', 'error',
             'invariant is structurally false on every assignment')
    if (isinstance(i_expr_early, dict)
            and i_expr_early.get('op') == 'implies'
            and len(i_expr_early.get('args') or []) == 2
            and i_expr_early['args'][0] == i_expr_early['args'][1]):
        _add(problems, 'I_SELF_IMPLICATION', 'error',
             'implication has identical antecedent and consequent')
    if (isinstance(i_expr_early, dict)
            and i_expr_early.get('op') in {'eq', 'le', 'ge'}
            and len(i_expr_early.get('args') or []) == 2
            and i_expr_early['args'][0] == i_expr_early['args'][1]):
        _add(problems, 'I_TRIVIAL_OPERAND', 'error',
             'invariant compares an expression with itself')
    if (v_expr_early is not None and _always_true(v_expr_early)
            and _const(v_expr_early) is not True):
        _add(problems, 'V_TAUTOLOGY', 'error',
             'effect is a structural tautology and cannot witness a hazard')
    if (v_expr_early is not None and _always_false(v_expr_early)
            and _const(v_expr_early) is not False):
        _add(problems, 'V_CONTRADICTION', 'error',
             'effect is structurally false and cannot be witnessed')

    for role, symbols in roles.items():
        node = expressions.get(role)
        if _const(node) in (True, False):
            if role == 'safety' and _const(node) is True:
                _add(problems, 'CONSTANT_INVARIANT', 'error',
                     'invariant is constant true', role)
            elif role == 'effects':
                _add(problems, 'CONSTANT_EFFECT', 'error',
                     'effect is constant', role)
            elif role == 'preconditions' and _const(node) is False:
                _add(problems, 'CONSTANT_FALSE_PRECONDITION', 'error',
                     'preconditions are constant false', role)
        for symbol in sorted(symbols):
            meta = _symbol_meta(formal, observability, symbol)
            if not str(meta.get('checkpoint') or '').strip():
                _add(problems, 'MISSING_CHECKPOINT', 'warning',
                     'symbol has no checkpoint', symbol)
            if observability_active:
                if not meta.get('observable_kind'):
                    _add(problems, 'OBSERVABLE_KIND_MISSING', 'warning',
                         'symbol has no observable kind', symbol)
                if meta.get('scope') == 'cross_contract' and not meta.get('receiver'):
                    _add(problems, 'CROSS_CONTRACT_RECEIVER_MISSING', 'warning',
                         'cross-contract symbol has no receiver', symbol)

    i_expr = expressions.get('safety')
    v_expr = expressions.get('effects')
    p_expr = expressions.get('preconditions')
    if i_expr is not None and i_expr == v_expr:
        _add(problems, 'I_COPIED_FROM_V', 'error',
             'invariant and effect are the same expression')
    elif _effect_is_polarity_only(i_expr, v_expr):
        _add(problems, 'I_V_POLARITY_ONLY', 'warning',
             'effect is only the logical polarity complement of the invariant; '
             'it does not independently witness the hazard')
    elif _effect_restates_invariant(i_expr, v_expr):
        _add(problems, 'I_V_RESTATEMENT', 'warning',
             'effect merely restates the invariant or one of its subexpressions')
    elif (_opposite_vars(i_symbols, v_symbols)
          and not _effect_is_implication_counterexample(i_expr, v_expr)):
        _add(problems, 'EFFECT_NOT_INDEPENDENT', 'warning',
             'effect uses only invariant symbols without an independent '
             'counterexample')
    elif (isinstance(i_expr, dict) and i_expr.get('op') == 'implies'
          and isinstance(v_expr, dict) and _contains(
              v_expr, (i_expr.get('args') or [None])[0])
          and not _effect_is_implication_counterexample(i_expr, v_expr)):
        _add(problems, 'I_V_TAUTOLOGY', 'warning',
             'effect reuses the implication antecedent without negating its '
             'consequent; the pair is a tautology')
    if (p_expr is not None and i_expr == p_expr):
        _add(problems, 'I_COPIED_FROM_P', 'warning',
             'invariant is identical to the precondition expression')
    if (i_symbols and i_symbols <= p_symbols
            and not _effect_is_implication_counterexample(i_expr, v_expr)):
        _add(problems, 'I_ONLY_REUSES_P', 'warning',
             'invariant references only precondition symbols; it is not an '
             'independent post-state property')

    # Code-observability contract.  When Stage 2 supplies an observability
    # artifact, an invariant that only reuses P or only exists at one
    # post-state snapshot is not a transition witness and must not be treated
    # as auto-assertable.  Without the artifact these checks stay dormant so
    # historical report-only replay remains possible.
    if observability_active:
        i_meta = [_symbol_meta(formal, observability, symbol)
                  for symbol in sorted(i_symbols)]
        v_meta = [_symbol_meta(formal, observability, symbol)
                  for symbol in sorted(v_symbols)]
        i_layers = {_checkpoint_layer(_checkpoint(meta)) for meta in i_meta
                    if _checkpoint(meta)}
        v_layers = {_checkpoint_layer(_checkpoint(meta)) for meta in v_meta
                    if _checkpoint(meta)}
        if (i_layers and len(i_layers) == 1 and 'before' not in i_layers
                and v_layers and v_layers <= i_layers):
            _add(problems, 'I_SAME_CHECKPOINT_ONLY', 'warning',
                 'invariant and effect share only the same post-state '
                 'checkpoint; no before/after transition can be observed')
        if i_layers and v_layers and i_layers == v_layers and len(i_layers) == 1:
            _add(problems, 'I_NOT_TRANSITION', 'warning',
                 'invariant is evaluated at one layer only; verify that it '
                 'constrains a transition rather than a single snapshot')
        for symbol in sorted(i_symbols | v_symbols):
            meta = _symbol_meta(formal, observability, symbol)
            if meta.get('observable_kind') and not (
                    meta.get('source_entity') or meta.get('code_fact')
                    or meta.get('mutation_site')):
                _add(problems, 'OBSERVABILITY_REQUIRES_CODE_FACT', 'warning',
                     'observable symbol has no source entity, code fact, or '
                     'mutation site', symbol)
            if symbol in i_symbols and not meta.get('mutation_site'):
                _add(problems, 'I_MUTATION_SITE_MISSING', 'warning',
                     'invariant symbol has no code mutation site', symbol)

    if semantic_profile['bucket'] == 'snapshot_only':
        _add(problems, 'I_SNAPSHOT_ONLY', 'advisory',
             'invariant is observed at one snapshot layer; bind a transition '
             'or supply a code-fact checkpoint')
    if (semantic_profile['bucket'] == 'snapshot_only'
            and semantic_profile['i_shape'] in {'var', 'not'}):
        _add(problems, 'I_SNAPSHOT_BARE_VAR', 'advisory',
             'invariant is a bare predicate at a single checkpoint; it may be '
             'a restatement of the scenario rather than a safety relation')

    metas = [_symbol_meta(formal, observability, symbol)
             for symbol in sorted(i_symbols | v_symbols)]
    checkpoint_missing = any(not str(meta.get('checkpoint') or '').strip()
                             for meta in metas)
    for symbol in sorted(i_symbols | v_symbols):
        if _symbol_meta(formal, observability, symbol).get('binding_risk') == 'high':
            _add(problems, 'OBSERVABILITY_HIGH_RISK', 'warning',
                 'symbol declares high binding risk; stage 3 must resolve it',
                 symbol)
    observable_missing = any(not meta.get('observable_kind') for meta in metas) \
        if observability_active else False
    high_risk = any(meta.get('binding_risk') == 'high' for meta in metas)
    errors = [row for row in problems if row['severity'] == 'error']
    warnings = [row for row in problems if row['severity'] not in
                {'error', 'advisory'}]
    advisory = [row for row in problems if row['severity'] == 'advisory']
    review_codes = {
        'EFFECT_NOT_INDEPENDENT', 'I_V_POLARITY_ONLY', 'I_V_RESTATEMENT',
        'I_V_TAUTOLOGY', 'I_COPIED_FROM_P', 'I_ONLY_REUSES_P',
    }
    review_warnings = [row for row in warnings
                       if row['code'] in review_codes]
    can_auto_assert = (not errors and not observable_missing and not high_risk
                       and not review_warnings)
    if errors:
        route = 'stage2_repair'
    elif observable_missing:
        route = 'reference_patch_candidate'
    elif checkpoint_missing or high_risk or review_warnings:
        route = 'binding_review'
    else:
        route = 'auto_assert'

    return {
        'claim_id': claim.get('id'),
        'status': ('rejected' if errors else
                   'needs_review' if warnings else 'ready'),
        'roles': {name: sorted(symbols) for name, symbols in roles.items()},
        'checkpoint_missing': checkpoint_missing,
        'observable_missing': observable_missing,
        'i_checkpoints': sorted({_checkpoint(_symbol_meta(formal, observability, symbol))
                                 for symbol in sorted(i_symbols)
                                 if _checkpoint(_symbol_meta(formal, observability,
                                                            symbol))}),
        'v_checkpoints': sorted({_checkpoint(_symbol_meta(formal, observability, symbol))
                                 for symbol in sorted(v_symbols)
                                 if _checkpoint(_symbol_meta(formal, observability,
                                                            symbol))}),
        'shared_with_p': sorted(i_symbols & p_symbols),
        'requires_code_fact': sorted(
            symbol for symbol in sorted(i_symbols | v_symbols)
            if (_symbol_meta(formal, observability, symbol).get('observable_kind')
                and not (_symbol_meta(formal, observability, symbol).get(
                    'source_entity') or _symbol_meta(formal, observability,
                                                     symbol).get('code_fact')
                         or _symbol_meta(formal, observability, symbol).get(
                             'mutation_site')))),
        'i_v': {
            'same_expression': i_expr is not None and i_expr == v_expr,
            'shared_symbols': sorted(i_symbols & v_symbols),
            'polarity_only': _effect_is_polarity_only(i_expr, v_expr),
            'restates_invariant': _effect_restates_invariant(i_expr, v_expr),
            'implication_counterexample': _effect_is_implication_counterexample(
                i_expr, v_expr),
            'independent': not (
                i_expr is not None and i_expr == v_expr
                or _effect_is_polarity_only(i_expr, v_expr)
                or _effect_restates_invariant(i_expr, v_expr)),
        },
        'can_auto_assert': can_auto_assert,
        'auto_assert_allowed': can_auto_assert,
        'route': route,
        'problems': problems,
        'warnings': [row['code'] for row in warnings],
        'advisories': [row['code'] for row in advisory],
        'semantic_profile': semantic_profile,
        'semantic_bucket': semantic_profile['bucket'],
    }


def build_contract(formal: dict, observability: dict | None = None) -> dict:
    claims = []
    for claim in formal.get('claims') or []:
        if not isinstance(claim, dict) or not claim.get('id'):
            continue
        claim_observability = (observability or {}).get(claim['id'])
        claims.append(audit_claim(formal, claim, claim_observability))
    rows = {row['claim_id']: row for row in claims}
    return {
        'schema_version': SCHEMA_VERSION,
        'claims': rows,
        'summary': {
            'claims': len(rows),
            'ready': sum(row['status'] == 'ready' for row in rows.values()),
            'needs_review': sum(row['status'] == 'needs_review'
                                for row in rows.values()),
            'rejected': sum(row['status'] == 'rejected' for row in rows.values()),
            'auto_assert': sum(row['can_auto_assert'] for row in rows.values()),
            'binding_review': sum(row['route'] == 'binding_review'
                                  for row in rows.values()),
            'stage2_repair': sum(row['route'] == 'stage2_repair'
                                 for row in rows.values()),
            'reference_patch_candidate': sum(
                row['route'] == 'reference_patch_candidate'
                for row in rows.values()),
        },
    }
