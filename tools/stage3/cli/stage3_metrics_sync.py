#!/usr/bin/env python3
"""Close the loop: run artifacts -> authoritative four metrics.

Run with cwd = tools/stage3:
    python -m cli.stage3_metrics_sync [--runs-dir runs]
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from lib.metrics_sync import sync, verify_consistency

ROOT = Path(__file__).resolve().parents[1]  # tools/stage3


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runs-dir', type=Path,
                        default=ROOT / 'runs')
    parser.add_argument('--check', action='store_true',
                        help='regenerate then fail on cross-file inconsistency')
    args = parser.parse_args(argv)

    result = sync(args.runs_dir)
    check = verify_consistency()
    result['consistency'] = check
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if check['ok'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
