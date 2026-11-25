#!/usr/bin/env python3
"""Collect lightweight evidence from historical stage3 runs cited by docs."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT / 'tools' / 'stage3' / 'runs'
OUT = ROOT / 'docs' / 'legacy_stage3_runs'
SEARCH = (ROOT / 'docs', ROOT / 'tools' / 'stage3' / 'evaluation' / 'metrics')
REF_RE = re.compile(r'tools/stage3/runs/([^`"\s)]+)')
SUMMARY_NAME = 'stage3-summary.json'


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def collect(out: Path) -> dict:
    refs: dict[str, set[str]] = {}
    for base in SEARCH:
        if not base.is_dir():
            continue
        for path in base.rglob('*'):
            if not path.is_file() or path.suffix not in {'.md', '.json'}:
                continue
            text = path.read_text(errors='ignore')
            for match in REF_RE.finditer(text):
                run = match.group(1).split('/')[0].strip().rstrip(',;')
                if not run or '<' in run or '*' in run:
                    continue
                refs.setdefault(run, set()).add(
                    str(path.relative_to(ROOT)))

    out.mkdir(parents=True, exist_ok=True)
    runs_out = out / 'runs'
    runs_out.mkdir(parents=True, exist_ok=True)

    rows = []
    for run in sorted(refs):
        source = RUNS / run / SUMMARY_NAME
        if not source.is_file():
            continue
        target = runs_out / run / SUMMARY_NAME
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        summary = json.loads(target.read_text())
        rows.append({
            'run': run,
            'archived_path': str(target.relative_to(ROOT)),
            'source_sha256': sha256(source),
            'archived_sha256': sha256(target),
            'referenced_by': sorted(refs[run]),
            'schema_version': summary.get('schema_version'),
            'run_id': summary.get('run_id'),
            'case': summary.get('case'),
            'claim_id': summary.get('claim_id'),
            'consistency_verdict': summary.get('consistency_verdict'),
            'raw_consistency_verdict': summary.get('raw_consistency_verdict'),
        })

    return {
        'schema_version': 'legacy-stage3-run-evidence/1',
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'source_root': 'tools/stage3/runs',
        'scope': 'stage3-summary.json files for runs cited in docs and metrics',
        'warning': (
            'diagnostic evidence only; these runs are not part of the '
            'authoritative denominator and must not be used as current '
            'protocol results'),
        'counts': {
            'referenced_runs': len(refs),
            'archived_summaries': len(rows),
        },
        'rows': rows,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=OUT)
    args = parser.parse_args(argv)
    manifest = collect(args.out)
    (args.out / 'manifest.json').write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(manifest['counts'], ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
