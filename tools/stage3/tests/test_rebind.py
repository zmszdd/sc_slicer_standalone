import unittest

from lib.rebind import (parse_source_signatures, rebind_binding,
                        coerce_boolean_predicates, qualify_unqualified_calls)


class ParseSignaturesTest(unittest.TestCase):
    def test_function_and_struct_signatures(self):
        source = (
            'contract A {\n'
            '  function q(uint256 x) external view returns (uint256 a, uint256 b) {}\n'
            '  function s() public view returns (int256 total) {}\n'
            '  struct S { uint128 a; uint128 b; uint128 c; }\n'
            '  mapping(uint256 e => S) public states;\n'
            '}\n'
        )
        sigs = parse_source_signatures(source)
        self.assertEqual(sigs['functions']['q'][0]['returns'],
                         ['uint256', 'uint256'])
        self.assertEqual(sigs['functions']['s'][0]['returns'], ['int256'])
        self.assertEqual(sigs['mapping_getters']['states'], 'S')
        self.assertEqual([f['name'] for f in sigs['structs']['S']],
                         ['a', 'b', 'c'])


class RebindTest(unittest.TestCase):
    def _binding(self, bindings):
        return {'schema_version': 'stage3-binding/1', 'claim_id': 'x',
                'bindings': bindings}

    def test_tuple_comparison_destructures_first_component(self):
        binding = self._binding({
            'p': {'kind': 'boolean_predicate',
                  'solidity_expr': 'msg.value == messenger.q(returnTrip)',
                  'checkpoint': 'input', 'source': 'C.sol:f'},
        })
        source = 'function q(uint256 x) external view returns (uint256 a, uint256 b) {}\n'
        result, changes = rebind_binding(binding, source)
        expr = result['bindings']['p']['solidity_expr']
        self.assertIn('msg.value == __stage3_0_0', expr)
        self.assertTrue(result['bindings']['p'].get('solidity_stmts'))
        self.assertEqual(len(changes), 1)

    def test_tuple_member_access_uses_struct_field_index(self):
        binding = self._binding({
            'v': {'kind': 'boolean_predicate',
                  'solidity_expr': 'vault.states(epoch).c > 0',
                  'checkpoint': 'after', 'source': 'C.sol:f'},
        })
        source = (
            'struct S { uint128 a; uint128 b; uint128 c; }\n'
            'mapping(uint256 e => S) public states;\n')
        result, changes = rebind_binding(binding, source)
        expr = result['bindings']['v']['solidity_expr']
        self.assertIn('__stage3_0_2 > 0', expr)
        self.assertEqual(len(changes), 1)

    def test_signed_before_snapshot_typed(self):
        binding = self._binding({
            'n': {'kind': 'numeric_value',
                  'solidity_expr': 'accountant.s()',
                  'checkpoint': 'before', 'source': 'C.sol:f'},
        })
        source = 'function s() public view returns (int256 total) {}\n'
        result, changes = rebind_binding(binding, source)
        self.assertEqual(result['bindings']['n']['solidity_type'], 'int256')
        self.assertEqual(len(changes), 1)

    def test_zero_arg_array_length_repair(self):
        binding = self._binding({
            'p': {'kind': 'boolean_predicate',
                  'solidity_expr': 'manager.pools.length > 0',
                  'checkpoint': 'before', 'source': 'C.sol:f'},
        })
        source = (
            'function pools() external view returns (address[] memory);\n'
            'function pools(uint256 i) external view returns (address);\n')
        result, changes = rebind_binding(binding, source)
        self.assertEqual(result['bindings']['p']['solidity_expr'],
                         'manager.pools().length > 0')
        self.assertEqual(len(changes), 1)


if __name__ == '__main__':
    unittest.main()


