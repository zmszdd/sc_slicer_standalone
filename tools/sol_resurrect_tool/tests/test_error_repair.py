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


class MalformedFunctionSignatureRepairTest(unittest.TestCase):
    def test_repairs_payable_split_across_parameter_list(self):
        code = ('interface I {\n'
                '  function transferFee(ISiloVault _vault, address) '
                'payable _feeRecipient) external;\n'
                '  function sendValue(address) payable recipient, uint256 '
                'amount) internal {}\n'
                '}\n')
        new, changes = main._repair_malformed_function_signatures(code)
        self.assertIn(
            'function transferFee(ISiloVault _vault, address payable '
            '_feeRecipient) external;', new)
        self.assertIn(
            'function sendValue(address payable recipient, uint256 amount) '
            'internal {}', new)
        self.assertTrue(changes)

    def test_restores_terminator_before_next_interface_declaration(self):
        code = ('interface I {\n'
                '  function add(address _agent, address _minter)\n'
                '  function remove(address _agent, address _minter)\n'
                '  function value(address _agent) external view returns '
                '(uint256);\n'
                '}\n')
        new, changes = main._repair_malformed_function_signatures(code)
        self.assertIn('function add(address _agent, address _minter) external;',
                      new)
        self.assertIn(
            'function remove(address _agent, address _minter) external;', new)
        self.assertTrue(changes)


