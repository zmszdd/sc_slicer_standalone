#!/usr/bin/env python3
"""Freeze a fresh blind set for the staged Impact inventory pipeline.

Mirrors prompt_live7_blind_01/select.py (hash-rule freezing, full historical
exclusion) with a new salt so the sample cannot overlap any prior batch,
including prior blind and terminal sets (their SELECTION.json files are picked
up by the historical scan). Ten cases across two five-case manifests: the
batch runner caps a manifest at five cases. The measurement evaluates whether
impact claims stay grounded in explicitly labeled Impact sections.
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
from prompts.current import IMPACT_INVENTORY_PROMPT  # noqa: E402


SALT = 'stage2-live22-impact-qualifier-blind-2026-10-21-01:'
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
                    if isinstance(row, str):
                        case_ids.add(row)
                        continue
                    if not isinstance(row, dict):
                        continue
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
        'lib/impact_inventory.py',
        'lib/plan_synthesizer.py',
        'lib/multi_impact.py',
        'lib/report_only.py',
        'lib/salvage.py',
        'lib/semantic_core.py',
        'lib/piv_contract.py',
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
    if not 1 <= args.count <= 50:
        parser.error('count must be 1..50')

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

    # Round-robin over projects by deterministic selection digest to keep the
    # sample diverse while allowing repeated projects when the corpus has fewer
    # eligible projects than requested cases.
    by_project = {}
    for row in sorted(candidates, key=lambda item: item['selection_digest']):
        by_project.setdefault(row['project'], []).append(row)
    selected = []
    projects = sorted(by_project)
    round_index = 0
    while len(selected) < args.count:
        added = False
        for project in projects:
            rows = by_project[project]
            if round_index < len(rows):
                selected.append(rows[round_index])
                added = True
                if len(selected) == args.count:
                    break
        if not added:
            break
        round_index += 1

    if len(selected) != args.count:
        raise SystemExit('not enough eligible distinct unseen reports')

    prompts = resolve_prompt_set(PROMPT_VERSION, 'ids', 'core')
    selection = {
        'schema_version': 'stage2-live22-impact-qualifier-selection/1',
        'frozen_at_utc': '2026-10-21',
        'status': 'frozen_before_model_run',
        'purpose': ('Blind evaluation of semantic-live impact modality and granularity: '
                    'extract impact facts using only an input catalog restricted to explicitly labeled '
                    'Impact sections, merge the validated inventory with core elements, then formalize '
                    'each impact separately.'),
        'source_root': str(root),
        'selection_rule': (
            'Unseen case ID, report hash, and report-input hash; exact-submission; '
            'report-json-input/4 length 600..4500; round-robin by project and distinct report; ascending '
            f'sha256 of {SALT}case_id; no semantic inspection before freezing. '
            'Impact-section presence/content is not an eligibility condition.'),
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
        'impact_inventory_prompt_sha256': sha(
            IMPACT_INVENTORY_PROMPT.encode()),
        'code_sha256': code_hashes(),
        'cases': selected,
    }
    (HERE / 'SELECTION.json').write_text(
        json.dumps(selection, ensure_ascii=False, indent=2) + '\n')

    # Manifests are chunked because the bounded runner accepts at most five cases each.
    for index in range(0, len(selected), 5):
        chunk = selected[index:index + 5]
        manifest = {
            'data_root': str(root),
            'cases': [{'id': row['case_id'], 'case_directory': row['case_id']}
                      for row in chunk],
        }
        (HERE / f'manifest_{index // 5 + 1:02d}.json').write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'selected': len(selected),
                      'case_ids': [row['case_id'] for row in selected]},
                     ensure_ascii=False))


if __name__ == '__main__':
    main()
