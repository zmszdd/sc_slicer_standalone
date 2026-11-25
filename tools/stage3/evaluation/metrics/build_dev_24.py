#!/usr/bin/env python3
"""Build the frozen 24-case stratified development regression manifest.

The set is intentionally small.  It samples every major FN bucket plus the
known precision-failure families, and it never expands into the full dev pool.
Selection is deterministic and project-diverse; no result-based cherry-picking.
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
STAGE3 = HERE.parents[1]
CASES = STAGE3 / 'cases'
FROZEN = STAGE3 / 'evaluation' / 'frozen' / 'dev252_20261117.json'
BLIND_INVALID = HERE / 'positive_eval_blind_invalid.json'
IMPACT_INSUFFICIENT = HERE / 'impact_insufficient_cases.json'
OUT = STAGE3 / 'evaluation' / 'frozen' / 'dev24_20261117.json'

# Keep the failure mix visible instead of letting one large bucket dominate.
POSITIVE_QUOTAS = {
    'partial_binding': 4,
    'invariant_holds_on_exploit_path': 4,
    'poc_not_witnessed': 3,
    'mixed_non_dynamic': 3,
    'compile_error': 1,
    'binding_error': 1,
    'reference_patch_required': 1,
}
TP_QUOTA = 1
NEGATIVE_QUOTA = 6


def _load(path: Path) -> dict:
    return json.loads(path.read_text())


def _project(case: str) -> str:
    return case.split('__', 1)[0]


def _select_project_diverse(rows: list[dict], quota: int) -> list[dict]:
    """Pick one case per project first, then fill deterministically."""
    rows = sorted(rows, key=lambda row: (row.get('case_id') or row.get('case'),))
    chosen = []
    seen = set()
    for row in rows:
        case = row.get('case_id') or row.get('case')
        project = _project(case)
        if project in seen:
            continue
        chosen.append(row)
        seen.add(project)
        if len(chosen) == quota:
            return chosen
    for row in rows:
        if row in chosen:
            continue
        chosen.append(row)
        if len(chosen) == quota:
            break
    return chosen


def _case_exists(case: str) -> bool:
    return (CASES / case).is_dir()


def build() -> dict:
    frozen = _load(FROZEN)['case_list']['cases']
    by_bucket: dict[str, list[dict]] = defaultdict(list)
    for row in frozen:
        if row.get('label') != 'fn' or row.get('bucket') not in POSITIVE_QUOTAS:
            continue
        if _case_exists(row['case_id']):
            by_bucket[row['bucket']].append(row)

    positives = []
    for bucket, quota in POSITIVE_QUOTAS.items():
        selected = _select_project_diverse(by_bucket.get(bucket, []), quota)
        for row in selected:
            positives.append({**row, 'label': 'positive', 'bucket': bucket,
                              'source': 'frozen/dev252_20261117.json'})

    tp_rows = [row for row in frozen
               if row.get('label') == 'tp' and _case_exists(row['case_id'])]
    # Use a stable, non-Blackhole project so the one TP does not duplicate the
    # projects already represented by failure cases.
    tp_rows = sorted(tp_rows, key=lambda row: row['case_id'])
    positives.extend({**row, 'label': 'positive', 'bucket': 'tp',
                      'source': 'frozen/dev252_20261117.json'}
                     for row in tp_rows[:TP_QUOTA])

    blind = [row for row in _load(BLIND_INVALID).get('cases', [])
             if row.get('case') and _case_exists(row['case'])]
    impact = [case for case in _load(IMPACT_INSUFFICIENT).get('cases', [])
              if _case_exists(case)]
    negatives = []
    for case in sorted(impact, key=_project)[:3]:
        negatives.append({
            'case_id': case, 'label': 'negative', 'reason': 'impact_insufficient',
            'source': 'impact_insufficient_cases.json', 'project': _project(case),
            'case_dir': str((CASES / case).relative_to(STAGE3.parents[1])),
        })
    blind_selected = _select_project_diverse(
        [{'case_id': row['case'], 'source': 'positive_eval_blind_invalid.json',
          'project': _project(row['case'])} for row in blind],
        min(3, max(0, NEGATIVE_QUOTA - len(negatives))))
    for row in blind_selected:
        if len(negatives) >= NEGATIVE_QUOTA:
            break
        case = row['case_id']
        bucket = 'blind_invalid_gte' if 'GTE_' in case else 'blind_invalid_other'
        negatives.append({
            'case_id': case, 'label': 'negative', 'reason': bucket,
            'source': 'positive_eval_blind_invalid.json',
            'project': _project(case),
            'case_dir': str((CASES / case).relative_to(STAGE3.parents[1])),
        })

    cases = []
    for row in positives:
        case = row['case_id']
        cases.append({
            'case_id': case,
            'label': 'positive',
            'bucket': row['bucket'],
            'project': _project(case),
            'source': row['source'],
            'case_dir': row['case_dir'],
            'exists': _case_exists(case),
        })
    for row in negatives:
        cases.append({**row, 'exists': _case_exists(row['case_id'])})

    project_count = len({row['project'] for row in cases})
    baseline_tp = sum(row.get('bucket') == 'tp' for row in cases
                      if row.get('label') == 'positive')
    positive_count = len(positives)
    return {
        'schema_version': 'dev-regression-manifest/1',
        'name': 'dev24_20261117',
        'source_frozen': 'tools/stage3/evaluation/frozen/dev252_20261117.json',
        'policy': ('deterministic stratified development set; every major FN '
                   'bucket plus known FP families; not a test set'),
        'case_count': len(cases),
        'positive_count': positive_count,
        'negative_count': len(negatives),
        'project_count': project_count,
        'baseline': {
            'positive_tp': baseline_tp,
            'positive_total': positive_count,
            'positive_tp_rate': baseline_tp / positive_count if positive_count else 0.0,
            'note': ('derived from the frozen dev252 labels; this failure-heavy '
                     'set is a regression set, not a representative sample'),
        },
        'quotas': {**POSITIVE_QUOTAS, 'tp': TP_QUOTA,
                   'negative': NEGATIVE_QUOTA},
        'cases': cases,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=OUT)
    args = parser.parse_args(argv)
    record = build()
    args.out.write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({key: record[key] for key in
                      ('case_count', 'positive_count', 'negative_count',
                       'project_count')}, ensure_ascii=False, indent=2))
    missing = [row['case_id'] for row in record['cases'] if not row['exists']]
    if missing:
        print('missing case dirs:', missing)
    return 0 if record['case_count'] == 24 and not missing else 1


if __name__ == '__main__':
    raise SystemExit(main())
