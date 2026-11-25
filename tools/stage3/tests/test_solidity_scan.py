import unittest
import json
import tempfile
from pathlib import Path

from lib.solidity_scan import (base_identifiers, expr_identifiers,
                               _strip_comments_and_strings,
                               is_snapshot_identifier, scan_src,
                               contract_state_vars,
                               contract_visible_state_vars,
                               contract_instances,
                               poc_test_contract, poc_test_function,
                               poc_test_function_for_case,
                               contract_has_function)

E2E_SRC = Path(__file__).resolve().parents[1] / 'cases' / 'panoptic_builder_init_e2e' / 'src'


class SolidityScanTest(unittest.TestCase):
    def test_scan_e2e_contracts_and_functions(self):
        if not E2E_SRC.is_dir():
            self.skipTest('optional e2e fixture is not present')
        index = scan_src(E2E_SRC)
        declared = index.all_declared()
        for name in ('BuilderWallet', 'BuilderFactory', 'Create2Lib', 'IERC20',
                     'init', 'sweep', 'deployBuilder', 'predictBuilderWallet',
                     'builderAdmin'):
            self.assertIn(name, declared)

    def test_base_identifiers_drop_members_and_call_args(self):
        self.assertEqual(base_identifiers('msg.sender'), {'msg'})
        self.assertEqual(base_identifiers('balances[msg.sender]'), {'balances'})
        self.assertEqual(
            base_identifiers('IERC20(token).balanceOf(address(this))'), {'IERC20'})
        self.assertEqual(base_identifiers('builderAdmin == address(attacker)'),
                         {'builderAdmin', 'address'})
        self.assertEqual(base_identifiers('!(x) || (y)'), {'x', 'y'})
        self.assertEqual(base_identifiers('uint256(x)'), {'uint256'})

    def test_expr_identifiers_and_snapshot(self):
        self.assertEqual(expr_identifiers('a + b * c'), ['a', 'b', 'c'])
        self.assertTrue(is_snapshot_identifier('stage3_balance_before'))
        self.assertFalse(is_snapshot_identifier('balances'))

    def test_visible_state_vars_include_inherited(self):
        src = (
            'contract Base { uint256 gHybr; }\n'
            'contract Harness is Base { uint256 local; }\n'
            'contract C4PoC is Harness { function test_x() external {} }\n'
        )
        self.assertEqual(contract_state_vars(src, 'C4PoC'), set())
        self.assertIn('gHybr', contract_visible_state_vars(src, 'C4PoC'))
        self.assertIn('local', contract_visible_state_vars(src, 'C4PoC'))

    def test_contract_instances_include_inherited_harness_state(self):
        src = (
            'contract Vault { uint256 public total; }\n'
            'contract Base { Vault public vault; }\n'
            'contract C4PoC is Base { function test_x() external {} }\n'
        )
        self.assertEqual(contract_instances(src, 'C4PoC'),
                         {'vault': 'Vault'})

    def test_poc_test_contract_detection(self):
        src = (
            'contract A { function test_a() external {} }\n'
            'contract B { function test_b() external {} }\n'
            'contract C { function setUp() public {} }\n'
        )
        self.assertEqual(poc_test_contract(src), 'B')

    def test_poc_test_contract_none(self):
        self.assertIsNone(poc_test_contract('contract A { function f() {} }'))

    def test_poc_test_function_detection(self):
        src = (
            'contract A { function test_a() external {} }\n'
            'contract C4PoC is A { function test_inflationAttack() external {} }'
        )
        self.assertEqual(poc_test_function(src), ('C4PoC', 'test_inflationAttack'))

    def test_local_manifest_prefers_report_poc_over_neutral_entrypoint(self):
        src = (
            'contract C4PoC { function test_realBug() external { x(); } }\n'
            'contract Neutral_x is C4PoC { function test_entrypoint() public '
            '{ require(true, "neutral stage1 entrypoint"); } }'
        )
        self.assertEqual(poc_test_function(src), ('Neutral_x', 'test_entrypoint'))
        self.assertEqual(poc_test_function(src, ignore_neutral=True),
                         ('C4PoC', 'test_realBug'))
        with tempfile.TemporaryDirectory() as tmp:
            case_dir = Path(tmp)
            (case_dir / 'harness-manifest.json').write_text(json.dumps({
                'local_runnable': True}))
            self.assertEqual(poc_test_function_for_case(case_dir, src),
                             ('C4PoC', 'test_realBug'))

    def test_contract_has_function(self):
        src = 'contract A { function test_x() external {} }\ncontract B {}'
        self.assertTrue(contract_has_function(src, 'A', 'test_x'))
        self.assertFalse(contract_has_function(src, 'B', 'test_x'))

    def test_comment_stripping_preserves_source_offsets(self):
        src = ('// header\n'
               'contract A { string s = "x"; /* note */\n'
               '  function f() external { uint256 n = 1; }\n'
               '}\n')
        clean = _strip_comments_and_strings(src)
        self.assertEqual(len(clean), len(src))
        self.assertEqual(clean.count('\n'), src.count('\n'))
        self.assertTrue(contract_has_function(src, 'A', 'f'))


if __name__ == '__main__':
    unittest.main()


class FileLevelStateVarsTest(unittest.TestCase):
    def test_file_level_constant_is_not_contract_scoped(self):
        from lib.solidity_scan import file_level_state_vars
        src = '''uint256 constant SIG_OK = 0;
contract A { uint256 internal x; }
contract B { function f() external {} }
'''
        self.assertIn('SIG_OK', file_level_state_vars(src))
        self.assertNotIn('x', file_level_state_vars(src))

    def test_file_level_function_not_counted_as_state_var(self):
        from lib.solidity_scan import file_level_state_vars
        src = '''function helper(uint256 v) pure returns (uint256) { return v; }
contract A { uint256 internal x; }
'''
        self.assertNotIn('helper', file_level_state_vars(src))


class OwnerLookupTest(unittest.TestCase):
    def test_function_owner_and_state_var_owner(self):
        from lib.solidity_scan import function_owner, state_var_owner
        src = ('uint256 constant SIG_OK = 0;\n'
               'contract A {\n function f() external {}\n uint256 internal x;\n }\n'
               'contract B {\n function f() external {}\n }\n')
        self.assertEqual(function_owner(src, 'f'), {'A', 'B'})
        self.assertEqual(state_var_owner(src, 'x'), {'A'})
        self.assertIn(None, state_var_owner(src, 'SIG_OK'))

    def test_file_level_function_owner(self):
        from lib.solidity_scan import function_owner
        src = ('function helper(uint256 v) pure returns (uint256) { return v; }\n'
               'contract A { function g() external {} }\n')
        self.assertEqual(function_owner(src, 'helper'), {None})
