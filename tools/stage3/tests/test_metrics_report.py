import unittest

from cli.metrics_report import analyze, render_md


class MetricsReportTest(unittest.TestCase):
    def _pos(self):
        return {'cases': [
            {'case': 'ProjA__f1__s1', 'status': 'done', 'reproduced': 1,
             'verdicts': ['violation_reproduced']},
            {'case': 'ProjA__f2__s2', 'status': 'done', 'reproduced': 0,
             'verdicts': ['partial_binding']},
            {'case': 'ProjB__f3__s3', 'status': 'done', 'reproduced': 0,
             'verdicts': ['violation_not_reproduced']},
            {'case': 'ProjC__f4__s4', 'status': 'stage2_blocked'},
        ]}

    def test_funnel_and_coverage_loss(self):
        m = analyze(self._pos(), [])
        self.assertEqual(m['funnel']['stage1_flatten']['n'], 4)
        self.assertEqual(m['funnel']['stage2_spec_nonempty']['n'], 3)
        self.assertEqual(m['funnel']['stage3_dynamic']['n'], 2)
        self.assertEqual(m['funnel']['stage3_reproduced']['n'], 1)
        self.assertEqual(m['coverage_loss_total'], 2)
        self.assertIn('stage2:stage2_blocked', m['coverage_loss'])
        self.assertIn('stage3:partial_binding', m['coverage_loss'])

    def test_project_level_recall(self):
        m = analyze(self._pos(), [])
        p = m['project_level']
        self.assertEqual(p['total_projects'], 3)
        self.assertEqual(p['recalled_projects'], 1)
        self.assertAlmostEqual(p['recall'], 1 / 3)

    def test_multi_recall_denominators(self):
        m = analyze(self._pos(), [])
        self.assertAlmostEqual(m['metrics']['recall_end_to_end'], 1 / 4)
        self.assertAlmostEqual(m['metrics']['recall_evaluable'], 1 / 2)
        self.assertAlmostEqual(m['metrics']['recall_project_level'], 1 / 3)

    def test_precision_with_fp(self):
        pos = self._pos()
        neg = [{'verdict': 'violation_not_reproduced'},
               {'verdict': 'violation_reproduced'}]
        m = analyze(pos, neg)
        self.assertEqual(m['metrics']['tp_cases'], 1)
        self.assertEqual(m['metrics']['fp_cases'], 1)
        self.assertAlmostEqual(m['metrics']['precision_constructed_negatives'], 0.5)

    def test_coverage_loss_has_no_case_level_ceiling_dominated(self):
        pos = {'cases': [
            {'case': 'ProjA__f1__s1', 'status': 'done', 'reproduced': 0,
             'verdicts': ['reference_patch_required', 'reference_patch_required',
                          'reference_patch_required', 'partial_binding']},
            {'case': 'ProjA__f2__s2', 'status': 'done', 'reproduced': 0,
             'verdicts': ['partial_binding', 'reference_patch_required']},
        ]}
        m = analyze(pos, [])
        self.assertNotIn('stage3:ceiling_dominated', m['coverage_loss'])
        self.assertEqual(m['coverage_loss']['stage3:mixed_non_dynamic'], 2)
        self.assertEqual(m['coverage_loss_claims']['stage3:reference_patch_required'], 4)
        self.assertEqual(m['coverage_loss_claims']['stage3:partial_binding'], 2)

    def test_render_md_contains_funnel(self):
        md = render_md(analyze(self._pos(), []))
        self.assertIn('主线漏斗', md)
        self.assertIn('覆盖损失', md)

    def test_claim_level_coverage_loss_splits_mixed_verdicts(self):
        pos = {'cases': [
            {'case': 'ProjA__f1__s1', 'status': 'done', 'reproduced': 0,
             'verdicts': ['partial_binding', 'compile_error'],
             'bound_claim_ids': ['c1', 'c2']},
            {'case': 'ProjA__f2__s2', 'status': 'done', 'reproduced': 0,
             'verdicts': ['partial_binding']},
        ]}
        m = analyze(pos, [])
        self.assertEqual(m['coverage_loss_claims']['stage3:partial_binding'], 2)
        self.assertEqual(m['coverage_loss_claims']['stage3:compile_error'], 1)
        self.assertEqual(m['coverage_loss_claims_total'], 3)
        self.assertEqual(len(m['mixed_claim_cases']), 1)
        self.assertEqual(m['mixed_claim_cases'][0]['claim_breakdown']['compile_error'], ['c2'])
        md = render_md(m)
        self.assertIn('多 claim 状态混杂明细', md)
        self.assertIn('claim 级拆分', md)

    def test_claim_breakdown_prefers_full_claim_ids(self):
        pos = {'cases': [
            {'case': 'ProjA__f1__s1', 'status': 'done', 'reproduced': 0,
             'claim_ids': ['c_a', 'c_b'],
             'bound_claim_ids': ['c_b'],
             'verdicts': ['partial_binding', 'compile_error']},
        ]}
        m = analyze(pos, [])
        self.assertEqual(
            m['mixed_claim_cases'][0]['claim_breakdown']['partial_binding'],
            ['c_a'])
        self.assertEqual(
            m['mixed_claim_cases'][0]['claim_breakdown']['compile_error'],
            ['c_b'])


