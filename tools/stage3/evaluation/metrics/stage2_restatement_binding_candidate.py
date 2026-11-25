#!/usr/bin/env python3
"""Stage-2 restatement-guided candidate-first binding for quarantined A/B.

The tool never edits the frozen goldset, labels, protocol, or authoritative
runs.  It prepares candidate case directories whose bindings are chosen before
any Stage-3 verdict is observed; the existing ``stage3_eval_run --skip-llm``
path then executes them.  Promotion remains governed by the negative recovery
gate.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STAGE3 = HERE.parents[1]
if str(STAGE3) not in sys.path:
    sys.path.insert(0, str(STAGE3))
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from lib import case_builder, stage2_contract, stage2_restate  # noqa: E402
from lib.binding import validate_binding  # noqa: E402
from lib.binding_validate import lint_binding  # noqa: E402
from lib.invariant_ranking import rank_claims  # noqa: E402
from lib.spec_loader import (SpecError, load_stage2_run,  # noqa: E402
                             precondition_symbols_for_claim,
                             safety_symbols_for_claim)

SCHEMA_VERSION = 'stage2-restatement-candidate-binding/1'


def _load(path: Path) -> dict:
    try:
        payload = json.loads(Path(path).read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _save(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n',
                    encoding='utf-8')


def _restatement_hint(stage2_dir: Path, formal: dict, spec: dict,
                      claim_id: str) -> dict:
    declaration = next(
        (row for row in spec.get('claims') or []
         if isinstance(row, dict) and row.get('claim_id') == claim_id), {})
    restatement = stage2_restate.restate_claim(
        formal, claim_id, declaration=declaration,
        formalization_contract=stage2_contract.load(stage2_dir, claim_id),
        observability=stage2_restate.load_observability(stage2_dir, claim_id))
    unresolved = [str(row.get('reason') or row.get('rule') or row)
                  for row in restatement.get('unresolved') or []
                  if isinstance(row, (dict, str))]
    changes = [str(row.get('rule') or row)
               for row in restatement.get('changes') or []
               if isinstance(row, (dict, str))]
    hint = 'stage2_restatement_status=' + str(restatement.get('status'))
    if unresolved:
        hint += '; unresolved=' + ','.join(sorted(set(unresolved))[:8])
    if changes:
        hint += '; restatement_rules=' + ','.join(sorted(set(changes))[:8])
    return {'restatement': restatement, 'hint': hint}


def _unbound(binding: dict, symbols: set[str]) -> tuple[list[str], list[str]]:
    entries = binding.get('bindings') or {}
    unbound = [name for name, row in entries.items()
               if isinstance(row, dict)
               and str(row.get('solidity_expr') or '').strip().upper() == 'UNBOUND']
    invariant = sorted(set(unbound) & symbols)
    return invariant, sorted(unbound)


def _score_proposal(path: Path, *, spec: dict, formal: dict, claim_id: str,
                    case_dir: Path, index: int) -> dict | None:
    row: dict = {'index': index, 'binding_path': str(path)}
    try:
        binding = json.loads(path.read_text())
        validate_binding(binding, spec)
    except (OSError, ValueError, SpecError) as exc:
        row.update({'accepted': False, 'error': str(exc)})
        return row
    symbols = safety_symbols_for_claim(formal, claim_id)
    symbols |= precondition_symbols_for_claim(formal, claim_id)
    invariant_unbound, unbound = _unbound(binding, symbols)
    lint = lint_binding(binding, case_dir / 'src',
                        test_dir=case_dir / 'test', strict=False,
                        safety_symbols=symbols)
    errors = int((lint.get('summary') or {}).get('errors') or 0)
    row.update({
        'accepted': errors == 0,
        'lint_errors': errors,
        'invariant_unbound': invariant_unbound,
        'unbound': unbound,
        'sort_key': [len(invariant_unbound), errors, len(unbound), index],
    })
    return row


def _prepare_case(out_root: Path, case: str, stage2_dir: Path,
                  flatten: Path) -> Path:
    case_dir = out_root / 'cases' / case
    if case_dir.exists():
        case_builder.refresh_stage2_run(stage2_dir, case_dir)
    else:
        case_builder.assemble_case(
            name=case, src=flatten, stage2_run=stage2_dir, test=None,
            out=case_dir, default_foundry_toml=True, src_name='Contract.sol')
    manifest = flatten.parent / 'harness-manifest.json'
    if manifest.is_file():
        shutil.copyfile(manifest, case_dir / 'harness-manifest.json')
    return case_dir


def _bind_claim(*, case: str, claim_id: str, stage2_dir: Path, case_dir: Path,
                out_root: Path, formal: dict, spec: dict, hint: str,
                candidates: int, run_fn) -> dict:
    proposal_root = out_root / 'proposals' / case / claim_id
    rows = []
    previous_hint = hint
    for index in range(1, candidates + 1):
        proposal_dir = proposal_root / f'candidate_{index}'
        if proposal_dir.exists():
            shutil.rmtree(proposal_dir)
        proposal_dir.mkdir(parents=True)
        command = [sys.executable, '-m', 'cli.stage3_binding_llm',
                   '--stage2-run', str(stage2_dir), '--claim-id', claim_id,
                   '--src', str(case_dir / 'src'), '--out', str(proposal_dir),
                   '--hint', previous_hint]
        run_fn(command, capture_output=True, text=True, cwd=str(STAGE3))
        proposal_path = proposal_dir / 'binding.proposal.json'
        row = _score_proposal(proposal_path, spec=spec['spec'], formal=formal,
                              claim_id=claim_id, case_dir=case_dir,
                              index=index)
        if row is None:
            row = {'index': index, 'accepted': False,
                   'error': 'no proposal file'}
        try:
            proposal = json.loads(proposal_path.read_text())
        except (OSError, ValueError):
            proposal = {}
        row['proposal'] = {
            'ok': bool(proposal.get('ok')),
            'partial': bool(proposal.get('partial')),
            'unbound': sorted(proposal.get('unbound') or []),
        }
        rows.append(row)
        unbound = row.get('unbound') or []
        if unbound:
            previous_hint = hint + '; reject_unbound=' + ','.join(unbound[:8])

    accepted = [row for row in rows if row.get('accepted')]
    accepted.sort(key=lambda row: row['sort_key'])
    selected = accepted[0] if accepted else None
    binding_path = case_dir / 'bindings' / f'{claim_id}.json'
    if selected is not None:
        binding_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(selected['binding_path'], binding_path)
    return {
        'claim_id': claim_id,
        'restatement_hint': hint,
        'candidates': rows,
        'selected': (selected or {}).get('index'),
        'binding': str(binding_path) if selected is not None else None,
    }


def build(stage2_root: Path, flatten_root: Path, out_root: Path, *,
          cases: list[str] | None = None, candidates: int = 3,
          claim_limit: int = 3, run_fn=subprocess.run) -> dict:
    stage2_root = Path(stage2_root).resolve()
    flatten_root = Path(flatten_root).resolve()
    out_root = Path(out_root).resolve()
    if out_root.exists():
        shutil.rmtree(out_root)
    out_root.mkdir(parents=True)
    wanted = set(cases or [path.name for path in stage2_root.iterdir()
                           if path.is_dir()])
    case_rows = []
    for case in sorted(wanted):
        stage2_dir = stage2_root / case
        spec_path = stage2_dir / 'stage3-spec.json'
        flatten = flatten_root / case / 'contract.flattened.t.sol'
        if not spec_path.is_file() or not flatten.is_file():
            continue
        spec = load_stage2_run(stage2_dir)
        ranking = rank_claims(stage2_dir, spec['spec'], limit=claim_limit)
        claims = [claim_id for claim_id in ranking['selected_claim_ids']
                  if any(row.get('claim_id') == claim_id
                         for row in spec['spec'].get('claims') or [])]
        if not claims:
            continue
        case_dir = _prepare_case(out_root, case, stage2_dir, flatten)
        claim_rows = []
        for claim_id in claims:
            guided = _restatement_hint(stage2_dir, spec['formal'],
                                       spec['spec'], claim_id)
            claim_rows.append(_bind_claim(
                case=case, claim_id=claim_id, stage2_dir=stage2_dir,
                case_dir=case_dir, out_root=out_root, formal=spec['formal'],
                spec=spec, hint=guided['hint'], candidates=candidates,
                run_fn=run_fn))
        case_rows.append({
            'case': case,
            'selected_claim_ids': claims,
            'claims': claim_rows,
        })
    report = {
        'schema_version': SCHEMA_VERSION,
        'stage2_root': str(stage2_root.resolve()),
        'flatten_root': str(flatten_root.resolve()),
        'out_root': str(out_root.resolve()),
        'candidates': candidates,
        'claim_limit': claim_limit,
        'cases': case_rows,
    }
    _save(out_root / 'candidate-binding-report.json', report)
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage2-root', type=Path, required=True)
    parser.add_argument('--flatten-root', type=Path, required=True)
    parser.add_argument('--out-root', type=Path, required=True)
    parser.add_argument('--case', action='append', default=[])
    parser.add_argument('--candidates', type=int, default=3)
    parser.add_argument('--claim-limit', type=int, default=3)
    args = parser.parse_args(argv)
    report = build(args.stage2_root, args.flatten_root, args.out_root,
                   cases=args.case, candidates=args.candidates,
                   claim_limit=args.claim_limit)
    selected = sum(1 for row in report['cases'] for claim in row['claims']
                   if claim['selected'] is not None)
    print(json.dumps({
        'schema_version': SCHEMA_VERSION,
        'cases': len(report['cases']),
        'claims': sum(len(row['claims']) for row in report['cases']),
        'selected_bindings': selected,
        'out_root': str(args.out_root),
    }, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
