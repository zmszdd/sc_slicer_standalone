from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from cli.stage3_repair_batch import RECOVERABLE_BUCKETS, recoverable_cases


class RepairBatchTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.cases = self.tmp / 'cases'
        self.cases.mkdir()

    def _mk_case(self, name):
        d = self.cases / name / 'stage2_run'
        d.mkdir(parents=True)
        (d / 'stage3-spec.json').write_text('{}')

    def test_only_recoverable_buckets_with_stage2_run(self):
        self._mk_case('A__a')
        self._mk_case('B__b')
        triage = {'rows': [
            {'case': 'A__a', 'bucket': 'partial_binding'},
            {'case': 'B__b', 'bucket': 'not_dynamically_expressible'},
            {'case': 'C__c', 'bucket': 'partial_binding'},
        ]}
        rows = recoverable_cases(triage, self.cases)
        self.assertEqual([r['case'] for r in rows], ['A__a'])
        self.assertEqual(rows[0]['command'][:2],
                         ['cli.stage3_verdict_loop', '--case-dir'])

    def test_recoverable_buckets_exclude_ceilings(self):
        self.assertNotIn('not_dynamically_expressible', RECOVERABLE_BUCKETS)
        self.assertNotIn('reference_patch_required', RECOVERABLE_BUCKETS)


if __name__ == '__main__':
    unittest.main()
