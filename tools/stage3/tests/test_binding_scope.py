import tempfile
import unittest
from pathlib import Path

from lib.binding_scope import (from_anchor, from_binding, merge)


SOURCE = '''
contract Vault {
    uint256 public total;
    function deposit(uint256 amount) external { total += amount; }
}

contract ProbeTest {
    function testExploit() external { new Vault().deposit(1); }
}
'''

CALL_SLICE_SOURCE = '''
contract Vault {
    bool public flag;
    function postLimitOrder(uint256 amount) external {
        _executeAskLimitOrder(amount);
    }
    function _executeAskLimitOrder(uint256 amount) internal {
        if (amount > 0) flag = true;
    }
}

contract ProbeTest {
    function testExploit() external { new Vault().postLimitOrder(1); }
}
'''


class BindingScopeTest(unittest.TestCase):
    def test_business_target_is_recovered_from_binding_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            case = Path(tmp)
            (case / 'src').mkdir()
            (case / 'src' / 'Contract.sol').write_text(SOURCE)
            binding = {
                'patch': {'file': 'Contract.sol', 'contract': 'ProbeTest',
                          'functions': [{'name': 'testExploit'}]},
                'probe': {'contract': 'ProbeTest',
                          'exploit_test': 'testExploit'},
                'bindings': {
                    'deposit_amount': {
                        'source': 'Contract.sol:deposit',
                        'checkpoint': 'before',
                        'solidity_expr': 'amount',
                    },
                },
            }
            scope = from_binding(case, binding)
        self.assertEqual(scope['probe_contract'], 'ProbeTest')
        self.assertEqual(scope['probe_function'], 'testExploit')
        self.assertEqual(scope['patch_contract'], 'Vault')
        self.assertEqual(scope['patch_functions'], ['deposit'])

    def test_anchor_contract_is_used_for_new_bindings(self):
        self.assertEqual(from_anchor({'suggested_patch_contract': 'Vault'}),
                         {'patch_contract': 'Vault'})
        self.assertEqual(from_anchor({}), {})

    def test_call_slice_links_patch_target_to_binding_source_function(self):
        with tempfile.TemporaryDirectory() as tmp:
            case = Path(tmp)
            (case / 'src').mkdir()
            (case / 'src' / 'Contract.sol').write_text(CALL_SLICE_SOURCE)
            binding = {
                'patch': {'file': 'Contract.sol', 'contract': 'ProbeTest',
                          'functions': [{'name': 'postLimitOrder'}]},
                'probe': {'contract': 'ProbeTest',
                          'exploit_test': 'testExploit'},
                'bindings': {
                    'limit_amount': {
                        'source': 'Contract.sol:_executeAskLimitOrder',
                        'checkpoint': 'before',
                        'solidity_expr': 'amount',
                    },
                },
            }
            scope = from_binding(case, binding)
        self.assertEqual(scope['patch_contract'], 'Vault')
        self.assertEqual(scope['call_slices'], [
            ['postLimitOrder', '_executeAskLimitOrder']])
        self.assertEqual(scope['patch_functions'], [
            '_executeAskLimitOrder', 'postLimitOrder'])

    def test_merge_keeps_later_non_empty_values(self):
        merged = merge({'patch_contract': 'Vault', 'probe_function': None},
                       {'patch_contract': 'Other'}, None)
        self.assertEqual(merged, {'patch_contract': 'Other'})


if __name__ == '__main__':
    unittest.main()
