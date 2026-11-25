from __future__ import annotations

import json
import os
import tempfile
import time
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from lib.metrics_sync import (discover_auto_reproductions, latest_run_summary,
                              latest_claim_run_summary, reconcile_positive_eval,
                              revalidate_p2_auto, _is_auto_dir)


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


def _write_manifest(run_dir: Path, created_at: str) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / 'run-manifest.json').write_text(json.dumps({
        'schema_version': 'stage3-run-manifest/1',
        'run_id': run_dir.name,
        'created_at': created_at,
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

    def test_run_manifest_time_overrides_mtime_and_run_id(self):
        case = 'Proj_Manifest__sub'
        older = self._mk(case, 'c1', 'violation_reproduced', 'Success', 'Failure',
                         suffix='__c1__20991231T000000Z')
        newer = self._mk(case, 'c1', 'partial_binding', 'Success', 'Success',
                         suffix='__c1__20000101T000000Z')
        _write_summary(older, case, 'c1', 'violation_reproduced', 'Success', 'Failure', 'panic')
        _write_summary(newer, case, 'c1', 'partial_binding', 'Success', 'Success', None)
        _write_manifest(older, '2026-01-01T00:00:00+00:00')
        _write_manifest(newer, '2026-11-20T00:00:00+00:00')
        os.utime(older, (time.time(), time.time()))
        os.utime(newer, (time.time() - 100, time.time() - 100))
        latest = latest_claim_run_summary(self.runs, case, 'c1')
        self.assertEqual(latest['consistency_verdict'], 'partial_binding')

    def test_run_id_time_is_deterministic_without_mtime(self):
        case = 'Proj_Legacy__sub'
        older = self._mk(case, 'c1', 'violation_reproduced', 'Success', 'Failure',
                         suffix='__c1__20261110T000000Z')
        newer = self._mk(case, 'c1', 'partial_binding', 'Success', 'Success',
                         suffix='__c1__20261111T000000Z')
        _write_summary(older, case, 'c1', 'violation_reproduced', 'Success', 'Failure', 'panic')
        _write_summary(newer, case, 'c1', 'partial_binding', 'Success', 'Success', None)
        os.utime(older, (time.time(), time.time()))
        os.utime(newer, (time.time() - 100, time.time() - 100))
        latest = latest_claim_run_summary(self.runs, case, 'c1')
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

    def test_discover_uses_reproduced_claim_when_case_latest_is_not(self):
        case = 'Proj_Partial__p'
        good = self._mk(case, 'c1', 'violation_reproduced', 'Success', 'Failure',
                        suffix='__c1__20261110T000000Z')
        bad = self._mk(case, 'c2', 'partial_binding', 'Success', 'Success',
                       suffix='__c2__20261111T000000Z')
        _write_summary(good, case, 'c1', 'violation_reproduced', 'Success', 'Failure', 'panic')
        _write_summary(bad, case, 'c2', 'partial_binding', 'Success', 'Success', None)
        os.utime(good, (time.time() - 100, time.time() - 100))
        os.utime(bad, (time.time(), time.time()))
        rows = discover_auto_reproductions(
            self.runs, [{'case': case, 'validity': 'valid'}],
            base_tp=set(), existing_auto=set(),
            positive_eval=[{'case': case, 'bound_claim_ids': ['c1', 'c2']}])
        self.assertEqual([r['case'] for r in rows], [case])
        self.assertEqual(rows[0]['claim_id'], 'c1')


class ReconcilePositiveEvalTest(TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.runs = self.tmp / 'runs'
        self.runs.mkdir()
        self.eval_path = self.tmp / 'positive_eval.json'
        self.gt_path = self.tmp / 'judge_ground_truth.json'

    def _write_eval(self, cases):
        self.eval_path.write_text(json.dumps({'cases': cases}) + '\n')

    def _write_gt(self, cases):
        self.gt_path.write_text(json.dumps({'cases': cases}) + '\n')

    def test_flips_reproduced_for_valid_case_with_latest_run(self):
        case = 'Proj_A__sub'
        run = self.runs / f'{case}__impact_claim_x__20261111T000000Z'
        _write_summary(run, case, 'c1', 'violation_reproduced', 'Success',
                       'Failure', 'panic: assertion failed (0x01)')
        self._write_gt([{'case': case, 'validity': 'valid'}])
        self._write_eval([{'case': case, 'status': 'done', 'reproduced': 0,
                           'verdicts': ['violation_not_reproduced'],
                           'claim_ids': ['c1']}])
        changed = reconcile_positive_eval(self.runs, self.eval_path, self.gt_path)
        self.assertEqual(changed, 1)
        row = json.loads(self.eval_path.read_text())['cases'][0]
        self.assertEqual(row['reproduced'], 1)
        self.assertIn('violation_reproduced', row['verdicts'])
        # 幂等：第二次对账不应再变化
        self.assertEqual(reconcile_positive_eval(self.runs, self.eval_path,
                                                 self.gt_path), 0)

    def test_partial_case_uses_reproduced_claim_not_case_latest(self):
        case = 'Proj_Partial__p'
        good = self.runs / f'{case}__c1__20261110T000000Z'
        bad = self.runs / f'{case}__c2__20261111T000000Z'
        _write_summary(good, case, 'c1', 'violation_reproduced', 'Success',
                       'Failure', 'panic: assertion failed (0x01)')
        _write_summary(bad, case, 'c2', 'partial_binding', 'Success',
                       'Success', None)
        os.utime(good, (time.time() - 100, time.time() - 100))
        os.utime(bad, (time.time(), time.time()))
        self._write_gt([{'case': case, 'validity': 'valid'}])
        self._write_eval([{'case': case, 'status': 'done', 'reproduced': 0,
                           'verdicts': ['violation_not_reproduced',
                                        'partial_binding'],
                           'bound_claim_ids': ['c1', 'c2']}])
        changed = reconcile_positive_eval(self.runs, self.eval_path, self.gt_path)
        self.assertEqual(changed, 1)
        row = json.loads(self.eval_path.read_text())['cases'][0]
        self.assertEqual(row['reproduced'], 1)
        self.assertEqual(row['verdicts'],
                         ['violation_reproduced', 'partial_binding'])
        self.assertEqual(reconcile_positive_eval(self.runs, self.eval_path,
                                                 self.gt_path), 0)

    def test_ignores_invalid_case(self):
        case = 'Proj_B__sub'
        run = self.runs / f'{case}__impact_claim_x__20261111T000000Z'
        _write_summary(run, case, 'c1', 'violation_reproduced', 'Success',
                       'Failure', 'panic')
        self._write_gt([{'case': case, 'validity': 'invalid'}])
        self._write_eval([{'case': case, 'status': 'done', 'reproduced': 0,
                           'verdicts': ['violation_not_reproduced'],
                           'claim_ids': ['c1']}])
        self.assertEqual(reconcile_positive_eval(self.runs, self.eval_path,
                                                 self.gt_path), 0)


class RevalidateP2AutoTest(TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.runs = self.tmp / 'runs'
        self.runs.mkdir()

    def test_neg_token_in_claim_not_excluded_from_auto_dirs(self):
        case = 'Proj_Neg__sub'
        name = f'{case}__impact_claim_finite_negative_for_zero__20261111T000000Z'
        self.assertTrue(_is_auto_dir(name, case))

    def test_downgrades_stale_p2_row_when_no_current_run(self):
        case = 'Proj_Stale__s'
        p2_rows = [{'case': case, 'verdict': 'violation_reproduced',
                    'note': 'old'}]
        changed = revalidate_p2_auto(
            self.runs, [{'case': case, 'validity': 'valid'}],
            [{'case': case, 'bound_claim_ids': ['c1']}], p2_rows)
        self.assertEqual(changed, 1)
        self.assertEqual(p2_rows[0]['verdict'], 'superseded_by_rebind')

    def test_keeps_p2_row_with_current_reproduction(self):
        case = 'Proj_Live__l'
        run = self.runs / f'{case}__c1__20261111T000000Z'
        _write_summary(run, case, 'c1', 'violation_reproduced', 'Success',
                       'Failure', 'panic: assertion failed (0x01)')
        p2_rows = [{'case': case, 'verdict': 'violation_reproduced',
                    'note': 'live'}]
        changed = revalidate_p2_auto(
            self.runs, [{'case': case, 'validity': 'valid'}],
            [{'case': case, 'bound_claim_ids': ['c1']}], p2_rows)
        self.assertEqual(changed, 0)
        self.assertEqual(p2_rows[0]['verdict'], 'violation_reproduced')


class MetricsSyncCliTest(TestCase):
    def test_check_is_read_only(self):
        from cli import stage3_metrics_sync

        with patch.object(stage3_metrics_sync, 'sync') as sync_mock, \
                patch.object(stage3_metrics_sync, 'verify_consistency',
                             return_value={'ok': True, 'problems': []}):
            code = stage3_metrics_sync.main(['--check'])

        self.assertEqual(code, 0)
        sync_mock.assert_not_called()

    def test_sync_fails_when_generators_fail(self):
        from cli import stage3_metrics_sync

        result = {
            'generation_ok': False,
            'generation_failures': ['mainline_metrics.py'],
            'consistency': {'ok': True, 'problems': []},
        }
        with patch.object(stage3_metrics_sync, 'sync', return_value=result), \
                patch.object(stage3_metrics_sync, 'verify_consistency',
                             return_value={'ok': True, 'problems': []}):
            code = stage3_metrics_sync.main([])
        self.assertEqual(code, 1)
        self.assertFalse(result['consistency']['ok'])
        self.assertIn('generation failed: mainline_metrics.py',
                      result['consistency']['problems'])

    def test_check_detects_missing_generator(self):
        from lib import metrics_sync

        with patch.object(metrics_sync, 'METRICS', Path('/nonexistent')):
            result = metrics_sync.verify_consistency()
        self.assertFalse(result['ok'])
        self.assertTrue(any('required metrics generator is missing'
                            in problem for problem in result['problems']))


if __name__ == '__main__':
    import unittest
    unittest.main()


class VerifyConsistencyTest(TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.write = self.tmp / 'unified_metrics.json'
        self.judge = self.tmp / 'judge_anchored_metrics.json'
        for name in ('sample_mainline.py', 'mainline_metrics.py',
                     'mainline_stage2_triage.py',
                     'effect_witness_reaudit.py', 'fullset_metrics.py',
                     'unified_metrics.py', 'independence_report.py',
                     'recall_recoverability.py', 'repro_failure_triage.py',
                     'stage2_trigger_audit.py', 'fn_work_queue.py'):
            (self.tmp / name).write_text('')

    def _write(self, path, value):
        path.write_text(json.dumps(value) + '\n')

    def _check(self, unified_cm=None, judge_fields=None, metrics=None):
        metrics = metrics or {'completion_rate': 0.9, 'recall': 0.61}
        self._write(self.write, {
            'confusion_matrix': unified_cm or {
                'tp': 62, 'fp': 15, 'fn': 39, 'tn': 60,
                'judge_valid_total': 101, 'judge_invalid_evaluated': 75,
            },
            'metrics': metrics,
        })
        self._write(self.judge, judge_fields or {
            'tp_clean': 62, 'fp_from_judge_invalid': 15, 'fn_judge_valid': 39,
            'tn_invalid': 60, 'judge_valid_cases': 101,
            'judge_invalid_evaluated_total': 75,
        })
        self._write(self.tmp / 'metrics_report_161.json', {
            'metrics': {'completion_rate': metrics['completion_rate']},
        })
        from lib import metrics_sync
        old_metrics = metrics_sync.METRICS
        old_read = metrics_sync.read_json
        try:
            metrics_sync.METRICS = self.tmp
            metrics_sync.read_json = lambda p: json.loads(Path(p).read_text())
            return metrics_sync.verify_consistency()
        finally:
            metrics_sync.METRICS = old_metrics
            metrics_sync.read_json = old_read

    def test_consistent_artifacts_pass(self):
        self.assertTrue(self._check()['ok'])

    def test_tp_fp_disagreement_detected(self):
        result = self._check(
            unified_cm={'tp': 61, 'fp': 15, 'fn': 40, 'tn': 60,
                        'judge_valid_total': 101,
                        'judge_invalid_evaluated': 75})
        self.assertFalse(result['ok'])
        self.assertTrue(any('tp' in p for p in result['problems']))

    def test_denominator_mismatch_detected(self):
        result = self._check(
            unified_cm={'tp': 62, 'fp': 15, 'fn': 39, 'tn': 60,
                        'judge_valid_total': 99,
                        'judge_invalid_evaluated': 75})
        self.assertFalse(result['ok'])
        self.assertTrue(any('judge_valid_total' in p for p in result['problems']))
