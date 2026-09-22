"""Active prompt assembly and inspection regressions; no model calls."""

import io
import sys
import unittest
from contextlib import redirect_stderr, redirect_stdout

from prompts.active import resolve_prompt_set
from prompts.definitions import PIV_DEFINITIONS, render_definitions
from prompts.registry import EXPERIMENTAL_VERSION, RECOMMENDED_VERSION
from prompts.versions import semantic_prompts_v316
import preview


class CanonicalDefinitionsTest(unittest.TestCase):
    def test_piv_definitions_are_central_and_distinct(self):
        self.assertEqual(tuple(item.symbol for item in PIV_DEFINITIONS), ('P', 'I', 'V'))
        rendered = render_definitions()
        self.assertIn('hold before the checked action', rendered)
        self.assertIn('property that should hold', rendered)
        self.assertIn('makes I false', rendered)


class ActivePromptTest(unittest.TestCase):
    def test_recommended_prompt_is_behavior_preserving(self):
        resolved = resolve_prompt_set(RECOMMENDED_VERSION)
        self.assertEqual(resolved.version, 'semantic-v3.16')
        self.assertEqual(resolved.element_prompt, semantic_prompts_v316.ID_ELEMENT_PROMPT)
        self.assertEqual(resolved.formal_prompt,
                         semantic_prompts_v316.formal_prompt('ids', 'core'))

    def test_resolved_prompt_exposes_stable_hashes(self):
        resolved = resolve_prompt_set()
        self.assertEqual(len(resolved.sha256('element')), 64)
        self.assertEqual(len(resolved.sha256('formal')), 64)
        with self.assertRaisesRegex(ValueError, 'unknown prompt part'):
            resolved.text('both')

    def test_experimental_prompt_also_satisfies_the_piv_contract(self):
        resolved = resolve_prompt_set(EXPERIMENTAL_VERSION)
        self.assertEqual(resolved.version, 'semantic-v3.17')
        self.assertIn('direct negation witness V', resolved.formal_prompt)

    def test_preview_prints_exact_resolved_prompt_without_model(self):
        previous = sys.argv
        out, err = io.StringIO(), io.StringIO()
        try:
            sys.argv = ['preview.py', 'prompt', '--part', 'element']
            with redirect_stdout(out), redirect_stderr(err):
                code = preview.main()
        finally:
            sys.argv = previous
        resolved = resolve_prompt_set()
        self.assertEqual(code, 0)
        self.assertEqual(out.getvalue(), resolved.element_prompt)
        self.assertIn(resolved.sha256('element'), err.getvalue())
        self.assertIn('"external_model_called": false', err.getvalue())
