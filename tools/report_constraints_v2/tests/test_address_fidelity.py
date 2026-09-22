"""Offline controls for explicit zero-address P/I/V formalization."""
import copy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from fidelity import ZERO_INPUT, check_address_plan, zero_relation
import semantic_pipeline as pipeline
from prompts.versions import semantic_prompts_v311 as prompts


ELEMENTS = {'statements': [
    {'id': 'p_recipient', 'kind': 'precondition',
     'text': 'The recipient input is address(0).'},
    {'id': 'i_reject', 'kind': 'security_intent',
     'text': 'A transfer to the zero address must revert.'},
    {'id': 'v_owner', 'kind': 'impact',
     'text': 'Ownership is assigned to address(0).'},
]}


def relation(symbol):
    return {'kind': 'comparison', 'left': symbol, 'operator': 'eq',
            'right': {'symbol': 'zero_address'}}


def plan():
    return {'symbols': {
        'zero_address': {'sort': 'address', 'meaning': 'address(0)'},
        'recipient': {'sort': 'address'}, 'owner_after': {'sort': 'address'}},
        'precondition_terms': [{'source_id': 'p_recipient',
                                'predicate': relation('recipient')}],
        'intent_id': 'i_reject', 'impact_ids': ['v_owner'],
        'pattern': {'kind': 'condition_forbids_effect',
                    'condition': relation('recipient'),
                    'effect': relation('owner_after')}}


class AddressFidelityTests(unittest.TestCase):
    def test_address_comparisons_pass(self):
        good = plan()
        self.assertTrue(zero_relation(good['pattern']['condition'], good['symbols']))
        check_address_plan(good, ELEMENTS)

    def test_boolean_placeholders_and_wrong_sort_rejected(self):
        weak = plan()
        weak['precondition_terms'][0]['predicate'] = {
            'kind': 'truth', 'symbol': 'transfer_to_zero', 'value': True}
        with self.assertRaisesRegex(ValueError, 'P relation'):
            check_address_plan(weak, ELEMENTS)
        weak = plan()
        weak['pattern']['effect'] = {'kind': 'truth', 'symbol': 'ownership_zero',
                                     'value': True}
        with self.assertRaisesRegex(ValueError, 'V ownership'):
            check_address_plan(weak, ELEMENTS)
        weak = plan()
        weak['symbols']['zero_address']['sort'] = 'bool'
        with self.assertRaisesRegex(ValueError, 'P relation'):
            check_address_plan(weak, ELEMENTS)

    def test_guard_absence_context_is_not_recipient_identity(self):
        self.assertIsNotNone(ZERO_INPUT.search(
            'The recipient specified for the transfer is address(0).'))
        self.assertIsNone(ZERO_INPUT.search(
            'No upstream validation blocks the zero-address recipient.'))
        elements = copy.deepcopy(ELEMENTS)
        elements['statements'].append({
            'id': 'a_guard', 'kind': 'assumption',
            'text': 'No upstream validation blocks the zero-address recipient.'})
        candidate = plan()
        candidate['precondition_terms'].append({
            'source_id': 'a_guard',
            'predicate': {'kind': 'truth', 'symbol': 'no_upstream_check',
                          'value': True}})
        check_address_plan(candidate, elements)

    def test_v311_targeted_retry(self):
        weak, good = copy.deepcopy(plan()), plan()
        weak['pattern']['condition'] = {
            'kind': 'truth', 'symbol': 'transfer_to_zero', 'value': True}
        calls = []

        def fake_extract(payload, output, model, prompt):
            calls.append(prompt)
            return weak if len(calls) == 1 else good

        with tempfile.TemporaryDirectory() as work, \
                patch.object(pipeline, 'synthesize_id_formalization', return_value={}):
            candidate, _, _ = pipeline.request_formalization(
                '{}', prompts.formal_prompt('ids', 'core'), 'synthetic', Path(work), 1,
                True, ELEMENTS, extract_fn=fake_extract, address_guard=True)
        self.assertIs(candidate, good)
        self.assertEqual(len(calls), 2)
        self.assertIn('Do not use a Boolean placeholder', calls[1])


if __name__ == '__main__':
    unittest.main()
