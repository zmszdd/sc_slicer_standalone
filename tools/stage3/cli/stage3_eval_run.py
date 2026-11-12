#!/usr/bin/env python3
"""Batch-run stage-3 over positive goldset samples.

For each goldset case: assemble a stage-3 case from the verified flatten file,
propose a binding per claim via DeepSeek, lint it, then run the differential
pipeline. Emits one summary row per case.

Run with cwd = tools/stage3:
    python -m cli.stage3_eval_run --goldset-root <...>/goldset_v1_pos20 \
        --flatten-root <...>/verified_flatten_pass_1568_exact_cases \
        --cases-root cases --out /tmp/eval_run.json
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

from lib.spec_loader import SpecError, load_stage2_run, safety_symbols_for_claim
from lib.binding_validate import lint_binding

ROOT = Path(__file__).resolve().parents[1]


def _round_hint(claim_id: str, round_no: int, problems: list[str]) -> str:
    items = '; '.join(str(problem) for problem in problems[:12])
    return (f'round {round_no} failed for claim {claim_id}. '
            f'Fix these problems: {items}.')


def _assemble(name, flatten, stage2_dir, cases_root, src_name):
    """Delegate to the shared case builder so eval and product share one path."""
    out = cases_root / name
    if out.exists():
        return out
    from lib.case_builder import assemble_case
    return assemble_case(
        name=name,
        src=flatten,
        stage2_run=stage2_dir,
        test=None,
        out=out,
        default_foundry_toml=True,
        src_name=src_name,
    )


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--goldset-root', required=True)
    parser.add_argument('--flatten-root', required=True)
    parser.add_argument('--cases-root', required=True)
    parser.add_argument('--out', required=True)
    parser.add_argument('--cases', default=None,
                        help='comma-separated case ids; default: all in selection')
    parser.add_argument('--skip-llm', action='store_true',
                        help='reuse existing bindings/ dir instead of re-proposing')
    parser.add_argument('--max-binding-rounds', type=int, default=3,
                        help='LLM binding repair rounds per claim (default 3)')
    args = parser.parse_args(argv)

    goldset = Path(args.goldset_root)
    selection = json.loads((goldset / 'selection.json').read_text())
    cases_root = Path(args.cases_root).resolve()
    flatten_root = Path(args.flatten_root)

    wanted = set(args.cases.split(',')) if args.cases else None
    rows = []
    for item in selection['cases']:
        cid = item['case']
        if wanted is not None and cid not in wanted:
            continue
        stage2_dir = None
        for b in sorted(goldset.glob('runs_*')):
            candidate = b / cid
            if (candidate / 'stage3-spec.json').is_file():
                stage2_dir = candidate
                break
        if stage2_dir is None:
            rows.append({'case': cid, 'status': 'no_stage2_run'})
            continue

        try:
            spec = load_stage2_run(stage2_dir)
        except SpecError as exc:
            rows.append({'case': cid, 'status': 'stage2_blocked',
                         'detail': str(exc)})
            continue
        claims = [r['claim_id'] for r in spec['spec'].get('claims', [])]
        if not claims:
            rows.append({'case': cid, 'status': 'zero_claims'})
            continue

        flatten = flatten_root / cid / 'contract.flattened.t.sol'
        if not flatten.is_file():
            rows.append({'case': cid, 'status': 'no_flatten'})
            continue

        case_dir = _assemble(cid, flatten, stage2_dir, cases_root,
                             'Contract.sol')
        bindings_dir = case_dir / 'bindings'
        bindings_dir.mkdir(parents=True, exist_ok=True)

        bound = 0
        failed = []
        unobservable_symbols = []
        bindabilities = []
        bindability_by_claim = {}
        bound_claim_ids: list[str] = []
        for claim_id in claims:
            binding_path = bindings_dir / f'{claim_id}.json'
            if args.skip_llm and binding_path.is_file():
                bound += 1
                bound_claim_ids.append(claim_id)
                bindabilities.append('reused')
                continue
            try:
                from lib.binding_skeleton import build_skeleton
                skeleton = build_skeleton(stage2_dir, claim_id,
                                          src=case_dir / 'src')
                for sym, entry in skeleton.get('bindings', {}).items():
                    if entry.get('observability') == 'low':
                        unobservable_symbols.append(sym)
            except Exception:
                pass
            try:
                from lib.anchor_resolver import resolve_anchors
                anchor = resolve_anchors(stage2_dir, claim_id, case_dir / 'src')
                bindabilities.append(anchor['bindability'])
                bindability_by_claim[claim_id] = anchor['bindability']
            except Exception:
                bindabilities.append('unknown')
            hint = None
            accepted = False
            bound_counted = False
            for round_no in range(1, args.max_binding_rounds + 1):
                cmd = [sys.executable, '-m', 'cli.stage3_binding_llm',
                       '--stage2-run', str(stage2_dir), '--claim-id', claim_id,
                       '--src', str(case_dir / 'src'),
                       '--out', str(case_dir / 'llm_proposal')]
                if hint:
                    cmd += ['--hint', hint]
                if round_no > 1 and binding_path.is_file():
                    cmd += ['--existing', str(binding_path)]
                proposal = subprocess.run(cmd, capture_output=True, text=True,
                                          cwd=str(ROOT))
                try:
                    proposal_json = json.loads(proposal.stdout)
                except ValueError:
                    proposal_json = None
                if proposal_json is None or not isinstance(proposal_json, dict):
                    problems = ['transport: ' +
                                (proposal.stderr or proposal.stdout)[:200]]
                    hint = _round_hint(claim_id, round_no, problems)
                    continue
                if proposal_json.get('partial') and not proposal_json.get('problems'):
                    proposal_path = case_dir / 'llm_proposal' / 'binding.proposal.json'
                    if proposal_path.is_file():
                        shutil.copy2(proposal_path, binding_path)
                        accepted = True
                        if claim_id not in bound_claim_ids:
                            bound_claim_ids.append(claim_id)
                        if not bound_counted:
                            bound += 1
                            bound_counted = True
                        if round_no < args.max_binding_rounds:
                            detail = proposal_json.get('unbound_detail') or {}
                            rebindable = [s for s in (proposal_json.get('unbound') or [])
                                          if detail.get(s, {}).get('observability') != 'low'
                                          or detail.get(s, {}).get('candidates')]
                            if rebindable:
                                hint = None
                                continue
                        break
                if not proposal_json.get('ok'):
                    problems = list(proposal_json.get('problems') or [])
                    if proposal_json.get('partial'):
                        problems.append('unbound: ' + ', '.join(
                            proposal_json.get('unbound', [])))
                    hint = _round_hint(claim_id, round_no, problems)
                    continue
                proposal_path = case_dir / 'llm_proposal' / 'binding.proposal.json'
                if not proposal_path.is_file():
                    problems = ['no proposal file written']
                    hint = _round_hint(claim_id, round_no, problems)
                    continue
                binding = json.loads(proposal_path.read_text())
                safety_symbols = safety_symbols_for_claim(
                    spec['formal'], claim_id)
                lint = lint_binding(binding, case_dir / 'src',
                                    test_dir=case_dir / 'test', strict=False,
                                    safety_symbols=safety_symbols)
                if lint['summary']['errors']:
                    problems = [f"{problem['where']}: {problem['message']}"
                                for problem in lint['problems']]
                    hint = _round_hint(claim_id, round_no, problems)
                    continue
                shutil.copy2(proposal_path, binding_path)
                bound += 1
                bound_claim_ids.append(claim_id)
                accepted = True
                break
            if not accepted:
                failed.append({'claim': claim_id, 'reason': 'binding_exhausted',
                               'rounds': args.max_binding_rounds,
                               'detail': hint})

        bound = len(set(bound_claim_ids))
        bound_claim_ids = list(dict.fromkeys(bound_claim_ids))
        (case_dir / 'stage3-bindability.json').write_text(
            json.dumps({
                'schema_version': 'stage3-bindability-feedback/1',
                'case': cid,
                'bindabilities': bindability_by_claim,
            }, ensure_ascii=False, indent=2) + '\n')

        multi_verdicts: dict[str, str] = {}
        if bound_claim_ids:
            multi = subprocess.run(
                [sys.executable, '-m', 'cli.stage3_multi',
                 '--case-dir', str(case_dir), '--bindings-dir', str(bindings_dir),
                 '--stage2-run', str(case_dir / 'stage2_run'),
                 '--run-id-prefix', cid,
                 '--claims', ','.join(bound_claim_ids)],
                capture_output=True, text=True, cwd=str(ROOT))
            try:
                payload = json.loads(multi.stdout)
                for row in payload.get('claims', []):
                    multi_verdicts[row.get('claim_id')] = (
                        row.get('consistency_verdict') or 'binding_failed')
            except ValueError:
                pass

        verdicts = []
        for claim_id in claims:
            if claim_id in bound_claim_ids:
                verdicts.append(multi_verdicts.get(claim_id, 'binding_failed'))
            else:
                verdicts.append('binding_failed')

        reproduced = verdicts.count('violation_reproduced')
        compile_blocked = verdicts.count('compile_blocked')
        compile_error = verdicts.count('compile_error')
        not_expressible = verdicts.count('not_dynamically_expressible')
        reference_required = verdicts.count('reference_patch_required')
        halt_required = verdicts.count('halt_witness_required')

        if bound == 0:
            rows.append({'case': cid, 'status': 'no_bound_claims',
                         'claims': len(claims), 'failed': failed,
                         'unobservable_symbols': sorted(set(unobservable_symbols))})
            continue

        rows.append({
            'case': cid, 'status': 'done',
            'claims': len(claims), 'bound': bound,
            'claim_ids': claims,
            'verdicts': verdicts,
            'reproduced': reproduced,
            'compile_blocked': compile_blocked,
            'compile_error': compile_error,
            'not_dynamically_expressible': not_expressible,
            'reference_patch_required': reference_required,
            'halt_witness_required': halt_required,
            'bound_claim_ids': bound_claim_ids,
            'bindabilities': bindabilities,
            'failed_bindings': failed,
            'unobservable_symbols': sorted(set(unobservable_symbols)),
        })
        print(json.dumps(rows[-1], ensure_ascii=False), flush=True)

    summary = {
        'schema_version': 'stage3-eval-run/1',
        'cases': rows,
        'total_cases': len(rows),
        'done': sum(1 for r in rows if r['status'] == 'done'),
        'zero_claims': sum(1 for r in rows if r['status'] == 'zero_claims'),
        'reproduced_total': sum(r.get('reproduced', 0) for r in rows),
        'compile_blocked_total': sum(r.get('compile_blocked', 0) for r in rows),
        'compile_error_total': sum(r.get('compile_error', 0) for r in rows),
        'not_dynamically_expressible_total': sum(
            r.get('not_dynamically_expressible', 0) for r in rows),
        'reference_patch_required_total': sum(
            r.get('reference_patch_required', 0) for r in rows),
        'halt_witness_required_total': sum(
            r.get('halt_witness_required', 0) for r in rows),
        'bindability_single_anchor_total': sum(
            (r.get('bindabilities') or []).count('single_anchor') for r in rows),
        'bindability_multi_contract_total': sum(
            (r.get('bindabilities') or []).count('multi_contract') for r in rows),
        'bindability_file_level_total': sum(
            (r.get('bindabilities') or []).count('file_level') for r in rows),
        'bindability_no_anchor_total': sum(
            (r.get('bindabilities') or []).count('no_anchor') for r in rows),
        'unobservable_symbols_total': sum(
            len(r.get('unobservable_symbols') or []) for r in rows),
    }
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n')
    print('\nSUMMARY')
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
