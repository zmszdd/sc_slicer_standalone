"""Single shared implementation of the stage-3 case run core.

This module is the one and only place that encodes how a stage-3 case goes
from ``(src/, stage2_run/)`` to per-claim consistency verdicts:

    bind_claims()   -> one binding loop (propose + bounded repair + lint)
    run_multi()     -> one stage3_multi invocation
    derive_verdicts() -> one claim->verdict mapping with ceiling routing

Every entry point that drives stage-3 over a case (``cli.stage3_bind``,
``cli.stage3_eval_run``, and the cross-stage ``tools/pipeline`` runner) must
route through these functions instead of re-implementing the loop.  The small
call-site differences (strict lint, budget ceiling routing, reuse semantics)
are expressed as explicit parameters so there is still exactly one code path
for the binding loop itself.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

from lib.spec_loader import SpecError, load_stage2_run, safety_symbols_for_claim
from lib.binding_validate import lint_binding

ROOT = Path(__file__).resolve().parents[1]  # tools/stage3


def round_hint(claim_id: str, round_no: int, problems: list[str]) -> str:
    items = '; '.join(str(problem) for problem in problems[:12])
    return (f'round {round_no} failed for claim {claim_id}. '
            f'Fix these problems: {items}.')


def ceiling_verdict_for_bindability(bindability: str | None,
                                    anchor_observability: str | None = None
                                    ) -> str | None:
    """Deterministic terminal verdict for a hard-ceiling bindability class.

    ``no_anchor`` only becomes a hard ceiling when the anchor resolver also
    reports ``low`` observability: the deterministic matcher saw no semantic
    signal for an anchoring (I/V) symbol, so no ``assert(I)`` injection point
    can be derived. ``no_anchor`` with ``medium``/``high`` observability is a
    fuzzy-token false negative and must still be offered to the binding LLM.
    ``multi_contract`` is intentionally not mapped here.
    """
    if bindability == 'no_anchor' and anchor_observability == 'low':
        return 'not_dynamically_expressible'
    return None


def bind_claims(*, case_dir: Path, stage2_dir: Path, src_dir: Path,
                claims: list[str], formal: dict,
                max_rounds: int = 3, reuse: bool = False,
                strict: bool = True, apply_ceiling: bool = False,
                run_fn=subprocess.run) -> dict:
    """Propose a binding for every claim with bounded repair + lint.

    Returns a record bag consumed by the callers (``stage3_bind`` and
    ``stage3_eval_run``) plus the deterministic bindability contract when
    ``apply_ceiling`` is enabled.  ``run_fn`` is injectable so callers can
    monkeypatch transport failures in tests.
    """
    case_dir = Path(case_dir)
    stage2_dir = Path(stage2_dir)
    src_dir = Path(src_dir)
    bindings_dir = case_dir / 'bindings'
    bindings_dir.mkdir(parents=True, exist_ok=True)

    bindability_by_claim: dict[str, str] = {}
    anchor_by_claim: dict[str, dict] = {}
    if apply_ceiling:
        from lib.bindability_contract import build_contract
        contract = build_contract(stage2_dir, claims, src_dir)
        for claim_id, anchor in contract.items():
            bindability_by_claim[claim_id] = anchor.get('bindability', 'unknown')
            anchor_by_claim[claim_id] = anchor
    else:
        for claim_id in claims:
            bindability_by_claim[claim_id] = 'unknown'

    records: dict[str, dict] = {}
    bound_claim_ids: list[str] = []
    routed_verdicts: dict[str, str] = {}
    failed: list[dict] = []
    unobservable_symbols: list[str] = []

    for claim_id in claims:
        bindability = bindability_by_claim[claim_id]
        anchor = anchor_by_claim.get(claim_id, {})
        binding_path = bindings_dir / f'{claim_id}.json'

        # An existing binding wins over ceiling routing: ``--reuse`` /
        # ``--skip-llm`` means "use the binding already on disk", not
        # "re-decide whether the claim is bindable".
        if reuse and binding_path.is_file():
            records[claim_id] = {
                'claim_id': claim_id, 'status': 'reused', 'verdict': None,
                'bindability': 'reused', 'rounds_used': 0, 'unbound': [],
                'binding': str(binding_path), 'detail': None,
            }
            bound_claim_ids.append(claim_id)
            continue

        ceiling = (ceiling_verdict_for_bindability(
            bindability, anchor.get('anchor_observability'))
            if apply_ceiling else None)
        if ceiling is not None:
            routed_verdicts[claim_id] = ceiling
            records[claim_id] = {
                'claim_id': claim_id, 'status': 'routed', 'verdict': ceiling,
                'bindability': bindability, 'rounds_used': 0, 'unbound': [],
                'binding': None, 'detail': None,
            }
            continue

        safety_symbols = safety_symbols_for_claim(formal, claim_id)
        hint = None
        accepted = False
        unbound: list[str] = []
        rounds_used = 0
        for round_no in range(1, max_rounds + 1):
            rounds_used = round_no
            cmd = [sys.executable, '-m', 'cli.stage3_binding_llm',
                   '--stage2-run', str(stage2_dir), '--claim-id', claim_id,
                   '--src', str(src_dir),
                   '--out', str(case_dir / 'llm_proposal')]
            if hint:
                cmd += ['--hint', hint]
            if round_no > 1 and binding_path.is_file():
                cmd += ['--existing', str(binding_path)]
            proc = run_fn(cmd, capture_output=True, text=True, cwd=str(ROOT))
            try:
                proposal = json.loads(proc.stdout)
            except ValueError:
                proposal = None
            if proposal is None or not isinstance(proposal, dict):
                hint = round_hint(claim_id, round_no,
                                  ['transport: ' + (proc.stderr or proc.stdout)[:200]])
                continue
            if proposal.get('partial') and not proposal.get('problems'):
                written = case_dir / 'llm_proposal' / 'binding.proposal.json'
                if written.is_file():
                    shutil.copy2(written, binding_path)
                    accepted = True
                    unbound = list(proposal.get('unbound') or [])
                    if round_no < max_rounds:
                        detail = proposal.get('unbound_detail') or {}
                        rebindable = [s for s in unbound
                                      if detail.get(s, {}).get('observability') != 'low'
                                      or detail.get(s, {}).get('candidates')]
                        if rebindable:
                            hint = None
                            continue
                    break
            if not proposal.get('ok'):
                problems = list(proposal.get('problems') or [])
                if proposal.get('partial'):
                    problems.append('unbound: ' + ', '.join(
                        proposal.get('unbound', [])))
                hint = round_hint(claim_id, round_no, problems)
                continue
            written = case_dir / 'llm_proposal' / 'binding.proposal.json'
            if not written.is_file():
                hint = round_hint(claim_id, round_no, ['no proposal file written'])
                continue
            binding = json.loads(written.read_text())
            lint = lint_binding(binding, src_dir, test_dir=case_dir / 'test',
                                strict=strict, safety_symbols=safety_symbols)
            if lint['summary']['errors']:
                problems = [f"{problem['where']}: {problem['message']}"
                            for problem in lint['problems']]
                hint = round_hint(claim_id, round_no, problems)
                continue
            shutil.copy2(written, binding_path)
            accepted = True
            break

        if accepted:
            bound_claim_ids.append(claim_id)
            records[claim_id] = {
                'claim_id': claim_id, 'status': 'bound', 'verdict': None,
                'bindability': bindability, 'rounds_used': rounds_used,
                'unbound': unbound, 'binding': str(binding_path), 'detail': None,
            }
        else:
            failed.append({'claim': claim_id, 'reason': 'binding_exhausted',
                           'rounds': max_rounds, 'detail': hint})
            records[claim_id] = {
                'claim_id': claim_id, 'status': 'failed', 'verdict': None,
                'bindability': bindability, 'rounds_used': rounds_used,
                'unbound': unbound, 'binding': None, 'detail': hint,
            }

    bound_claim_ids = list(dict.fromkeys(bound_claim_ids))
    return {
        'records': records,
        'bound_claim_ids': bound_claim_ids,
        'routed_verdicts': routed_verdicts,
        'bindability_by_claim': bindability_by_claim,
        'failed': failed,
        'unobservable_symbols': sorted(set(unobservable_symbols)),
    }


def run_multi(*, case_dir: Path, bindings_dir: Path, stage2_run_dir: Path,
              bound_claim_ids: list[str], run_id_prefix: str,
              run_fn=subprocess.run) -> dict[str, str]:
    """Run the differential pipeline for every bound claim.

    Returns ``{claim_id: consistency_verdict}``; claims that fail to produce a
    parseable verdict map to ``binding_failed``.
    """
    if not bound_claim_ids:
        return {}
    proc = run_fn(
        [sys.executable, '-m', 'cli.stage3_multi',
         '--case-dir', str(case_dir), '--bindings-dir', str(bindings_dir),
         '--stage2-run', str(stage2_run_dir),
         '--run-id-prefix', run_id_prefix,
         '--claims', ','.join(bound_claim_ids)],
        capture_output=True, text=True, cwd=str(ROOT))
    verdicts: dict[str, str] = {}
    try:
        payload = json.loads(proc.stdout)
        for row in payload.get('claims', []):
            verdicts[row.get('claim_id')] = (
                row.get('consistency_verdict') or 'binding_failed')
    except ValueError:
        pass
    return verdicts


def derive_verdicts(*, claims: list[str], routed_verdicts: dict[str, str],
                    bound_claim_ids: list[str],
                    multi_verdicts: dict[str, str]) -> list[str]:
    """Map every claim to exactly one terminal verdict, in claim order."""
    verdicts = []
    for claim_id in claims:
        if claim_id in routed_verdicts:
            verdicts.append(routed_verdicts[claim_id])
        elif claim_id in bound_claim_ids:
            verdicts.append(multi_verdicts.get(claim_id, 'binding_failed'))
        else:
            verdicts.append('binding_failed')
    return verdicts


def verdict_counts(verdicts: list[str]) -> dict[str, int]:
    """Count the terminal verdicts the metrics path reports."""
    counts = {
        'reproduced': verdicts.count('violation_reproduced'),
        'compile_blocked': verdicts.count('compile_blocked'),
        'compile_error': verdicts.count('compile_error'),
        'not_dynamically_expressible': verdicts.count(
            'not_dynamically_expressible'),
        'reference_patch_required': verdicts.count('reference_patch_required'),
        'halt_witness_required': verdicts.count('halt_witness_required'),
    }
    return counts
