#!/usr/bin/env python3
"""Assemble a stage-3 case from stage-1/2 artifacts.

Run with cwd = tools/stage3:
    python -m cli.stage3_assemble --name foo --src slice.sol \
        --stage2-run <stage2-dir> --binding binding.json --test poc.t.sol
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from lib.case_builder import assemble_case
from lib.spec_loader import SpecError

ROOT = Path(__file__).resolve().parents[1]  # tools/stage3


def _resolve(path: str | None) -> Path | None:
    if path is None:
        return None
    value = Path(path)
    return value if value.is_absolute() else (Path.cwd() / value).resolve()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--name', required=True)
    parser.add_argument('--src', required=True,
                        help='stage-1 slice .sol file, or a directory of Solidity sources')
    parser.add_argument('--stage2-run', required=True,
                        help='stage-2 run directory with stage3-spec.json')
    parser.add_argument('--binding', default=None,
                        help='stage3 binding.json; omit to auto-bind later')
    parser.add_argument('--test', default=None, help='PoC test file or directory')
    parser.add_argument('--out', default=None,
                        help=f'default: {ROOT / "cases" / "<name>"}')
    parser.add_argument('--foundry-toml')
    parser.add_argument('--lib', help='dependency tree copied verbatim')
    parser.add_argument('--remappings', help='remappings.txt')
    parser.add_argument('--expected', help='expected/expected.json')
    parser.add_argument('--default-foundry-toml', action='store_true',
                        help='write the default foundry.toml (via_ir=true) '
                             'instead of requiring an explicit --foundry-toml')
    parser.add_argument('--overwrite', action='store_true')
    args = parser.parse_args(argv)

    out = (_resolve(args.out) if args.out is not None
           else (ROOT / 'cases' / args.name))
    try:
        case_dir = assemble_case(
            name=args.name,
            src=Path(args.src),
            stage2_run=Path(args.stage2_run),
            binding=Path(args.binding) if args.binding else None,
            test=Path(args.test) if args.test else None,
            out=out,
            foundry_toml=_resolve(args.foundry_toml),
            default_foundry_toml=bool(args.default_foundry_toml),
            lib=_resolve(args.lib),
            remappings=_resolve(args.remappings),
            expected=_resolve(args.expected),
            overwrite=args.overwrite,
        )
    except SpecError as exc:
        raise SystemExit(f'input error: {exc}')
    print(f'assembled case: {case_dir}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
