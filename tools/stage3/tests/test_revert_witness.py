from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

STAGE3 = Path(__file__).resolve().parents[1]
if str(STAGE3) not in sys.path:
    sys.path.insert(0, str(STAGE3))
METRICS = STAGE3 / 'evaluation' / 'metrics'
if str(METRICS) not in sys.path:
    sys.path.insert(0, str(METRICS))

from lib import revert_witness  # noqa: E402
import effect_witness_reaudit  # noqa: E402


class RevertWitnessPolicyTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def _fixture(self, body: str, patch_function: str,
                 test_name: str = 'testExploit'):
        case = self.root / 'case'
        (case / 'bindings').mkdir(parents=True)
        binding = {
            'claim_id': 'claim-1',
            'probe': {'contract': 'PoC', 'exploit_test': test_name},
            'patch': {
                'file': 'Contract.sol',
                'contract': 'Vault',
                'functions': [{'name': patch_function}],
            },
        }
        (case / 'bindings' / 'claim-1.json').write_text(json.dumps(binding))
        source = (
            'contract PoC {\n'
            f'    function {test_name}() public {{\n'
            f'{body}\n'
            '    }\n'
            '}\n'
        )
        (case / 'src').mkdir()
        (case / 'src' / 'Contract.sol').write_text(source)
        run = self.root / 'run'
        (run / 'original' / 'src').mkdir(parents=True)
        (run / 'original' / 'src' / 'Contract.sol').write_text(source)
        (run / 'patched' / 'src').mkdir(parents=True)
        (run / 'patched' / 'src' / 'Contract.sol').write_text(
            'contract PoC { bool stage3_ok; bytes stage3_ret; }\n')
        summary = {
            'case': str(case),
            'run_id': 'run',
            'claim_id': 'claim-1',
            'probe': {'contract': 'PoC', 'exploit_test': test_name},
            'consistency_verdict': 'effect_not_witnessed',
            'raw_consistency_verdict': 'violation_reproduced',
            'post_execution_gate': {'code': 'REVERT_EFFECT_NOT_WITNESSED'},
            'witness': {
                'original_status': 'Success',
                'patched_status': 'Failure',
                'invariant_contradicted': True,
            },
            'execution_gate': {'metric_eligibility': {
                'consistency': True, 'vulnerability': True}},
        }
        return summary, run

    def test_expected_revert_is_patched_vulnerable_operation(self):
        summary, run = self._fixture(
            '        vm.expectRevert();\n'
            '        vault.postLimitOrder(1);\n',
            'postLimitOrder')
        decision = revert_witness.evaluate(summary, run_dir=run)
        self.assertTrue(decision['eligible'])
        self.assertEqual(decision['reason'],
                         'revert_is_vulnerable_operation')

    def test_safe_behaviour_revert_before_exploit_is_rejected(self):
        summary, run = self._fixture(
            '        token.transfer(recipient, 1);\n'
            '        vm.expectRevert();\n'
            '        token.transfer(recipient, 1);\n'
            '        token.batchTransfers(recipient);\n',
            'batchTransfers')
        decision = revert_witness.evaluate(summary, run_dir=run)
        self.assertFalse(decision['eligible'])
        self.assertEqual(decision['reason'],
                         'revert_not_vulnerable_operation')

    def test_prior_vulnerable_call_is_not_enough(self):
        summary, run = self._fixture(
            '        perpManager.deposit(user, 1);\n'
            '        vm.expectRevert();\n'
            '        perpManager.placeOrder(user);\n'
            '        perpManager.deposit(user, 1);\n',
            'deposit')
        decision = revert_witness.evaluate(summary, run_dir=run)
        self.assertFalse(decision['eligible'])
        self.assertEqual(decision['reason'],
                         'revert_not_vulnerable_operation')

    def test_metric_ineligible_candidate_does_not_project_tp(self):
        summary, run = self._fixture(
            '        vm.expectRevert();\n'
            '        vault.postLimitOrder(1);\n',
            'postLimitOrder')
        row = effect_witness_reaudit.candidate(summary, run)
        self.assertTrue(row['policy_eligible'])
        self.assertTrue(row['eligible'])
        summary['execution_gate']['metric_eligibility']['vulnerability'] = False
        summary.pop('metric_eligibility', None)
        row = effect_witness_reaudit.candidate(summary, run)
        self.assertTrue(row['policy_eligible'])
        self.assertFalse(row['metric_eligible'])
        self.assertFalse(row['eligible'])


if __name__ == '__main__':
    unittest.main()
