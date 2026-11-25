#!/usr/bin/env python3
"""Rank Stage-2 claims by code observability before Stage-3 binding.

The preflight uses only the frozen Stage-2 artifacts and the Stage-1 source
slice.  It never inspects a Stage-3 verdict, so it cannot select claims because
they happened to pass.  Claims whose P/I/V symbols have no visible expression
at the injection point are marked unobservable and are not promoted into the
candidate Stage-2 goldset.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STAGE3 = HERE.parents[1]
if str(STAGE3) not in sys.path:
    sys.path.insert(0, str(STAGE3))
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from lib import observable_ir  # noqa: E402
from lib.spec_loader import load_stage2_run, required_symbols  # noqa: E402

SCHEMA_VERSION = 'stage2-observability-preflight/1'


def _load(path: Path) -> dict:
    try:
        payload = json.loads(Path(path).read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _ready_recipes(symbol_row: dict) -> list[dict]:
    plan = symbol_row.get('recipe_plan') or {}
    return [
        row for row in (plan.get('recipes') or [])
        if isinstance(row, dict) and row.get('expression')
        and row.get('executable') and row.get('confidence') == 'high'
    ]


def score_claim(stage2_dir: Path, claim_id: str, src: Path) -> dict:
    run = load_stage2_run(Path(stage2_dir))
    symbols = sorted(required_symbols(run['spec'], claim_id))
    ir = observable_ir.build_contract(Path(stage2_dir), claim_id, Path(src))
    rows = []
    for symbol in symbols:
        row = (ir.get('symbols') or {}).get(symbol) or {}
        candidates = row.get('candidates') or []
        visible = [item for item in candidates
                   if item.get('visible_at_injection')]
        grounded = [item for item in candidates
                    if item.get('source_grounded')]
        recipes = _ready_recipes(row)
        if visible:
            value = 1.0
            route = 'visible'
        elif recipes:
            value = 0.75
            route = 'recipe'
        elif grounded:
            value = 0.5
            route = 'source_grounded'
        else:
            value = 0.0
            route = 'unobservable'
        rows.append({
            'symbol': symbol,
            'role': ','.join(row.get('roles') or []),
            'route': route,
            'score': value,
            'candidate_count': len(candidates),
        })
    ratio = (sum(row['score'] for row in rows) / len(rows)
             if rows else 0.0)
    return {
        'claim_id': claim_id,
        'observable_ratio': round(ratio, 4),
        'symbols': rows,
        'unobservable_symbols': [row['symbol'] for row in rows
                                 if row['route'] == 'unobservable'],
    }


def build(stage2_root: Path, flatten_root: Path, out_root: Path, *,
          cases: list[str] | None = None, limit: int = 3,
          min_ratio: float = 0.6) -> dict:
    stage2_root = Path(stage2_root)
    flatten_root = Path(flatten_root)
    out_root = Path(out_root)
    if out_root.exists():
        shutil.rmtree(out_root)
    out_root.mkdir(parents=True)
    wanted = set(cases or [path.name for path in stage2_root.iterdir()
                           if path.is_dir()])
    case_rows = []
    for case in sorted(wanted):
        source = stage2_root / case
        spec_path = source / 'stage3-spec.json'
        slice_path = flatten_root / case / 'contract.flattened.t.sol'
        if not spec_path.is_file() or not slice_path.is_file():
            continue
        spec = _load(spec_path)
        ranked = [score_claim(source, str(row['claim_id']), slice_path)
                  for row in spec.get('claims') or []
                  if isinstance(row, dict) and row.get('claim_id')]
        ranked.sort(key=lambda row: (-row['observable_ratio'],
                                     row['claim_id']))
        selected_ids = [row['claim_id'] for row in ranked
                        if row['observable_ratio'] >= min_ratio][:limit]
        if not selected_ids:
            continue
        destination = out_root / case
        shutil.copytree(source, destination)
        spec['claims'] = [row for row in spec.get('claims') or []
                          if str(row.get('claim_id')) in set(selected_ids)]
        (destination / 'stage3-spec.json').write_text(
            json.dumps(spec, ensure_ascii=False, indent=2) + '\n',
            encoding='utf-8')
        (destination / 'observability-ranking.json').write_text(
            json.dumps({
                'schema_version': SCHEMA_VERSION,
                'case': case,
                'ranked': ranked,
                'selected_claim_ids': selected_ids,
            }, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        provenance = _load(destination / 'provenance.json')
        provenance['observability_preflight'] = {
            'schema_version': SCHEMA_VERSION,
            'selected_claim_ids': selected_ids,
            'min_ratio': min_ratio,
        }
        (destination / 'provenance.json').write_text(
            json.dumps(provenance, ensure_ascii=False, indent=2) + '\n',
            encoding='utf-8')
        case_rows.append({
            'case': case,
            'input_claims': len(ranked),
            'selected_claim_ids': selected_ids,
            'ranking': ranked,
        })
    report = {
        'schema_version': SCHEMA_VERSION,
        'stage2_root': str(stage2_root.resolve()),
        'flatten_root': str(flatten_root.resolve()),
        'out_root': str(out_root.resolve()),
        'limit': limit,
        'min_ratio': min_ratio,
        'cases': case_rows,
    }
    (out_root / 'preflight-report.json').write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + '\n',
        encoding='utf-8')
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage2-root', type=Path, required=True)
    parser.add_argument('--flatten-root', type=Path, required=True)
    parser.add_argument('--out-root', type=Path, required=True)
    parser.add_argument('--case', action='append', default=[])
    parser.add_argument('--limit', type=int, default=3)
    parser.add_argument('--min-ratio', type=float, default=0.6)
    args = parser.parse_args(argv)
    report = build(args.stage2_root, args.flatten_root, args.out_root,
                   cases=args.case, limit=args.limit,
                   min_ratio=args.min_ratio)
    print(json.dumps({
        'schema_version': SCHEMA_VERSION,
        'cases': len(report['cases']),
        'selected': sum(len(row['selected_claim_ids'])
                        for row in report['cases']),
        'out_root': str(args.out_root),
    }, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
