#!/usr/bin/env python3
"""Propose one stage-3 binding via DeepSeek for a stage-2 claim.

Run with cwd = tools/stage3:
    python -m cli.stage3_binding_llm --stage2-run <dir> --claim-id <id> \
        --src cases/<case>/src --out <proposal dir>

Exit codes: 0 complete binding, 1 partial binding (some symbols UNBOUND),
2 proposal/transport failure. A partial binding is still written to
``binding.proposal.json`` for later manual completion.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from lib.binding_llm import propose_binding
from lib.spec_loader import SpecError


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage2-run', required=True)
    parser.add_argument('--claim-id', required=True)
    parser.add_argument('--src', required=True)
    parser.add_argument('--out', required=True)
    parser.add_argument('--hint', default=None,
                        help='repair hint describing a previous failed attempt')
    parser.add_argument('--existing', default=None,
                        help='existing partial binding.json; only its UNBOUND '
                             'symbols are re-proposed, others stay unchanged')
    args = parser.parse_args(argv)

    try:
        proposal = propose_binding(
            Path(args.stage2_run), args.claim_id, Path(args.src), Path(args.out),
            hint=args.hint,
            existing=json.loads(Path(args.existing).read_text())
            if args.existing else None)
    except SpecError as exc:
        raise SystemExit(f'input error: {exc}')
    except Exception as exc:  # model transport / validation failures
        print(json.dumps({'ok': False, 'partial': False, 'error': str(exc)},
                         ensure_ascii=False))
        return 2
    print(json.dumps(proposal, ensure_ascii=False, indent=2))
    if proposal.get('ok'):
        return 0
    if proposal.get('partial'):
        return 1
    return 2


if __name__ == '__main__':
    raise SystemExit(main())
