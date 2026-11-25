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
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from lib.spec_loader import SpecError, load_stage2_run, safety_symbols_for_claim
from lib.bindability_contract import is_hard_ceiling, load_contract
from lib.binding_validate import lint_binding
from lib.verdict_loop import verdict_action, repair_hint

ROOT = Path(__file__).resolve().parents[1]  # tools/stage3


def _poc_shape(case_dir: Path) -> str:
    """Read-only PoC shape: revert-expected tests cannot be fixed by rebinding
    an injected invariant, so the loop must route them to the reference-patch
    ceiling instead of burning rounds.
    """
    src = case_dir / 'src'
    text = ''
    if src.is_dir():
        for sol in src.glob('*.sol'):
            try:
                text += sol.read_text(errors='ignore') + '\n'
            except OSError:
                continue
    bindings = case_dir / 'bindings'
    probe = None
    if bindings.is_dir():
        for binding_file in bindings.glob('*.json'):
            try:
                probe = json.loads(binding_file.read_text()).get('probe')
            except (OSError, json.JSONDecodeError):
                continue
            if probe:
                break
    if not probe:
        return 'no_body'
    name = probe.get('exploit_test')
    if not name:
        return 'no_body'
    match = re.search(rf'function\s+{re.escape(name)}\s*\([^)]*\)\s*[^{{]*\{{', text)
    if not match:
        return 'other_test'
    start = match.end() - 1
    depth = 0
    body = text[start:]
    for j, char in enumerate(body):
        if char == '{':
            depth += 1
        elif char == '}':
            depth -= 1
            if depth == 0:
                body = body[:j + 1]
                break
    if 'expectRevert' in body:
        return 'revert_expected_test'
    if re.search(r'assert(?:Eq|True|False|Le|Ge|Lt|Gt)?\s*\(', body):
        return 'state_assert_test'
    return 'other_test'


def _exhausted_status(bindability: dict, fallback: str) -> str:
    """Map a rebind-exhausted multi-contract claim to the reference-patch
    ceiling instead of leaving it mislabelled as a rebindable failure.

    ``multi_contract`` is the only bindability class whose observables live in
    another contract; when the binding LLM still cannot bind its safety symbols
    after ``--max-rounds``, the invariant is genuinely inexpressible as a single
    injected assert(I), so the next correct mainline action is an M1 reference
    patch rather than another binding round.
    """
    if bindability.get('bindability') == 'multi_contract':
        return 'reference_patch_required'
    return fallback


def _fresh_run_prefix(run_id_prefix: str | None, name: str,
                       now=None) -> str:
    """Timestamped run-id prefix so re-runs never collide with a
    previous session's deterministic ``<case>__<claim>__rN`` run dir.
    """
    stamp = (now or datetime.now(timezone.utc)).strftime('%Y%m%dT%H%M%S%f')
    return f'{run_id_prefix or name}__{stamp}'


def _terminal_record(claim_id: str, verdict: str | None,
                     trajectory: list[dict]) -> dict:
    """Record for a terminal verdict.

    ``status == accepted`` historically meant "a terminal verdict was reached",
    but both ``violation_reproduced`` and ``violation_not_reproduced`` are
    terminal.  ``reproduced`` makes the distinction explicit so callers don't
    count a non-reproduction as a recovered claim.
    """
    return {
        'claim_id': claim_id,
        'status': 'accepted',
        'verdict': verdict,
        'reproduced': verdict == 'violation_reproduced',
        'trajectory': trajectory,
    }


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


def _lint_proposal(binding: dict, case_dir: Path, stage2_dir: Path,
                   claim_id: str) -> dict:
    """Lint a proposal with the safety-symbol scope.

    A bare ``true``/``false`` binding is vacuous only when it waters down the
    safety (I) expression itself; a faithful P-side precondition bound to
    ``true`` must pass. This mirrors the eval-run lint scope so the repair loop
    does not reject valid preconditions.
    """
    try:
        stage2 = load_stage2_run(stage2_dir)
        safety_symbols = safety_symbols_for_claim(stage2['formal'], claim_id)
    except SpecError:
        safety_symbols = None
    return lint_binding(binding, case_dir / 'src',
                        test_dir=case_dir / 'test', strict=True,
                        safety_symbols=safety_symbols)


def _propose_once(case_dir: Path, stage2_dir: Path, claim_id: str,
                  hint: str | None) -> tuple[dict | None, str]:
    out_dir = case_dir / 'llm_proposal'
    cmd = [sys.executable, '-m', 'cli.stage3_binding_llm',
           '--stage2-run', str(stage2_dir), '--claim-id', claim_id,
           '--src', str(case_dir / 'src'), '--out', str(out_dir)]
    existing_path = case_dir / 'bindings' / f'{claim_id}.json'
    if existing_path.is_file():
        cmd += ['--existing', str(existing_path)]
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
    return json.loads(proposal_path.read_text()), ''


