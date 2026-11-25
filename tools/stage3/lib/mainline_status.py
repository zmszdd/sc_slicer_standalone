"""Canonical case-level readiness contract for the three-stage mainline.

This module does not run solvers, models, or forge.  It turns the artifacts
already produced by stage 1/2/3 into one fail-closed status record so callers
cannot accidentally treat ``pending``, ``compile ok but no test entrypoint``,
or an unresolved binding as an evaluable case.
"""
from __future__ import annotations

import json
from pathlib import Path

SCHEMA_VERSION = 'mainline-case-status/1'

RECOVERABLE_POC_ACTIONS = {
    'snippet_only', 'bare_test_fn', 'repo_test_deps', 'self_contained',
}
NON_RECOVERABLE_POC_ACTIONS = {'no_poc_code', 'fork_rpc', 'missing_submission'}

WEAK_INVARIANT_BLOCKING_CODES = {
    'I_LAYER_MISMATCH', 'I_SELF_IMPLICATION',
    'I_SNAPSHOT_ONLY', 'I_SNAPSHOT_BARE_VAR',
}

NON_EXECUTION_VERDICTS = {
    'binding_error', 'binding_failed', 'partial_binding',
    'compile_error', 'compile_blocked',
    'stage2_restatement_required', 'stage2_review_required',
    'stage2_repair_required', 'stage2_reference_patch_candidate',
    'stage2_not_run', 'stage2_missing',
    'reference_patch_required', 'not_dynamically_expressible',
    'halt_witness_required',
}


def _unique(values):
    return list(dict.fromkeys(value for value in values if value))


def stage1_status(*, compile_status: str | None,
                  test_entrypoint: bool,
                  poc_action: str | None = None,
                  blockers: list[str] | None = None) -> dict:
    """Return the stage-1 data-readiness decision.

    ``compile ok`` alone is not enough.  A case must also expose a runnable
    ``test_*`` entrypoint, and a PoC that depends on live RPC is not considered
    self-contained for the trusted local execution path.
    """
    local: list[str] = list(blockers or [])
    if compile_status != 'ok':
        local.append(f'compile_{compile_status or "missing"}')
    if not test_entrypoint:
        local.append('no_test_entrypoint')
    if poc_action in NON_RECOVERABLE_POC_ACTIONS:
        local.append(f'poc_{poc_action}')
    elif poc_action and poc_action not in RECOVERABLE_POC_ACTIONS:
        local.append(f'poc_{poc_action}')
    local = _unique(local)
    return {
        'data_ready': not local,
        'compile_status': compile_status,
        'test_entrypoint': bool(test_entrypoint),
        'poc_action': poc_action,
        'blockers': local,
    }


def stage2_status(*, contract: dict | None,
                  weak_invariant: dict | None = None) -> dict:
    """Return the claim-readiness decision for one formalized claim."""
    contract = contract if isinstance(contract, dict) else {}
    weak = weak_invariant if isinstance(weak_invariant, dict) else {}
    blockers: list[str] = []
    if not contract:
        blockers.append('formalization_contract_missing')
        claim_ready = False
    else:
        route = str(contract.get('route') or '').strip()
        can_auto = bool(contract.get('can_auto_assert'))
        if route != 'auto_assert' or not can_auto:
            blockers.append(f'stage2_route_{route or "unknown"}')
        codes = set()
        for key in ('problems', 'warnings', 'advisories'):
            for row in contract.get(key) or []:
                if isinstance(row, dict) and row.get('code'):
                    codes.add(str(row['code']))
                elif isinstance(row, str):
                    codes.add(row)
        if codes & WEAK_INVARIANT_BLOCKING_CODES:
            blockers.extend(sorted(codes & WEAK_INVARIANT_BLOCKING_CODES))
        claim_ready = not blockers

    weak_codes = set(weak.get('codes') or [])
    weak_blocking = sorted(weak_codes & WEAK_INVARIANT_BLOCKING_CODES)
    stage2_diag = [
        row for row in (weak.get('stage2_diagnostics') or [])
        if isinstance(row, dict) and row.get('severity') == 'blocking'
    ]
    if weak.get('risk') == 'high' or stage2_diag:
        if weak_blocking:
            blockers.extend(weak_blocking)
        if stage2_diag:
            blockers.extend(
                str(row.get('code') or 'stage2_weak_invariant')
                for row in stage2_diag)
        claim_ready = False

    return {
        'claim_ready': bool(claim_ready),
        'route': str((contract or {}).get('route') or ''),
        'can_auto_assert': bool((contract or {}).get('can_auto_assert')),
        'weak_invariant_risk': weak.get('risk'),
        'blockers': _unique(blockers),
    }


