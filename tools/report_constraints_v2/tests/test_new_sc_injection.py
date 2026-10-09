"""Unit tests for the new-SC translator (evaluation/new_sc_injection_02).

The translator (translate / collect_vars / check_binding_coverage) is pure
and directly determines what the injected guard computes, so every QEXPR
shape it must handle is pinned here. Both bugs fixed on 2026-10-09 (const
leaf nodes without 'args'/'op', and n-ary boolean ops) escaped notice
because Ekubo, the only regression case at the time, has no const nodes and
only 2-ary ops -- these tests keep that from recurring.
"""

import sys
import unittest
from pathlib import Path

NEW_SC_DIR = (Path(__file__).resolve().parents[1]
              / 'evaluation/new_sc_injection_02')
sys.path.insert(0, str(NEW_SC_DIR))

import new_sc  # noqa: E402


SYMBOLS = {
    'fot_deposit_received': {'phase': 'post', 'type': 'uint256',
                             'expr': '(fotDepositReceivedWei / 1e18)'},
    'standard_deposit_received': {'phase': 'post', 'type': 'uint256',
                                  'expr': '(standardDepositReceivedWei / 1e18)'},
    'physical_balance': {'phase': 'post', 'type': 'uint256',
                         'expr': '(physicalBalanceWei / 1e18)'},
    'total_liabilities': {'phase': 'post', 'type': 'uint256',
                          'expr': '(totalLiabilitiesWei / 1e18)'},
}

# The Merkl core_claim P: a 4-ary and over eq comparisons with const nodes.
MERKL_P = {
    'op': 'and',
    'args': [
        {'op': 'eq', 'args': [{'var': 'fot_deposit_received'}, {'const': 990}]},
        {'op': 'eq', 'args': [{'var': 'standard_deposit_received'}, {'const': 1000}]},
        {'op': 'eq', 'args': [{'var': 'physical_balance'}, {'const': 1990}]},
        {'op': 'eq', 'args': [{'var': 'total_liabilities'}, {'const': 2000}]},
    ],
}


def claim_with(*expressions):
    kinds = ('preconditions', 'safety', 'effects')
    return {'properties': {kind: {'expression': expr}
                           for kind, expr in zip(kinds, expressions)}}


class TranslateTests(unittest.TestCase):

    def test_bool_literals(self):
        self.assertEqual(new_sc.translate(True, SYMBOLS), 'true')
        self.assertEqual(new_sc.translate(False, SYMBOLS), 'false')

    def test_bare_int_literals(self):
        self.assertEqual(new_sc.translate(990, SYMBOLS), 'uint256(990)')
        self.assertEqual(new_sc.translate(-5, SYMBOLS), 'int256(-5)')

    def test_const_node_literals(self):
        # {"const": N} nodes are the compiled form; both signs must take the
        # same path as bare ints (regression: KeyError 'op' / 'args').
        self.assertEqual(new_sc.translate({'const': 990}, SYMBOLS), 'uint256(990)')
        self.assertEqual(new_sc.translate({'const': -5}, SYMBOLS), 'int256(-5)')

    def test_var_node_wraps_bound_expression(self):
        self.assertEqual(new_sc.translate({'var': 'physical_balance'}, SYMBOLS),
                         '((physicalBalanceWei / 1e18))')

    def test_not_and_implies(self):
        self.assertEqual(new_sc.translate({'op': 'not', 'args': [True]}, SYMBOLS),
                         '(!true)')
        self.assertEqual(
            new_sc.translate({'op': 'implies', 'args': [False, True]}, SYMBOLS),
            '((!false) || true)')

    def test_binary_comparisons_and_arithmetic(self):
        for op, sol in (('eq', '=='), ('ne', '!='), ('lt', '<'), ('le', '<='),
                        ('gt', '>'), ('ge', '>='), ('add', '+'), ('sub', '-'),
                        ('mul', '*')):
            node = {'op': op, 'args': [{'const': 2}, {'const': 3}]}
            self.assertEqual(new_sc.translate(node, SYMBOLS),
                             f'(uint256(2) {sol} uint256(3))')

    def test_n_ary_and_folds_left(self):
        # Regression: 4-ary and previously crashed the 2-value unpack.
        result = new_sc.translate(MERKL_P, SYMBOLS)
        self.assertEqual(result.count('&&'), 3)
        self.assertIn('fotDepositReceivedWei', result)
        self.assertIn('uint256(990)', result)

    def test_n_ary_add_folds_left(self):
        node = {'op': 'add', 'args': [{'const': 1}, {'const': 2}, {'const': 3}]}
        self.assertEqual(new_sc.translate(node, SYMBOLS),
                         '((uint256(1) + uint256(2)) + uint256(3))')

    def test_unsupported_op_raises(self):
        with self.assertRaises(ValueError):
            new_sc.translate({'op': 'div', 'args': [{'const': 1}, {'const': 2}]},
                             SYMBOLS)


