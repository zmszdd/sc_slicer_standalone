import sys
import unittest
from collections import Counter
from pathlib import Path

METRICS = Path(__file__).resolve().parents[1] / 'evaluation' / 'metrics'
sys.path.insert(0, str(METRICS))
import case_readiness  # noqa: E402
import mainline_metrics  # noqa: E402


class CaseReadinessTest(unittest.TestCase):
    def test_every_case_has_one_distinct_status(self):
        report = case_readiness.build()
        self.assertEqual(report['schema_version'], 'case-readiness/2')
        self.assertEqual(report['totals'], {'positive': 40, 'negative': 40})
        self.assertEqual(len(report['rows']), 80)
        for label in ('positive', 'negative'):
            self.assertEqual(
                sum(report['counts'][label].values()), report['totals'][label])
        statuses = {'eligible', 'not_run', 'stage2_blocked', 'stale_only',
                    'run_unresolved', 'run_nonterminal'}
        for row in report['rows']:
            self.assertIn(row['status'], statuses)
            self.assertTrue(row['reason'])
            self.assertTrue(row['next_action'])

    def test_negative_not_run_reasons_separate_slice_and_stage2_gaps(self):
        root = Path(__file__).resolve().parents[2]
        if not (root / 'c4_pipeline_output').is_dir():
            self.skipTest('external negative-slice cache is not present')
        report = case_readiness.build()
        reasons = Counter(row['reason'] for row in report['rows']
                          if row['label'] == 'negative'
                          and row['status'] == 'not_run')
        self.assertEqual(reasons['no_slice'], 4)
        self.assertEqual(reasons['awaiting_stage2'], 8)
        self.assertEqual(reasons['stage2_needs_impact_review'], 1)
        self.assertEqual(reasons['zero_claim_stage2'], 3)
        self.assertEqual(sum(reasons.values()), 16)
        self.assertNotIn('no_stage3_run', reasons)

    def test_negative_blockers_match_rows(self):
        report = case_readiness.build()
        reasons = Counter(row['reason'] for row in report['rows']
                          if row['label'] == 'negative'
                          and row['status'] != 'eligible')
        self.assertEqual(report['blockers']['negative'], dict(reasons))

    def test_coverage_matches_authoritative_metric_evidence(self):
        report = case_readiness.build()
        metrics = mainline_metrics.main()
        self.assertEqual(
            report['coverage']['positive']['eligible'],
            metrics['coverage']['positives_evaluated'])
        self.assertEqual(
            report['coverage']['negative']['eligible'],
            metrics['coverage']['negatives_consistency_eligible'])
        self.assertEqual(
            report['counts']['positive'].get('stale_only', 0),
            metrics['coverage']['positives_stale_runs_excluded'])

    def test_next_action_mapping(self):
        self.assertEqual(case_readiness._next_action('eligible', 'x'), 'none')
        self.assertEqual(
            case_readiness._next_action('run_unresolved', 'binding_error'),
            'rebind')
        self.assertEqual(
            case_readiness._next_action('run_unresolved', 'compile_error'),
            'repair_harness_then_rerun')
        self.assertEqual(
            case_readiness._next_action(
                'run_unresolved', 'negative_witness_ineligible'),
            'restore_negative_witness_then_rerun')
        self.assertEqual(
            case_readiness._next_action('not_run', 'no_stage3_run'),
            'run_stage3')
        self.assertEqual(
            case_readiness._next_action('not_run', 'no_slice'),
            'build_negative_witness_slice')
        self.assertEqual(
            case_readiness._next_action('not_run', 'zero_claim_stage2'),
            'repair_stage2_zero_claims')

    def test_negative_stage2_reason_reads_claims(self):
        with __import__('tempfile').TemporaryDirectory() as tmp:
            goldset = Path(tmp) / 'goldset'
            case_dir = goldset / 'runs_01' / 'case_a'
            case_dir.mkdir(parents=True)
            (case_dir / 'stage3-spec.json').write_text(
                '{"claims": []}', encoding='utf-8')
            self.assertEqual(
                case_readiness._negative_stage2_reason('case_a', goldset),
                'zero_claim_stage2')
            (case_dir / 'stage3-spec.json').write_text(
                '{"claims": [{"claim_id": "c1", '
                '"formalization_status": "formalized_candidate"}]}',
                encoding='utf-8')
            self.assertEqual(
                case_readiness._negative_stage2_reason('case_a', goldset),
                'stage3_ready')

    def test_negative_slice_requires_flattened_contract(self):
        with __import__('tempfile').TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.assertFalse(case_readiness._negative_slice_ready('case_a', root))
            case_dir = root / 'case_a'
            case_dir.mkdir()
            (case_dir / 'contract.flattened.t.sol').write_text('// x')
            self.assertTrue(case_readiness._negative_slice_ready('case_a', root))


if __name__ == '__main__':
    unittest.main()