def stage3_status(*, binding_ready: bool, execution_ready: bool,
                  verdict: str | None = None,
                  blockers: list[str] | None = None) -> dict:
    local = list(blockers or [])
    if not binding_ready:
        local.append('binding_not_ready')
    if not execution_ready:
        local.append('execution_not_ready')
    local = _unique(local)
    return {
        'binding_ready': bool(binding_ready),
        'execution_ready': bool(execution_ready),
        'verdict': verdict,
        'eligible_for_metrics': bool(binding_ready and execution_ready),
        'blockers': local,
    }


def claim_status(*, claim_id: str, stage2_gate: dict | None,
                 weak_gate: dict | None = None,
                 binding_ready: bool = False,
                 execution: dict | None = None) -> dict:
    """Join one claim's stage-2 gate, binding, and execution outcome.

    Case-level summary must never infer eligibility by combining a ready
    binding from one claim with an execution result from another.  Keeping the
    decision at claim level is what makes ``eligible_for_metrics`` honest.
    """
    gate = stage2_gate if isinstance(stage2_gate, dict) else {}
    weak = weak_gate if isinstance(weak_gate, dict) else {}
    execution = execution if isinstance(execution, dict) else {}
    stage2_blocking = bool(gate.get('blocking')) or bool(weak.get('blocking'))
    verdict = execution.get('consistency_verdict') or execution.get('verdict')
    execution_ready = bool(
        execution.get('status') == 'done' and verdict
        and verdict not in NON_EXECUTION_VERDICTS)
    blockers = []
    if not gate:
        blockers.append('stage2_contract_missing')
    elif stage2_blocking:
        blockers.append(gate.get('category') or weak.get('category')
                        or 'stage2_review_required')
    if not binding_ready:
        blockers.append('binding_not_ready')
    if not execution_ready:
        blockers.append('execution_not_ready')
    return {
        'claim_id': claim_id,
        'stage2_allowed': not stage2_blocking and bool(gate),
        'claim_ready': not stage2_blocking and bool(gate),
        'binding_ready': bool(binding_ready),
        'execution_ready': execution_ready,
        'eligible_for_metrics': bool(
            not stage2_blocking and gate and binding_ready and execution_ready),
        'verdict': verdict,
        'blockers': _unique(blockers),
    }


def aggregate_claim_status(rows: list[dict]) -> tuple[dict, dict, dict]:
    """Return case-level stage-2/stage-3 status plus the claim rows."""
    rows = [row for row in rows if isinstance(row, dict)]
    stage2_blockers: list[str] = []
    stage3_blockers: list[str] = []
    if not rows:
        stage2_blockers.append('stage2_not_run')
        stage3_blockers.extend(['stage3_not_run', 'binding_not_ready'])
        return (
            {'claim_ready': False, 'blockers': stage2_blockers,
             'claims_total': 0, 'claims_ready': 0},
            {'binding_ready': False, 'execution_ready': False,
             'eligible_for_metrics': False, 'blockers': stage3_blockers,
             'claims_total': 0, 'claims_eligible': 0},
            [],
        )
    ready = [row for row in rows if row.get('claim_ready')]
    bound = [row for row in rows
             if row.get('claim_ready') and row.get('binding_ready')]
    executed = [row for row in rows
                if row.get('claim_ready') and row.get('execution_ready')]
    eligible = [row for row in rows if row.get('eligible_for_metrics')]
    for row in rows:
        if not row.get('claim_ready'):
            stage2_blockers.extend(row.get('blockers') or [])
        if not row.get('binding_ready'):
            stage3_blockers.append('binding_not_ready')
        if not row.get('execution_ready'):
            stage3_blockers.append('execution_not_ready')
    stage2 = {
        'claim_ready': bool(ready),
        'claims_total': len(rows),
        'claims_ready': len(ready),
        'blockers': _unique(stage2_blockers),
    }
    stage3 = {
        'binding_ready': bool(bound),
        'execution_ready': bool(executed),
        'eligible_for_metrics': bool(eligible),
        'claims_total': len(rows),
        'claims_bound': len(bound),
        'claims_executed': len(executed),
        'claims_eligible': len(eligible),
        'blockers': _unique(stage3_blockers),
    }
    return stage2, stage3, rows


