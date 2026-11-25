import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from lib.case_runner import bind_claims


CLAIM = 'claim_multi'
SOURCE = '''
contract Vault {
    uint256 public total;
    function deposit(uint256 amount) external { total += amount; }
}

contract ProbeTest {
    function testExploit() external { new Vault().deposit(1); }
}
'''


class CaseRunnerRoutingTest(unittest.TestCase):
    def test_multi_contract_patch_route_skips_binding_llm(self):
        with tempfile.TemporaryDirectory() as tmp:
            case = Path(tmp) / 'case'
            stage2 = case / 'stage2_run'
            src = case / 'src'
            (stage2).mkdir(parents=True)
            src.mkdir(parents=True)
            (case / 'test').mkdir()
            (src / 'Contract.sol').write_text(SOURCE)
            (stage2 / 'constraints.json').write_text('{}')
            (stage2 / 'stage3-spec.json').write_text(json.dumps({'claims': [{
                'claim_id': CLAIM,
                'formalization_status': 'formalized_candidate',
                'binding_contract': {'symbols': [
                    {'symbol': 'total', 'sort': 'int',
                     'meaning': 'vault total', 'checkpoint': 'before',
                     'appears_in': ['I'], 'binding_kind': 'numeric_value'},
                    {'symbol': 'deposit_amount', 'sort': 'int',
                     'meaning': 'deposited amount', 'checkpoint': 'input',
                     'appears_in': ['P'], 'binding_kind': 'numeric_value'},
                ]},
            }]}))
            (stage2 / 'formalization.json').write_text(json.dumps({
                'symbols': {'total': {'sort': 'int'},
                            'deposit_amount': {'sort': 'int'}},
                'claims': [{'id': CLAIM, 'properties': {
                    'preconditions': {'expression': {'var': 'deposit_amount'}},
                    'safety': {'expression': {'var': 'total'}},
                    'effects': {'expression': {'var': 'total'}},
                }}],
            }))
            from lib.spec_loader import load_stage2_run
            spec = load_stage2_run(stage2)
            anchor = {'bindability': 'multi_contract',
                      'suggested_patch_contract': 'Vault',
                      'anchor_observability': 'high'}
            with mock.patch('lib.bindability_contract.build_contract',
                            return_value={CLAIM: anchor}), \
                 mock.patch('lib.reference_patch.has_reference_patch',
                            return_value=True), \
                 mock.patch('lib.reference_patch.build_reference_patch',
                            return_value={'accepted': True,
                                          'source_kind': 'patched_dir'}), \
                 mock.patch('subprocess.run', side_effect=AssertionError(
                     'binding LLM must not run for a validated patch route')):
                result = bind_claims(
                    case_dir=case, stage2_dir=stage2, src_dir=src,
                    claims=[CLAIM], formal=spec['formal'], spec=spec['spec'],
                    apply_ceiling=True, max_rounds=1)
            self.assertEqual(result['bound_claim_ids'], [CLAIM])
            binding = json.loads((case / 'bindings' / f'{CLAIM}.json').read_text())
            self.assertEqual(binding['patch']['contract'], 'Vault')
            self.assertEqual(binding['probe']['exploit_test'], 'testExploit')
            self.assertTrue((case / 'bindability-feedback.json').is_file())
            self.assertFalse(result['bindability_feedback']['claims'][CLAIM][
                'needs_restatement'])


if __name__ == '__main__':
    unittest.main()
