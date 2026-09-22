"""Polarity prompt versioning regressions."""
import unittest

from prompts.versions import semantic_prompts_v313 as previous
from prompts.versions import semantic_prompts_v314 as current


class PromptV314Tests(unittest.TestCase):
    def test_polarity_rule_is_new_and_explicit(self):
        self.assertNotIn('condition requires revert', previous.FORMAL_PLAN_PROMPT)
        prompt = current.formal_prompt('ids', 'core')
        self.assertIn('semantic-v3.14', prompt)
        self.assertIn('condition requires revert', prompt)
        self.assertIn('program-generated V MUST describe the selected impact', prompt)
        self.assertIn('condition forbids revert', prompt)
        self.assertIn('never emit placeholders such as not_applicable', prompt)
        self.assertIn('Never encode a BEFORE condition', prompt)
        self.assertIn('another selected P is allowed', prompt)
        self.assertIn('expected-versus-actual values', current.ID_ELEMENT_PROMPT)
        self.assertIn('operands, operator/direction', current.ID_ELEMENT_PROMPT)


if __name__ == '__main__':
    unittest.main()
