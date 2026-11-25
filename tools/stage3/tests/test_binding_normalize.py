import tempfile
import unittest
from pathlib import Path

from lib.binding_normalize import _previous_statement, normalize_binding

CASES = Path(__file__).resolve().parents[1] / 'cases'


class BindingNormalizeTest(unittest.TestCase):
    def _require_case(self, case):
        if not case.is_dir():
            self.skipTest(f'optional real-case fixture {case.name} is not present')

    def test_previous_statement_uses_balanced_statement_boundary(self):
        body = (
            '        vm.warp(block.timestamp + 1);\n'
            '        bool ok = oracle\n'
            '            .validatePrice(0);\n'
            '        assertTrue(ok);\n'
        )
        index = body.index('.validatePrice')
        self.assertEqual(_previous_statement(body, index),
                         'vm.warp(block.timestamp + 1);')

    def _merkl_binding(self, patch_contract, patch_function):
        return {
            'schema_version': 'stage3-binding/1',
            'claim_id': 'core_claim',
            'bindings': {
                'operator_allowance': {
                    'kind': 'numeric_value',
                    'solidity_expr':
                        'creator.creatorAllowance(alice, bob, address(rewardToken))',
                    'checkpoint': 'before',
                    'source': 'Contract.sol:testAllowanceBypass'},
                'campaign_amount': {
                    'kind': 'numeric_value', 'solidity_expr': '100',
                    'checkpoint': 'before', 'source': 'Contract.sol:testAllowanceBypass'},
                'allowance_decremented': {
                    'kind': 'boolean_predicate',
                    'solidity_expr':
                        'creator.creatorAllowance(alice, bob, address(rewardToken)) / 1 ether < 50',
                    'checkpoint': 'after', 'source': 'Contract.sol:testAllowanceBypass'},
            },
            'patch': {
                'file': 'Contract.sol', 'contract': patch_contract,
                'functions': [{'name': patch_function, 'file': 'Contract.sol'}]},
            'probe': {
                'contract': 'AllowanceBypassTest',
                'exploit_test': 'testAllowanceBypass', 'safety_test': None},
        }

    def test_redirects_wrong_injection_point(self):
        case = CASES / 'Merkl_T4ExvutBBXC__si6yAc4Sp6f__ZWh59mSfE3A'
        self._require_case(case)
        binding = self._merkl_binding('DistributionCreator', 'createCampaign')
        normalized, changes = normalize_binding(binding, case / 'src')
        self.assertTrue(changes)
        self.assertEqual(normalized['patch']['contract'], 'AllowanceBypassTest')
        self.assertEqual(normalized['patch']['functions'][0]['name'],
                         'testAllowanceBypass')

    def test_redirect_anchors_before_snapshots_at_exploit_call(self):
        case = (CASES /
                'SukukFi_syLyTBz5KNA__SZy2Ly7Y3Cu__5WuJ4CMVoB4')
        self._require_case(case)
        binding = {
            'bindings': {
                'victim_balance': {
                    'kind': 'numeric_value',
                    'solidity_expr': 'shareToken.balanceOf(user1)',
                    'checkpoint': 'before'},
                'attacker_authorized': {
                    'kind': 'boolean_predicate',
                    'solidity_expr':
                        'msg.sender == user1 || shareToken.allowance(user1, msg.sender) > 0',
                    'checkpoint': 'before'},
            },
            'patch': {
                'file': 'Contract.sol', 'contract': 'WERC7575Vault',
                'functions': [{'name': 'withdraw', 'file': 'Contract.sol'}]},
            'probe': {
                'contract': 'WERC7575VaultCoverageTests',
                'exploit_test': 'test_MissingCallerAuthorizationAllowsFundTheft'},
        }
        normalized, changes = normalize_binding(binding, case / 'src')
        self.assertTrue(any('anchored before exploit call' in c for c in changes))
        for entry in normalized['bindings'].values():
            self.assertEqual(entry['snapshot_after'], 'vm.startPrank(user2);')

    def test_keeps_correct_injection_point_unchanged(self):
        case = CASES / 'Merkl_T4ExvutBBXC__si6yAc4Sp6f__ZWh59mSfE3A'
        self._require_case(case)
        binding = self._merkl_binding('AllowanceBypassTest', 'testAllowanceBypass')
        original = binding['patch']
        normalized, changes = normalize_binding(binding, case / 'src')
        self.assertEqual(changes, [])
        self.assertEqual(normalized['patch'], original)

    def test_does_not_redirect_business_parameter_into_test_scope(self):
        source = (
            'contract Business {\n'
            '  function transferFrom(address from, address to) external {\n'
            '    emit Transfer(msg.sender, to, 1);\n'
            '  }\n'
            '}\n'
            'contract Harness {\n'
            '  address internal from;\n'
            '  function test_Exploit() public {\n'
            '    Business(address(0)).transferFrom(address(1), address(2));\n'
            '  }\n'
            '}\n'
        )
        binding = {
            'bindings': {
                'holder': {
                    'kind': 'address_value',
                    'solidity_expr': 'from',
                    'checkpoint': 'after',
                },
            },
            'patch': {
                'file': 'Contract.sol', 'contract': 'Business',
                'functions': [{'name': 'transferFrom', 'file': 'Contract.sol'}],
            },
            'probe': {'contract': 'Harness', 'exploit_test': 'test_Exploit'},
        }
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp)
            (src / 'Contract.sol').write_text(source)
            normalized, changes = normalize_binding(binding, src)
        self.assertEqual(changes, [])
        self.assertEqual(normalized['patch']['contract'], 'Business')
        self.assertEqual(normalized['patch']['functions'][0]['name'],
                         'transferFrom')


if __name__ == '__main__':
    unittest.main()
