"""Deterministic diagnostics for the stage-2 direct-witness gate."""
import unittest

from lib.plan_synthesizer import (_negated_condition_outcome_symbol,
                                  _vacuous_safety_shapes,
                                  reject_vacuous_safety)
from lib.solving import direct_relation_diagnostics


class DirectWitnessDiagnosticsTests(unittest.TestCase):
    def test_outcome_negating_condition_is_named(self):
        plan = {
            'pattern': {
                'kind': 'bounded_relation',
                'condition': {'kind': 'truth', 'symbol': 'underflow_occurred',
                              'value': False},
                'value': {'symbol': 'balance'},
                'operator': 'ge',
                'bound': {'symbol': 'accrued_fees'},
            },
            'impact_outcome': {
                'source_id': 'impact',
                'predicate': {'kind': 'truth', 'symbol': 'underflow_occurred',
                              'value': True},
            },
        }
        self.assertEqual(_negated_condition_outcome_symbol(plan),
                         'underflow_occurred')
        reasons = reject_vacuous_safety(plan)
        self.assertTrue(any(
            'impact outcome negates the pattern condition symbol' in reason
            for reason in reasons))

    def test_outcome_not_negating_condition_is_unnamed(self):
        plan = {
            'pattern': {
                'kind': 'bounded_relation',
                'condition': {'kind': 'truth', 'symbol': 'in_scope',
                              'value': True},
                'value': {'symbol': 'balance'},
                'operator': 'ge',
                'bound': {'symbol': 'accrued_fees'},
            },
            'impact_outcome': {
                'source_id': 'impact',
                'predicate': {'kind': 'truth', 'symbol': 'underflow_occurred',
                              'value': True},
            },
        }
        self.assertIsNone(_negated_condition_outcome_symbol(plan))

    def test_direct_contradiction_is_feasible(self):
        claim = {
            'symbols': {'v': {'sort': 'bool'}},
            'properties': {
                'safety': {'expression': {'op': 'not',
                                          'args': [{'var': 'v'}]}},
                'effects': {'expression': {'var': 'v'}},
            },
        }
        diagnostics = direct_relation_diagnostics(claim)
        self.assertTrue(diagnostics['feasible'])
        self.assertEqual(diagnostics['failing'], [])

    def test_tautological_safety_consequent_is_named(self):
        claim = {
            'symbols': {'a': {'sort': 'bool'}, 'x': {'sort': 'bool'}},
            'properties': {
                'safety': {'expression': {
                    'op': 'implies',
                    'args': [{'var': 'a'},
                             {'op': 'eq', 'args': [{'var': 'x'},
                                                   {'var': 'x'}]}]}},
                'effects': {'expression': {'var': 'a'}},
            },
        }
        shapes = _vacuous_safety_shapes(claim)
        self.assertIn('safety consequent is a tautological self-equality',
                      shapes)

    def test_contradictory_effect_is_named(self):
        claim = {
            'symbols': {'a': {'sort': 'bool'}, 'x': {'sort': 'bool'}},
            'properties': {
                'safety': {'expression': {'op': 'implies',
                                          'args': [{'var': 'a'},
                                                   {'op': 'eq',
                                                    'args': [{'var': 'x'},
                                                             {'var': 'x'}]}]}},
                'effects': {'expression': {
                    'op': 'and',
                    'args': [{'op': 'not',
                              'args': [{'op': 'eq',
                                        'args': [{'var': 'x'},
                                                 {'var': 'x'}]}]},
                             {'var': 'a'}]}},
            },
        }
        shapes = _vacuous_safety_shapes(claim)
        self.assertIn(
            'effects contains an unsatisfiable negation of a self-equality',
            shapes)


if __name__ == '__main__':
    unittest.main()
