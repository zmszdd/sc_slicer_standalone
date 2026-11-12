#!/usr/bin/env python3
"""Parallel three-stage pipeline entry.

Usage:
    python tools/pipeline/cli/pipeline_run.py --manifest <case.json> \
        [--run-dir DIR] [--skip-stage1] [--skip-stage2] [--serial] [--run-id ID]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]  # repo root
sys.path.insert(0, str(ROOT / 'tools' / 'pipeline'))

from lib.runner import run_pipeline  # noqa: E402


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', required=True)
    parser.add_argument('--run-dir', help='default: <manifest-dir>/runs/<case_id>')
    parser.add_argument('--skip-stage1', action='store_true')
    parser.add_argument('--skip-stage2', action='store_true')
    parser.add_argument('--serial', action='store_true',
                        help='run stage1 then stage2 sequentially for debugging')
    parser.add_argument('--run-id', help='stage-3 run id override')
    args = parser.parse_args(argv)

    try:
        rc, _run_dir = run_pipeline(
            manifest_path=Path(args.manifest),
            run_dir=Path(args.run_dir) if args.run_dir else None,
            skip_stage1=args.skip_stage1,
            skip_stage2=args.skip_stage2,
            serial=args.serial,
            run_id=args.run_id,
        )
        return rc
    except Exception as exc:  # noqa: BLE001 - surface any setup error cleanly
        print(f'pipeline error: {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
