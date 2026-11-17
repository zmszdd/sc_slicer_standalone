"""Deterministic diagnostics for the stage-2 direct-witness gate."""
import unittest

from lib.plan_synthesizer import (_negated_condition_outcome_symbol,
                                  _vacuous_safety_shapes,
                                  reject_vacuous_safety,
                                  weak_invariant_bucket,
                                  weak_invariant_diagnostics)
from lib.solving import direct_relation_diagnostics


class DirectWitnessDiagnosticsTests(unittest.TestCase):
    @staticmethod
    def claim(safety, effects, symbols=None, preconditions=None):
        return {
            'symbols': symbols or {'v': {'sort': 'bool', 'checkpoint': 'after'}},
            'properties': {
                'preconditions': {'expression': preconditions or {'const': True}},
                'safety': {'expression': safety},
                'effects': {'expression': effects},
            },
        }

    def test_exploit_path_sat_is_coded_as_weak_invariant(self):
        claim = self.claim(
            {'op': 'lt', 'args': [{'var': 'a'}, {'var': 'b'}]},
            {'var': 'v'},
            symbols={'a': {'sort': 'int', 'checkpoint': 'after'},
                     'b': {'sort': 'int', 'checkpoint': 'after'},
                     'v': {'sort': 'bool', 'checkpoint': 'after'}})
        codes = [item['code'] for item in
                 weak_invariant_diagnostics(formal={'claims': [
                     {'id': 'core_claim', **claim}]})]
        self.assertIn('I_HOLDS_ON_EXPLOIT_PATH', codes)

    def test_p_entailing_i_is_coded(self):
        relation = {'op': 'lt', 'args': [{'var': 'a'}, {'var': 'b'}]}
        claim = self.claim(
            relation, {'var': 'v'}, preconditions=relation,
            symbols={'a': {'sort': 'int', 'checkpoint': 'after'},
                     'b': {'sort': 'int', 'checkpoint': 'after'},
                     'v': {'sort': 'bool', 'checkpoint': 'after'}})
        codes = [item['code'] for item in
                 weak_invariant_diagnostics(formal={'claims': [
                     {'id': 'core_claim', **claim}]})]
        self.assertIn('I_IMPLIED_BY_P', codes)

    def test_trivial_bound_is_coded(self):
        claim = self.claim(
            {'op': 'le', 'args': [{'var': 'a'}, {'var': 'a'}]},
            {'var': 'v'},
            symbols={'a': {'sort': 'int', 'checkpoint': 'after'},
                     'v': {'sort': 'bool', 'checkpoint': 'after'}})
        codes = [item['code'] for item in
                 weak_invariant_diagnostics(formal={'claims': [
                     {'id': 'core_claim', **claim}]})]
        self.assertIn('I_TRIVIAL_BOUND', codes)

    def test_checkpoint_collapse_is_advisory_only(self):
        claim = self.claim(
            {'op': 'le', 'args': [{'var': 'i_before'}, {'var': 'i_after'}]},
            {'op': 'lt', 'args': [{'var': 'e_before'}, {'var': 'e_after'}]},
            symbols={'i_before': {'sort': 'int', 'checkpoint': 'state_after'},
                     'i_after': {'sort': 'int', 'checkpoint': 'state_after'},
                     'e_before': {'sort': 'int', 'checkpoint': 'call_entry'},
                     'e_after': {'sort': 'int', 'checkpoint': 'call_exit'}})
        findings = weak_invariant_diagnostics(formal={'claims': [
            {'id': 'core_claim', **claim}]})
        advisory = [item for item in findings
                    if item['code'] == 'I_CHECKPOINT_COLLAPSED']
        self.assertTrue(advisory)
        self.assertEqual(advisory[0]['severity'], 'advisory')
        self.assertNotIn('I_CHECKPOINT_COLLAPSED',
                         reject_vacuous_safety({}, formal={'claims': [
                             {'id': 'core_claim', **claim}]}))

    def test_bucket_mapping_routes_weak_and_layer_codes(self):
        self.assertEqual(weak_invariant_bucket('I_HOLDS_ON_EXPLOIT_PATH'),
                         'weak_invariant')
        self.assertEqual(weak_invariant_bucket('I_LAYER_MISMATCH'),
                         'numeric_alignment')
        self.assertEqual(weak_invariant_bucket('I_CHECKPOINT_COLLAPSED'),
                         'semantic_alignment')

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

    def test_qualitative_only_safety_over_numeric_effect_is_named(self):
        claim = {
            'symbols': {
                'deposit_fee_charged': {'sort': 'bool'},
                'after': {'sort': 'int'},
                'before': {'sort': 'int'},
            },
            'properties': {
                'safety': {'expression': {'var': 'deposit_fee_charged'}},
                'effects': {'expression': {
                    'op': 'lt',
                    'args': [{'var': 'after'}, {'var': 'before'}]}},
            },
        }
        shapes = _vacuous_safety_shapes(claim)
        self.assertTrue(any(
            'safety is qualitative-only while effects assert a numeric harm'
            in shape for shape in shapes))

    def test_numeric_safety_over_numeric_effect_is_not_flagged(self):
        claim = {
            'symbols': {
                'fee_charged': {'sort': 'bool'},
                'after': {'sort': 'int'},
                'before': {'sort': 'int'},
            },
            'properties': {
                'safety': {'expression': {
                    'op': 'lt',
                    'args': [{'var': 'after'}, {'var': 'before'}]}},
                'effects': {'expression': {
                    'op': 'lt',
                    'args': [{'var': 'after'}, {'var': 'before'}]}},
            },
        }
        shapes = _vacuous_safety_shapes(claim)
        self.assertNotIn(
            'safety is qualitative-only while effects assert a numeric harm',
            shapes)

    def test_qualitative_only_safety_surfaces_through_reject_gate(self):
        formal = {
            'symbols': {
                'prior_holders_hold_shares': {'sort': 'bool'},
                'first_after': {'sort': 'int'},
                'first_before': {'sort': 'int'},
            },
            'claims': [{
                'id': 'core_claim',
                'properties': {
                    'preconditions': {'expression': {'var': 'prior_holders_hold_shares'}},
                    'safety': {'expression': {'var': 'prior_holders_hold_shares'}},
                    'effects': {'expression': {
                        'op': 'lt',
                        'args': [{'var': 'first_after'},
                                 {'var': 'first_before'}]}},
                },
            }],
        }
        reasons = reject_vacuous_safety({}, formal=formal, claim_id='core_claim')
        self.assertTrue(any(
            'safety is qualitative-only while effects assert a numeric harm'
            in reason for reason in reasons))


if __name__ == '__main__':
    unittest.main()
