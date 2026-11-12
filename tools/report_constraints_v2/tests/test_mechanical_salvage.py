import copy
import json
from lib.salvage import check_numeric_plan, example_pinning_review
from pathlib import Path
import tempfile
import unittest

from lib.salvage import (normalize_attack_step_roles, normalize_element_ids,
                                drop_unused_invalid_symbols,
                                merge_appended_relationship_trace,
                                salvage_formal_response,
                                strip_deepseek_json_suffix,
                                strip_duplicate_relationship_trace,
                                strip_trailing_dangling_brace)
from lib.plan_synthesizer import synthesize_id_formalization
from lib.solving import direct_relation_feasible
from lib.semantic_core import validate_elements
from lib.ingest import build_catalog, hydrate_elements
from cli.semantic_pipeline import request_formalization
from tests.test_evidence_ids import id_inputs
from tests.test_plan_synthesizer import plan as base_plan


class MechanicalSalvageTests(unittest.TestCase):
    PILOT = Path(__file__).resolve().parents[1] / 'evaluation/archive/deepseek_flash_pilot_01/runs'

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



    def test_numeric_gate_message_names_source_and_literals(self):
        """final_holdout_02 (Kinetiq): the rejection must point at the
        source and literals so the retry repairs THAT source."""
        elements = {'statements': [
            {'id': 'p_protocol_holds', 'kind': 'precondition',
             'text': 'The protocol holds 50 HYPE instead of 100.'}]}
        plan = {'precondition_terms': []}
        with self.assertRaises(ValueError) as caught:
            check_numeric_plan(plan, elements)
        message = str(caught.exception)
        self.assertTrue(message.startswith('numeric P source missing from plan'))
        self.assertIn('p_protocol_holds', message)
        self.assertIn('50', message)
        self.assertIn('100', message)

    def test_example_pinning_review_flags_impact_only_constants(self):
        """final_holdout_02 (Hybra): P pinned 10000/5000 straight from the
        impact's worked example -- advisory, never auto-rejecting."""
        elements = {'statements': [
            {'id': 'p_deposit', 'kind': 'precondition',
             'text': 'A user deposits into the vault.'},
            {'id': 'p_balance', 'kind': 'precondition',
             'text': 'The vault holds assets before the deposit.'},
            {'id': 'i_dilution', 'kind': 'impact',
             'text': 'With vault assets of 10000 and a deposit of 5000, the '
                     'depositor receives fewer shares than a fair mint.'}]}
        plan = {'precondition_terms': [
            {'source_id': 'p_balance',
             'predicate': {'kind': 'comparison', 'operator': 'eq',
                           'left': 'vault_assets_before',
                           'right': {'const': 10000}}},
            {'source_id': 'p_deposit',
             'predicate': {'kind': 'comparison', 'operator': 'eq',
                           'left': 'deposit', 'right': {'const': 5000}}},
        ]}
        review = example_pinning_review(plan, elements)
        self.assertTrue(review['advisory_only'])
        self.assertFalse(review['blocks_candidate_acceptance'])
        self.assertEqual(review['flagged_count'], 2)
        self.assertEqual({row['statement_id'] for row in review['flagged']},
                         {'p_balance', 'p_deposit'})

    def test_example_pinning_review_passes_own_source_constants(self):
        elements = {'statements': [
            {'id': 'p_threshold', 'kind': 'precondition',
             'text': 'The minimum stake is 100 tokens.'},
            {'id': 'i_loss', 'kind': 'impact',
             'text': 'Users lose 100 tokens.'}]}
        plan = {'precondition_terms': [
            {'source_id': 'p_threshold',
             'predicate': {'kind': 'comparison', 'operator': 'ge',
                           'left': 'stake', 'right': {'const': 100}}}]}
        review = example_pinning_review(plan, elements)
        self.assertEqual(review['flagged_count'], 0)

    def test_example_pinning_review_flags_restated_example_sources(self):
        """The real Hybra shape: the model restated the worked example AS
        precondition sources, so every constant is 'in its own source' -- the
        tell is several distinct P pins tracing to one impact example."""
        elements = {'statements': [
            {'id': 'p_vault', 'kind': 'precondition',
             'text': 'The vault holds 10000 tokens.'},
            {'id': 'p_deposit', 'kind': 'precondition',
             'text': 'The deposit is 5000 tokens.'},
            {'id': 'i_dilution', 'kind': 'impact',
             'text': 'Depositing 5000 into a vault holding 10000 yields only '
                     '~33.33% of the vault instead of 50%.'}]}
        plan = {'precondition_terms': [
            {'source_id': 'p_vault',
             'predicate': {'kind': 'comparison', 'operator': 'eq',
                           'left': 'vault_assets_before',
                           'right': {'const': 10000}}},
            {'source_id': 'p_deposit',
             'predicate': {'kind': 'comparison', 'operator': 'eq',
                           'left': 'deposit', 'right': {'const': 5000}}},
        ]}
        review = example_pinning_review(plan, elements)
        self.assertEqual(review['flagged_count'], 2)

    def test_example_pinning_review_allows_a_single_incident_constant(self):
        """Precision: one genuine incident equality whose number is also
        quoted in the impact is not a worked example."""
        elements = {'statements': [
            {'id': 'p_supply', 'kind': 'precondition',
             'text': 'The token supply is 1000000 tokens.'},
            {'id': 'i_drain', 'kind': 'impact',
             'text': 'The attacker drained value equal to 1000000 tokens.'}]}
        plan = {'precondition_terms': [
            {'source_id': 'p_supply',
             'predicate': {'kind': 'comparison', 'operator': 'eq',
                           'left': 'token_supply', 'right': {'const': 1000000}}}]}
        review = example_pinning_review(plan, elements)
        self.assertEqual(review['flagged_count'], 0)


