from __future__ import annotations

import unittest

from evaluation.metrics.metrics_core import (completion_rate, confusion_metrics,
                                             accuracy_rate, cluster_bootstrap_ci,
                                             f1, precision_rate, recall)


class MetricsCoreTest(unittest.TestCase):
    def test_f1_and_recall(self):
        self.assertEqual(accuracy_rate(8, 2, 2, 8), 16 / 20)
        self.assertEqual(accuracy_rate(0, 0, 0, 0), 0.0)
        self.assertEqual(recall(74, 101), 74 / 101)
        self.assertEqual(recall(0, 0), 0.0)
        self.assertEqual(precision_rate(74, 89), 74 / 89)
        self.assertEqual(completion_rate(102, 105), 102 / 105)
        self.assertEqual(f1(None, 0.5), None)
        self.assertEqual(f1(0.5, 0.0), 0.0)
        self.assertAlmostEqual(f1(1.0, 1.0), 1.0)

    def test_confusion_metrics_matches_authoritative_values(self):
        block = confusion_metrics(
            tp=74, fp=15, fn=27, tn=60,
            fp_impact_insufficient=12, automatic_tp=62,
        )
        self.assertEqual(block['accuracy'], 0.7614)
        self.assertEqual(block['recall'], 0.7327)
        self.assertEqual(block['precision_vuln'], 0.961)
        self.assertEqual(block['precision_consistency'], 0.8315)
        self.assertEqual(block['recall_automatic'], 0.6139)
        self.assertEqual(block['f1_vuln'], 0.8315)

    def test_confusion_metrics_fp_vuln_falls_back(self):
        block = confusion_metrics(tp=10, fp=5, fn=10, tn=0)
        self.assertEqual(block['precision_vuln'], 0.6667)
        self.assertEqual(block['precision'], block['precision_vuln'])

    def test_cluster_bootstrap_resamples_projects_not_rows(self):
        rows = [
            {'project': 'a', 'value': 1}, {'project': 'a', 'value': 1},
            {'project': 'a', 'value': 1}, {'project': 'b', 'value': 0},
        ]
        low, high = cluster_bootstrap_ci(
            rows, lambda xs: sum(x['value'] for x in xs) / len(xs),
            samples=200, seed=3)
        self.assertIsNotNone(low)
        self.assertIsNotNone(high)
        self.assertLessEqual(low, high)
        self.assertEqual(cluster_bootstrap_ci([], lambda xs: 0), (None, None))


if __name__ == '__main__':
    unittest.main()
