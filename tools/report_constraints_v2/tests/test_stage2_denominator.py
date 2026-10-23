"""Complete P/I/V eligibility is the only rule-success denominator."""
import unittest

from cli.semantic_pipeline import stage2_assessment


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


if __name__ == '__main__':
    unittest.main()
