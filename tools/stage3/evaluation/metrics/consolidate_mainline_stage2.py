#!/usr/bin/env python3
"""Consolidate frozen positive stage-2 artifacts for one protocol run."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STAGE3 = HERE.parents[1]
ROOT = HERE.parents[3]
if str(STAGE3) not in sys.path:
    sys.path.insert(0, str(STAGE3))
from lib import mainline_protocol, path_config

SAMPLE = HERE / 'mainline_sample.json'
C4_OUTPUT = path_config.c4_output_root()
SOURCE_ROOTS = (
    C4_OUTPUT / 'objective_mainline_stage2_shard_0_1_7_4',
    C4_OUTPUT / 'objective_mainline_stage2_shard_1_1_7_4',
    HERE / 'mainline_stage2_out',
    C4_OUTPUT / 'objective_mainline_stage2_1_7_0_live27_diag',
)
REQUIRED = ('stage3-spec.json', 'constraints.json', 'formalization.json')
DEFAULT_OUT = C4_OUTPUT / 'objective_mainline_stage2_unified_1_7_14'


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build(out: Path) -> dict:
    sample = json.loads(SAMPLE.read_text())
    cases = sample.get('positive_cases') or []
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    rows = []
    missing = []
    for case in cases:
        source = next((root / case for root in SOURCE_ROOTS
                       if all((root / case / name).is_file()
                              for name in REQUIRED)), None)
        if source is None:
            missing.append(case)
            continue
        destination = out / case
        shutil.copytree(source, destination)
        rows.append({
            'case': case,
            'source': str(source.relative_to(ROOT)),
            'artifact_sha256': {
                name: _sha256(destination / name) for name in REQUIRED
            },
        })
    manifest = {
        'schema_version': 'mainline-stage2-consolidation/1',
        'protocol': mainline_protocol.current(),
        'sample': str(SAMPLE.relative_to(ROOT)),
        'seed': sample.get('seed'),
        'source_roots': [str(root.relative_to(ROOT)) for root in SOURCE_ROOTS],
        'required_files': list(REQUIRED),
        'ready': len(rows),
        'missing': missing,
        'cases': rows,
    }
    (out / 'consolidated-stage2.json').write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    return manifest


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=DEFAULT_OUT)
    args = parser.parse_args(argv)
    manifest = build(args.out)
    print(json.dumps({
        'out': str(args.out),
        'protocol': manifest['protocol']['version'],
        'ready': manifest['ready'],
        'missing': len(manifest['missing']),
    }, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
