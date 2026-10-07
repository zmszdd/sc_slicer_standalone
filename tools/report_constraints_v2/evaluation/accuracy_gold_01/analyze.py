#!/usr/bin/env python3
"""Compute stage-2 translation accuracy from the blind gold review.

Metrics:
- Translation accuracy (candidates): gold pass rate per P/I/V dimension,
  strict all-pass rate, and faithful rate (no unfaithful rating).
- Rejection accuracy (non-candidates): correct catches vs misfires vs
  honest abstains.
- System accuracy: (gold-faithful candidates + gold-correct refusals) / 40,
  strict variant uses all-pass.
- Meta: agreement between the gold judge and the primary assistant review
  (validates the primary review).
"""

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
STAGE2 = HERE.parents[1]
EVAL = STAGE2 / 'evaluation'

FORMULA_KEYS = ('formula_preconditions', 'formula_required_property',
                'formula_bad_outcome')
ELEMENT_KEYS = ('element_preconditions', 'element_required_property',
                'element_bad_outcome')
RATING_MAP = {'faithful': 'pass', 'weakened': 'partial', 'unfaithful': 'fail'}


def primary_formula_ratings():
    """(batch, project) -> {'P','I','V'} primary-review ratings."""
    ratings = {}
    for batch in ('prompt_live1_blind_01', 'prompt_live2_blind_01',
                  'prompt_live3_blind_01', 'prompt_live4_blind_01',
                  'final_holdout_01'):
        path = EVAL / batch / 'SEMANTIC_REVIEW.json'
        if not path.is_file():
            continue
        data = json.loads(path.read_text())
        if 'ratings' in data:  # live1-3: flat list, full run names
            for row in data['ratings']:
                project = row['case'].split('__')[0]
                ratings[(batch, project)] = {
                    'P': row.get('formula_P'),
                    'I': row.get('formula_I'),
                    'V': row.get('formula_V'),
                    'route': row.get('route'),
                }
        else:  # live4/holdout: dict keyed by project name
            for project, row in data['cases'].items():
                formula = row.get('formula', {})
                ratings[(batch, project)] = {
                    'P': formula.get('P'),
                    'I': formula.get('I'),
                    'V': formula.get('V'),
                    'route': row.get('engineering'),
                }
    return ratings


def main():
    gold = json.loads((HERE / 'GOLD_REVIEW.json').read_text())['cases']
    primary = primary_formula_ratings()

    candidates, rejected = [], []
    for row in gold:
        (candidates if row.get('engineering_route') == 'candidate'
         else rejected).append(row)

    print(f'gold cases: {len(gold)} (candidates {len(candidates)}, '
          f'rejected {len(rejected)})')

    strict, faithful = [], []
    dim_counts = {}
    for row in candidates:
        ratings = {key: row.get(key, {}).get('rating', 'missing')
                   for key in ELEMENT_KEYS + FORMULA_KEYS}
        for key, rating in ratings.items():
            ok, weak, bad = dim_counts.setdefault(key, [0, 0, 0])
            if rating == 'faithful':
                dim_counts[key][0] += 1
            elif rating == 'weakened':
                dim_counts[key][1] += 1
            else:
                dim_counts[key][2] += 1
        if all(v == 'faithful' for v in ratings.values()):
            strict.append(row['case_id'])
        if all(v != 'unfaithful' for v in ratings.values()):
            faithful.append(row['case_id'])

    print('\n== translation accuracy (candidates, gold) ==')
    for key in ELEMENT_KEYS + FORMULA_KEYS:
        ok, weak, bad = dim_counts[key]
        print(f'  {key:28s} faithful {ok}/{len(candidates)}  '
              f'weakened {weak}  unfaithful {bad}')
    print(f'  strict all-six-pass: {len(strict)}/{len(candidates)}')
    print(f'  faithful (no unfaithful): {len(faithful)}/{len(candidates)}')

    verdicts = {}
    for row in rejected:
        verdicts.setdefault(row.get('rejection_verdict', '?'), []).append(
            (row['case_id'], row.get('reason', '')))
    print('\n== rejection accuracy (gold) ==')
    for verdict, cases in sorted(verdicts.items()):
        print(f'  {verdict}: {len(cases)}')
        for case, reason in cases:
            print(f'    - {case[:70]}')
            print(f'      {reason[:170]}')

    correct_refusals = len(verdicts.get('correct_catch', [])) + \
        len(verdicts.get('honest_abstain', []))
    print(f'  correct refusals: {correct_refusals}/{len(rejected)}')

    print('\n== system accuracy ==')
    strict_system = (len(strict) + correct_refusals) / len(gold)
    faithful_system = (len(faithful) + correct_refusals) / len(gold)
    print(f'  strict:   {len(strict)} + {correct_refusals} of {len(gold)} '
          f'= {strict_system:.0%}')
    print(f'  faithful: {len(faithful)} + {correct_refusals} of {len(gold)} '
          f'= {faithful_system:.0%}')

    print('\n== gold vs primary review (formula dims, all batches) ==')
    agree, disagree, total = 0, 0, 0
    disagreements = []
    for row in candidates:
        batch = row['batch']
        project = row['case_id'].split('::')[1].split('__')[0]
        mine = primary.get((batch, project))
        if not mine:
            continue
        for my_key, gold_key in (('P', 'formula_preconditions'),
                                 ('I', 'formula_required_property'),
                                 ('V', 'formula_bad_outcome')):
            gold_rating = row.get(gold_key, {}).get('rating')
            mapped = RATING_MAP.get(gold_rating, gold_rating)
            my_rating = mine.get(my_key)
            total += 1
            if mapped == my_rating:
                agree += 1
            else:
                disagree += 1
                disagreements.append(
                    (f'{batch}::{project}', my_key, my_rating, gold_rating))
    print(f'  formula-dim agreement: {agree}/{total}')
    for case, dim, mine, theirs in disagreements:
        print(f'    {case} {dim}: primary={mine} gold={theirs}')

    summary = {
        'schema_version': 'stage2-accuracy-metrics/1',
        'candidates': len(candidates),
        'rejected': len(rejected),
        'dimension_counts': {k: dict(zip(('faithful', 'weakened',
                                          'unfaithful'), v))
                             for k, v in dim_counts.items()},
        'strict_all_pass': len(strict),
        'faithful_no_unfaithful': len(faithful),
        'rejection_verdicts': {k: len(v) for k, v in verdicts.items()},
        'correct_refusals': correct_refusals,
        'system_accuracy_strict': round(strict_system, 3),
        'system_accuracy_faithful': round(faithful_system, 3),
        'primary_review_agreement': f'{agree}/{total}',
        'strict_cases': strict,
    }
    (HERE / 'METRICS.json').write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + '\n')
    print('\nwrote METRICS.json')


if __name__ == '__main__':
    main()
