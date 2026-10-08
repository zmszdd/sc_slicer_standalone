"""The single live prompt: contract, feature decoupling, CLI reachability."""
import unittest

from prompts import current
from prompts.active import resolve_prompt_set
from prompts import registry
from prompts.definitions import ELEMENT_CONTRACT_MARKERS, FORMAL_CONTRACT_MARKERS
from semantic_pipeline import formal_repair_fields


class LivePromptTests(unittest.TestCase):
    def test_live_prompt_resolves_and_keeps_piv_markers(self):
        resolved = resolve_prompt_set('semantic-live')
        self.assertEqual(resolved.version, 'semantic-live')
        self.assertEqual(resolved.element_prompt, current.ID_ELEMENT_PROMPT)
        self.assertEqual(resolved.formal_prompt, current.FORMAL_PLAN_PROMPT)
        # _assert_piv_contract covers the live version, so a marker going
        # missing in an in-place edit fails resolution; assert it directly too.
        for marker in ELEMENT_CONTRACT_MARKERS:
            self.assertIn(marker, resolved.element_prompt)
        for marker in FORMAL_CONTRACT_MARKERS:
            self.assertIn(marker, resolved.formal_prompt)

    def test_live_formal_prompt_only_supports_ids_core(self):
        with self.assertRaises(ValueError):
            current.formal_prompt('quotes', 'full')
        self.assertEqual(current.formal_prompt('ids', 'core'),
                         current.FORMAL_PLAN_PROMPT)

    def test_live_formal_prompt_keeps_fixed_template_mandate(self):
        formal = current.FORMAL_PLAN_PROMPT
        for phrase in ('monotonicity MUST use kind monotonicity with trigger, before_symbol,',
                       'conservation MUST use kind conservation with trigger, before and after;',
                       'every other class MUST use kind relation_obligation with condition and relation.'):
            self.assertIn(phrase, formal)

    def test_live_element_prompt_keeps_p_temporal_role_mandate(self):
        # blind-03 attribution: formula-layer P failures were all inherited from
        # the element layer admitting action-produced observations as P.  The
        # live prompt forbids it; this guard keeps the rule from silently
        # disappearing in a later in-place edit.
        element = current.ID_ELEMENT_PROMPT
        for phrase in ('An action-produced observation is equally never P',
                       'is an outcome, not a precondition',
                       'prior state only when separate fragments establish it before '
                       'the action begins',
                       'the precondition is circular'):
            self.assertIn(phrase, element)

    def test_live_formal_prompt_keeps_rate_and_i_applicability_mandates(self):
        # prompt_live1_blind_01 attribution: Hybra fabricated
        # expected_rate = total * 1 because QEXPR cannot express division, and
        # SukukFi's I narrowed the report's general caller-not-owner
        # requirement to the concrete scenario subcase.  Guards keep both
        # live-2 rules from silently disappearing in a later in-place edit.
        formal = current.FORMAL_PLAN_PROMPT
        for phrase in ('Rates and ratios cannot be defined',
                       'QEXPR has no divisor',
                       'Never multiply by 1 or another constant to force a unit match',
                       'never fabricate an identity',
                       'The condition of I carries the intent',
                       'makes I protect only the subcase',
                       'record the narrowing in limitations',
                       'Compare the condition of I against the intent statement'):
            self.assertIn(phrase, formal)
        # The formal prompt's own audit list must keep the applicability check.
        self.assertIn("7. Compare the condition of I against the intent statement", formal)

    def test_live_formal_prompt_keeps_constant_literal_mandates(self):
        # prompt_live2_blind_01 attribution: Panoptic expressed a 12-bit width
        # bound as the computed constant 4096 and Hybra expressed an explicit
        # `_gaugeType == 1` bound as a named symbol, so the numeric gate
        # correctly rejected both while the repair channel then discarded the
        # direction-correct repairs.  Guards keep the live-3 constant-form rule
        # from silently disappearing in a later in-place edit.
        formal = current.FORMAL_PLAN_PROMPT
        self.assertIn('TASK VERSION: semantic-live-5', formal)
        for phrase in ('Every explicit bound constant must be a literal',
                       'appears in the cited report text',
                       'never 2^12, 4096, or a',
                       'symbol standing for the constant',
                       'record that bound in unresolved',
                       'instead of inventing a'):
            self.assertIn(phrase, formal)

    def test_live_formal_prompt_keeps_duplicate_predicate_mandate(self):
        # prompt_live3_blind_01 attribution: both Panoptic candidates collapsed
        # two distinct extracted facts onto one repeated truth predicate, so one
        # fact stopped being represented.  Guards keep the live-4 audit-list
        # extension from silently disappearing in a later in-place edit.
        formal = current.FORMAL_PLAN_PROMPT
        # Phrases avoid the prompt's mid-phrase line breaks.
        for phrase in ('Two different precondition sources must never share one',
                       'identical predicate',
                       'the conjunction collapses to a single fact',
                       'move it to assumptions instead of repeating the',
                       "first fact's predicate"):
            self.assertIn(phrase, formal)

    def test_live_formal_prompt_keeps_partial_formalization_mandate(self):
        # Post-closure semantic-live-5 rule (goal-directed, disclosed as an
        # iteration outside the closed blind-batch cycle): a rate relation the
        # DSL cannot express gets ONE declared bool symbol standing for the
        # whole relation plus a NONBLOCKING unsupported_relation item, instead
        # of a blocking rejection that discards the derived invariant.
        # Attributed to the disclosed blocking family: live1 Hybra
        # expected_rate fabrication and the SukukFi/Monetrix decimal-binding
        # rejections.
        formal = current.FORMAL_PLAN_PROMPT
        for phrase in ('represent that whole rate relation as ONE declared',
                       'Record\nthe missing numeric definition as a NONBLOCKING',
                       'never leave the rate',
                       'relation both unrepresented and nonblocking'):
            self.assertIn(phrase, formal)

    def test_repair_feedback_prescribes_concrete_changes(self):
        # prompt_live3_blind_01 / live1 attribution: repairs that resubmitted the
        # previous plan byte-identically repaired nothing, and type/unit
        # rejections lacked the cross-multiplication recipe.
        from semantic_pipeline import formal_retry_hint
        no_change = formal_retry_hint(ValueError('local repair made no change'))
        self.assertIn('repairs nothing', no_change)
        self.assertIn('Produce a', no_change)
        unit = formal_retry_hint(ValueError('type/unit mismatch'))
        self.assertIn('cross-multiplied relation', unit)
        self.assertIn('never define a derived symbol', unit)

    def test_numeric_repair_fields_allow_pattern(self):
        # prompt_live2_blind_01 attribution: both constant-expression rejections
        # died as "local repair changed frozen fields" because the numeric
        # gate's repair scope omitted pattern, so a direction-correct repair
        # that rewrote the comparison predicate was mechanically discarded.
        for message in ('numeric P literal changed',
                        'numeric P bound hidden by non-comparison predicate',
                        'numeric P literal or direction changed',
                        'numeric P source missing from plan'):
            fields = formal_repair_fields(ValueError(message))
            self.assertIn('pattern', fields, message)
            self.assertIn('precondition_terms', fields, message)


