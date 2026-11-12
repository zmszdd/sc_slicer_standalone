"""Verdict classification and repair-hint building for the stage-3 outer loop."""
from __future__ import annotations

TERMINAL_VERDICTS = {
    'violation_reproduced',
    'violation_not_reproduced',
}
BINDING_FIXABLE_VERDICTS = {
    'partial_binding',
    'preconditions_infeasible_on_code',
    'compile_error',
    'binding_error',
    # A witnessed effect while I holds means I is vacuous or mis-bound;
    # the loop must rebind/restate I instead of accepting the non-repro.
    'effect_observed_invariant_holds',
}
NON_FIXABLE_VERDICTS = {
    'compile_blocked',
    'not_dynamically_expressible',
    'reference_patch_required',
    'halt_witness_required',
    # PoC never witnessed P on code: stage-1/PoC problem, not a binding problem.
    'poc_not_witnessed',
}
# Entry gate for the stage-3 repair loop.  ``binding_failed`` is the eval-run
# verdict for claims whose binding LLM proposal never succeeded, and
# ``inconclusive`` is the evidence-collection verdict; both are re-attempted by
# ``stage3_verdict_loop`` even though they are not pipeline binding verdicts.
REPAIR_LOOP_VERDICTS = BINDING_FIXABLE_VERDICTS | {
    'inconclusive',
    'binding_failed',
}


def verdict_action(verdict: str | None, summary: dict | None = None) -> str:
    """Route a consistency verdict to the next bounded outer-loop action.

    ``preconditions_infeasible_on_code`` is the only verdict whose fixability
    depends on *why* P was not witnessed, so it is split on the pipeline's
    ``precondition_failure`` field.  When the original PoC itself did not pass,
    P was never witnessed on code and rebinding the observables cannot help;
    that case routes to ``skip`` instead of a futile rebind loop.
    """
    if verdict in TERMINAL_VERDICTS:
        return 'accept'
    if verdict == 'preconditions_infeasible_on_code':
        failure = (summary or {}).get('precondition_failure')
        if failure == 'poc_not_witnessed':
            return 'skip'
        return 'rebind'
    if verdict in BINDING_FIXABLE_VERDICTS:
        return 'rebind'
    if verdict in NON_FIXABLE_VERDICTS:
        return 'skip'
    if verdict == 'inconclusive':
        return 'collect_missing_evidence'
    return 'rebind'


def repair_hint(summary: dict, consistency: dict | None) -> str:
    """Build a concise LLM repair hint from a run summary plus consistency record."""
    verdict = summary.get('consistency_verdict')
    if verdict == 'binding_error':
        info = summary.get('binding_error') or {}
        return 'binding failed to build the patched project: ' + \
            str(info.get('reason') or '')[:1200]
    if verdict == 'compile_blocked':
        compile_info = summary.get('compile_error') or {}
        original = str(compile_info.get('original') or '')[:1200]
        return ('original slice failed to compile (stage-1 flatten problem): '
                + original) if original else 'original slice failed to compile'
    if verdict == 'not_dynamically_expressible':
        expr = summary.get('expressibility') or {}
        kind = expr.get('expressibility')
        symbols = (expr.get('cross_contract_symbols') or []) + \
            (expr.get('unobservable_symbols') or [])
        detail = f'{kind}; blocked symbols: {symbols[:8]}'
        return ('safety invariant cannot be expressed as an assertion at the '
                'injection point: ' + detail)
    if verdict == 'reference_patch_required':
        routing = summary.get('routing') or {}
        return ('claim requires a reference patch and none was provided; '
                'route=' + str(routing.get('route') or 'unknown'))
    if verdict == 'compile_error':
        compile_info = summary.get('compile_error') or {}
        retry = summary.get('compile_retry') or {}
        neutralized = retry.get('neutralized') or []
        prefix = ''
        if neutralized:
            prefix = f'previous blacklist retry neutralized: {neutralized}; '
        patched = str(compile_info.get('patched') or '')[:1200]
        return (prefix + 'patched project failed to compile: ' + patched) \
            if patched else (prefix + 'patched project failed to compile')
    if verdict == 'effect_observed_invariant_holds':
        return ('effect observed while invariant holds: restate I or rebind the '
                'I-side observable; current I is vacuous on the exploit path')
    if verdict == 'preconditions_infeasible_on_code':
        failure = summary.get('precondition_failure')
        if failure == 'poc_not_witnessed':
            return ('PoC did not witness P on code: fix the PoC or stage-1 '
                    'slice, not the binding')
        if failure == 'snapshot_unwitnessed':
            return ('injected precondition snapshot was false at its '
                    'mid-function anchor: restate the before-symbol with an '
                    'entry-level expression so the snapshot is not relocated, '
                    'or change its checkpoint; P must hold where the snapshot '
                    'is captured')
        return 'check binding.json against the Stage-2 binding_contract'
    if verdict == 'poc_not_witnessed':
        return ('PoC did not witness P on code: fix the PoC or stage-1 slice, '
                'not the binding')
    if isinstance(consistency, dict):
        diagnostic = consistency.get('replan_diagnostic')
        if isinstance(diagnostic, dict) and diagnostic.get('hint'):
            return str(diagnostic['hint'])
        unbound = consistency.get('unbound_symbols') or []
        if unbound:
            return 'unbound symbols: ' + ', '.join(unbound)
    if verdict == 'partial_binding':
        info = summary.get('partial_binding') or {}
        unbound = info.get('unbound_symbols') or []
        if unbound:
            return 'unbound symbols: ' + ', '.join(unbound)
        reason = str(info.get('reason') or '')[:1200]
        if reason:
            return reason
    return f'verdict {verdict!r} needs a corrected binding'
