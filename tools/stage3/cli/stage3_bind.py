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
import subprocess
import sys
from pathlib import Path

from lib.spec_loader import SpecError, load_stage2_run
from lib.case_runner import bind_claims

ROOT = Path(__file__).resolve().parents[1]  # tools/stage3


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

    result = bind_claims(
        case_dir=case_dir, stage2_dir=stage2_dir, src_dir=src_dir,
        claims=claims, formal=stage2['formal'], spec=stage2['spec'],
        max_rounds=args.max_rounds, reuse=args.reuse,
        strict=True, apply_ceiling=False, run_fn=subprocess.run)

    rows = []
    for claim_id in claims:
        record = result['records'][claim_id]
        rows.append({
            'claim_id': claim_id,
            'status': record['status'],
            'rounds_used': record['rounds_used'],
            'unbound': record['unbound'],
            'binding': record['binding'],
            'detail': record['detail'],
        })

    bound = sum(1 for row in rows if row['status'] == 'bound')
    reused = sum(1 for row in rows if row['status'] == 'reused')
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