class AppendedTraceSalvageTests(unittest.TestCase):
    PILOT = Path(__file__).resolve().parents[1] / 'evaluation/archive/deepseek_flash_pilot_01/runs'
    MALFORMED = ('{"schema_version":"report-formal-plan/8","relation_class":'
                 '"sequence_preservation","precondition_ids":["p_one"]}'
                 ',"relationship_trace":{"status":"explicit","links":[],'
                 '"gap":""}}')

    def test_appended_trace_key_is_merged_into_the_plan_object(self):
        salvaged = merge_appended_relationship_trace(self.MALFORMED)
        self.assertIsNotNone(salvaged)
        claim, record = salvaged
        self.assertEqual(claim['schema_version'], 'report-formal-plan/8')
        self.assertEqual(claim['precondition_ids'], ['p_one'])
        self.assertEqual(claim['relationship_trace'],
                         {'status': 'explicit', 'links': [], 'gap': ''})
        self.assertEqual(record['transform'],
                         'merge_appended_relationship_trace')

    def test_balanced_response_is_left_alone(self):
        balanced = ('{"schema_version":"report-formal-plan/8",'
                    '"relationship_trace":{"status":"insufficient",'
                    '"links":[],"gap":""}}')
        self.assertIsNone(merge_appended_relationship_trace(balanced))

    def test_unrelated_extra_data_is_not_salvaged(self):
        unrelated = '{"schema_version":"report-formal-plan/8"} trailing notes'
        self.assertIsNone(merge_appended_relationship_trace(unrelated))

    def test_deepseek_json_suffix_is_stripped(self):
        text = ('{"schema_version":"report-formal-plan/8","precondition_ids":["p_one"]}'
                ',"type":"json_object"}')
        salvaged = strip_deepseek_json_suffix(text)
        self.assertIsNotNone(salvaged)
        claim, record = salvaged
        self.assertEqual(claim['schema_version'], 'report-formal-plan/8')
        self.assertEqual(claim['precondition_ids'], ['p_one'])
        self.assertEqual(record['transform'], 'strip_deepseek_json_suffix')

    def test_deepseek_json_suffix_rejects_unrelated_tail(self):
        text = ('{"schema_version":"report-formal-plan/8"},"type":"json_object"} extra')
        self.assertIsNone(strip_deepseek_json_suffix(text))

    def test_trailing_dangling_brace_is_stripped(self):
        text = ('{"schema_version":"report-formal-plan/8","precondition_ids":["p_one"]}}')
        salvaged = strip_trailing_dangling_brace(text)
        self.assertIsNotNone(salvaged)
        claim, record = salvaged
        self.assertEqual(claim['schema_version'], 'report-formal-plan/8')
        self.assertEqual(record['transform'], 'strip_trailing_dangling_brace')

    def test_trailing_dangling_brace_rejects_unrelated_tail(self):
        text = ('{"schema_version":"report-formal-plan/8"}} extra')
        self.assertIsNone(strip_trailing_dangling_brace(text))

    def test_duplicate_relationship_trace_is_stripped(self):
        text = ('{"formal_plan":{"schema_version":"report-formal-plan/8"},'
                '"relationship_trace":{"status":"explicit","links":[],"gap":""}}'
                ',"relationship_trace":{"status":"explicit","links":[],"gap":""}}')
        salvaged = strip_duplicate_relationship_trace(text)
        self.assertIsNotNone(salvaged)
        claim, record = salvaged
        self.assertIn('formal_plan', claim)
        self.assertIn('relationship_trace', claim)
        self.assertEqual(record['transform'], 'strip_duplicate_relationship_trace')

    def test_duplicate_relationship_trace_requires_existing_trace(self):
        text = ('{"formal_plan":{"schema_version":"report-formal-plan/8"}}'
                ',"relationship_trace":{"status":"explicit","links":[],"gap":""}}')
        self.assertIsNone(strip_duplicate_relationship_trace(text))

    def test_salvage_formal_response_prefers_trace_then_suffix(self):
        trace_text = ('{"schema_version":"report-formal-plan/8"}'
                      ',"relationship_trace":{"status":"explicit","links":[],"gap":""}}')
        claim, record = salvage_formal_response(trace_text)
        self.assertEqual(record['transform'], 'merge_appended_relationship_trace')
        suffix_text = ('{"schema_version":"report-formal-plan/8"},"type":"json_object"}')
        claim, record = salvage_formal_response(suffix_text)
        self.assertEqual(record['transform'], 'strip_deepseek_json_suffix')

    def test_non_dict_trace_value_is_not_salvaged(self):
        malformed = ('{"schema_version":"report-formal-plan/8"}'
                     ',"relationship_trace":"explicit"}')
        self.assertIsNone(merge_appended_relationship_trace(malformed))

    def test_request_formalization_salvages_the_appended_trace_key(self):
        """live-24 paired attribution: four no-rule pairs died on exactly
        this response shape; the wiring must recover the pair without a
        retry and record the transform for offline replay."""
        source = self.PILOT / 'kinetiq'
        elements = json.loads((source / 'elements-ids.json').read_text())
        plan = json.loads(
            (source / 'neural-formalization/model-claim.json').read_text())
        trace = {'status': 'explicit',
                 'links': [{'from_source_ids': ['p_one'],
                            'context_statement_id': 'act_one',
                            'evidence_ids': ['e_1'],
                            'reported_relation': 'the action skips the check'}],
                 'gap': ''}
        raw = json.dumps(plan) + ',"relationship_trace":' + \
            json.dumps(trace) + '}'

        def fake_extract(_payload, folder, _model, _prompt):
            (folder / 'model-response.txt').write_text(raw)
            raise json.JSONDecodeError('Extra data: line 1 column 68', '', 68)

        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp)
            salvaged_plan, _, _ = request_formalization(
                '{}', 'prompt', 'test-model', output, 1, True, elements,
                extract_fn=fake_extract, attempts=[],
                mechanical_salvage=True,
                relationship_trace_enabled=True)
            # mechanical_salvage drops the plan's unused zero_address symbol
            # exactly as in the opt-in salvage test; nothing else may change.
            expected = copy.deepcopy(plan)
            del expected['symbols']['zero_address']
            self.assertEqual(salvaged_plan, expected)
            self.assertNotIn('relationship_trace', salvaged_plan)
            self.assertEqual(
                json.loads((output / 'relationship-trace.json').read_text()),
                trace)
            saved_claim = json.loads(
                (output / 'neural-formalization/model-claim.json').read_text())
            self.assertIn('relationship_trace', saved_claim)
            self.assertEqual(saved_claim['relationship_trace'], trace)
            normalization = json.loads(
                (output / 'neural-formalization/response-normalization.json')
                .read_text())
            self.assertEqual(normalization['transform'],
                             'merge_appended_relationship_trace')
            attempts = json.loads(
                (output / 'formalization-attempts.json').read_text())
            self.assertEqual([x['outcome'] for x in attempts],
                             ['accepted_for_validation'])
            self.assertEqual(attempts[0]['response_normalization'],
                             'merge_appended_relationship_trace')
            # The raw response itself is never rewritten.
            self.assertEqual(
                (output / 'neural-formalization/model-response.txt')
                .read_text(), raw)

    def test_request_formalization_unrelated_json_error_still_raises(self):
        source = self.PILOT / 'kinetiq'
        elements = json.loads((source / 'elements-ids.json').read_text())

        def fake_extract(_payload, folder, _model, _prompt):
            (folder / 'model-response.txt').write_text('{"a":1} extra')
            raise json.JSONDecodeError('Extra data', '', 8)

        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(json.JSONDecodeError):
                request_formalization(
                    '{}', 'prompt', 'test-model', Path(temp), 0, True,
                    elements, extract_fn=fake_extract)


