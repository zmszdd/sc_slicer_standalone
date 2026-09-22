#!/usr/bin/env python3
"""Compute accuracy only from human-approved gold and artifact-bound ratings."""
import argparse
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
DIMENSIONS = ('P_completeness', 'P_purity', 'I_correctness', 'V_directness',
              'unresolved_correctness')
VALUES = ('pass', 'partial', 'fail', 'not_evaluable')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def evaluate(approval_path, ratings_path):
    approval = json.loads(approval_path.read_text())
    manifest = json.loads((HERE / 'manifest.json').read_text())
    gold = json.loads((HERE / 'gold.json').read_text())
    require(approval.get('status') == 'human_review_approved', 'gold is not human approved')
    require(approval.get('manifest_sha256') == sha(HERE / 'manifest.json'), 'manifest changed after approval')
    require(approval.get('gold_sha256') == sha(HERE / 'gold.json'), 'gold changed after approval')
    require(approval.get('review_sha256') == sha(HERE / 'REVIEW.md'), 'review card changed after approval')
    ids = [case['id'] for case in manifest['cases']]
    require(ids == [case['id'] for case in gold['cases']] == approval['case_ids'], 'gold case mismatch')
    for case in manifest['cases']:
        path = HERE / case['input']
        require(path.is_file() and sha(path) == case['snapshot_sha256'], 'input snapshot changed: ' + case['id'])

    ratings = json.loads(ratings_path.read_text())
    require(ratings.get('review_status') == 'human_approved', 'ratings are not human approved')
    require(isinstance(ratings.get('reviewer'), str) and ratings['reviewer'].strip() and
            not ratings['reviewer'].lower().startswith('assistant'), 'ratings require a named human reviewer')
    rows = {row['id']: row for row in ratings.get('cases', [])}
    require(set(rows) == set(ids) and len(rows) == len(ids), 'ratings case coverage mismatch')
    for case_id, row in rows.items():
        require(all(row.get(key) in VALUES for key in DIMENSIONS), 'invalid rating: ' + case_id)
        directory = Path(row.get('result_directory') or '')
        require(directory.is_dir(), 'missing result directory: ' + case_id)
        artifacts = row.get('artifact_sha256')
        require(isinstance(artifacts, dict) and artifacts.get('status.json'),
                'status artifact hash required: ' + case_id)
        for name, expected in artifacts.items():
            if expected is not None:
                path = directory / name
                require(path.is_file() and sha(path) == expected,
                        'result artifact changed: ' + case_id + '/' + name)
        require(isinstance(row.get('reason'), str) and row['reason'].strip(),
                'rating reason required: ' + case_id)

    counts = {dimension: {value: sum(rows[c][dimension] == value for c in ids)
                          for value in VALUES} for dimension in DIMENSIONS}
    pass_cells = sum(counts[dimension]['pass'] for dimension in DIMENSIONS)
    exact_cases = sum(all(rows[c][dimension] == 'pass' for dimension in DIMENSIONS) for c in ids)
    return {
        'schema_version': 'stage2-gold-evaluation/1',
        'gold_reviewer': approval['reviewer'],
        'ratings_reviewer': ratings['reviewer'],
        'prompt_version': ratings['prompt_version'],
        'case_count': len(ids),
        'dimension_counts': counts,
        'strict_pass_cell_accuracy': pass_cells / (len(ids) * len(DIMENSIONS)),
        'exact_case_accuracy': exact_cases / len(ids),
        'exact_case_pass_count': exact_cases,
        'accuracy_scope': 'five selected clear public reports; not population accuracy',
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--approval', type=Path, default=HERE / 'approved-gold.json')
    parser.add_argument('--ratings', type=Path, required=True)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    result = evaluate(args.approval, args.ratings)
    rendered = json.dumps(result, ensure_ascii=False, indent=2) + '\n'
    if args.output:
        with args.output.open('x') as stream:
            stream.write(rendered)
    print(rendered, end='')


if __name__ == '__main__':
    main()
