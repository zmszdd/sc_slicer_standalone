import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from evaluation.sample_longtail import sample_longtail  # noqa: E402


def _row(key, project):
    return {'key': key, 'project': project}


class SampleLongTailTest(unittest.TestCase):
    def test_prioritises_long_tail(self):
        rows = [
            _row('a1', 'P1'), _row('a2', 'P1'), _row('a3', 'P1'),
            _row('b1', 'P2'), _row('b2', 'P2'),
            _row('c1', 'P3'),
        ]
        picked = sample_longtail(rows, seed=1, max_cases=3, per_project=1)
        projects = [r['project'] for r in picked]
        self.assertEqual(len(picked), 3)
        self.assertEqual(projects, ['P3', 'P2', 'P1'])

    def test_respects_per_project_and_max_cases(self):
        rows = [_row(f'a{i}', 'P1') for i in range(5)]
        rows += [_row(f'b{i}', 'P2') for i in range(5)]
        rows += [_row(f'c{i}', 'P3') for i in range(5)]
        picked = sample_longtail(rows, seed=1, max_cases=4, per_project=2)
        self.assertEqual(len(picked), 4)
        projects = [r['project'] for r in picked]
        self.assertLessEqual(projects.count('P1'), 2)
        self.assertLessEqual(projects.count('P2'), 2)
        self.assertLessEqual(projects.count('P3'), 2)


if __name__ == '__main__':
    unittest.main()
