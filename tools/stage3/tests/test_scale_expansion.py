from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'evaluation' / 'metrics' / 'scale_expansion.py'


def _load_scale_expansion():
    spec = importlib.util.spec_from_file_location('scale_expansion', SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ScaleExpansionVerifyTest(unittest.TestCase):
    def setUp(self):
        self.mod = _load_scale_expansion()
        self.tmp = Path(tempfile.mkdtemp())
        self.flatten = self.tmp / 'c4_pipeline_output'
        self.reports = self.tmp / 'code4rena_reports'
        self.flatten.mkdir()
        self.reports.mkdir()

    def test_ready_project_with_sorted_sol_and_submissions(self):
        proj = self.flatten / 'Recall_MW5DuS6ehpj'
        (proj / 'flatten_sorted').mkdir(parents=True)
        (proj / 'flatten_sorted' / 'a.sorted.sol').write_text('')
        sub = self.reports / 'Recall_MW5DuS6ehpj'
        sub.mkdir(parents=True)
        (sub / 'submission_1.json').write_text('{}')
        rows = self.mod.verify(
            {'queue': [{'project_id': 'MW5DuS6ehpj', 'project': 'Recall_MW5DuS6ehpj'}]},
            self.flatten, self.reports)
        self.assertTrue(rows[0]['ready'])
        self.assertEqual(rows[0]['sorted_sol_count'], 1)

    def test_discover_candidates_joins_slices_and_submissions(self):
        proj = self.flatten / 'Recall_MW5DuS6ehpj'
        (proj / 'flatten_sorted').mkdir(parents=True)
        (proj / 'flatten_sorted' / 'a.sorted.sol').write_text('')
        sub = self.reports / 'Recall_MW5DuS6ehpj'
        sub.mkdir(parents=True)
        (sub / 'submission_1.json').write_text('{}')
        rows = self.mod.discover_candidates(self.flatten, self.reports)
        by_id = {r['project_id']: r for r in rows}
        self.assertIn('MW5DuS6ehpj', by_id)
        self.assertTrue(by_id['MW5DuS6ehpj']['ready'])
        self.assertEqual(by_id['MW5DuS6ehpj']['submissions_count'], 1)

    def test_discover_marks_slice_only_not_ready(self):
        proj = self.flatten / 'NoReports_ZZZzzz12345'
        (proj / 'flatten_sorted').mkdir(parents=True)
        (proj / 'flatten_sorted' / 'a.sorted.sol').write_text('')
        rows = self.mod.discover_candidates(self.flatten, self.reports)
        by_id = {r['project_id']: r for r in rows}
        self.assertFalse(by_id['ZZZzzz12345']['ready'])
        self.assertIn('no submission dump', by_id['ZZZzzz12345']['blocker'])

    def test_missing_sorted_sol_not_ready(self):
        rows = self.mod.verify(
            {'queue': [{'project_id': 'X1', 'project': 'Proj_X1'}]},
            self.flatten, self.reports)
        self.assertFalse(rows[0]['ready'])
        self.assertEqual(rows[0]['sorted_sol_count'], 0)


if __name__ == '__main__':
    unittest.main()
