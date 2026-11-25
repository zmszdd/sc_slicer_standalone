import json
import tempfile
import unittest
from pathlib import Path

from evaluation.metrics import execution_preflight as ep


def _write_stage2(root: Path, case: str, claim_id: str = 'c1') -> None:
    stage2 = root / 'runs_01' / case
    stage2.mkdir(parents=True, exist_ok=True)
    (stage2 / 'stage3-spec.json').write_text(json.dumps({
        'claims': [{
            'claim_id': claim_id,
            'formalization_status': 'formalized_candidate',
        }],
    }))
    (stage2 / 'constraints.json').write_text('{}')
    (stage2 / 'formalization.json').write_text(json.dumps({
        'claims': [{'id': claim_id}],
    }))


def _write_binding(cases_root: Path, case: str, expression: str,
                   claim_id: str = 'c1') -> None:
    bindings = cases_root / case / 'bindings'
    bindings.mkdir(parents=True, exist_ok=True)
    (bindings / f'{claim_id}.json').write_text(json.dumps({
        'claim_id': claim_id,
        'bindings': {'x': {'solidity_expr': expression}},
        'patch': {'file': 'Contract.sol', 'contract': 'C', 'functions': []},
        'probe': {'contract': 'PoC', 'exploit_test': 'testX',
                  'safety_test': None},
    }))


class ExecutionPreflightTest(unittest.TestCase):
    def test_unbound_binding_blocks_offline_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sample = root / 'sample.json'
            sample.write_text(json.dumps({'positive_cases': ['case_a']}))
            goldset = root / 'goldset'
            cases = root / 'cases'
            _write_stage2(goldset, 'case_a')
            _write_binding(cases, 'case_a', 'UNBOUND')
            report = ep.build(sample_path=sample, goldset_root=goldset,
                              cases_root=cases, check_provider=False)
        self.assertFalse(report['ok'])
        self.assertEqual(report['mode'], 'blocked')
        self.assertEqual(report['incomplete'], ['case_a'])
        self.assertIn('unbound symbols', report['rows'][0]['issues'][0])

    def test_complete_binding_allows_offline_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sample = root / 'sample.json'
            sample.write_text(json.dumps({'positive_cases': ['case_a']}))
            goldset = root / 'goldset'
            cases = root / 'cases'
            _write_stage2(goldset, 'case_a')
            _write_binding(cases, 'case_a', 'x > 0')
            report = ep.build(sample_path=sample, goldset_root=goldset,
                              cases_root=cases, check_provider=False)
        self.assertTrue(report['ok'])
        self.assertEqual(report['mode'], 'offline')
        self.assertEqual(report['incomplete'], [])

    def test_missing_stage2_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sample = root / 'sample.json'
            sample.write_text(json.dumps({'positive_cases': ['case_a']}))
            report = ep.build(sample_path=sample,
                              goldset_root=root / 'goldset',
                              cases_root=root / 'cases',
                              check_provider=False)
        self.assertFalse(report['ok'])
        self.assertEqual(report['rows'][0]['issues'],
                         ['stage2 spec missing'])


if __name__ == '__main__':
    unittest.main()
