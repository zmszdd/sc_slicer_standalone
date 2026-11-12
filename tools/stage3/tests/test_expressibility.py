import unittest
from pathlib import Path

from lib.expressibility import (
    BINDING_ERROR, CROSS_CONTRACT, EXPRESSIBLE, UNOBSERVABLE,
    classify, classify_lint)

CASES = Path(__file__).resolve().parents[1] / 'cases'


def _problem(where, message, severity='error'):
    return {'where': where, 'message': message, 'severity': severity}


class ClassifyLintTest(unittest.TestCase):
    def test_empty_problems_is_expressible(self):
        result = classify_lint({'problems': []})
        self.assertEqual(result['expressibility'], EXPRESSIBLE)
        self.assertTrue(result['dynamically_expressible'])
        self.assertFalse(result['reference_patch_required'])

    def test_cross_contract_dominates(self):
        result = classify_lint({'problems': [
            _problem('bindings.a.solidity_expr',
                     "identifier 'x' not declared in src"),
            _problem('bindings.b.solidity_expr',
                     "cross-contract reference: '_validateSignature' is a "
                     "function declared outside 'PoCCore' and is not visible"),
        ]})
        self.assertEqual(result['expressibility'], CROSS_CONTRACT)
        self.assertTrue(result['reference_patch_required'])
        self.assertEqual(result['cross_contract_symbols'], ['b'])

    def test_cross_contract_on_non_safety_is_rebindable(self):
        result = classify_lint({'problems': [
            _problem('bindings.p.solidity_expr',
                     "cross-contract reference: '_validateSignature' is a "
                     "function declared outside 'PoCCore' and is not visible"),
            _problem('bindings.i.solidity_expr',
                     "identifier 'x' not declared in src"),
        ]}, safety_symbols={'i'})
        # P-side cross-contract is a rebindable binding error, not a ceiling.
        self.assertEqual(result['expressibility'], UNOBSERVABLE)
        self.assertFalse(result['reference_patch_required'])
        self.assertEqual(result['cross_contract_symbols'], [])

    def test_unobservable_unknown_identifier(self):
        result = classify_lint({'problems': [
            _problem('bindings.a.solidity_expr',
                     "identifier 'UNBOUND' not declared in src"),
        ]})
        self.assertEqual(result['expressibility'], UNOBSERVABLE)
        self.assertFalse(result['reference_patch_required'])
        self.assertEqual(result['unobservable_symbols'], ['a'])

    def test_binding_error_only(self):
        result = classify_lint({'problems': [
            _problem('bindings.a.solidity_expr', 'empty solidity_expr'),
        ]})
        self.assertEqual(result['expressibility'], BINDING_ERROR)
        self.assertFalse(result['dynamically_expressible'])


class ClassifyRealCaseTest(unittest.TestCase):
    def test_intuition_cross_contract_is_not_expressible(self):
        case = CASES / ('Intuition_2VUsxVJwReb__6YNDfbQYkTa__KcTHtNrsMFs')
        binding_path = case / 'bindings' / \
            'impact_claim_dos_via_expired_window_8ceee315_ddfa6e3d.json'
        if not binding_path.is_file():
            self.skipTest('Intuition case binding not present')
        import json
        binding = json.loads(binding_path.read_text())
        result = classify(binding, case / 'src', test_dir=case / 'test',
                          strict=True)
        self.assertEqual(result['expressibility'], CROSS_CONTRACT)
        self.assertTrue(result['cross_contract_symbols'])


if __name__ == '__main__':
    unittest.main()
