import unittest

from lib.stage2_contract import decide
from lib.stage2_restate import (_pair_index, _verify, apply,
                                build_final_contract, restate_claim)


def formal(safety, symbols):
    return {
        'symbols': {name: {'sort': sort, 'checkpoint': checkpoint}
                    for name, (sort, checkpoint) in symbols.items()},
        'claims': [{
            'id': 'c1',
            'properties': {
                'preconditions': {'expression': {'var': 'p'}},
                'safety': {'expression': safety},
                'effects': {'expression': {'var': 'v'}},
            },
        }],
    }


class Stage2RestateTest(unittest.TestCase):
    def test_pair_index_links_intended_and_recipient_roles(self):
        symbols = {
            'intended_user': {'sort': 'address', 'checkpoint': 'at distribution'},
            'rewards_recipient': {'sort': 'address',
                                  'checkpoint': 'at distribution'},
        }
        metas = {
            'intended_user': {
                **symbols['intended_user'],
                'meaning': 'the intended user for this reward',
                'entity_ids': ['user'],
            },
            'rewards_recipient': {
                **symbols['rewards_recipient'],
                'meaning': 'recipient of the pending rewards',
                'entity_ids': ['user', 'rewards'],
            },
        }
        pairs = _pair_index(symbols, metas)
        self.assertTrue(any(
            row['before'] == 'intended_user'
            and row['after'] == 'rewards_recipient'
            and row.get('synthetic')
            for row in pairs))

    def test_contract_exposes_piv_checkpoints_and_verification(self):
        data = formal({'op': 'implies', 'args': [
            {'var': 'p'}, {'var': 'tree_size_changed'}]}, {
                'p': ('bool', 'input'),
                'tree_size_before': ('int', 'before submission'),
                'tree_size_after': ('int', 'after submission'),
                'tree_size_changed': ('bool', 'after submission'),
                'v': ('bool', 'after'),
            })
        declaration = {'claim_id': 'c1', 'binding_contract': {'symbols': [
            {'symbol': 'tree_size_before', 'meaning': 'tree size before submission'},
            {'symbol': 'tree_size_after', 'meaning': 'tree size after submission'},
        ]}}
        data['claims'][0]['properties']['effects']['expression'] = {
            'op': 'and', 'args': [{'var': 'v'},
                                  {'var': 'tree_size_before'},
                                  {'var': 'tree_size_after'}]}
        result = restate_claim(data, 'c1', declaration=declaration)
        self.assertEqual(result['schema_version'], 'invariant-restatement/2')
        self.assertEqual(result['original'], {
            'preconditions': {'var': 'p'},
            'safety': data['claims'][0]['properties']['safety']['expression'],
            'effects': data['claims'][0]['properties']['effects']['expression']})
        self.assertTrue(result['before_after_pairs'])
        self.assertTrue(result['verification']['accepted'])
        self.assertEqual(
            result['verification']['audit_rules_version'],
            'stage2-formalization-contract/2')

    def test_precondition_symbols_are_not_restated(self):
        data = formal({'op': 'implies', 'args': [
            {'var': 'changed'}, {'var': 'p'}]}, {
                'changed': ('bool', 'before'),
                'p': ('bool', 'after'),
                'p_before': ('int', 'before'),
                'p_after': ('int', 'after'),
            })
        data['claims'][0]['properties']['preconditions']['expression'] = {
            'var': 'changed'}
        result = restate_claim(data, 'c1')
        self.assertEqual(result['status'], 'unchanged')
        self.assertEqual(result['restated_safety'],
                         result['original_safety'])

    def test_self_implication_is_rejected_by_shared_audit(self):
        data = formal({'var': 'authorized'}, {
            'p': ('bool', 'input'),
            'authorized': ('bool', 'after'),
            'v': ('bool', 'after'),
        })
        verification = _verify(
            data, data['claims'][0], 'c1',
            {'op': 'implies', 'args': [{'var': 'p'}, {'var': 'p'}]},
            None, None)
        self.assertFalse(verification['accepted'])
        self.assertIn('I_SELF_IMPLICATION', verification['restated_codes'])

    def test_i_copied_from_v_is_rejected_by_shared_audit(self):
        data = formal({'var': 'v'}, {
            'p': ('bool', 'input'),
            'v': ('bool', 'after'),
        })
        data['claims'][0]['properties']['effects']['expression'] = {'var': 'v'}
        verification = _verify(data, data['claims'][0], 'c1',
                               {'var': 'v'}, None, None)
        self.assertFalse(verification['accepted'])
        self.assertIn('I_COPIED_FROM_V', verification['restated_codes'])

    def test_call_outcome_witness_is_reported_without_guessing(self):
        data = formal({'var': 'order_succeeds'}, {
            'p': ('bool', 'input'),
            'order_succeeds': ('bool', 'after submission'),
            'orders_stopped': ('bool', 'after submission'),
            'v': ('bool', 'after'),
        })
        data['claims'][0]['properties']['effects']['expression'] = {
            'op': 'and', 'args': [
                {'op': 'not', 'args': [{'var': 'order_succeeds'}]},
                {'var': 'orders_stopped'}]}
        result = restate_claim(data, 'c1')
        self.assertEqual(result['status'], 'unchanged')
        self.assertEqual(result['call_outcome']['witnessed_by_v'], True)
        self.assertEqual(result['unresolved'], [])

    def test_failure_outcome_keeps_implication_counterexample(self):
        data = formal({'op': 'implies', 'args': [
            {'var': 'signed'},
            {'op': 'not', 'args': [{'var': 'reverts'}]},
        ]}, {
            'signed': ('bool', 'before call'),
            'reverts': ('bool', 'during call'),
            'observed': ('bool', 'after call'),
        })
        data['claims'][0]['properties']['effects']['expression'] = {
            'op': 'and', 'args': [
                {'var': 'signed'},
                {'var': 'reverts'},
                {'var': 'observed'},
            ]}
        result = restate_claim(data, 'c1')
        self.assertEqual(result['status'], 'unchanged')
        self.assertEqual(result['restated_safety'], result['original_safety'])
        self.assertTrue(result['verification']['accepted'])
        self.assertNotIn('I_V_TAUTOLOGY',
                         result['verification']['restated_codes'])
        self.assertEqual(result['unresolved'], [])

    def test_v_falsifier_restates_layer_mismatch_with_independent_witness(self):
        data = {
            'symbols': {
                'p': {'sort': 'bool', 'checkpoint': 'input'},
                'balance_before': {'sort': 'uint256',
                                   'checkpoint': 'before call'},
                'balance_after': {'sort': 'uint256',
                                  'checkpoint': 'after call'},
                'hazard': {'sort': 'bool', 'checkpoint': 'after call'},
                'worst_removed': {'sort': 'bool',
                                  'checkpoint': 'after call'},
            },
            'claims': [{
                'id': 'c1',
                'properties': {
                    'preconditions': {'expression': {'var': 'p'}},
                    'safety': {'expression': {'var': 'worst_removed'}},
                    'effects': {'expression': {'op': 'and', 'args': [
                        {'op': 'lt', 'args': [
                            {'var': 'balance_before'},
                            {'var': 'balance_after'}]},
                        {'op': 'not', 'args': [{'var': 'worst_removed'}]},
                        {'var': 'hazard'},
                    ]}},
                },
            }],
        }
        declaration = {
            'claim_id': 'c1',
            'weak_invariant_diagnostics': [{
                'code': 'I_LAYER_MISMATCH', 'severity': 'blocking',
                'detail': 'qualitative invariant over numeric effect',
            }],
            'i_falsifier_hint': {'query': 'P_and_V_and_not_I',
                                 'status': 'sat', 'witness': {}},
        }
        result = restate_claim(data, 'c1', declaration=declaration)
        self.assertEqual(result['status'], 'restated')
        self.assertTrue(result['verification']['accepted'])
        self.assertEqual(result['restated_safety'], {'op': 'ge', 'args': [
            {'var': 'balance_before'}, {'var': 'balance_after'}]})
        self.assertIn('I_LAYER_MISMATCH',
                      result['verification']['original_weak_codes'])
        self.assertNotIn('I_LAYER_MISMATCH',
                         result['verification']['restated_weak_codes'])
        self.assertEqual(result['v_falsifier']['witness'], 'worst_removed')

    def test_v_falsifier_rejects_atom_already_in_preconditions(self):
        relation = {'op': 'lt', 'args': [
            {'var': 'balance_before'}, {'var': 'balance_after'}]}
        data = formal({'var': 'worst_removed'}, {
            'p': ('bool', 'input'),
            'balance_before': ('uint256', 'before call'),
            'balance_after': ('uint256', 'after call'),
            'hazard': ('bool', 'after call'),
            'worst_removed': ('bool', 'after call'),
        })
        data['claims'][0]['properties']['preconditions']['expression'] = relation
        data['claims'][0]['properties']['effects']['expression'] = {
            'op': 'and', 'args': [relation,
                                  {'op': 'not', 'args': [
                                      {'var': 'worst_removed'}]},
                                  {'var': 'hazard'}]}
        declaration = {'weak_invariant_diagnostics': [
            {'code': 'I_LAYER_MISMATCH', 'severity': 'blocking'}]}
        result = restate_claim(data, 'c1', declaration=declaration)
        self.assertIsNone(result['v_falsifier'])
        self.assertEqual(result['status'], 'unchanged')

    def test_v_falsifier_restates_post_state_bound_violation(self):
        data = {
            'symbols': {
                'p': {'sort': 'bool', 'checkpoint': 'input'},
                'queue_after': {'sort': 'uint256',
                                'checkpoint': 'after attacker spam'},
                'max_entries': {'sort': 'uint256',
                                'checkpoint': 'configured limit'},
                'hazard': {'sort': 'bool', 'checkpoint': 'after spam'},
            },
            'claims': [{
                'id': 'c1',
                'properties': {
                    'preconditions': {'expression': {'var': 'p'}},
                    'safety': {'expression': {'var': 'hazard'}},
                    'effects': {'expression': {'op': 'and', 'args': [
                        {'op': 'gt', 'args': [
                            {'var': 'queue_after'}, {'var': 'max_entries'}]},
                        {'var': 'hazard'},
                    ]}},
                },
            }],
        }
        declaration = {
            'claim_id': 'c1',
            'weak_invariant_diagnostics': [{
                'code': 'I_LAYER_MISMATCH', 'severity': 'blocking',
                'detail': 'qualitative invariant over numeric effect'}],
            'i_falsifier_hint': {'query': 'P_and_V_and_not_I',
                                 'status': 'sat', 'witness': {}},
        }
        result = restate_claim(data, 'c1', declaration=declaration)
        self.assertEqual(result['status'], 'restated')
        self.assertTrue(result['verification']['accepted'])
        self.assertEqual(result['restated_safety'], {'op': 'le', 'args': [
            {'var': 'queue_after'}, {'var': 'max_entries'}]})
        self.assertEqual(result['v_falsifier']['mode'], 'post_bound')
        self.assertEqual(result['v_falsifier']['witness'], 'queue_after')
        self.assertNotIn('I_LAYER_MISMATCH',
                         result['verification']['restated_weak_codes'])

    def test_v_falsifier_ignores_negated_numeric_atom(self):
        data = {
            'symbols': {
                'p': {'sort': 'bool', 'checkpoint': 'input'},
                'queue_after': {'sort': 'uint256',
                                'checkpoint': 'after attacker spam'},
                'max_entries': {'sort': 'uint256',
                                'checkpoint': 'configured limit'},
                'hazard': {'sort': 'bool', 'checkpoint': 'after spam'},
            },
            'claims': [{
                'id': 'c1',
                'properties': {
                    'preconditions': {'expression': {'var': 'p'}},
                    'safety': {'expression': {'var': 'hazard'}},
                    'effects': {'expression': {'op': 'and', 'args': [
                        {'op': 'not', 'args': [
                            {'op': 'le', 'args': [
                                {'var': 'queue_after'},
                                {'var': 'max_entries'}]}]},
                        {'var': 'hazard'},
                    ]}},
                },
            }],
        }
        declaration = {'weak_invariant_diagnostics': [
            {'code': 'I_LAYER_MISMATCH', 'severity': 'blocking'}]}
        result = restate_claim(data, 'c1', declaration=declaration)
        self.assertIsNone(result['v_falsifier'])
        self.assertEqual(result['status'], 'unchanged')

    def test_v_falsifier_requires_configured_bound(self):
        data = {
            'symbols': {
                'p': {'sort': 'bool', 'checkpoint': 'input'},
                'queue_after': {'sort': 'uint256',
                                'checkpoint': 'after attacker spam'},
                'victims': {'sort': 'uint256',
                            'checkpoint': 'during attacker spam'},
                'hazard': {'sort': 'bool', 'checkpoint': 'after spam'},
            },
            'claims': [{
                'id': 'c1',
                'properties': {
                    'preconditions': {'expression': {'var': 'p'}},
                    'safety': {'expression': {'var': 'hazard'}},
                    'effects': {'expression': {'op': 'and', 'args': [
                        {'op': 'gt', 'args': [
                            {'var': 'queue_after'}, {'var': 'victims'}]},
                        {'var': 'hazard'},
                    ]}},
                },
            }],
        }
        declaration = {'weak_invariant_diagnostics': [
            {'code': 'I_LAYER_MISMATCH', 'severity': 'blocking'}]}
        result = restate_claim(data, 'c1', declaration=declaration)
        self.assertIsNone(result['v_falsifier'])
        self.assertEqual(result['status'], 'unchanged')

    def test_numeric_counterexample_accepts_constant_bound(self):
        data = {
            'symbols': {
                'p': {'sort': 'bool', 'checkpoint': 'input'},
                'inner_value': {'sort': 'uint256',
                                'checkpoint': 'during nested call'},
                'hazard': {'sort': 'bool', 'checkpoint': 'after call'},
            },
            'claims': [{
                'id': 'c1',
                'properties': {
                    'preconditions': {'expression': {'var': 'p'}},
                    'safety': {'expression': {'var': 'hazard'}},
                    'effects': {'expression': {'op': 'and', 'args': [
                        {'op': 'gt', 'args': [
                            {'var': 'inner_value'}, {'const': 0}]},
                        {'var': 'hazard'},
                    ]}},
                },
            }],
        }
        declaration = {'weak_invariant_diagnostics': [
            {'code': 'I_LAYER_MISMATCH', 'severity': 'blocking'}]}
        result = restate_claim(data, 'c1', declaration=declaration)
        self.assertEqual(result['status'], 'restated')
        self.assertTrue(result['verification']['accepted'])
        self.assertEqual(result['v_falsifier']['mode'], 'const_bound')
        self.assertEqual(result['restated_safety'], {'op': 'implies', 'args': [
            {'op': 'gt', 'args': [{'var': 'inner_value'}, {'const': 0}]},
            {'op': 'le', 'args': [{'var': 'inner_value'}, {'const': 0}]},
        ]})
        self.assertIn(
            'I_LAYER_MISMATCH',
            result['verification']['original_weak_codes'])
        self.assertNotIn(
            'I_LAYER_MISMATCH',
            result['verification']['restated_weak_codes'])

    def test_numeric_counterexample_accepts_before_input_bound(self):
        data = {
            'symbols': {
                'p': {'sort': 'bool', 'checkpoint': 'input'},
                'sent_value': {'sort': 'uint256', 'checkpoint': 'at call'},
                'quoted_fee': {'sort': 'uint256', 'checkpoint': 'before call'},
                'hazard': {'sort': 'bool', 'checkpoint': 'after call'},
            },
            'claims': [{
                'id': 'c1',
                'properties': {
                    'preconditions': {'expression': {'var': 'p'}},
                    'safety': {'expression': {'var': 'hazard'}},
                    'effects': {'expression': {'op': 'and', 'args': [
                        {'op': 'gt', 'args': [
                            {'var': 'sent_value'}, {'var': 'quoted_fee'}]},
                        {'var': 'hazard'},
                    ]}},
                },
            }],
        }
        declaration = {'weak_invariant_diagnostics': [
            {'code': 'I_LAYER_MISMATCH', 'severity': 'blocking'}]}
        result = restate_claim(data, 'c1', declaration=declaration)
        self.assertEqual(result['status'], 'restated')
        self.assertEqual(result['v_falsifier']['mode'], 'input_bound')
        self.assertEqual(result['restated_safety'], {'op': 'implies', 'args': [
            {'op': 'gt', 'args': [
                {'var': 'sent_value'}, {'var': 'quoted_fee'}]},
            {'op': 'le', 'args': [
                {'var': 'sent_value'}, {'var': 'quoted_fee'}]},
        ]})

    def test_numeric_counterexample_rejects_same_layer_comparison(self):
        data = {
            'symbols': {
                'p': {'sort': 'bool', 'checkpoint': 'input'},
                'left': {'sort': 'uint256', 'checkpoint': 'at call'},
                'right': {'sort': 'uint256', 'checkpoint': 'at call'},
                'hazard': {'sort': 'bool', 'checkpoint': 'after call'},
            },
            'claims': [{
                'id': 'c1',
                'properties': {
                    'preconditions': {'expression': {'var': 'p'}},
                    'safety': {'expression': {'var': 'hazard'}},
                    'effects': {'expression': {'op': 'and', 'args': [
                        {'op': 'gt', 'args': [
                            {'var': 'left'}, {'var': 'right'}]},
                        {'var': 'hazard'},
                    ]}},
                },
            }],
        }
        declaration = {'weak_invariant_diagnostics': [
            {'code': 'I_LAYER_MISMATCH', 'severity': 'blocking'}]}
        result = restate_claim(data, 'c1', declaration=declaration)
        self.assertIsNone(result['v_falsifier'])
        self.assertEqual(result['status'], 'unchanged')

    def test_numeric_counterexample_coexists_with_symbol_replacement(self):
        data = {
            'symbols': {
                'p': {'sort': 'bool', 'checkpoint': 'input'},
                'tree_size_before': {'sort': 'uint256', 'checkpoint': 'before call'},
                'tree_size_after': {'sort': 'uint256', 'checkpoint': 'after call'},
                'tree_size_changed': {'sort': 'bool',
                                      'checkpoint': 'after call'},
                'inner_value': {'sort': 'uint256',
                                'checkpoint': 'during nested call'},
                'hazard': {'sort': 'bool', 'checkpoint': 'after call'},
            },
            'claims': [{
                'id': 'c1',
                'properties': {
                    'preconditions': {'expression': {'var': 'p'}},
                    'safety': {'expression': {'var': 'tree_size_changed'}},
                    'effects': {'expression': {'op': 'and', 'args': [
                        {'var': 'tree_size_before'},
                        {'var': 'tree_size_after'},
                        {'op': 'gt', 'args': [
                            {'var': 'inner_value'}, {'const': 0}]},
                        {'var': 'hazard'},
                    ]}},
                },
            }],
        }
        declaration = {
            'claim_id': 'c1',
            'binding_contract': {'symbols': [
                {'symbol': 'tree_size_before',
                 'meaning': 'tree size before call'},
                {'symbol': 'tree_size_after',
                 'meaning': 'tree size after call'},
            ]},
            'weak_invariant_diagnostics': [
                {'code': 'I_LAYER_MISMATCH', 'severity': 'blocking'}],
        }
        result = restate_claim(data, 'c1', declaration=declaration)
        self.assertEqual(result['status'], 'restated')
        rules = {row.get('rule') for row in result['changes']}
        self.assertIn('changed', rules)
        self.assertIn('v_counterexample', rules)
        self.assertEqual(result['v_falsifier']['mode'], 'const_bound')

    def test_v_falsifier_requires_independent_effect_witness(self):
        data = formal({'var': 'worst_removed'}, {
            'p': ('bool', 'input'),
            'balance_before': ('uint256', 'before call'),
            'balance_after': ('uint256', 'after call'),
            'hazard': ('bool', 'after call'),
        })
        data['claims'][0]['properties']['effects']['expression'] = {
            'op': 'and', 'args': [
                {'op': 'lt', 'args': [
                    {'var': 'balance_before'}, {'var': 'balance_after'}]},
                {'op': 'not', 'args': [{'var': 'worst_removed'}]},
            ]}
        declaration = {'weak_invariant_diagnostics': [
            {'code': 'I_LAYER_MISMATCH', 'severity': 'blocking'}]}
        result = restate_claim(data, 'c1', declaration=declaration)
        self.assertIsNone(result['v_falsifier'])
        self.assertEqual(result['status'], 'unchanged')

    def test_final_contract_preserves_non_restatable_stage2_route(self):
        restatement = {
            'schema_version': 'invariant-restatement/2',
            'claim_id': 'c1',
            'status': 'unchanged',
            'changes': [],
            'unresolved': [],
            'verification': {'accepted': False},
        }
        original = {'route': 'binding_review', 'status': 'needs_review',
                    'can_auto_assert': False,
                    'problems': [{'code': 'MISSING_CHECKPOINT'}]}
        contract = build_final_contract(
            formal({'var': 'v'}, {'v': ('bool', 'after')}),
            restatement, original_contract=original)
        self.assertEqual(contract['route'], 'binding_review')
        self.assertEqual(contract['contract_source'], 'stage2_preserved')

    def test_final_contract_uses_verified_restatement_audit(self):
        data = formal({'op': 'implies', 'args': [
            {'var': 'p'}, {'var': 'tree_size_changed'}]}, {
                'p': ('bool', 'input'),
                'tree_size_before': ('int', 'before'),
                'tree_size_after': ('int', 'after'),
                'tree_size_changed': ('bool', 'after'),
                'v': ('bool', 'after'),
            })
        data['claims'][0]['properties']['effects']['expression'] = {
            'op': 'and', 'args': [
                {'var': 'v'}, {'var': 'tree_size_before'},
                {'var': 'tree_size_after'}]}
        restatement = restate_claim(data, 'c1')
        updated = apply(data, restatement)
        contract = build_final_contract(
            updated, restatement,
            original_contract={'route': 'auto_assert', 'status': 'ready',
                               'can_auto_assert': True})
        self.assertEqual(contract['route'], 'auto_assert')
        self.assertEqual(contract['contract_source'], 'stage3_restated')
        self.assertTrue(contract['invariant_restatement']['accepted'])

    def test_trusted_negative_without_accepted_restatement_routes_to_negative_witness(self):
        restatement = {
            'schema_version': 'invariant-restatement/2',
            'claim_id': 'c1',
            'status': 'unchanged',
            'changes': [],
            'unresolved': [],
            'verification': {'accepted': False, 'reasons': []},
        }
        contract = build_final_contract(
            formal({'var': 'v'}, {'v': ('bool', 'after')}), restatement,
            original_contract={'route': 'auto_assert', 'status': 'ready',
                               'can_auto_assert': True},
            trusted_label={'claim_id': 'c1', 'validity': 'invalid'})
        gate = decide(contract)
        self.assertEqual(contract['route'], 'negative_witness')
        self.assertFalse(contract['can_auto_assert'])
        self.assertEqual(contract['trusted_label_review']['code'],
                         'TRUSTED_JUDGE_INVALID')
        self.assertFalse(gate['blocking'])
        self.assertEqual(gate['semantic_route'], 'negative_witness')

    def test_accepted_restatement_does_not_override_trusted_negative(self):
        data = formal({'op': 'implies', 'args': [
            {'var': 'p'}, {'var': 'tree_size_changed'}]}, {
                'p': ('bool', 'input'),
                'tree_size_before': ('int', 'before'),
                'tree_size_after': ('int', 'after'),
                'tree_size_changed': ('bool', 'after'),
                'v': ('bool', 'after'),
            })
        data['claims'][0]['properties']['effects']['expression'] = {
            'op': 'and', 'args': [
                {'var': 'v'}, {'var': 'tree_size_before'},
                {'var': 'tree_size_after'}]}
        restatement = {
            'schema_version': 'invariant-restatement/2',
            'claim_id': 'c1',
            'status': 'restated',
            'changes': [{'symbol': 'tree_size_changed', 'rule': 'changed'}],
            'unresolved': [],
            'verification': {'accepted': True, 'reasons': []},
        }
        contract = build_final_contract(
            data, restatement,
            trusted_label={'claim_id': 'c1', 'validity': 'invalid'})
        self.assertEqual(contract['route'], 'negative_witness')
        self.assertFalse(contract['can_auto_assert'])
        self.assertTrue(contract['negative_witness_route']['eligible'])
        self.assertTrue(contract['trusted_label_review']['restatement_accepted'])

    def test_bindability_feedback_blocks_unresolved_handoff(self):
        restatement = {
            'schema_version': 'invariant-restatement/2',
            'claim_id': 'c1',
            'status': 'unchanged',
            'changes': [], 'unresolved': [],
            'verification': {'accepted': False, 'reasons': []},
        }
        contract = build_final_contract(
            formal({'var': 'v'}, {'v': ('bool', 'after')}), restatement,
            original_contract={'route': 'auto_assert', 'status': 'ready',
                               'can_auto_assert': True},
            binding_feedback={'needs_restatement': True,
                              'reasons': ['unbound P/I symbols: x']})
        gate = decide(contract)
        self.assertEqual(contract['route'], 'binding_review')
        self.assertEqual(contract['contract_source'],
                         'stage3_bindability_feedback')
        self.assertEqual(gate['category'], 'stage2_review_required')
        self.assertTrue(gate['blocking'])

    def test_changed_becomes_before_after_transition(self):
        data = formal(
            {'op': 'implies', 'args': [
                {'var': 'p'}, {'var': 'tree_size_changed'}]},
            {
                'p': ('bool', 'input'),
                'tree_size_before_post': ('int', 'before post'),
                'tree_size_after_post': ('int', 'after post'),
                'tree_size_changed': ('bool', 'after post'),
                'v': ('bool', 'after'),
            })
        data['claims'][0]['properties']['effects']['expression'] = {
            'op': 'and', 'args': [
                {'var': 'v'}, {'var': 'tree_size_before_post'},
                {'var': 'tree_size_after_post'}]}
        result = restate_claim(data, 'c1')
        self.assertEqual(result['status'], 'restated')
        self.assertEqual(result['changes'][0]['rule'], 'changed')
        self.assertEqual(result['restated_safety'], {
            'op': 'implies', 'args': [
                {'var': 'p'},
                {'op': 'neq', 'args': [
                    {'var': 'tree_size_before_post'},
                    {'var': 'tree_size_after_post'}]}]})

    def test_unchanged_and_drained_rules(self):
        data = formal(
            {'op': 'and', 'args': [
                {'var': 'owner_unchanged'}, {'var': 'vault_drained'}]},
            {
                'p': ('bool', 'input'),
                'owner_before': ('address', 'before call'),
                'owner_after': ('address', 'after call'),
                'owner_unchanged': ('bool', 'after call'),
                'balance_before': ('int', 'before call'),
                'balance_after': ('int', 'after call'),
                'vault_drained': ('bool', 'after call'),
                'v': ('bool', 'after'),
            })
        data['claims'][0]['properties']['effects']['expression'] = {
            'op': 'and', 'args': [
                {'var': 'v'}, {'var': 'owner_before'}, {'var': 'owner_after'},
                {'var': 'balance_before'}, {'var': 'balance_after'}]}
        result = restate_claim(data, 'c1')
        exprs = {row['rule']: row['expression'] for row in result['changes']}
        self.assertEqual(exprs['unchanged']['op'], 'eq')
        self.assertEqual(exprs['drained']['op'], 'gt')

    def test_unresolved_symbol_keeps_original_expression(self):
        data = formal({'var': 'authorized'}, {
            'p': ('bool', 'input'),
            'authorized': ('bool', 'after'),
            'v': ('bool', 'after'),
        })
        result = restate_claim(data, 'c1')
        self.assertEqual(result['status'], 'unchanged')
        self.assertEqual(result['restated_safety'], {'var': 'authorized'})
        self.assertTrue(result['unresolved'])

    def test_polarity_only_authorization_is_rejected_by_audit(self):
        data = formal({'var': 'caller_authorized'}, {
            'p': ('bool', 'input'),
            'caller_authorized': ('bool', 'after'),
            'rebalance_triggered_by_unauthorized_caller': ('bool', 'after'),
            'v': ('bool', 'after'),
        })
        data['claims'][0]['properties']['effects']['expression'] = {
            'var': 'rebalance_triggered_by_unauthorized_caller'}
        result = restate_claim(data, 'c1')
        self.assertEqual(result['status'], 'rejected')
        self.assertEqual(result['restated_safety'], {'var': 'caller_authorized'})
        self.assertIn('I_V_POLARITY_ONLY',
                      result['verification']['restated_codes'])

    def test_apply_does_not_mutate_input(self):
        data = formal({'var': 'tree_size_changed'}, {
            'p': ('bool', 'input'),
            'tree_size_before': ('int', 'before'),
            'tree_size_after': ('int', 'after'),
            'tree_size_changed': ('bool', 'after'),
            'v': ('bool', 'after'),
        })
        result = restate_claim(data, 'c1')
        updated = apply(data, result)
        self.assertEqual(data['claims'][0]['properties']['safety']['expression'],
                         {'var': 'tree_size_changed'})
        self.assertEqual(updated['claims'][0]['properties']['safety']['expression'],
                         result['restated_safety'])


if __name__ == '__main__':
    unittest.main()
