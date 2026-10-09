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

    def test_hex_slot_identifiers_are_not_numeric_bounds(self):
        # prompt_live3/live4_blind_01 Monetrix: the storage-slot identifier
        # 0x811 was parsed as the literal 2065, so direction-correct ge-0
        # predicates were rejected as "numeric P literal changed".  A 0x
        # prefix marks a protocol/slot identifier, not a semantic bound;
        # the fix direction was pre-registered in the live-3 report and the
        # family threshold (>= 2 independent cases) was met in live-4.
        text = 'The 0x811 user state holds supply.value and borrow.value.'
        self.assertEqual(explicit_numbers(text), set())
        self.assertEqual(explicit_bounds(text), set())
        # A real hex bound stated with a comparator is still enforced.
        self.assertEqual(explicit_bounds('The cap is >= 0x1000.'),
                         {('ge', Decimal(4096))})
        elements = {'statements': [{
            'id': 'p_slot', 'kind': 'precondition', 'text': text,
        }]}
        candidate = {'precondition_terms': [
            {'source_id': 'p_slot',
             'predicate': {'kind': 'comparison', 'left': 'borrow_value',
                           'operator': 'ge', 'right': {'const': 0}}},
        ]}
        check_numeric_plan(candidate, elements)

    def test_comparison_word_zero_grounds_const_zero(self):
        # final_holdout_02 GTE_Perps: "Accrued fees are greater than zero
        # (fee0=1e16 ...)" -- the statement's comparison constant IS zero, but
        # explicit_numbers saw only the parenthetical 1e16, so a faithful
        # "> 0" predicate was rejected as "numeric P literal changed" and the
        # case died as "local repair made no change". A comparison-context
        # "zero" must ground a const 0.
        text = ('Accrued fees are greater than zero '
                '(fee0=1e16, fee1=1e16 after the swaps).')
        self.assertEqual(explicit_numbers(text),
                         {Decimal(0), Decimal('1E+16')})
        elements = {'statements': [{
            'id': 'p_fees', 'kind': 'precondition', 'text': text,
        }]}
        candidate = {'precondition_terms': [
            {'source_id': 'p_fees',
             'predicate': {'kind': 'comparison', 'left': 'accrued_fee0',
                           'operator': 'gt', 'right': {'const': 0}}},
        ]}
        check_numeric_plan(candidate, elements)

    def test_rhetorical_and_address_zero_are_not_numeric_bounds(self):
        # The word "zero" alone is not always a number: "effectively zero" is
        # rhetoric (prompt_live4 Intuition), and "zero address" / "address(0)"
        # name the address sentinel (prompt_live4 Hybra: the 0 inside
        # address(0) was parsed as a literal and demanded numeric encoding of
        # an address assumption). Compound words never match either.
        self.assertEqual(explicit_numbers(
            'No special privileges are required; the cost is effectively zero.'),
            set())
        self.assertEqual(explicit_numbers(
            'A GaugeCL with rHYBR == address(0).'), set())
        self.assertEqual(explicit_numbers(
            'The balance is nonzero; the vault was zeroed.'), set())
        # An explicit numeric statement of zero stays a fact the plan must
        # encode (archive prompt_v320 SukukFi: totalAssets() returns zero).
        self.assertEqual(explicit_numbers(
            'totalAssets() returns zero by design.'), {Decimal(0)})

    def test_relax_assumptions_exempts_unencoded_assumption_numbers(self):
        # prompt_live1_blind_01: Kinetiq/Intuition were rejected because a
        # narrative assumption restating numbers (or naming a chain constant)
        # was not itself encoded as a P predicate.
        elements = {'statements': [
            {'id': 'p_interval', 'kind': 'precondition',
             'text': 'The oracle updates at most every 24 hours.'},
            {'id': 'asm_narrative', 'kind': 'assumption',
             'text': 'The 1-hour fast oracle versus the 24-hour slow oracle '
                     'creates a front-running window; blocks are 2 seconds.'},
        ]}
        candidate = {'precondition_terms': [
            {'source_id': 'p_interval',
             'predicate': {'kind': 'comparison', 'left': 'interval_hours',
                           'operator': 'eq', 'right': {'const': 24}}}]}
        with self.assertRaisesRegex(ValueError, 'source missing'):
            check_numeric_plan(candidate, elements)
        check_numeric_plan(candidate, elements, relax_assumptions=True)

    def test_relax_assumptions_never_reaches_preconditions_or_fidelity(self):
        elements = {'statements': [
            {'id': 'p_interval', 'kind': 'precondition',
             'text': 'The oracle updates at most every 24 hours.'},
            {'id': 'asm_narrative', 'kind': 'assumption',
             'text': 'Blocks are 2 seconds.'},
        ]}
        strict_precondition = {'precondition_terms': []}
        # Precondition literals stay mandatory even with the relief on.
        with self.assertRaisesRegex(ValueError, 'source missing'):
            check_numeric_plan(strict_precondition, elements, relax_assumptions=True)
        # An assumption that IS encoded still has its literals checked.
        changed_literal = {'precondition_terms': [
            {'source_id': 'p_interval',
             'predicate': {'kind': 'comparison', 'left': 'interval_hours',
                           'operator': 'le', 'right': {'const': 24}}},
            {'source_id': 'asm_narrative',
             'predicate': {'kind': 'comparison', 'left': 'block_seconds',
                           'operator': 'eq', 'right': {'const': 12}}}]}
        with self.assertRaisesRegex(ValueError, 'literal changed'):
            check_numeric_plan(changed_literal, elements, relax_assumptions=True)

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
