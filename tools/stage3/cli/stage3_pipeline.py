#!/usr/bin/env python3
"""Stage-3 single-case pipeline: binding -> patch -> forge -> differential -> verdict.

Run with cwd = tools/stage3:
    python -m cli.stage3_pipeline --case-dir cases/smoke_vault
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

from lib.spec_loader import (SpecError, load_stage2_run, required_symbols,
                             precondition_symbols_for_claim,
                             safety_symbols_for_claim)
from lib.binding import build_feedback, load_binding, validate_binding
from lib.binding_normalize import normalize_binding
from lib.binding_validate import lint_binding
from lib.expressibility import classify as classify_expressibility
from lib.routing import classify_route
from lib.patch import (build_effect_project, build_negative_project,
                       build_projects,
                        injection_selfdestruct_targets,
                        relocate_before_snapshots,
                        relocate_injection_to_test,
                        _is_revert_expected_test,
                        _is_revert_vulnerability_test)
from lib.reference_patch import (build_reference_patch,
                                 has_reference_patch,
                                 ReferencePatchError)
from lib.forge_runner import first_failure_reason, run_forge_safe, test_result
from lib.differential import compute_queries
from lib.verdict import submit
from lib.compile_retry import error_identifiers, failure_classes
from lib import rebind
from lib import unbound_semantics
from lib import weak_invariant
from lib import execution_contract
from lib import execution_gate
from lib import test_monitor
from lib import stage2_restate
from lib import stage2_contract
from lib import source_ir as source_ir_lib
from lib import witness_router
from lib import witness_protocol
from lib import artifact_fingerprint
from lib import mechanism_ceiling
from lib import bindability_feedback
from lib import binding_scope

ROOT = Path(__file__).resolve().parents[1]  # tools/stage3
ARTIFACT_FINGERPRINT = None


def _decide_stage2(contract: dict, mode: str) -> dict:
    if mode == 'strict':
        return stage2_contract.decide(contract, strict=True)
    if mode == 'aplus':
        return stage2_contract.decide(contract, mode='aplus')
    return stage2_contract.decide(contract)


def fallback_bindability_feedback(case_dir: Path, claim_id: str,
                                  stage2: dict, binding: dict) -> dict | None:
    """Recover a bindability request for runs that bypassed ``bind_claims``.

    The dev regression runner uses pre-existing bindings and therefore has no
    ``bindability-feedback.json``.  An UNBOUND P/I symbol is still a failed
    Stage-2 -> Stage-3 handoff and must be sent back for restatement instead
    of consuming a forge run.  Reference-patch routes legitimately leave I/V
    unbound and are excluded.
    """
    if has_reference_patch(case_dir):
        return None
    invariant_symbols = (safety_symbols_for_claim(stage2['formal'], claim_id)
                         | precondition_symbols_for_claim(
                             stage2['formal'], claim_id))
    unbound = [
        str(symbol) for symbol, entry in (binding.get('bindings') or {}).items()
        if isinstance(entry, dict)
        and str(entry.get('solidity_expr') or '').strip() == 'UNBOUND'
        and symbol in invariant_symbols]
    if not unbound:
        return None
    return bindability_feedback.build(
        claim_id, binding_record={'status': 'bound',
                                  'bindability': 'unknown',
                                  'unbound': unbound})


def write_json(path: Path, value):
    if (path.name == 'stage3-summary.json'
            and isinstance(value, dict)
            and ARTIFACT_FINGERPRINT is not None):
        value.setdefault('artifact_fingerprint', ARTIFACT_FINGERPRINT)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def independent_effect_gate(*, verdict: dict, reference_patch_used: bool,
                            revert_expected: bool, effect_independent: bool,
                            queries: dict | None,
                            witness: dict | None) -> dict | None:
    """Gate a reproduced claim on an independent effect witness.

    The revert-witness route derives its raw verdict from the original/patched
    differential.  That differential is not an independent hazard witness, so
    it must pass the same effect check as the assert-based route.  Reference
    patches remain exempt because the patch itself is the adjudication.
    """
    if (verdict.get('consistency_verdict') != 'violation_reproduced'
            or reference_patch_used):
        return None
    witness = witness if isinstance(witness, dict) else {}
    queries = queries if isinstance(queries, dict) else {}
    effect_witnessed = (bool(witness.get('effect_witnessed'))
                        or queries.get('P_and_T_and_V') == 'sat')
    if not effect_independent:
        return {
            'code': 'EFFECT_NOT_INDEPENDENT',
            'verdict': 'weak_effect_not_independent',
            'reason': ('V shares only the I observables and is not a '
                       'logical negation; the effect is not independent'),
        }
    if not effect_witnessed:
        return {
            'code': ('REVERT_EFFECT_NOT_WITNESSED' if revert_expected
                     else 'EFFECT_NOT_WITNESSED'),
            'verdict': 'effect_not_witnessed',
            'reason': ('the revert-witness differential passed, but no '
                       'independent effect probe witnessed V'
                       if revert_expected else
                       'the I probe failed, but the independently built V '
                       'probe did not observe the claimed effect'),
        }
    return None


def stage2_blocked_summary(*, run_id: str, case_dir: Path, stage2_src: Path,
                           claim_id: str, probe: dict, gate: dict,
                           restatement: dict, contract: dict) -> dict:
    """Build the fail-closed summary for a blocking Stage-2 contract gate."""
    category = gate['category']
    return {
        'schema_version': 'stage3-run-summary/1',
        'case': str(case_dir),
        'run_id': run_id,
        'stage2_run': str(stage2_src),
        'claim_id': claim_id,
        'probe': probe,
        'forge': {'exploit': {'original': None, 'patched': None},
                  'safety': None},
        'code_query_results': None,
        'compile_retry': None,
        'expressibility': None,
        'consistency_verdict': category,
        'witness': witness_protocol.unavailable(
            claim_id, category, gate['reason']),
        'stage2_contract_gate': gate,
        'stage2_restatement': restatement,
        'stage2_final_contract': contract,
        'execution_contract': {'stage2_contract': contract},
    }


def _load_formalization_contract(stage2_dir: Path, claim_id: str) -> dict:
    return stage2_contract.load(stage2_dir, claim_id)


def derive_run_id(case_dir: Path) -> str:
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    return f'{case_dir.name}_{stamp}'


def _downgrade_via_ir(project_dir: Path) -> bool:
    """Disable ``via_ir`` in a project's foundry.toml.

    Flattened code4rena slices are large and frequently hit ``stack too deep``
    under ``via_ir = true``; recompiling with the legacy codegen removes the
    constraint. Returns True when the config was rewritten.
    """
    toml = project_dir / 'foundry.toml'
    if not toml.is_file():
        return False
    text = toml.read_text()
    if 'via_ir' not in text:
        return False
    text = text.replace('via_ir = true', 'via_ir = false')
    toml.write_text(text)
    return True


_STACK_TOO_DEEP = 'too deep in the stack'


def _retry_without_via_ir(run: dict, project_dir: Path) -> dict:
    """Re-run a failed forge build with ``via_ir`` disabled on stack overflow."""
    if run.get('ok') or _STACK_TOO_DEEP not in (run.get('compile_error') or ''):
        return run
    if _downgrade_via_ir(project_dir):
        return run_forge_safe(project_dir)
    return run


def _enable_via_ir(project_dir: Path) -> bool:
    """Enable ``via_ir = true`` in a project's foundry.toml.

    The minimal default config does not set ``via_ir``, so the legacy codegen
    is used; when that hits ``stack too deep`` the IR pipeline is the standard
    remedy and must be tried before giving up on the project.
    """
    toml = project_dir / 'foundry.toml'
    if not toml.is_file():
        return False
    text = toml.read_text()
    if 'via_ir = false' in text:
        text = text.replace('via_ir = false', 'via_ir = true')
    elif 'via_ir' not in text:
        text = text.rstrip() + '\nvia_ir = true\n'
    else:
        return False
    toml.write_text(text)
    return True


def _retry_stack_too_deep(run: dict, project_dir: Path) -> dict:
    """Try the IR pipeline when the legacy codegen reports ``stack too deep``.

    Inverse of ``_retry_without_via_ir``: after downgrade attempts have been
    exhausted, enabling ``via_ir`` is the deterministic way to lift the stack
    limit without removing snapshot locals (which would silently weaken the
    invariant).
    """
    if run.get('ok') or _STACK_TOO_DEEP not in (run.get('compile_error') or ''):
        return run
    if _enable_via_ir(project_dir):
        retried = run_forge_safe(project_dir)
        if retried.get('ok') or _STACK_TOO_DEEP not in (retried.get('compile_error') or ''):
            return retried
        _downgrade_via_ir(project_dir)
    return run


def partition_unbound(binding: dict, invariant_symbols: set[str]) -> tuple[list[str], list[str], list[str]]:
    """Return ``(unbound, invariant_unbound, effect_unbound)`` for a binding.

    P/I symbols must all be bound for the invariant probe; V-only UNBOUND
    symbols only disable the optional effect probe and must not block the
    differential. Kept as a pure helper so the routing decision is testable.
    """
    unbound = sorted(
        name for name, entry in (binding.get('bindings') or {}).items()
        if isinstance(entry, dict)
        and str(entry.get('solidity_expr') or '').strip() == 'UNBOUND')
    invariant_unbound = sorted(
        name for name in unbound if name in invariant_symbols)
    effect_unbound = sorted(
        name for name in unbound if name not in invariant_symbols)
    return unbound, invariant_unbound, effect_unbound


def _try_test_monitor(*, case_dir: Path, run_dir: Path, binding: dict,
                       stage2: dict, safety_symbols: set[str],
                       probe: dict) -> tuple[dict | None, dict | None, dict]:
    """Build and compile-check the test-level monitor route.

    The monitor is only an observation-point relocation.  It is accepted when
    the resulting binding is source-expressible and the patched project
    compiles; otherwise the caller keeps the reference-patch route.
    """
    candidate, record = test_monitor.build_monitor_binding(binding, case_dir)
    if candidate is None:
        return None, None, record
    try:
        expression = classify_expressibility(
            candidate, case_dir / 'src', test_dir=case_dir / 'test',
            strict=True, safety_symbols=safety_symbols)
    except Exception as exc:
        record.update({'status': 'rejected', 'reason': str(exc)})
        return None, None, record
    record['expressibility'] = expression
    if not expression.get('dynamically_expressible'):
        record.update({
            'status': 'rejected',
            'reason': 'test-level monitor still has an unobservable expression',
        })
        return None, None, record
    try:
        monitor_dir = run_dir / 'monitor'
        build_projects(case_dir, monitor_dir, binding=candidate,
                       spec=stage2['spec'], formal=stage2['formal'])
        patched_run = run_forge_safe(monitor_dir / 'patched')
        patched_run = _retry_without_via_ir(patched_run, monitor_dir / 'patched')
        patched_run = _retry_stack_too_deep(patched_run, monitor_dir / 'patched')
    except Exception as exc:
        record.update({'status': 'rejected', 'reason': str(exc)})
        return None, None, record
    record['compile_ok'] = bool(patched_run.get('ok'))
    if not patched_run.get('ok'):
        record.update({
            'status': 'rejected',
            'reason': 'monitor project did not compile',
            'compile_error': str(patched_run.get('compile_error') or '')[:2000],
        })
        return None, None, record
    record['status'] = 'accepted'
    return candidate, expression, record


def main(argv=None):
    global ARTIFACT_FINGERPRINT
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case-dir', type=Path, required=True)
    parser.add_argument('--run-id', type=str)
    parser.add_argument('--stage2-run', type=Path,
                        help='defaults to <case-dir>/stage2_run')
    parser.add_argument('--binding', type=Path,
                        help='defaults to <case-dir>/binding.json; '
                             'override for multi-claim runs')
    parser.add_argument('--lint', action='store_true',
                        help='run source-aware binding lint and emit binding-lint.json')
    parser.add_argument('--strict-lint', action='store_true',
                        help='like --lint but fail on warnings as well as errors')
    parser.add_argument('--stage2-gate-mode', choices=('legacy', 'strict', 'aplus'),
                        default='aplus',
                        help='A+ keeps hard checkpoints/observability/independence '
                             'but records snapshot/review codes as quality labels')
    args = parser.parse_args(argv)

    case_dir = args.case_dir.resolve()
    stage2_src = (args.stage2_run or case_dir / 'stage2_run').resolve()
    binding_path = (args.binding or case_dir / 'binding.json').resolve()
    run_id = args.run_id or derive_run_id(case_dir)
    run_dir = (ROOT / 'runs' / run_id).resolve()

    if run_dir.exists():
        raise SystemExit(f'run directory already exists: {run_dir}\n'
                         'choose a fresh --run-id to keep replay discipline')

    try:
        stage2 = load_stage2_run(stage2_src)
        binding = load_binding(binding_path)
        claim_id, entries = validate_binding(binding, stage2['spec'])
    except SpecError as exc:
        raise SystemExit(f'input error: {exc}')

    probe = binding.get('probe') or {}
    run_dir.mkdir(parents=True)
    ARTIFACT_FINGERPRINT = artifact_fingerprint.write(
        run_dir / 'artifact-fingerprint.json', stage2_src, binding_path)
    artifact_fingerprint.write_run_manifest(
        run_dir / 'run-manifest.json',
        run_id=run_id,
        created_at=datetime.now(timezone.utc).isoformat(timespec='milliseconds'),
        stage2_dir=stage2_src,
        binding_path=binding_path,
        case_dir=case_dir,
        claim_id=claim_id,
        protocol=ARTIFACT_FINGERPRINT['mainline_protocol'])

    # P2: derive and verify one deterministic invariant restatement, then
    # rebuild the claim contract.  Stage 3 only consumes this final contract;
    # an unresolved or rejected restatement keeps the original blocking route.
    # Trusted negative labels are read here, before the final contract is
    # built, so a known-invalid claim cannot enter forge on an unverified
    # restatement.  Positive claims and accepted restatements are unaffected.
    trusted_label = execution_gate.load_trusted_label(
        case_dir, claim_id, stage2_src)
    formalization_contract = _load_formalization_contract(stage2_src, claim_id)
    declaration = next(
        (row for row in stage2['spec'].get('claims', [])
         if isinstance(row, dict) and row.get('claim_id') == claim_id), {})
    observability = stage2_restate.load_observability(stage2_src, claim_id)
    feedback_index = bindability_feedback.load(case_dir)
    binding_feedback = feedback_index.get(claim_id)
    original_formal = stage2['formal']
    restatement = stage2_restate.restate_claim(
        stage2['formal'], claim_id,
        declaration=declaration,
        formalization_contract=formalization_contract,
        observability=observability)
    write_json(run_dir / 'stage2-restatement.json', restatement)
    if restatement.get('status') == 'restated':
        stage2 = {**stage2,
                  'formal': stage2_restate.apply(stage2['formal'], restatement)}
    final_contract = stage2_restate.build_final_contract(
        stage2['formal'], restatement,
        original_contract=formalization_contract,
        observability=observability,
        declaration=declaration,
        trusted_label=trusted_label,
        binding_feedback=binding_feedback)
    write_json(run_dir / 'stage2-restated-contract.json', final_contract)
    stage2_gate = _decide_stage2(final_contract, args.stage2_gate_mode)
    write_json(run_dir / 'stage2-contract-gate.json', stage2_gate)
    if stage2_gate['blocking']:
        summary = stage2_blocked_summary(
            run_id=run_id, case_dir=case_dir, stage2_src=stage2_src,
            claim_id=claim_id, probe=probe, gate=stage2_gate,
            restatement=restatement, contract=final_contract)
        write_json(run_dir / 'stage3-summary.json', summary)
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0

    binding, normalization_changes = normalize_binding(
        binding, case_dir / 'src', test_dir=case_dir / 'test', strict=True)
    if normalization_changes:
        print(f'binding-normalize: {"; ".join(normalization_changes)}',
              file=sys.stderr)
    binding, qualify_changes = rebind.qualify_unqualified_calls(
        binding, rebind.load_source(case_dir / 'src'))
    if qualify_changes:
        print(f'binding-call-qualify: {"; ".join(qualify_changes)}',
              file=sys.stderr)
        binding, call_normalization = normalize_binding(
            binding, case_dir / 'src', test_dir=case_dir / 'test', strict=True)
        if call_normalization:
            print(f'binding-call-normalize: {"; ".join(call_normalization)}',
                  file=sys.stderr)
    binding, rebind_changes = rebind.rebind_binding(
        binding, rebind.load_source(case_dir / 'src'))
    if rebind_changes:
        print(f'binding-rebind: {"; ".join(rebind_changes)}', file=sys.stderr)
    binding, bool_coerce_changes = rebind.coerce_boolean_predicates(
        binding, rebind.load_source(case_dir / 'src'))
    if bool_coerce_changes:
        print(f'binding-bool-coerce: {"; ".join(bool_coerce_changes)}',
              file=sys.stderr)
    from lib.spec_loader import claim_binding_contract
    binding, complement_changes = rebind.complete_complementary_bindings(
        binding, claim_binding_contract(stage2['spec'], claim_id))
    if complement_changes:
        print(f'binding-complement: {"; ".join(complement_changes)}',
              file=sys.stderr)
    binding, name_changes = rebind.complete_unbound_by_name(
        binding, claim_binding_contract(stage2['spec'], claim_id),
        rebind.parse_source_signatures(rebind.load_source(case_dir / 'src')))
    if name_changes:
        print(f'binding-name: {"; ".join(name_changes)}', file=sys.stderr)

    # P7: compile deterministic recipes against the real patch target before
    # semantic UNBOUND recovery.  The binding may have been produced by an
    # older run whose IR used the PoC probe as the visibility frame.
    patch_scope = binding_scope.from_binding(case_dir, binding)
    recipe_changes = []
    try:
        from lib import observable_ir as observable_ir_lib
        from lib.recipe_compiler import compile_binding

        runtime_ir = observable_ir_lib.build_contract(
            stage2_src, claim_id, case_dir / 'src', **patch_scope)
        source_index = source_ir_lib.build(
            case_dir / 'src', test_dir=case_dir / 'test')
        runtime_ir = source_ir_lib.annotate_observable_ir(
            runtime_ir, source_index)
        write_json(run_dir / 'source-ir.json', source_index)
        binding, recipe_changes = compile_binding(binding, runtime_ir)
        write_json(run_dir / 'observable-ir.json', runtime_ir)
    except Exception as exc:
        recipe_changes = []
        write_json(run_dir / 'observable-ir-error.json', {
            'error': f'{type(exc).__name__}: {exc}',
        })
    if recipe_changes:
        write_json(run_dir / 'recipe-compile.json', {
            'schema_version': 'stage3-recipe-compile-report/1',
            'changes': recipe_changes,
        })

    # Semantic UNBOUND recovery: deterministic, source-grounded repairs only.
    # The report is persisted even when nothing resolves so the verdict loop
    # can route each remaining symbol instead of rebinding blindly.
    binding_contract = claim_binding_contract(stage2['spec'], claim_id)
    binding, semantic_changes, unbound_report = \
        unbound_semantics.resolve_unbound(
            binding, binding_contract, rebind.load_source(case_dir / 'src'),
            injection_contract=(patch_scope.get('patch_contract')
                                or probe.get('contract')))
    if semantic_changes:
        print(f'binding-semantic-unbound: {"; ".join(semantic_changes)}',
              file=sys.stderr)
        binding, semantic_normalization = normalize_binding(
            binding, case_dir / 'src', test_dir=case_dir / 'test', strict=True)
        if semantic_normalization:
            print(f'binding-semantic-normalize: '
                  f'{"; ".join(semantic_normalization)}', file=sys.stderr)
    write_json(run_dir / 'unbound-semantics.json', unbound_report)

    # P0: derive fallback feedback only after deterministic repair.  Reading
    # raw binding UNBOUND symbols here used to block claims whose P/I facts
    # were already recovered by rebind/recipe/unbound resolution.  Case-level
    # feedback supplied by the bind stage remains authoritative and is kept
    # unchanged.
    if binding_feedback is None:
        binding_feedback = fallback_bindability_feedback(
            case_dir, claim_id, {'formal': original_formal}, binding)
        if binding_feedback:
            write_json(run_dir / 'bindability-feedback.json', binding_feedback)
        final_contract = stage2_restate.build_final_contract(
            stage2['formal'], restatement,
            original_contract=formalization_contract,
            observability=observability,
            declaration=declaration,
            trusted_label=trusted_label,
            binding_feedback=binding_feedback)
        write_json(run_dir / 'stage2-restated-contract.json', final_contract)
        stage2_gate = _decide_stage2(final_contract, args.stage2_gate_mode)
        write_json(run_dir / 'stage2-contract-gate.json', stage2_gate)
        if stage2_gate['blocking']:
            summary = stage2_blocked_summary(
                run_id=run_id, case_dir=case_dir, stage2_src=stage2_src,
                claim_id=claim_id, probe=probe, gate=stage2_gate,
                restatement=restatement, contract=final_contract)
            write_json(run_dir / 'stage3-summary.json', summary)
            print(json.dumps(summary, ensure_ascii=False, indent=2))
            return 0

    weak_risk = weak_invariant.diagnose(
        stage2['formal'], claim_id, binding, declaration)
    write_json(run_dir / 'weak-invariant-risk.json', weak_risk)
    weak_gate = weak_invariant.gate(weak_risk)
    write_json(run_dir / 'weak-invariant-gate.json', weak_gate)
    if weak_gate['blocking']:
        summary = {
            'schema_version': 'stage3-run-summary/1',
            'case': str(case_dir),
            'run_id': run_id,
            'stage2_run': str(stage2_src),
            'claim_id': claim_id,
            'probe': probe,
            'forge': {'exploit': {'original': None, 'patched': None},
                      'effect': None, 'safety': None},
            'code_query_results': None,
            'compile_retry': None,
            'expressibility': None,
            'weak_invariant_risk': weak_risk,
            'weak_invariant_gate': weak_gate,
            'consistency_verdict': weak_gate['category'],
            'witness': witness_protocol.unavailable(
                claim_id, weak_gate['category'], weak_gate['reason']),
            'execution_contract': {
                'weak_invariant': weak_risk,
            },
        }
        write_json(run_dir / 'stage3-summary.json', summary)
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0
    # Adjudication remains separate from execution: post-forge evidence still
    # decides whether a trusted-negative claim is a real false positive.  The
    # Stage-2 hard gate above only blocks unverified restatements.
    preflight_gate = execution_gate.preflight(
        stage2['formal'], binding, claim_id)
    write_json(run_dir / 'execution-preflight.json', preflight_gate)
    contract = execution_contract.build(
        stage2['formal'], binding, claim_id, weak_invariant=weak_risk,
        execution_gate=preflight_gate,
        formalization_contract=final_contract)
    write_json(run_dir / 'execution-contract.json', contract)

    if preflight_gate['status'] == 'reject':
        summary = {
            'schema_version': 'stage3-run-summary/1',
            'case': str(case_dir),
            'run_id': run_id,
            'stage2_run': str(stage2_src),
            'claim_id': claim_id,
            'probe': probe,
            'forge': {'exploit': {'original': None, 'patched': None},
                      'effect': None, 'safety': None},
            'code_query_results': None,
            'compile_retry': None,
            'expressibility': None,
            'execution_gate': preflight_gate,
            'preflight_execution_gate': preflight_gate,
            'execution_contract': contract,
            'consistency_verdict': (preflight_gate.get('category')
                                    or 'binding_error'),
            'witness': witness_protocol.unavailable(
                claim_id, 'execution_preflight_rejected',
                'deterministic structural preflight rejected the claim before forge'),
            'execution_gate_rejection': {
                'category': preflight_gate.get('category'),
                'codes': preflight_gate.get('codes'),
                'reason': ('deterministic structural preflight rejected the '
                           'claim before forge: vacuous or constant observables'),
            },
        }
        write_json(run_dir / 'stage3-summary.json', summary)
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0

    entries = binding['bindings']
    reference_patch_mode = has_reference_patch(case_dir)
    revert_expected = False
    revert_vulnerability = False
    _probe = binding.get('probe') or {}
    if _probe.get('exploit_test'):
        _patch = binding.get('patch') or {}
        _pf = _patch.get('file') if isinstance(_patch, dict) else None
        _src = case_dir / 'src' / _pf if _pf else None
        if _src is not None and _src.is_file():
            source_text = _src.read_text()
            revert_expected = _is_revert_expected_test(
                source_text, _probe['exploit_test'],
                _probe.get('contract'))
            revert_vulnerability = _is_revert_vulnerability_test(
                source_text, _probe['exploit_test'],
                _probe.get('contract'))
    safety_symbols = safety_symbols_for_claim(stage2['formal'], claim_id)
    invariant_symbols = safety_symbols | precondition_symbols_for_claim(
        stage2['formal'], claim_id)
    # Only the invariant probe (P -> I) needs every P/I symbol bound to reach a
    # dynamic verdict. V-side UNBOUND symbols only disable the optional effect
    # probe; short-circuiting on them would turn recoverable cases into
    # ``partial_binding`` even though the assert(!P || I) differential can run.
    unbound_symbols, invariant_unbound, effect_unbound = partition_unbound(
        binding, invariant_symbols)
    if invariant_unbound and not revert_expected and not reference_patch_mode:
        summary = {
            'schema_version': 'stage3-run-summary/1',
            'case': str(case_dir),
            'run_id': run_id,
            'stage2_run': str(stage2_src),
            'claim_id': claim_id,
            'probe': probe,
            'forge': {'exploit': {'original': None, 'patched': None},
                      'safety': None},
            'code_query_results': None,
            'compile_retry': None,
            'expressibility': None,
            'consistency_verdict': 'partial_binding',
            'witness': witness_protocol.classify(
                claim_id, original_result=None, patched_result=None,
                invariant_unbound=invariant_unbound),
            'partial_binding': {
                'unbound_symbols': unbound_symbols,
                'invariant_unbound_symbols': invariant_unbound,
                'effect_unbound_symbols': effect_unbound,
                'unbound_buckets': unbound_report.get('counts'),
                'unbound_route_suggestion': unbound_report.get(
                    'route_suggestion'),
                'semantic_unresolved_buckets': unbound_report.get(
                    'unresolved_buckets'),
                'semantic_terminal_unresolved': unbound_report.get(
                    'terminal_unresolved'),
                'weak_invariant_risk': weak_risk,
                'execution_contract': contract,
                'reason': ('binding is incomplete: these required P/I symbols '
                           'have solidity_expr=UNBOUND and must be rebound '
                           'before forge can produce a dynamic verdict'),
                'repair_hint': 'rerun cli.stage3_binding_llm or '
                               'cli.stage3_verdict_loop for this claim',
            },
        }
        write_json(run_dir / 'stage3-summary.json', summary)
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0

    expressibility = classify_expressibility(binding, case_dir / 'src',
                                             test_dir=case_dir / 'test',
                                             strict=True,
                                             safety_symbols=safety_symbols)
    if revert_expected or reference_patch_mode:
        # The revert-witness / reference-patch routes do not inject I/V as an
        # assert, so cross-contract / unobservable / binding-error
        # classifications on I/V must not gate them.
        expressibility = {
            'schema_version': 'stage3-expressibility/1',
            'expressibility': 'expressible',
            'reference_patch_required': False,
            'dynamically_expressible': True,
            'expressible_symbols': [],
            'cross_contract_symbols': [],
            'unobservable_symbols': [],
            'other_problems': [],
        }
    if (not revert_expected
            and not reference_patch_mode
            and not expressibility['dynamically_expressible']
            and expressibility['expressibility'] == 'binding_error'):
        summary = {
            'schema_version': 'stage3-run-summary/1',
            'case': str(case_dir),
            'run_id': run_id,
            'stage2_run': str(stage2_src),
            'claim_id': claim_id,
            'probe': probe,
            'forge': {'exploit': {'original': None, 'patched': None},
                      'safety': None},
            'code_query_results': None,
            'compile_retry': None,
            'expressibility': expressibility,
            'consistency_verdict': 'binding_error',
            'witness': witness_protocol.unavailable(
                claim_id, 'binding_structural_error',
                'the binding has a structural error that makes the invariant '
                'vacuous or unobservable'),
            'binding_error': {
                'reason': ('the binding has a structural error that would make '
                           'the injected invariant vacuous or unobservable; '
                           'for example a constant safety binding or an '
                           'unknown identifier'),
                'other_problems': expressibility['other_problems'],
            },
        }
        write_json(run_dir / 'stage3-summary.json', summary)
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0

    # Deterministic mainline routing is *advisory*: it records the conservative
    # anchor upper bound (single_anchor / multi_contract / no_anchor) and feeds
    # binding hints, but the authoritative gate for "can assert(I) be injected"
    # is the actual binding's expressibility (``expressibility`` below). Many
    # claims whose symbols span contracts still bind to one injection point and
    # reproduce, so gating on the upper bound would wrongly discard them.
    try:
        routing = classify_route(stage2_src, claim_id, case_dir / 'src')
    except Exception as exc:  # keep legacy behaviour when routing is unavailable
        routing = {
            'schema_version': 'stage3-routing/1',
            'claim_id': claim_id,
            'route': 'auto_assert',
            'reason': f'routing unavailable: {exc}',
            'auto_verifiable': True,
            'requires_reference_patch': False,
        }
    write_json(run_dir / 'routing.json', routing)

    selfdestruct_targets = injection_selfdestruct_targets(case_dir, binding)

    if args.lint or args.strict_lint:
        lint = lint_binding(binding, case_dir / 'src',
                            test_dir=case_dir / 'test',
                            strict=bool(args.strict_lint))
        write_json(run_dir / 'binding-lint.json', lint)
        for problem in lint['problems']:
            print(f"binding-lint: {problem['severity']} {problem['where']}: "
                  f"{problem['message']}", file=sys.stderr)
        if not lint['ok']:
            raise SystemExit('binding lint failed; see binding-lint.json '
                             'and fix the binding before rerunning')

    # Local copy of the three stage-2 artifacts keeps the authoritative
    # verdict inside this run and makes reruns non-destructive.
    local_stage2 = run_dir / 'stage2'
    local_stage2.mkdir()
    for name in ('stage3-spec.json', 'constraints.json', 'formalization.json'):
        shutil.copy2(stage2_src / name, local_stage2 / name)
    if restatement.get('status') == 'restated':
        write_json(local_stage2 / 'formalization.json', stage2['formal'])

    monitor_record = None
    if (not revert_expected and not reference_patch_mode
            and expressibility.get('expressibility') == 'cross_contract_reference'):
        monitor_binding, monitor_expression, monitor_record = _try_test_monitor(
            case_dir=case_dir, run_dir=run_dir, binding=binding,
            stage2=stage2, safety_symbols=safety_symbols, probe=probe)
        if monitor_binding is not None:
            binding = monitor_binding
            entries = binding['bindings']
            expressibility = monitor_expression
            routing = {
                **routing,
                'route': 'test_level_monitor',
                'auto_verifiable': True,
                'requires_reference_patch': False,
                'monitor_reason': ('cross-contract symbols are observable from '
                                   'the PoC test frame'),
            }
            contract = execution_contract.build(
                stage2['formal'], binding, claim_id,
                weak_invariant=weak_risk, monitor=monitor_record)
            write_json(run_dir / 'execution-contract.json', contract)
            write_json(run_dir / 'routing.json', routing)
    if monitor_record is not None:
        write_json(run_dir / 'test-monitor.json', monitor_record)

    # M1 reference patch: the route accepts either ``case/patched`` (verbatim
    # tree) or ``case/patched.diff`` (unified diff against case/src). When
    # only the diff exists and the binding needs the M1 route, materialize
    # the patched tree deterministically before the differential build.
    needs_reference_patch = (
        expressibility['reference_patch_required'] or bool(selfdestruct_targets))
    reference_patch_record = None
    if needs_reference_patch and has_reference_patch(case_dir):
        patch_data = binding.get('patch') or {}
        patch_functions = patch_data.get('functions') or []
        target_function = None
        if isinstance(patch_functions, list) and patch_functions:
            first = patch_functions[0]
            target_function = (first.get('name') if isinstance(first, dict)
                               else None)
        try:
            reference_patch_record = build_reference_patch(
                case_dir, target_function=target_function,
                validate_compile=True)
        except ReferencePatchError as exc:
            reference_patch_record = {
                'schema_version': 'stage1-reference-patch/1',
                'accepted': False,
                'blockers': [str(exc)],
            }
        write_json(run_dir / 'reference-patch-manifest.json',
                   reference_patch_record)
        if not reference_patch_record.get('accepted'):
            reason = '; '.join(reference_patch_record.get('blockers') or [])
            summary = {
                'schema_version': 'stage3-run-summary/1',
                'case': str(case_dir),
                'run_id': run_id,
                'stage2_run': str(stage2_src),
                'claim_id': claim_id,
                'probe': probe,
                'forge': {'exploit': {'original': None, 'patched': None},
                          'safety': None},
                'code_query_results': None,
                'compile_retry': None,
                'expressibility': expressibility,
                'routing': routing,
                'consistency_verdict': 'reference_patch_required',
                'witness': witness_protocol.unavailable(
                    claim_id, 'reference_patch_apply_failed', reason),
                'reference_patch_required': {
                    'route': routing['route'],
                    'reason': ('a reference patch is present but could not '
                               'be applied deterministically'),
                    'apply_error': reason,
                    'record': reference_patch_record,
                    'expected_patch_dir': str(case_dir / 'patched'),
                    'expected_patch_diff': str(case_dir / 'patched.diff'),
                },
                'mechanism_ceiling': mechanism_ceiling.record(
                    'reference_patch',
                    'reference patch exists but could not be materialized',
                    apply_error=reason),
            }
            write_json(run_dir / 'stage3-summary.json', summary)
            print(json.dumps(summary, ensure_ascii=False, indent=2))
            return 0

    if (expressibility['reference_patch_required']
            and not (case_dir / 'patched').is_dir()):
        summary = {
            'schema_version': 'stage3-run-summary/1',
            'case': str(case_dir),
            'run_id': run_id,
            'stage2_run': str(stage2_src),
            'claim_id': claim_id,
            'probe': probe,
            'forge': {'exploit': {'original': None, 'patched': None},
                      'safety': None},
            'code_query_results': None,
            'compile_retry': None,
            'expressibility': expressibility,
            'routing': routing,
            'consistency_verdict': 'reference_patch_required',
            'witness': witness_protocol.unavailable(
                claim_id, 'reference_patch_required',
                'the binding spans contracts and cannot be injected as assert(I)'),
            'reference_patch_required': {
                'route': routing['route'],
                'reason': ('the actual binding references symbols across '
                           'contracts and cannot be injected as one assert(I)'),
                'expressibility': expressibility['expressibility'],
                'expected_patch_dir': str(case_dir / 'patched'),
            },
            'mechanism_ceiling': mechanism_ceiling.record(
                'reference_patch',
                'the claim cannot be injected as a single assert(I)',
                expressibility=expressibility.get('expressibility'),
                cross_contract_symbols=expressibility.get(
                    'cross_contract_symbols') or []),
        }
        write_json(run_dir / 'stage3-summary.json', summary)
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0

    if selfdestruct_targets and not (case_dir / 'patched').is_dir():
        summary = {
            'schema_version': 'stage3-run-summary/1',
            'case': str(case_dir),
            'run_id': run_id,
            'stage2_run': str(stage2_src),
            'claim_id': claim_id,
            'probe': probe,
            'forge': {'exploit': {'original': None, 'patched': None},
                      'safety': None},
            'code_query_results': None,
            'compile_retry': None,
            'expressibility': expressibility,
            'routing': routing,
            'consistency_verdict': 'halt_witness_required',
            'witness': witness_protocol.unavailable(
                claim_id, 'halt_witness_required',
                'selfdestruct halts the execution context; a halt witness is '
                'required before an invariant verdict can be produced'),
            'halt_witness_required': {
                'reason': ('injection target executes selfdestruct and halts '
                           'the execution context; the halt-to-revert rewrite '
                           'only covers stop()'),
                'targets': selfdestruct_targets,
            },
        }
        write_json(run_dir / 'stage3-summary.json', summary)
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0

    try:
        original, patched = build_projects(
            case_dir, run_dir, binding=binding, spec=stage2['spec'],
            formal=stage2['formal'])
    except SpecError as exc:
        summary = {
            'schema_version': 'stage3-run-summary/1',
            'case': str(case_dir),
            'run_id': run_id,
            'stage2_run': str(stage2_src),
            'claim_id': claim_id,
            'probe': probe,
            'forge': {'exploit': {'original': None, 'patched': None},
                      'safety': None},
            'code_query_results': None,
            'compile_retry': None,
            'consistency_verdict': 'binding_error',
            'witness': witness_protocol.unavailable(
                claim_id, 'binding_structural_error', str(exc)),
            'binding_error': {'reason': str(exc)},
        }
        write_json(run_dir / 'stage3-summary.json', summary)
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0
    original_run = run_forge_safe(original)
    patched_run = run_forge_safe(patched)
    original_run = _retry_without_via_ir(original_run, original)
    patched_run = _retry_without_via_ir(patched_run, patched)
    original_run = _retry_stack_too_deep(original_run, original)
    patched_run = _retry_stack_too_deep(patched_run, patched)

    compile_retry = None
    neutralized_symbols: list[str] = []
    if (original_run['ok'] and not patched_run['ok']
            and expressibility['dynamically_expressible']):
        max_compile_retries = 3
        retry_rounds = []
        while (not patched_run['ok'] and len(retry_rounds) < max_compile_retries):
            reported = error_identifiers(patched_run.get('compile_error') or '')
            patch_file = ((binding.get('patch') or {}).get('file') or '')
            src_target = case_dir / 'src' / patch_file
            anchors = []
            if patch_file and src_target.is_file():
                try:
                    _, anchors = relocate_before_snapshots(
                        binding, src_target.read_text())
                except Exception:
                    anchors = []
            if anchors:
                reloc_binding, anchors = relocate_before_snapshots(
                    binding, src_target.read_text())
                build_projects(case_dir, run_dir, binding=reloc_binding,
                               spec=stage2['spec'], formal=stage2['formal'])
                reloc_run = run_forge_safe(run_dir / 'patched')
                reloc_run = _retry_without_via_ir(reloc_run, run_dir / 'patched')
                reloc_run = _retry_stack_too_deep(reloc_run, run_dir / 'patched')
                retry_rounds.append({
                    'attempt': len(retry_rounds) + 1,
                    'error_identifiers': sorted(reported),
                    'relocated': anchors,
                    'relocated_injection': False,
                    'neutralized': [],
                    'compiled': bool(reloc_run['ok']),
                })
                patched_run = reloc_run
                if reloc_run['ok']:
                    binding = reloc_binding
                    entries = binding['bindings']
                    patched = run_dir / 'patched'
                continue
            # Undeclared-identifier failures are usually a wrong injection
            # point: the snapshot reads PoC-test locals but the assertion is
            # injected into a business function.  Retry with the injection
            # point moved to the probe's exploit test function.
            test_location = test_monitor.find_test_location(case_dir, probe)
            test_binding = relocate_injection_to_test(
                binding,
                source=(src_target.read_text()
                        if src_target.is_file() else None),
                test_source=(test_location[0].read_text()
                             if test_location is not None else None))
            if test_binding is not None and src_target.is_file():
                try:
                    test_binding, _ = relocate_before_snapshots(
                        test_binding, src_target.read_text())
                    build_projects(case_dir, run_dir, binding=test_binding,
                                   spec=stage2['spec'], formal=stage2['formal'])
                    test_run = run_forge_safe(run_dir / 'patched')
                    test_run = _retry_without_via_ir(test_run, run_dir / 'patched')
                    test_run = _retry_stack_too_deep(test_run, run_dir / 'patched')
                    retry_rounds.append({
                        'attempt': len(retry_rounds) + 1,
                        'error_identifiers': sorted(reported),
                        'relocated': [],
                        'relocated_injection': True,
                        'neutralized': [],
                        'compiled': bool(test_run['ok']),
                    })
                    patched_run = test_run
                    if test_run['ok']:
                        binding = test_binding
                        entries = binding['bindings']
                        patched = run_dir / 'patched'
                    continue
                except SpecError:
                    pass
            retry_rounds.append({
                'attempt': len(retry_rounds) + 1,
                'error_identifiers': sorted(reported),
                'relocated': [],
                'neutralized': [],
                'compiled': False,
                'note': ('no deterministic snapshot relocation or injection-point '
                         'relocation available; compile-retry neutralization '
                         'disabled to avoid constant-binding false negatives'),
            })
            break
        compile_retry = {
            'attempted': bool(retry_rounds),
            'rounds': retry_rounds,
            'neutralized': [],
            'neutralization_disabled': True,
            'retry_compiled': bool(patched_run['ok']) if retry_rounds else None,
        }

    if not original_run['ok'] or not patched_run['ok']:
        if original_run.get('no_tests') or patched_run.get('no_tests'):
            compile_kind = 'no_test_entrypoint'
            verdict = 'compile_blocked'
        else:
            compile_kind = ('slice_compile_failure' if not original_run['ok']
                            else 'binding_compile_failure')
            verdict = ('compile_blocked' if not original_run['ok']
                       else 'compile_error')
        if original_run['ok'] and not expressibility['dynamically_expressible']:
            compile_kind = 'not_dynamically_expressible'
            verdict = 'not_dynamically_expressible'
        compile_record = {
            'claim_id': claim_id,
            'compile_kind': compile_kind,
            'expressibility': expressibility,
            'original': original_run if not original_run['ok'] else {'ok': True},
            'patched': patched_run if not patched_run['ok'] else {'ok': True},
            'compile_retry': compile_retry,
            'failure_classes': {
                'original': failure_classes(
                    original_run.get('compile_error')
                    if not original_run['ok'] else None),
                'patched': failure_classes(
                    patched_run.get('compile_error')
                    if not patched_run['ok'] else None),
            },
            'witness': witness_protocol.classify(
                claim_id, compile_error={
                    'original': (original_run.get('compile_error')
                                 if not original_run['ok'] else None),
                    'patched': (patched_run.get('compile_error')
                                if not patched_run['ok'] else None),
                }),
        }
        write_json(run_dir / 'compile-error.json', compile_record)
        failure_by_target = compile_record['failure_classes']
        failure_flat = sorted({
            item for values in failure_by_target.values() for item in values})
        summary = {
            'schema_version': 'stage3-run-summary/1',
            'case': str(case_dir),
            'run_id': run_id,
            'stage2_run': str(stage2_src),
            'claim_id': claim_id,
            'probe': probe,
            'forge': {
                'exploit': {'original': None, 'patched': None},
                'safety': None,
            },
            'code_query_results': None,
            'consistency_verdict': verdict,
            'expressibility': expressibility,
            'compile_error': {
                'kind': compile_kind,
                'original': (original_run.get('compile_error')
                             if not original_run['ok'] else None),
                'patched': (patched_run.get('compile_error')
                            if not patched_run['ok'] else None),
            },
            'compile_retry': compile_retry,
            'compile_failure_classes': failure_flat,
            'compile_failure_classes_by_target': failure_by_target,
        }
        if verdict == 'not_dynamically_expressible':
            summary['mechanism_ceiling'] = mechanism_ceiling.record(
                'not_dynamically_expressible',
                'no source-visible injection point can observe the invariant',
                compile_kind=compile_kind,
                expressibility=expressibility)
        write_json(run_dir / 'stage3-summary.json', summary)
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0

    original_json = original_run['result']
    patched_json = patched_run['result']

    exploit_test = probe.get('exploit_test')
    original_result = test_result(original_json, exploit_test) if exploit_test else None
    patched_result = test_result(patched_json, exploit_test) if exploit_test else None
    if original_result is None or patched_result is None:
        reason = (first_failure_reason(original_json)
                  or first_failure_reason(patched_json)
                  or f'probe test {exploit_test!r} not present in forge output')
        summary = {
            'schema_version': 'stage3-run-summary/1',
            'case': str(case_dir),
            'run_id': run_id,
            'stage2_run': str(stage2_src),
            'claim_id': claim_id,
            'probe': probe,
            'forge': {
                'exploit': {'original': original_result, 'patched': patched_result},
                'safety': None,
            },
            'code_query_results': None,
            'compile_retry': compile_retry,
            'consistency_verdict': 'inconclusive',
            'inconclusive': {
                'reason': reason,
                'exploit_test': exploit_test,
            },
            'witness': witness_protocol.classify(
                claim_id, original_result=original_result,
                patched_result=patched_result, test_missing=True),
        }
        write_json(run_dir / 'stage3-summary.json', summary)
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0

    safety_test = probe.get('safety_test')
    safety_patched = test_result(patched_json, safety_test) if safety_test else None

    # Weak-invariant repair: when the exploit PoC passes on both original and
    # the I-probe slice, I may be vacuously true on the exploit path (a
    # ``guard -> property`` implication whose guard never fires on vulnerable
    # code).  Build an effect-probe slice (``assert(!P || V)``) so V is
    # witnessed independently instead of being hard-coded to unsat.
    effect_result = None
    if (not (case_dir / 'patched').is_dir()
            and original_result.get('status') == 'Success'
            and not effect_unbound):
        try:
            build_effect_project(case_dir, run_dir / 'effect', binding,
                                 stage2['spec'], stage2['formal'])
            effect_run = run_forge_safe(run_dir / 'effect')
            effect_run = _retry_without_via_ir(effect_run, run_dir / 'effect')
            effect_run = _retry_stack_too_deep(effect_run, run_dir / 'effect')
            if effect_run.get('ok'):
                effect_result = test_result(effect_run['result'], exploit_test)
        except SpecError as exc:
            effect_result = None
            print(f'effect-probe unavailable: {exc}', file=sys.stderr)

    # P13: trusted negatives need an independent effect-absence witness.
    # This probe supplies ``P AND T AND NOT V`` without changing any dynamic
    # verdict; a missing or failed probe leaves the claim unresolved.
    negative_result = None
    if (execution_gate.is_trusted_negative(trusted_label)
            and original_result.get('status') == 'Success'
            and not effect_unbound):
        try:
            build_negative_project(case_dir, run_dir / 'negative', binding,
                                   stage2['spec'], stage2['formal'])
            negative_run = run_forge_safe(run_dir / 'negative')
            negative_run = _retry_without_via_ir(
                negative_run, run_dir / 'negative')
            negative_run = _retry_stack_too_deep(
                negative_run, run_dir / 'negative')
            if negative_run.get('ok'):
                negative_result = test_result(negative_run['result'],
                                              exploit_test)
        except SpecError as exc:
            negative_result = None
            print(f'negative-probe unavailable: {exc}', file=sys.stderr)

    queries = compute_queries(probe, original_result, patched_result,
                              safety_patched,
                              reference_patch=(case_dir / 'patched').is_dir(),
                              effect_result=effect_result,
                              negative_result=negative_result)
    # P AND T infeasible conflates two very different stage-1 failures: the PoC
    # never witnessed P (fix the PoC/slice), or the injected precondition
    # snapshot was false at its anchor (fix the checkpoint geometry).  Record
    # which one so the verdict loop routes it instead of rebinding forever.
    precondition_failure = None
    if queries.get('P_and_T') == 'unsat':
        if original_result.get('status') != 'Success':
            precondition_failure = 'poc_not_witnessed'
        elif patched_result and 'stage3:precondition_unwitnessed' in \
                str(patched_result.get('reason') or ''):
            precondition_failure = 'snapshot_unwitnessed'
        elif patched_result and 'stage3:P' in \
                str(patched_result.get('reason') or ''):
            precondition_failure = 'legacy_precondition_failed'
    witness = witness_protocol.classify(
        claim_id, original_result=original_result,
        patched_result=patched_result, effect_result=effect_result,
        queries=queries, precondition_failure=precondition_failure,
        invariant_unbound=invariant_unbound, binding=binding)
    poc = {
        'executed': True,
        'description': f"PoC test {exploit_test}: original={original_result['status']}, "
                       f"patched={patched_result['status']} "
                       f"({patched_result.get('reason')})",
    }
    feedback = build_feedback(claim_id, entries, queries, poc)
    for name, entry in entries.items():
        if str(entry.get('solidity_expr') or '').strip() == 'UNBOUND':
            if name in feedback['symbol_bindings']:
                feedback['symbol_bindings'][name] = {
                    'status': 'unbound',
                    'binding': 'UNBOUND (no code observable)',
                }
    reference_patch_used = (case_dir / 'patched').is_dir()
    if revert_expected:
        # The revert-witness route replaces ``assert(!P || I)`` with a
        # low-level-call capture of the revert expectation, so the verdict is
        # read from the forge differential directly instead of stage-2's
        # assert-I adjudication (which cannot see I-symbols left UNBOUND on
        # purpose). original Success + patched Failure == reproduced.
        reproduced = (original_result.get('status') == 'Success'
                      and patched_result.get('status') == 'Failure')
        verdict = {
            'consistency_verdict': ('violation_reproduced' if reproduced
                                    else 'violation_not_reproduced'),
            'schema_version': 'stage3-revert-witness-verdict/1',
        }
    elif reference_patch_used:
        # M1 reference patch: the patched contract is the fix, so the binding
        # may legitimately carry UNBOUND observables. Read the verdict from
        # the forge differential instead of stage-2's binding adjudication.
        if revert_vulnerability:
            # Revert-DoS fix patch: the buggy PoC reverts (original Failure)
            # and the fixed code completes (patched Success).
            reproduced = (original_result.get('status') == 'Failure'
                          and patched_result.get('status') == 'Success')
        else:
            reproduced = (original_result.get('status') == 'Success'
                          and patched_result.get('status') == 'Failure')
        verdict = {
            'consistency_verdict': ('violation_reproduced' if reproduced
                                    else 'violation_not_reproduced'),
            'schema_version': 'stage3-reference-patch-verdict/1',
        }
    else:
        verdict = submit(local_stage2, feedback)

    # Independent-evidence gate: a failing I probe alone is not enough when V
    # uses only the same observables (no polarity witness) or when the V probe
    # was available but did not witness the hazard.  The revert-witness route
    # is included because its differential is not an independent effect probe.
    post_gate = independent_effect_gate(
        verdict=verdict,
        reference_patch_used=reference_patch_used,
        revert_expected=revert_expected,
        effect_independent=bool(preflight_gate.get('effect_independent', True)),
        queries=queries,
        witness=witness)
    if post_gate:
        verdict = {
            **verdict,
            'raw_consistency_verdict': verdict.get('consistency_verdict'),
            'consistency_verdict': post_gate['verdict'],
            'post_execution_gate': post_gate,
        }

    gate = execution_gate.adjudicate(
        stage2['formal'], binding, claim_id,
        trusted_label=trusted_label,
        preflight_result=preflight_gate,
        execution={**verdict, 'code_query_results': queries,
                   'witness': witness})
    write_json(run_dir / 'execution-gate.json', gate)
    contract = execution_contract.build(
        stage2['formal'], binding, claim_id, weak_invariant=weak_risk,
        monitor=monitor_record, execution_gate=gate,
        formalization_contract=final_contract)
    write_json(run_dir / 'execution-contract.json', contract)

    summary = {
        'schema_version': 'stage3-run-summary/1',
        'case': str(case_dir),
        'run_id': run_id,
        'stage2_run': str(stage2_src),
        'claim_id': claim_id,
        'probe': probe,
        'forge': {
            'exploit': {'original': original_result, 'patched': patched_result},
            'effect': effect_result,
            'safety': safety_patched,
            'negative': negative_result,
        },
        'code_query_results': queries,
        'compile_retry': compile_retry,
        'expressibility': expressibility,
        'execution_contract': contract,
        'test_monitor': monitor_record,
        'reference_patch_used': reference_patch_used,
        'reference_patch': reference_patch_record,
        'consistency_verdict': verdict.get('consistency_verdict'),
        'raw_consistency_verdict': verdict.get(
            'raw_consistency_verdict', verdict.get('consistency_verdict')),
        'post_execution_gate': post_gate,
        'precondition_failure': precondition_failure,
        'witness': witness,
        'weak_invariant_risk': weak_risk,
        'stage2_contract_gate': stage2_gate,
        'stage2_restatement': restatement,
        'stage2_final_contract': final_contract,
        'execution_gate': gate,
        'preflight_execution_gate': preflight_gate,
        'impact_sufficiency': gate.get('impact_sufficiency'),
        'impact_class': gate.get('impact_class'),
        'metric_eligibility': gate.get('metric_eligibility'),
        'verdict_artifact': str(local_stage2 / 'stage3-consistency.json'),
    }
    summary['witness_route'] = witness_router.route(summary)
    write_json(run_dir / 'stage3-summary.json', summary)
    write_json(run_dir / 'code-query-results.json', {
        'claim_id': claim_id,
        'probe': probe,
        'code_query_results': queries,
    })
    if negative_result is not None:
        write_json(run_dir / 'negative-probe.json', {
            'claim_id': claim_id,
            'trusted_label': trusted_label,
            'result': negative_result,
            'code_query_results': queries,
        })

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
