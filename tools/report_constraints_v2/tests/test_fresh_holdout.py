"""Offline checks for the frozen, previously unused stage-2 pilot."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

HERE = Path(__file__).resolve().parents[1]
EVALUATOR = HERE / 'evaluation/fresh_holdout_01/evaluate.py'
spec = importlib.util.spec_from_file_location('fresh_holdout_evaluator', EVALUATOR)
evaluator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(evaluator)


class FreshHoldoutTests(unittest.TestCase):
    def test_manifest_and_unrun_rates(self):
        manifest_path = EVALUATOR.with_name('manifest.json')
        manifest = json.loads(manifest_path.read_text())
        if not Path(manifest['source_root']).is_dir():
            self.skipTest('external report corpus not available')
        validated = evaluator.validate_manifest(manifest_path)
        self.assertEqual(len(validated['cases']), 8)
        with tempfile.TemporaryDirectory() as dirname:
            result = evaluator.evaluate_runs(validated, Path(dirname))
        self.assertEqual(result['attempted'], 0)
        self.assertIsNone(result['z3_success_rate_on_attempted'])
        self.assertIsNone(result['semantic_accuracy'])

    def test_unrun_case_cannot_be_rated_pass(self):
        manifest = {'cases': [{'case_id': 'example'}]}
        with tempfile.TemporaryDirectory() as dirname:
            root = Path(dirname)
            ratings = {'schema_version': 'stage2-fresh-ratings/1',
                       'reviewer_kind': 'human', 'reviewer': 'independent reviewer',
                       'cases': [{'case_id': 'example', 'artifact_sha256': {},
                                  'dimensions': {name: 'pass' for name in evaluator.DIMENSIONS},
                                  'reason': 'test'}]}
            ratings_path = root / 'ratings.json'
            ratings_path.write_text(json.dumps(ratings))
            with self.assertRaisesRegex(ValueError, 'cannot receive semantic ratings'):
                evaluator.evaluate_ratings(manifest, root, ratings_path)


if __name__ == '__main__':
    unittest.main()
