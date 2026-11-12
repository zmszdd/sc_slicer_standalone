#!/usr/bin/env python3
"""Emit a binding.json skeleton for one stage-2 claim."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from lib.binding_skeleton import build_skeleton
from lib.spec_loader import SpecError


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage2-run', required=True)
    parser.add_argument('--claim-id', required=True)
    parser.add_argument('--out', required=True, help='binding.skeleton.json path')
    parser.add_argument('--src', default=None,
                        help='optional src dir/file; adds source candidates to hints')
    args = parser.parse_args(argv)

    try:
        skeleton = build_skeleton(Path(args.stage2_run), args.claim_id,
                                  src=Path(args.src) if args.src else None)
    except SpecError as exc:
        raise SystemExit(f'input error: {exc}')
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(skeleton, ensure_ascii=False, indent=2) + '\n')
    print(f'wrote binding skeleton: {out}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
