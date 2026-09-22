"""Offline checks for explicit P-bound preservation and targeted retry."""
from decimal import Decimal
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from fidelity import check_numeric_plan, explicit_bounds, explicit_numbers
import semantic_pipeline as pipeline
from prompts.versions import semantic_prompts_v310 as prompts


ELEMENTS = {'statements': [
    {'id': 'p_limit', 'kind': 'precondition',
     'text': 'The offset18 parameter is smaller than 1e9.'},
    {'id': 'p_state', 'kind': 'precondition',
     'text': 'The user has a deposit.'},
]}


def plan(predicate):
    return {'precondition_terms': [
        {'source_id': 'p_limit', 'predicate': predicate},
        {'source_id': 'p_state',
         'predicate': {'kind': 'truth', 'symbol': 'has_deposit', 'value': True}}]}


class NumericFidelityTests(unittest.TestCase):
    def test_number_and_direction_are_preserved(self):
        self.assertEqual(explicit_bounds('OFFSET18 < 1e18 and ratio at least 2'),
                         {('lt', 10**18), ('ge', 2)})
        check_numeric_plan(plan({'kind': 'comparison', 'left': 'offset18',
                         'operator': 'lt', 'right': {'const': 1000000000}}), ELEMENTS)
        check_numeric_plan(plan({'kind': 'comparison', 'left': {'const': 1000000000},
                         'operator': 'gt', 'right': 'offset18'}), ELEMENTS)

    def test_boolean_placeholder_or_weakened_bound_rejected(self):
        with self.assertRaisesRegex(ValueError, 'hidden'):
            check_numeric_plan(plan({'kind': 'truth', 'symbol': 'low_offset', 'value': True}),
                       ELEMENTS)
        with self.assertRaisesRegex(ValueError, 'literal or direction changed'):
            check_numeric_plan(plan({'kind': 'comparison', 'left': 'offset18',
                             'operator': 'lt', 'right': {'const': 10**18}}), ELEMENTS)
        with self.assertRaisesRegex(ValueError, 'literal or direction changed'):
            check_numeric_plan(plan({'kind': 'comparison', 'left': 'offset18',
                             'operator': 'le', 'right': {'const': 10**9}}), ELEMENTS)

    def test_power_of_two_bound_is_exact(self):
        elements = {'statements': [{
            'id': 'p_power', 'kind': 'precondition',
            'text': 'The supported supply is below 2^127 - 1.',
        }]}
        self.assertEqual(explicit_bounds(elements['statements'][0]['text']),
                         {('lt', 2**127 - 1)})
        candidate = {'precondition_terms': [{
            'source_id': 'p_power',
            'predicate': {
                'kind': 'comparison', 'left': 'supply', 'operator': 'lt',
                'right': {'power_of_two': 127, 'offset': -1},
            },
        }]}
        check_numeric_plan(candidate, elements)

    def test_unqualified_exact_literal_cannot_be_replaced(self):
        elements = {'statements': [{
            'id': 'p_order', 'kind': 'precondition',
            'text': 'A user submits an order to buy 100.5 ether.',
        }]}
        self.assertEqual(explicit_numbers(elements['statements'][0]['text']),
                         {Decimal('100.5')})
        # JSON plans accept integer constants only, so an unsupported decimal report
        # quantity must not be silently rounded to a different integer.
        bad = {'precondition_terms': [{
            'source_id': 'p_order',
            'predicate': {'kind': 'comparison', 'left': 'amount', 'operator': 'le',
                          'right': {'const': 101}},
        }]}
        with self.assertRaisesRegex(ValueError, 'numeric P literal changed'):
            check_numeric_plan(bad, elements)

    def test_comma_separated_literal_is_one_number(self):
        self.assertEqual(explicit_numbers('Epoch length is 1,209,600 seconds.'),
                         {Decimal(1209600)})

    def test_protocol_identifiers_are_not_numeric_constraints_in_v317(self):
        text = 'The wallet supports ERC-4337 and EIP-191.'
        self.assertEqual(explicit_numbers(text), {Decimal(4337), Decimal(191)})
        self.assertEqual(explicit_numbers(text, exclude_protocol_identifiers=True), set())
        elements = {'statements': [{
            'id': 'p_standard', 'kind': 'precondition', 'text': text,
        }]}
        candidate = {'precondition_terms': []}
        check_numeric_plan(candidate, elements, exclude_protocol_identifiers=True)

    def test_v310_retries_only_bad_numeric_plan(self):
        weak = plan({'kind': 'truth', 'symbol': 'low_offset', 'value': True})
        good = plan({'kind': 'comparison', 'left': 'offset18', 'operator': 'lt',
                     'right': {'const': 10**9}})
        calls = []

        def fake_extract(payload, output, model, prompt):
            calls.append(prompt)
            return weak if len(calls) == 1 else good

        with tempfile.TemporaryDirectory() as work, \
                patch.object(pipeline, 'synthesize_id_formalization', return_value={}):
            candidate, _, _ = pipeline.request_formalization(
                '{}', prompts.formal_prompt('ids', 'core'), 'synthetic', Path(work), 1,
                True, ELEMENTS, extract_fn=fake_extract, numeric_guard=True)
        self.assertIs(candidate, good)
        self.assertEqual(len(calls), 2)
        self.assertIn('SAME literal and comparison direction', calls[1])


if __name__ == '__main__':
    unittest.main()
