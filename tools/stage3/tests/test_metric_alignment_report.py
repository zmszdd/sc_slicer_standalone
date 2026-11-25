import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from evaluation.metrics import metric_alignment_report as alignment
from lib import mainline_protocol


class MetricAlignmentReportTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.built = alignment.build()
        cls.authority = json.loads(
            alignment.MAINLINE_METRICS.read_text(encoding='utf-8'))

    def test_canonical_main_table_has_only_four_authoritative_metrics(self):
        rows = {row['name']: row for row in self.built['canonical_main_table']}
        self.assertEqual(set(rows), {
            'mainline_accuracy_consistency_conservative',
            'mainline_recall_consistency_conservative',
            'mainline_precision_consistency_evaluated',
            'mainline_f1_consistency_conservative',
        })
        metrics = self.authority['metrics']
        canonical_metrics = self.authority['canonical_metrics']
        cm = self.authority['confusion_matrix']
        self.assertEqual(
            rows['mainline_accuracy_consistency_conservative']['value'],
            canonical_metrics['accuracy'])
        self.assertEqual(
            rows['mainline_recall_consistency_conservative']['value'],
            canonical_metrics['recall'])
        self.assertEqual(
            rows['mainline_precision_consistency_evaluated']['value'],
            canonical_metrics['precision'])
        self.assertEqual(
            rows['mainline_f1_consistency_conservative']['value'],
            canonical_metrics['f1'])
        self.assertEqual(
            rows['mainline_recall_consistency_conservative']['ratio'],
            f"{cm['tp_consistency']}/{self.authority['sample']['positives']}")
        self.assertEqual(
            rows['mainline_precision_consistency_evaluated']['ratio'],
            f"{cm['tp_consistency']}/"
            f"{cm['tp_consistency'] + cm['fp_raw']}")
        self.assertEqual(
            rows['mainline_accuracy_consistency_conservative']['ci95'],
            self.authority['confidence_intervals'][
                'accuracy_consistency_conservative'])
        self.assertEqual(
            rows['mainline_recall_consistency_conservative']['ci95'],
            self.authority['confidence_intervals'][
                'recall_consistency_conservative'])
        self.assertEqual(
            rows['mainline_f1_consistency_conservative']['ci95'],
            self.authority['confidence_intervals'][
                'f1_consistency_cluster_bootstrap'])

    def test_diagnostics_stay_out_of_canonical_table(self):
        canonical = {row['name'] for row in
                     self.built['canonical_main_table']}
        diagnostics = {row['name'] for row in
                       self.built['same_protocol_diagnostics']}
        self.assertIn('diagnostic_completion_rate', diagnostics)
        self.assertIn('diagnostic_precision_consistency', diagnostics)
        self.assertTrue(diagnostics.isdisjoint(canonical))
        for row in self.built['same_protocol_diagnostics']:
            self.assertIn('not paper main table', row['allowed_use'])

    def test_dev252_conditional_and_full_pool_are_not_confused(self):
        rows = {row['name']: row for row in
                self.built['development_retrospective']['metrics']}
        conditional = rows['dev252_conditional_recall']
        lower_bound = rows['dev252_full_pool_recall_lower_bound']
        self.assertEqual(conditional['ratio'], '173/252')
        self.assertAlmostEqual(conditional['value'], 173 / 252)
        self.assertEqual(lower_bound['ratio'], '173/1465')
        self.assertAlmostEqual(lower_bound['value'], 173 / 1465)
        self.assertIn('not dev252 recall', lower_bound['allowed_use'])
        self.assertEqual(
            self.built['development_retrospective']['status'],
            'development-only; not authoritative; not a locked test')

    def test_aplus_smoke_keeps_old_protocol_and_appendix_scope(self):
        smoke = self.built['aplus_hardened_smoke']
        self.assertEqual(smoke['protocol'], 'mainline/1.6.1')
        self.assertFalse(smoke['reportable'])
        self.assertEqual(smoke['allowed_use'], 'appendix diagnostic only')
        self.assertAlmostEqual(smoke['metrics']['accuracy'], 0.7297)
        self.assertAlmostEqual(smoke['metrics']['recall'], 0.8125)
        self.assertAlmostEqual(smoke['metrics']['precision_vuln'], 1.0)
        self.assertAlmostEqual(
            smoke['metrics']['precision_consistency'], 0.8667)
        self.assertAlmostEqual(smoke['metrics']['f1_vuln'], 0.8966)

    def test_forbidden_comparisons_and_naming_rules_are_explicit(self):
        forbidden = {row['id']: row
                     for row in self.built['forbidden_comparisons']}
        self.assertIn('dev252_vs_mainline_recall', forbidden)
        self.assertEqual(forbidden['smoke_vs_mainline']['decision'],
                         'forbidden')
        self.assertEqual(forbidden['completion_as_performance']['decision'],
                         'forbidden')
        self.assertIn(
            'mainline_recall_consistency_conservative',
            forbidden['completion_as_performance']['pair'])
        rules = {row['ambiguous_name']: row['canonical_name']
                 for row in self.built['naming_rules']}
        self.assertEqual(rules['dev252 recall'],
                         'dev252_conditional_recall')
        self.assertEqual(rules['173/1465'],
                         'dev252_full_pool_recall_lower_bound')
        self.assertEqual(rules['completion rate'],
                         'diagnostic_completion_rate')

    def test_gate_evidence_exposes_coverage_without_publishing(self):
        gates = self.built['gate_evidence']
        self.assertEqual(gates['protocol_version'],
                         mainline_protocol.current()['version'])
        self.assertTrue(gates['locked_ready'])
        self.assertFalse(gates['locked_publishable'])
        self.assertEqual(gates['publication_status'], 'coverage-limited')
        self.assertEqual(gates['coverage']['eligible_positive'], 35)
        locked = json.loads((alignment.MAINLINE_METRICS.parent /
                             'locked_eval_contract.json').read_text())
        self.assertEqual(gates['coverage']['eligible_negative'],
                         locked['gates']['eligible_negative'])
        self.assertTrue(self.built[
            'report_does_not_rewrite_authoritative_metrics'])
        self.assertEqual(
            self.built['source_of_truth'],
            'tools/stage3/evaluation/metrics/mainline_metrics.json')

    def test_markdown_labels_every_non_authoritative_bucket(self):
        text = alignment.markdown(self.built)
        self.assertIn('不改写权威指标', text)
        self.assertIn('不得进入主表', text)
        self.assertIn('不得作为权威主表', text)
        self.assertIn('不得与主线比较', text)
        self.assertIn('不是 dev252 recall', text)
        self.assertIn('173/252 = 68.7%', text)
        self.assertIn('173/1465 = 11.8%', text)
        self.assertIn('正例 35/40', text)
        self.assertIn(
            f"负例 {self.built['gate_evidence']['coverage']['eligible_negative']}/40",
            text)

    def test_main_does_not_rewrite_authoritative_metrics(self):
        before = hashlib.sha256(
            alignment.MAINLINE_METRICS.read_bytes()).hexdigest()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.assertEqual(alignment.main([
                '--out-json', str(root / 'report.json'),
                '--out-md', str(root / 'report.md'),
            ]), 0)
            written = json.loads((root / 'report.json').read_text(
                encoding='utf-8'))
            self.assertEqual(written, self.built)
            self.assertIn('不改写权威指标',
                          (root / 'report.md').read_text(encoding='utf-8'))
        after = hashlib.sha256(
            alignment.MAINLINE_METRICS.read_bytes()).hexdigest()
        self.assertEqual(after, before)


if __name__ == '__main__':
    unittest.main()
