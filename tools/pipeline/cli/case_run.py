#!/usr/bin/env python3
"""Run one brand-new flattened case end-to-end (stage-2 -> stage-3).

The input case directory should contain:

* ``report.json`` (or ``report.md``) — stage-2 report input
* ``contract.flattened.t.sol`` — self-contained flattened PoC (the PoC test
  harness lives inside it), or a ``src/`` directory
* ``metadata.json`` — optional; supplies ``test_name`` when present

The flatten is passed straight through to stage-3 (``skip_stage1=True``);
stage-1 slicing can still be requested separately via ``main.py pipeline-run``
with an explicit manifest. Stage-3 binding is auto-proposed unless
``--binding`` is given.

Run with cwd = repo root:
    python main.py case --case-dir /path/to/flatten_case --out-dir runs/demo
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools' / 'pipeline'))

from lib.manifest import build_manifest_from_case  # noqa: E402
from lib.runner import run_pipeline  # noqa: E402


def _first_file(directory: Path, *names: str) -> Path | None:
    for name in names:
        candidate = directory / name
        if candidate.is_file():
            return candidate
    return None


def _find_src(case_dir: Path) -> Path:
    flatten = case_dir / 'contract.flattened.t.sol'
    if flatten.is_file():
        return flatten
    src_dir = case_dir / 'src'
    if src_dir.is_dir():
        sols = sorted(src_dir.glob('*.sol')) + sorted(src_dir.glob('*.t.sol'))
        if sols:
            return sols[0]
    raise SystemExit(f'no contract.flattened.t.sol or src/*.sol in {case_dir}')


def _read_test_name(case_dir: Path) -> str | None:
    meta = case_dir / 'metadata.json'
    if not meta.is_file():
        return None
    try:
        data = json.loads(meta.read_text())
    except ValueError:
        return None
    return data.get('test_name')


_POC_TEST_RE = re.compile(r'\bfunction\s+(?:test\w*|invariant\w*)\s*\(')


def _has_poc_test(path: Path) -> bool:
    try:
        return bool(_POC_TEST_RE.search(path.read_text()))
    except OSError:
        return False


def _build_manifest(args, case_dir: Path, out_dir: Path, *,
                      report: Path | None, src: Path) -> dict:
    return build_manifest_from_case(
        case_id=case_dir.name,
        src=src,
        test=None,
        out_dir=out_dir,
        report=report,
        stage2_run_dir=Path(args.stage2_run_dir).resolve()
        if args.stage2_run_dir else None,
        stage2_output=out_dir / 'stage2',
        contract=args.contract,
        variable=args.variable,
        function=args.function or _read_test_name(case_dir),
        binding=Path(args.binding).resolve() if args.binding else None,
        binding_rounds=args.binding_rounds,
    )


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case-dir', required=True)
    parser.add_argument('--out-dir', required=True)
    parser.add_argument('--contract', default=None)
    parser.add_argument('--variable', default=None)
    parser.add_argument('--function', default=None)
    parser.add_argument('--binding', default=None)
    parser.add_argument('--binding-rounds', type=int, default=3)
    parser.add_argument('--stage2-run-dir', default=None,
                        help='reuse an existing stage-2 run instead of running report')
    args = parser.parse_args(argv)

    case_dir = Path(args.case_dir).resolve()
    if not case_dir.is_dir():
        raise SystemExit(f'case dir not found: {case_dir}')
    out_dir = Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    report = _first_file(case_dir, 'report.json', 'report.md')
    if report is None and not args.stage2_run_dir:
        raise SystemExit(f'no report.json/report.md in {case_dir}; '
                         'use --stage2-run-dir to reuse an existing run')

    src = _find_src(case_dir)
    if (src == (case_dir / 'contract.flattened.t.sol')
            and not _has_poc_test(src)):
        raise SystemExit(
            f'{src} has no PoC test function (function test*/invariant*); '
            'the flatten must be self-contained')
    manifest = _build_manifest(args, case_dir, out_dir, report=report, src=src)
    manifest_path = out_dir / 'manifest.pipeline.json'
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False,
                                        indent=2) + '\n')
    rc, _run_dir = run_pipeline(manifest_path, run_dir=out_dir / 'run',
                                skip_stage1=True)
    summary = out_dir / 'run' / 'pipeline-summary.json'
    if summary.is_file():
        print(json.dumps(json.loads(summary.read_text()), ensure_ascii=False,
                         indent=2))
    return rc


if __name__ == '__main__':
    raise SystemExit(main())
