"""Active prompt assembly and inspection regressions; no model calls."""

import io
import sys
import unittest
from contextlib import redirect_stderr, redirect_stdout

from prompts.active import resolve_prompt_set
from prompts.definitions import PIV_DEFINITIONS, render_definitions
from prompts.registry import EXPERIMENTAL_VERSION, RECOMMENDED_VERSION
from prompts.versions import (semantic_prompts_v316, semantic_prompts_v318,
                              semantic_prompts_v319)
import preview


class CanonicalDefinitionsTest(unittest.TestCase):
    def test_piv_definitions_are_central_and_distinct(self):
        self.assertEqual(tuple(item.symbol for item in PIV_DEFINITIONS), ('P', 'I', 'V'))
        rendered = render_definitions()
        self.assertIn('hold before the checked action', rendered)
        self.assertIn('property that should hold', rendered)
        # V must NOT be defined as "makes I false": that would assume the very
        # conclusion that the P AND V AND I check exists to establish.
        self.assertIn('defined independently of I', rendered)
        self.assertIn('P AND V AND I check', rendered)


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
        # Deliberately version-agnostic: ``resolve_prompt_set`` already asserts the
        # P/I/V contract markers for whatever the label points at, so this test
        # pins the label to its module instead of to a wording that will move.
        resolved = resolve_prompt_set(EXPERIMENTAL_VERSION)
        self.assertEqual(resolved.version, EXPERIMENTAL_VERSION)
        self.assertEqual(resolved.formal_prompt,
                         semantic_prompts_v319.formal_prompt('ids', 'core'))

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


class LegacyPatternKindRemovalTest(unittest.TestCase):
    """The formal prompt must never offer a pattern kind the compiler rejects.

    ``FIXED_RELATION_CLASS_PATTERN`` admits exactly three kinds -- monotonicity,
    conservation and relation_obligation -- yet the v3.16 formal prompt inherited
    text that specified the fields of the legacy condition_*_effect shapes and
    told the model to *use* one of them for "a valid operation should complete but
    instead reverts".  That case is ``progress_or_liveness``, which the fixed
    template reserves for relation_obligation, so the prompt contradicted itself
    and the model resolved the contradiction by disobeying the template (3/10
    obedient on that class, against 10/10 on every other class measured).
    """

    LEGACY_KINDS = ('condition_forbids_effect', 'condition_requires_effect')

    def test_recommended_version_still_carries_the_legacy_guidance(self):
        # Negative control.  If v3.16 stopped naming the legacy shapes this suite
        # would prove nothing about the version that removes them.
        prompt = resolve_prompt_set(RECOMMENDED_VERSION).formal_prompt
        for kind in self.LEGACY_KINDS:
            self.assertIn(kind, prompt)

    def test_experimental_version_never_names_a_legacy_pattern_kind(self):
        prompt = resolve_prompt_set(EXPERIMENTAL_VERSION).formal_prompt
        for kind in self.LEGACY_KINDS:
            self.assertNotIn(kind, prompt)

    def test_experimental_version_keeps_the_fixed_template_mandate(self):
        prompt = resolve_prompt_set(EXPERIMENTAL_VERSION).formal_prompt
        for phrase in ('you do NOT choose among',
                       'monotonicity MUST use kind monotonicity',
                       'conservation MUST use kind conservation',
                       'every other class MUST use kind relation_obligation'):
            self.assertIn(phrase, prompt)

    def test_experimental_version_pins_progress_or_liveness(self):
        prompt = resolve_prompt_set(EXPERIMENTAL_VERSION).formal_prompt
        self.assertIn('progress_or_liveness class MUST keep kind relation_obligation',
                      prompt)

    def test_experimental_version_does_not_move_the_plan_schema(self):
        # A prompt-only fix must keep the compiler contract it was measured under.
        prompt = resolve_prompt_set(EXPERIMENTAL_VERSION).formal_prompt
        self.assertIn('report-formal-plan/4', prompt)
        self.assertNotIn('report-formal-plan/5', prompt)

    def test_each_version_differs_from_its_base_only_in_declared_regions(self):
        # (derived module, the version it derives from, the regions it declares)
        cases = (
            (semantic_prompts_v318, 'semantic-v3.16',
             ((semantic_prompts_v318._LEGACY_POLARITY,
               semantic_prompts_v318._FIXED_POLARITY),
              (semantic_prompts_v318._LEGACY_FIELD_SPEC,
               semantic_prompts_v318._FIXED_FIELD_SPEC),
              (semantic_prompts_v318._LEGACY_AUDIT_MENTION,
               semantic_prompts_v318._FIXED_AUDIT_MENTION))),
            (semantic_prompts_v319, 'semantic-v3.18',
             ((semantic_prompts_v319._LEGACY_ACCESS_CONTROL_RULE,
               semantic_prompts_v319._FIXED_ACCESS_CONTROL_RULE),)),
        )
        for module, base, pairs in cases:
            with self.subTest(version=module.PROMPT_VERSION):
                legacy = resolve_prompt_set(base).formal_prompt
                fixed = module.formal_prompt('ids', 'core')
                self.assertNotEqual(legacy, fixed)
                for old, new in pairs:
                    self.assertIn(old, legacy)
                    self.assertIn(new, fixed)
                    legacy = legacy.replace(old, '\x00')
                    fixed = fixed.replace(new, '\x00')
                # Everything outside the declared regions is byte-identical, so a
                # measured effect cannot be attributed to an accidental extra edit.
                self.assertEqual(legacy, fixed)


class AccessControlImpactCitationTest(unittest.TestCase):
    """The access-control relation must be able to cite the selected impact.

    ``classified_relation_alignment`` requires every selected ``impact_id`` to be
    cited by a symbol appearing in ``relation``; condition-only triggers explicitly
    do not count.  The v3.16 class guidance instead said access control's ``relation``
    *is the required authorization*, and only preconditions can source an
    authorization predicate -- so the two rules could not both hold and the prompt
    never stated precedence.  The measured consequence was that the only plans
    passing validation were the ones that broke the class rule.
    """

    LEGACY_RULE = 'relation is the required\nauthorization'
    FIXED_RULE = 'Relation must cite the selected impact on a relation symbol'

    def test_base_version_still_pins_relation_to_authorization(self):
        # Negative control: the contradiction must be visible where it started.
        prompt = resolve_prompt_set('semantic-v3.18').formal_prompt
        self.assertIn(self.LEGACY_RULE, prompt)

    def test_experimental_version_drops_the_authorization_only_rule(self):
        prompt = resolve_prompt_set(EXPERIMENTAL_VERSION).formal_prompt
        self.assertNotIn(self.LEGACY_RULE, prompt)

    def test_experimental_version_states_the_citation_duty(self):
        prompt = resolve_prompt_set(EXPERIMENTAL_VERSION).formal_prompt
        self.assertIn(self.FIXED_RULE, prompt)
        self.assertIn("relation is the ABSENCE of the impact", prompt)

    def test_experimental_version_keeps_the_grounding_rule_itself(self):
        # The fix must not soften the rule it exists to satisfy.
        prompt = resolve_prompt_set(EXPERIMENTAL_VERSION).formal_prompt
        self.assertIn('Trigger/condition-only variables do', prompt)
        self.assertIn('EVERY selected impact_id', prompt)

    def test_experimental_version_leaves_progress_or_liveness_alone(self):
        prompt = resolve_prompt_set(EXPERIMENTAL_VERSION).formal_prompt
        self.assertIn(
            'For progress/liveness, condition is the valid operation scenario', prompt)
