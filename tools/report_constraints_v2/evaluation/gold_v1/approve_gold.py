#!/usr/bin/env python3
"""Seal a fully checked human review card into an immutable approval record."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re


HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reviewer', required=True)
    parser.add_argument('--output', type=Path, default=HERE / 'approved-gold.json')
    args = parser.parse_args()
    if not args.reviewer.strip() or args.reviewer.strip().lower().startswith('assistant'):
        parser.error('a named human reviewer is required')
    review = (HERE / 'REVIEW.md').read_text()
    checked = len(re.findall(r'^- \[[xX]\] ', review, re.M))
    unchecked = len(re.findall(r'^- \[ \] ', review, re.M))
    if checked != 25 or unchecked:
        raise ValueError(f'gold review incomplete: checked={checked}, unchecked={unchecked}')
    manifest = json.loads((HERE / 'manifest.json').read_text())
    gold = json.loads((HERE / 'gold.json').read_text())
    ids = [case['id'] for case in manifest['cases']]
    if ids != [case['id'] for case in gold['cases']] or len(ids) != 5:
        raise ValueError('manifest/gold case mismatch')
    approval = {
        'schema_version': 'stage2-gold-approval/1',
        'status': 'human_review_approved',
        'reviewer': args.reviewer.strip(),
        'approved_at_utc': datetime.now(timezone.utc).isoformat(),
        'case_ids': ids,
        'manifest_sha256': sha(HERE / 'manifest.json'),
        'gold_sha256': sha(HERE / 'gold.json'),
        'review_sha256': sha(HERE / 'REVIEW.md'),
    }
    with args.output.open('x') as stream:
        json.dump(approval, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps(approval, ensure_ascii=False))


if __name__ == '__main__':
    main()
