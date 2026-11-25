import unittest
from unittest import mock

from evaluation.metrics.run_dev_24 import classify, evaluate_gate, summarize


class Dev24RunnerTest(unittest.TestCase):
    def test_binding_error_is_unresolved_not_tn_or_tp(self):
        positive = classify(
            {'label': 'positive'},
            {'claims': [{'consistency_verdict': 'binding_error'}]})
        self.assertEqual(positive['outcome'], 'fn_unresolved')
        negative = classify(
            {'label': 'negative'},
            {'claims': [{'consistency_verdict': 'binding_error'}]})
        self.assertEqual(negative['outcome'], 'unresolved')
        self.assertTrue(negative['unresolved'])

    def test_partial_binding_on_negative_is_not_tn(self):
        negative = classify(
            {'label': 'negative'},
            {'claims': [{'consistency_verdict': 'partial_binding'}]})
        self.assertEqual(negative['outcome'], 'unresolved')

    def test_stage2_gate_verdicts_are_unresolved_for_both_labels(self):
        for verdict in ('stage2_restatement_required', 'stage2_review_required',
                        'stage2_repair_required',
                        'stage2_reference_patch_candidate'):
            with self.subTest(verdict=verdict):
                positive = classify(
                    {'label': 'positive'},
                    {'claims': [{'consistency_verdict': verdict}]})
                negative = classify(
                    {'label': 'negative'},
                    {'claims': [{'consistency_verdict': verdict}]})
                self.assertEqual(positive['outcome'], 'fn_unresolved')
                self.assertTrue(negative['unresolved'])
                self.assertEqual(negative['outcome'], 'unresolved')

    def test_impact_insufficient_negative_is_not_tn(self):
        negative = classify(
            {'label': 'negative'},
            {'claims': [{'consistency_verdict': 'impact_insufficient'}]})
        self.assertEqual(negative['outcome'], 'unresolved')
        self.assertTrue(negative['unresolved'])

    def test_effect_not_witnessed_is_not_tn(self):
        negative = classify(
            {'label': 'negative'},
            {'claims': [{'consistency_verdict': 'effect_not_witnessed'}]})
        self.assertEqual(negative['outcome'], 'unresolved')

    def test_empty_negative_claims_fail_closed(self):
        negative = classify({'label': 'negative'}, {'claims': []})
        self.assertEqual(negative['outcome'], 'unresolved')

    def test_explicit_no_violation_is_tn(self):
        with mock.patch(
                'evaluation.metrics.run_dev_24._load_run_summary',
                return_value={'execution_gate': {
                    'metric_eligibility': {'negative': True},
                    'negative_witness': {'eligible': True}}}):
            negative = classify(
                {'label': 'negative'},
                {'claims': [{
                    'claim_id': 'c', 'run_id': 'r',
                    'consistency_verdict': 'violation_not_reproduced'}]})
        self.assertEqual(negative['outcome'], 'tn')

    def test_explicit_no_violation_without_witness_is_unresolved(self):
        negative = classify(
            {'label': 'negative'},
            {'claims': [{'consistency_verdict': 'violation_not_reproduced'}]})
        self.assertEqual(negative['outcome'], 'unresolved')
        self.assertFalse(negative['negative_witness'])

    def test_impact_ineligible_reproduction_is_consistency_fp(self):
        summary = {'claims': [{
            'claim_id': 'c', 'run_id': 'r',
            'consistency_verdict': 'violation_reproduced'}]}
        run_summary = {
            'execution_gate': {'metric_eligibility': {
                'consistency': True, 'vulnerability': False,
                'exclusion_reason': 'TRUSTED_IMPACT_INSUFFICIENT'}}}
        with mock.patch(
                'evaluation.metrics.run_dev_24._load_run_summary',
                return_value=run_summary):
            negative = classify({'label': 'negative'}, summary)
        self.assertEqual(negative['outcome'], 'consistency_fp')
        self.assertFalse(negative['unresolved'])

    def test_summary_keeps_unresolved_visible(self):
        results = [
            {'label': 'positive', 'classification': {'outcome': 'tp'}},
            {'label': 'positive', 'classification': {'outcome': 'fn_unresolved'}},
            {'label': 'negative', 'classification': {'outcome': 'unresolved'}},
            {'label': 'negative', 'classification': {'outcome': 'tn'}},
        ]
        summary = summarize(results)
        self.assertEqual(summary['tp'], 1)
        self.assertEqual(summary['fn_unresolved'], 1)
        self.assertEqual(summary['fp'], 0)
        self.assertEqual(summary['tn'], 1)
        self.assertEqual(summary['negative_unresolved'], 1)
        self.assertEqual(summary['negative_other_unresolved'], 1)
        self.assertEqual(summary['positive_tp_rate'], 0.5)

    def test_gate_checks_baseline_not_absolute_sample_rate(self):
        summary = {'fp': 0, 'negative_unresolved': 0, 'tp': 1}
        results = [{'status': 'done'}]
        gate = evaluate_gate(summary, results, baseline_tp=1)
        self.assertTrue(all(gate.values()))

    def test_negative_unresolved_blocks_gate(self):
        summary = {'fp': 0, 'negative_unresolved': 1, 'tp': 1}
        gate = evaluate_gate(summary, [{'status': 'done'}], baseline_tp=1)
        self.assertFalse(gate['negative_all_resolved'])


if __name__ == '__main__':
    unittest.main()
