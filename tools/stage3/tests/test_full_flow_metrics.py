import unittest

from cli.full_flow_metrics import analyze


class FullFlowMetricsTest(unittest.TestCase):
    def test_case_level_four_metrics(self):
        pos = {'cases': [
            {'status': 'done', 'reproduced': 2,
             'verdicts': ['violation_reproduced']},
            {'status': 'done', 'reproduced': 0,
             'verdicts': ['partial_binding']},
            {'status': 'stage2_blocked'},
        ]}
        neg = [{'verdict': 'violation_not_reproduced'},
               {'verdict': 'violation_reproduced'}]
        m = analyze(pos, neg)
        self.assertEqual(m['positive_total_cases'], 3)
        self.assertEqual(m['positive_completed_cases'], 2)
        self.assertEqual(m['positive_evaluable_cases'], 1)
        self.assertEqual(m['positive_blocked_cases'], 2)
        self.assertAlmostEqual(m['completion_rate'], 2 / 3)
        self.assertAlmostEqual(m['recall_rate'], 1.0)  # 1 tp / 1 evaluable
        self.assertEqual(m['tp_cases'], 1)
        self.assertEqual(m['fp_cases'], 1)
        self.assertAlmostEqual(m['precision'], 1 / 2)  # tp/(tp+fp)
        p, r = 0.5, 1.0
        self.assertAlmostEqual(m['f1'], 2 * p * r / (p + r))

    def test_not_dynamically_expressible_excluded_from_recall(self):
        pos = {'cases': [
            {'status': 'done', 'reproduced': 1,
             'verdicts': ['violation_reproduced']},
            {'status': 'done', 'reproduced': 0,
             'verdicts': ['not_dynamically_expressible']},
        ]}
        neg = [{'verdict': 'violation_not_reproduced'}]
        m = analyze(pos, neg)
        self.assertEqual(m['positive_evaluable_cases'], 1)
        self.assertEqual(m['positive_not_dynamically_expressible_cases'], 1)
        self.assertAlmostEqual(m['recall_rate'], 1.0)
        self.assertAlmostEqual(m['evaluable_coverage'], 0.5)


if __name__ == '__main__':
    unittest.main()


class JudgeAnchoredFullFlowTest(unittest.TestCase):
    def test_judge_anchored_nested_and_top_level_not_mixed(self):
        pos = {'cases': [
            {'status': 'done', 'reproduced': 1,
             'verdicts': ['violation_reproduced']},
            {'status': 'done', 'reproduced': 0,
             'verdicts': ['violation_not_reproduced']},
        ]}
        neg = [{'verdict': 'violation_not_reproduced'}]
        jm = {
            'tp_clean': 1,
            'fp_from_judge_invalid': 1,
            'fn_judge_valid': 0,
            'tn_invalid': 1,
            'judge_valid_cases': 1,
            'judge_valid_dynamic': 1,
            'precision': 0.5,
            'precision_ci': [0.0, 1.0],
        }
        m = analyze(pos, neg, judge_metrics=jm)
        # 顶层仍是构造负样本口径（FP=0 -> precision=1.0），不能被判例精度污染
        self.assertAlmostEqual(m['precision'], 1.0)
        ja = m['judge_anchored']
        self.assertAlmostEqual(ja['precision'], 0.5)
        self.assertAlmostEqual(ja['recall_evaluable'], 1.0)
        self.assertAlmostEqual(ja['f1_evaluable'], 2 * 0.5 * 1.0 / 1.5)
