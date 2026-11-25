import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'evaluation' / 'metrics'))
import mainline_backlog as mb


class Stage2FailureLabelTest(unittest.TestCase):
    def test_http_402_detected(self):
        self.assertEqual(
            mb._stage2_failure_label(
                {'core_formalization_status': 'failed',
                 'error': 'DeepSeek HTTP 402; response body not saved'}),
            'stage2_http_402')

    def test_no_marked_impact_section(self):
        self.assertEqual(
            mb._stage2_failure_label(
                {'core_formalization_status': 'not_attempted',
                 'impact_inventory_status': 'no_marked_impact_section'}),
            'report_no_marked_impact_section')

    def test_core_piv_not_fully_formalized(self):
        self.assertEqual(
            mb._stage2_failure_label(
                {'core_formalization_status': 'partial',
                 'continuation_blockers': ['core P/I/V is not fully formalized']}),
            'core_piv_not_fully_formalized')


class VerdictBucketTest(unittest.TestCase):
    def test_rebind_buckets(self):
        for verdict in ('partial_binding', 'compile_error', 'binding_error'):
            self.assertEqual(mb._verdict_bucket(verdict), 'rebind')

    def test_weak_invariant_bucket(self):
        self.assertEqual(mb._verdict_bucket('effect_observed_invariant_holds'),
                         'stage2_rerun')

    def test_reference_patch_bucket(self):
        for verdict in ('reference_patch_required', 'not_dynamically_expressible'):
            self.assertEqual(mb._verdict_bucket(verdict), 'reference_patch')


if __name__ == '__main__':
    unittest.main()
