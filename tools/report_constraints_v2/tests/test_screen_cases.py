"""Offline input preflight tests; no external model calls."""
import json
from pathlib import Path
import tempfile
import unittest

from preview import screen_case


class ScreenCasesTests(unittest.TestCase):
    @staticmethod
    def make_case(root):
        case = root / 'case'
        case.mkdir()
        (case / 'report.json').write_text(json.dumps({
            'title': 'Unprotected transfer',
            'body': '## Description\nA caller may transfer funds without authorization.\n'
                    '## Impact\nThe owner loses those funds.'}))
        return case

    def test_valid_input_requires_semantic_gate(self):
        with tempfile.TemporaryDirectory() as work:
            result = screen_case(self.make_case(Path(work)))
            self.assertEqual(result['decision'], 'requires_semantic_input_screen')
            self.assertEqual(result['dimensions']['input_integrity'], 'passed')
            self.assertEqual(result['external_model_calls'], 0)
            self.assertNotIn('run_dir', result)

    def test_invalid_input_is_excluded_without_model_call(self):
        with tempfile.TemporaryDirectory() as work:
            result = screen_case(Path(work) / 'missing')
            self.assertEqual(result['decision'], 'exclude_invalid_input')
            self.assertEqual(result['external_model_calls'], 0)


if __name__ == '__main__':
    unittest.main()