class ComplementaryBindingTest(unittest.TestCase):
    def test_completes_derived_from_bound_reverts(self):
        from lib.rebind import complete_complementary_bindings
        binding = {
            'bindings': {
                'h_completes': {'solidity_expr': 'UNBOUND', 'kind': 'boolean_predicate'},
                'h_reverts': {'solidity_expr': 'true', 'kind': 'boolean_predicate'},
            },
        }
        contract = {'symbols': [
            {'symbol': 'h_completes', 'meaning': 'operation completes without reverting',
             'appears_in': ['I'], 'binding_kind': 'boolean_predicate'},
            {'symbol': 'h_reverts', 'meaning': 'operation reverts',
             'appears_in': ['V'], 'binding_kind': 'boolean_predicate'},
        ]}
        out, changes = complete_complementary_bindings(binding, contract)
        self.assertEqual(out['bindings']['h_completes']['solidity_expr'], '!(true)')
        self.assertTrue(changes)

    def test_no_mate_leaves_unbound(self):
        from lib.rebind import complete_complementary_bindings
        binding = {
            'bindings': {
                'h_completes': {'solidity_expr': 'UNBOUND', 'kind': 'boolean_predicate'},
                'h_reverts': {'solidity_expr': 'UNBOUND', 'kind': 'boolean_predicate'},
            },
        }
        contract = {'symbols': [
            {'symbol': 'h_completes', 'meaning': 'operation completes',
             'appears_in': ['I'], 'binding_kind': 'boolean_predicate'},
            {'symbol': 'h_reverts', 'meaning': 'operation reverts',
             'appears_in': ['V'], 'binding_kind': 'boolean_predicate'},
        ]}
        out, changes = complete_complementary_bindings(binding, contract)
        self.assertEqual(out['bindings']['h_completes']['solidity_expr'], 'UNBOUND')
        self.assertEqual(changes, [])


class ScalarSnapshotTypeTest(unittest.TestCase):
    def _binding(self, bindings):
        return {'schema_version': 'stage3-binding/1', 'claim_id': 'x',
                'bindings': bindings}

    def test_uint128_state_var_snapshot_typed(self):
        binding = self._binding({
            'n': {'kind': 'numeric_value',
                  'solidity_expr': 'reserve0',
                  'checkpoint': 'before', 'source': 'C.sol:f'},
        })
        source = 'uint128 public reserve0;\n'
        result, changes = rebind_binding(binding, source)
        self.assertEqual(result['bindings']['n']['solidity_type'], 'uint128')
        self.assertEqual(len(changes), 1)

    def test_single_return_address_call_typed(self):
        binding = self._binding({
            'n': {'kind': 'numeric_value',
                  'solidity_expr': 'vault.asset()',
                  'checkpoint': 'before', 'source': 'C.sol:f'},
        })
        source = 'function asset() public view returns (address) {}\n'
        result, changes = rebind_binding(binding, source)
        self.assertEqual(result['bindings']['n']['solidity_type'], 'address')
        self.assertEqual(len(changes), 1)

    def test_uint256_default_not_forced(self):
        binding = self._binding({
            'n': {'kind': 'numeric_value',
                  'solidity_expr': 'totalSupply',
                  'checkpoint': 'before', 'source': 'C.sol:f'},
        })
        source = 'uint256 public totalSupply;\n'
        result, changes = rebind_binding(binding, source)
        self.assertEqual(result['bindings']['n']['solidity_type'], 'uint256')


class StructGetterTest(unittest.TestCase):
    def test_struct_public_state_var_getter_destructures_member(self):
        binding = {'schema_version': 'stage3-binding/1', 'claim_id': 'x',
                   'bindings': {
                       'elapsed': {'kind': 'numeric_value',
                                   'solidity_expr':
                                       'block.timestamp - oracle.snapshotHistory().lastUpdated',
                                   'checkpoint': 'after', 'source': 'C.sol:f'}}}
        source = (
            'struct PriceSnapshot { uint256 cumulativePrice; '
            'uint256 lastUpdated; uint256 averagePrice; }\n'
            'contract BalancerPriceOracle { '
            'PriceSnapshot public snapshotHistory; }\n')
        result, changes = rebind_binding(binding, source)
        expr = result['bindings']['elapsed']['solidity_expr']
        self.assertIn('__stage3_0_1', expr)
        self.assertTrue(result['bindings']['elapsed'].get('solidity_stmts'))


