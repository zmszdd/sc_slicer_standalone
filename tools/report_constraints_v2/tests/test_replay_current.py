"""Regression coverage for input-policy and current-plan offline replay."""
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from cli import batch_verify as verify_semantic


HERE = Path(__file__).resolve().parents[1]
# A versioned external-model run predating both the snapshot policy and the
# prompt-hash provenance fields: replay cross-checks the sent prompt texts
# (neural-*/prompt.txt) against the time-invariant frozen module.
NO_SNAPSHOT_RUN = HERE / 'results/semantic/generalization_probe_01/forte_sqrt_zero'
# A pre-versioning run: no prompt_version was recorded at all, so the sent
# prompts are required in-run but cannot be checked against the archive.
PRE_VERSIONING_RUN = HERE / 'results/semantic/multi_report_model_01/gte_zero_cost'
# An ID-era offline run: the evidence catalog is mandatory there.
ID_ERA_OFFLINE_RUN = HERE / 'results/semantic/brix_fee_ids_offline_01'
# A pre-catalog offline run: no *-ids.json artifacts exist, so replay has no
# ID resolution to check.
PRE_CATALOG_RUN = HERE / 'results/semantic/brix_fee_offline_01'


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

    def test_sent_prompt_tampering_is_rejected(self):
        # The era-aware fallback cross-checks the sent prompt against the
        # frozen module: rewriting the sent text breaks that identity.
        if not NO_SNAPSHOT_RUN.is_dir():
            self.skipTest('saved model outputs not included in this checkout')
        with tempfile.TemporaryDirectory() as work:
            copied = Path(work) / 'case'
            shutil.copytree(NO_SNAPSHOT_RUN, copied)
            element_prompt = copied / 'neural-elements' / 'prompt.txt'
            element_prompt.write_text('X' + element_prompt.read_text())
            with self.assertRaisesRegex(
                    ValueError, 'sent element prompt not rendered'):
                verify_semantic.verify(copied)
            formal_prompt = (verify_semantic.accepted_model_claim_path(copied).parent
                             / 'prompt.txt')
            formal_prompt.write_text('X' + formal_prompt.read_text())
            # Restore the element prompt so the formal failure is isolated.
            element_prompt.write_text(
                (NO_SNAPSHOT_RUN / 'neural-elements' / 'prompt.txt').read_text())
            with self.assertRaisesRegex(
                    ValueError, 'sent formal prompt not rendered'):
                verify_semantic.verify(copied)

    def test_deleted_sent_prompt_forfeits_replay(self):
        if not NO_SNAPSHOT_RUN.is_dir():
            self.skipTest('saved model outputs not included in this checkout')
        with tempfile.TemporaryDirectory() as work:
            copied = Path(work) / 'case'
            shutil.copytree(NO_SNAPSHOT_RUN, copied)
            (copied / 'neural-elements' / 'prompt.txt').unlink()
            with self.assertRaises(ValueError):
                verify_semantic.verify(copied)
        with tempfile.TemporaryDirectory() as work:
            copied = Path(work) / 'case'
            shutil.copytree(NO_SNAPSHOT_RUN, copied)
            (verify_semantic.accepted_model_claim_path(copied).parent
             / 'prompt.txt').unlink()
            with self.assertRaises(ValueError):
                verify_semantic.verify(copied)

    def test_pre_versioning_run_replays_but_requires_sent_prompts(self):
        if not PRE_VERSIONING_RUN.is_dir():
            self.skipTest('saved multi-report pilot run not included')
        report = verify_semantic.verify(PRE_VERSIONING_RUN)
        self.assertTrue(report['offline_verified'])
        self.assertIn('pre_versioning_sent_prompts', report['checks_performed'])
        with tempfile.TemporaryDirectory() as work:
            copied = Path(work) / 'case'
            shutil.copytree(PRE_VERSIONING_RUN, copied)
            (copied / 'neural-formalization' / 'prompt.txt').unlink()
            with self.assertRaisesRegex(ValueError, 'replay forfeited'):
                verify_semantic.verify(copied)

    def test_catalog_is_mandatory_for_id_era_runs_only(self):
        # Deleting the catalog from an ID-era run still forfeits replay...
        with tempfile.TemporaryDirectory() as work:
            copied = Path(work) / 'case'
            shutil.copytree(ID_ERA_OFFLINE_RUN, copied)
            (copied / 'evidence-catalog.json').unlink()
            with self.assertRaisesRegex(ValueError, 'evidence catalog missing'):
                verify_semantic.verify(copied)
        # ...while a pre-catalog run (no *-ids.json artifacts) keeps replaying
        # without one: its era never wrote ID artifacts to resolve.
        report = verify_semantic.verify(PRE_CATALOG_RUN)
        self.assertTrue(report['offline_verified'])
        self.assertNotIn('evidence_catalog', report['checks_performed'])
        self.assertNotIn('id_hydration', report['checks_performed'])


if __name__ == '__main__':
    unittest.main()