if __name__ == '__main__':
    unittest.main()


class JudgeAnchoredTest(unittest.TestCase):
    def _pos(self):
        return {'cases': [
            {'case': 'ProjA__f1__s1', 'status': 'done', 'reproduced': 1,
             'verdicts': ['violation_reproduced']},
            {'case': 'ProjA__f2__s2', 'status': 'done', 'reproduced': 1,
             'verdicts': ['violation_reproduced']},
            {'case': 'ProjB__f3__s3', 'status': 'done', 'reproduced': 0,
             'verdicts': ['violation_not_reproduced']},
            {'case': 'ProjB__f4__s4', 'status': 'stage2_blocked',
             'reproduced': None},
        ]}

    def test_judge_anchored_confusion_matrix(self):
        # 判例：f1 valid(TP)、f2 invalid(FP)、f3 valid(FN)、f4 valid(FN)
        jm = {
            'tp_clean': 1,
            'judge_valid_cases': 3,
            'judge_valid_dynamic': 2,
            'fn_judge_valid': 2,
            'fp_from_judge_invalid': 1,
            'tn_invalid': 1,
            'precision': 0.5,
            'precision_ci': [0.0, 1.0],
            'recall_end_to_end_ci': [0.0, 1.0],
            'recall_evaluable_ci': [0.0, 1.0],
        }
        m = analyze(self._pos(), [], judge_metrics=jm)
        ja = m['metrics']['judge_anchored']
        self.assertEqual(ja['tp_judge_clean'], 1)
        self.assertEqual(ja['fn_judge_valid'], 2)
        self.assertAlmostEqual(ja['recall_end_to_end'], 1 / 3)
        self.assertAlmostEqual(ja['recall_evaluable'], 1 / 2)
        self.assertAlmostEqual(ja['precision'], 0.5)
        self.assertAlmostEqual(ja['f1_end_to_end'], 0.4)
        self.assertAlmostEqual(ja['f1_evaluable'], 0.5)

    def test_impact_gated_precision_and_f1(self):
        jm = {
            'tp_clean': 43,
            'judge_valid_cases': 101,
            'judge_valid_dynamic': 57,
            'fn_judge_valid': 58,
            'fp_from_judge_invalid': 15,
            'tn_invalid': 60,
            'precision': 43 / 58,
            'precision_ci': [0.6, 0.8],
            'precision_vuln_level': 0.9347826086956522,
            'precision_vuln_level_ci': [0.825, 0.978],
            'recall_end_to_end_ci': [0.3, 0.5],
            'recall_evaluable_ci': [0.6, 0.9],
        }
        m = analyze(self._pos(), [], judge_metrics=jm)
        ja = m['metrics']['judge_anchored']
        self.assertAlmostEqual(ja['precision_vuln_level'], 0.9347826086956522)
        self.assertGreater(ja['f1_vuln_end_to_end'], ja['f1_end_to_end'])
        self.assertLess(ja['f1_vuln_evaluable'], 1.0)

    def test_end_to_end_ceiling_from_judge_metrics(self):
        jm = {
            'tp_clean': 43,
            'judge_valid_cases': 101,
            'judge_valid_dynamic': 57,
            'fn_judge_valid': 58,
            'fp_from_judge_invalid': 15,
            'tn_invalid': 60,
            'precision': 43 / 58,
            'precision_ci': [0.6, 0.8],
            'recall_end_to_end_ci': [0.3, 0.5],
            'recall_evaluable_ci': [0.6, 0.9],
            'ceiling_count': 7,
            'recoverable_fn_count': 51,
            'recall_end_to_end_ceiling': 0.931,
        }
        m = analyze(self._pos(), [], judge_metrics=jm)
        ja = m['metrics']['judge_anchored']
        self.assertAlmostEqual(ja['recall_end_to_end_ceiling'], 0.931)
        self.assertEqual(ja['ceiling_count'], 7)
        self.assertEqual(ja['recoverable_fn_count'], 51)
        md = render_md(m)
        self.assertIn('召回(端到端天花板)', md)

    def test_claim_level_recovery_rail_propagates(self):
        jm = {
            'tp_clean': 43,
            'judge_valid_cases': 101,
            'judge_valid_dynamic': 57,
            'fn_judge_valid': 58,
            'fp_from_judge_invalid': 15,
            'tn_invalid': 60,
            'precision': 43 / 58,
            'precision_ci': [0.6, 0.8],
            'recall_end_to_end_ci': [0.3, 0.5],
            'recall_evaluable_ci': [0.6, 0.9],
            'claim_total': 363,
            'claim_dynamic': 173,
            'claim_reproduced': 87,
            'claim_dynamic_rate': 173 / 363,
            'claim_reproduced_rate': 87 / 363,
            'mixed_non_dynamic_cases': 34,
        }
        m = analyze(self._pos(), [], judge_metrics=jm)
        ja = m['metrics']['judge_anchored']
        self.assertEqual(ja['claim_total'], 363)
        self.assertEqual(ja['claim_dynamic'], 173)
        self.assertEqual(ja['claim_reproduced'], 87)
        self.assertAlmostEqual(ja['claim_reproduced_rate'], 87 / 363)
        self.assertEqual(ja['mixed_non_dynamic_cases'], 34)
        md = render_md(m)
        self.assertIn('claim级回收(复现/claim)', md)

    def test_f1_no_longer_uses_constructed_fp_zero(self):
        # 构造负样本 FP=0 不能把 F1 抬到 1；判例锚定 precision 必须主导 F1。
        jm = {
            'tp_clean': 43,
            'judge_valid_cases': 101,
            'judge_valid_dynamic': 57,
            'fn_judge_valid': 58,
            'fp_from_judge_invalid': 15,
            'tn_invalid': 60,
            'precision': 43 / 58,
            'precision_ci': [0.6, 0.8],
            'recall_end_to_end_ci': [0.3, 0.5],
            'recall_evaluable_ci': [0.6, 0.9],
        }
        m = analyze(self._pos(), [], judge_metrics=jm)
        ja = m['metrics']['judge_anchored']
        self.assertLess(ja['f1_end_to_end'], 0.6)
        self.assertLess(ja['f1_evaluable'], 0.8)
        self.assertGreater(m['metrics']['precision_constructed_negatives'], 0.99)