class CollectVarsTests(unittest.TestCase):

    def test_const_leaves_do_not_crash(self):
        acc = set()
        new_sc.collect_vars(MERKL_P, acc)
        self.assertEqual(acc, set(SYMBOLS))

    def test_nested_connectives(self):
        node = {'op': 'implies',
                'args': [{'op': 'and', 'args': [{'var': 'physical_balance'},
                                                {'const': 1990}]},
                         {'op': 'not', 'args': [{'var': 'total_liabilities'}]}]}
        acc = set()
        new_sc.collect_vars(node, acc)
        self.assertEqual(acc, {'physical_balance', 'total_liabilities'})


class BindingCoverageTests(unittest.TestCase):

    PLAN = {'symbols': sorted(SYMBOLS)}

    def test_exact_coverage_passes(self):
        new_sc.check_binding_coverage(SYMBOLS, claim_with(MERKL_P, True, False),
                                      self.PLAN)

    def test_missing_binding_fails(self):
        symbols = dict(SYMBOLS)
        del symbols['total_liabilities']
        with self.assertRaises(new_sc.CaseError):
            new_sc.check_binding_coverage(symbols, claim_with(MERKL_P, True, False),
                                          self.PLAN)

    def test_extra_binding_fails(self):
        symbols = dict(SYMBOLS, extra_symbol={'phase': 'post', 'type': 'uint256',
                                              'expr': '0'})
        with self.assertRaises(new_sc.CaseError):
            new_sc.check_binding_coverage(symbols, claim_with(MERKL_P, True, False),
                                          self.PLAN)

    def test_symbol_absent_from_plan_fails(self):
        plan = {'symbols': sorted(SYMBOLS)[:-1]}
        with self.assertRaises(new_sc.CaseError):
            new_sc.check_binding_coverage(SYMBOLS, claim_with(MERKL_P, True, False),
                                          plan)


class AdjudicateTests(unittest.TestCase):
    """The pre-registered four-branch table, pinned as executable spec."""

    def test_table(self):
        cases = [((True, False, True), 'violation_reproduced'),
                 ((True, True, True), 'i_too_weak'),
                 ((False, True, False), 'precondition_mismatch'),
                 ((False, False, False), 'precondition_mismatch'),
                 ((True, False, False), 'violation_not_observed'),
                 ((True, True, False), 'violation_not_observed')]
        for piv, expected in cases:
            self.assertEqual(new_sc.adjudicate(*piv), expected, piv)


class SummarizeTests(unittest.TestCase):

    def test_counts_verdicts_and_errors(self):
        records = [
            {'case_key': 'a', 'verdict': 'violation_reproduced', 'piv': {}},
            {'case_key': 'b', 'verdict': 'violation_reproduced', 'piv': {}},
            {'case_key': 'c', 'error': 'binding map missing: [x]'},
        ]
        summary = new_sc.summarize(records, 'some_batch')
        self.assertEqual(summary['counts'],
                         {'violation_reproduced': 2,
                          'error: binding map missing': 1})


if __name__ == '__main__':
    unittest.main()
