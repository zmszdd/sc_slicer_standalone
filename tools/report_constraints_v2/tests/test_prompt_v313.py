"""Local controls for compound qualifiers and proportional relations."""
import unittest

import z3

from plan_synthesizer import _predicate, _pattern_expressions
import report_only as r
from prompts.versions import semantic_prompts_v312 as previous
from prompts.versions import semantic_prompts_v313 as current


class PromptV313Tests(unittest.TestCase):
    def setUp(self):
        self.symbols = {
            'direct_call': {'sort': 'bool', 'unit': None},
            'funds_present': {'sort': 'bool', 'unit': None},
            'approval': {'sort': 'bool', 'unit': None},
            'minted': {'sort': 'int', 'unit': 'share'},
            'assets_before': {'sort': 'int', 'unit': 'asset'},
            'deposit': {'sort': 'int', 'unit': 'asset'},
            'supply_before': {'sort': 'int', 'unit': 'share'},
        }

    @staticmethod
    def truth(name):
        return {'kind': 'truth', 'symbol': name, 'value': True}

    def test_compound_condition_preserves_two_qualifiers(self):
        condition = {'kind': 'all_of', 'terms': [
            self.truth('direct_call'), self.truth('funds_present')]}
        safety, violation = _pattern_expressions({
            'kind': 'condition_forbids_effect', 'condition': condition,
            'effect': self.truth('approval')}, self.symbols)
        self.assertEqual(r.expr_type(safety, self.symbols), ('bool', None))
        variables = {name: z3.Bool(name) for name in ('direct_call', 'funds_present', 'approval')}
        solver = z3.Solver()
        solver.add(r.lower(violation, variables), z3.Not(variables['direct_call']))
        self.assertEqual(str(solver.check()), 'unsat')

    def test_product_relation_has_matching_derived_units(self):
        relation = {'kind': 'relation', 'operator': 'ge',
                    'left': {'op': 'mul', 'args': [
                        {'symbol': 'minted'}, {'symbol': 'assets_before'}]},
                    'right': {'op': 'mul', 'args': [
                        {'symbol': 'deposit'}, {'symbol': 'supply_before'}]}}
        expression = _predicate(relation, self.symbols)
        self.assertEqual(r.expr_type(expression, self.symbols), ('bool', None))
        self.assertEqual(expression['args'][0]['op'], 'mul')
        variables = {name: z3.Int(name) for name in (
            'minted', 'assets_before', 'deposit', 'supply_before')}
        solver = z3.Solver()
        solver.add(variables['minted'] == 50, variables['assets_before'] == 100,
                   variables['deposit'] == 100, variables['supply_before'] == 100,
                   r.lower(expression, variables))
        self.assertEqual(str(solver.check()), 'unsat')

    def test_product_relation_rejects_mismatched_units(self):
        bad = {'kind': 'relation', 'operator': 'ge',
               'left': {'op': 'mul', 'args': [
                   {'symbol': 'minted'}, {'symbol': 'supply_before'}]},
               'right': {'op': 'mul', 'args': [
                   {'symbol': 'deposit'}, {'symbol': 'supply_before'}]}}
        with self.assertRaisesRegex(ValueError, 'types/units|type/unit'):
            _predicate(bad, self.symbols)

    def test_new_prompt_does_not_mutate_v312(self):
        self.assertNotIn('"kind":"all_of"', previous.FORMAL_PLAN_PROMPT)
        text = current.formal_prompt('ids', 'core')
        self.assertIn('semantic-v3.13', text)
        self.assertIn('"kind":"all_of"', text)
        self.assertIn('"kind":"relation"', text)
        self.assertIn('attack_steps MUST contain action IDs only', current.ID_ELEMENT_PROMPT)
        self.assertIn('Do not add placeholder', current.ID_ELEMENT_PROMPT)


if __name__ == '__main__':
    unittest.main()
