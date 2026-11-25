import json
import tempfile
import unittest
from pathlib import Path

from lib.observable_ir import (
    _direct_state_decls, _function_bodies, audit_binding, build_contract,
    select_typed_top)


SOURCE = '''
contract Asset {
    uint256 public totalAssets;
    bool public paused;

    function totalSupply() external view returns (uint256) {
        return totalAssets;
    }
}

contract Vault {
    Asset public asset;
    uint256 public shares;
    bool public frozen;

    function convertToShares(uint256 amount) external view returns (uint256) {
        return amount;
    }

    function setShares(uint256 amount) external {
        shares = amount;
    }
}

contract C4PoC {
    Vault public vault;

    function testExploit() external {
        require(!vault.frozen());
    }
}
'''

TYPED_SCOPE_SOURCE = '''
struct RedBlackTree {
    uint256 tree;
}

library TreeLib {
    function size(RedBlackTree storage tree) internal view returns (uint256) {
        return tree.tree;
    }
}

struct Book {
    RedBlackTree bidTree;
    RedBlackTree askTree;
}

contract PerpsBook {
    function processAmend(Book storage ds, uint256 amount) internal {
        uint256 depth = ds.askTree.size();
        uint256 bidDepth = ds.bidTree.size();
        uint256 amount_after = amount;
    }
}
'''


