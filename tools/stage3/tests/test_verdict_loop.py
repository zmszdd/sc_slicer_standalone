import unittest
import json
import tempfile
from pathlib import Path

from lib.verdict_loop import BINDING_FIXABLE_VERDICTS, EVIDENCE_VERDICTS, \
    NON_FIXABLE_VERDICTS, REPAIR_LOOP_VERDICTS, TERMINAL_VERDICTS, \
    repair_hint, verdict_action


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

    def test_terminal_semantic_unbound_skips_rebinding(self):
        summary = {
            'consistency_verdict': 'partial_binding',
            'partial_binding': {
                'unbound_route_suggestion':
                    'stage2_restate_or_reference_patch',
                'semantic_terminal_unresolved': True,
            },
        }
        self.assertEqual(verdict_action('partial_binding', summary), 'skip')

    def test_partial_binding_hint_names_semantic_buckets(self):
        summary = {
            'consistency_verdict': 'partial_binding',
            'partial_binding': {
                'unbound_symbols': ['a'],
                'unbound_buckets': {'semantic_time_window': 1,
                                    'semantic_effect_only': 2},
            },
        }
        hint = repair_hint(summary, None)
        self.assertIn('semantic_time_window', hint)
        self.assertNotIn('semantic_effect_only', hint)
        self.assertIn('one attempt', hint)

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

    def test_inconclusive_business_revert_hint_targets_injection_point(self):
        summary = {
            'consistency_verdict': 'inconclusive',
            'forge': {'exploit': {
                'original': {'status': 'Success'},
                'patched': {'status': 'Failure',
                            'reason': 'ERC721NonexistentToken(1)'},
            }},
        }
        hint = repair_hint(summary, None)
        self.assertIn('ERC721NonexistentToken(1)', hint)
        self.assertIn('injection point', hint)

    def test_inconclusive_no_revert_falls_back_to_restate_i(self):
        summary = {
            'consistency_verdict': 'inconclusive',
            'forge': {'exploit': {
                'original': {'status': 'Success'},
                'patched': {'status': 'Success'},
            }},
        }
        hint = repair_hint(summary, None)
        self.assertIn('restate I', hint)

    def test_inconclusive_hint_asks_to_restate_i(self):
        hint = repair_hint({'consistency_verdict': 'inconclusive'}, None)
        self.assertIn('restate I', hint)
        self.assertIn('witness', hint)

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

    def test_terminal_verdict_sets_derive_from_single_source(self):
        from cli import (full_flow_metrics, full_metrics, metrics_report,
                         stage3_negative_batch, stage3_negative_eval)
        self.assertEqual(metrics_report.DYNAMIC, tuple(TERMINAL_VERDICTS))
        self.assertIs(full_metrics.TERMINAL, TERMINAL_VERDICTS)
        self.assertIs(full_metrics.VERIFIABLE, EVIDENCE_VERDICTS)
        self.assertEqual(full_flow_metrics.DYNAMIC_VERDICTS,
                         tuple(TERMINAL_VERDICTS))
        self.assertIs(stage3_negative_batch.TERMINAL, TERMINAL_VERDICTS)
        self.assertIs(stage3_negative_eval.VERDICTS, EVIDENCE_VERDICTS)


if __name__ == '__main__':
    unittest.main()


class VerdictLoopTerminalRecordTest(unittest.TestCase):
    def test_reproduced_flag_distinguishes_terminal_verdicts(self):
        from cli.stage3_verdict_loop import _terminal_record
        reproduced = _terminal_record('c1', 'violation_reproduced', [])
        not_reproduced = _terminal_record('c2', 'violation_not_reproduced', [])
        self.assertTrue(reproduced['reproduced'])
        self.assertFalse(not_reproduced['reproduced'])
        self.assertEqual(reproduced['status'], 'accepted')
        self.assertEqual(not_reproduced['status'], 'accepted')


class VerdictLoopRunPrefixTest(unittest.TestCase):
    def test_fresh_prefix_includes_timestamp_and_varies(self):
        from cli.stage3_verdict_loop import _fresh_run_prefix
        a = _fresh_run_prefix(None, 'case_name')
        b = _fresh_run_prefix(None, 'case_name')
        self.assertIn('case_name', a)
        self.assertNotEqual(a, b)
        self.assertTrue(a.split('__')[-1].startswith('20'))

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


class PocShapeTest(unittest.TestCase):
    def _case(self, src_files: dict[str, str], probe: dict | None):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        src = root / 'src'
        src.mkdir()
        for name, text in src_files.items():
            (src / name).write_text(text)
        bindings = root / 'bindings'
        bindings.mkdir()
        (bindings / 'p.json').write_text(json.dumps({'probe': probe}))
        return root

    def test_exploit_body_expect_revert_is_revert_expected(self):
        from cli.stage3_verdict_loop import _poc_shape
        case = self._case(
            {'A.sol': 'function test_exploit() public {\n'
                      '    vm.expectRevert(bytes("boom"));\n'
                      '    target.run();\n'
                      '}\n'},
            {'exploit_test': 'test_exploit'})
        self.assertEqual(_poc_shape(case), 'revert_expected_test')

    def test_other_file_expect_revert_does_not_poison_state_assert(self):
        from cli.stage3_verdict_loop import _poc_shape
        case = self._case(
            {'A.sol': 'function helper() public pure returns (bool) {\n'
                      '    return true;\n'
                      '}\n',
             'B.sol': 'function test_exploit() public {\n'
                      '    assert(target.balance() == 0);\n'
                      '}\n',
             'C.sol': 'function unrelated() public { vm.expectRevert(); }\n'},
            {'exploit_test': 'test_exploit'})
        self.assertEqual(_poc_shape(case), 'state_assert_test')

    def test_missing_exploit_test_is_no_body(self):
        from cli.stage3_verdict_loop import _poc_shape
        case = self._case({'A.sol': 'contract A {}'}, {})
        self.assertEqual(_poc_shape(case), 'no_body')

    def test_function_not_found_is_other_test(self):
        from cli.stage3_verdict_loop import _poc_shape
        case = self._case(
            {'A.sol': 'contract A { function run() public {} }'},
            {'exploit_test': 'test_missing'})
        self.assertEqual(_poc_shape(case), 'other_test')
