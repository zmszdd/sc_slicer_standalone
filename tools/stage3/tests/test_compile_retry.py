import unittest
from pathlib import Path

from lib.compile_retry import error_identifiers

PIPELINE = Path(__file__).resolve().parents[1] / 'cli' / 'stage3_pipeline.py'


class CompileRetryTest(unittest.TestCase):
    def test_error_identifiers_from_caret_lines(self):
        stderr = (
            'Error (7920): Identifier not found or not unique.\n'
            '  --> src/Contract.sol:21975:9:\n'
            '   |\n'
            '   |     stakingManager.getPendingWithdrawalsCount() > 0\n'
            '   |     ^^^^^^^^^^^^^\n'
        )
        self.assertIn('stakingManager', error_identifiers(stderr))

    def test_error_identifiers_fallback_to_phrase_lines(self):
        stderr = (
            'Error (6160): Undeclared identifier. "ghostVar" is not visible.\n'
        )
        self.assertIn('ghostVar', error_identifiers(stderr))

    def test_compile_retry_has_no_neutralization_api(self):
        import lib.compile_retry as module
        self.assertFalse(hasattr(module, 'neutralize_binding'))
        self.assertFalse(hasattr(module, 'blacklist_symbols'))


class PipelineNeutralizationRegressionTest(unittest.TestCase):
    def test_compile_retry_no_longer_neutralizes_bindings(self):
        source = PIPELINE.read_text()
        self.assertNotIn('neutralize_binding(', source)
        self.assertIn('neutralization_disabled', source)

    def test_unbound_bindings_fail_closed_before_forge(self):
        source = PIPELINE.read_text()
        self.assertIn("'consistency_verdict': 'partial_binding'", source)
        self.assertIn("'unbound_symbols': unbound_symbols", source)

    def test_constant_binding_error_gates_before_forge(self):
        source = PIPELINE.read_text()
        self.assertIn("expressibility['expressibility'] == 'binding_error'", source)
        self.assertIn("'consistency_verdict': 'binding_error'", source)


if __name__ == '__main__':
    unittest.main()
