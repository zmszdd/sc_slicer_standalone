"""semantic-v3.16 fixed-template and local-repair regressions; no model calls."""

import copy
import json
from pathlib import Path
import tempfile
import unittest

from prompts.versions import semantic_prompts_v316 as prompts
from plan_synthesizer import synthesize_id_formalization
from semantic_pipeline import request_formalization, validate_local_repair
from tests.test_evidence_ids import id_inputs
from tests.test_plan_synthesizer import plan


def fixed_plan():
    candidate = plan()
    candidate['schema_version'] = 'report-formal-plan/4'
    candidate['relation_class'] = 'progress_or_liveness'
    candidate['derived_definitions'] = []
    candidate['pattern'] = {
        'kind': 'relation_obligation',
        'condition': {
            'kind': 'comparison', 'left': 'paid_fee', 'operator': 'gt',
            'right': {'symbol': 'required_fee'},
        },
        'relation': {'kind': 'truth', 'symbol': 'fee_revert', 'value': False},
    }
    return candidate


class PromptV316Tests(unittest.TestCase):
    def test_prompt_uses_v4_fixed_templates_and_derived_definitions(self):
        text = prompts.formal_prompt('ids', 'core')
        self.assertIn('semantic-v3.16', text)
        self.assertIn('report-formal-plan/4', text)
        self.assertIn('The program fixes the logical template', text)
        self.assertIn('every other class MUST use kind relation_obligation', text)
        self.assertIn('derived_definitions', text)
        self.assertIn('Do not select or encode the vulnerable return value', text)
        self.assertIn('Never duplicate a vulnerable result as a precondition',
                      prompts.ID_ELEMENT_PROMPT)

    def test_fixed_template_is_enforced(self):
        elements, _ = id_inputs()
        candidate = fixed_plan()
        candidate['pattern'] = {
            'kind': 'condition_forbids_effect',
            'condition': candidate['pattern']['condition'],
            'effect': {'kind': 'truth', 'symbol': 'fee_revert', 'value': True},
        }
        with self.assertRaisesRegex(ValueError, 'fixed relation template mismatch'):
            synthesize_id_formalization(candidate, elements)

    def test_v4_observable_needs_impact_while_intent_grounds_property(self):
        elements, _ = id_inputs()
        candidate = fixed_plan()
        formal = synthesize_id_formalization(candidate, elements)
        self.assertEqual(formal['schema_version'], 'report-formalization/2')

    def test_derived_symbol_requires_and_compiles_definition(self):
        elements, _ = id_inputs()
        candidate = fixed_plan()
        candidate['symbols']['expected_fee'] = {
            'sort': 'int', 'unit': 'native_wei',
            'meaning': 'Report-grounded expected fee', 'checkpoint': 'derived',
            'entity_ids': ['messenger', 'native_fee'],
            'source_ids': ['pre_overpay', 'intent_accept_buffer', 'impact_revert'],
        }
        candidate['pattern']['relation'] = {
            'kind': 'comparison', 'left': 'paid_fee', 'operator': 'eq',
            'right': {'symbol': 'expected_fee'},
        }
        with self.assertRaisesRegex(ValueError, 'referenced derived symbol lacks definition'):
            synthesize_id_formalization(candidate, elements)
        candidate['derived_definitions'] = [{
            'symbol': 'expected_fee',
            'expression': {'op': 'add', 'args': [
                {'symbol': 'required_fee'}, {'const': 0}]},
            'source_ids': ['pre_overpay', 'intent_accept_buffer'],
        }]
        formal = synthesize_id_formalization(candidate, elements)
        safety = formal['claims'][0]['properties']['safety']['expression']
        effects = formal['claims'][0]['properties']['effects']['expression']
        self.assertEqual(safety['op'], 'implies')
        self.assertEqual(safety['args'][0]['op'], 'eq')
        self.assertEqual(effects['op'], 'and')

    def test_same_unknown_multiplicative_factor_on_both_sides_is_rejected(self):
        elements, _ = id_inputs()
        candidate = fixed_plan()
        candidate['symbols']['duration'] = {
            'sort': 'int', 'unit': 'seconds', 'meaning': 'duration',
            'checkpoint': 'input', 'entity_ids': ['caller'],
            'source_ids': ['pre_overpay'],
        }
        candidate['symbols']['total_duration'] = {
            'sort': 'int', 'unit': 'seconds', 'meaning': 'total duration',
            'checkpoint': 'input', 'entity_ids': ['caller'],
            'source_ids': ['impact_revert'],
        }
        candidate['pattern']['relation'] = {
            'kind': 'relation',
            'left': {'op': 'mul', 'args': [
                {'symbol': 'paid_fee'}, {'symbol': 'duration'}]},
            'operator': 'le',
            'right': {'op': 'mul', 'args': [
                {'symbol': 'paid_fee'}, {'symbol': 'total_duration'}]},
        }
        with self.assertRaisesRegex(ValueError, 'cancellable observable'):
            synthesize_id_formalization(candidate, elements)

    def test_local_repair_freezes_unrelated_semantic_fields(self):
        previous = fixed_plan()
        repaired = copy.deepcopy(previous)
        repaired['pattern']['relation']['value'] = True
        self.assertEqual(validate_local_repair(previous, repaired, ('pattern',)),
                         ['pattern'])
        repaired['relation_class'] = 'state_correspondence'
        with self.assertRaisesRegex(ValueError, 'changed frozen fields'):
            validate_local_repair(previous, repaired, ('pattern',))

    def test_invalid_template_gets_a_field_scoped_retry(self):
        elements, _ = id_inputs()
        good = fixed_plan()
        bad = copy.deepcopy(good)
        bad['pattern'] = {
            'kind': 'condition_forbids_effect',
            'condition': good['pattern']['condition'],
            'effect': {'kind': 'truth', 'symbol': 'fee_revert', 'value': True},
        }
        calls = []

        def fake_extract(payload, folder, _model, _prompt):
            calls.append(json.loads(payload))
            candidate = bad if len(calls) == 1 else good
            (folder / 'model-claim.json').write_text(json.dumps(candidate))
            return copy.deepcopy(candidate)

        with tempfile.TemporaryDirectory() as work:
            root = Path(work)
            _, formal, _ = request_formalization(
                '{}', 'PROMPT', 'model', root, 1, True, elements,
                structured=True, extract_fn=fake_extract, local_repair=True)
            self.assertEqual(formal['schema_version'], 'report-formalization/2')
            self.assertEqual(calls[1]['task'], 'repair_previous_formal_plan_locally')
            self.assertEqual(calls[1]['mutable_top_level_fields'], ['pattern'])
            attempts = json.loads((root / 'formalization-attempts.json').read_text())
            self.assertEqual(attempts[1]['repair_mode'], 'field_scoped')
            self.assertEqual(attempts[1]['changed_top_level_fields'], ['pattern'])

    def test_null_repair_resubmission_gets_exactly_one_extra_reprompt(self):
        """final_holdout_02 (GTE_Perps): the retry resubmitted the plan
        byte-identically on the FINAL attempt, so the no-change prescription
        could never fire -- no next attempt existed.  A null response now
        grants exactly one reprompt, and only one.
        """
        elements, _ = id_inputs()
        good = fixed_plan()
        bad = copy.deepcopy(good)
        bad['pattern'] = {
            'kind': 'condition_forbids_effect',
            'condition': good['pattern']['condition'],
            'effect': {'kind': 'truth', 'symbol': 'fee_revert', 'value': True},
        }
        calls = []

        def fake_extract(payload, folder, _model, _prompt):
            calls.append(json.loads(payload))
            candidate = bad if len(calls) <= 2 else good
            (folder / 'model-claim.json').write_text(json.dumps(candidate))
            return copy.deepcopy(candidate)

        with tempfile.TemporaryDirectory() as work:
            root = Path(work)
            _, formal, _ = request_formalization(
                '{}', 'PROMPT', 'model', root, 1, True, elements,
                structured=True, extract_fn=fake_extract, local_repair=True)
            self.assertEqual(formal['schema_version'], 'report-formalization/2')
            self.assertEqual(len(calls), 3)
            attempts = json.loads((root / 'formalization-attempts.json').read_text())
            self.assertEqual(len(attempts), 3)
            self.assertTrue(attempts[1]['null_repair_reprompt'])
            self.assertEqual(attempts[1]['error'], 'local repair made no change')
            self.assertEqual(attempts[2]['repair_mode'], 'field_scoped')

    def test_second_null_repair_still_ends_the_run(self):
        """The null-reprompt grant is one-shot: a model that resubmits
        identically twice must not open an infinite repair loop."""
        elements, _ = id_inputs()
        bad = fixed_plan()
        condition = bad['pattern']['condition']
        bad['pattern'] = {
            'kind': 'condition_forbids_effect',
            'condition': condition,
            'effect': {'kind': 'truth', 'symbol': 'fee_revert', 'value': True},
        }
        calls = []

        def fake_extract(payload, folder, _model, _prompt):
            calls.append(json.loads(payload))
            (folder / 'model-claim.json').write_text(json.dumps(bad))
            return copy.deepcopy(bad)

        with tempfile.TemporaryDirectory() as work:
            root = Path(work)
            with self.assertRaisesRegex(ValueError,
                                        'local repair made no change'):
                request_formalization(
                    '{}', 'PROMPT', 'model', root, 1, True, elements,
                    structured=True, extract_fn=fake_extract, local_repair=True)
            self.assertEqual(len(calls), 3)


if __name__ == '__main__':
    unittest.main()
