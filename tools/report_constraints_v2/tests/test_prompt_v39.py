"""Offline controls for scenario-vs-history prompt refinement."""
import unittest

from cli import semantic_pipeline as pipeline
from prompts.versions import semantic_prompts_v38 as v38
from prompts.versions import semantic_prompts_v39 as v39


class PromptV39Tests(unittest.TestCase):
    def test_opt_in_version_preserves_v38(self):
        self.assertIs(pipeline.PROMPT_MODULES[v39.PROMPT_VERSION], v39)
        self.assertNotEqual(v39.ID_ELEMENT_PROMPT, v38.ID_ELEMENT_PROMPT)
        self.assertIn('P is an antecedent', v39.ID_ELEMENT_PROMPT)
        self.assertIn('historical state transition', v39.ID_ELEMENT_PROMPT)
        self.assertIn('TASK VERSION: semantic-v3.9', v39.formal_prompt('ids', 'core'))
        self.assertTrue(v39.formal_prompt('ids', 'core').endswith('DATA:\n'))

    def test_no_case_answers_in_prompt(self):
        prompt = v39.ID_ELEMENT_PROMPT + v39.formal_prompt('ids', 'core')
        for case_term in ('Forte', 'Merkl', 'Sukuk', 'Intuition', 'Brix'):
            self.assertNotIn(case_term, prompt)


if __name__ == '__main__':
    unittest.main()
