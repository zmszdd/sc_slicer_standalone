import unittest
from pathlib import Path

from lib.spec_loader import load_stage2_run
from lib.binding import load_binding, validate_binding
from lib.patch import (_render_expr, _snapshot_decls, function_has_halt,
                       function_has_stop, function_has_selfdestruct,
                       _rewrite_stop_globally, inject_patched_sources,
                       injection_has_halt, injection_selfdestruct_targets,
                       local_decl_statements, relocate_before_snapshots,
                       _contract_region, _function_body)

CASE = Path(__file__).resolve().parents[1] / 'cases' / 'mint_supply'


class PatchInjectionTest(unittest.TestCase):
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
        self.assertIn('assert(!((stage3_supply_before) >= (stage3_balance_before))', source)
        self.assertIn('(totalSupply) >= (balanceOf[to])', source)


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

    def test_contract_region_abstract_contract(self):
        source = 'abstract contract A { uint x; }'
        start, end = _contract_region(source, 'A')
        self.assertEqual(start, source.index('{'))
        self.assertEqual(end, source.index('}'))


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