class FeatureDecouplingTests(unittest.TestCase):
    def test_feature_names_match_live_features(self):
        self.assertEqual(set(current.FEATURES), set(registry.FEATURE_NAMES))

    def test_feature_enabled_reads_live_features(self):
        for name, value in current.FEATURES.items():
            self.assertEqual(registry.feature_enabled('semantic-live', name), value)

    def test_live_features_match_the_v320_generation_baseline(self):
        # Locks the creation baseline: the live file was flattened from
        # semantic-v3.20 and v3.16/v3.20 agree on every inherited feature, so
        # the default switch changed only the prompt text.  Live features added
        # after the switch are asserted explicitly instead.  Recorded per run
        # via provenance.prompt_features.
        post_baseline = {'assumption_numeric_relief', 'duplicate_predicate_gate',
                         'requirement_source_review', 'intent_scope_review',
                         'partial_formalization', 'example_pinning_review'}
        inherited = [name for name in registry.FEATURE_NAMES
                     if name not in post_baseline]
        for version in ('semantic-v3.16', 'semantic-v3.20'):
            self.assertEqual({name: registry.feature_enabled('semantic-live', name)
                              for name in inherited},
                             {name: registry.feature_enabled(version, name)
                              for name in inherited})
        # semantic-live-2: the numeric gate no longer forces narrative
        # assumptions into P; every frozen version keeps the strict gate.
        self.assertTrue(registry.feature_enabled('semantic-live',
                                                 'assumption_numeric_relief'))
        self.assertFalse(registry.feature_enabled('semantic-v3.16',
                                                  'assumption_numeric_relief'))
        self.assertFalse(registry.feature_enabled('semantic-v3.20',
                                                  'assumption_numeric_relief'))
        # semantic-live-5 (post-closure): the four structural additions are
        # live-only; every frozen version keeps the behaviour it shipped with,
        # so recorded runs replay under their own feature decisions.
        for name in ('duplicate_predicate_gate', 'requirement_source_review',
                     'intent_scope_review', 'partial_formalization'):
            with self.subTest(feature=name):
                self.assertTrue(registry.feature_enabled('semantic-live', name))
                self.assertFalse(registry.feature_enabled('semantic-v3.16', name))
                self.assertFalse(registry.feature_enabled('semantic-v3.20', name))
        # live-6 (post-holdout defect-side): same rule for the advisory added
        # from the final_holdout_02 findings.
        self.assertTrue(registry.feature_enabled('semantic-live',
                                                 'example_pinning_review'))
        for version in registry.VERSIONS:
            self.assertFalse(registry.feature_enabled(version,
                                                      'example_pinning_review'))

    def test_frozen_versions_keep_their_legacy_sets(self):
        self.assertTrue(registry.feature_enabled('semantic-v3.5', 'strict_piv'))
        self.assertFalse(registry.feature_enabled('semantic-v3.9', 'numeric_guard'))
        self.assertTrue(registry.feature_enabled('semantic-v3.10', 'numeric_guard'))
        self.assertFalse(registry.feature_enabled('semantic-v3.16', 'protocol_identifier_exclusion'))
        self.assertTrue(registry.feature_enabled('semantic-v3.17', 'protocol_identifier_exclusion'))
        self.assertFalse(registry.feature_enabled('semantic-v3.18', 'protocol_identifier_exclusion'))

    def test_versions_stay_frozen_only(self):
        self.assertNotIn('semantic-live', registry.VERSIONS)
        self.assertIn('semantic-live', registry.SELECTABLE_VERSIONS)
        self.assertEqual(len(registry.VERSIONS), 16)
        self.assertEqual(registry.SELECTABLE_VERSIONS[-1], 'semantic-live')

    def test_unknown_feature_rejected(self):
        with self.assertRaises(ValueError):
            registry.feature_enabled('semantic-live', 'not_a_feature')
        with self.assertRaises(ValueError):
            registry.feature_enabled('semantic-v3.16', 'not_a_feature')
        with self.assertRaises(ValueError):
            registry.feature_enabled('semantic-v9.99', 'strict_piv')


if __name__ == '__main__':
    unittest.main()
