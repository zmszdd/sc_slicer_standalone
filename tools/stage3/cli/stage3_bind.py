#!/usr/bin/env python3
"""Propose stage-3 bindings for every claim in a stage-2 run.

This is the mainline auto-binding entry: given an assembled case (``src/`` +
``stage2_run/``), it writes one ``bindings/<claim_id>.json`` per claim by
reusing the same DeepSeek binding loop as ``stage3_eval_run``, then emits a
summary that ``stage3_multi`` can consume directly.

Run with cwd = tools/stage3:
    python -m cli.stage3_bind --case-dir cases/<case> --stage2-run <dir>
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

from lib.spec_loader import SpecError, load_stage2_run
from lib.binding_validate import lint_binding

ROOT = Path(__file__).resolve().parents[1]  # tools/stage3


def _round_hint(claim_id: str, round_no: int, problems: list[str]) -> str:
    items = '; '.join(str(problem) for problem in problems[:12])
    return (f'round {round_no} failed for claim {claim_id}. '
            f'Fix these problems: {items}.')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case-dir', required=True)
    parser.add_argument('--stage2-run', help='defaults to <case-dir>/stage2_run')
    parser.add_argument('--binding-rounds', '--max-rounds', dest='max_rounds',
                        type=int, default=3,
                        help='LLM binding repair rounds per claim (default 3)')
    parser.add_argument('--claims', default=None,
                        help='comma-separated claim ids; default: all in spec')
    parser.add_argument('--reuse', action='store_true',
                        help='skip claims that already have bindings/<claim_id>.json')
    args = parser.parse_args(argv)

    case_dir = Path(args.case_dir).resolve()
    stage2_dir = (Path(args.stage2_run) if args.stage2_run
                  else case_dir / 'stage2_run').resolve()
    src_dir = case_dir / 'src'

    try:
        stage2 = load_stage2_run(stage2_dir)
    except SpecError as exc:
        raise SystemExit(f'input error: {exc}')

    claims = [row['claim_id'] for row in stage2['spec'].get('claims', [])
              if isinstance(row, dict) and 'claim_id' in row]
    if args.claims:
        selected = {c.strip() for c in args.claims.split(',') if c.strip()}
        claims = [c for c in claims if c in selected]
    if not claims:
        raise SystemExit('no claims in stage3-spec.json')

    bindings_dir = case_dir / 'bindings'
    bindings_dir.mkdir(parents=True, exist_ok=True)

    rows = []
    reused = 0
    for claim_id in claims:
        binding_path = bindings_dir / f'{claim_id}.json'
        if args.reuse and binding_path.is_file():
            reused += 1
            rows.append({'claim_id': claim_id, 'status': 'reused',
                         'rounds_used': 0, 'unbound': [],
                         'binding': str(binding_path), 'detail': None})
            continue
        proposal_dir = case_dir / 'llm_proposal'
        hint = None
        accepted = False
        bound_counted = False
        unbound = []
        rounds_used = 0
        for round_no in range(1, args.max_rounds + 1):
            rounds_used = round_no
            cmd = [sys.executable, '-m', 'cli.stage3_binding_llm',
                   '--stage2-run', str(stage2_dir), '--claim-id', claim_id,
                   '--src', str(src_dir), '--out', str(proposal_dir)]
            if hint:
                cmd += ['--hint', hint]
            if round_no > 1 and binding_path.is_file():
                cmd += ['--existing', str(binding_path)]
            proc = subprocess.run(cmd, capture_output=True, text=True,
                                  cwd=str(ROOT))
            try:
                proposal = json.loads(proc.stdout)
            except ValueError:
                proposal = None
            if proposal is None or not isinstance(proposal, dict):
                hint = _round_hint(claim_id, round_no,
                                   ['transport: ' + (proc.stderr or proc.stdout)[:200]])
                continue
            if proposal.get('partial') and not proposal.get('problems'):
                written = proposal_dir / 'binding.proposal.json'
                if written.is_file():
                    shutil.copy2(written, binding_path)
                    accepted = True
                    if not bound_counted:
                        bound_counted = True
                    unbound = list(proposal.get('unbound') or [])
                    if round_no < args.max_rounds:
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
                hint = _round_hint(claim_id, round_no, problems)
                continue
            written = proposal_dir / 'binding.proposal.json'
            if not written.is_file():
                hint = _round_hint(claim_id, round_no, ['no proposal file written'])
                continue
            binding = json.loads(written.read_text())
            lint = lint_binding(binding, src_dir,
                                test_dir=case_dir / 'test', strict=True)
            if lint['summary']['errors']:
                problems = [f"{problem['where']}: {problem['message']}"
                            for problem in lint['problems']]
                hint = _round_hint(claim_id, round_no, problems)
                continue
            shutil.copy2(written, binding_path)
            accepted = True
            bound_counted = True
            break

        rows.append({
            'claim_id': claim_id,
            'status': 'bound' if accepted else 'failed',
            'rounds_used': rounds_used,
            'unbound': unbound,
            'binding': str(binding_path) if accepted else None,
            'detail': hint if not accepted else None,
        })

    bound = sum(1 for row in rows if row['status'] == 'bound')
    payload = {
        'schema_version': 'stage3-bind-summary/1',
        'case': str(case_dir),
        'stage2_run': str(stage2_dir),
        'total_claims': len(rows),
        'bound': bound,
        'reused': reused,
        'failed': len(rows) - bound - reused,
        'claims': rows,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload['failed'] == 0 else 1


if __name__ == '__main__':
    raise SystemExit(main())
