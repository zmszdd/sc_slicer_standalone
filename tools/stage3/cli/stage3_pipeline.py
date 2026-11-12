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
                             safety_symbols_for_claim)
from lib.binding import build_feedback, load_binding, validate_binding
from lib.binding_normalize import normalize_binding
from lib.binding_validate import lint_binding
from lib.expressibility import classify as classify_expressibility
from lib.routing import classify_route
from lib.patch import (build_effect_project, build_projects,
                        injection_selfdestruct_targets,
                        relocate_before_snapshots)
from lib.forge_runner import first_failure_reason, run_forge_safe, test_result
from lib.differential import compute_queries
from lib.verdict import submit
from lib.compile_retry import error_identifiers
from lib import rebind

ROOT = Path(__file__).resolve().parents[1]  # tools/stage3


def write_json(path: Path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


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


def main(argv=None):
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
    binding, normalization_changes = normalize_binding(
        binding, case_dir / 'src', test_dir=case_dir / 'test', strict=True)
    if normalization_changes:
        print(f'binding-normalize: {"; ".join(normalization_changes)}',
              file=sys.stderr)
    binding, rebind_changes = rebind.rebind_binding(
        binding, rebind.load_source(case_dir / 'src'))
    if rebind_changes:
        print(f'binding-rebind: {"; ".join(rebind_changes)}', file=sys.stderr)

    safety_symbols = safety_symbols_for_claim(stage2['formal'], claim_id)
    unbound_symbols = sorted(
        name for name, entry in (binding.get('bindings') or {}).items()
        if isinstance(entry, dict)
        and str(entry.get('solidity_expr') or '').strip() == 'UNBOUND')
    if unbound_symbols:
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
            'partial_binding': {
                'unbound_symbols': unbound_symbols,
                'reason': ('binding is incomplete: these required symbols have '
                           'solidity_expr=UNBOUND and must be rebound before '
                           'forge can produce a dynamic verdict'),
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
    if (not expressibility['dynamically_expressible']
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
            'reference_patch_required': {
                'route': routing['route'],
                'reason': ('the actual binding references symbols across '
                           'contracts and cannot be injected as one assert(I)'),
                'expressibility': expressibility['expressibility'],
                'expected_patch_dir': str(case_dir / 'patched'),
            },
        }
        write_json(run_dir / 'stage3-summary.json', summary)
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0

    selfdestruct_targets = injection_selfdestruct_targets(case_dir, binding)
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
            'binding_error': {'reason': str(exc)},
        }
        write_json(run_dir / 'stage3-summary.json', summary)
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0
    original_run = run_forge_safe(original)
    patched_run = run_forge_safe(patched)
    original_run = _retry_without_via_ir(original_run, original)
    patched_run = _retry_without_via_ir(patched_run, patched)

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
            if not anchors:
                retry_rounds.append({
                    'attempt': len(retry_rounds) + 1,
                    'error_identifiers': sorted(reported),
                    'relocated': [],
                    'neutralized': [],
                    'compiled': False,
                    'note': ('no deterministic snapshot relocation available; '
                             'compile-retry neutralization disabled to avoid '
                             'constant-binding false negatives'),
                })
                break
            reloc_binding, anchors = relocate_before_snapshots(
                binding, src_target.read_text())
            build_projects(case_dir, run_dir, binding=reloc_binding,
                           spec=stage2['spec'], formal=stage2['formal'])
            reloc_run = run_forge_safe(run_dir / 'patched')
            retry_rounds.append({
                'attempt': len(retry_rounds) + 1,
                'error_identifiers': sorted(reported),
                'relocated': anchors,
                'neutralized': [],
                'compiled': bool(reloc_run['ok']),
            })
            patched_run = reloc_run
            if reloc_run['ok']:
                binding = reloc_binding
                entries = binding['bindings']
                patched = run_dir / 'patched'
            break
        compile_retry = {
            'attempted': bool(retry_rounds),
            'rounds': retry_rounds,
            'neutralized': [],
            'neutralization_disabled': True,
            'retry_compiled': bool(patched_run['ok']) if retry_rounds else None,
        }

    if not original_run['ok'] or not patched_run['ok']:
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
        }
        write_json(run_dir / 'compile-error.json', compile_record)
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
        }
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
            and patched_result.get('status') == 'Success'):
        try:
            build_effect_project(case_dir, run_dir / 'effect', binding,
                                 stage2['spec'], stage2['formal'])
            effect_run = run_forge_safe(run_dir / 'effect')
            effect_run = _retry_without_via_ir(effect_run, run_dir / 'effect')
            if effect_run.get('ok'):
                effect_result = test_result(effect_run['result'], exploit_test)
        except SpecError as exc:
            effect_result = None
            print(f'effect-probe unavailable: {exc}', file=sys.stderr)

    queries = compute_queries(probe, original_result, patched_result,
                              safety_patched,
                              reference_patch=(case_dir / 'patched').is_dir(),
                              effect_result=effect_result)
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
    verdict = submit(local_stage2, feedback)

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
        },
        'code_query_results': queries,
        'compile_retry': compile_retry,
        'expressibility': expressibility,
        'consistency_verdict': verdict.get('consistency_verdict'),
        'precondition_failure': precondition_failure,
        'verdict_artifact': str(local_stage2 / 'stage3-consistency.json'),
    }
    write_json(run_dir / 'stage3-summary.json', summary)
    write_json(run_dir / 'code-query-results.json', {
        'claim_id': claim_id,
        'probe': probe,
        'code_query_results': queries,
    })

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
