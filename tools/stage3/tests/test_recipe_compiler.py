import unittest

from lib.recipe_compiler import compile_binding


def _ir(recipes, **row):
    record = {'recipe_plan': {'recipes': recipes}}
    record.update(row)
    return {'symbols': {'s1': record}}


def _recipe(expression, *, recipe_id, confidence='high',
            statements=None):
    return {
        'recipe_id': recipe_id,
        'expression': expression,
        'executable': True,
        'confidence': confidence,
        'solidity_stmts': statements or [],
        'evidence': ['typed code fact'],
    }


class RecipeCompilerTest(unittest.TestCase):
    def test_compiles_unbound_symbol_from_unique_recipe(self):
        binding = {'bindings': {'s1': {'solidity_expr': 'UNBOUND'}}}
        ir = _ir([_recipe('vault.shares()', recipe_id='s1:direct:0',
                          statements=['uint256 x = vault.shares();'])])
        result, changes = compile_binding(binding, ir)
        self.assertEqual(result['bindings']['s1']['solidity_expr'],
                         'vault.shares()')
        self.assertEqual(result['bindings']['s1']['solidity_stmts'],
                         ['uint256 x = vault.shares();'])
        self.assertEqual(changes[0]['recipe_id'], 's1:direct:0')
        self.assertEqual(binding['bindings']['s1']['solidity_expr'],
                         'UNBOUND')

    def test_keeps_existing_binding(self):
        binding = {'bindings': {'s1': {'solidity_expr': 'manual()'}}}
        ir = _ir([_recipe('vault.shares()', recipe_id='s1:direct:0')])
        result, changes = compile_binding(binding, ir)
        self.assertEqual(result['bindings']['s1']['solidity_expr'],
                         'manual()')
        self.assertEqual(changes, [])

    def test_competing_recipes_are_not_guessed(self):
        binding = {'bindings': {'s1': {'solidity_expr': 'UNBOUND'}}}
        ir = _ir([
            _recipe('a()', recipe_id='s1:direct:0'),
            _recipe('b()', recipe_id='s1:direct:1'),
        ])
        result, changes = compile_binding(binding, ir)
        self.assertEqual(result['bindings']['s1']['solidity_expr'],
                         'UNBOUND')
        self.assertEqual(changes, [])

    def test_unique_medium_recipe_compiles_when_fully_grounded(self):
        recipe = _recipe('vault.shares()', recipe_id='s1:direct:0',
                         confidence='medium')
        recipe.update({'solidity_type': 'uint256', 'checkpoint': 'after',
                       'visible_at_injection': True,
                       'source_grounded': True, 'ambiguous': False})
        binding = {'bindings': {'s1': {'solidity_expr': 'UNBOUND'}}}
        ir = _ir([recipe], binding_kind='numeric_value',
                 checkpoint='after')
        result, changes = compile_binding(binding, ir)
        self.assertEqual(result['bindings']['s1']['solidity_expr'],
                         'vault.shares()')
        self.assertEqual(changes[0]['confidence'], 'medium')

    def test_recipe_hidden_at_patch_target_is_not_compiled(self):
        recipe = _recipe('probeValue', recipe_id='s1:direct:0')
        recipe.update({'solidity_type': 'uint256',
                       'visible_at_injection': False})
        binding = {'bindings': {'s1': {'solidity_expr': 'UNBOUND'}}}
        ir = _ir([recipe], binding_kind='numeric_value')
        result, changes = compile_binding(binding, ir)
        self.assertEqual(result['bindings']['s1']['solidity_expr'], 'UNBOUND')
        self.assertEqual(changes, [])

    def test_checkpoint_mismatch_is_not_compiled(self):
        recipe = _recipe('total', recipe_id='s1:direct:0')
        recipe.update({'solidity_type': 'uint256', 'checkpoint': 'after',
                       'visible_at_injection': True})
        binding = {'bindings': {'s1': {'solidity_expr': 'UNBOUND'}}}
        ir = _ir([recipe], binding_kind='numeric_value',
                 checkpoint='before')
        result, changes = compile_binding(binding, ir)
        self.assertEqual(result['bindings']['s1']['solidity_expr'], 'UNBOUND')
        self.assertEqual(changes, [])


if __name__ == '__main__':
    unittest.main()
