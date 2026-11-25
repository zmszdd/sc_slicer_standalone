import unittest

from lib.stage2_contract import decide


class Stage2ContractTest(unittest.TestCase):
    def test_missing_contract_does_not_claim_auto_assert(self):
        gate = decide({})
        self.assertFalse(gate['blocking'])
        self.assertFalse(gate['auto_assert_allowed'])
        self.assertEqual(gate['route'], 'legacy_missing')

    def test_rejected_contract_blocks_before_binding(self):
        gate = decide({'status': 'rejected', 'route': 'stage2_repair',
                       'can_auto_assert': False})
        self.assertTrue(gate['blocking'])
        self.assertEqual(gate['category'], 'stage2_repair_required')

    def test_needs_review_blocks_auto_assert(self):
        gate = decide({'status': 'needs_review', 'route': 'binding_review',
                       'can_auto_assert': False})
        self.assertTrue(gate['blocking'])
        self.assertEqual(gate['category'], 'stage2_review_required')

    def test_ready_auto_assert_is_allowed(self):
        gate = decide({'status': 'ready', 'route': 'auto_assert',
                       'can_auto_assert': True})
        self.assertFalse(gate['blocking'])
        self.assertTrue(gate['auto_assert_allowed'])

    def test_unknown_route_fails_closed(self):
        gate = decide({'status': 'ready', 'route': 'future_fast_path',
                       'can_auto_assert': True})
        self.assertTrue(gate['blocking'])
        self.assertFalse(gate['auto_assert_allowed'])

    def test_semantic_review_routes_to_stage2_restatement(self):
        gate = decide({'status': 'needs_review', 'route': 'binding_review',
                       'can_auto_assert': False,
                       'warnings': ['I_V_TAUTOLOGY']})
        self.assertTrue(gate['blocking'])
        self.assertEqual(gate['semantic_route'], 'stage2_restatement')
        self.assertEqual(gate['category'],
                         'stage2_restatement_required')

    def test_snapshot_only_routes_to_stage2_restatement(self):
        gate = decide({'status': 'ready', 'route': 'auto_assert',
                       'can_auto_assert': True,
                       'problems': [{'code': 'I_SNAPSHOT_ONLY',
                                     'severity': 'advisory'}]})
        self.assertTrue(gate['blocking'])
        self.assertEqual(gate['semantic_route'], 'stage2_restatement')
        self.assertEqual(gate['category'],
                         'stage2_restatement_required')

    def test_reference_candidate_routes_to_reference_patch(self):
        gate = decide({'status': 'needs_review',
                       'route': 'reference_patch_candidate',
                       'can_auto_assert': False})
        self.assertEqual(gate['semantic_route'], 'reference_patch')
        self.assertEqual(gate['category'],
                         'stage2_reference_patch_candidate')

    def test_strict_gate_blocks_snapshot_only_auto_assert(self):
        gate = decide({
            'status': 'ready', 'route': 'auto_assert',
            'can_auto_assert': True,
            'semantic_profile': {'bucket': 'snapshot_only',
                                 'has_before_after': False},
            'i_v': {'independent': True},
        }, strict=True)
        self.assertTrue(gate['blocking'])
        self.assertEqual(gate['category'],
                         'stage2_strong_invariant_required')
        self.assertFalse(gate['auto_assert_allowed'])

    def test_strict_gate_allows_verified_transition(self):
        gate = decide({
            'status': 'ready', 'route': 'auto_assert',
            'can_auto_assert': True,
            'semantic_profile': {'bucket': 'transition',
                                 'has_before_after': True},
            'i_v': {'independent': True},
        }, strict=True)
        self.assertFalse(gate['blocking'])
        self.assertTrue(gate['auto_assert_allowed'])

    def test_strict_gate_allows_accepted_restatement_of_snapshot(self):
        gate = decide({
            'status': 'ready', 'route': 'auto_assert',
            'can_auto_assert': True,
            'semantic_profile': {'bucket': 'snapshot_only',
                                 'has_before_after': False},
            'invariant_restatement': {'status': 'restated',
                                      'accepted': True},
            'i_v': {'independent': True},
        }, strict=True)
        self.assertFalse(gate['blocking'])
        self.assertTrue(gate['auto_assert_allowed'])

    def test_trusted_negative_routes_to_negative_witness_without_blocking(self):
        gate = decide({
            'status': 'negative_witness', 'route': 'negative_witness',
            'negative_witness_route': {'eligible': True},
            'semantic_profile': {'bucket': 'snapshot_only'},
        }, strict=True)
        self.assertFalse(gate['blocking'])
        self.assertFalse(gate['auto_assert_allowed'])
        self.assertEqual(gate['semantic_route'], 'negative_witness')

    def test_aplus_records_snapshot_as_quality_label_without_blocking(self):
        gate = decide({
            'status': 'ready', 'route': 'auto_assert',
            'can_auto_assert': True,
            'semantic_profile': {'bucket': 'snapshot_only',
                                 'has_before_after': False},
            'i_v': {'independent': True},
            'checkpoint_missing': False, 'observable_missing': False,
            'problems': [{'code': 'I_SNAPSHOT_ONLY'}],
        }, mode='aplus')
        self.assertFalse(gate['blocking'])
        self.assertTrue(gate['auto_assert_allowed'])
        self.assertEqual(gate['gate_mode'], 'aplus')
        self.assertEqual(gate['semantic_route'], 'stage2_quality_label')
        self.assertIn('I_SNAPSHOT_ONLY', gate['quality_labels'])

    def test_aplus_still_blocks_missing_observability(self):
        gate = decide({
            'status': 'ready', 'route': 'auto_assert',
            'can_auto_assert': True,
            'semantic_profile': {'bucket': 'transition',
                                 'has_before_after': True},
            'i_v': {'independent': True},
            'checkpoint_missing': False, 'observable_missing': True,
        }, mode='aplus')
        self.assertTrue(gate['blocking'])
        self.assertEqual(gate['category'], 'stage2_strong_invariant_required')
        self.assertFalse(gate['auto_assert_allowed'])

    def test_aplus_downgrades_binding_review_with_soft_codes_only(self):
        gate = decide({
            'status': 'needs_review', 'route': 'binding_review',
            'can_auto_assert': False,
            'warnings': ['I_V_RESTATEMENT'],
            'semantic_profile': {'bucket': 'transition',
                                 'has_before_after': True},
            'i_v': {'independent': True},
            'checkpoint_missing': False, 'observable_missing': False,
        }, mode='aplus')
        self.assertFalse(gate['blocking'])
        self.assertTrue(gate['auto_assert_allowed'])
        self.assertIn('I_V_RESTATEMENT', gate['quality_labels'])

    def test_aplus_downgrades_report_only_observability_labels(self):
        gate = decide({
            'status': 'needs_review', 'route': 'binding_review',
            'can_auto_assert': False,
            'warnings': ['OBSERVABILITY_HIGH_RISK',
                         'OBSERVABILITY_REQUIRES_CODE_FACT',
                         'I_MUTATION_SITE_MISSING',
                         'I_SAME_CHECKPOINT_ONLY'],
            'semantic_profile': {'bucket': 'transition',
                                 'has_before_after': True},
            'i_v': {'independent': True},
            'checkpoint_missing': False, 'observable_missing': False,
        }, mode='aplus')
        self.assertFalse(gate['blocking'])
        self.assertTrue(gate['auto_assert_allowed'])
        self.assertEqual(gate['route'], 'auto_assert')

    def test_legacy_gate_keeps_report_only_observability_labels_blocking(self):
        gate = decide({
            'status': 'needs_review', 'route': 'binding_review',
            'can_auto_assert': False,
            'warnings': ['OBSERVABILITY_HIGH_RISK'],
        })
        self.assertTrue(gate['blocking'])
        self.assertFalse(gate['auto_assert_allowed'])

    def test_aplus_downgrades_clean_binding_review(self):
        gate = decide({
            'status': 'needs_review', 'route': 'binding_review',
            'can_auto_assert': False,
            'warnings': [],
            'semantic_profile': {'bucket': 'snapshot_only',
                                 'has_before_after': False},
            'i_v': {'independent': True},
            'checkpoint_missing': False, 'observable_missing': False,
        }, mode='aplus')
        self.assertFalse(gate['blocking'])
        self.assertTrue(gate['auto_assert_allowed'])
        self.assertEqual(gate['route'], 'auto_assert')


if __name__ == '__main__':
    unittest.main()
