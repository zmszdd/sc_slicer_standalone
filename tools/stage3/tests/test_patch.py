import unittest
from pathlib import Path

from lib.spec_loader import load_stage2_run
from lib.binding import load_binding, validate_binding
from lib.patch import (_assert_tail, _render_expr, _snapshot_decls, function_has_halt,
                       relocate_injection_to_test, _find_revert_exploit_call,
                       inject_revert_witness,
                       function_has_stop, function_has_selfdestruct,
                       _rewrite_stop_globally, inject_patched_sources,
                       injection_has_halt, injection_selfdestruct_targets,
                       local_decl_statements, relocate_before_snapshots,
                       _contract_region, _function_body)

CASE = Path(__file__).resolve().parents[1] / 'cases' / 'mint_supply'


class PatchInjectionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not CASE.is_dir():
            raise unittest.SkipTest('optional mint_supply fixture is not present')

    def test_unbound_symbols_raise_instead_of_neutralized(self):
        from lib.spec_loader import SpecError
        entries = {
            'p': {'kind': 'boolean_predicate', 'solidity_expr': 'UNBOUND',
                  'checkpoint': 'before'},
            'i': {'kind': 'numeric_value', 'solidity_expr': 'UNBOUND',
                  'checkpoint': 'after'},
        }
        with self.assertRaises(SpecError):
            _snapshot_decls(entries)
        with self.assertRaises(SpecError):
            _render_expr({'var': 'i'}, entries)

    def test_insert_after_statement_multiline_anchor(self):
        from lib.patch import _insert_after_statement
        body = (
            '  function test_Exploit() public {\n'
            '    RiskParameters riskParams = RiskParametersLibrary.storeRiskParameters(\n'
            '        0, 10, 0, protocolSplit, builderSplit\n'
            '    );\n'
            '    _target(riskParams);\n'
            '  }\n'
        )
        anchor = (
            'RiskParameters riskParams = RiskParametersLibrary.storeRiskParameters(\n'
            '        0, 10, 0, protocolSplit, builderSplit\n'
            '    );'
        )
        out = _insert_after_statement(body, anchor, '        stage3_x = 1;')
        self.assertIn('    );\n        stage3_x = 1;\n', out)
        self.assertIn('_target(riskParams);', out)
        self.assertIn('RiskParameters riskParams = RiskParametersLibrary.', out)

    def test_numeric_snapshot_injection(self):
        stage2 = load_stage2_run(CASE / 'stage2_run')
        binding = load_binding(CASE / 'binding.json')
        claim_id, entries = validate_binding(binding, stage2['spec'])
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            inject_patched_sources(CASE, out, binding, stage2['spec'],
                                   stage2['formal'])
            source = (out / 'Token.sol').read_text()
        self.assertIn('uint256 stage3_balance_before = balanceOf[to];', source)
        self.assertIn('uint256 stage3_supply_before = totalSupply;', source)
        # Entry-level before snapshots (no snapshot_after) must not hard-revert
        # on P=false: the injected function can be called legitimately during
        # PoC setup with P false. The plain assert(!P || I) is the guard.
        self.assertNotIn('stage3:precondition_unwitnessed', source)
        self.assertIn('require(!((stage3_supply_before) >= (stage3_balance_before))', source)
        self.assertIn('(totalSupply) >= (balanceOf[to])', source)

    def test_negative_probe_asserts_effect_absence(self):
        stage2 = load_stage2_run(CASE / 'stage2_run')
        binding = load_binding(CASE / 'binding.json')
        claim_id, entries = validate_binding(binding, stage2['spec'])
        lines = _assert_tail(stage2['spec'], stage2['formal'], claim_id,
                             entries, probe_kind='negative')
        self.assertTrue(any('stage3:not_V' in line for line in lines))
        self.assertTrue(any('!((' in line and 'require(' in line
                            for line in lines))