class FormalPlanEnvelopeTests(unittest.TestCase):
    PILOT = Path(__file__).resolve().parents[1] / 'evaluation/archive/deepseek_flash_pilot_01/runs'

    def test_request_formalization_unwraps_formal_plan_envelope(self):
        """semantic-live-24 asks for {formal_plan, relationship_trace}; the
        generator must deterministically unwrap the envelope while keeping the
        raw response untouched."""
        source = self.PILOT / 'kinetiq'
        elements = json.loads((source / 'elements-ids.json').read_text())
        plan = json.loads(
            (source / 'neural-formalization/model-claim.json').read_text())
        trace = {'status': 'explicit',
                 'links': [{'from_source_ids': ['p_one'],
                            'context_statement_id': 'act_one',
                            'evidence_ids': ['e_1'],
                            'reported_relation': 'the action skips the check'}],
                 'gap': ''}
        envelope = {'formal_plan': plan, 'relationship_trace': trace}
        raw = json.dumps(envelope)

        def fake_extract(_payload, folder, _model, _prompt):
            (folder / 'model-response.txt').write_text(raw)
            (folder / 'model-claim.json').write_text(raw)
            return json.loads(raw)

        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp)
            expected, _ = drop_unused_invalid_symbols(copy.deepcopy(plan))
            unwrapped, _, _ = request_formalization(
                '{}', 'prompt', 'test-model', output, 0, True, elements,
                extract_fn=fake_extract, attempts=[],
                mechanical_salvage=True,
                relationship_trace_enabled=True)
            self.assertEqual(unwrapped, expected)
            self.assertNotIn('relationship_trace', unwrapped)
            saved_claim = json.loads(
                (output / 'neural-formalization/model-claim.json').read_text())
            self.assertEqual(saved_claim, envelope)
            self.assertEqual(
                json.loads((output / 'relationship-trace.json').read_text()),
                trace)
            # The raw response itself is never rewritten.
            self.assertEqual(
                (output / 'neural-formalization/model-response.txt')
                .read_text(), raw)