class ObservableIRTest(unittest.TestCase):
    def test_structural_scan_ignores_braces_in_comments_and_strings(self):
        source = '''
contract Vault {
    // note { with ; and }
    string public label = "{;}";
    uint256 public immutable maxNumLimitsPerSide;

    function read() external view returns (uint256) {
        return maxNumLimitsPerSide;
    }
}
'''
        decls = _direct_state_decls(source, 'Vault')
        self.assertEqual(decls.get('maxNumLimitsPerSide'), 'uint256')
        bodies = dict(_function_bodies(source, 'Vault'))
        self.assertIn('maxNumLimitsPerSide', bodies.get('read', ''))

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.src = self.root / 'src'
        self.src.mkdir()
        (self.src / 'Contract.sol').write_text(SOURCE)
        stage2 = self.root / 'stage2'
        stage2.mkdir()
        claim_id = 'c1'
        symbols = [
            {'symbol': 'shares_after', 'appears_in': ['I'],
             'meaning': 'vault shares after the action', 'checkpoint': 'after'},
            {'symbol': 'total_assets', 'appears_in': ['I'],
             'meaning': 'vault total assets', 'checkpoint': 'before'},
            {'symbol': 'frozen_changed', 'appears_in': ['V'],
             'meaning': 'vault frozen state changed', 'checkpoint': 'after'},
            {'symbol': 'impossible_signal', 'appears_in': ['V'],
             'meaning': 'zzzz no matching code fact', 'checkpoint': 'after'},
        ]
        (stage2 / 'constraints.json').write_text('{}')
        (stage2 / 'formalization.json').write_text(json.dumps({
            'symbols': {row['symbol']: {'sort': 'bool'} for row in symbols},
            'claims': [{'id': claim_id, 'properties': {
                'preconditions': {'expression': {'var': symbols[0]['symbol']}},
                'safety': {'expression': {'var': symbols[0]['symbol']}},
                'effects': {'expression': {'var': symbols[0]['symbol']}},
            }}],
        }))
        (stage2 / 'stage3-spec.json').write_text(json.dumps({'claims': [{
            'claim_id': claim_id,
            'formalization_status': 'formalized_candidate',
            'binding_contract': {'symbols': symbols},
        }]}))
        self.stage2 = stage2
        self.claim_id = claim_id

    def test_state_getter_and_cross_contract_candidates(self):
        ir = build_contract(self.stage2, self.claim_id, self.src)
        self.assertEqual(ir['injection_contract'], 'C4PoC')
        self.assertEqual(ir['symbol_table']['state_types']['shares'],
                         'uint256')
        self.assertTrue(ir['symbol_table']['mutation_sites']['shares'])
        shares = ir['symbols']['shares_after']
        self.assertIn('vault.shares', [row['expression']
                                       for row in shares['candidates']])
        cross = next(row for row in shares['candidates']
                     if row['expression'] == 'vault.shares')
        self.assertEqual(cross['receiver_type'], 'Vault')
        self.assertTrue(cross['mutation_sites'])
        assets = ir['symbols']['total_assets']
        expressions = [row['expression'] for row in assets['candidates']]
        self.assertIn('vault.asset.totalAssets', expressions)
        self.assertIn('vault.asset.totalSupply()', expressions)

    def test_unmatched_symbol_is_low_observability(self):
        ir = build_contract(self.stage2, self.claim_id, self.src)
        row = ir['symbols']['impossible_signal']
        self.assertEqual(row['observability'], 'low')
        self.assertFalse(row['candidates'])
        self.assertTrue(row['unobservable_reason'])

    def test_typed_selector_removes_contradictory_top_candidate(self):
        rows = [
            {'expression': 'flag', 'solidity_type': 'bool'},
            {'expression': 'shares', 'solidity_type': 'uint256'},
        ]
        selected = select_typed_top(rows, {
            'sort': 'uint256', 'meaning': 'share count'})
        self.assertEqual([row['expression'] for row in selected], ['shares'])

    def test_test_function_parameter_is_typed_function_scope_candidate(self):
        (self.src / 'Contract.sol').write_text(SOURCE.replace(
            'function testExploit() external {',
            'function testExploit(uint256 amount, bool shouldFreeze) external {'))
        symbols = [
            {'symbol': 'amount_value', 'appears_in': ['P'],
             'meaning': 'amount value in the exploit', 'checkpoint': 'before'},
            {'symbol': 'freeze_flag', 'appears_in': ['P'],
             'meaning': 'whether to freeze', 'checkpoint': 'before'},
        ]
        (self.stage2 / 'stage3-spec.json').write_text(json.dumps({'claims': [{
            'claim_id': self.claim_id,
            'formalization_status': 'formalized_candidate',
            'binding_contract': {'symbols': symbols},
        }]}))
        ir = build_contract(self.stage2, self.claim_id, self.src)
        amount = ir['symbols']['amount_value']['candidates']
        frozen = ir['symbols']['freeze_flag']['candidates']
        self.assertTrue(any(row['kind'] == 'parameter'
                            and row['expression'] == 'amount'
                            and row['solidity_type'] == 'uint256'
                            for row in amount))
        self.assertTrue(any(row['kind'] == 'parameter'
                            and row['expression'] == 'shouldFreeze'
                            and row['solidity_type'] == 'bool'
                            for row in frozen))

    def test_audit_warns_for_expression_outside_ir_but_allows_declared_roots(self):
        ir = build_contract(self.stage2, self.claim_id, self.src)
        binding = {'bindings': {
            'shares_after': {'solidity_expr': 'shares'},
            'total_assets': {'solidity_expr': 'ghost.member'},
        }}
        audit = audit_binding(binding, ir,
                              declared_roots={'ghost', 'shares'})
        self.assertTrue(audit['ok'])
        self.assertEqual(audit['problems'], [])
        binding['bindings']['total_assets']['solidity_expr'] = 'unknown.member'
        audit = audit_binding(binding, ir, declared_roots={'shares'})
        self.assertTrue(any(row['symbol'] == 'total_assets'
                            for row in audit['problems']))

    def test_audit_rejects_known_type_mismatch(self):
        ir = build_contract(self.stage2, self.claim_id, self.src)
        binding = {'bindings': {
            'shares_after': {'kind': 'numeric_value',
                             'solidity_expr': 'vault.frozen'},
        }}
        audit = audit_binding(binding, ir)
        self.assertFalse(audit['ok'])
        self.assertTrue(any(row['code'] == 'BINDING_TYPE_MISMATCH'
                            for row in audit['problems']))

    def test_audit_rejects_unmatched_overload_arity(self):
        ir = build_contract(self.stage2, self.claim_id, self.src)
        binding = {'bindings': {
            'shares_after': {'kind': 'numeric_value',
                             'solidity_expr': 'vault.convertToShares()'},
        }}
        audit = audit_binding(binding, ir)
        self.assertFalse(audit['ok'])
        self.assertTrue(any(row['code'] == 'BINDING_OVERLOAD_ARITY'
                            for row in audit['problems']))

    def test_equal_top_candidates_are_marked_ambiguous(self):
        (self.src / 'Contract.sol').write_text(SOURCE.replace(
            'uint256 public shares;',
            'uint256 public shares;\nuint256 public liquidityA;\n'
            'uint256 public liquidityB;'))
        symbols = [{'symbol': 'liquidity_value', 'appears_in': ['I'],
                    'meaning': 'liquidity value', 'checkpoint': 'after'}]
        (self.stage2 / 'stage3-spec.json').write_text(json.dumps({'claims': [{
            'claim_id': self.claim_id,
            'formalization_status': 'formalized_candidate',
            'binding_contract': {'symbols': symbols},
        }]}))
        (self.stage2 / 'formalization.json').write_text(json.dumps({
            'symbols': {'liquidity_value': {'sort': 'uint256'}},
            'claims': [{'id': self.claim_id, 'properties': {
                'preconditions': {'expression': {'var': 'liquidity_value'}},
                'safety': {'expression': {'var': 'liquidity_value'}},
                'effects': {'expression': {'var': 'liquidity_value'}},
            }}],
        }))
        ir = build_contract(self.stage2, self.claim_id, self.src)
        row = ir['symbols']['liquidity_value']
        self.assertTrue(row['ambiguous'])
        self.assertEqual(row['observability'], 'medium')
        self.assertTrue(all(candidate.get('ambiguous')
                            for candidate in row['candidates']
                            if candidate['match_score'] ==
                            row['candidates'][0]['match_score']))

    def _set_typed_scope_case(self, symbols):
        (self.src / 'Contract.sol').write_text(TYPED_SCOPE_SOURCE)
        (self.stage2 / 'stage3-spec.json').write_text(json.dumps({'claims': [{
            'claim_id': self.claim_id,
            'formalization_status': 'formalized_candidate',
            'binding_contract': {'symbols': symbols},
        }]}))
        (self.stage2 / 'formalization.json').write_text(json.dumps({
            'symbols': {row['symbol']: {'sort': 'uint256'} for row in symbols},
            'claims': [{'id': self.claim_id, 'properties': {
                'preconditions': {'expression': {'var': symbols[0]['symbol']}},
                'safety': {'expression': {'var': symbols[0]['symbol']}},
                'effects': {'expression': {'var': symbols[0]['symbol']}},
            }}],
        }))

    def test_business_function_parameter_grounds_typed_member_chain(self):
        symbols = [{
            'symbol': 'ask_depth_after', 'appears_in': ['I'],
            'meaning': 'ask tree size after amend',
            'checkpoint': 'after', 'binding_kind': 'numeric_value',
        }]
        self._set_typed_scope_case(symbols)
        ir = build_contract(
            self.stage2, self.claim_id, self.src,
            injection_contract='PerpsBook',
            injection_function='processAmend')
        row = ir['symbols']['ask_depth_after']
        candidate = next(item for item in row['candidates']
                         if item['expression'] == 'ds.askTree.size()')
        self.assertEqual(candidate['scope'], 'business_function_scope')
        self.assertEqual(candidate['contract'], 'PerpsBook')
        self.assertEqual(candidate['function'], 'processAmend')
        self.assertEqual(candidate['solidity_type'], 'uint256')
        self.assertEqual(candidate['receiver_type'], 'Book')
        self.assertTrue(candidate['visible_at_injection'])
        self.assertTrue(candidate['ready_eligible'])
        self.assertEqual(row['observability'], 'high')

    def test_probe_and_patch_targets_are_separate_visibility_domains(self):
        symbols = [{
            'symbol': 'ask_depth_after', 'appears_in': ['I'],
            'meaning': 'ask tree size after amend',
            'checkpoint': 'after', 'binding_kind': 'numeric_value',
        }]
        self._set_typed_scope_case(symbols)
        source = (self.src / 'Contract.sol').read_text()
        (self.src / 'Contract.sol').write_text(source + '''
contract ProbeTest {
    function testProbe() external {}
}
''')
        ir = build_contract(
            self.stage2, self.claim_id, self.src,
            probe_contract='ProbeTest', probe_function='testProbe',
            patch_contract='PerpsBook', patch_function='processAmend')
        candidate = next(item for item in ir['symbols']['ask_depth_after'][
            'candidates'] if item['expression'] == 'ds.askTree.size()')
        self.assertEqual(ir['probe_contract'], 'ProbeTest')
        self.assertEqual(ir['patch_contract'], 'PerpsBook')
        self.assertFalse(candidate['visible_at_probe'])
        self.assertTrue(candidate['visible_at_injection'])
        self.assertTrue(candidate['ready_eligible'])

    def test_direct_getter_wins_same_score_tie_over_source_chain(self):
        (self.src / 'Contract.sol').write_text('''
contract FeeSource {
    uint256 public feeBufferBPS;

    function charge(uint256 fee) external {
        uint256 bufferedFee = fee;
    }
}
''')
        symbols = [{
            'symbol': 'buffered_fee', 'appears_in': ['I'],
            'meaning': 'buffered fee charged to the user',
            'checkpoint': 'before', 'binding_kind': 'numeric_value',
        }]
        (self.stage2 / 'stage3-spec.json').write_text(json.dumps({'claims': [{
            'claim_id': self.claim_id,
            'formalization_status': 'formalized_candidate',
            'binding_contract': {'symbols': symbols},
        }]}))
        ir = build_contract(
            self.stage2, self.claim_id, self.src,
            probe_contract='FeeSource', probe_function='charge')
        row = ir['symbols']['buffered_fee']
        getter = next(item for item in row['candidates']
                      if item['expression'] == 'feeBufferBPS')
        self.assertFalse(getter['ambiguous'])
        self.assertTrue(getter['ready_eligible'])
        self.assertEqual(row['recipe_plan']['status'], 'ready')

    def test_business_scope_chain_is_not_ready_in_test_frame(self):
        symbols = [{
            'symbol': 'ask_depth_after', 'appears_in': ['I'],
            'meaning': 'ask tree size after amend',
            'checkpoint': 'after', 'binding_kind': 'numeric_value',
        }]
        self._set_typed_scope_case(symbols)
        ir = build_contract(
            self.stage2, self.claim_id, self.src,
            injection_contract='PerpsBook',
            injection_function='differentFunction')
        candidate = next(item for item in ir['symbols']['ask_depth_after'][
            'candidates'] if item['expression'] == 'ds.askTree.size()')
        self.assertFalse(candidate['visible_at_injection'])
        self.assertFalse(candidate['ready_eligible'])
        self.assertEqual(ir['symbols']['ask_depth_after']['observability'],
                         'medium')

    def test_equal_bid_and_ask_tree_chains_remain_ambiguous(self):
        symbols = [{
            'symbol': 'tree_depth_after', 'appears_in': ['I'],
            'meaning': 'tree size after amend',
            'checkpoint': 'after', 'binding_kind': 'numeric_value',
        }]
        self._set_typed_scope_case(symbols)
        ir = build_contract(
            self.stage2, self.claim_id, self.src,
            injection_contract='PerpsBook',
            injection_function='processAmend')
        row = ir['symbols']['tree_depth_after']
        self.assertTrue(row['ambiguous'])
        self.assertEqual(row['observability'], 'medium')
        self.assertTrue({'ds.askTree.size()', 'ds.bidTree.size()'}
                        <= set(row['top_candidate_expressions']))

    def test_test_local_is_not_reclassified_as_business_scope(self):
        test_dir = self.root / 'test'
        test_dir.mkdir()
        (test_dir / 'Probe.t.sol').write_text('''
contract ProbeTest {
    function testProbe() external {
        uint256 leakedProbeValue = 1;
    }
}

contract LaterTest {
    function testLater() external {
        uint256 laterValue = 2;
    }
}
''')
        symbols = [{
            'symbol': 'leaked_probe_value', 'appears_in': ['P'],
            'meaning': 'probe local value', 'checkpoint': 'before',
            'binding_kind': 'numeric_value',
        }]
        self._set_typed_scope_case(symbols)
        ir = build_contract(
            self.stage2, self.claim_id, self.src,
            injection_contract='ProbeTest',
            injection_function='testProbe')
        candidate = next(item for item in ir['symbols']['leaked_probe_value'][
            'candidates'] if item['expression'] == 'leakedProbeValue')
        self.assertEqual(candidate['scope'], 'function_scope')
        self.assertNotEqual(candidate['scope'], 'business_function_scope')
        self.assertTrue(candidate['visible_at_injection'])

    def test_audit_requires_business_scope_patch_function_match(self):
        symbols = [{
            'symbol': 'ask_depth_after', 'appears_in': ['I'],
            'meaning': 'ask tree size after amend',
            'checkpoint': 'after', 'binding_kind': 'numeric_value',
        }]
        self._set_typed_scope_case(symbols)
        ir = build_contract(
            self.stage2, self.claim_id, self.src,
            injection_contract='PerpsBook',
            injection_function='processAmend')
        binding = {
            'patch': {'contract': 'PerpsBook',
                      'functions': [{'name': 'processAmend'}]},
            'bindings': {'ask_depth_after': {
                'kind': 'numeric_value',
                'solidity_expr': 'ds.askTree.size()',
            }},
        }
        audit = audit_binding(binding, ir)
        self.assertTrue(audit['ok'])
        binding['patch']['functions'] = [{'name': 'otherFunction'}]
        audit = audit_binding(binding, ir)
        self.assertFalse(audit['ok'])
        self.assertTrue(any(row['code'] == 'BINDING_SCOPE_MISMATCH'
                            for row in audit['problems']))


if __name__ == '__main__':
    unittest.main()