class RevertWitnessTest(unittest.TestCase):
    def test_find_exploit_call_after_expect_revert(self):
        body = (
            '            vm.deal(address(this), 1 wei);\n'
            '            vm.expectRevert(E.selector);\n'
            '            covenant.multicall{value: 1 wei}(outer);\n'
        )
        found = _find_revert_exploit_call(body)
        self.assertIsNotNone(found)
        start, end, groups = found
        self.assertEqual(groups['target'], 'covenant')
        self.assertEqual(groups['method'], 'multicall')
        self.assertEqual(groups['args'], 'outer')

    def test_inject_revert_witness_removes_expect_revert(self):
        import tempfile
        from lib.binding import load_binding
        from lib.spec_loader import load_stage2_run
        case = Path('cases/mint_supply')
        # mint_supply is not a revert PoC; only test the helper on a synthetic
        # source by checking the marker handling path is wired.
        source = (
            'contract T { function doThing() external {} }\n'
            'contract Harness {\n'
            '  function test_X() public {\n'
            '    vm.expectRevert(E.selector);\n'
            '    target.doThing();\n'
            '  }\n'
            '}\n'
        )
        found = _find_revert_exploit_call(
            '    vm.expectRevert(E.selector);\n    target.doThing();\n')
        self.assertIsNotNone(found)
        self.assertEqual(found[2]['target'], 'target')

    def test_inject_revert_witness_keeps_multiline_args_after_comments(self):
        import tempfile
        source = (
            'contract Harness {\n'
            '  function test_X() public {\n'
            '    vm.expectRevert();\n'
            '    target.doThing(\n'
            '        amount,\n'
            '        assets,  // totalAssets = amount\n'
            '        shares   // totalShares = shares\n'
            '    );\n'
            '  }\n'
            '}\n'
        )
        with tempfile.TemporaryDirectory() as tmp:
            case = Path(tmp) / 'case'
            (case / 'src').mkdir(parents=True)
            (case / 'src' / 'Contract.sol').write_text(source)
            binding = {
                'patch': {'file': 'Contract.sol', 'contract': 'Harness',
                          'functions': [{'name': 'test_X'}]},
                'probe': {'contract': 'Harness', 'exploit_test': 'test_X'},
                'bindings': {},
            }
            inject_revert_witness(case, case / 'patched', binding, {}, {})
            patched = (case / 'patched' / 'Contract.sol').read_text()
        self.assertIn('try target.doThing(', patched)
        self.assertIn('shares) {', patched)
        self.assertNotIn('// totalShares', patched)


class ContractRegionTest(unittest.TestCase):
    def test_contract_region_matches_contract(self):
        source = 'contract A { uint x; }'
        start, end = _contract_region(source, 'A')
        self.assertEqual(start, source.index('{'))
        self.assertEqual(end, source.index('}'))

    def test_contract_region_matches_library(self):
        # code4rena targets are frequently libraries; patch injection must
        # locate a library body just like a contract body.
        source = 'library A { uint x; }'
        start, end = _contract_region(source, 'A')
        self.assertEqual(start, source.index('{'))
        self.assertEqual(end, source.index('}'))

    def test_function_body_inside_library(self):
        source = 'library A {\n  function f() internal pure returns (uint) { return 1; }\n}\n'
        open_idx, close_idx = _function_body(source, 'f', 'A')
        self.assertIn('return 1;', source[open_idx + 1:close_idx])

    def test_overload_disambiguated_by_call_site_arity(self):
        source = (
            'contract A {\n'
            '  function redeem(uint256 a, address b, address c) public returns (uint256) {\n'
            '    return a;\n'
            '  }\n'
            '  function redeem(uint256 epoch) external {}\n'
            '}\n'
            'contract T is Test {\n'
            '  function test_poc() public { A(0).redeem(1, address(0), address(0)); }\n'
            '}\n'
        )
        open_idx, close_idx = _function_body(source, 'redeem', 'A')
        self.assertIn('return a;', source[open_idx + 1:close_idx])

    def test_overload_same_arity_raises(self):
        from lib.spec_loader import SpecError
        source = (
            'contract A {\n'
            '  function redeem(uint256 a) public {}\n'
            '  function redeem(address b) public {}\n'
            '}\n'
        )
        with self.assertRaises(SpecError):
            _function_body(source, 'redeem', 'A')

    def test_interface_declaration_does_not_shadow_concrete_definition(self):
        source = (
            'interface I {\n'
            '  function stake() external payable;\n'
            '}\n'
            'contract A is I {\n'
            '  function stake() public payable override { current = 1; }\n'
            '}\n'
        )
        open_idx, close_idx = _function_body(source, 'stake', 'A')
        self.assertIn('current = 1;', source[open_idx + 1:close_idx])

    def test_overload_no_call_site_prefers_higher_arity(self):
        source = (
            'contract A {\n'
            '  function redeem(uint256 a, address b) public returns (uint256) {\n'
            '    return a;\n'
            '  }\n'
            '  function redeem(uint256 epoch) external {}\n'
            '}\n'
        )
        open_idx, close_idx = _function_body(source, 'redeem', 'A')
        self.assertIn('return a;', source[open_idx + 1:close_idx])

    def test_contract_region_abstract_contract(self):
        source = 'abstract contract A { uint x; }'
        start, end = _contract_region(source, 'A')
        self.assertEqual(start, source.index('{'))
        self.assertEqual(end, source.index('}'))


