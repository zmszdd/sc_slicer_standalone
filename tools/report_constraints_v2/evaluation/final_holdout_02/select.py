#!/usr/bin/env python3
"""Freeze the second terminal holdout set BEFORE the semantic-live-5 changes are measured.

This mirrors final_holdout_01 (which measured live-1..4): it is frozen BEFORE
any blind-batch measurement of the five semantic-live-5 structural changes, and
its cases are excluded from every future selection.  When a measurement is
authorised it is run once against the then-current semantic-live prompt; that
run is the only unbiased number for the post-closure structural additions.

This is not an iteration batch.  Its cases are frozen now, excluded from every
future live-batch selection (future select.py runs scan evaluation/**/SELECTION.json
and pick up this file's case IDs and report/input hashes), and are never inspected
semantically until the iteration loop stops.  When a terminal measurement is needed,
both manifests are run once against whatever `semantic-live` then is; that run is the
only unbiased number the loop ever produces.

Mirrors prompt_live2_blind_01/select.py (hash-rule freezing, full historical
exclusion) with a distinct salt.  Ten cases, split into two five-case manifests
because the batch runner caps a manifest at five cases.
"""

import argparse
import hashlib
import json
from pathlib import Path
import sys


HERE = Path(__file__).resolve().parent
STAGE2 = HERE.parents[1]
sys.path.insert(0, str(STAGE2))
for directory in (STAGE2 / 'lib', STAGE2 / 'cli'):
    sys.path.insert(0, str(directory))

from cli.semantic_pipeline import load_report  # noqa: E402


SALT = 'stage2-final-holdout2-2026-10-08-01:'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def previous_inputs():
    case_ids, report_hashes, input_hashes = set(), set(), set()
    for base in (STAGE2 / 'evaluation', STAGE2 / 'results'):
        for path in base.rglob('provenance.json'):
            try:
                row = json.loads(path.read_text())
            except (OSError, json.JSONDecodeError):
                continue
            for key, target in (('case_id', case_ids),
                                ('report_sha256', report_hashes),
                                ('report_input_sha256', input_hashes)):
                value = row.get(key)
                if isinstance(value, str):
                    target.add(value)
        for name in ('manifest.json', 'SELECTION.json'):
            for path in base.rglob(name):
                try:
                    data = json.loads(path.read_text())
                except (OSError, json.JSONDecodeError):
                    continue
                for row in data.get('cases', []):
                    value = row.get('case_id') or row.get('case_directory') or row.get('id')
                    if isinstance(value, str):
                        case_ids.add(value)
                    for key, target in (('report_sha256', report_hashes),
                                        ('input_sha256', input_hashes)):
                        value = row.get(key)
                        if isinstance(value, str):
                            target.add(value)
    return case_ids, report_hashes, input_hashes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root', type=Path, required=True)
    parser.add_argument('--count', type=int, default=10)
    args = parser.parse_args()
    if not 1 <= args.count <= 10:
        parser.error('count must be 1..10 (two five-case manifests)')

    root = args.source_root.resolve()
    excluded_ids, excluded_reports, excluded_inputs = previous_inputs()
    candidates = []
    for directory in root.iterdir():
        metadata_path = directory / 'metadata.json'
        report_path = directory / 'report.json'
        if (not directory.is_dir() or directory.name in excluded_ids or
                not metadata_path.is_file() or not report_path.is_file()):
            continue
        try:
            metadata = json.loads(metadata_path.read_text())
            if metadata.get('report_match_status') != 'exact_submission':
                continue
            text, raw, provenance = load_report(case_dir=directory, input_policy_version=4)
        except (KeyError, OSError, ValueError, json.JSONDecodeError):
            continue
        report_hash = sha(raw)
        input_hash = provenance['report_input_sha256']
        if report_hash in excluded_reports or input_hash in excluded_inputs:
            continue
        size = len(text.encode())
        project = metadata.get('project')
        if not 600 <= size <= 4500 or not isinstance(project, str) or not project:
            continue
        candidates.append({
            'case_id': directory.name,
            'project': project,
            'input_bytes': size,
            'report_sha256': report_hash,
            'input_sha256': input_hash,
            'selection_digest': sha((SALT + directory.name).encode()),
        })

    selected, projects = [], set()
    for row in sorted(candidates, key=lambda item: item['selection_digest']):
        if row['project'] in projects:
            continue
        selected.append(row)
        projects.add(row['project'])
        if len(selected) == args.count:
            break
    if len(selected) != args.count:
        raise SystemExit('not enough eligible unseen reports from distinct projects')

    selection = {
        'schema_version': 'stage2-final-holdout-selection/1',
        'frozen_at_utc': '2026-10-08',
        'status': 'frozen_before_semantic_live5_measurement',
        'purpose': ('Terminal blind measurement only.  These cases are excluded from all '
                    'future iteration-batch selections and receive no semantic inspection '
                    'of any kind until the iteration loop stops; they are then run once '
                    'against the final semantic-live prompt.  The anti-overfitting '
                    'instrument for the adaptive iterate-fix-measure loop.'),
        'source_root': str(root),
        'selection_rule': (
            'Unseen case ID, report hash, and report-input hash; exact-submission; '
            'report-json-input/4 length 600..4500; one report per project; ascending '
            f'sha256 of {SALT}case_id; no semantic inspection before freezing.'),
        'excluded_prior_case_count': len(excluded_ids),
        'excluded_prior_report_hash_count': len(excluded_reports),
        'excluded_prior_input_hash_count': len(excluded_inputs),
        'provider': 'deepseek',
        'model': 'deepseek-flash',
        'prompt_version': ('semantic-live (deferred: the terminal run records its own '
                           'prompt snapshot; this file pins cases, not the prompt)'),
        'input_policy': 'report-json-input/4',
        'lean_formal_input': True,
        'element_retries': 1,
        'formal_retries': 1,
        'continue_on_review': True,
        'claim_verdict': 'signals',
        'cases': selected,
    }
    (HERE / 'SELECTION.json').write_text(
        json.dumps(selection, ensure_ascii=False, indent=2) + '\n')

    # Two manifests: the batch runner caps a manifest at five cases.
    manifest_names = ['manifest_a.json', 'manifest_b.json']
    chunks = [selected[:5], selected[5:10]]
    for name, chunk in zip(manifest_names, chunks):
        if not chunk:
            continue
        manifest = {
            'data_root': str(root),
            'cases': [{'id': row['case_id'], 'case_directory': row['case_id']}
                      for row in chunk],
        }
        (HERE / name).write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'selected': len(selected),
                      'case_ids': [row['case_id'] for row in selected]},
                     ensure_ascii=False))


if __name__ == '__main__':
    main()
