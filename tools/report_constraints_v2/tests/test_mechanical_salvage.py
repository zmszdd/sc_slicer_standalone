import copy
import json
from fidelity import check_numeric_plan
from pathlib import Path
import tempfile
import unittest

from mechanical_salvage import (normalize_attack_step_roles, normalize_element_ids,
                                drop_unused_invalid_symbols)
from plan_synthesizer import synthesize_id_formalization
from semantic_core import validate_elements
from evidence_catalog import build_catalog, hydrate_elements
from semantic_pipeline import request_formalization


class MechanicalSalvageTests(unittest.TestCase):
    PILOT = Path(__file__).resolve().parents[1] / 'evaluation/deepseek_flash_pilot_01/runs'

    def test_lowercase_id_and_references_only(self):
        raw = {'schema_version': 'report-elements/2',
               'entities': [{'id': 'Pool_ID', 'name': 'Pool'}],
               'statements': [{'id': 'kLast_initial', 'entity_ids': ['Pool_ID'],
                               'text': 'Original text', 'evidence_ids': ['e_1']}],
               'attack_steps': ['kLast_initial']}
        original = copy.deepcopy(raw)
        result, repairs = normalize_element_ids(raw)
        self.assertEqual(raw, original)
        self.assertEqual(result['entities'][0]['id'], 'pool_id')
        self.assertEqual(result['statements'][0]['id'], 'klast_initial')
        self.assertEqual(result['statements'][0]['entity_ids'], ['pool_id'])
        self.assertEqual(result['attack_steps'], ['klast_initial'])
        self.assertEqual(result['statements'][0]['text'], 'Original text')
        self.assertEqual(result['statements'][0]['evidence_ids'], ['e_1'])
        self.assertEqual(len(repairs), 2)

    def test_case_collision_is_not_salvaged(self):
        raw = {'schema_version': 'report-elements/2', 'entities': [],
               'statements': [{'id': 'aB'}, {'id': 'ab'}], 'attack_steps': []}
        result, repairs = normalize_element_ids(raw)
        self.assertEqual(result, raw)
        self.assertEqual(repairs, [])

    def test_non_action_attack_step_reference_is_removed_without_semantic_edit(self):
        raw = {'schema_version': 'report-elements/2',
               'statements': [
                   {'id': 'send_order', 'kind': 'action', 'text': 'send order'},
                   {'id': 'loss', 'kind': 'impact', 'text': 'fund loss'},
                   {'id': 'cause', 'kind': 'root_cause', 'text': 'missing check'},
               ],
               'attack_steps': ['send_order', 'cause', 'loss']}
        original = copy.deepcopy(raw)
        result, changes = normalize_attack_step_roles(raw)
        self.assertEqual(raw, original)
        self.assertEqual(result['attack_steps'], ['send_order'])
        self.assertEqual(result['statements'], raw['statements'])
        self.assertEqual([item['statement_id'] for item in changes], ['cause', 'loss'])

    def test_unknown_attack_step_reference_remains_for_validator(self):
        raw = {'schema_version': 'report-elements/2',
               'statements': [{'id': 'send_order', 'kind': 'action'}],
               'attack_steps': ['unknown_step']}
        result, changes = normalize_attack_step_roles(raw)
        self.assertEqual(result['attack_steps'], ['unknown_step'])
        self.assertEqual(changes, [])

    def test_mixed_case_ids_can_be_lowercased_before_role_normalization(self):
        raw = {'schema_version': 'report-elements/2',
               'entities': [{'id': 'gHYBR_Shares', 'name': 'shares'}],
               'statements': [{'id': 'a_calculateShares', 'kind': 'action',
                               'entity_ids': ['gHYBR_Shares']}],
               'attack_steps': ['a_calculateShares']}
        lowered, id_changes = normalize_element_ids(raw)
        result, role_changes = normalize_attack_step_roles(lowered)
        self.assertEqual(result['entities'][0]['id'], 'ghybr_shares')
        self.assertEqual(result['statements'][0]['id'], 'a_calculateshares')
        self.assertEqual(result['attack_steps'], ['a_calculateshares'])
        self.assertEqual(len(id_changes), 2)
        self.assertEqual(role_changes, [])

    def test_unused_invalid_symbol_is_dropped(self):
        raw = {'symbols': {'zero_address': {'entity_ids': []},
                           'amount': {'entity_ids': ['asset']}},
               'precondition_terms': [{'predicate': {'kind': 'comparison', 'left': 'amount'}}],
               'pattern': {'condition': {'kind': 'truth', 'symbol': 'amount'}}}
        original = copy.deepcopy(raw)
        result, repairs = drop_unused_invalid_symbols(raw)
        self.assertEqual(raw, original)
        self.assertEqual(list(result['symbols']), ['amount'])
        self.assertEqual(len(repairs), 1)

    def test_referenced_invalid_symbol_is_never_dropped(self):
        raw = {'symbols': {'zero_address': {'entity_ids': []}},
               'precondition_terms': [],
               'pattern': {'effect': {'right': {'symbol': 'zero_address'}}}}
        result, repairs = drop_unused_invalid_symbols(raw)
        self.assertEqual(result, raw)
        self.assertEqual(repairs, [])

    def test_kinetiq_saved_plan_reaches_formalization_without_weaker_guard(self):
        source = self.PILOT / 'kinetiq'
        elements = json.loads((source / 'elements-ids.json').read_text())
        raw = json.loads((source / 'neural-formalization/model-claim.json').read_text())
        plan, repairs = drop_unused_invalid_symbols(raw)
        self.assertEqual([row['symbol'] for row in repairs], ['zero_address'])
        self.assertEqual(synthesize_id_formalization(plan, elements)['schema_version'],
                         'report-formalization/2')
        check_numeric_plan(plan, elements)

    def test_virtuals_saved_elements_validate_after_case_only_repair(self):
        source = self.PILOT / 'virtuals'
        raw = json.loads((source / 'neural-elements/model-claim.json').read_text())
        elements, repairs = normalize_element_ids(raw)
        self.assertEqual(len(repairs), 1)
        self.assertEqual(repairs[0]['from'], 'kLast_initial')
        text = (source / 'extraction-input.txt').read_text()
        hydrated = hydrate_elements(elements, build_catalog(text), text)
        validate_elements(hydrated, text)

    def test_olas_numeric_meaning_is_still_blocked(self):
        source = self.PILOT / 'olas'
        elements = json.loads((source / 'elements-ids.json').read_text())
        raw = json.loads((source / 'neural-formalization/model-claim.json').read_text())
        plan, repairs = drop_unused_invalid_symbols(raw)
        self.assertEqual(repairs, [])
        with self.assertRaisesRegex(ValueError, 'numeric P source missing from plan'):
            check_numeric_plan(plan, elements)

    def test_request_formalization_opt_in_salvages_only_unused_symbol(self):
        source = self.PILOT / 'kinetiq'
        elements = json.loads((source / 'elements-ids.json').read_text())
        raw = json.loads((source / 'neural-formalization/model-claim.json').read_text())
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp)
            plan, formal, _ = request_formalization(
                '{}', 'prompt', 'test-model', output, 0, True, elements,
                extract_fn=lambda *_args: copy.deepcopy(raw),
                numeric_guard=True, mechanical_salvage=True)
            self.assertNotIn('zero_address', plan['symbols'])
            self.assertIn('zero_address', raw['symbols'])
            self.assertEqual(formal['schema_version'], 'report-formalization/2')
            audit = json.loads((output / 'neural-formalization/mechanical-salvage.json').read_text())
            self.assertEqual(audit[0]['symbol'], 'zero_address')


if __name__ == '__main__':
    unittest.main()
