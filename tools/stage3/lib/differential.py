"""Map original/patched test outcomes to stage-2 code query results.

Dynamic testing only produces witnesses. The mapping is intentionally
conservative: anything not witnessed becomes ``unknown`` unless both versions
agree the exploit path does not reproduce the violation.

The live codegen (``lib/patch.py``) injects a single combined assertion
``assert(!P || I)`` with no message, so a patched failure that is not an
assertion panic is NOT evidence about I; it is left ``unknown``. The legacy
``require(..., "stage3:P failed")`` fixtures are still honoured for offline
replay, but new runs no longer produce that marker.
"""
from __future__ import annotations

QUERIES = (
    'P_and_T', 'P_and_T_and_not_I', 'P_and_T_and_V', 'P_and_T_and_not_V')


def _success(result: dict | None) -> bool:
    return bool(result) and result.get('status') == 'Success'


def _reason_has(result: dict | None, needle: str) -> bool:
    return bool(result) and needle in str(result.get('reason') or '')


def compute_queries(probe: dict, original_result: dict | None,
                    patched_result: dict | None,
                    safety_patched: dict | None = None,
                    reference_patch: bool = False,
                    effect_result: dict | None = None) -> dict:
    results = {name: 'unknown' for name in QUERIES}
    if not original_result or not patched_result:
        return results

    original_ok = _success(original_result)
    patched_ok = _success(patched_result)
    # Legacy fixtures only: the current codegen emits a plain assert(!P || I),
    # so 'stage3:P' no longer appears in live run reasons.
    p_failed = _reason_has(patched_result, 'stage3:P')
    reason = str(patched_result.get('reason') or '') if patched_result else ''
    i_failed = 'assertion' in reason or 'panic' in reason.lower()
    halt_failed = 'stage3:halt' in reason
    precondition_unwitnessed = 'stage3:precondition_unwitnessed' in reason

    if original_ok and patched_ok:
        # original PoC passes => P and T witnessed; patched assert(!P||I) also
        # passes => I held (or P false), so the invariant was not contradicted.
        # ``P_and_T_and_V`` is no longer hard-coded to unsat: the effect probe
        # (assert(!P || V)) witnesses V independently.  When I is vacuous on the
        # exploit path the effect still occurs, and the correct verdict is
        # ``effect_observed_invariant_holds`` (restate I), not a plain
        # ``violation_not_reproduced``.
        results.update({
            'P_and_T': 'sat',
            'P_and_T_and_not_I': 'unsat',
            'P_and_T_and_V': 'sat' if _success(effect_result) else 'unsat',
        })
    elif original_ok and not patched_ok:
        if precondition_unwitnessed:
            # The injected precondition snapshot was false at the injection
            # point, so P was not actually witnessed on the exploit path. This
            # is a binding/checkpoint fidelity signal, not a clean repro or a
            # clean "invariant holds".
            results.update({
                'P_and_T': 'unsat',
                'P_and_T_and_not_I': 'unknown',
                'P_and_T_and_V': 'unknown',
            })
        elif p_failed:
            # Legacy marker: patched failed on the precondition assert.
            results.update({
                'P_and_T': 'unsat',
                'P_and_T_and_not_I': 'unknown',
                'P_and_T_and_V': 'unknown',
            })
        elif halt_failed:
            # patched slice reverted on the halt-to-revert rewrite: the original
            # transition halts (stop) instead of returning, so the invariant is
            # contradicted on the exploit path.
            results.update({
                'P_and_T': 'sat',
                'P_and_T_and_not_I': 'sat',
                'P_and_T_and_V': 'sat',
            })
        elif i_failed:
            # assert(!P || I) failed => P holds and I is contradicted.
            results.update({
                'P_and_T': 'sat',
                'P_and_T_and_not_I': 'sat',
                'P_and_T_and_V': 'sat',
            })
        elif reference_patch:
            # M1 reference fix: the patched contract reverted for a business
            # reason (e.g. the fix's require) while the original PoC passed,
            # so the reference patch blocks the exploit -> violation witnessed.
            results.update({
                'P_and_T': 'sat',
                'P_and_T_and_not_I': 'sat',
                'P_and_T_and_V': 'sat',
            })
        # else: patched failed for a non-assertion reason (business revert);
        # all queries stay unknown -> inconclusive, never a false positive.
    elif not original_ok and patched_ok:
        # original PoC failed => P was NOT witnessed on code. This is a
        # preconditions/binding signal, not a violation.
        results.update({
            'P_and_T': 'unsat',
            'P_and_T_and_not_I': 'unknown',
            'P_and_T_and_V': 'unknown',
        })
    else:
        # Both exploit tests ran and failed: the violation was not witnessed on
        # either version, so the invariant was not contradicted on code.
        results.update({
            'P_and_T_and_not_I': 'unsat',
            'P_and_T_and_V': 'unsat',
        })

    # A safe path that passes on the patched contract witnesses P AND T AND NOT V
    # (the invariant held and no violation was observed).
    if safety_patched is not None and _success(safety_patched):
        results['P_and_T_and_not_V'] = 'sat'
    return results
