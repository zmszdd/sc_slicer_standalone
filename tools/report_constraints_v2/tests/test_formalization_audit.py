import unittest

from lib.formalization_audit import build_contract


def formal(i_expr=None, v_expr=None):
    return {
        'symbols': {
            'p': {'sort': 'bool', 'checkpoint': 'input'},
            'i': {'sort': 'bool', 'checkpoint': 'input'},
            'v': {'sort': 'bool', 'checkpoint': 'after'},
        },
        'claims': [{
            'id': 'c1',
            'properties': {
                'preconditions': {'expression': {'var': 'p'}},
                'safety': {'expression': i_expr or {'var': 'i'}},
                'effects': {'expression': v_expr or {'var': 'v'}},
            },
        }],
    }


class FormalizationAuditTest(unittest.TestCase):
    def test_ready_claim_can_auto_assert(self):
        result = build_contract(formal())
        self.assertEqual(result['claims']['c1']['status'], 'ready')
        self.assertTrue(result['claims']['c1']['can_auto_assert'])

    def test_copied_i_v_is_rejected(self):
        expr = {'var': 'i'}
        result = build_contract(formal(i_expr=expr, v_expr=expr))
        self.assertFalse(result['claims']['c1']['can_auto_assert'])
        self.assertIn('I_COPIED_FROM_V',
                      [row['code'] for row in result['claims']['c1']['problems']])

    def test_missing_observable_kind_routes_to_reference_candidate(self):
        observability = {'c1': {'symbols': {
            'p': {}, 'i': {}, 'v': {},
        }}}
        result = build_contract(formal(), observability)
        claim = result['claims']['c1']
        self.assertIn('OBSERVABLE_KIND_MISSING', claim['warnings'])
        self.assertEqual(claim['route'], 'reference_patch_candidate')

    def test_high_binding_risk_routes_to_binding_review(self):
        observability = {'c1': {'contract_present': True, 'symbols': {
            'p': {'observable_kind': 'state', 'binding_risk': 'low'},
            'i': {'observable_kind': 'state', 'binding_risk': 'high'},
            'v': {'observable_kind': 'state', 'binding_risk': 'low'},
        }}}
        claim = build_contract(formal(), observability)['claims']['c1']
        self.assertIn('OBSERVABILITY_HIGH_RISK', claim['warnings'])
        self.assertFalse(claim['can_auto_assert'])
        self.assertEqual(claim['route'], 'binding_review')

    def test_legacy_observability_without_contract_is_not_blocking(self):
        observability = {'c1': {'contract_present': False, 'symbols': {
            'p': {}, 'i': {}, 'v': {},
        }}}
        result = build_contract(formal(), observability)
        claim = result['claims']['c1']
        self.assertNotIn('OBSERVABLE_KIND_MISSING', claim['warnings'])
        self.assertFalse(claim['observable_missing'])
        self.assertEqual(claim['route'], 'auto_assert')

    def test_cross_contract_receiver_is_required(self):
        observability = {'c1': {'symbols': {
            'p': {'observable_kind': 'state'},
            'i': {'observable_kind': 'state', 'scope': 'cross_contract'},
            'v': {'observable_kind': 'state', 'scope': 'cross_contract'},
        }}}
        result = build_contract(formal(), observability)
        self.assertIn('CROSS_CONTRACT_RECEIVER_MISSING',
                      result['claims']['c1']['warnings'])

    def test_expanded_implication_complement_is_independent(self):
        amount = {'var': 'amount'}
        minted = {'var': 'minted'}
        entitled = {'var': 'entitled'}
        i_expr = {'op': 'implies', 'args': [
            {'op': 'gt', 'args': [amount, {'const': 0}]},
            {'op': 'ge', 'args': [minted, entitled]}]}
        v_expr = {'op': 'and', 'args': [
            {'op': 'gt', 'args': [amount, {'const': 0}]},
            {'op': 'not', 'args': [
                {'op': 'ge', 'args': [minted, entitled]}]}]}
        data = formal(i_expr=i_expr, v_expr=v_expr)
        data['claims'][0]['properties']['preconditions']['expression'] = {
            'var': 'p'}
        result = build_contract(data)
        claim = result['claims']['c1']
        self.assertNotIn('EFFECT_NOT_INDEPENDENT',
                         [row['code'] for row in claim['problems']])

    def test_polarity_only_effect_is_not_auto_asserted(self):
        i_expr = {'op': 'eq', 'args': [{'var': 'i'}, {'const': 1}]}
        v_expr = {'op': 'neq', 'args': [{'var': 'i'}, {'const': 1}]}
        result = build_contract(formal(i_expr=i_expr, v_expr=v_expr))
        claim = result['claims']['c1']
        self.assertFalse(claim['can_auto_assert'])
        self.assertIn('I_V_POLARITY_ONLY', claim['warnings'])
        self.assertTrue(claim['i_v']['polarity_only'])

    def test_polarity_flip_with_independent_witness_is_not_polarity_only(self):
        i_expr = {'op': 'ge', 'args': [{'var': 'i'}, {'var': 'p'}]}
        v_expr = {'op': 'and', 'args': [
            {'op': 'not', 'args': [i_expr]}, {'var': 'v'}]}
        data = formal(i_expr=i_expr, v_expr=v_expr)
        data['symbols']['p'] = {'sort': 'bool', 'checkpoint': 'input'}
        data['symbols']['i'] = {'sort': 'bool', 'checkpoint': 'after'}
        result = build_contract(data)
        claim = result['claims']['c1']
        self.assertNotIn('I_V_POLARITY_ONLY', claim['warnings'])
        self.assertFalse(claim['i_v']['polarity_only'])

    def test_nested_implication_counterexample_is_independent(self):
        outer = {'var': 'amount'}
        inner = {'var': 'locked'}
        consequent = {'op': 'ge', 'args': [{'var': 'supply'},
                                           {'const': 0}]}
        i_expr = {'op': 'implies', 'args': [
            outer, {'op': 'implies', 'args': [inner, consequent]}]}
        v_expr = {'op': 'and', 'args': [
            outer, inner, {'op': 'not', 'args': [consequent]},
            {'var': 'underflow'}]}
        data = formal(i_expr=i_expr, v_expr=v_expr)
        result = build_contract(data)
        claim = result['claims']['c1']
        self.assertTrue(claim['i_v']['implication_counterexample'])
        self.assertNotIn('I_V_TAUTOLOGY', claim['warnings'])

    def test_invariant_restating_precondition_routes_to_review(self):
        data = formal()
        data['claims'][0]['properties']['safety']['expression'] = {'var': 'p'}
        result = build_contract(data)
        claim = result['claims']['c1']
        self.assertFalse(claim['can_auto_assert'])
        self.assertIn('I_COPIED_FROM_P', claim['warnings'])

    def test_self_implication_is_rejected(self):
        expr = {'op': 'implies', 'args': [{'var': 'i'}, {'var': 'i'}]}
        result = build_contract(formal(i_expr=expr))
        claim = result['claims']['c1']
        self.assertEqual(claim['status'], 'rejected')
        self.assertIn('I_SELF_IMPLICATION',
                      [row['code'] for row in claim['problems']])

    def test_trivial_operand_invariant_is_rejected(self):
        expr = {'op': 'eq', 'args': [{'var': 'i'}, {'var': 'i'}]}
        result = build_contract(formal(i_expr=expr))
        claim = result['claims']['c1']
        self.assertIn('I_TRIVIAL_OPERAND',
                      [row['code'] for row in claim['problems']])

    def test_before_after_implication_is_a_transition(self):
        i_expr = {'op': 'implies', 'args': [{'var': 'p'}, {'var': 'i'}]}
        data = formal(i_expr=i_expr)
        data['symbols']['p']['checkpoint'] = 'before action'
        data['symbols']['i']['checkpoint'] = 'after action'
        result = build_contract(data)
        claim = result['claims']['c1']
        self.assertTrue(claim['semantic_profile']['has_before_after'])
        self.assertEqual(claim['semantic_bucket'], 'transition')

    def test_single_snapshot_is_reported_but_not_automatically_rejected(self):
        result = build_contract(formal())
        claim = result['claims']['c1']
        self.assertEqual(claim['semantic_bucket'], 'transition')
        data = formal()
        data['symbols']['i']['checkpoint'] = 'after action'
        data['symbols']['v']['checkpoint'] = 'after action'
        result = build_contract(data)
        claim = result['claims']['c1']
        self.assertEqual(claim['semantic_bucket'], 'snapshot_only')
        self.assertIn('I_SNAPSHOT_ONLY', claim['advisories'])

    def test_qualitative_impact_shadow_is_reported_in_profile(self):
        data = formal()
        data['symbols']['size'] = {'sort': 'int', 'checkpoint': 'after call'}
        data['symbols']['bloated'] = {
            'sort': 'bool', 'checkpoint': 'after call',
            'meaning': 'tree bloated beyond the configured limit'}
        relation = {'op': 'le', 'args': [
            {'var': 'size'}, {'const': 3}]}
        data['claims'][0]['properties']['safety']['expression'] = relation
        data['claims'][0]['properties']['effects']['expression'] = {
            'op': 'and', 'args': [
                {'var': 'bloated'}, {'op': 'not', 'args': [relation]}]}
        claim = build_contract(data)['claims']['c1']
        self.assertIn('bloated',
                      claim['semantic_profile']['qualitative_impact_shadow'])


if __name__ == '__main__':
    unittest.main()
