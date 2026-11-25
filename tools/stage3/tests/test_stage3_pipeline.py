import tempfile
import unittest
from pathlib import Path

from cli import stage3_pipeline


class ViaIrToggleTest(unittest.TestCase):
    def _tmp(self, toml):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        (root / 'foundry.toml').write_text(toml)
        return root

    def test_enable_appends_to_default_config(self):
        root = self._tmp('[profile.default]\nsrc = "src"\ntest = "test"\n')
        self.assertTrue(stage3_pipeline._enable_via_ir(root))
        text = (root / 'foundry.toml').read_text()
        self.assertIn('via_ir = true', text)

    def test_enable_flips_false(self):
        root = self._tmp('via_ir = false\n')
        self.assertTrue(stage3_pipeline._enable_via_ir(root))
        self.assertIn('via_ir = true', (root / 'foundry.toml').read_text())

    def test_enable_noop_when_already_true(self):
        root = self._tmp('via_ir = true\n')
        self.assertFalse(stage3_pipeline._enable_via_ir(root))

    def test_retry_stack_too_deep_guard(self):
        run = {'ok': True, 'compile_error': None}
        self.assertIs(stage3_pipeline._retry_stack_too_deep(run, Path('/nonexistent')), run)

    def test_retry_enables_and_recovers(self):
        root = self._tmp('[profile.default]\n')
        original_forge = stage3_pipeline.run_forge_safe
        calls = []
        stage3_pipeline.run_forge_safe = lambda p: (
            calls.append(p) or {'ok': True, 'result': {}}
        )
        try:
            run = {'ok': False, 'compile_error': 'Error: too deep in the stack'}
            result = stage3_pipeline._retry_stack_too_deep(run, root)
        finally:
            stage3_pipeline.run_forge_safe = original_forge
        self.assertTrue(result['ok'])
        self.assertEqual(len(calls), 1)
        self.assertIn('via_ir = true', (root / 'foundry.toml').read_text())

    def test_retry_downgrades_when_ir_still_fails(self):
        root = self._tmp('via_ir = false\n')
        original_forge = stage3_pipeline.run_forge_safe
        stage3_pipeline.run_forge_safe = lambda p: {
            'ok': False, 'compile_error': 'Error: too deep in the stack'}
        try:
            run = {'ok': False, 'compile_error': 'Error: too deep in the stack'}
            result = stage3_pipeline._retry_stack_too_deep(run, root)
        finally:
            stage3_pipeline.run_forge_safe = original_forge
        self.assertFalse(result['ok'])
        self.assertIn('via_ir = false', (root / 'foundry.toml').read_text())

    def test_trusted_label_only_routes_unverified_stage2_restatement(self):
        source = (Path(__file__).resolve().parents[1] /
                  'cli' / 'stage3_pipeline.py').read_text()
        self.assertNotIn('execution_gate.inspect(', source)
        load = source.index('trusted_label = execution_gate.load_trusted_label(')
        build = source.index('stage2_restate.build_final_contract(')
        self.assertLess(load, build)
        self.assertIn('trusted_label=trusted_label', source)
        preflight = source.index('execution_gate.preflight(')
        adjudicate = source.index('execution_gate.adjudicate(')
        self.assertLess(preflight, adjudicate)

    def test_fallback_feedback_flags_unbound_invariant_symbols(self):
        with tempfile.TemporaryDirectory() as tmp:
            case = Path(tmp)
            stage2 = {'formal': {'claims': [{
                'id': 'c1',
                'properties': {
                    'preconditions': {'expression': {'var': 'p'}},
                    'safety': {'expression': {'var': 'i'}},
                    'effects': {'expression': {'var': 'v'}},
                },
            }]}}
            binding = {'bindings': {
                'p': {'solidity_expr': 'true'},
                'i': {'solidity_expr': 'UNBOUND'},
                'v': {'solidity_expr': 'UNBOUND'},
            }}
            feedback = stage3_pipeline.fallback_bindability_feedback(
                case, 'c1', stage2, binding)
        self.assertTrue(feedback['needs_restatement'])
        self.assertEqual(feedback['unbound_symbols'], ['i'])

    def test_fallback_feedback_is_derived_after_repair(self):
        source = (Path(__file__).resolve().parents[1] /
                  'cli' / 'stage3_pipeline.py').read_text()
        call = source.index('binding_feedback = fallback_bindability_feedback(')
        compile_call = source.index('compile_binding(binding, runtime_ir)')
        unbound_call = source.index('unbound_semantics.resolve_unbound(')
        self.assertLess(compile_call, call)
        self.assertLess(unbound_call, call)


class IndependentEffectGateTest(unittest.TestCase):
    def _gate(self, **overrides):
        values = {
            'verdict': {'consistency_verdict': 'violation_reproduced'},
            'reference_patch_used': False,
            'revert_expected': False,
            'effect_independent': True,
            'queries': {'P_and_T_and_V': 'unknown'},
            'witness': {'effect_witnessed': False},
        }
        values.update(overrides)
        return stage3_pipeline.independent_effect_gate(**values)

    def test_revert_route_without_effect_is_gated(self):
        gate = self._gate(revert_expected=True)
        self.assertEqual(gate['code'], 'REVERT_EFFECT_NOT_WITNESSED')
        self.assertEqual(gate['verdict'], 'effect_not_witnessed')

    def test_assert_route_without_effect_is_still_gated(self):
        gate = self._gate()
        self.assertEqual(gate['code'], 'EFFECT_NOT_WITNESSED')

    def test_independent_effect_clears_revert_route(self):
        self.assertIsNone(self._gate(
            revert_expected=True,
            queries={'P_and_T_and_V': 'sat'}))
        self.assertIsNone(self._gate(
            revert_expected=True,
            witness={'effect_witnessed': True}))

    def test_reference_patch_route_remains_exempt(self):
        self.assertIsNone(self._gate(
            revert_expected=True, reference_patch_used=True))

    def test_dependent_effect_is_rejected_before_witness(self):
        gate = self._gate(effect_independent=False,
                          queries={'P_and_T_and_V': 'sat'})
        self.assertEqual(gate['code'], 'EFFECT_NOT_INDEPENDENT')


if __name__ == '__main__':
    unittest.main()
