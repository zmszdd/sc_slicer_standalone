import json
import tempfile
import unittest
from pathlib import Path

from cli.stage3_negative_eval import aggregate, run_one, _binding_files, _case_dirs


class NegativeEvalTest(unittest.TestCase):
    def test_aggregate_preserves_raw_verdicts(self):
        rows = [
            {'case': 'a_neg', 'status': 'ok', 'claim': 'c1',
             'verdict': 'violation_not_reproduced'},
            {'case': 'b_neg', 'status': 'ok', 'claim': 'c2',
             'verdict': 'inconclusive'},
            {'case': 'c_neg', 'status': 'error', 'claim': None, 'verdict': None},
            {'case': 'd_neg', 'status': 'multi', 'claims': [
                {'claim': 'c3', 'verdict': 'violation_reproduced'},
                {'claim': 'c4', 'verdict': 'inconclusive'},
            ]},
        ]
        payload = aggregate(rows)
        results = payload['results']
        self.assertEqual(len(results), 5)
        by_verdict = {r['verdict'] for r in results}
        # inconclusive must stay inconclusive, never rewritten
        self.assertIn('inconclusive', by_verdict)
        self.assertIn('violation_not_reproduced', by_verdict)
        self.assertIn('violation_reproduced', by_verdict)
        self.assertEqual(payload['summary']['errors'], 1)
        self.assertEqual(payload['summary']['total_claims'], 5)
        self.assertEqual(payload['summary']['verdicts']['inconclusive'], 2)

    def test_binding_files_single_and_multi(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            single = root / 'single'
            (single / 'bindings').mkdir(parents=True)
            (single / 'binding.json').write_text('{}')
            multi = root / 'multi'
            (multi / 'bindings').mkdir(parents=True)
            (multi / 'bindings' / 'a.json').write_text('{}')
            (multi / 'bindings' / 'b.json').write_text('{}')
            empty = root / 'empty'
            empty.mkdir()
            self.assertEqual([p.name for p in _binding_files(single)],
                             ['binding.json'])
            self.assertEqual({p.name for p in _binding_files(multi)},
                             {'a.json', 'b.json'})
            self.assertEqual(_binding_files(empty), [])
            dirs = _case_dirs(root, None)
            self.assertEqual({d.name for d in dirs}, {'single', 'multi'})

    def test_run_one_reuse_keeps_verdict(self):
        # reuse path uses _existing_summary; run_one with a fresh temp case
        # must return a row whose status is ok/error and whose verdict key exists.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'binding.json').write_text('{}')
            (root / 'stage2_run').mkdir()
            row = run_one(root, reuse=False)
            self.assertIn(row['status'], ('ok', 'error'))
            self.assertIn('verdict', row)


if __name__ == '__main__':
    unittest.main()