class DirectRelationGateTests(unittest.TestCase):
    def _authorization_guard_plan(self):
        elements = {
            'scope': {'flow': 'request claim', 'environment': 'vault'},
            'entities': [{'id': 'e1', 'name': 'Vault'}],
            'statements': [
                {'id': 'p_submit', 'kind': 'precondition',
                 'text': 'operator submits request', 'evidence_ids': ['ev1'],
                 'entity_ids': ['e1'], 'modality': 'potential'},
                {'id': 'p_zero', 'kind': 'precondition',
                 'text': 'controller is zero', 'evidence_ids': ['ev2'],
                 'entity_ids': ['e1'], 'modality': 'potential'},
                {'id': 'i_auth', 'kind': 'security_intent',
                 'text': 'claim requires authenticated caller',
                 'evidence_ids': ['ev3'], 'entity_ids': ['e1'],
                 'modality': 'asserted'},
                {'id': 'impact', 'kind': 'impact',
                 'text': 'funds permanently locked', 'evidence_ids': ['ev4'],
                 'entity_ids': ['e1'], 'modality': 'asserted'},
            ],
        }
        plan = {
            'schema_version': 'report-formal-plan/8',
            'relation_class': 'access_control',
            'precondition_ids': ['p_submit', 'p_zero'],
            'intent_id': 'i_auth', 'impact_ids': ['impact'],
            'symbols': {
                'request_submitted': {'sort': 'bool', 'unit': None,
                                      'meaning': 'submitted',
                                      'checkpoint': 'before',
                                      'entity_ids': ['e1'],
                                      'source_ids': ['p_submit']},
                'controller_zero': {'sort': 'bool', 'unit': None,
                                    'meaning': 'zero', 'checkpoint': 'before',
                                    'entity_ids': ['e1'],
                                    'source_ids': ['p_zero']},
                'effect': {'sort': 'bool', 'unit': None,
                           'meaning': 'claim performable',
                           'checkpoint': 'after', 'entity_ids': ['e1'],
                           'source_ids': ['impact', 'i_auth']},
                'auth': {'sort': 'bool', 'unit': None,
                         'meaning': 'auth caller exists',
                         'checkpoint': 'after', 'entity_ids': ['e1'],
                         'source_ids': ['i_auth']},
                'outcome': {'sort': 'bool', 'unit': None,
                            'meaning': 'funds locked', 'checkpoint': 'after',
                            'entity_ids': ['e1'], 'source_ids': ['impact']},
            },
            'precondition_terms': [
                {'source_id': 'p_submit',
                 'predicate': {'kind': 'truth', 'symbol': 'request_submitted',
                               'value': True}},
                {'source_id': 'p_zero',
                 'predicate': {'kind': 'truth', 'symbol': 'controller_zero',
                               'value': True}},
            ],
            'impact_outcome': {'source_id': 'impact',
                               'predicate': {'kind': 'truth',
                                             'symbol': 'outcome', 'value': True}},
            'impact_context_terms': [],
            'derived_definitions': [],
            'pattern': {'kind': 'authorization_guard',
                        'effect': {'kind': 'truth', 'symbol': 'effect',
                                   'value': True},
                        'authorization': {'kind': 'truth', 'symbol': 'auth',
                                          'value': True}},
            'assumptions': [], 'unresolved': [], 'limitations': [],
        }
        return elements, plan

    def test_direct_witness_effects_makes_authorization_guard_feasible(self):
        elements, plan = self._authorization_guard_plan()
        for enabled, expected in ((False, False), (True, True)):
            formal = synthesize_id_formalization(
                plan, elements, claim_id='c', fidelity_only=True,
                direct_witness_effects=enabled)
            claim = dict(formal['claims'][0], symbols=formal['symbols'])
            self.assertEqual(direct_relation_feasible(claim), expected)

    def test_direct_witness_effects_collapse_double_negation(self):
        elements, _ = id_inputs()
        plan = base_plan()
        plan['schema_version'] = 'report-formal-plan/8'
        plan['relation_class'] = 'progress_or_liveness'
        plan['derived_definitions'] = []
        plan['impact_context_terms'] = []
        plan['pattern'] = {
            'kind': 'required_effect',
            'condition': {'kind': 'comparison', 'left': 'paid_fee',
                          'operator': 'gt', 'right': {'symbol': 'required_fee'}},
            'effect': {'kind': 'truth', 'symbol': 'fee_revert', 'value': False},
        }
        plan['impact_outcome'] = {
            'source_id': 'impact_revert',
            'predicate': {'kind': 'truth', 'symbol': 'fee_revert', 'value': True},
        }
        formal = synthesize_id_formalization(
            plan, elements, claim_id='c', direct_witness_effects=True)
        effects = formal['claims'][0]['properties']['effects']['expression']

        def has_double_not(node):
            if not isinstance(node, dict):
                return False
            if node.get('op') == 'not':
                args = node.get('args')
                if (isinstance(args, list) and len(args) == 1 and
                        isinstance(args[0], dict) and args[0].get('op') == 'not'):
                    return True
            return any(has_double_not(v) for v in node.values())

        self.assertFalse(has_double_not(effects))

    def test_direct_contradiction_is_feasible(self):
        claim = {'symbols': {'v': {'sort': 'bool'}},
                 'properties': {
                     'safety': {'expression': {'op': 'not',
                                               'args': [{'var': 'v'}]}},
                     'effects': {'expression': {'var': 'v'}},
                 }}
        self.assertTrue(direct_relation_feasible(claim))

    def test_v_guarded_safety_is_infeasible(self):
        claim = {'symbols': {'v': {'sort': 'bool'}, 'q': {'sort': 'bool'}},
                 'properties': {
                     'preconditions': {'expression': {'var': 'v'}},
                     'safety': {'expression': {
                         'op': 'implies',
                         'args': [{'op': 'not', 'args': [{'var': 'v'}]},
                                  {'var': 'q'}]}},
                     'effects': {'expression': {'var': 'v'}},
                 }}
        self.assertFalse(direct_relation_feasible(claim))


if __name__ == '__main__':
    unittest.main()
