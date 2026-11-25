import unittest

from evaluation.metrics.collect_stage3_runs import _next_action


class CollectStage3RunsTest(unittest.TestCase):
    def test_gate_verdicts_map_to_repair_routes(self):
        self.assertEqual(_next_action('stage2_review_required'),
                         'stage2_review')
        self.assertEqual(_next_action('stage2_restatement_required'),
                         'stage2_restate')
        self.assertEqual(_next_action('partial_binding'), 'binding_repair')
        self.assertEqual(_next_action('violation_reproduced'), 'none')

    def test_missing_verdict_is_explicit(self):
        self.assertEqual(_next_action(None), 'rerun')
        self.assertEqual(_next_action('future_verdict'), 'triage')


if __name__ == '__main__':
    unittest.main()
