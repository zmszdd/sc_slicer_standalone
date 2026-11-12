#!/usr/bin/env python3
"""Run the stage-3 pipeline over every case in a cases directory.

Each case is run in an isolated subprocess so one failing case cannot poison the
others. A batch summary is written in addition to each case's own run directory.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]  # tools/stage3


def _case_dirs(cases_root: Path, pattern: str | None) -> list[Path]:
    dirs = []
    for child in sorted(cases_root.iterdir()):
        if not child.is_dir():
            continue
        if not (child / 'binding.json').is_file():
            continue
        if pattern and pattern not in child.name:
            continue
        dirs.append(child)
    return dirs


def run_one(case_dir: Path) -> dict:
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')
    run_id = f'{case_dir.name}_{stamp}'
    proc = subprocess.run(
        [sys.executable, '-m', 'cli.stage3_pipeline',
         '--case-dir', str(case_dir.resolve()), '--run-id', run_id],
        capture_output=True, text=True, cwd=str(ROOT))
    if proc.returncode != 0:
        return {
            'case': case_dir.name,
            'status': 'error',
            'run_id': run_id,
            'detail': (proc.stderr or proc.stdout or '').strip()[:600],
        }
    summary = json.loads(proc.stdout)
    return {
        'case': case_dir.name,
        'status': 'ok',
        'run_id': run_id,
        'claim_id': summary.get('claim_id'),
        'consistency_verdict': summary.get('consistency_verdict'),
        'exploit_original': (summary.get('forge', {})
                             .get('exploit', {}).get('original', {}).get('status')),
        'exploit_patched': (summary.get('forge', {})
                            .get('exploit', {}).get('patched', {}).get('status')),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cases-root', required=True,
                        help='directory containing stage-3 case directories')
    parser.add_argument('--output', required=True, help='batch-summary.json path')
    parser.add_argument('--max-cases', type=int, default=0,
                        help='limit number of cases (0 = all)')
    parser.add_argument('--filter', dest='pattern',
                        help='only run case directory names containing this')
    args = parser.parse_args(argv)

    cases_root = Path(args.cases_root).resolve()
    if not cases_root.is_dir():
        raise SystemExit(f'--cases-root is not a directory: {cases_root}')
    dirs = _case_dirs(cases_root, args.pattern)
    if args.max_cases > 0:
        dirs = dirs[:args.max_cases]
    if not dirs:
        raise SystemExit('no stage-3 cases found (missing binding.json?)')

    rows = [run_one(d) for d in dirs]
    ok = sum(1 for row in rows if row['status'] == 'ok')
    failed = len(rows) - ok
    verdicts = {}
    for row in rows:
        if row['status'] == 'ok':
            key = row.get('consistency_verdict') or 'unknown'
            verdicts[key] = verdicts.get(key, 0) + 1
    payload = {
        'schema_version': 'stage3-batch-summary/1',
        'cases_root': str(cases_root),
        'total': len(rows),
        'ok': ok,
        'failed': failed,
        'verdicts': verdicts,
        'cases': rows,
    }
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if failed == 0 else 1


if __name__ == '__main__':
    raise SystemExit(main())
