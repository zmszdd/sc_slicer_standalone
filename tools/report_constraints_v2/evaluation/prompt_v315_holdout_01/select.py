#!/usr/bin/env python3
"""Freeze a deterministic, previously unseen semantic-v3.15 holdout."""
import argparse
import hashlib
import json
from pathlib import Path
import sys


HERE = Path(__file__).resolve().parent
STAGE2 = HERE.parents[1]
EVALUATION = STAGE2 / 'evaluation'
sys.path.insert(0, str(STAGE2))

from semantic_pipeline import load_report  # noqa: E402
from prompts.versions import semantic_prompts_v315 as prompts  # noqa: E402


SALT = 'stage2-v315-independent-2026-09-20:'
CORE_FILES = (
    'semantic_pipeline.py', 'prompts/versions/semantic_prompts_v315.py',
    'plan_synthesizer.py',
    'report_only.py', 'report_readiness.py', 'numeric_fidelity.py',
    'address_fidelity.py',
)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def prior_case_ids():
    result = set()
    for path in EVALUATION.rglob('provenance.json'):
        try:
            case_id = json.loads(path.read_text()).get('case_id')
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(case_id, str):
            result.add(case_id)
    for name in ('manifest.json', 'SELECTION.json'):
        for path in EVALUATION.rglob(name):
            try:
                data = json.loads(path.read_text())
            except (OSError, json.JSONDecodeError):
                continue
            for row in data.get('cases', []):
                case_id = row.get('case_id') or row.get('case_directory') or row.get('id')
                if isinstance(case_id, str):
                    result.add(case_id)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--count', type=int, default=5)
    args = parser.parse_args()
    if not 1 <= args.count <= 10:
        parser.error('count must be 1..10')
    root = args.source_root.resolve()
    excluded = prior_case_ids()
    candidates = []
    for directory in root.iterdir():
        if not directory.is_dir() or directory.name in excluded:
            continue
        metadata_path = directory / 'metadata.json'
        report_path = directory / 'report.json'
        if not metadata_path.is_file() or not report_path.is_file():
            continue
        try:
            metadata = json.loads(metadata_path.read_text())
            if metadata.get('report_match_status') != 'exact_submission':
                continue
            text, raw, provenance = load_report(
                case_dir=directory, input_policy_version=4)
        except (KeyError, OSError, ValueError, json.JSONDecodeError):
            continue
        size = len(text.encode())
        if not 600 <= size <= 4500:
            continue
        project = metadata.get('project')
        if not isinstance(project, str) or not project:
            continue
        digest = sha((SALT + directory.name).encode())
        candidates.append({
            'case_id': directory.name,
            'project': project,
            'input_bytes': size,
            'report_sha256': sha(raw),
            'input_sha256': provenance['report_input_sha256'],
            'selection_digest': digest,
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
        raise SystemExit('not enough eligible unseen projects')
    manifest = {
        'schema_version': 'stage2-v315-holdout/1',
        'frozen_at_utc': '2026-09-20',
        'status': 'frozen_before_model_run',
        'purpose': ('Prospective v3.15 completion, classification, formula-fidelity '
                    'and false-rejection evaluation'),
        'source_root': str(root),
        'selection_rule': ('Previously unseen exact-submission reports; '
                           'report-json-input/4 length 600..4500; one per project; '
                           'ascending sha256 of ' + SALT + 'case_id'),
        'excluded_prior_case_count': len(excluded),
        'provider': 'deepseek',
        'model': 'deepseek-flash',
        'prompt_version': prompts.PROMPT_VERSION,
        'input_policy': 'report-json-input/4',
        'lean_formal_input': True,
        'element_retries': 1,
        'formal_retries': 2,
        'continue_on_review': True,
        'element_prompt_sha256': sha(prompts.ID_ELEMENT_PROMPT.encode()),
        'formal_prompt_sha256': sha(prompts.formal_prompt('ids', 'core').encode()),
        'code_sha256': {name: sha((STAGE2 / name).read_bytes()) for name in CORE_FILES},
        'cases': selected,
    }
    args.output.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'selected': len(selected),
                      'case_ids': [row['case_id'] for row in selected]},
                     ensure_ascii=False))


if __name__ == '__main__':
    main()
