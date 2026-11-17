"""Trigger/liveness predicates must be kept out of I/V in the live prompt."""
import unittest

from prompts import current


class PromptTriggerRoleTests(unittest.TestCase):
    def test_live_prompt_contains_trigger_role_rule(self):
        prompt = current.FORMAL_PLAN_PROMPT
        self.assertIn('Trigger/liveness predicates stay in P, never in I or V',
                      prompt)
        self.assertIn('restricted_function_called', prompt)
        self.assertIn('create_gauge_callable_by_anyone', prompt)
        self.assertIn('distribution_call_reverts', prompt)

    def test_live_prompt_still_supports_ids_core_only(self):
        self.assertEqual(current.formal_prompt('ids', 'core'),
                         current.FORMAL_PLAN_PROMPT)


if __name__ == '__main__':
    unittest.main()
