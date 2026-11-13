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
import subprocess
import sys
from pathlib import Path

from lib.spec_loader import SpecError, load_stage2_run
from lib.case_runner import (bind_claims, ceiling_verdict_for_bindability,
                             derive_verdicts, run_multi, verdict_counts)

ROOT = Path(__file__).resolve().parents[1]


_ceiling_verdict_for_bindability = ceiling_verdict_for_bindability


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

        bind_result = bind_claims(
            case_dir=case_dir, stage2_dir=stage2_dir, src_dir=case_dir / 'src',
            claims=claims, formal=spec['formal'],
            max_rounds=args.max_binding_rounds, reuse=args.skip_llm,
            strict=False, apply_ceiling=True, run_fn=subprocess.run)
        bound_claim_ids = bind_result['bound_claim_ids']
        routed_verdicts = bind_result['routed_verdicts']
        failed = bind_result['failed']
        bindabilities = [
            bind_result['records'][claim_id]['bindability'] for claim_id in claims
        ]

        from lib.bindability_contract import write_contract
        write_contract(case_dir, stage2_dir, claims)

        multi_verdicts = run_multi(
            case_dir=case_dir, bindings_dir=bindings_dir,
            stage2_run_dir=case_dir / 'stage2_run',
            bound_claim_ids=bound_claim_ids, run_id_prefix=cid,
            run_fn=subprocess.run)
        verdicts = derive_verdicts(
            claims=claims, routed_verdicts=routed_verdicts,
            bound_claim_ids=bound_claim_ids, multi_verdicts=multi_verdicts)
        counts = verdict_counts(verdicts)
        bound = len(bound_claim_ids)

        if bound == 0 and not routed_verdicts:
            rows.append({'case': cid, 'status': 'no_bound_claims',
                         'claims': len(claims), 'failed': failed,
                         'unobservable_symbols': []})
            continue

        rows.append({
            'case': cid, 'status': 'done',
            'claims': len(claims), 'bound': bound,
            'claim_ids': claims,
            'verdicts': verdicts,
            'reproduced': counts['reproduced'],
            'compile_blocked': counts['compile_blocked'],
            'compile_error': counts['compile_error'],
            'not_dynamically_expressible': counts['not_dynamically_expressible'],
            'reference_patch_required': counts['reference_patch_required'],
            'halt_witness_required': counts['halt_witness_required'],
            'bound_claim_ids': bound_claim_ids,
            'bindabilities': bindabilities,
            'failed_bindings': failed,
            'unobservable_symbols': [],
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
