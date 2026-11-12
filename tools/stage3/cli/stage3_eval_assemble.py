#!/usr/bin/env python3
"""Assemble a positive goldset sample into a stage-3 case directory.

Mechanical parts only: copies the verified flattened PoC into ``src/``,
copies the three stage-2 artifacts, and emits one binding skeleton per claim
(with semantic hints + source candidates). Semantic ``solidity_expr`` filling
remains explicit in each ``bindings/<claim_id>.json``.

Run with cwd = tools/stage3:
    python -m cli.stage3_eval_assemble --name forte_float128_pos \
        --flatten <...>/contract.flattened.t.sol \
        --stage2-run <stage2 run dir> --out cases/forte_float128_pos
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

from lib.spec_loader import SpecError, load_stage2_run
from lib.binding_skeleton import build_skeleton

ROOT = Path(__file__).resolve().parents[1]  # tools/stage3
ARTIFACTS = ('stage3-spec.json', 'constraints.json', 'formalization.json')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--name', required=True)
    parser.add_argument('--flatten', required=True,
                        help='verified flattened PoC .t.sol (self-contained)')
    parser.add_argument('--stage2-run', required=True,
                        help='stage-2 run directory with stage3-spec.json')
    parser.add_argument('--out', required=True)
    parser.add_argument('--src-name', default=None,
                        help='src file name; default: name of the flatten file')
    args = parser.parse_args(argv)

    flatten = Path(args.flatten).resolve()
    stage2_dir = Path(args.stage2_run).resolve()
    out = Path(args.out).resolve()

    if out.exists():
        raise SystemExit(f'output already exists: {out}\nchoose a fresh --out')
    if not flatten.is_file() or flatten.suffix != '.sol':
        raise SystemExit(f'flatten must be a .sol file: {flatten}')

    try:
        stage2 = load_stage2_run(stage2_dir)
    except SpecError as exc:
        raise SystemExit(f'input error: {exc}')

    src_name = args.src_name or flatten.name
    if not src_name.endswith('.sol'):
        src_name += '.sol'

    (out / 'src').mkdir(parents=True)
    (out / 'test').mkdir(parents=True)
    (out / 'stage2_run').mkdir(parents=True)
    (out / 'bindings').mkdir(parents=True)
    shutil.copy2(flatten, out / 'src' / src_name)
    for artifact in ARTIFACTS:
        shutil.copy2(stage2_dir / artifact, out / 'stage2_run' / artifact)

    claims = [row['claim_id'] for row in stage2['spec'].get('claims', [])]
    for claim_id in claims:
        skeleton = build_skeleton(stage2_dir, claim_id, src=out / 'src')
        (out / 'bindings' / f'{claim_id}.json').write_text(
            json.dumps(skeleton, ensure_ascii=False, indent=2) + '\n')

    manifest = {
        'schema_version': 'stage3-eval-case/1',
        'name': out.name,
        'flatten': str(flatten),
        'stage2_run': str(stage2_dir),
        'src_name': src_name,
        'claims': claims,
        'binding_workflow': (
            'fill bindings/<claim_id>.json solidity_expr/patch/probe, then run '
            'python -m cli.stage3_multi --case-dir <out> --bindings-dir <out>/bindings'),
    }
    (out / 'case.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')

    print(f'assembled eval case: {out}')
    print(f'claims: {len(claims)}')
    for claim_id in claims:
        print(f'  skeleton: {out}/bindings/{claim_id}.json')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
