#!/usr/bin/env python3
"""Continuous stage-3 consumer for the mainline sample.

The mainline executor produces stage-2 outputs in batches.  Instead of waiting
for every stage-2 chunk, this script repeatedly builds the goldset from the
latest ``mainline_stage2_out`` and runs stage-3 eval for ready, not-yet-done
cases.  It is safe to run concurrently with ``run_mainline.py``; the two
processes share ``mainline_eval.json`` and the executor skips rows already
marked done.
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from run_mainline import (SAMPLE, STAGE2_OUT_DEFAULT, GOLDSET_DEFAULT,
                          CASES_DEFAULT, EVAL_OUT_DEFAULT, FLATTEN_DEFAULT,
                          _load, _build_goldset, _run_stage3_parallel)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sample', type=Path, default=SAMPLE)
    parser.add_argument('--flatten-root', type=Path, default=FLATTEN_DEFAULT)
    parser.add_argument('--stage2-out', type=Path, default=STAGE2_OUT_DEFAULT)
    parser.add_argument('--goldset-root', type=Path, default=GOLDSET_DEFAULT)
    parser.add_argument('--cases-root', type=Path, default=CASES_DEFAULT)
    parser.add_argument('--eval-out', type=Path, default=EVAL_OUT_DEFAULT)
    parser.add_argument('--concurrency', type=int, default=3)
    parser.add_argument('--idle-seconds', type=int, default=30)
    parser.add_argument('--max-idle-cycles', type=int, default=40)
    args = parser.parse_args(argv)

    sample = _load(args.sample)
    positives = sample.get('positive_cases', [])
    idle = 0
    while idle < args.max_idle_cycles:
        ready = _build_goldset(sample, args.stage2_out, args.goldset_root)
        if not ready:
            idle += 1
            time.sleep(args.idle_seconds)
            continue
        before = len(ready)
        _run_stage3_parallel(ready, args.goldset_root, args.flatten_root,
                             args.cases_root, args.eval_out, args.concurrency)
        # After one pass, detect whether any new stage-2 outputs appeared.
        ready_after = _build_goldset(sample, args.stage2_out, args.goldset_root)
        grew = len(ready_after) > before
        idle = 0 if grew else idle + 1
        if not grew:
            time.sleep(args.idle_seconds)


if __name__ == '__main__':
    main()
