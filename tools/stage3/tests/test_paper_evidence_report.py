import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from evaluation.metrics import metric_alignment_report as alignment
from evaluation.metrics import paper_evidence_report as report


class PaperEvidenceReportTest(unittest.TestCase):
    def test_build_uses_authoritative_metrics_and_gate_evidence(self):
        built = report.build()
        authority = json.loads(
            report.MAINLINE_METRICS.read_text(encoding='utf-8'))

        self.assertEqual(built['schema_version'], report.SCHEMA_VERSION)
        self.assertEqual(built['authoritative']['metrics']['accuracy'],
                         authority['metrics']['accuracy'])
        self.assertEqual(built['authoritative']['metrics']['recall'],
                         authority['metrics']['recall'])
        self.assertEqual(built['authoritative']['metrics']['precision_vuln'],
                         authority['metrics']['precision_vuln'])
        self.assertEqual(built['authoritative']['metrics']['f1_vuln'],
                         authority['metrics']['f1_vuln'])
        canonical = built['authoritative']['canonical_metrics']
        self.assertEqual(canonical['accuracy'],
                         authority['canonical_metrics']['accuracy'])
        self.assertEqual(canonical['recall_conservative'],
                         authority['canonical_metrics']['recall'])
        self.assertEqual(canonical['precision'],
                         authority['canonical_metrics']['precision'])
        self.assertEqual(canonical['f1_conservative'],
                         authority['canonical_metrics']['f1'])
        self.assertEqual(
            built['authoritative']['canonical_ci95']['recall_conservative'],
            authority['confidence_intervals'][
                'recall_consistency_conservative'])
        self.assertEqual(
            built['authoritative']['canonical_ci95']['f1_conservative'],
            authority['confidence_intervals'][
                'f1_consistency_cluster_bootstrap'])
        self.assertEqual(
            built['gate_evidence']['dev252_eligible_current'], 0)
        self.assertFalse(
            built['gate_evidence']['dev252_in_authoritative_denominator'])
        self.assertFalse(
            built['gate_evidence']['legacy_diagnostics_gating'])
        self.assertFalse(
            built['gate_evidence']['report_rewrites_authoritative_metrics'])

    def test_dev_retrospective_keeps_conditional_and_full_pool_separate(self):
        dev = report._development_retrospective()
        self.assertTrue(dev['dev_denominator_is_primary'])
        self.assertAlmostEqual(dev['conditional_recall'], 173 / 252)
        self.assertAlmostEqual(dev['full_pool_recall'], 173 / 1465)
        self.assertIn('not dev252 recall', dev['full_pool_metric_scope'])
        self.assertLess(dev['full_pool_recall'], dev['conditional_recall'])
        self.assertIsNotNone(dev['full_pool_f1_ratio'])
        self.assertLess(dev['full_pool_f1_ratio'], dev['conditional_f1'])

    def test_markdown_labels_development_only_and_shows_both_recalls(self):
        built = report.build()
        text = report.markdown(built)
        canonical = built['authoritative']['canonical_metrics']
        conditional = (built['authoritative']['metrics']['recall'] * 100)
        conditional_recall = f'{conditional:.1f}%'
        canonical_recall = f"{canonical['recall_conservative'] * 100:.1f}%"
        self.assertIn('development-only companion', text)
        self.assertIn('权威数值只来自', text)
        self.assertIn('68.7%', text)
        self.assertIn('11.8%', text)
        self.assertIn('## 1. 权威主表', text)
        self.assertIn('Recall（consistency，保守，未评测计 FN）', text)
        self.assertIn(canonical_recall, text)
        self.assertIn(conditional_recall, text)
        self.assertIn('只作诊断', text)
        self.assertIn('不是 dev252 recall', text)
        if built['authoritative'].get('effect_adjudication', {}).get(
                'tp_revert_witness'):
            self.assertIn('revert-witness 重新裁决', text)

    def test_canonical_table_matches_metric_alignment_report(self):
        canonical = report.build()['authoritative']['canonical_metrics']
        alignment_rows = {row['name']: row['value']
                          for row in alignment.build()[
                              'canonical_main_table']}
        self.assertEqual(canonical['accuracy'],
                         alignment_rows[
                             'mainline_accuracy_consistency_conservative'])
        self.assertEqual(canonical['recall_conservative'],
                         alignment_rows[
                             'mainline_recall_consistency_conservative'])
        self.assertEqual(canonical['precision'],
                         alignment_rows[
                             'mainline_precision_consistency_evaluated'])
        self.assertEqual(canonical['f1_conservative'],
                         alignment_rows[
                             'mainline_f1_consistency_conservative'])

    def test_main_does_not_rewrite_authoritative_metrics(self):
        before = hashlib.sha256(
            report.MAINLINE_METRICS.read_bytes()).hexdigest()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.assertEqual(report.main([
                '--out-json', str(root / 'report.json'),
                '--out-md', str(root / 'report.md'),
            ]), 0)
            self.assertTrue((root / 'report.json').is_file())
            self.assertTrue((root / 'report.md').is_file())
        after = hashlib.sha256(
            report.MAINLINE_METRICS.read_bytes()).hexdigest()
        self.assertEqual(after, before)


if __name__ == '__main__':
    unittest.main()
