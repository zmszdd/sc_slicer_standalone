import json
import tempfile
import unittest
from pathlib import Path

from evaluation.metrics.build_dev_24 import build as build_dev_24
from evaluation.metrics.experiment_contract import build_contract, build_split


def write(path, payload):
    path.write_text(json.dumps(payload))


class ExperimentContractTest(unittest.TestCase):
    def test_dev24_is_stratified_and_complete(self):
        root = Path(__file__).resolve().parents[2]
        if not (root / 'code4rena_reports').is_dir():
            self.skipTest('external code4rena report cache is not present')
        record = build_dev_24()
        self.assertEqual(record['case_count'], 24)
        self.assertEqual(record['positive_count'], 18)
        self.assertEqual(record['negative_count'], 6)
        self.assertEqual(len({row['case_id'] for row in record['cases']}), 24)
        self.assertTrue(all(row['exists'] for row in record['cases']))

    def test_split_reserves_same_project_pool_and_locks_test(self):
        split = build_split()
        self.assertEqual(split['dev']['positives'], 252)
        self.assertEqual(split['reserve_same_project']['positives'], 1213)
        self.assertTrue(split['policy']['reserve_is_not_test'])
        self.assertEqual(split['locked_test']['status'], 'not_assigned')

    def test_contract_binds_one_confusion_matrix(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            judge = root / 'judge.json'
            triage = root / 'triage.json'
            frozen = root / 'frozen.json'
            write(judge, {
                'positive_cases': 2,
                'tp_rows': [{'case': 'P__a__1'}, {'case': 'P__a__2'}],
                'fp_in_pool_rows': [], 'fp_blind_rows': [{'case': 'N__n__1'}],
                'judge_invalid_evaluated_total': 2,
                'fp_project_counts': {'N': 1},
                'fp_impact_insufficient_count': 0,
                'fp_remaining_count': 1,
                'recoverable_fn_count': 0, 'ceiling_count': 0,
            })
            write(triage, {'rows': []})
            write(frozen, {'case_list': {
                'count': 2, 'tp': 2, 'fn': 0,
                'cases': [{'case_id': 'P__a__1'}, {'case_id': 'P__a__2'}],
            }})
            result = build_contract(judge, triage, frozen)
        self.assertTrue(result['validation']['ok'])
        self.assertEqual(result['confusion_matrix'],
                         {'tp': 2, 'fp': 1, 'fn': 0, 'tn': 1})
        self.assertEqual(result['metrics']['accuracy'], 0.75)
        self.assertEqual(result['metrics']['precision'], 0.6667)
        self.assertEqual(result['metrics']['recall'], 1.0)


if __name__ == '__main__':
    unittest.main()
