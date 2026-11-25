import json
import unittest
from pathlib import Path

METRICS = Path(__file__).resolve().parents[1] / 'evaluation' / 'metrics'


class FullsetMetricsTest(unittest.TestCase):
    def test_denominators_are_full_ground_truth(self):
        data = json.loads((METRICS / 'fullset_metrics.json').read_text())
        self.assertEqual(data['denominator']['positives'], 1465)
        self.assertEqual(data['denominator']['negatives'], 91)

    def test_confusion_matrix_is_consistent(self):
        cm = json.loads((METRICS / 'fullset_metrics.json').read_text())['confusion_matrix']
        self.assertEqual(cm['tp'] + cm['fn'], cm['positives'])
        self.assertLessEqual(cm['fp_raw'] + cm['tn'], cm['negatives_evaluated'])
        self.assertGreaterEqual(cm['tp'], 0)
        self.assertGreaterEqual(cm['fn'], 0)

    def test_metrics_ranges_and_ci_contain_point_estimate(self):
        data = json.loads((METRICS / 'fullset_metrics.json').read_text())
        for name in ('completion_rate', 'recall', 'recall_automatic',
                     'precision_consistency', 'precision_vuln', 'accuracy'):
            value = data['metrics'][name]
            self.assertIsNotNone(value)
            self.assertTrue(0.0 <= value <= 1.0)
            ci = data['confidence_intervals'][name]
            self.assertLessEqual(ci['low'], value + 1e-9)
            self.assertLessEqual(value, ci['high'] + 1e-9)


if __name__ == '__main__':
    unittest.main()
