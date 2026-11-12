#!/usr/bin/env python3
"""Close the loop: run artifacts -> authoritative four metrics.

Run with cwd = tools/stage3:
    python -m cli.stage3_metrics_sync [--runs-dir runs]
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from lib.metrics_sync import sync

ROOT = Path(__file__).resolve().parents[1]  # tools/stage3


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runs-dir', type=Path,
                        default=ROOT / 'runs')
    args = parser.parse_args(argv)

    result = sync(args.runs_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