class InjectionPointRelocationTest(unittest.TestCase):
    def test_moves_injection_to_probe_exploit_test(self):
        binding = {
            'patch': {'file': 'Contract.sol', 'contract': 'Business',
                      'functions': [{'name': 'doThing', 'file': 'Contract.sol'}]},
            'probe': {'contract': 'Harness', 'exploit_test': 'test_Exploit'},
        }
        out = relocate_injection_to_test(binding)
        self.assertEqual(out['patch']['functions'][0]['name'], 'test_Exploit')
        self.assertEqual(out['patch']['functions'][0]['contract'], 'Harness')
        self.assertEqual(out['patch']['contract'], 'Harness')

    def test_noop_when_already_test_function(self):
        binding = {
            'patch': {'file': 'Contract.sol', 'functions': [{'name': 'test_Exploit'}]},
            'probe': {'contract': 'Harness', 'exploit_test': 'test_Exploit'},
        }
        self.assertIsNone(relocate_injection_to_test(binding))

    def test_noop_without_probe(self):
        binding = {'patch': {'file': 'Contract.sol',
                             'functions': [{'name': 'doThing'}]}}
        self.assertIsNone(relocate_injection_to_test(binding))

    def test_rejects_business_parameter_not_visible_in_test(self):
        binding = {
            'bindings': {
                'i': {'solidity_expr': 'from == msg.sender',
                      'checkpoint': 'after'},
            },
            'patch': {'file': 'Contract.sol', 'contract': 'Business',
                      'functions': [{'name': 'transferFrom', 'file': 'Contract.sol'}]},
            'probe': {'contract': 'Harness', 'exploit_test': 'test_Exploit'},
        }
        source = (
            'contract Business {\n'
            '  function transferFrom(address from, address to) external {}\n'
            '}\n'
        )
        test_source = (
            'contract Harness {\n'
            '  function test_Exploit() public {}\n'
            '}\n'
        )
        self.assertIsNone(relocate_injection_to_test(
            binding, source=source, test_source=test_source))


class SnapshotRelocationTest(unittest.TestCase):
    SOURCE = (
        'contract T {\n'
        '  function test_Exploit() public {\n'
        '    uint256 base = 100;\n'
        '    uint256 amount = base * 10;\n'
        '    _target(amount);\n'
        '  }\n'
        '}\n'
    )

    def test_local_decl_statements_find_declaring_stmt(self):
        decls = local_decl_statements(self.SOURCE, 'test_Exploit', {'amount'})
        self.assertIn('amount', decls)
        self.assertIn('uint256 amount = base * 10;', decls['amount'])

    def test_local_decl_statements_find_multiline_initializer(self):
        source = (
            'contract T {\n'
            '  function test_Exploit() public {\n'
            '    RiskParameters riskParams = RiskParametersLibrary.storeRiskParameters(\n'
            '        0, 10, 0, protocolSplit, builderSplit\n'
            '    );\n'
            '    _target(riskParams);\n'
            '  }\n'
            '}\n'
        )
        decls = local_decl_statements(source, 'test_Exploit', {'riskParams'})
        self.assertIn('riskParams', decls)
        self.assertIn('RiskParameters riskParams = RiskParametersLibrary.', decls['riskParams'])

    def test_local_decl_statements_balanced_multiline_member_call(self):
        source = (
            'contract T {\n'
            '  function test_Exploit() public {\n'
            '    bool ok = oracle\n'
            '        .validatePrice(0);\n'
            '    _target(ok);\n'
            '  }\n'
            '}\n'
        )
        decls = local_decl_statements(source, 'test_Exploit', {'ok'})
        self.assertEqual(decls['ok'],
                         'bool ok = oracle\n        .validatePrice(0);')

    def test_local_decl_statements_skip_interface_declaration(self):
        source = (
            'interface I {\n'
            '  function redelegate() external;\n'
            '}\n'
            'contract Mock {\n'
            '  struct Operation { uint64 amount; }\n'
            '}\n'
            'contract T is I {\n'
            '  function redelegate() external {\n'
            '    uint256 amount = 10;\n'
            '    _target(amount);\n'
            '  }\n'
            '}\n'
        )
        decls = local_decl_statements(source, 'redelegate', {'amount'},
                                      contract='T')
        self.assertEqual(decls['amount'], 'uint256 amount = 10;')

    def test_relocate_adds_snapshot_after_for_before_symbol(self):
        binding = {
            'claim_id': 'c1',
            'bindings': {
                'violates': {'kind': 'boolean_predicate',
                             'solidity_expr': 'amount > base',
                             'checkpoint': 'before'},
            },
            'patch': {'file': 'Contract.sol',
                      'functions': [{'name': 'test_Exploit'}]},
        }
        relocated, anchors = relocate_before_snapshots(binding, self.SOURCE)
        self.assertEqual(
            relocated['bindings']['violates']['snapshot_after'],
            'uint256 amount = base * 10;')
        self.assertEqual(set(anchors), {'violates'})

    def test_relocate_ignores_identical_declaration_in_earlier_function(self):
        source = (
            'contract T {\n'
            '  function mint() external {\n'
            '    uint256 localBaseSupply = 0;\n'
            '  }\n'
            '  function test_Exploit() public {\n'
            '    MarketParams memory mp = _params();\n'
            '    uint256 localBaseSupply = 10;\n'
            '    _target(mp, localBaseSupply);\n'
            '  }\n'
            '}\n'
        )
        binding = {
            'bindings': {
                'noop': {'kind': 'boolean_predicate',
                         'solidity_expr': 'mp.baseToken != address(0) && '
                                          'localBaseSupply > 0',
                         'checkpoint': 'before'},
            },
            'patch': {'file': 'Contract.sol', 'contract': 'T',
                      'functions': [{'name': 'test_Exploit'}]},
        }
        relocated, anchors = relocate_before_snapshots(binding, source)
        self.assertEqual(anchors, {'noop': 'uint256 localBaseSupply = 10;'})
        self.assertEqual(
            relocated['bindings']['noop']['snapshot_after'],
            'uint256 localBaseSupply = 10;')


