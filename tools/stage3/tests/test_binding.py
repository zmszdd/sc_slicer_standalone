import json
import tempfile
import unittest
from pathlib import Path

from lib.binding import build_feedback, load_binding, validate_binding
from lib.spec_loader import load_stage2_run, required_symbols

CASE = Path(__file__).resolve().parents[1] / 'cases' / 'smoke_vault'


class BindingTest(unittest.TestCase):
    def setUp(self):
        self.stage2 = load_stage2_run(CASE / 'stage2_run')
        self.binding = load_binding(CASE / 'binding.json')

    def test_validate_and_required(self):
        claim_id, entries = validate_binding(self.binding, self.stage2['spec'])
        self.assertEqual(claim_id, 'claim_smoke_vault_double_withdraw')
        required = required_symbols(self.stage2['spec'], claim_id)
        self.assertEqual(required, {'balance_before', 'balance_after', 'amount'})
        self.assertEqual(set(entries), required)

    def test_feedback_shape(self):
        claim_id, entries = validate_binding(self.binding, self.stage2['spec'])
        feedback = build_feedback(claim_id, entries, {'P_and_T': 'sat'})
        self.assertEqual(feedback['schema_version'], 'stage3-consistency-feedback/1')
        self.assertTrue(all(row['status'] == 'bound'
                            for row in feedback['symbol_bindings'].values()))


if __name__ == '__main__':
    unittest.main()
