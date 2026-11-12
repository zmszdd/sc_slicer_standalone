#!/usr/bin/env python3
"""Back-compute candidate vs logically-complete denominators from stage2-assessment.json.

Usage: python3 evaluation/compute_double_denominator.py <round_dir>...
A round dir is scanned for runs_*/*/stage2-assessment.json.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STAGE2 = HERE.parent
sys.path.insert(0, str(STAGE2))

from cli.semantic_pipeline import piv_failure_bucket  # noqa: E402


def assessments(round_dir):
    for run in sorted(Path(round_dir).glob('runs_*')):
        for case in sorted(run.iterdir()):
            path = case / 'stage2-assessment.json'
            if path.is_file():
                yield case.name, json.loads(path.read_text())


def main():
    for round_dir in sys.argv[1:]:
        eligible = 0
        formalized = 0
        incomplete = 0
        defect = 0
        unclassified = 0
        per_case_incomplete = []
        for name, doc in assessments(round_dir):
            rf = doc.get('rule_formalization') or {}
            eligible += rf.get('eligible_complete_piv_count', 0)
            formalized += rf.get('formalized_complete_piv_count', 0)
            for item in rf.get('pending_impacts') or []:
                bucket = item.get('failure_bucket') or piv_failure_bucket(
                    item.get('reason', ''))
                if bucket == 'incomplete_piv':
                    incomplete += 1
                elif bucket == 'generator_defect':
                    defect += 1
                else:
                    unclassified += 1
            per_case_incomplete.append((name, sum(
                1 for i in rf.get('pending_impacts') or []
                if (i.get('failure_bucket') or piv_failure_bucket(i.get('reason', ''))) == 'incomplete_piv')))
        logically_complete = eligible - incomplete
        print(f'== {round_dir} ==')
        print(f'eligible={eligible} formalized={formalized} '
              f'incomplete_piv={incomplete} generator_defect={defect} '
              f'unclassified={unclassified}')
        print(f'candidate_rate={formalized/eligible if eligible else 0:.4f} '
              f'logically_complete_denominator={logically_complete} '
              f'logically_complete_rate={formalized/logically_complete if logically_complete else 0:.4f}')
        if incomplete:
            print('incomplete_piv cases:', [n.split("__")[0] for n, c in per_case_incomplete if c])
        print()


if __name__ == '__main__':
    main()
