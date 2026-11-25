import unittest

from evaluation.metrics.current_denominator import (
    classify_claim, claim_allowed, consistency_effect_confirmed,
    metric_eligible_cases)


def current_fingerprint():
    from lib import (artifact_fingerprint, execution_gate, mainline_protocol,
                     observable_ir, observable_recipes)
    return {
        'schema_version': 'stage3-artifact-fingerprint/1',
        'mainline_protocol': mainline_protocol.current(),
        'protocol_versions': {
            'execution_gate': execution_gate.SCHEMA_VERSION,
            'observable_ir': observable_ir.SCHEMA_VERSION,
            'observable_recipes': observable_recipes.SCHEMA_VERSION,
        },
    }


class CurrentDenominatorTest(unittest.TestCase):
    def test_empty_frozen_population_allows_first_attempt(self):
        population = {'case': frozenset(), 'frozen': frozenset({'a'})}
        self.assertTrue(claim_allowed(population, 'case', 'new_claim'))
        self.assertTrue(claim_allowed(population, 'missing', 'anything'))
        self.assertTrue(claim_allowed(population, 'frozen', 'a'))
        self.assertFalse(claim_allowed(population, 'frozen', 'b'))

    def test_metric_ineligible_claims_do_not_inflate_case_coverage(self):
        eligible = [
            {'case': 'pos-a', 'label': 'positive',
             'metric_eligibility': {'consistency': True,
                                    'negative_witness_eligible': True}},
            {'case': 'neg-a', 'label': 'negative',
             'metric_eligibility': {'consistency': True,
                                    'negative_witness_eligible': True}},
            {'case': 'neg-b', 'label': 'negative',
             'metric_eligibility': {'consistency': False,
                                    'negative_witness_eligible': True}},
            {'case': 'neg-b', 'label': 'negative',
             'metric_eligibility': {'consistency': True,
                                    'negative_witness_eligible': True}},
            {'case': 'neg-c', 'label': 'negative',
             'metric_eligibility': {'consistency': False,
                                    'negative_witness_eligible': False}},
        ]
        cases = metric_eligible_cases(eligible)
        self.assertEqual(cases['positive'], {'pos-a'})
        self.assertEqual(cases['negative'], {'neg-a', 'neg-b'})

    def test_negative_without_witness_stays_unresolved_in_coverage(self):
        eligible = [
            {'case': 'neg-a', 'label': 'negative',
             'metric_eligibility': {'consistency': True,
                                    'negative_witness_eligible': False}},
        ]
        self.assertEqual(metric_eligible_cases(eligible)['negative'], set())

    def test_effect_observed_without_invariant_violation_is_effect_confirmed(self):
        summary = {
            'consistency_verdict': 'effect_observed_invariant_holds',
            'code_query_results': {
                'P_and_T': 'sat', 'P_and_T_and_not_I': 'unsat',
                'P_and_T_and_V': 'sat', 'P_and_T_and_not_V': 'unknown',
            },
            'forge': {'effect': {'status': 'Success'}},
        }
        self.assertTrue(consistency_effect_confirmed(summary))
        decision = classify_claim({
            'consistency_verdict': summary['consistency_verdict'],
            'summary': {**summary, 'artifact_fingerprint': current_fingerprint()},
            'label': 'negative',
        })
        self.assertEqual(decision['bucket'], 'eligible_current')
        self.assertTrue(decision['metric_eligibility']['effect_confirmed'])

    def test_effect_confirmed_negative_is_fp_not_tn_coverage(self):
        eligible = [
            {'case': 'neg-fp', 'label': 'negative',
             'metric_eligibility': {'consistency': True,
                                    'negative_witness_eligible': False,
                                    'effect_confirmed': True}},
            {'case': 'neg-conflict', 'label': 'negative',
             'metric_eligibility': {'consistency': True,
                                    'negative_witness_eligible': True,
                                    'effect_confirmed': True}},
            {'case': 'neg-tn', 'label': 'negative',
             'metric_eligibility': {'consistency': True,
                                    'negative_witness_eligible': True,
                                    'effect_confirmed': False}},
        ]
        self.assertEqual(metric_eligible_cases(eligible)['negative'],
                         {'neg-fp', 'neg-conflict', 'neg-tn'})

    def test_impact_gate_does_not_block_consistency_evidence(self):
        summary = {
            'artifact_fingerprint': current_fingerprint(),
            'consistency_verdict': 'effect_observed_invariant_holds',
            'code_query_results': {
                'P_and_T': 'sat', 'P_and_T_and_not_I': 'unsat',
                'P_and_T_and_V': 'sat', 'P_and_T_and_not_V': 'unknown',
            },
            'forge': {'effect': {'status': 'Success'}},
            'execution_gate': {'metric_eligibility': {
                'consistency': False, 'vulnerability': False,
                'exclusion_reason': 'TRUSTED_JUDGE_INVALID',
                'consistency_exclusion_reason': 'IMPACT_DUST_OR_DONATION_DOS',
            }},
        }
        decision = classify_claim({
            'consistency_verdict': summary['consistency_verdict'],
            'summary': summary, 'label': 'negative'})
        self.assertEqual(decision['bucket'], 'eligible_current')
        eligibility = decision['metric_eligibility']
        self.assertTrue(eligibility['consistency'])
        self.assertTrue(eligibility['effect_confirmed'])
        self.assertEqual(eligibility['consistency_override'],
                         'IMPACT_DUST_OR_DONATION_DOS')
        self.assertFalse(eligibility['vulnerability'])

    def test_stale_run_is_excluded_not_unresolved(self):
        row = {'consistency_verdict': 'violation_reproduced',
               'summary': {'consistency_verdict': 'violation_reproduced'}}
        decision = classify_claim(row)
        self.assertEqual(decision['bucket'], 'excluded_retry')
        self.assertEqual(decision['reason'], 'stale_or_missing_fingerprint')

    def test_old_protocol_version_is_excluded(self):
        row = {'consistency_verdict': 'violation_reproduced',
               'summary': {'artifact_fingerprint': {
                   **current_fingerprint(),
                   'protocol_versions': {
                       **current_fingerprint()['protocol_versions'],
                       'observable_ir': 'stage3-observable-ir/0',
                   }}}}
        decision = classify_claim(row)
        self.assertEqual(decision['bucket'], 'excluded_retry')
        self.assertTrue(decision['reason'].startswith(
            'stale_protocol_version:'))

    def test_changed_mainline_code_is_excluded(self):
        fingerprint = current_fingerprint()
        fingerprint['mainline_protocol'] = {
            **fingerprint['mainline_protocol'],
            'sha256': '0' * 64,
        }
        row = {'consistency_verdict': 'violation_reproduced',
               'summary': {'artifact_fingerprint': fingerprint}}
        decision = classify_claim(row)
        self.assertEqual(decision['bucket'], 'excluded_retry')
        self.assertEqual(decision['reason'], 'stale_mainline_protocol')

    def test_fingerprinted_binding_error_is_unresolved_not_tn(self):
        row = {'consistency_verdict': 'binding_error',
               'summary': {'artifact_fingerprint': current_fingerprint()}}
        decision = classify_claim(row)
        self.assertEqual(decision['bucket'], 'unresolved')

    def test_stage2_restatement_is_unresolved_not_tn(self):
        row = {'consistency_verdict': 'stage2_restatement_required',
               'summary': {'artifact_fingerprint': current_fingerprint()}}
        decision = classify_claim(row)
        self.assertEqual(decision['bucket'], 'unresolved')

    def test_fingerprinted_terminal_result_is_current(self):
        row = {'consistency_verdict': 'violation_not_reproduced',
               'summary': {'artifact_fingerprint': current_fingerprint()}}
        decision = classify_claim(row)
        self.assertEqual(decision['bucket'], 'eligible_current')

    def test_consistency_only_claim_is_not_vulnerability_eligible(self):
        row = {'consistency_verdict': 'violation_reproduced',
               'summary': {'artifact_fingerprint': current_fingerprint(),
                   'execution_gate': {'metric_eligibility': {
                       'consistency': True,
                       'vulnerability': False,
                       'exclusion_reason': 'TRUSTED_IMPACT_INSUFFICIENT',
                   }}}}
        decision = classify_claim(row)
        self.assertEqual(decision['bucket'], 'eligible_current')
        self.assertTrue(decision['metric_eligibility']['consistency'])
        self.assertFalse(decision['metric_eligibility']['vulnerability'])
        self.assertTrue(decision['metric_eligibility']['consistency_only'])


if __name__ == '__main__':
    unittest.main()