class MultilineAndStructuralRepairTest(unittest.TestCase):
    def test_restores_referenced_duplicate_constant(self):
        code = ('library SafePct {\n'
                '  // [DUPLICATE REMOVED] uint256 internal constant MAX_BIPS = 10_000;\n'
                '  function mulBips(uint256 x, uint256 y) internal pure returns (uint256) {\n'
                '    return x * y / MAX_BIPS;\n'
                '  }\n'
                '}\n')
        new = main._restore_referenced_duplicate_constants(code)
        self.assertIn('uint256 internal constant MAX_BIPS = 10_000;', new)
        self.assertNotIn('[DUPLICATE REMOVED]', new)

    def test_renames_keyword_parameter_in_multiline_signature(self):
        code = ('contract C {\n'
                '  function isOwner(\n'
                '    Agent.State storage _agent,\n'
                '    address address\n'
                '  ) internal view returns (bool) {\n'
                '    return address == _agent.owner;\n'
                '  }\n'
                '}\n')
        new, changes = main._repair_keyword_param_names(code)
        self.assertIn('address _address', new)
        self.assertTrue(changes)

    def test_renames_keyword_parameter_uses_in_function_body(self):
        code = ('contract C {\n'
                '  function f(address address) internal returns (uint256) {\n'
                '    return uint256(uint160(address));\n'
                '  }\n'
                '}\n')
        new, changes = main._repair_keyword_param_names(code)
        self.assertIn('address _address', new)
        self.assertIn('uint160(_address)', new)
        self.assertTrue(changes)

    def test_removes_indexed_from_function_parameter(self):
        code = ('interface I {\n'
                '  function addOwner(address indexed owner) external;\n'
                '}\n'
                'event OwnerAdded(address indexed owner);\n')
        new, changes = main._repair_keyword_param_names(code)
        self.assertIn('function addOwner(address owner) external;', new)
        self.assertIn('event OwnerAdded(address indexed owner);', new)
        self.assertTrue(changes)

    def test_restores_truncated_mapping_parameter(self):
        code = ('library L {\n'
                '  function f(\n'
                '    address _owner,\n'
                '    bool _flag,\n'
                '    uint256 bool) storage _flags\n'
                '  ) external {}\n'
                '}\n')
        new, changes = main._repair_malformed_function_signatures(code)
        self.assertIn('mapping(address => bool) storage _flags', new)
        self.assertTrue(changes)

    def test_adds_data_location_for_known_struct_parameter(self):
        code = ('struct Origin { uint32 srcEid; }\n'
                'contract C { function f(Origin value) public view returns '
                '(bool) { return true; } }\n')
        new, changes = main._ensure_external_data_locations(code)
        self.assertIn('Origin memory value', new)
        self.assertTrue(changes)

    def test_adds_data_location_for_internal_reference_parameter(self):
        code = ('contract C { function f(bytes data) internal {} }\n')
        new, changes = main._ensure_external_data_locations(code)
        self.assertIn('bytes memory data', new)
        self.assertTrue(changes)

    def test_adds_memory_to_struct_return_value(self):
        code = ('struct S { uint256 x; }\n'
                'interface I { function f() external view returns (S); }\n')
        new, changes = main._ensure_return_data_locations(code)
        self.assertIn('returns (S memory)', new)
        self.assertTrue(changes)

    def test_aligns_override_data_location_with_virtual_base(self):
        code = ('contract A { function f(bytes calldata data) internal virtual; }\n'
                'contract B is A {\n'
                '  function f(bytes memory data) internal virtual override {}\n'
                '}\n')
        new, changes = main._align_override_data_locations(code)
        self.assertIn('function f(bytes calldata data) internal virtual override',
                      new)
        self.assertTrue(changes)

    def test_removes_struct_field_with_missing_type(self):
        code = ('struct S {\n'
                '  constant status;\n'
                '  uint256 value;\n'
                '}\n')
        new, changes = main._remove_invalid_struct_fields(code)
        self.assertNotIn('constant status', new)
        self.assertIn('uint256 value', new)
        self.assertTrue(changes)

    def test_removes_indexed_token_from_struct_field(self):
        code = ('struct S {\n'
                '  indexed newRedemptionRequestId;\n'
                '  indexed uint256 kept;\n'
                '}\n')
        new, changes = main._remove_invalid_struct_fields(code)
        self.assertNotIn('indexed newRedemptionRequestId;', new)
        self.assertIn('uint256 kept;', new)
        self.assertTrue(changes)

    def test_downgrades_transient_state_variable(self):
        code = ('pragma solidity ^0.8.0;\n'
                'contract C { bool transient _lock; }\n')
        new = main._normalize_solidity_output(code)
        self.assertIn('bool _lock;', new)
        self.assertNotIn('bool transient', new)

    def test_recovers_contract_placeholder_used_as_struct(self):
        code = ('contract InboundPacket {}\n'
                'contract C {\n'
                '  function f(InboundPacket calldata packet) external {\n'
                '    uint32 eid = packet.dstEid;\n'
                '    bytes32 guid = packet.guid;\n'
                '  }\n'
                '}\n')
        new, changes = main._repair_placeholder_value_types(code)
        self.assertIn('struct InboundPacket {', new)
        self.assertIn('uint32 dstEid;', new)
        self.assertIn('bytes32 guid;', new)
        self.assertTrue(changes)

    def test_converts_local_calldata_variable_to_memory(self):
        code = ('contract C {\n'
                '  function f() external {\n'
                '    InboundPacket calldata packet = _packets[i];\n'
                '  }\n'
                '}\n')
        new, changes = main._repair_local_data_locations(code)
        self.assertIn('InboundPacket memory packet = _packets[i];', new)
        self.assertTrue(changes)

    def test_adds_memory_to_local_struct_variable(self):
        code = ('library Agent { struct Status { uint256 value; } }\n'
                'contract C {\n'
                '  function f() external view returns (bool) {\n'
                '    Agent.Status status = Agent.Status(0);\n'
                '    return status.value == 0;\n'
                '  }\n'
                '}\n')
        new, changes = main._ensure_local_struct_data_locations(code)
        self.assertIn('Agent.Status memory status =', new)
        self.assertTrue(changes)

    def test_expands_zero_arg_struct_constructor(self):
        code = ('struct TrackedTicket { uint256 id; int24 packedTicket; }\n'
                'contract C {\n'
                '  function f() external pure returns (TrackedTicket memory) {\n'
                '    return TrackedTicket();\n'
                '  }\n'
                '}\n')
        new, changes = main._expand_zero_arg_struct_constructors(code)
        self.assertIn('return TrackedTicket(0, 0);', new)
        self.assertTrue(changes)

    def test_adds_missing_scoped_state_struct(self):
        code = ('library L {\n'
                '  struct Ownership { address owner; }\n'
                '  function f(State storage state, bytes32 h) internal {\n'
                '    Ownership storage ownership = state.ownership[h];\n'
                '  }\n'
                '}\n')
        new, changes = main._ensure_missing_scoped_structs(code)
        self.assertIn('struct State {', new)
        self.assertIn('mapping(bytes32 => Ownership) ownership;', new)
        self.assertTrue(changes)

    def test_precedes_multiline_interface_base_before_derived(self):
        code = ('interface IDerived is\n'
                '    IBase,\n'
                '    IOther\n'
                '{\n'
                '  function f() external;\n'
                '}\n'
                'interface IBase { function g() external; }\n'
                'interface IOther { function h() external; }\n')
        new = main._ensure_base_contracts_precede_derived(code)
        self.assertLess(new.index('interface IBase'), new.index('interface IDerived'))
        self.assertLess(new.index('interface IOther'), new.index('interface IDerived'))

    def test_adds_missing_address_delegate_helper(self):
        code = ('library Address {\n'
                '  function functionCall(address target, bytes memory data) '
                'internal returns (bytes memory) { return data; }\n'
                '}\n'
                'contract C { function f() external { '
                'Address.functionDelegateCall(address(this), ""); } }\n')
        new = main._ensure_address_library_helpers(code)
        self.assertIn('function functionDelegateCall(', new)

    def test_adds_missing_qualified_error_used_by_revert(self):
        code = ('library Errors {\n'
                '  error InsufficientBalance(uint256 available, uint256 required);\n'
                '}\n'
                'contract C {\n'
                '  function f() external { revert Errors.FailedDeployment(); }\n'
                '}\n')
        new, changes = main._ensure_qualified_revert_errors(code)
        self.assertIn('error FailedDeployment();', new)
        self.assertTrue(changes)

    def test_repairs_qualified_error_argument_types(self):
        code = ('interface IMarket { }\n'
                'library ErrorsLib {\n'
                '  error SupplyCapExceeded(uint256 market);\n'
                '}\n'
                'contract C {\n'
                '  function f(IMarket market) external {\n'
                '    revert ErrorsLib.SupplyCapExceeded(market);\n'
                '  }\n'
                '}\n')
        new, changes = main._repair_qualified_error_arguments(code)
        self.assertIn('error SupplyCapExceeded(IMarket arg0);', new)
        self.assertTrue(changes)

    def test_adds_missing_qualified_event_used_by_emit(self):
        code = ('library EventsLib { }\n'
                'contract C {\n'
                '  function f(address user, uint256 amount) external {\n'
                '    emit EventsLib.Updated(user, amount);\n'
                '  }\n'
                '}\n')
        new, changes = main._ensure_qualified_emit_events(code)
        self.assertIn('event Updated(address arg0, uint256 arg1);', new)
        self.assertTrue(changes)

    def test_repairs_qualified_event_argument_types(self):
        code = ('library EventsLib {\n'
                '  event Updated(address arg0, uint256 arg1);\n'
                '}\n'
                'contract C {\n'
                '  function f(address payable user) external {\n'
                '    emit EventsLib.Updated(user, 1);\n'
                '  }\n'
                '}\n')
        new, changes = main._repair_qualified_event_arguments(code)
        self.assertIn('event Updated(address payable arg0, uint256 arg1);', new)
        self.assertTrue(changes)

    def test_repairs_require_qualified_zero_arg_error(self):
        code = ('library ErrorsLib { }\n'
                'contract C {\n'
                '  function f(address value) external {\n'
                '    require(value != address(0), ErrorsLib.ZeroAddress(hex""));\n'
                '  }\n'
                '}\n')
        new, changes = main._repair_require_custom_errors(code)
        self.assertIn('error ZeroAddress();', new)
        self.assertIn('ErrorsLib.ZeroAddress()', new)
        self.assertNotIn('hex""', new)
        self.assertTrue(changes)

    def test_infers_error_argument_types_from_call_site(self):
        code = ('struct Origin { uint32 srcEid; bytes32 sender; }\n'
                'error OnlyPeer(uint256, uint256);\n'
                'error InvalidOptions(uint256);\n'
                'contract C {\n'
                '  function f(Origin calldata origin, bytes calldata options) external {\n'
                '    revert OnlyPeer(origin.srcEid, origin.sender);\n'
                '    revert InvalidOptions(options);\n'
                '  }\n'
                '}\n')
        new, changes = main._repair_custom_error_arguments(code)
        self.assertIn('error OnlyPeer(uint32 arg0, bytes32 arg1);', new)
        self.assertIn('error InvalidOptions(bytes arg0);', new)
        self.assertTrue(changes)

    def test_infers_nearest_identifier_type_for_error_argument(self):
        code = ('error SafeCastOverflowedIntToUint(uint256 arg0);\n'
                'contract C {\n'
                '  function toUint8(uint256 value) internal pure returns (uint8) { '
                'return uint8(value); }\n'
                '  function toUint256(int256 value) internal pure returns (uint256) {\n'
                '    if (value < 0) revert SafeCastOverflowedIntToUint(value);\n'
                '    return uint256(value);\n'
                '  }\n'
                '}\n')
        new, changes = main._repair_custom_error_arguments(code)
        self.assertIn('error SafeCastOverflowedIntToUint(int256 arg0);', new)
        self.assertTrue(changes)

    def test_infers_error_argument_from_member_call_return_type(self):
        code = ('interface IPreCrime {\n'
                '  function buildSimulationResult() external view returns (bytes memory);\n'
                '}\n'
                'error SimulationResult(uint256 arg0);\n'
                'contract C {\n'
                '  function f() external {\n'
                '    revert SimulationResult('
                'IPreCrime(msg.sender).buildSimulationResult());\n'
                '  }\n'
                '}\n')
        new, changes = main._repair_custom_error_arguments(code)
        self.assertIn('error SimulationResult(bytes arg0);', new)
        self.assertTrue(changes)

    def test_infers_member_type_from_qualified_struct_declaration(self):
        code = ('library Redemption {\n'
                '  struct Request { address payable executor; }\n'
                '}\n'
                'contract C {\n'
                '  function f(Redemption.Request memory request) external {\n'
                '    emit E(request.executor);\n'
                '  }\n'
                '}\n')
        position = code.index('request.executor')
        inferred = main._infer_expression_type_at(
            'request.executor', code, position)
        self.assertEqual(inferred, 'address payable')

    def test_removes_placeholder_struct_conflicting_with_event(self):
        code = ('library EventsLib {\n'
                '  event SetIsAllocator(address indexed allocator, bool value);\n'
                '  struct SetIsAllocator { bytes data; }\n'
                '}\n')
        new, changes = main._remove_placeholder_structs_conflicting_with_errors(code)
        self.assertNotIn('struct SetIsAllocator', new)
        self.assertIn('event SetIsAllocator', new)
        self.assertTrue(changes)

    def test_marks_uninstantiated_contract_abstract_from_compiler_output(self):
        code = 'contract Titn is OFT { }\n'
        output = 'Contract "Titn" should be marked as abstract.'
        new, changes = main._mark_contracts_abstract_from_compiler_output(
            code, output)
        self.assertIn('abstract contract Titn', new)
        self.assertTrue(changes)

    def test_sanitizes_event_token_in_error_argument(self):
        code = 'error E(indexed arg0, public arg1, uint256 arg2);\n'
        new, changes = main._sanitize_error_argument_tokens(code)
        self.assertIn('error E(uint256 arg0, uint256 arg1, uint256 arg2);', new)
        self.assertTrue(changes)

    def test_error_argument_inference_ignores_event_indexed_prefix(self):
        code = ('event E(address indexed spender, uint256 value);\n'
                'function f(address spender) { revert X(spender); }\n')
        inferred = main._infer_expression_type_in_code('spender', code)
        self.assertEqual(inferred, 'address')

    def test_adds_missing_nested_qualified_type(self):
        code = ('interface IProof {}\n'
                'interface IVerifier { function verify(IProof.Proof calldata '
                'proof) external; }\n')
        new, changes = main._ensure_nested_qualified_types(code)
        self.assertIn('struct Proof { bytes data; }', new)
        self.assertTrue(changes)

    def test_wraps_orphan_interface_members_and_drops_unmatched_brace(self):
        code = ('contract C {}\n'
                'function mint(address recipient) external;\n'
                'function burn(uint256 id) external;\n'
                '}\n'
                'interface IERC20 { function totalSupply() external view '
                'returns (uint256); }\n')
        new, changes = main._wrap_orphan_top_level_prototypes(code)
        self.assertIn('interface _RecoveredInterface_1 {', new)
        self.assertIn('function mint(address recipient) external;', new)
        self.assertIn('interface IERC20 {', new)
        self.assertNotIn('\n}\n}\n', new)
        self.assertTrue(changes)

    def test_drops_orphan_event_parameter_fragment(self):
        code = ('interface I {}\n'
                '        address indexed owner,\n'
                '        uint256 indexed id);\n'
                'interface J { event Ok(address indexed owner); }\n')
        new, changes = main._wrap_orphan_top_level_prototypes(code)
        self.assertNotIn('address indexed owner,', new)
        self.assertIn('interface J { event Ok(address indexed owner); }', new)
        self.assertTrue(changes)

    def test_removes_unterminated_event_header(self):
        code = ('interface I {\n'
                '  event A(\n'
                '  event B(\n'
                '  event C(address indexed owner);\n'
                '}\n')
        new, changes = main._wrap_orphan_top_level_prototypes(code)
        self.assertNotIn('event A(', new)
        self.assertNotIn('event B(', new)
        self.assertIn('event C(address indexed owner);', new)
        self.assertTrue(changes)

    def test_removes_orphan_parameter_fragment_inside_interface(self):
        code = ('interface I {\n'
                '  event Ok(address indexed owner);\n'
                '  uint256 blockNumber,\n'
                '  uint256 timestamp);\n'
                '}\n')
        new, changes = main._wrap_orphan_top_level_prototypes(code)
        self.assertNotIn('uint256 blockNumber,', new)
        self.assertIn('event Ok(address indexed owner);', new)
        self.assertTrue(changes)

    def test_new_expression_does_not_downgrade_data_location_type_to_contract(self):
        from src.assembler import Assembler
        code = ('contract C {\n'
                '  function decode(bytes[] calldata data) external {\n'
                '    InboundPacket[] memory packets = new InboundPacket[](data.length);\n'
                '    InboundPacket calldata packet = packets[0];\n'
                '  }\n'
                '}\n')
        refs = Assembler()._extract_referenced_types(code)
        self.assertIn('InboundPacket', refs['structs'])
        self.assertNotIn('InboundPacket', refs['contracts'])


if __name__ == '__main__':
    unittest.main()
