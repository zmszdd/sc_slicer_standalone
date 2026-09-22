"""Regression coverage for input-policy and current-plan offline replay."""
import json
from pathlib import Path
import tempfile
import unittest

import verify_semantic


HERE = Path(__file__).resolve().parents[1]


class CurrentReplayTests(unittest.TestCase):
    def test_accepted_retry_path_is_selected(self):
        with tempfile.TemporaryDirectory() as dirname:
            root = Path(dirname)
            (root / 'formalization-attempts.json').write_text(json.dumps([
                {'artifact_dir': 'neural-formalization', 'outcome': 'retryable_failure'},
                {'artifact_dir': 'neural-formalization-retry-1',
                 'outcome': 'accepted_for_validation'},
            ]))
            self.assertEqual(verify_semantic.accepted_model_claim_path(root),
                             root / 'neural-formalization-retry-1/model-claim.json')

    def test_retry_path_traversal_is_rejected(self):
        with tempfile.TemporaryDirectory() as dirname:
            root = Path(dirname)
            (root / 'formalization-attempts.json').write_text(json.dumps([
                {'artifact_dir': '../outside', 'outcome': 'accepted_for_validation'},
            ]))
            with self.assertRaises(ValueError):
                verify_semantic.accepted_model_claim_path(root)

    def test_second_retry_path_is_selected(self):
        with tempfile.TemporaryDirectory() as dirname:
            root = Path(dirname)
            (root / 'formalization-attempts.json').write_text(json.dumps([
                {'artifact_dir': 'neural-formalization', 'outcome': 'retryable_failure'},
                {'artifact_dir': 'neural-formalization-retry-1',
                 'outcome': 'retryable_failure'},
                {'artifact_dir': 'neural-formalization-retry-2',
                 'outcome': 'accepted_for_validation'},
            ]))
            self.assertEqual(verify_semantic.accepted_model_claim_path(root),
                             root / 'neural-formalization-retry-2/model-claim.json')

    def test_saved_current_and_retry_results_replay_if_available(self):
        paths = (
            'results/semantic/p_repair_02/hybra_address_guard',
            'results/semantic/p_repair_01/intuition_numeric_guard_retest',
            'results/semantic/generalization_probe_01/forte_sqrt_zero',
        )
        available = [HERE / path for path in paths if (HERE / path / 'constraints.json').is_file()]
        if not available:
            self.skipTest('saved model outputs not included in this checkout')
        for path in available:
            with self.subTest(path=path):
                self.assertTrue(verify_semantic.verify(path)['offline_verified'])


if __name__ == '__main__':
    unittest.main()
