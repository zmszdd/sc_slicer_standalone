import unittest

from lib.verdict_loop import BINDING_FIXABLE_VERDICTS, NON_FIXABLE_VERDICTS, \
    REPAIR_LOOP_VERDICTS, TERMINAL_VERDICTS, repair_hint, verdict_action


class VerdictLoopTest(unittest.TestCase):
    def test_action_routing(self):
        for verdict in TERMINAL_VERDICTS:
            self.assertEqual(verdict_action(verdict), 'accept', verdict)
        for verdict in BINDING_FIXABLE_VERDICTS:
            self.assertEqual(verdict_action(verdict), 'rebind', verdict)
        self.assertEqual(verdict_action('inconclusive'),
                         'collect_missing_evidence')
        for verdict in NON_FIXABLE_VERDICTS:
            self.assertEqual(verdict_action(verdict), 'skip', verdict)
        self.assertEqual(verdict_action(None), 'rebind')

    def test_compile_error_hint_mentions_neutralized(self):
        summary = {
            'consistency_verdict': 'compile_error',
            'compile_error': {'patched': 'Undeclared identifier stakingManager'},
            'compile_retry': {'neutralized': ['a']},
        }
        hint = repair_hint(summary, None)
        self.assertIn('neutralized: [\'a\']', hint)
        self.assertIn('stakingManager', hint)

    def test_compile_blocked_hint_mentions_slice_failure(self):
        summary = {
            'consistency_verdict': 'compile_blocked',
            'compile_error': {'original': 'ParserError: expected but got'},
        }
        hint = repair_hint(summary, None)
        self.assertIn('original slice failed to compile', hint)
        self.assertIn('ParserError', hint)

    def test_binding_error_routes_to_rebind(self):
        self.assertEqual(verdict_action('binding_error'), 'rebind')
        hint = repair_hint(
            {'consistency_verdict': 'binding_error',
             'binding_error': {'reason': 'function testExploit not found'}},
            None)
        self.assertIn('testExploit not found', hint)

    def test_consistency_hint_prefers_replan_diagnostic(self):
        summary = {'consistency_verdict': 'partial_binding'}
        consistency = {'replan_diagnostic': {'hint': 'complete binding.json'}}
        self.assertEqual(repair_hint(summary, consistency),
                         'complete binding.json')

    def test_unbound_fallback(self):
        summary = {'consistency_verdict': 'partial_binding'}
        consistency = {'unbound_symbols': ['x', 'y']}
        self.assertEqual(repair_hint(summary, consistency),
                         'unbound symbols: x, y')

    def test_partial_binding_summary_unbound_hint(self):
        summary = {
            'consistency_verdict': 'partial_binding',
            'partial_binding': {'unbound_symbols': ['a', 'b'],
                                'reason': 'incomplete'},
        }
        self.assertEqual(repair_hint(summary, None),
                         'unbound symbols: a, b')

    def test_effect_observed_invariant_holds_routes_to_rebind(self):
        self.assertEqual(verdict_action('effect_observed_invariant_holds'),
                         'rebind')
        hint = repair_hint(
            {'consistency_verdict': 'effect_observed_invariant_holds'}, None)
        self.assertIn('restate I', hint)
        self.assertIn('vacuous', hint)

    def test_poc_not_witnessed_routes_to_skip(self):
        self.assertEqual(verdict_action('poc_not_witnessed'), 'skip')
        hint = repair_hint(
            {'consistency_verdict': 'poc_not_witnessed'}, None)
        self.assertIn('PoC did not witness P', hint)

    def test_preconditions_infeasible_poc_not_witnessed_skips(self):
        summary = {
            'consistency_verdict': 'preconditions_infeasible_on_code',
            'precondition_failure': 'poc_not_witnessed',
        }
        self.assertEqual(
            verdict_action('preconditions_infeasible_on_code', summary), 'skip')
        hint = repair_hint(summary, None)
        self.assertIn('PoC did not witness P', hint)

    def test_preconditions_infeasible_snapshot_unwitnessed_rebinds(self):
        summary = {
            'consistency_verdict': 'preconditions_infeasible_on_code',
            'precondition_failure': 'snapshot_unwitnessed',
        }
        self.assertEqual(
            verdict_action('preconditions_infeasible_on_code', summary),
            'rebind')
        hint = repair_hint(summary, None)
        self.assertIn('entry-level expression', hint)

    def test_preconditions_infeasible_hint_beats_replan_diagnostic(self):
        summary = {
            'consistency_verdict': 'preconditions_infeasible_on_code',
            'precondition_failure': 'snapshot_unwitnessed',
        }
        consistency = {
            'replan_diagnostic': {
                'hint': 'check binding.json against the Stage-2 binding_contract'
            }
        }
        self.assertIn('entry-level expression', repair_hint(summary, consistency))

    def test_preconditions_infeasible_without_failure_mode_rebinds(self):
        self.assertEqual(
            verdict_action('preconditions_infeasible_on_code'), 'rebind')

    def test_repair_loop_verdicts_covers_all_binding_fixable(self):
        self.assertTrue(BINDING_FIXABLE_VERDICTS <= REPAIR_LOOP_VERDICTS)
        for verdict in ('inconclusive', 'binding_failed'):
            self.assertIn(verdict, REPAIR_LOOP_VERDICTS)

    def test_fullflow_and_autorun_share_repair_loop_gate(self):
        from cli import stage3_autorun, stage3_fullflow
        self.assertIs(stage3_fullflow.REPAIR_LOOP_VERDICTS,
                      REPAIR_LOOP_VERDICTS)
        self.assertIs(stage3_autorun.REPAIR_LOOP_VERDICTS,
                      REPAIR_LOOP_VERDICTS)


if __name__ == '__main__':
    unittest.main()


class Stage3MultiDigTest(unittest.TestCase):
    def test_dig_returns_leaf(self):
        from cli.stage3_multi import _dig
        summary = {'forge': {'exploit': {'original': {'status': 'Success'}}}}
        self.assertEqual(_dig(summary, ['forge', 'exploit', 'original', 'status']),
                         'Success')

    def test_dig_none_midpath(self):
        from cli.stage3_multi import _dig
        self.assertIsNone(_dig({'forge': None}, ['forge', 'exploit', 'original', 'status']))
        self.assertIsNone(_dig({'forge': {'exploit': None}},
                                ['forge', 'exploit', 'original', 'status']))

    def test_dig_missing_returns_default(self):
        from cli.stage3_multi import _dig
        self.assertEqual(_dig({'forge': {}}, ['forge', 'exploit', 'status'], 'D'),
                         'D')
