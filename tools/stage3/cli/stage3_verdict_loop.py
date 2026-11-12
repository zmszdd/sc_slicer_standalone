#!/usr/bin/env python3
"""Close the stage-3 loop for binding-repairable verdicts.

For each claim in a stage-2 run: run the single-claim differential pipeline,
read the consistency verdict, and for binding-fixable outcomes re-propose the
binding with the replan diagnostic as a repair hint, then re-run. The loop is
bounded by ``--max-rounds``; terminal verdicts stop immediately.

Run with cwd = tools/stage3:
    python -m cli.stage3_verdict_loop --case-dir cases/smoke_vault
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from lib.spec_loader import SpecError, load_stage2_run
from lib.binding_validate import lint_binding
from lib.verdict_loop import verdict_action, repair_hint

ROOT = Path(__file__).resolve().parents[1]  # tools/stage3


def _run_pipeline(case_dir: Path, stage2_dir: Path, binding_path: Path,
                  run_id: str) -> tuple[int, dict | None, str]:
    proc = subprocess.run(
        [sys.executable, '-m', 'cli.stage3_pipeline',
         '--case-dir', str(case_dir), '--stage2-run', str(stage2_dir),
         '--binding', str(binding_path), '--run-id', run_id],
        capture_output=True, text=True, cwd=str(ROOT))
    if proc.returncode != 0:
        return proc.returncode, None, (proc.stderr or proc.stdout or '')[:1500]
    try:
        return 0, json.loads(proc.stdout), ''
    except ValueError:
        return 1, None, (proc.stdout or proc.stderr or '')[:1500]


def _propose(case_dir: Path, stage2_dir: Path, claim_id: str,
             hint: str | None) -> tuple[dict | None, str]:
    out_dir = case_dir / 'llm_proposal'
    cmd = [sys.executable, '-m', 'cli.stage3_binding_llm',
           '--stage2-run', str(stage2_dir), '--claim-id', claim_id,
           '--src', str(case_dir / 'src'), '--out', str(out_dir)]
    if hint:
        cmd += ['--hint', hint]
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=str(ROOT))
    try:
        payload = json.loads(proc.stdout)
    except ValueError:
        return None, (proc.stderr or proc.stdout or '')[:800]
    if not isinstance(payload, dict):
        return None, 'proposal was not an object'
    if not payload.get('ok'):
        problems = payload.get('problems') or []
        if payload.get('partial'):
            problems.append('unbound: ' + ', '.join(payload.get('unbound', [])))
        return None, '; '.join(str(problem) for problem in problems[:12])
    proposal_path = out_dir / 'binding.proposal.json'
    if not proposal_path.is_file():
        return None, 'no proposal file written'
    binding = json.loads(proposal_path.read_text())
    lint = lint_binding(binding, case_dir / 'src',
                        test_dir=case_dir / 'test', strict=True)
    if lint['summary']['errors']:
        problems = [f"{problem['where']}: {problem['message']}"
                    for problem in lint['problems']]
        return None, '; '.join(problems[:12])
    return binding, ''


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case-dir', type=Path, required=True)
    parser.add_argument('--stage2-run', type=Path,
                        help='defaults to <case-dir>/stage2_run')
    parser.add_argument('--max-rounds', type=int, default=2)
    parser.add_argument('--run-id-prefix', help='defaults to case directory name')
    args = parser.parse_args(argv)

    case_dir = args.case_dir.resolve()
    stage2_dir = (args.stage2_run or case_dir / 'stage2_run').resolve()
    prefix = args.run_id_prefix or case_dir.name
    bindings_dir = case_dir / 'bindings'
    bindings_dir.mkdir(parents=True, exist_ok=True)

    try:
        stage2 = load_stage2_run(stage2_dir)
    except SpecError as exc:
        raise SystemExit(f'input error: {exc}')

    claims = [row['claim_id'] for row in stage2['spec'].get('claims', [])
              if isinstance(row, dict) and 'claim_id' in row]
    if not claims:
        raise SystemExit('no claims in stage3-spec.json')

    rows = []
    for claim_id in claims:
        binding_path = bindings_dir / f'{claim_id}.json'
        trajectory = []
        final = {'claim_id': claim_id, 'status': 'exhausted', 'trajectory': []}
        for round_no in range(1, args.max_rounds + 1):
            if not binding_path.is_file():
                binding, problem = _propose(case_dir, stage2_dir, claim_id, None)
                if binding is None:
                    final = {'claim_id': claim_id, 'status': 'binding_failed',
                             'detail': problem, 'trajectory': trajectory}
                    break
                binding_path.write_text(
                    json.dumps(binding, ensure_ascii=False, indent=2) + '\n')
            run_id = f'{prefix}__{claim_id}__r{round_no}'
            code, summary, error = _run_pipeline(
                case_dir, stage2_dir, binding_path, run_id)
            if code != 0 or summary is None:
                trajectory.append({'round': round_no, 'status': 'pipeline_error',
                                   'detail': error[:400]})
                continue
            verdict = summary.get('consistency_verdict')
            trajectory.append({'round': round_no, 'verdict': verdict,
                               'run_id': run_id})
            action = verdict_action(verdict, summary)
            if action == 'accept':
                final = {'claim_id': claim_id, 'status': 'accepted',
                         'verdict': verdict, 'trajectory': trajectory}
                break
            if action == 'skip':
                poc_not_witnessed = (
                    verdict == 'poc_not_witnessed'
                    or (verdict == 'preconditions_infeasible_on_code'
                        and (summary or {}).get('precondition_failure')
                        == 'poc_not_witnessed'))
                if verdict == 'not_dynamically_expressible':
                    status = verdict
                elif poc_not_witnessed:
                    status = 'poc_not_witnessed'
                else:
                    status = 'compile_blocked'
                final = {'claim_id': claim_id, 'status': status,
                         'verdict': verdict, 'trajectory': trajectory}
                break
            consistency = None
            artifact = summary.get('verdict_artifact')
            if artifact and Path(artifact).is_file():
                try:
                    consistency = json.loads(Path(artifact).read_text())
                except ValueError:
                    consistency = None
            hint = repair_hint(summary, consistency)
            binding, problem = _propose(case_dir, stage2_dir, claim_id, hint)
            if binding is None:
                trajectory.append({'round': round_no, 'status': 'repair_failed',
                                   'detail': problem[:400]})
                final = {'claim_id': claim_id, 'status': 'repair_exhausted',
                         'detail': problem[:400], 'trajectory': trajectory}
                break
            binding_path.write_text(
                json.dumps(binding, ensure_ascii=False, indent=2) + '\n')
        else:
            final = {'claim_id': claim_id, 'status': 'exhausted',
                     'trajectory': trajectory}
        rows.append(final)
        print(json.dumps(final, ensure_ascii=False), flush=True)

    payload = {
        'schema_version': 'stage3-verdict-loop/1',
        'case': str(case_dir),
        'claims': rows,
        'total': len(rows),
        'accepted': sum(1 for row in rows if row['status'] == 'accepted'),
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
