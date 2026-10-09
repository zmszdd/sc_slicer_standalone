"""relationship_review lives in report_only after the 2026-09-21 merge."""
import copy
import json
from pathlib import Path
import unittest

from tests.test_report_only import fixture, TEXT
from lib.report_only import relationship_review


class RelationshipTests(unittest.TestCase):
    def test_effect_same_as_safety_warns(self):
        claim = fixture()
        claim['properties']['effects'] = copy.deepcopy(claim['properties']['safety'])
        result = relationship_review(claim, TEXT, require_direct_counterexample=True)
        self.assertEqual(result['review_status'], 'needs_review')
        self.assertEqual(result['queries']['P_and_V_and_not_I'], 'unsat')

    def test_bad_effect_can_violate_intended_safety(self):
        claim = fixture()
        claim['properties']['preconditions']['expression'] = {'op': 'gt', 'args': [{'var': 'paid'}, {'var': 'quoted'}]}
        claim['properties']['effects']['expression'] = {'var': 'fee_revert'}
        result = relationship_review(claim, TEXT, require_direct_counterexample=True)
        self.assertEqual(result['review_status'], 'no_relationship_warning')
        self.assertEqual(result['queries']['P_and_V_and_not_I'], 'sat')
        self.assertEqual(result['queries']['P_and_V_and_I'], 'unsat')
        self.assertEqual(result['direct_counterexample_status'], 'passed')
        self.assertFalse(result['eligible_for_stage3'])

    def test_effect_that_can_coexist_with_safety_fails_direct_relation(self):
        claim = fixture()
        claim['properties']['preconditions']['expression'] = {
            'op': 'gt', 'args': [{'var': 'paid'}, {'var': 'quoted'}]}
        claim['properties']['effects']['expression'] = {'const': True}
        result = relationship_review(claim, TEXT, require_direct_counterexample=True)
        self.assertEqual(result['queries']['P_and_V_and_I'], 'sat')
        self.assertEqual(result['queries']['P_and_V_and_not_I'], 'sat')
        self.assertEqual(result['direct_counterexample_status'], 'failed')
        self.assertIn('direct V/I counterexample relation failed', ' '.join(result['warnings']))

    def test_missing_effect_not_guessed(self):
        result = relationship_review(fixture(), TEXT)
        self.assertEqual(result['review_status'], 'incomplete_check')

    def test_infeasible_effect_warns(self):
        claim = fixture(); claim['properties']['effects']['expression'] = {'const': False}
        self.assertEqual(relationship_review(claim, TEXT)['review_status'], 'needs_review')

    def test_saved_model_inversion_is_detected(self):
        directory = Path(__file__).resolve().parents[1] / 'results/report_only/brix_fee_model_01'
        if not (directory / 'model-claim.json').exists(): self.skipTest('saved model result absent')
        claim = json.loads((directory / 'model-claim.json').read_text())
        text = (directory / 'extraction-input.txt').read_text()
        self.assertEqual(relationship_review(claim, text)['review_status'], 'needs_review')


if __name__ == '__main__': unittest.main()
