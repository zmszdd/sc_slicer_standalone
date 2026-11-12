import unittest

from lib.rebind import parse_source_signatures, rebind_binding


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