def _propose(case_dir: Path, stage2_dir: Path, claim_id: str,
             hint: str | None) -> tuple[dict | None, str]:
    """Propose a binding, retrying once with the lint failures as a hint.

    The first model proposal is frequently rejected by the deterministic lint
    (for example a vacuous ``solidity_expr: "true"`` on a safety symbol).
    Without this retry the loop marks ``binding_failed`` and stops before the
    model ever sees the lint message.
    """
    problems: list[str] = []
    for attempt in (0, 1):
        binding, problem = _propose_once(case_dir, stage2_dir, claim_id, hint)
        if binding is None:
            return None, problem
        lint = _lint_proposal(binding, case_dir, stage2_dir, claim_id)
        if not lint['summary']['errors']:
            return binding, ''


        problems = [f"{p['where']}: {p['message']}"
                    for p in lint['problems']]
        hint = ('binding lint rejected the proposal; fix exactly these '
                'problems and keep everything else unchanged: '
                + '; '.join(problems[:12]))
    return None, '; '.join(problems[:12])


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case-dir', type=Path, required=True)
    parser.add_argument('--stage2-run', type=Path,
                        help='defaults to <case-dir>/stage2_run')
    parser.add_argument('--max-rounds', type=int, default=2)
    parser.add_argument('--run-id-prefix', help='defaults to case directory name')
    parser.add_argument('--claims', default=None,
                        help='comma-separated claim ids to re-run; default: all')
    args = parser.parse_args(argv)

    case_dir = args.case_dir.resolve()
    stage2_dir = (args.stage2_run or case_dir / 'stage2_run').resolve()
    prefix = _fresh_run_prefix(args.run_id_prefix, case_dir.name)
    bindings_dir = case_dir / 'bindings'
    bindings_dir.mkdir(parents=True, exist_ok=True)

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

    rows = []
    for claim_id in claims:
        binding_path = bindings_dir / f'{claim_id}.json'
        trajectory = []
        final = {'claim_id': claim_id, 'status': 'exhausted', 'trajectory': []}
        bindability = load_contract(case_dir).get(claim_id, {})
        poc_shape = _poc_shape(case_dir)
        if is_hard_ceiling(bindability):
            final = {'claim_id': claim_id,
                     'status': 'not_dynamically_expressible',
                     'verdict': 'not_dynamically_expressible',
                     'trajectory': trajectory}
            rows.append(final)
            print(json.dumps(final, ensure_ascii=False), flush=True)
            continue
        for round_no in range(1, args.max_rounds + 1):
            if not binding_path.is_file():
                binding, problem = _propose(case_dir, stage2_dir, claim_id, None)
                if binding is None:
                    status = _exhausted_status(bindability, 'binding_failed')
                    final = {'claim_id': claim_id, 'status': status,
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
            action = verdict_action(verdict, summary)
            if (verdict == 'effect_observed_invariant_holds'
                    and poc_shape == 'revert_expected_test'):
                action = 'skip'
                verdict = 'reference_patch_required'
            trajectory.append({'round': round_no, 'verdict': verdict,
                               'run_id': run_id, 'action': action})
            if action == 'accept':
                final = _terminal_record(claim_id, verdict, trajectory)
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
                elif verdict == 'reference_patch_required':
                    status = verdict
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
                failed_status = ('evidence_exhausted'
                                 if action == 'collect_missing_evidence'
                                 else 'repair_exhausted')
                failed_status = _exhausted_status(bindability, failed_status)
                trajectory.append({'round': round_no,
                                   'status': ('evidence_collection_failed'
                                              if action == 'collect_missing_evidence'
                                              else 'repair_failed'),
                                   'detail': problem[:400]})
                final = {'claim_id': claim_id, 'status': failed_status,
                         'detail': problem[:400], 'trajectory': trajectory}
                break
            binding_path.write_text(
                json.dumps(binding, ensure_ascii=False, indent=2) + '\n')
        else:
            final = {'claim_id': claim_id,
                     'status': _exhausted_status(bindability, 'exhausted'),
                     'trajectory': trajectory}
        rows.append(final)
        print(json.dumps(final, ensure_ascii=False), flush=True)

    payload = {
        'schema_version': 'stage3-verdict-loop/1',
        'case': str(case_dir),
        'claims': rows,
        'total': len(rows),
        'accepted': sum(1 for row in rows if row['status'] == 'accepted'),
        'reproduced': sum(1 for row in rows if row.get('reproduced')),
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
