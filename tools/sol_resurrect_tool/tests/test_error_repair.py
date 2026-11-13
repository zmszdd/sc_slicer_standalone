import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import main


class ZeroArgErrorRepairTest(unittest.TestCase):
    def test_expands_zero_arg_error_to_revert_site(self):
        code = (
            'error OwnableInvalidOwner();\n'
            'error SafeERC20FailedOperation();\n'
            'contract C {\n'
            '  function f(address token) internal {\n'
            '    revert OwnableInvalidOwner(address(0));\n'
            '    revert SafeERC20FailedOperation(address(token));\n'
            '  }\n'
            '}\n'
        )
        new, changes = main._repair_zero_arg_custom_errors(code)
        self.assertIn('error OwnableInvalidOwner(address arg0);', new)
        self.assertIn('error SafeERC20FailedOperation(address arg0);', new)
        self.assertTrue(changes)

    def test_nested_cast_preserved(self):
        code = (
            'error E();\n'
            'contract C { function f() internal { revert E(address(0)); } }\n'
        )
        new, _ = main._repair_zero_arg_custom_errors(code)
        self.assertIn('error E(address arg0);', new)

    def test_no_revert_site_keeps_declaration(self):
        code = 'error E();\ncontract C {}'
        new, changes = main._repair_zero_arg_custom_errors(code)
        self.assertEqual(new, code)
        self.assertEqual(changes, [])


if __name__ == '__main__':
    unittest.main()


class ModifierAndKeywordRepairTest(unittest.TestCase):
    def test_drops_placeholder_modifier_when_real_exists(self):
        code = (
            'contract A {\n'
            '  modifier onlyOwner() { require(msg.sender == owner); _; }\n'
            '}\n'
            'contract B is A {\n'
            '  modifier onlyOwner() { _; }  // Placeholder modifier\n'
            '  function f() onlyOwner public {}\n'
            '}\n'
        )
        new, changes = main._repair_duplicate_placeholder_modifiers(code)
        self.assertNotIn('// Placeholder modifier', new)
        self.assertTrue(changes)

    def test_renames_keyword_param_only_when_it_is_a_name(self):
        code = ('contract C {\n'
                '  function toBytes32(address address) internal pure '
                'returns (bytes32 result) { return bytes32(uint160(address)); }\n'
                '}\n')
        new, changes = main._repair_keyword_param_names(code)
        self.assertIn('function toBytes32(address _address)', new)
        self.assertEqual(len(changes), 1)

    def test_leaves_returns_clause_untouched(self):
        code = ('contract C {\n'
                '  function f() internal view returns (bytes calldata) '
                '{ return msg.data; }\n'
                '}\n')
        new, changes = main._repair_keyword_param_names(code)
        self.assertEqual(new, code)
        self.assertEqual(changes, [])


if __name__ == '__main__':
    unittest.main()
