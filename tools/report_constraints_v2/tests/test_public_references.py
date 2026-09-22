"""Public-spec review controls are synthetic tests, not extraction accuracy."""
import copy
import importlib.util
from pathlib import Path
import unittest

HERE = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('public_reference_checker', HERE / 'review_samples/check_reference.py')
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


class PublicReferenceTests(unittest.TestCase):
    def setUp(self):
        self.cases = {case['id']: case for case in checker.cases()}

    def candidate(self, ident):
        return copy.deepcopy({key: self.cases[ident][key] for key in ('preconditions', 'safety')})

    def test_three_references_self_equivalent(self):
        self.assertEqual(len(self.cases), 3)
        for ident, case in self.cases.items():
            self.assertTrue(checker.compare(case, self.candidate(ident))['both_equivalent'])
            self.assertIsNone(case['effects'])

    def test_equivalent_reversed_operator(self):
        candidate = self.candidate('single_balance')
        candidate['safety'] = {'op': 'ge', 'args': [{'var': 'supply'}, {'var': 'balance'}]}
        self.assertTrue(checker.compare(self.cases['single_balance'], candidate)['both_equivalent'])

    def test_strict_comparison_detected(self):
        candidate = self.candidate('single_balance'); candidate['safety']['op'] = 'lt'
        result = checker.compare(self.cases['single_balance'], candidate)
        self.assertFalse(result['both_equivalent'])
        self.assertIsNotNone(result['checks']['safety_under_reference_preconditions']['difference_witness'])

    def test_inverted_safety_detected(self):
        candidate = self.candidate('single_balance'); candidate['safety']['op'] = 'ge'
        self.assertFalse(checker.compare(self.cases['single_balance'], candidate)['both_equivalent'])

    def test_vacuous_true_detected(self):
        candidate = self.candidate('single_balance'); candidate['safety'] = {'const': True}
        self.assertFalse(checker.compare(self.cases['single_balance'], candidate)['both_equivalent'])

    def test_missing_distinct_accounts_detected(self):
        candidate = self.candidate('two_balances'); candidate['preconditions'] = {'const': True}
        self.assertEqual(checker.compare(self.cases['two_balances'], candidate)['checks']['preconditions']['comparison'], 'different')

    def test_missing_initial_condition_detected(self):
        candidate = self.candidate('mint_postcondition'); candidate['preconditions'] = {'const': True}
        self.assertFalse(checker.compare(self.cases['mint_postcondition'], candidate)['both_equivalent'])

    def test_wrong_checkpoint_detected(self):
        candidate = self.candidate('mint_postcondition')
        candidate['safety']['args'][0] = {'var': 'supply_before'}
        self.assertFalse(checker.compare(self.cases['mint_postcondition'], candidate)['both_equivalent'])

    def test_unknown_symbol_rejected(self):
        candidate = self.candidate('single_balance'); candidate['safety']['args'][0] = {'var': 'unknown'}
        with self.assertRaises(KeyError): checker.compare(self.cases['single_balance'], candidate)

    def test_non_boolean_and_extra_fields_rejected(self):
        candidate = self.candidate('single_balance'); candidate['safety'] = {'const': 1}
        with self.assertRaises(ValueError): checker.compare(self.cases['single_balance'], candidate)
        candidate = self.candidate('single_balance'); candidate['effects'] = {'const': True}
        with self.assertRaises(ValueError): checker.compare(self.cases['single_balance'], candidate)


if __name__ == '__main__': unittest.main()
