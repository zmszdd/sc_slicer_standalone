import json
import os
import tempfile
import unittest
from pathlib import Path

from evaluation.metrics import provenance_gate as gate
from evaluation.metrics import current_denominator as denominator
from lib import mainline_protocol


class ProvenanceGateTest(unittest.TestCase):
    def _write(self, path: Path, payload: dict) -> Path:
        path.write_text(json.dumps(payload))
        return path

    def test_latest_negative_sample_blocks_refresh(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ledger = self._write(root / 'ledger.json', {'rows': [
                {'claim_outcome': 'fn', 'summary_path': None},
            ]})
            dev24 = self._write(root / 'dev24.json', {'gate': {
                'negative_fp_zero': True,
                'negative_all_resolved': True,
            }})
            negative5 = self._write(root / 'negative5.json', {'gate': {
                'negative_fp_zero': False,
                'negative_all_resolved': True,
            }})
            recipe = self._write(root / 'recipe.json', {
                'summary': {'recipe_ready': 1},
            })
            sample = self._write(root / 'sample.json', {
                'positive_cases': ['p1', 'p2'],
                'negative_cases': ['n1', 'n2'],
                'negative_slice_ready': 2,
                'negative_source': None,
            })
            runs_dir = root / 'runs'
            runs_dir.mkdir()

            report = gate.build(ledger, dev24, recipe, negative5,
                                sample_path=sample, runs_dir=runs_dir)

            self.assertTrue(report['negative5_required'])
            self.assertFalse(report['refresh_allowed'])
            self.assertEqual(report['mode'], 'mainline-only/1')
            self.assertFalse(report['legacy_diagnostics']['gating'])
            self.assertFalse(report['legacy_diagnostics']['negative_gate_ok'])
            self.assertNotIn(
                'negative gate is not resolved with zero consistency '
                'and vulnerability FP', report['reasons'])
            self.assertTrue(any('mainline runs' in reason
                                for reason in report['reasons']))

    def test_stale_protocol_fingerprint_is_not_current(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = root / 'runs' / 'old'
            run_dir.mkdir(parents=True)
            (run_dir / 'stage3-summary.json').write_text(json.dumps({
                'case': 'p1',
                'claim_id': 'c1',
                'artifact_fingerprint': {
                    'schema_version': 'artifact-fingerprint/1',
                    'mainline_protocol': {
                        'version': 'mainline/0.0.0',
                        'sha256': '0' * 64,
                    },
                },
            }))
            self.assertEqual(
                gate._summary_provenance(
                    str(run_dir / 'stage3-summary.json')),
                'stale_protocol_run')

    def test_latest_summary_supersedes_stale_summary(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            protocol = mainline_protocol.current()
            current = {
                'schema_version': 'artifact-fingerprint/1',
                'mainline_protocol': {
                    'version': protocol['version'],
                    'sha256': protocol['sha256'],
                },
                'protocol_versions': denominator._current_versions(),
            }
            stale = {
                **current,
                'mainline_protocol': {
                    'version': 'mainline/0.0.0',
                    'sha256': '0' * 64,
                },
            }
            old_dir = root / 'runs' / 'old'
            new_dir = root / 'runs' / 'new'
            old_dir.mkdir(parents=True)
            new_dir.mkdir(parents=True)
            old_path = old_dir / 'stage3-summary.json'
            new_path = new_dir / 'stage3-summary.json'
            old_path.write_text(json.dumps({
                'case': 'p1', 'claim_id': 'c1',
                'artifact_fingerprint': stale,
            }))
            new_path.write_text(json.dumps({
                'case': 'p1', 'claim_id': 'c1',
                'artifact_fingerprint': current,
            }))
            os.utime(old_path, (1, 1))
            os.utime(new_path, (2, 2))
            sample = root / 'sample.json'
            sample.write_text(json.dumps({
                'positive_cases': ['p1'],
                'negative_cases': ['n1'],
                'selected_negatives': 1,
                'negative_slice_ready': 1,
            }))
            report = gate.build_mainline_gate(
                sample_path=sample, runs_dir=root / 'runs',
                denominator={'mainline': {'refresh_ready': True}})
            self.assertTrue(report['current_only'], report)
            self.assertEqual(report['runs_provenance'],
                             {'fingerprinted_run': 1})

    def test_frozen_negatives_may_be_a_subset_of_official_pool(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pool = root / 'pool.json'
            pool.write_text(json.dumps({'selected': [
                {'case': 'n1', 'validity': 'invalid'},
                {'case': 'n2', 'validity': 'invalid'},
                {'case': 'n3', 'validity': 'invalid'},
            ]}))
            sample = root / 'sample.json'
            sample.write_text(json.dumps({
                'positive_cases': [],
                'negative_cases': ['n1', 'n2'],
                'negative_source': str(pool),
            }))
            report = gate.build_mainline_gate(
                sample_path=sample, runs_dir=root / 'runs',
                denominator={'mainline': {'refresh_ready': True}})
            self.assertTrue(report['negative_pool_labels_ok'])
            self.assertNotIn(
                'official negative pool no longer matches frozen labels',
                report['reasons'])


if __name__ == '__main__':
    unittest.main()
