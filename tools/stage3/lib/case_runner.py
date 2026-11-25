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
from lib.binding import validate_binding
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


def _binding_scope_for_claim(*, case_dir: Path, claim_id: str,
                             binding_path: Path, src_dir: Path,
                             anchor: dict) -> dict:
    """Recover probe/patch visibility before building the observable IR."""
    from lib import binding_scope

    scope = binding_scope.load_binding_scope(case_dir, claim_id,
                                             src_dir=src_dir)
    return binding_scope.merge(scope, binding_scope.from_anchor(anchor))


def _compile_recipes(binding: dict, observable_ir: dict | None,
                     *, binding_path: Path | None = None,
                     src_dir: Path | None = None,
                     test_dir: Path | None = None,
                     safety_symbols: set[str] | None = None,
                     strict: bool = False) -> list[dict]:
    """Fill deterministic code observables and persist the compiled binding."""
    if not observable_ir:
        return []
    from lib.recipe_compiler import compile_binding
    from lib.binding_projection import project_binding

    compiled, changes = compile_binding(binding, observable_ir)

    def _projection_errors(trial: dict) -> list[str]:
        if src_dir is None:
            return []
        lint = lint_binding(
            trial, Path(src_dir), test_dir=Path(test_dir) if test_dir else None,
            strict=strict, safety_symbols=safety_symbols,
            observable_ir=observable_ir)
        return [
            f"{row.get('where')}: {row.get('message')}"
            for row in lint.get('problems') or []
            if row.get('severity') == 'error'
        ]

    projected, projection_changes = project_binding(
        compiled, observable_ir, validate=_projection_errors)
    changes.extend(projection_changes)
    compiled = projected
    if changes and binding_path is not None:
        binding_path.write_text(
            json.dumps(compiled, ensure_ascii=False, indent=2) + '\n')
    binding.clear()
    binding.update(compiled)
    return changes


def _feedback_row(claim_id: str, bindability: str, record: dict,
                  observable_ir: dict | None,
                  *, reference_patch: dict | None = None) -> dict:
    from lib import bindability_feedback

    return bindability_feedback.build(
        claim_id, bindability=bindability, binding_record=record,
        observable_ir=observable_ir, reference_patch=reference_patch)


def _reference_patch_binding(*, case_dir: Path, stage2_dir: Path,
                             claim_id: str, src_dir: Path,
                             spec: dict, anchor: dict, scope: dict) -> dict | None:
    """Build a minimal binding for a pre-validated cross-contract patch route.

    With ``case/patched`` the differential does not inject ``I`` into the
    business source, so asking the LLM to guess every P/I/V expression only
    burns repair rounds.  The probe still has to name the real PoC test.
    """
    from lib.binding import BINDING_SCHEMA, KINDS
    from lib.solidity_scan import poc_test_function_for_case

    contract = None
    for row in spec.get('claims') or []:
        if isinstance(row, dict) and row.get('claim_id') == claim_id:
            contract = row.get('binding_contract') or {}
            break
    if not isinstance(contract, dict):
        return None
    source = '\n'.join(path.read_text(errors='replace')
                       for path in sorted(src_dir.rglob('*.sol'))
                       if path.is_file())
    detected = poc_test_function_for_case(case_dir, source)
    probe_contract = scope.get('probe_contract') or (detected[0] if detected else None)
    probe_function = scope.get('probe_function') or (detected[1] if detected else None)
    if not probe_contract or not probe_function:
        return None
    patch_contract = scope.get('patch_contract') or anchor.get(
        'suggested_patch_contract') or probe_contract
    functions = scope.get('patch_functions') or []
    patch_function = functions[0] if functions else probe_function
    patch_file = 'Contract.sol'
    source_files = sorted(src_dir.glob('*.sol'))
    if source_files:
        patch_file = source_files[0].name
    entries = {}
    for row in contract.get('symbols') or []:
        if not isinstance(row, dict) or not row.get('appears_in'):
            continue
        checkpoint = str(row.get('checkpoint') or '').lower()
        checkpoint = ('before' if 'before' in checkpoint or 'input' in checkpoint
                      else 'after' if 'after' in checkpoint or 'post' in checkpoint
                      else 'input' if checkpoint else 'input')
        kind = str(row.get('binding_kind') or row.get('sort') or '')
        if kind not in KINDS:
            kind = 'boolean_predicate' if 'bool' in kind else 'numeric_value'
        entries[str(row['symbol'])] = {
            'kind': kind,
            'solidity_expr': 'UNBOUND',
            'checkpoint': checkpoint,
            'source': f'{patch_file}:{patch_function}',
        }
    return {
        'schema_version': BINDING_SCHEMA,
        'claim_id': claim_id,
        'bindings': entries,
        'patch': {
            'file': patch_file,
            'contract': patch_contract,
            'functions': [{'name': patch_function, 'file': patch_file}],
        },
        'probe': {'contract': probe_contract, 'exploit_test': probe_function,
                  'safety_test': None},
    }


