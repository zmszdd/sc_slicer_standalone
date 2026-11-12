#!/usr/bin/env python3
"""Run every pipeline manifest under a directory and aggregate the results.

Each manifest already runs stage1 || stage2 -> stage3 internally; this wrapper
adds case-level fan-in via a thread pool and writes one batch summary.

Skeleton manifests (``kind == "skeleton"`` or under a ``skeleton/`` directory)
are skipped: they carry TODO paths and are placeholders, not runnable cases.
"""
from __future__ import annotations

import argparse
import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools' / 'pipeline'))

from lib.manifest import load_manifest  # noqa: E402
from lib.runner import run_pipeline  # noqa: E402


def _find_manifests(root: Path, pattern: str | None) -> list[Path]:
    manifests = []
    for path in sorted(root.rglob('*.pipeline.json')):
        if any(part in path.parts for part in ('skeleton', 'needs_input')):
            continue
        if pattern and pattern not in path.name:
            continue
        manifests.append(path)
    return manifests


def _read_summary(run_dir: Path) -> dict:
    summary_path = run_dir / 'pipeline-summary.json'
    if not summary_path.is_file():
        return {}
    return json.loads(summary_path.read_text())


def _resume_row(manifest_path: Path, case_id: str) -> dict | None:
    run_dir = manifest_path.parent / 'runs' / case_id
    summary = _read_summary(run_dir)
    if summary.get('status') != 'ok':
        return None
    return {
        'case_id': case_id,
        'status': 'skipped',
        'overlap': summary.get('overlap'),
        'verdict': (summary.get('stage3') or {}).get('consistency_verdict'),
        'stage3_run_id': (summary.get('stage3') or {}).get('run_id'),
        'detail': '',
    }


def run_one(manifest_path: Path, skip_stage1: bool, skip_stage2: bool,
            resume: bool = False) -> dict:
    manifest = load_manifest(manifest_path)
    case_id = manifest['case_id']
    if resume:
        skipped = _resume_row(manifest_path, case_id)
        if skipped is not None:
            return skipped
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')
    run_id = f'{case_id}_{stamp}'
    rc, run_dir = run_pipeline(manifest_path, run_id=run_id,
                               skip_stage1=skip_stage1, skip_stage2=skip_stage2)
    timeline_path = run_dir / 'timeline.json'
    timeline = json.loads(timeline_path.read_text()) if timeline_path.is_file() else {}
    summary = _read_summary(run_dir)
    return {
        'case_id': case_id,
        'status': 'ok' if rc == 0 else 'failed',
        'overlap': timeline.get('overlap'),
        'verdict': (summary.get('stage3') or {}).get('consistency_verdict'),
        'stage3_run_id': ((timeline.get('stages', {}).get('stage3', {}) or {})
                          .get('run_id')),
        'detail': '; '.join(timeline.get('failures', []))[:400],
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifests-root', required=True)
    parser.add_argument('--output', required=True, help='batch summary json path')
    parser.add_argument('--max-cases', type=int, default=0)
    parser.add_argument('--filter', dest='pattern')
    parser.add_argument('--concurrency', type=int, default=1,
                        choices=(1, 2, 3, 4))
    parser.add_argument('--skip-stage1', action='store_true')
    parser.add_argument('--skip-stage2', action='store_true')
    parser.add_argument('--resume', action='store_true',
                        help='skip cases whose pipeline-summary.json is already ok')
    args = parser.parse_args(argv)

    root = Path(args.manifests_root).resolve()
    if not root.is_dir():
        raise SystemExit(f'--manifests-root is not a directory: {root}')
    manifests = _find_manifests(root, args.pattern)
    if args.max_cases > 0:
        manifests = manifests[:args.max_cases]
    if not manifests:
        raise SystemExit('no runnable *.pipeline.json manifests found')

    rows = []
    if args.concurrency == 1:
        for path in manifests:
            rows.append(run_one(path, args.skip_stage1, args.skip_stage2,
                                resume=args.resume))
    else:
        with ThreadPoolExecutor(max_workers=args.concurrency) as pool:
            futures = {pool.submit(run_one, path, args.skip_stage1,
                                   args.skip_stage2, resume=args.resume):
                       path for path in manifests}
            for future in as_completed(futures):
                rows.append(future.result())
    rows.sort(key=lambda row: row['case_id'])

    verdicts: dict[str, int] = {}
    for row in rows:
        verdict = row.get('verdict')
        if verdict:
            verdicts[verdict] = verdicts.get(verdict, 0) + 1

    payload = {
        'schema_version': 'pipeline-batch-summary/1',
        'manifests_root': str(root),
        'total': len(rows),
        'ok': sum(1 for row in rows if row['status'] == 'ok'),
        'failed': sum(1 for row in rows if row['status'] == 'failed'),
        'skipped': sum(1 for row in rows if row['status'] == 'skipped'),
        'verdict_distribution': verdicts,
        'cases': rows,
    }
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload['failed'] == 0 else 1


if __name__ == '__main__':
    raise SystemExit(main())
