"""Pin the reference-patch gate to the binding lint, not the anchor upper bound.

Regression: an earlier version gated on ``routing['requires_reference_patch']``
(anchor upper bound) and would have discarded every multi_contract claim whose
binding is still single-contract-injectable -- collapsing recall. The gate must
key off ``expressibility['reference_patch_required']`` (actual binding lint).
"""
import unittest
from pathlib import Path

PIPELINE = Path(__file__).resolve().parents[1] / 'cli' / 'stage3_pipeline.py'


class RoutingGateRegressionTest(unittest.TestCase):
    def test_gate_keys_off_binding_expressibility(self):
        source = PIPELINE.read_text()
        self.assertIn("expressibility['reference_patch_required']", source)
        self.assertNotIn("routing['requires_reference_patch'] and not", source)

    def test_routing_still_written_as_advisory(self):
        source = PIPELINE.read_text()
        self.assertIn("write_json(run_dir / 'routing.json', routing)", source)


if __name__ == '__main__':
    unittest.main()
