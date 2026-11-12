import json
import tempfile
import unittest
from pathlib import Path

from cli.eval_report import analyze_eval_run, analyze_runs


class EvalReportTest(unittest.TestCase):
    def test_analyze_eval_run_buckets_losses(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'summary.json'
            path.write_text(json.dumps({
                'cases': [
                    {'status': 'done', 'verdicts': [
                        'violation_reproduced', 'inconclusive',
                        'compile_blocked', 'reference_patch_required']},
                ],
            }))
            metrics = analyze_eval_run(path)
            self.assertEqual(metrics['total_claims'], 4)
            self.assertEqual(metrics['reproduced'], 1)
            self.assertEqual(metrics['recall_full'], 0.25)
            self.assertEqual(metrics['loss_buckets']['inconclusive'], 1)
            self.assertEqual(metrics['loss_buckets']['compile_blocked'], 1)
            self.assertEqual(metrics['loss_buckets']['reference_patch_required'], 1)

    def test_analyze_runs_only_counts_routed_for_auto_recall(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'a').mkdir()
            (root / 'a' / 'stage3-summary.json').write_text(json.dumps({
                'consistency_verdict': 'violation_reproduced'}))
            (root / 'a' / 'routing.json').write_text(json.dumps({
                'schema_version': 'stage3-routing/1',
                'route': 'auto_assert', 'auto_verifiable': True,
                'requires_reference_patch': False}))
            (root / 'b').mkdir()
            (root / 'b' / 'stage3-summary.json').write_text(json.dumps({
                'consistency_verdict': 'reference_patch_required'}))
            (root / 'b' / 'routing.json').write_text(json.dumps({
                'schema_version': 'stage3-routing/1',
                'route': 'reference_patch_cross_contract',
                'auto_verifiable': False,
                'requires_reference_patch': True}))
            metrics = analyze_runs(root)
            self.assertEqual(metrics['total_claims'], 2)
            self.assertEqual(metrics['routed_claims'], 2)
            self.assertEqual(metrics['auto_verifiable_claims'], 1)
            self.assertEqual(metrics['auto_verifiable_reproduced'], 1)
            self.assertEqual(metrics['recall_auto_verifiable'], 1.0)
            self.assertEqual(metrics['reference_patch_required_claims'], 1)


if __name__ == '__main__':
    unittest.main()