def build_case_status(*, case_id: str, project: str | None = None,
                      stage1: dict | None = None,
                      stage2: dict | None = None,
                      stage3: dict | None = None,
                      claims: list[dict] | None = None,
                      protocol_version: str | None = None,
                      fingerprint: str | None = None) -> dict:
    stage1 = stage1 or stage1_status(
        compile_status=None, test_entrypoint=False)
    stage2 = stage2 or {'claim_ready': False, 'blockers': ['not_run']}
    stage3 = stage3 or stage3_status(
        binding_ready=False, execution_ready=False)
    blockers = _unique(
        [f'stage1:{row}' for row in stage1.get('blockers') or []]
        + [f'stage2:{row}' for row in stage2.get('blockers') or []]
        + [f'stage3:{row}' for row in stage3.get('blockers') or []])
    return {
        'schema_version': SCHEMA_VERSION,
        'case_id': case_id,
        'project': project,
        'protocol_version': protocol_version,
        'fingerprint': fingerprint,
        'stage1': stage1,
        'stage2': stage2,
        'stage3': stage3,
        'claims': list(claims or []),
        'data_ready': bool(stage1.get('data_ready')),
        'claim_ready': bool(stage2.get('claim_ready')),
        'binding_ready': bool(stage3.get('binding_ready')),
        'execution_ready': bool(stage3.get('execution_ready')),
        'eligible_for_metrics': bool(stage3.get('eligible_for_metrics')),
        'blockers': blockers,
    }


def from_blind_audit_row(row: dict) -> dict:
    ignored = {
        # A snippet is the source form; once the resurrected harness has a
        # test entrypoint, that snippet-shape blocker no longer prevents the
        # local differential run.
        'poc_is_snippet_not_harness',
    }
    blockers = [item for item in (row.get('blockers') or [])
                if item not in ignored]
    stage1 = stage1_status(
        compile_status=row.get('contract_compile'),
        test_entrypoint=bool(row.get('harness_has_test')),
        poc_action=row.get('poc_action'),
        blockers=blockers,
    )
    return build_case_status(
        case_id=row.get('case'),
        project=row.get('project'),
        stage1=stage1,
        stage2={'claim_ready': False, 'blockers': ['stage2_not_run']},
        stage3=stage3_status(
            binding_ready=False, execution_ready=False,
            blockers=['stage3_not_run']),
    )


def from_canonical_row(row: dict, claims: list[dict] | None = None) -> dict:
    """Build a case status from canonical stage-1 audit plus claim verdicts.

    Unlike :func:`from_blind_audit_row`, this variant does not assume stage 2
    or stage 3 never ran.  It is used by the read-only aggregator after joining
    the canonical flatten artifact, formalization contract gates, bindings and
    stage-3 run summaries.
    """
    canonical_ok = (row.get('stage1_route') == 'flatten_root'
                    and row.get('contract_compile') == 'ok')
    ignored = {'poc_is_snippet_not_harness'} if canonical_ok else set()
    if canonical_ok:
        # A legacy skeleton row may still be pending even when the canonical
        # flatten artifact exists; never let the fallback mask stage 1.
        ignored.add('contract_skeleton_not_compiling')
    blockers = [item for item in (row.get('blockers') or [])
                if item not in ignored]
    compile_status = row.get('contract_compile')
    stage1 = stage1_status(
        compile_status=compile_status,
        test_entrypoint=bool(row.get('harness_has_test')),
        poc_action=row.get('poc_action'),
        blockers=blockers,
    )
    if claims:
        stage2, stage3, joined = aggregate_claim_status(claims)
    else:
        stage2 = {'claim_ready': False, 'blockers': ['stage2_not_run']}
        stage3 = stage3_status(
            binding_ready=False, execution_ready=False,
            blockers=['stage3_not_run'])
        joined = []
    return build_case_status(
        case_id=row.get('case'),
        project=row.get('project'),
        stage1=stage1,
        stage2=stage2,
        stage3=stage3,
        claims=joined,
    )


def load_json(path: Path | str) -> dict:
    try:
        return json.loads(Path(path).read_text())
    except (OSError, ValueError):
        return {}


def summarize(rows: list[dict]) -> dict:
    claims = [claim for row in rows for claim in (row.get('claims') or [])]
    return {
        'cases': len(rows),
        'data_ready': sum(bool(row.get('data_ready')) for row in rows),
        'claim_ready': sum(bool(row.get('claim_ready')) for row in rows),
        'binding_ready': sum(bool(row.get('binding_ready')) for row in rows),
        'execution_ready': sum(bool(row.get('execution_ready')) for row in rows),
        'eligible_for_metrics': sum(
            bool(row.get('eligible_for_metrics')) for row in rows),
        'claims': len(claims),
        'claims_ready': sum(bool(row.get('claim_ready')) for row in claims),
        'claims_eligible': sum(
            bool(row.get('eligible_for_metrics')) for row in claims),
    }
