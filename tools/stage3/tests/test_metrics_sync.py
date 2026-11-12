from __future__ import annotations

import json
import os
import tempfile
import time
from pathlib import Path
from unittest import TestCase

from lib.metrics_sync import discover_auto_reproductions, latest_run_summary


def _write_summary(run_dir: Path, case: str, claim: str, verdict: str,
                   original: str, patched: str, reason: str | None) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / 'stage3-summary.json').write_text(json.dumps({
        'schema_version': 'stage3-run-summary/1',
        'case': case,
        'run_id': run_dir.name,
        'claim_id': claim,
        'consistency_verdict': verdict,
        'routing': {'route': 'single_anchor'},
        'forge': {'exploit': {
            'original': {'name': 't', 'status': original, 'reason': None},
            'patched': {'name': 't', 'status': patched, 'reason': reason},
        }, 'safety': None},
    }) + '\n')


class MetricsSyncTest(TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.runs = self.tmp / 'runs'
        self.runs.mkdir()

    def _mk(self, case: str, claim: str, verdict: str, original: str,
            patched: str, suffix: str = '__impact_claim_x__20261111T000000Z',
            reason: str | None = 'panic: assertion failed (0x01)'):
        return self.runs / f'{case}{suffix}'

    def test_latest_auto_run_preferred_over_superseded(self):
        case = 'Proj_A__sub'
        old = self._mk(case, 'c1', 'violation_reproduced', 'Success', 'Failure',
                       suffix='__impact_claim_x__20261110T000000Z')
        new = self._mk(case, 'c1', 'partial_binding', 'Success', 'Success',
                       suffix='__impact_claim_x__20261111T000000Z')
        _write_summary(old, case, 'c1', 'violation_reproduced', 'Success', 'Failure', 'panic: assertion failed (0x01)')
        _write_summary(new, case, 'c1', 'partial_binding', 'Success', 'Success', None)
        os.utime(old, (time.time() - 100, time.time() - 100))
        os.utime(new, (time.time(), time.time()))
        latest = latest_run_summary(self.runs, case)
        self.assertEqual(latest['consistency_verdict'], 'partial_binding')

    def test_refpatch_and_neg_dirs_excluded(self):
        case = 'Proj_B__sub'
        ref = self._mk(case, 'c1', 'violation_reproduced', 'Success', 'Failure',
                       suffix='__core_claim_refpatch')
        _write_summary(ref, case, 'c1', 'violation_reproduced', 'Success', 'Failure', 'panic')
        self.assertIsNone(latest_run_summary(self.runs, case))

    def test_discover_only_valid_and_new(self):
        case_a = 'Proj_A__a'
        case_b = 'Proj_B__b'
        case_c = 'Proj_C__c'
        run_a = self._mk(case_a, 'c1', 'violation_reproduced', 'Success', 'Failure')
        run_b = self._mk(case_b, 'c1', 'violation_reproduced', 'Success', 'Failure')
        run_c = self._mk(case_c, 'c1', 'violation_reproduced', 'Success', 'Failure')
        _write_summary(run_a, case_a, 'c1', 'violation_reproduced', 'Success', 'Failure', 'panic')
        _write_summary(run_b, case_b, 'c1', 'violation_reproduced', 'Success', 'Failure', 'panic')
        _write_summary(run_c, case_c, 'c1', 'violation_reproduced', 'Success', 'Failure', 'panic')
        judge = [
            {'case': case_a, 'validity': 'valid'},
            {'case': case_b, 'validity': 'invalid'},
            {'case': case_c, 'validity': 'valid'},
        ]
        rows = discover_auto_reproductions(self.runs, judge, base_tp=set(),
                                           existing_auto={case_c})
        self.assertEqual({r['case'] for r in rows}, {case_a})
        self.assertEqual(rows[0]['run_id'], run_a.name)


if __name__ == '__main__':
    import unittest
    unittest.main()
