#!/usr/bin/env python3
"""Build the frozen dev-current mini evaluation manifest.

This is a development metric set, not the held-out mainline.  It contains 80
judge-valid cases from dev252 and 40 judge-invalid cases from the blind-invalid
pools.  dev24 is excluded because it was heavily used for failure-guided
regression work.  All case directories must already contain stage2_run/ and
bindings/ so the replay can run without new LLM calls.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
STAGE3 = HERE.parents[1]
ROOT = STAGE3.parents[1]
import sys  # noqa: E402
if str(STAGE3) not in sys.path:
    sys.path.insert(0, str(STAGE3))
DEFAULT_DEV252 = STAGE3 / 'evaluation' / 'frozen' / 'dev252_20261117.json'
DEFAULT_DEV24 = STAGE3 / 'evaluation' / 'frozen' / 'dev24_20261117.json'
DEFAULT_NEGATIVE_FILES = (
    HERE / 'positive_eval_blind_invalid.json',
    HERE / 'positive_eval_blind_invalid_remaining.json',
    HERE / 'positive_eval_blind_invalid_sukukfi_p1.json',
)
DEFAULT_OUT = STAGE3 / 'evaluation' / 'frozen' / 'dev_current_mini_20261120.json'
POSITIVES = 80
NEGATIVES = 40
SEED = 20261120


def _load(path: Path) -> dict:
    return json.loads(Path(path).read_text())


def _sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _project(case_id: str) -> str:
    return case_id.split('__', 1)[0]


def _allocate(populations: dict[str, int], total: int) -> dict[str, int]:
    """Deterministic proportional allocation with one member per project."""
    if total <= 0 or not populations:
        return {}
    names = sorted(populations)
    alloc = {name: min(1, populations[name]) for name in names}
    remaining = total - sum(alloc.values())
    if remaining <= 0:
        return {name: min(alloc[name], populations[name]) for name in names}
    room = {name: populations[name] - alloc[name] for name in names}
    total_population = sum(populations.values())
    quotas = {name: remaining * populations[name] / total_population
              for name in names}
    extra = {name: min(room[name], int(quotas[name])) for name in names}
    leftover = remaining - sum(extra.values())
    order = sorted(names, key=lambda name: (
        -(quotas[name] - int(quotas[name])), name))
    for name in order:
        if leftover <= 0:
            break
        if extra[name] < room[name]:
            extra[name] += 1
            leftover -= 1
    for name in names:
        alloc[name] += extra[name]
    return {name: min(alloc[name], populations[name]) for name in names}


def _stratified_sample(rows: list[dict], total: int, seed: int) -> list[dict]:
    by_project: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        by_project[_project(row['case_id'])].append(row)
    alloc = _allocate({name: len(items) for name, items in by_project.items()},
                      total)
    rng = random.Random(seed)
    selected = []
    for name in sorted(by_project):
        count = min(alloc.get(name, 0), len(by_project[name]))
        if count:
            selected.extend(rng.sample(by_project[name], count))
    rng.shuffle(selected)
    return selected


def _usable(case_id: str, root: Path) -> bool:
    case_dir = root / 'tools' / 'stage3' / 'cases' / case_id
    return (case_dir / 'stage2_run').is_dir() and (case_dir / 'bindings').is_dir()


def build(*, dev252_path: Path, dev24_path: Path,
          negative_paths: tuple[Path, ...], root: Path,
          positives: int = POSITIVES, negatives: int = NEGATIVES,
          seed: int = SEED) -> dict:
    dev24_ids = {row['case_id'] for row in _load(dev24_path).get('cases', [])}
    dev252 = _load(dev252_path).get('case_list', {}).get('cases', [])

    positive_rows = []
    for row in dev252:
        case_id = row['case_id']
        if case_id in dev24_ids or not _usable(case_id, root):
            continue
        positive_rows.append({
            'case_id': case_id,
            'label': 'positive',
            'bucket': 'dev252_positive',
            'historical_outcome': row.get('label'),
            'historical_bucket': row.get('bucket'),
            'project': _project(case_id),
            'source': 'frozen/dev252_20261117.json',
            'case_dir': f'tools/stage3/cases/{case_id}',
        })

    negative_seen = set()
    negative_rows = []
    for path in negative_paths:
        for row in _load(path).get('cases', []):
            case_id = row.get('case')
            if (not case_id or case_id in dev24_ids
                    or case_id in negative_seen or row.get('status') != 'done'
                    or not _usable(case_id, root)):
                continue
            negative_seen.add(case_id)
            negative_rows.append({
                'case_id': case_id,
                'label': 'negative',
                'bucket': 'blind_invalid',
                'project': _project(case_id),
                'source': str(path.relative_to(root)),
                'case_dir': f'tools/stage3/cases/{case_id}',
            })

    selected = (_stratified_sample(positive_rows, positives, seed)
                + _stratified_sample(negative_rows, negatives, seed + 1))
    from lib import mainline_protocol

    protocol = mainline_protocol.current()
    sources = [dev252_path, dev24_path, *negative_paths]
    return {
        'schema_version': 'dev-current-mini-manifest/1',
        'name': 'dev_current_mini_20261120',
        'policy': ('development-only current-protocol four metrics; dev24 '
                   'excluded; unresolved claims are excluded from the matrix'),
        'seed': seed,
        'protocol': protocol,
        'targets': {'positive': positives, 'negative': negatives},
        'source_hashes': {
            str(path.relative_to(root)): _sha256(path) for path in sources},
        'pools': {'positive': len(positive_rows),
                  'negative': len(negative_rows)},
        'case_count': len(selected),
        'cases': selected,
    }


def main(argv=None) -> dict:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dev252', type=Path, default=DEFAULT_DEV252)
    parser.add_argument('--dev24', type=Path, default=DEFAULT_DEV24)
    parser.add_argument('--negative', type=Path, action='append',
                        default=list(DEFAULT_NEGATIVE_FILES))
    parser.add_argument('--positives', type=int, default=POSITIVES)
    parser.add_argument('--negatives', type=int, default=NEGATIVES)
    parser.add_argument('--seed', type=int, default=SEED)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--out', type=Path, default=DEFAULT_OUT)
    args = parser.parse_args(argv)
    manifest = build(dev252_path=args.dev252, dev24_path=args.dev24,
                     negative_paths=tuple(args.negative), root=args.root,
                     positives=args.positives, negatives=args.negatives,
                     seed=args.seed)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({
        'manifest': str(args.out),
        'cases': manifest['case_count'],
        'pools': manifest['pools'],
        'protocol': manifest['protocol']['version'],
    }, ensure_ascii=False, indent=2))
    return manifest


if __name__ == '__main__':
    main()
