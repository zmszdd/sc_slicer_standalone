import unittest

from lib.codegen import expr_to_solidity


class CodegenTest(unittest.TestCase):
    def test_binary_and_implies(self):
        bindings = {'a': 'x', 'b': 'y > 0'}
        expr = {'op': 'implies', 'args': [
            {'op': 'and', 'args': [{'var': 'a'}, {'var': 'b'}]},
            {'op': 'not', 'args': [{'var': 'a'}]},
        ]}
        out = expr_to_solidity(expr, bindings)
        self.assertIn('(!((x) && (y > 0)) || (!(x)))', out)

    def test_numeric_sub(self):
        bindings = {'before': 'before', 'after': 'balances[msg.sender]'}
        expr = {'op': 'eq', 'args': [
            {'var': 'after'},
            {'op': 'sub', 'args': [{'var': 'before'}, {'const': 100}]},
        ]}
        self.assertEqual(
            '(balances[msg.sender]) == ((before) - (100))',
            expr_to_solidity(expr, bindings))

    def test_mul_div_mod_operators(self):
        bindings = {'a': 'x', 'b': 'y', 'c': 'z'}
        expr = {'op': 'mul', 'args': [
            {'var': 'a'},
            {'op': 'add', 'args': [{'var': 'b'}, {'var': 'c'}]},
        ]}
        self.assertEqual('(x) * ((y) + (z))',
                         expr_to_solidity(expr, bindings))

    def test_unbound_symbol(self):
        with self.assertRaises(ValueError):
            expr_to_solidity({'var': 'missing'}, {})


if __name__ == '__main__':
    unittest.main()
