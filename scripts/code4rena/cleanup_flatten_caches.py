#!/usr/bin/env python3
r"""Remove transient npm ``node_modules`` from the per-project GitHub caches.

``code4rena_flatten_pipeline.py`` installs npm dependencies on demand to resolve
``@openzeppelin/...`` / ``solady/...`` imports, but the produced
``flatten_sorted/*.sorted.sol`` already embeds every dependency. The
``node_modules`` trees under ``_github_repos_by_project`` are therefore safe to
delete once flatten has completed; re-flattening a project simply re-installs
them.

Usage:
    python scripts/code4rena/cleanup_flatten_caches.py \
        [--cache-dir c4_pipeline_output/_github_repos_by_project] \
        [--dry-run]
"""
from __future__ import annotations

import argparse
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CACHE = ROOT / 'c4_pipeline_output' / '_github_repos_by_project'


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache-dir', type=Path, default=DEFAULT_CACHE)
    parser.add_argument('--dry-run', action='store_true')
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.cache_dir.is_dir():
        print(f'cache dir not found: {args.cache_dir}')
        return 1
    freed = 0
    removed = 0
    for nm in sorted(args.cache_dir.rglob('node_modules')):
        if not nm.is_dir() or nm.is_symlink():
            continue
        size = sum(f.stat().st_size for f in nm.rglob('*') if f.is_file())
        if not args.dry_run:
            shutil.rmtree(nm, ignore_errors=True)
        freed += size
        removed += 1
    print(f'{"[dry-run] " if args.dry_run else ""}removed {removed} node_modules dirs, '
          f'freed {freed / 1e9:.2f} GB')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
