"""Fixed positive-divisor arithmetic remains typed, bounded, and executable."""
import unittest

import z3

from lib import report_only as r
from lib.plan_synthesizer import _predicate
from prompts.versions import semantic_prompts_v38 as prompts


SYMBOLS = {'duration_s': {'sort': 'int', 'unit': 'seconds'},
           'created': {'sort': 'bool', 'unit': None}}


class DivisibilityTests(unittest.TestCase):
    def test_nonmultiple_is_a_concrete_numeric_relation(self):
        predicate = _predicate({'kind': 'divisible_by', 'dividend': 'duration_s',
                                'divisor': 3600, 'value': False}, SYMBOLS)
        self.assertEqual(r.expr_type(predicate, SYMBOLS), ('bool', None))
        self.assertIn('mod', str(predicate))
        duration = z3.Int('duration_s')
        solver = z3.Solver()
        solver.add(duration == 5400, r.lower(predicate, {'duration_s': duration}))
        self.assertEqual(str(solver.check()), 'sat')
        solver.push(); solver.add(duration == 3600)
        self.assertEqual(str(solver.check()), 'unsat')

    def test_zero_and_negative_divisors_are_rejected(self):
        for divisor in (0, -1):
            with self.subTest(divisor=divisor), self.assertRaises(ValueError):
                _predicate({'kind': 'divisible_by', 'dividend': 'duration_s',
                            'divisor': divisor, 'value': True}, SYMBOLS)
            with self.subTest(divisor=divisor), self.assertRaises(ValueError):
                r.expr_type({'op': 'mod', 'args': [{'var': 'duration_s'},
                                                   {'const': divisor}]}, SYMBOLS)

    def test_non_integer_dividend_is_rejected(self):
        with self.assertRaises(ValueError):
            _predicate({'kind': 'divisible_by', 'dividend': 'created',
                        'divisor': 3600, 'value': True}, SYMBOLS)

    def test_old_prompt_untouched_and_new_prompt_has_guard(self):
        self.assertIn('TASK VERSION: semantic-v3.8', prompts.ID_ELEMENT_PROMPT)
        self.assertIn('A valid ID', prompts.ID_ELEMENT_PROMPT)
        self.assertIn('positive fixed integer divisor', prompts.FORMAL_PLAN_PROMPT)
        self.assertIn('divisible_by', prompts.formal_prompt('ids', 'core'))


if __name__ == '__main__':
    unittest.main()
