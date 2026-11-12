import unittest
from pathlib import Path

from lib.binding_normalize import normalize_binding

CASES = Path(__file__).resolve().parents[1] / 'cases'


class BindingNormalizeTest(unittest.TestCase):
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
        binding = self._merkl_binding('DistributionCreator', 'createCampaign')
        normalized, changes = normalize_binding(binding, case / 'src')
        self.assertTrue(changes)
        self.assertEqual(normalized['patch']['contract'], 'AllowanceBypassTest')
        self.assertEqual(normalized['patch']['functions'][0]['name'],
                         'testAllowanceBypass')

    def test_keeps_correct_injection_point_unchanged(self):
        case = CASES / 'Merkl_T4ExvutBBXC__si6yAc4Sp6f__ZWh59mSfE3A'
        binding = self._merkl_binding('AllowanceBypassTest', 'testAllowanceBypass')
        original = binding['patch']
        normalized, changes = normalize_binding(binding, case / 'src')
        self.assertEqual(changes, [])
        self.assertEqual(normalized['patch'], original)


if __name__ == '__main__':
    unittest.main()
