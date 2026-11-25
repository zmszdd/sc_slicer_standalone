#!/usr/bin/env python3
"""Restore frozen negative case source files from their recorded URLs.

This is a partial recovery helper for the accidentally deleted external data
root.  It writes only the exact source files referenced by the frozen case
manifest and records provenance.  It does not recreate full repository
checkouts, findings.json snapshots, flatten corpora, or any evaluation state.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CASES_DEFAULT = (
    ROOT / 'tools' / 'stage3' / 'evaluation' / 'metrics'
    / 'official_negative_stage1_cases_20261121.json'
)
MANIFEST_NAME = '_frozen_case_source_restore_manifest.json'
DATA_MARKER = '/c4_pipeline_output/'


def raw_url(url: str, ref_override: str | None = None) -> str | None:
    parsed = urllib.parse.urlparse(url)
    if parsed.netloc != 'github.com':
        return None
    parts = parsed.path.strip('/').split('/')
    if len(parts) < 5 or parts[2] != 'blob':
        return None
    owner, repo, _, url_ref = parts[:4]
    ref = ref_override or url_ref
    source_path = '/'.join(parts[4:])
    return (
        'https://raw.githubusercontent.com/'
        f'{owner}/{repo}/{urllib.parse.quote(ref, safe="/")}/'
        f'{urllib.parse.quote(source_path, safe="/")}'
    )


def target_path(source_path: str, root: Path) -> Path | None:
    index = source_path.find(DATA_MARKER)
    if index < 0:
        return None
    return root / source_path[index + 1:].lstrip('/')


def pinned_ref(target: Path) -> str | None:
    for part in target.parts:
        match = re.search(r'(?:^|__)([0-9a-f]{40})$', part)
        if match:
            return match.group(1)
    return None


def fetch(url: str, target: Path) -> tuple[str | None, str | None]:
    request = urllib.request.Request(
        url, headers={'User-Agent': 'sc-slicer-frozen-source-restore/1'})
    last_error = None
    for attempt in range(5):
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                data = response.read()
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            return hashlib.sha256(data).hexdigest(), None
        except Exception as exc:
            last_error = exc
            if attempt < 4:
                time.sleep(2 ** attempt)
    return None, f'{type(last_error).__name__}: {last_error}'


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cases', type=Path, default=CASES_DEFAULT)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--force', action='store_true')
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args(argv)

    cases = json.loads(args.cases.read_text())['cases']
    rows = []
    for case in cases:
        source_url = str(case.get('source_url') or '')
        source_path = str(case.get('source_path') or '')
        target = target_path(source_path, args.root)
        ref = pinned_ref(target) if target else None
        download_url = raw_url(source_url, ref)
        row = {
            'case': case.get('case'),
            'source_url': source_url,
            'ref': ref,
            'pinned': bool(ref),
            'target': str(target.relative_to(args.root)) if target else None,
            'status': '',
            'sha256': None,
            'error': None,
        }
        if target is None or download_url is None:
            row['status'] = 'unsupported_url_or_path'
            rows.append(row)
            continue
        if args.dry_run:
            row['status'] = 'dry_run'
            rows.append(row)
            continue
        if target.is_file() and not args.force:
            row['status'] = 'already_present'
            row['sha256'] = hashlib.sha256(target.read_bytes()).hexdigest()
            rows.append(row)
            continue
        digest, error = fetch(download_url, target)
        row['sha256'] = digest
        row['status'] = 'restored' if digest else 'fetch_failed'
        row['error'] = error
        rows.append(row)

    counts: dict[str, int] = {}
    for row in rows:
        counts[row['status']] = counts.get(row['status'], 0) + 1
    manifest = {
        'schema_version': 'frozen-case-source-restore/1',
        'restored_at': datetime.now(timezone.utc).isoformat(),
        'cases_file': str(args.cases),
        'scope': 'source files only; not a full external data root restore',
        'counts': counts,
        'rows': rows,
    }
    if not args.dry_run:
        manifest_path = args.root / 'c4_pipeline_output' / MANIFEST_NAME
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
        print(f'manifest: {manifest_path}')
    print(json.dumps(counts, ensure_ascii=False, sort_keys=True))
    return 0 if counts.get('fetch_failed', 0) == 0 else 1


if __name__ == '__main__':
    raise SystemExit(main())
