import json
import tempfile
import unittest
from pathlib import Path

from lib.locked_eval import (
    MIN_PUBLISHABLE_NEGATIVES, build, fpr_upper_95, markdown,
)


class LockedEvalTest(unittest.TestCase):
    def _coverage_report(self, root: Path, *, eligible_positive: int,
                         eligible_negative: int,
                         label_review_cases: tuple[str, ...] = ()) -> dict:
        sample = root / 'sample.json'
        denominator = root / 'denominator.json'
        provenance = root / 'provenance.json'
        ground_truth = root / 'gt.json'
        label_review = root / 'label-review.json'
        sample.write_text(json.dumps({
            'positive_cases': ['p%d' % i for i in range(150)],
            'negative_cases': ['n%d' % i for i in range(60)],
            'strata': [{'project': 'project-%d' % i}
                       for i in range(5)],
        }))
        denominator.write_text(json.dumps({
            'refresh_ready': True,
            'mainline': {'case_counts': {
                'eligible_positive': eligible_positive,
                'eligible_negative': eligible_negative,
            }},
            'dev252': {'case_counts': {'eligible_current': 10}},
        }))
        provenance.write_text(json.dumps({'refresh_allowed': True}))
        ground_truth.write_text('{}')
        label_review.write_text(json.dumps({
            'schema_version': 'label-review-gate/1',
            'cases': [{'case': case, 'status': 'label_review_required'}
                      for case in label_review_cases],
        }))
        return build(sample_path=sample, denominator_path=denominator,
                     provenance_path=provenance,
                     ground_truth_path=ground_truth,
                     label_review_path=label_review, root=root)

    def test_reports_blockers_for_legacy_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sample = root / 'sample.json'
            denominator = root / 'denominator.json'
            provenance = root / 'provenance.json'
            ground_truth = root / 'gt.json'
            sample.write_text(json.dumps({
                'positive_cases': ['p%d' % i for i in range(350)],
                'negative_cases': ['n%d' % i for i in range(7)],
                'strata': [{'project': 'project-%d' % i}
                           for i in range(18)],
            }))
            denominator.write_text(json.dumps({
                'refresh_ready': False,
                'dev252': {'case_counts': {'eligible_current': 0,
                                           'excluded_retry': 252}},
            }))
            provenance.write_text(json.dumps({'refresh_allowed': False}))
            ground_truth.write_text('{}')
            report = build(sample_path=sample, denominator_path=denominator,
                           provenance_path=provenance,
                           ground_truth_path=ground_truth, root=root)
            self.assertFalse(report['ready'])
            self.assertTrue(any('negative sample below floor' in item
                                for item in report['blockers']))
            self.assertTrue(any('provenance gate' in item
                                for item in report['blockers']))
            self.assertIn('ready: **false**', markdown(report))

    def test_ready_when_all_floors_and_gates_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sample = root / 'sample.json'
            denominator = root / 'denominator.json'
            provenance = root / 'provenance.json'
            ground_truth = root / 'gt.json'
            sample.write_text(json.dumps({
                'positive_cases': ['p%d' % i for i in range(150)],
                'negative_cases': ['n%d' % i for i in range(60)],
                'strata': [{'project': 'project-%d' % i}
                           for i in range(5)],
            }))
            denominator.write_text(json.dumps({
                'refresh_ready': True,
                'dev252': {'case_counts': {'eligible_current': 10}},
            }))
            provenance.write_text(json.dumps({'refresh_allowed': True}))
            ground_truth.write_text('{}')
            report = build(sample_path=sample, denominator_path=denominator,
                           provenance_path=provenance,
                           ground_truth_path=ground_truth, root=root)
            self.assertTrue(report['ready'], report['blockers'])
            self.assertEqual(report['gates']['eligible_current'], 10)

    def test_low_evidence_coverage_is_ready_but_not_publishable(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = self._coverage_report(
                Path(tmp), eligible_positive=100, eligible_negative=20)
            self.assertTrue(report['ready'], report['blockers'])
            self.assertFalse(report['publishable'])
            self.assertEqual(report['publication_status'],
                             'coverage-limited')
            self.assertEqual(report['gates']['positive_coverage'], 0.6667)
            self.assertEqual(report['gates']['negative_coverage'], 0.3333)
            self.assertTrue(any('positive evaluated coverage below' in item
                                for item in report['publication_blockers']))
            self.assertTrue(any('FPR upper95' in item
                                for item in report['publication_blockers']))
            md = markdown(report)
            self.assertIn('publishable: **false**', md)
            self.assertIn('publication status: `coverage-limited`', md)

    def test_full_evidence_coverage_is_publishable(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = self._coverage_report(
                Path(tmp), eligible_positive=140, eligible_negative=40)
            self.assertTrue(report['ready'], report['blockers'])
            self.assertTrue(report['publishable'])
            self.assertEqual(report['publication_status'], 'publishable')
            self.assertEqual(report['publication_blockers'], [])

    def test_high_positive_coverage_below_ninety_is_publishable(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = self._coverage_report(
                Path(tmp), eligible_positive=132, eligible_negative=40)
            self.assertEqual(report['gates']['positive_coverage'], 0.88)
            self.assertTrue(report['publishable'], report['publication_blockers'])
            self.assertEqual(report['publication_status'], 'publishable')

    def test_negative_fpr_floor_is_derived_from_statistical_target(self):
        self.assertEqual(MIN_PUBLISHABLE_NEGATIVES, 24)
        self.assertAlmostEqual(fpr_upper_95(9), 0.2831, places=3)
        self.assertAlmostEqual(fpr_upper_95(24), 0.1171, places=3)

    def test_label_review_blocks_publication_but_not_refresh(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = self._coverage_report(
                Path(tmp), eligible_positive=140, eligible_negative=40,
                label_review_cases=('GTE__W3F7ikgZG3G',))
            self.assertTrue(report['ready'])
            self.assertFalse(report['publishable'])
            self.assertTrue(any('label review required' in item
                                for item in report['publication_blockers']))
            self.assertEqual(report['label_review']['status'],
                             'label_review_required')

    def test_primary_gate_uses_consistency_metrics_when_available(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = self._coverage_report(
                Path(tmp), eligible_positive=140, eligible_negative=40)
            self.assertTrue(report['publishable'])
            consistency = Path(tmp) / 'mainline-metrics.json'
            consistency.write_text(json.dumps({
                'consistency_gate': {
                    'publishable': False,
                    'publication_status': 'coverage-limited',
                    'publication_blockers': ['witness-negative shortfall'],
                    'eligible_positive': 140,
                    'witness_eligible_negative': 8,
                    'fpr_upper95': 0.4707,
                },
            }))
            from lib.locked_eval import build as build_contract
            primary = build_contract(
                sample_path=Path(tmp) / 'sample.json',
                denominator_path=Path(tmp) / 'denominator.json',
                provenance_path=Path(tmp) / 'provenance.json',
                ground_truth_path=Path(tmp) / 'gt.json',
                label_review_path=Path(tmp) / 'label-review.json',
                consistency_metrics_path=consistency,
                root=Path(tmp))
            self.assertFalse(primary['primary_publishable'])
            self.assertEqual(primary['primary_publication_status'],
                             'coverage-limited')
            self.assertEqual(primary['primary_gate'][
                'publication_blockers'], ['witness-negative shortfall'])
            self.assertIn('primary publishable: **false**',
                          markdown(primary))

    def test_negative_project_coverage_and_concentration_are_gated(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sample = root / 'sample.json'
            denominator = root / 'denominator.json'
            provenance = root / 'provenance.json'
            ground_truth = root / 'gt.json'
            sample.write_text(json.dumps({
                'positive_cases': ['p%d' % i for i in range(150)],
                'negative_cases': ['ProjA__n%d__x' % i for i in range(40)],
                'strata': [{'project': 'project-%d' % i}
                           for i in range(5)],
            }))
            denominator.write_text(json.dumps({
                'refresh_ready': True,
                'dev252': {'case_counts': {'eligible_current': 10}},
            }))
            provenance.write_text(json.dumps({'refresh_allowed': True}))
            ground_truth.write_text('{}')
            report = build(sample_path=sample, denominator_path=denominator,
                           provenance_path=provenance,
                           ground_truth_path=ground_truth, root=root)
            self.assertFalse(report['ready'])
            self.assertTrue(any('negative project coverage below floor'
                                in item for item in report['blockers']))
            self.assertTrue(any('negative project concentration above cap'
                                in item for item in report['blockers']))

    def test_negative_source_slice_readiness_is_gated(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sample = root / 'sample.json'
            denominator = root / 'denominator.json'
            provenance = root / 'provenance.json'
            ground_truth = root / 'gt.json'
            sample.write_text(json.dumps({
                'positive_cases': ['p%d' % i for i in range(150)],
                'negative_cases': ['Proj%d__n%d__x' % (i % 8, i)
                                   for i in range(60)],
                'negative_slice_ready': 2,
                'strata': [{'project': 'project-%d' % i}
                           for i in range(5)],
            }))
            denominator.write_text(json.dumps({
                'refresh_ready': True,
                'dev252': {'case_counts': {'eligible_current': 10}},
            }))
            provenance.write_text(json.dumps({'refresh_allowed': True}))
            ground_truth.write_text('{}')
            report = build(sample_path=sample, denominator_path=denominator,
                           provenance_path=provenance,
                           ground_truth_path=ground_truth, root=root)
            self.assertFalse(report['ready'])
            self.assertTrue(any('negative source slices below floor'
                                in item for item in report['blockers']))


if __name__ == '__main__':
    unittest.main()