def _try_reuse_binding(*, claim_id: str, binding_path: Path, case_dir: Path,
                       src_dir: Path, formal: dict, spec: dict,
                       strict: bool,
                       observable_ir: dict | None = None) -> tuple[dict, bool]:
    """Validate an on-disk binding before reusing it.

    A binding produced against an older stage-2 spec must not be silently
    reused: it can reference symbols/contracts that no longer exist in the
    current formalization and would only surface later as ``binding_error`` /
    ``compile_error`` inside ``forge``.  Reject it as ``stale`` when either the
    structural symbol coverage no longer matches the current spec
    (``validate_binding``) or the source-level lint fails.
    """
    record = {
        'claim_id': claim_id, 'status': 'reused', 'verdict': None,
        'bindability': 'reused', 'rounds_used': 0, 'unbound': [],
        'binding': str(binding_path), 'detail': None,
    }
    try:
        binding = json.loads(binding_path.read_text())
        safety_symbols = safety_symbols_for_claim(formal, claim_id)
        recipe_changes = _compile_recipes(
            binding, observable_ir, binding_path=binding_path,
            src_dir=src_dir, test_dir=case_dir / 'test',
            safety_symbols=safety_symbols, strict=strict)
        validate_binding(binding, spec)
        lint = lint_binding(binding, src_dir, test_dir=case_dir / 'test',
                            strict=strict, safety_symbols=safety_symbols,
                            observable_ir=observable_ir)
        record['recipe_compile'] = recipe_changes
    except (OSError, ValueError, SpecError) as exc:
        record['status'] = 'stale'
        record['detail'] = f'invalid binding file: {exc}'
        return record, False
    if lint['summary']['errors']:
        problems = [f"{p['where']}: {p['message']}" for p in lint['problems']]
        record['status'] = 'stale'
        record['detail'] = '; '.join(problems[:6])
        return record, False
    return record, True


def _build_observable_ir(stage2_dir: Path, claim_id: str,
                         src_dir: Path,
                         scope: dict | None = None
                         ) -> tuple[dict | None, str | None]:
    """Build the observable IR without hiding source/scan failures.

    Returning ``None`` silently made a broken IR indistinguishable from a
    claim with no candidates.  Keep the optional behaviour for legacy cases,
    but expose the error so the binding record can fail closed and be triaged.
    """
    try:
        from lib.observable_ir import build_contract
        return build_contract(stage2_dir, claim_id, src_dir,
                              **(scope or {})), None
    except Exception as exc:
        return None, f'{type(exc).__name__}: {exc}'


