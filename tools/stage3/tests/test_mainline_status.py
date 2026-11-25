import unittest

from lib.mainline_status import (aggregate_claim_status, build_case_status,
                                 claim_status, stage1_status, stage2_status,
                                 stage3_status)


class MainlineStatusTest(unittest.TestCase):
    def test_stage1_compile_ok_without_test_entrypoint_is_not_ready(self):
        status = stage1_status(
            compile_status='ok', test_entrypoint=False,
            poc_action='snippet_only')
        self.assertFalse(status['data_ready'])
        self.assertIn('no_test_entrypoint', status['blockers'])

    def test_stage1_compiling_recoverable_harness_is_ready(self):
        status = stage1_status(
            compile_status='ok', test_entrypoint=True,
            poc_action='snippet_only')
        self.assertTrue(status['data_ready'])
        self.assertEqual(status['blockers'], [])

    def test_stage1_fork_rpc_is_not_self_contained(self):
        status = stage1_status(
            compile_status='ok', test_entrypoint=True,
            poc_action='fork_rpc')
        self.assertFalse(status['data_ready'])
        self.assertIn('poc_fork_rpc', status['blockers'])

    def test_stage2_snapshot_warning_blocks_claim(self):
        status = stage2_status(contract={
            'route': 'auto_assert', 'can_auto_assert': True,
            'problems': [{'code': 'I_SNAPSHOT_ONLY'}],
        })
        self.assertFalse(status['claim_ready'])
        self.assertIn('I_SNAPSHOT_ONLY', status['blockers'])

    def test_stage2_clean_auto_assert_is_ready(self):
        status = stage2_status(contract={
            'route': 'auto_assert', 'can_auto_assert': True,
            'problems': [], 'warnings': [], 'advisories': [],
        })
        self.assertTrue(status['claim_ready'])

    def test_stage2_weak_invariant_blocks_claim(self):
        status = stage2_status(
            contract={'route': 'auto_assert', 'can_auto_assert': True},
            weak_invariant={'risk': 'high',
                            'codes': ['I_LAYER_MISMATCH']})
        self.assertFalse(status['claim_ready'])
        self.assertIn('I_LAYER_MISMATCH', status['blockers'])

    def test_stage3_requires_both_binding_and_execution(self):
        status = stage3_status(binding_ready=True, execution_ready=False)
        self.assertFalse(status['eligible_for_metrics'])
        self.assertIn('execution_not_ready', status['blockers'])

    def test_case_status_propagates_stage_blockers(self):
        row = build_case_status(
            case_id='c1', project='p1',
            stage1=stage1_status(compile_status='ok', test_entrypoint=True),
            stage2=stage2_status(contract={
                'route': 'binding_review', 'can_auto_assert': False}),
            stage3=stage3_status(binding_ready=False, execution_ready=False),
        )
        self.assertFalse(row['claim_ready'])
        self.assertFalse(row['eligible_for_metrics'])
        self.assertIn('stage2:stage2_route_binding_review', row['blockers'])

    def test_claim_status_requires_stage2_gate_and_execution(self):
        row = claim_status(
            claim_id='c1',
            stage2_gate={'blocking': False, 'category': None},
            weak_gate={'blocking': False},
            binding_ready=True,
            execution={'status': 'done',
                       'consistency_verdict': 'violation_reproduced'})
        self.assertTrue(row['eligible_for_metrics'])

    def test_restatement_claim_is_never_execution_ready(self):
        row = claim_status(
            claim_id='c1',
            stage2_gate={'blocking': True,
                         'category': 'stage2_restatement_required'},
            binding_ready=True,
            execution={'status': 'done',
                       'consistency_verdict': 'stage2_restatement_required'})
        self.assertFalse(row['eligible_for_metrics'])
        self.assertFalse(row['execution_ready'])

    def test_reference_patch_required_is_not_eligible(self):
        row = claim_status(
            claim_id='c1',
            stage2_gate={'blocking': False, 'category': None},
            binding_ready=True,
            execution={'status': 'done',
                       'consistency_verdict': 'reference_patch_required'})
        self.assertFalse(row['eligible_for_metrics'])

    def test_aggregate_does_not_mix_binding_from_one_claim_with_execution_of_another(self):
        stage2, stage3, rows = aggregate_claim_status([
            {'claim_id': 'bound-only', 'claim_ready': True,
             'binding_ready': True, 'execution_ready': False,
             'eligible_for_metrics': False, 'blockers': []},
            {'claim_id': 'executed-unbound', 'claim_ready': True,
             'binding_ready': False, 'execution_ready': True,
             'eligible_for_metrics': False, 'blockers': []},
        ])
        self.assertTrue(stage2['claim_ready'])
        self.assertFalse(stage3['eligible_for_metrics'])
        self.assertEqual(len(rows), 2)


if __name__ == '__main__':
    unittest.main()
