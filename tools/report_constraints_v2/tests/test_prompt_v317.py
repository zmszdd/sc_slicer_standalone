"""semantic-v3.17 typed-template and binding-guard regressions; no model calls."""

import copy
import json
import unittest

from prompts.versions import semantic_prompts_v317 as prompts
from lib.plan_synthesizer import (impact_qualifier_types, _pattern_expressions,
                              synthesize_id_formalization)
from cli.semantic_pipeline import formal_repair_fields, local_repair_payload
from tests.test_evidence_ids import id_inputs
from tests.test_prompt_v316 import fixed_plan


def expanded_plan():
    candidate = fixed_plan()
    candidate['schema_version'] = 'report-formal-plan/5'
    candidate['impact_context_terms'] = []
    candidate['pattern'] = {
        'kind': 'required_effect',
        'condition': {
            'kind': 'comparison', 'left': 'paid_fee', 'operator': 'gt',
            'right': {'symbol': 'required_fee'},
        },
        'effect': {'kind': 'truth', 'symbol': 'fee_revert', 'value': False},
    }
    return candidate


class PromptV317Tests(unittest.TestCase):
    def test_prompt_has_typed_templates_and_three_guards(self):
        text = prompts.formal_prompt('ids', 'core')
        self.assertIn('semantic-v3.17', text)
        self.assertIn('report-formal-plan/5', text)
        self.assertIn('authorization_guard', text)
        self.assertIn('temporal_order', text)
        self.assertIn('impact_context_terms', text)
        self.assertIn('MUST NOT reuse an identical predicate', text)
        self.assertIn('ERC-4337', text)

    def test_expanded_progress_template_compiles(self):
        elements, _ = id_inputs()
        formal = synthesize_id_formalization(expanded_plan(), elements)
        claim = formal['claims'][0]
        self.assertEqual(claim['properties']['safety']['expression']['op'], 'implies')
        self.assertEqual(claim['properties']['effects']['expression']['op'], 'and')

    def test_relation_class_has_one_expanded_template(self):
        elements, _ = id_inputs()
        candidate = expanded_plan()
        candidate['pattern']['kind'] = 'relation_obligation'
        candidate['pattern']['relation'] = candidate['pattern'].pop('effect')
        with self.assertRaisesRegex(ValueError, 'expanded relation template mismatch'):
            synthesize_id_formalization(candidate, elements)

    def test_each_p_symbol_must_be_grounded_by_its_own_source(self):
        elements, _ = id_inputs()
        candidate = expanded_plan()
        candidate['precondition_ids'].append('assume_nonnegative')
        candidate['precondition_terms'].append({
            'source_id': 'assume_nonnegative',
            'predicate': {'kind': 'comparison', 'left': 'paid_fee',
                          'operator': 'ge', 'right': {'const': 0}},
        })
        with self.assertRaisesRegex(ValueError, 'grounded by its own source'):
            synthesize_id_formalization(candidate, elements)

    def test_distinct_p_sources_cannot_reuse_one_predicate(self):
        elements, _ = id_inputs()
        candidate = expanded_plan()
        candidate['precondition_ids'].append('assume_nonnegative')
        for item in candidate['symbols'].values():
            if item['sort'] == 'int':
                item['source_ids'].append('assume_nonnegative')
        candidate['precondition_terms'].append({
            'source_id': 'assume_nonnegative',
            'predicate': copy.deepcopy(candidate['precondition_terms'][0]['predicate']),
        })
        with self.assertRaisesRegex(ValueError, 'reuse identical predicate'):
            synthesize_id_formalization(candidate, elements)

    def test_strong_impact_qualifier_is_required_and_conjoined(self):
        elements, _ = id_inputs()
        for row in elements['statements']:
            if row['id'] == 'impact_revert':
                row['text'] = 'After withdrawal, the invocation reverts.'
        candidate = expanded_plan()
        with self.assertRaisesRegex(ValueError, 'impact qualifier missing'):
            synthesize_id_formalization(candidate, elements)
        candidate['symbols']['after_withdrawal'] = {
            'sort': 'bool', 'unit': None, 'meaning': 'Withdrawal already happened',
            'checkpoint': 'impact_context', 'entity_ids': ['caller'],
            'source_ids': ['impact_revert'],
        }
        candidate['impact_context_terms'] = [{
            'source_id': 'impact_revert',
            'qualifier_types': ['temporal'],
            'predicate': {'kind': 'truth', 'symbol': 'after_withdrawal', 'value': True},
        }]
        formal = synthesize_id_formalization(candidate, elements)
        safety = formal['claims'][0]['properties']['safety']['expression']
        violation = formal['claims'][0]['properties']['effects']['expression']
        self.assertEqual(safety['op'], 'implies')
        self.assertEqual(safety['args'][0], {'var': 'after_withdrawal'})
        self.assertEqual(violation['op'], 'and')

    def test_real_failure_phrases_have_structured_qualifier_types(self):
        self.assertEqual(impact_qualifier_types(
            'After an identical swap, LP value declines.'), ['temporal'])
        self.assertEqual(impact_qualifier_types(
            'The guard passes even when deviation exceeds tolerance.'),
            ['state', 'threshold'])
        self.assertEqual(impact_qualifier_types(
            'It reverts even though only dust remains.'), ['state'])

    def test_missing_qualifier_error_names_the_required_type(self):
        elements, _ = id_inputs()
        for row in elements['statements']:
            if row['id'] == 'impact_revert':
                row['text'] = 'After withdrawal, the invocation reverts.'
        with self.assertRaisesRegex(ValueError, 'impact_revert.*temporal'):
            synthesize_id_formalization(expanded_plan(), elements)

    def test_unit_conflict_allows_bounded_reclassification_only(self):
        fields = formal_repair_fields(ValueError('type/unit mismatch'))
        self.assertIn('relation_class', fields)
        previous = expanded_plan()
        payload = json.loads(local_repair_payload(
            '{}', previous, ValueError('type/unit mismatch'), fields))
        self.assertEqual(payload['task'], 'replan_relation_locally')
        self.assertIn('Keep intent_id and impact_ids fixed',
                      payload['requirements'][2])

    def test_new_typed_patterns_produce_boolean_formulas(self):
        symbols = {
            'condition': {'sort': 'bool', 'unit': None},
            'effect': {'sort': 'bool', 'unit': None},
            'authorized': {'sort': 'bool', 'unit': None},
            'value': {'sort': 'int', 'unit': 'token'},
            'bound': {'sort': 'int', 'unit': 'token'},
            'earlier': {'sort': 'int', 'unit': 'seconds'},
            'later': {'sort': 'int', 'unit': 'seconds'},
        }
        truth = lambda name: {'kind': 'truth', 'symbol': name, 'value': True}
        quantity = lambda name: {'symbol': name}
        patterns = [
            {'kind': 'authorization_guard', 'effect': truth('effect'),
             'authorization': truth('authorized')},
            {'kind': 'bounded_relation', 'condition': truth('condition'),
             'value': quantity('value'), 'operator': 'le', 'bound': quantity('bound')},
            {'kind': 'correspondence', 'condition': truth('condition'),
             'observed_symbol': 'value', 'expected_symbol': 'bound'},
            {'kind': 'temporal_order', 'condition': truth('condition'),
             'earlier_symbol': 'earlier', 'later_symbol': 'later', 'strict': False},
            {'kind': 'required_effect', 'condition': truth('condition'),
             'effect': truth('effect')},
            {'kind': 'proportional_relation', 'condition': truth('condition'),
             'left': quantity('value'), 'operator': 'le', 'right': quantity('bound')},
        ]
        for pattern in patterns:
            safety, violation = _pattern_expressions(pattern, symbols)
            self.assertIsInstance(safety, dict)
            self.assertIsInstance(violation, dict)


if __name__ == '__main__':
    unittest.main()