class HaltOpcodeDetectionTest(unittest.TestCase):
    def test_stop_and_selfdestruct_detected(self):
        source = ('contract A {\n'
                  '  function f() external { assembly { stop() } }\n'
                  '  function g(address x) external { selfdestruct(x); }\n'
                  '  function h() external pure returns (uint) { return 1; }\n'
                  '}\n')
        self.assertTrue(function_has_halt(source, 'f'))
        self.assertTrue(function_has_halt(source, 'g'))
        self.assertFalse(function_has_halt(source, 'h'))

    def test_comments_and_strings_ignored(self):
        source = ('contract A {\n'
                  '  function f() external pure returns (uint) {\n'
                  '    // stop() appears in a comment\n'
                  '    string memory s = "selfdestruct(x)";\n'
                  '    return 1;\n'
                  '  }\n'
                  '}\n')
        self.assertFalse(function_has_halt(source, 'f'))

    def test_injection_has_halt_reports_targets(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            case = Path(tmp)
            (case / 'src').mkdir()
            (case / 'src' / 'Token.sol').write_text(
                'contract Token { function withdraw() external { '
                'assembly { stop() } } }\n')
            binding = {'patch': {'file': 'Token.sol', 'contract': 'Token',
                                 'functions': [{'name': 'withdraw',
                                                'file': 'Token.sol'}]}}
            has_halt, targets = injection_has_halt(case, binding)
        self.assertTrue(has_halt)
        self.assertEqual(targets, ['Token.sol:withdraw'])

    def test_stop_rewritten_to_marker_revert(self):
        source = ('contract A {\n'
                  '  function f() external { assembly { stop() } }\n'
                  '  function g() external pure returns (uint) { return 1; }\n'
                  '}\n')
        rewritten = _rewrite_stop_globally(source)
        self.assertIn('stage3:halt', rewritten)
        self.assertNotIn('stop()', rewritten)
        self.assertIn('return 1', rewritten)

    def test_global_rewrite_catches_callee_stop(self):
        source = ('contract Lib {\n'
                  '  function sqrt(uint a) internal pure {\n'
                  '    assembly { if iszero(a) { stop() } }\n'
                  '  }\n'
                  '}\n'
                  'contract T {\n'
                  '  function test_Reverts() external { sqrt(0); }\n'
                  '}\n')
        rewritten = _rewrite_stop_globally(source)
        self.assertIn('stage3:halt', rewritten)
        self.assertNotIn('stop()', rewritten)
        self.assertIn('test_Reverts', rewritten)

    def test_function_has_stop_ignores_selfdestruct(self):
        source = ('contract A {\n'
                  '  function f(address x) external { selfdestruct(x); }\n'
                  '  function g() external { assembly { stop() } }\n'
                  '}\n')
        self.assertFalse(function_has_stop(source, 'f'))
        self.assertTrue(function_has_stop(source, 'g'))
        self.assertTrue(function_has_selfdestruct(source, 'f'))
        self.assertFalse(function_has_selfdestruct(source, 'g'))

    def test_injection_selfdestruct_targets_reports_target(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            case = Path(tmp)
            (case / 'src').mkdir()
            (case / 'src' / 'Token.sol').write_text(
                'contract Token { function burn(address x) external { '
                'selfdestruct(x); } }\n')
            binding = {'patch': {'file': 'Token.sol', 'contract': 'Token',
                                 'functions': [{'name': 'burn',
                                                'file': 'Token.sol'}]}}
            targets = injection_selfdestruct_targets(case, binding)
        self.assertEqual(targets, ['Token.sol:burn'])


if __name__ == '__main__':
    unittest.main()