class BoolCoerceTest(unittest.TestCase):
    def test_boolean_predicate_scalar_call_coerced(self):
        binding = {'schema_version': 'stage3-binding/1', 'claim_id': 'x',
                   'bindings': {
                       'distributed': {'kind': 'boolean_predicate',
                                       'solidity_expr': 'minter.update_period()',
                                       'checkpoint': 'after', 'source': 'C.sol:f'}}}
        source = 'function update_period() external returns (uint256 p) {}\n'
        result, changes = coerce_boolean_predicates(binding, source)
        self.assertEqual(result['bindings']['distributed']['solidity_expr'],
                         '((minter.update_period()) != 0)')
        self.assertEqual(len(changes), 1)

    def test_boolean_predicate_bool_call_untouched(self):
        binding = {'schema_version': 'stage3-binding/1', 'claim_id': 'x',
                   'bindings': {
                       'guard': {'kind': 'boolean_predicate',
                                 'solidity_expr': 'v._reentrancyGuardEntered()',
                                 'checkpoint': 'after', 'source': 'C.sol:f'}}}
        source = 'function _reentrancyGuardEntered() internal returns (bool b) {}\n'
        result, changes = coerce_boolean_predicates(binding, source)
        self.assertEqual(result['bindings']['guard']['solidity_expr'],
                         'v._reentrancyGuardEntered()')
        self.assertEqual(len(changes), 0)


class QualifyUnqualifiedCallTest(unittest.TestCase):
    def _binding(self, expr):
        return {
            'schema_version': 'stage3-binding/1',
            'claim_id': 'x',
            'probe': {'contract': 'Harness', 'exploit_test': 'test_X'},
            'bindings': {
                'p': {'kind': 'boolean_predicate', 'solidity_expr': expr,
                      'checkpoint': 'after', 'source': 'C.sol:f'},
            },
        }

    SOURCE = (
        'contract Oracle { function validatePrice(uint256 x) external view returns (bool) {} }\n'
        'contract Harness {\n'
        '  function test_X() public {\n'
        '    Oracle oracle = new Oracle();\n'
        '    bool ok = oracle.validatePrice(0);\n'
        '  }\n'
        '}\n'
    )

    def test_unique_probe_receiver_qualifies_call(self):
        result, changes = qualify_unqualified_calls(
            self._binding('validatePrice(0)'), self.SOURCE)
        self.assertEqual(result['bindings']['p']['solidity_expr'],
                         'oracle.validatePrice(0)')
        self.assertEqual(len(changes), 1)

    def test_qualified_call_is_untouched(self):
        result, changes = qualify_unqualified_calls(
            self._binding('oracle.validatePrice(0)'), self.SOURCE)
        self.assertEqual(result['bindings']['p']['solidity_expr'],
                         'oracle.validatePrice(0)')
        self.assertEqual(changes, [])

    def test_ambiguous_receivers_are_untouched(self):
        source = self.SOURCE.replace(
            '    bool ok = oracle.validatePrice(0);',
            '    bool ok = oracle.validatePrice(0);\n'
            '    bool ok2 = other.validatePrice(0);')
        result, changes = qualify_unqualified_calls(
            self._binding('validatePrice(0)'), source)
        self.assertEqual(result['bindings']['p']['solidity_expr'],
                         'validatePrice(0)')
        self.assertEqual(changes, [])

    def test_public_address_getter_receiver_qualifies(self):
        source = (
            'contract Wallet {\n'
            '  address public builderAdmin;\n'
            '}\n'
            'contract Harness {\n'
            '  function test_X() public {\n'
            '    address wallet = address(new Wallet());\n'
            '    address admin = Wallet(wallet).builderAdmin();\n'
            '  }\n'
            '}\n'
        )
        result, changes = qualify_unqualified_calls(
            self._binding('builderAdmin() != address(0)'), source)
        self.assertEqual(result['bindings']['p']['solidity_expr'],
                         'Wallet(wallet).builderAdmin() != address(0)')
        self.assertEqual(len(changes), 1)
