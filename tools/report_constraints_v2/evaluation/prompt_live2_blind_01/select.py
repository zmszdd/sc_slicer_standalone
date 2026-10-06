#!/usr/bin/env python3
"""Freeze a deterministic semantic-live-2 blind set before model calls.

Mirrors prompt_live1_blind_01/select.py (hash-rule freezing, full historical
exclusion) with a new salt so the sample cannot overlap any prior batch,
including prompt_live1_blind_01.  Single manifest of five cases.
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
from prompts.active import resolve_prompt_set  # noqa: E402


SALT = 'stage2-live2-blind-2026-10-06-02:'
PROMPT_VERSION = 'semantic-live'


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


def code_hashes():
    paths = (
        'cli/semantic_pipeline.py',
        'cli/batch_verify.py',
        'lib/ingest.py',
        'lib/plan_synthesizer.py',
        'lib/report_only.py',
        'lib/salvage.py',
        'lib/semantic_core.py',
        'lib/solving.py',
        'prompts/definitions.py',
        'prompts/active.py',
        'prompts/registry.py',
        'prompts/current.py',
    )
    return {name: sha((STAGE2 / name).read_bytes()) for name in paths}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root', type=Path, required=True)
    parser.add_argument('--count', type=int, default=5)
    args = parser.parse_args()
    if not 1 <= args.count <= 5:
        parser.error('count must be 1..5 (batch runner manifest limit)')

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

    prompts = resolve_prompt_set(PROMPT_VERSION, 'ids', 'core')
    selection = {
        'schema_version': 'stage2-live2-blind-selection/1',
        'frozen_at_utc': '2026-10-06',
        'status': 'frozen_before_model_run',
        'purpose': ('Prospective blind measurement of the semantic-live-2 prompt '
                    '(rate restatement rule, I applicability-scope rule) and the '
                    'assumption_numeric_relief gate on unseen reports'),
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
        'prompt_version': PROMPT_VERSION,
        'input_policy': 'report-json-input/4',
        'lean_formal_input': True,
        'element_retries': 1,
        'formal_retries': 1,
        'continue_on_review': True,
        'claim_verdict': 'signals',
        'element_prompt_sha256': prompts.sha256('element'),
        'formal_prompt_sha256': prompts.sha256('formal'),
        'code_sha256': code_hashes(),
        'cases': selected,
    }
    (HERE / 'SELECTION.json').write_text(
        json.dumps(selection, ensure_ascii=False, indent=2) + '\n')

    manifest = {
        'data_root': str(root),
        'cases': [{'id': row['case_id'], 'case_directory': row['case_id']}
                  for row in selected],
    }
    (HERE / 'manifest.json').write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'selected': len(selected),
                      'case_ids': [row['case_id'] for row in selected]},
                     ensure_ascii=False))


if __name__ == '__main__':
    main()
