import unittest

from evaluation.metrics.blind_metrics import compute_metrics


def _rows():
    return [
        {'case': 'a', 'status': 'done', 'claims': 2, 'reproduced': 1,
         'automatic_reproduced': 1},
        {'case': 'b', 'status': 'done', 'claims': 3, 'reproduced': 0,
         'automatic_reproduced': 0},
        {'case': 'c', 'status': 'no_stage2_run'},
    ]


class BlindMetricsTest(unittest.TestCase):
    def test_runnable_subset_recall(self):
        agg = compute_metrics(_rows(), ['a', 'b'], full_positives=None)
        self.assertEqual(agg['selected_runnable_cases'], 2)
        self.assertEqual(agg['tp'], 1)
        self.assertEqual(agg['fn'], 1)
        self.assertAlmostEqual(agg['metrics']['recall'], 0.5)
        self.assertIsNone(agg['recall_full_set'])

    def test_full_set_recall_uses_all_positives(self):
        agg = compute_metrics(_rows(), ['a', 'b'], full_positives=10)
        self.assertEqual(agg['full_set_positives'], 10)
        self.assertEqual(agg['tp'], 1)
        self.assertEqual(agg['fn_full_set'], 9)
        self.assertAlmostEqual(agg['recall_full_set'], 0.1)

    def test_in_scope_recall_excludes_unrunnable(self):
        agg = compute_metrics(_rows(), ['a', 'b'], full_positives=10,
                              in_scope_positives=8)
        self.assertEqual(agg['in_scope_positives'], 8)
        self.assertEqual(agg['fn_in_scope'], 7)
        self.assertAlmostEqual(agg['recall_in_scope'], 0.125)

    def test_automatic_recall_separates_from_reference_patch(self):
        rows = [
            {'case': 'a', 'status': 'done', 'claims': 1, 'reproduced': 1,
             'automatic_reproduced': 0, 'reference_patch_reproduced': 1},
        ]
        agg = compute_metrics(rows, ['a'], full_positives=None)
        self.assertEqual(agg['tp'], 1)
        self.assertEqual(agg['tp_automatic'], 0)
        self.assertAlmostEqual(agg['metrics']['recall_automatic'], 0.0)


if __name__ == '__main__':
    unittest.main()
