#!/usr/bin/env python3
"""Run the stage-3 differential pipeline for every claim in a stage-2 run.

Bindings are supplied one file per claim under ``--bindings-dir``, named
``<claim_id>.json``. Each claim runs in its own subprocess with a distinct
run-id, so one failing claim cannot poison the others.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from lib.spec_loader import SpecError, load_stage2_run

ROOT = Path(__file__).resolve().parents[1]  # tools/stage3


def _dig(node, path, default=None):
    for key in path:
        if not isinstance(node, dict):
            return default
        node = node.get(key)
        if node is None:
            return default
    return node


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case-dir', required=True)
    parser.add_argument('--bindings-dir', required=True)
    parser.add_argument('--stage2-run', help='defaults to <case-dir>/stage2_run')
    parser.add_argument('--run-id-prefix', help='defaults to the case directory name')
    parser.add_argument('--claims', default=None,
                        help='comma-separated claim ids to run; default: all in spec')
    args = parser.parse_args(argv)

    case_dir = Path(args.case_dir).resolve()
    stage2_dir = (Path(args.stage2_run) if args.stage2_run
                  else case_dir / 'stage2_run').resolve()
    bindings_dir = Path(args.bindings_dir).resolve()
    prefix = args.run_id_prefix or case_dir.name

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
        binding = bindings_dir / f'{claim_id}.json'
        fixed_binding = bindings_dir / f'{claim_id}.fixed.json'
        if fixed_binding.is_file():
            binding = fixed_binding
        if not binding.is_file():
            rows.append({'claim_id': claim_id, 'status': 'error',
                         'consistency_verdict': 'binding_failed',
                         'detail': f'missing binding file: {binding}'})
            continue
        stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
        run_id = f'{prefix}__{claim_id}__{stamp}'
        proc = subprocess.run(
            [sys.executable, '-m', 'cli.stage3_pipeline',
             '--case-dir', str(case_dir), '--stage2-run', str(stage2_dir),
             '--binding', str(binding), '--run-id', run_id],
            capture_output=True, text=True, cwd=str(ROOT))
        if proc.returncode != 0:
            rows.append({'claim_id': claim_id, 'status': 'error', 'run_id': run_id,
                         'detail': (proc.stderr or proc.stdout or '').strip()[:400]})
            continue
        summary = json.loads(proc.stdout)
        rows.append({
            'claim_id': claim_id,
            'status': 'ok',
            'run_id': run_id,
            'consistency_verdict': _dig(summary, ['consistency_verdict']),
            'exploit_original': _dig(summary, ['forge', 'exploit', 'original', 'status']),
            'exploit_patched': _dig(summary, ['forge', 'exploit', 'patched', 'status']),
        })

    payload = {
        'schema_version': 'stage3-multi-summary/1',
        'case': str(case_dir),
        'total': len(rows),
        'ok': sum(1 for row in rows if row['status'] == 'ok'),
        'failed': sum(1 for row in rows if row['status'] != 'ok'),
        'claims': rows,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload['failed'] == 0 else 1


if __name__ == '__main__':
    raise SystemExit(main())
