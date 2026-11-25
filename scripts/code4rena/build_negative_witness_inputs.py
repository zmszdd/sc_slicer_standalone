#!/usr/bin/env python3
"""Assemble stage-3 flatten inputs from verified negative-witness artifacts.

Only artifacts recorded as ``flatten_pass`` with ``route=negative_witness``
are copied. Frozen case ids, labels and the goldset selection are unchanged;
unresolved cases remain absent from the flatten root and therefore stay in the
full-sample denominator as unresolved.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STAGE3 = ROOT / 'tools' / 'stage3'
if str(STAGE3) not in sys.path:
    sys.path.insert(0, str(STAGE3))
from lib import path_config

C4_OUTPUT = path_config.c4_output_root()
WITNESS_DEFAULT = C4_OUTPUT / 'official_negative_witness_20261121'
GOLDSET_DEFAULT = C4_OUTPUT / 'objective_negative_goldset_1_7_3'
FLATTEN_DEFAULT = C4_OUTPUT / 'objective_negative_flatten_1_7_7'


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding='utf-8'))


def build(witness_roots: list[Path], goldset: Path, flatten_root: Path,
          merged_status: Path | None = None,
          neutral_root: Path | None = None) -> dict:
    selected = [str(row['case'])
                for row in _load(goldset / 'selection.json').get('cases', [])]
    by_case: dict[str, list[tuple[Path, dict]]] = {case: [] for case in selected}
    for root in witness_roots:
        status_path = root / 'status.json'
        if not status_path.is_file():
            continue
        for row in _load(status_path).get('rows', []):
            case = str(row.get('case') or '')
            if case in by_case:
                by_case[case].append((root, row))
    copied = []
    unresolved = []
    neutral_ready = []
    merged_rows = []
    for case in selected:
        candidates = by_case.get(case) or []
        chosen = None
        for root, row in candidates:
            artifact = Path(str(row.get('artifact') or ''))
            manifest = artifact.parent / 'harness-manifest.json'
            if (row.get('status') == 'flatten_pass'
                    and row.get('route') == 'negative_witness'
                    and artifact.is_file() and manifest.is_file()):
                chosen = (root, row, artifact, manifest)
                break
        if chosen is None:
            unresolved.append(case)
            neutral_artifact = None
            if neutral_root is not None:
                candidate = neutral_root / case / 'contract.flattened.t.sol'
                if candidate.is_file():
                    neutral_artifact = candidate
            if neutral_artifact is not None:
                neutral_ready.append(case)
                merged_rows.append({
                    'case': case,
                    'status': 'flatten_pass',
                    'route': 'neutral_entrypoint',
                    'artifact': str(neutral_artifact),
                    'artifact_sha256': hashlib.sha256(
                        neutral_artifact.read_bytes()).hexdigest(),
                    'witness_root': str(neutral_root),
                })
                continue
            previous = candidates[0][1] if candidates else {}
            merged_rows.append({
                'case': case,
                'status': 'blocked',
                'error': previous.get('error') or 'no_stage1_artifact',
                'route': 'negative_witness',
                'artifact': None,
            })
            continue
        root, row, artifact, manifest = chosen
        destination = flatten_root / case
        destination.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(artifact,
                        destination / 'contract.flattened.t.sol')
        shutil.copyfile(manifest, destination / 'harness-manifest.json')
        copied.append(case)
        merged_rows.append({**row, 'case': case,
                            'witness_root': str(root)})
    summary = {
        'schema_version': 'negative-witness-stage3-inputs/2',
        'witness_roots': [str(root) for root in witness_roots],
        'neutral_root': str(neutral_root) if neutral_root else None,
        'goldset': str(goldset),
        'flatten_root': str(flatten_root),
        'stage2_selected': len(selected),
        'witness_ready': len(copied),
        'neutral_slice_ready': len(neutral_ready),
        'unresolved': unresolved,
    }
    status_out = merged_status or (flatten_root / 'merged-status.json')
    status_out.parent.mkdir(parents=True, exist_ok=True)
    status_out.write_text(json.dumps({
        'schema_version': 'negative-witness-status-merged/1',
        'rows': merged_rows,
    }, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    summary['merged_status'] = str(status_out)
    (flatten_root / 'input-summary.json').write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + '\n',
        encoding='utf-8')
    return summary


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--witness-root', type=Path, action='append',
                        default=None)
    parser.add_argument('--goldset-root', type=Path, default=GOLDSET_DEFAULT)
    parser.add_argument('--flatten-root', type=Path, default=FLATTEN_DEFAULT)
    parser.add_argument('--merged-status', type=Path, default=None)
    parser.add_argument('--neutral-root', type=Path, default=None)
    args = parser.parse_args(argv)
    roots = args.witness_root or [WITNESS_DEFAULT]
    summary = build(roots, args.goldset_root, args.flatten_root,
                    args.merged_status, args.neutral_root)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