def bind_claims(*, case_dir: Path, stage2_dir: Path, src_dir: Path,
                claims: list[str], formal: dict, spec: dict,
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
    feedback_rows: list[dict] = []

    for claim_id in claims:
        bindability = bindability_by_claim[claim_id]
        anchor = anchor_by_claim.get(claim_id, {})
        binding_path = bindings_dir / f'{claim_id}.json'
        scope = _binding_scope_for_claim(
            case_dir=case_dir, claim_id=claim_id, binding_path=binding_path,
            src_dir=src_dir, anchor=anchor)
        observable_ir, observable_ir_error = _build_observable_ir(
            stage2_dir, claim_id, src_dir, scope=scope)

        reference_plan = None
        if apply_ceiling and bindability == 'multi_contract':
            from lib import reference_patch

            if reference_patch.has_reference_patch(case_dir):
                target_functions = scope.get('patch_functions') or []
                reference_plan = reference_patch.build_reference_patch(
                    case_dir, dry_run=True,
                    target_function=(target_functions[0]
                                     if target_functions else None))
                if reference_plan.get('accepted') and not binding_path.is_file():
                    reference_binding = _reference_patch_binding(
                        case_dir=case_dir, stage2_dir=stage2_dir,
                        claim_id=claim_id, src_dir=src_dir, spec=spec,
                        anchor=anchor, scope=scope)
                    if reference_binding is not None:
                        try:
                            validate_binding(reference_binding, spec)
                        except SpecError:
                            reference_binding = None
                    if reference_binding is not None:
                        binding_path.write_text(json.dumps(
                            reference_binding, ensure_ascii=False,
                            indent=2) + '\n')
                        records[claim_id] = {
                            'claim_id': claim_id, 'status': 'reference_route',
                            'verdict': None, 'bindability': bindability,
                            'rounds_used': 0, 'unbound': [],
                            'binding': str(binding_path), 'detail': None,
                            'observable_ir_error': observable_ir_error,
                            'binding_scope': scope,
                            'reference_patch': reference_plan,
                        }
                        bound_claim_ids.append(claim_id)
                        feedback_rows.append(_feedback_row(
                            claim_id, bindability, records[claim_id],
                            observable_ir, reference_patch=reference_plan))
                        continue

        # An existing binding wins over ceiling routing only when it still
        # lints against the current stage-2 spec; a stale binding is rejected
        # loudly (``binding_stale``) instead of being re-run into forge errors.
        if reuse and binding_path.is_file():
            record, accepted = _try_reuse_binding(
                claim_id=claim_id, binding_path=binding_path, case_dir=case_dir,
                src_dir=src_dir, formal=formal, spec=spec, strict=strict,
                observable_ir=observable_ir)
            record['observable_ir_error'] = observable_ir_error
            record['binding_scope'] = scope
            records[claim_id] = record
            if accepted:
                bound_claim_ids.append(claim_id)
            else:
                failed.append({'claim': claim_id, 'reason': 'binding_stale',
                               'rounds': 0, 'detail': record['detail']})
            feedback_rows.append(_feedback_row(
                claim_id, bindability, record, observable_ir,
                reference_patch=reference_plan))
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
                'observable_ir_error': observable_ir_error,
                'binding_scope': scope,
            }
            feedback_rows.append(_feedback_row(
                claim_id, bindability, records[claim_id], observable_ir,
                reference_patch=reference_plan))
            continue

        safety_symbols = safety_symbols_for_claim(formal, claim_id)
        hint = None
        accepted = False
        unbound: list[str] = []
        rounds_used = 0
        recipe_compile: list[dict] = []
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
            recipe_compile = _compile_recipes(
                binding, observable_ir, binding_path=written,
                src_dir=src_dir, test_dir=case_dir / 'test',
                safety_symbols=safety_symbols, strict=strict)
            lint = lint_binding(binding, src_dir, test_dir=case_dir / 'test',
                                strict=strict, safety_symbols=safety_symbols,
                                observable_ir=observable_ir)
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
                'observable_ir_error': observable_ir_error,
                'binding_scope': scope,
                'recipe_compile': recipe_compile,
            }
        else:
            terminal = None
            if bindability == 'multi_contract':
                terminal = 'reference_patch_required'
            elif (bindability == 'no_anchor'
                  and anchor.get('anchor_observability') == 'low'):
                terminal = 'not_dynamically_expressible'
            if terminal is not None:
                routed_verdicts[claim_id] = terminal
                records[claim_id] = {
                    'claim_id': claim_id, 'status': 'routed',
                    'verdict': terminal, 'bindability': bindability,
                    'rounds_used': rounds_used, 'unbound': unbound,
                    'binding': None,
                    'observable_ir_error': observable_ir_error,
                    'binding_scope': scope,
                    'detail': ('binding exhausted; routed deterministically: '
                               + hint),
                }
            else:
                failed.append({'claim': claim_id,
                               'reason': 'binding_exhausted',
                               'rounds': max_rounds, 'detail': hint})
                records[claim_id] = {
                    'claim_id': claim_id, 'status': 'failed',
                    'verdict': None, 'bindability': bindability,
                    'rounds_used': rounds_used, 'unbound': unbound,
                    'binding': None, 'detail': hint,
                    'observable_ir_error': observable_ir_error,
                    'binding_scope': scope,
                }

        feedback_rows.append(_feedback_row(
            claim_id, bindability, records[claim_id], observable_ir,
            reference_patch=reference_plan))

    bound_claim_ids = list(dict.fromkeys(bound_claim_ids))
    from lib import bindability_feedback
    bindability_feedback.write(case_dir, feedback_rows)
    return {
        'records': records,
        'bound_claim_ids': bound_claim_ids,
        'routed_verdicts': routed_verdicts,
        'bindability_by_claim': bindability_by_claim,
        'failed': failed,
        'unobservable_symbols': sorted(set(unobservable_symbols)),
        'bindability_feedback': bindability_feedback.build_index(feedback_rows),
    }


def run_multi(*, case_dir: Path, bindings_dir: Path, stage2_run_dir: Path,
              bound_claim_ids: list[str], run_id_prefix: str,
              run_fn=subprocess.run) -> dict:
    """Run the differential pipeline for every bound claim.

    Returns ``{'verdicts': {claim_id: consistency_verdict},
    'reference_patch_used': {claim_id: bool}}``. Claims that fail to produce a
    parseable verdict map to ``binding_failed``. ``reference_patch_used`` is
    true only when the claim was reproduced through the ``case/patched`` M1
    route, so callers can separate automatic recall from reference-patch recall.
    """
    if not bound_claim_ids:
        return {'verdicts': {}, 'reference_patch_used': {}}
    proc = run_fn(
        [sys.executable, '-m', 'cli.stage3_multi',
         '--case-dir', str(case_dir), '--bindings-dir', str(bindings_dir),
         '--stage2-run', str(stage2_run_dir),
         '--run-id-prefix', run_id_prefix,
         '--claims', ','.join(bound_claim_ids),
         '--claim-top-k', '0'],
        capture_output=True, text=True, cwd=str(ROOT))
    verdicts: dict[str, str] = {}
    reference_patch_used: dict[str, bool] = {}
    try:
        payload = json.loads(proc.stdout)
        for row in payload.get('claims', []):
            claim_id = row.get('claim_id')
            verdicts[claim_id] = (
                row.get('consistency_verdict') or 'binding_failed')
            if row.get('reference_patch_used'):
                reference_patch_used[claim_id] = True
    except ValueError:
        pass
    return {'verdicts': verdicts, 'reference_patch_used': reference_patch_used}


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
