import tempfile
import unittest
from pathlib import Path

from lib import bindability_feedback


class BindabilityFeedbackTest(unittest.TestCase):
    def test_unbound_symbol_requests_restatement(self):
        row = bindability_feedback.build(
            'c1', bindability='single_anchor',
            binding_record={'status': 'bound', 'unbound': ['tree_size']},
            observable_ir={'patch_contract': 'Vault',
                           'patch_functions': ['deposit'],
                           'symbols': {'tree_size': {'candidates': []}}})
        self.assertTrue(row['needs_restatement'])
        self.assertEqual(row['requested_route'],
                         'stage2_code_grounded_restatement')
        self.assertEqual(row['patch_contract'], 'Vault')

    def test_accepted_reference_patch_clears_restatement_request(self):
        row = bindability_feedback.build(
            'c1', binding_record={'status': 'bound', 'unbound': ['x']},
            reference_patch={'accepted': True})
        self.assertFalse(row['needs_restatement'])
        self.assertTrue(row['reference_patch_accepted'])

    def test_accepted_binding_clears_invisible_candidate_feedback(self):
        row = bindability_feedback.build(
            'c1', bindability='multi_contract',
            binding_record={'status': 'bound', 'unbound': []},
            observable_ir={'patch_contract': 'Vault',
                           'patch_functions': ['deposit'],
                           'symbols': {'effect': {'candidates': [
                               {'visible_at_injection': False}]}}})
        self.assertFalse(row['needs_restatement'])
        self.assertEqual(row['requested_route'], 'continue_stage3')
        self.assertEqual(row['invisible_symbols'], ['effect'])

    def test_apply_to_contract_blocks_unless_restatement_accepted(self):
        contract = {'status': 'ready', 'route': 'auto_assert',
                    'can_auto_assert': True, 'problems': []}
        feedback = bindability_feedback.build(
            'c1', binding_record={'status': 'bound', 'unbound': ['x']})
        blocked = bindability_feedback.apply_to_contract(contract, feedback)
        self.assertEqual(blocked['route'], 'binding_review')
        self.assertFalse(blocked['can_auto_assert'])
        self.assertEqual(
            blocked['problems'][0]['code'], 'BINDABILITY_FEEDBACK_UNRESOLVED')
        contract['invariant_restatement'] = {
            'accepted': True, 'status': 'restated',
            'changes': [{'symbol': 'x'}],
        }
        accepted = bindability_feedback.apply_to_contract(contract, feedback)
        self.assertEqual(accepted['route'], 'auto_assert')

    def test_accepted_unchanged_restatement_still_blocks(self):
        contract = {
            'status': 'ready', 'route': 'auto_assert',
            'can_auto_assert': True, 'problems': [],
            'invariant_restatement': {
                'accepted': True, 'status': 'unchanged', 'changes': [],
            },
        }
        feedback = bindability_feedback.build(
            'c1', binding_record={'status': 'bound', 'unbound': ['x']})
        blocked = bindability_feedback.apply_to_contract(contract, feedback)
        self.assertEqual(blocked['route'], 'binding_review')
        self.assertEqual(
            blocked['problems'][0]['code'], 'BINDABILITY_FEEDBACK_UNRESOLVED')

    def test_index_round_trip(self):
        row = bindability_feedback.build(
            'c1', binding_record={'status': 'failed'})
        with tempfile.TemporaryDirectory() as tmp:
            case = Path(tmp)
            path = bindability_feedback.write(case, [row])
            self.assertTrue(path.is_file())
            loaded = bindability_feedback.load(case)
        self.assertEqual(loaded['c1'], row)


if __name__ == '__main__':
    unittest.main()
