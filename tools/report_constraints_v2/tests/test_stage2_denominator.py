"""Complete P/I/V eligibility is the only rule-success denominator."""
import unittest

from cli.semantic_pipeline import stage2_assessment
from lib.impact_cards import (applicability_by_impact,
                              direct_v_infeasible_intent_ids,
                              formalizable_intent_ids,
                              formalization_scope,
                              not_applicable_impacts_for,
                              validate_applicability)


class Stage2DenominatorTests(unittest.TestCase):
    def test_incomplete_impacts_are_excluded_but_failed_eligible_items_remain(self):
        bundle = {
            'acceptance_status': 'needs_review',
            'report_impact_coverage': [
                {'impact_id': 'eligible_pass', 'status': 'formalized'},
                {'impact_id': 'eligible_failed', 'status': 'unformalized',
                 'reason': 'formula validation failed'},
                {'impact_id': 'missing_intent', 'status': 'unformalized',
                 'reason': 'no applicable explicit intent'},
            ],
        }

        assessment = stage2_assessment(
            bundle=bundle,
            eligible_impact_ids=['eligible_pass', 'eligible_failed'])
        result = assessment['rule_formalization']

        self.assertEqual(result['eligible_complete_piv_count'], 2)
        self.assertEqual(result['formalized_complete_piv_count'], 1)
        self.assertEqual(result['formalization_rate'], 0.5)
        self.assertEqual(result['impact_count'], 2)
        self.assertEqual(result['formalized_impact_count'], 1)
        self.assertEqual([row['impact_id'] for row in result['pending_impacts']],
                         ['eligible_failed'])

    def test_empty_eligible_denominator_is_not_applicable(self):
        assessment = stage2_assessment(
            bundle={'acceptance_status': 'needs_review',
                    'report_impact_coverage': [
                        {'impact_id': 'missing_intent', 'status': 'unformalized'}]},
            eligible_impact_ids=[])
        result = assessment['rule_formalization']

        self.assertEqual(result['status'], 'not_applicable')
        self.assertEqual(result['eligible_complete_piv_count'], 0)
        self.assertIsNone(result['formalization_rate'])
        self.assertEqual(result['pending_impacts'], [])

    def test_gate_infeasible_pairs_stay_in_denominator_as_unformalized(self):
        bundle = {
            'acceptance_status': 'needs_review',
            'report_impact_coverage': [
                {'impact_id': 'eligible_failed', 'status': 'unformalized',
                 'reason': 'compiled P/I/V gate does not admit a direct '
                           'violation witness'},
            ],
        }
        records = [
            {'impact_id': 'eligible_failed', 'intent_id': 'intent_zero_controller',
             'status': 'unformalized',
             'failure_family': 'direct_relation_infeasible',
             'reason': 'compiled P/I/V gate does not admit a direct violation '
                       'witness',
             'attempts': [{'rule_generated': True}]},
        ]

        result = stage2_assessment(
            bundle=bundle, eligible_impact_ids=['eligible_failed'],
            impact_formalization_records=records,
            gate_direct_denominator=False)['rule_formalization']

        self.assertEqual(result['eligible_complete_piv_count'], 1)
        self.assertEqual(result['formalized_complete_piv_count'], 0)
        self.assertEqual(result['formalization_rate'], 0.0)
        self.assertEqual([row['impact_id'] for row in result['pending_impacts']],
                         ['eligible_failed'])
        self.assertEqual(result['failure_counts_by_stage'],
                         {'direct_relation_infeasible': 1})
        self.assertEqual([row['intent_id']
                          for row in result['direct_relation_infeasible']],
                         ['intent_zero_controller'])
        self.assertNotIn('direct_relation_not_applicable', result)


if __name__ == '__main__':
    unittest.main()


class DirectVPreScreenTests(unittest.TestCase):
    def _elements(self):
        return {'statements': [
            {'id': 'imp_a', 'kind': 'impact', 'text': 'drain all funds',
             'modality': 'actual', 'evidence_ids': ['e1']},
            {'id': 'imp_b', 'kind': 'impact', 'text': 'init re-callable',
             'modality': 'actual', 'evidence_ids': ['e2']},
            {'id': 'p1', 'kind': 'precondition', 'text': 'factory deploys wallet',
             'evidence_ids': ['e1']},
            {'id': 'i1', 'kind': 'security_intent', 'modality': 'asserted',
             'text': 'init only once', 'evidence_ids': ['e2']},
            {'id': 'i2', 'kind': 'security_intent', 'modality': 'asserted',
             'text': 'funds protected', 'evidence_ids': ['e1']},
        ]}

    def test_v2_applicability_and_scope(self):
        raw = {'schema_version': 'stage2-impact-applicability/2', 'impacts': [
            {'impact_id': 'imp_a', 'status': 'selected',
             'precondition_ids': ['p1'], 'intent_ids': ['i2'],
             'direct_v_feasibility': {'i2': False},
             'reason': 'downstream consequence only'},
            {'impact_id': 'imp_b', 'status': 'selected',
             'precondition_ids': ['p1'], 'intent_ids': ['i1'],
             'direct_v_feasibility': {'i1': True},
             'reason': 'direct falsifier stated'},
        ]}
        validated = validate_applicability(raw, self._elements())
        self.assertEqual(validated['schema_version'],
                         'stage2-impact-applicability/2')
        by_impact = applicability_by_impact(validated)
        self.assertEqual(formalizable_intent_ids(by_impact['imp_a']), [])
        self.assertEqual(direct_v_infeasible_intent_ids(by_impact['imp_a']), ['i2'])
        self.assertEqual(formalization_scope(validated), {'imp_b': ['i1']})
        self.assertEqual([row['impact_id'] for row in
                          not_applicable_impacts_for(validated)], ['imp_a'])

    def test_stage2_assessment_lists_direct_v_infeasible_separately(self):
        bundle = {'acceptance_status': 'needs_review', 'report_impact_coverage': [
            {'impact_id': 'imp_b', 'status': 'formalized', 'claim_ids': ['c']}]}
        records = [
            {'impact_id': 'imp_a', 'intent_id': 'i2', 'status': 'unformalized',
             'failure_family': 'direct_relation_infeasible',
             'prescreen': 'direct_v_infeasible', 'reason': 'no direct V',
             'attempts': []},
            {'impact_id': 'imp_b', 'intent_id': 'i1',
             'status': 'formalized_candidate',
             'fidelity_status': 'passed', 'attempts': []},
        ]
        assessment = stage2_assessment(
            bundle=bundle, eligible_impact_ids=['imp_b'],
            impact_formalization_records=records,
            not_applicable_impacts=[{'impact_id': 'imp_a',
                                     'infeasible_intent_ids': ['i2'],
                                     'reason': 'no direct V'}],
            formalization_scope={'imp_b': ['i1']})
        rule = assessment['rule_formalization']
        self.assertEqual(rule['eligible_complete_piv_count'], 1)
        self.assertEqual(rule['formalized_complete_piv_count'], 1)
        self.assertEqual(rule['direct_relation_not_applicable'][0]['impact_id'],
                         'imp_a')
        self.assertEqual(rule['direct_relation_infeasible'][0]['intent_id'], 'i2')
        self.assertNotIn('direct_relation_infeasible',
                         rule.get('failure_counts_by_stage', {}))
