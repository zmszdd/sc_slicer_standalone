#!/usr/bin/env python3
"""Turn a Stage-3 verdict into one actionable witness route."""
from __future__ import annotations

SCHEMA_VERSION = 'stage3-witness-router/1'

_RULES = (
    ('reproduced', {'violation_reproduced'},
     'no_action', 'claim reproduced on the exploit path'),
    ('stage2_semantic', {'effect_observed_invariant_holds',
                         'invariant_holds_on_exploit_path'},
     'restate_stage2_invariant',
     'effect was witnessed but the invariant still holds'),
    ('revert_before_effect', {'poc_revert_before_effect',
                              'halt_witness_required'},
     'build_halt_witness', 'revert happened before the claimed effect'),
    ('precondition_false', {'precondition_false',
                            'preconditions_infeasible_on_code'},
     'repair_preconditions', 'claimed preconditions are not reachable'),
    ('effect_not_witnessed', {'effect_not_witnessed', 'poc_not_witnessed'},
     'repair_poc_or_p', 'the violation effect was not observed'),
    ('compile_failed', {'compile_error', 'compile_blocked'},
     'repair_harness', 'the patched harness did not compile'),
    ('binding_failed', {'binding_error', 'binding_failed', 'partial_binding'},
     'repair_binding', 'observable symbols were not fully bound'),
    ('reference_patch', {'reference_patch_required'},
     'use_mechanism_ceiling_route',
     'mechanism requires a reference patch and is not automatic recall'),
)


def route(summary: dict | None) -> dict:
    """Return the primary witness route and one next action."""
    summary = summary if isinstance(summary, dict) else {}
    verdict = str(summary.get('consistency_verdict')
                  or summary.get('verdict') or '')
    reasons: list[str] = []
    for text in (str(summary.get('compile_error') or ''),
                 str((summary.get('witness') or {}).get('reason') or '')):
        if text:
            reasons.append(text[:400])

    for name, verdicts, action, description in _RULES:
        if verdict in verdicts:
            return {
                'schema_version': SCHEMA_VERSION,
                'primary_reason': name,
                'next_action': action,
                'verdict': verdict,
                'description': description,
                'secondary_reasons': reasons,
            }
    return {
        'schema_version': SCHEMA_VERSION,
        'primary_reason': 'unresolved',
        'next_action': 'resolve_evidence_then_rerun',
        'verdict': verdict,
        'description': 'verdict has no deterministic witness route',
        'secondary_reasons': reasons,
    }
