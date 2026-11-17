"""Deterministic v3.5 plan synthesis controls; no external calls."""
import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from lib.ingest import build_catalog, hydrate_elements, hydrate_formalization
from lib.plan_synthesizer import (_pattern_expressions, structured_unresolved_review,
                              synthesize_id_formalization,
                              impact_qualifier_types, observability_contract,
                              symbol_table_review)
from lib import report_only as report_math
from lib import semantic_core
from cli import semantic_pipeline as pipeline
from prompts.versions import semantic_prompts_v35 as prompts
from prompts.versions import semantic_prompts_v36 as prompts_v36
from prompts.versions import semantic_prompts_v37 as prompts_v37
from tests.test_evidence_ids import id_inputs, TEXT
from cli import batch_verify as verify_semantic


def plan():
    return {
        'schema_version': 'report-formal-plan/1',
        'precondition_ids': ['pre_overpay'],
        'intent_id': 'intent_accept_buffer',
        'impact_ids': ['impact_revert'],
        'symbols': {
            'paid_fee': {'sort': 'int', 'unit': 'native_wei',
                         'meaning': 'Native fee supplied by the caller', 'checkpoint': 'call_entry',
                         'entity_ids': ['caller', 'native_fee'], 'source_ids': ['pre_overpay']},
            'required_fee': {'sort': 'int', 'unit': 'native_wei',
                             'meaning': 'Execution-time required native fee', 'checkpoint': 'call_entry',
                             'entity_ids': ['messenger', 'native_fee'], 'source_ids': ['pre_overpay']},
            'fee_revert': {'sort': 'bool', 'unit': None,
                           'meaning': 'Invocation reverted for the fee mismatch',
                           'checkpoint': 'call_exit', 'entity_ids': ['caller', 'messenger'],
                           'source_ids': ['impact_revert']},
        },
        'precondition_terms': [{
            'source_id': 'pre_overpay',
            'predicate': {'kind': 'comparison', 'left': 'paid_fee', 'operator': 'gt',
                          'right': {'symbol': 'required_fee'}},
        }],
        'pattern': {
            'kind': 'condition_forbids_effect',
            'condition': {'kind': 'comparison', 'left': 'paid_fee', 'operator': 'gt',
                          'right': {'symbol': 'required_fee'}},
            'effect': {'kind': 'truth', 'symbol': 'fee_revert', 'value': True},
        },
        'assumptions': [], 'unresolved': [], 'limitations': [],
    }


class PlanSynthesisTests(unittest.TestCase):
    def test_observability_fields_are_accepted_but_kept_out_of_formal_symbols(self):
        elements, _ = id_inputs()
        from tests.test_prompt_v317 import expanded_plan
        candidate = expanded_plan()
        candidate['symbols']['paid_fee'].update({
            'observable_kind': 'getter', 'scope': 'business',
            'receiver': None, 'contract_type': None, 'binding_risk': 'low'})
        formal = synthesize_id_formalization(candidate, elements)
        self.assertNotIn('observable_kind', formal['symbols']['paid_fee'])
        contract = observability_contract(candidate)
        self.assertTrue(contract['contract_present'])
        self.assertEqual(contract['symbols']['paid_fee']['observable_kind'],
                         'getter')
        self.assertNotIn('paid_fee', contract['high_risk'])

    def test_old_plan_has_no_observability_contract(self):
        from tests.test_prompt_v317 import expanded_plan
        contract = observability_contract(expanded_plan())
        self.assertFalse(contract['contract_present'])
        self.assertIsNone(contract['symbols']['paid_fee']['binding_risk'])

    def test_cross_contract_symbol_requires_receiver(self):
        elements, _ = id_inputs()
        from tests.test_prompt_v317 import expanded_plan
        candidate = expanded_plan()
        candidate['symbols']['paid_fee'].update({
            'observable_kind': 'getter', 'scope': 'cross_contract'})
        with self.assertRaisesRegex(ValueError,
                                    'cross-contract plan symbol lacks receiver'):
            synthesize_id_formalization(candidate, elements)

    def test_missing_observability_is_flagged_and_high_risk(self):
        from tests.test_prompt_v317 import expanded_plan
        candidate = expanded_plan()
        candidate['symbols']['fee_revert'].update({
            'observable_kind': 'getter', 'scope': 'business'})
        contract = observability_contract(candidate)
        self.assertIn('paid_fee', contract['high_risk'])
        review = symbol_table_review(candidate)
        flags = {row['flag'] for row in review['flagged']
                 if row['symbol'] == 'paid_fee'}
        self.assertIn('missing_observability', flags)

    def test_live8_compiles_report_impact_as_independent_v(self):
        elements, _ = id_inputs()
        from tests.test_prompt_v317 import expanded_plan
        candidate = expanded_plan()
        candidate['schema_version'] = 'report-formal-plan/8'
        candidate['derived_definitions'] = []
        candidate['impact_context_terms'] = []
        candidate['impact_outcome'] = {
            'source_id': 'impact_revert',
            'predicate': {'kind': 'truth', 'symbol': 'fee_revert', 'value': True},
        }
        formal = synthesize_id_formalization(candidate, elements)
        claim = formal['claims'][0]
        self.assertEqual(claim['properties']['effects']['expression'],
                         {'var': 'fee_revert'})
        self.assertNotEqual(claim['properties']['effects']['expression'],
                            claim['properties']['safety']['expression'])

    def test_impact_qualifier_detector_covers_scope_direction_and_duration(self):
        text = ('Every newly created vault is permanently griefed if the attacker '
                're-deposits before expiry; users lose more than 50% each day, '
                'with costs between $10 and $20.')
        self.assertEqual(
            set(impact_qualifier_types(text)),
            {'scope', 'duration_or_repetition', 'trigger', 'temporal',
             'comparison_direction', 'threshold', 'rate_or_cost', 'range'})

    def test_all_logical_patterns_produce_boolean_i_and_v(self):
        symbols = {
            'condition': {'sort': 'bool', 'unit': None},
            'effect': {'sort': 'bool', 'unit': None},
            'authorized': {'sort': 'bool', 'unit': None},
            'before': {'sort': 'int', 'unit': 'token'},
            'after': {'sort': 'int', 'unit': 'token'},
        }
        truth = lambda name: {'kind': 'truth', 'symbol': name, 'value': True}
        patterns = [
            {'kind': 'condition_forbids_effect', 'condition': truth('condition'),
             'effect': truth('effect')},
            {'kind': 'condition_requires_effect', 'condition': truth('condition'),
             'effect': truth('effect')},
            {'kind': 'effect_requires_any_authorization', 'effect': truth('effect'),
             'authorization_terms': [truth('authorized')]},
            {'kind': 'state_preservation', 'trigger': truth('condition'),
             'before_symbol': 'before', 'after_symbol': 'after'},
        ]
        for pattern in patterns:
            safety, violation = _pattern_expressions(pattern, symbols)
            self.assertEqual(report_math.expr_type(safety, symbols), ('bool', None))
            self.assertEqual(report_math.expr_type(violation, symbols), ('bool', None))

    def test_program_generates_ast_sources_and_exact_coverage(self):
        elements_raw, _ = id_inputs()
        formal_raw = synthesize_id_formalization(plan(), elements_raw)
        claim = formal_raw['claims'][0]
        self.assertEqual(claim['impact_ids'], ['impact_revert'])
        self.assertEqual([x['statement_id'] for x in claim['effect_coverage']],
                         ['impact_revert'])
        self.assertEqual(claim['properties']['safety']['expression']['op'], 'implies')
        self.assertEqual(claim['properties']['effects']['expression']['op'], 'and')
        self.assertIn('Deferred report impact: impact_ux', formal_raw['limitations'])
        catalog = build_catalog(TEXT)
        elements = hydrate_elements(elements_raw, catalog, TEXT)
        formal = hydrate_formalization(formal_raw, catalog, TEXT)
        result = semantic_core.compile_bundle(elements, formal, TEXT, strict_piv=True)
        relation = result['claims'][0]['semantic_relationship']['queries']
        self.assertEqual(relation['P_and_V_and_I'], 'unsat')
        self.assertEqual(relation['P_and_V_and_not_I'], 'sat')

    def test_trigger_condition_relocates_to_precondition(self):
        elements, _ = id_inputs()
        candidate = plan()
        candidate['symbols']['swap_triggered'] = {
            'sort': 'bool', 'unit': None,
            'meaning': 'swap finalization is triggered',
            'checkpoint': 'swap_finalization',
            'entity_ids': ['caller'],
            'source_ids': ['intent_accept_buffer'],
        }
        candidate['pattern'] = {
            'kind': 'required_effect',
            'condition': {'kind': 'truth', 'symbol': 'swap_triggered', 'value': True},
            'effect': {'kind': 'truth', 'symbol': 'fee_revert', 'value': True},
        }
        formal = synthesize_id_formalization(candidate, elements)
        claim = formal['claims'][0]
        self.assertEqual(claim['properties']['safety']['expression'],
                         {'var': 'fee_revert'})
        self.assertIn('swap_triggered',
                      json.dumps(claim['properties']['preconditions']['expression']))
        self.assertEqual(claim['properties']['effects']['expression']['op'], 'and')

    def test_trigger_relocated_without_precondition_carries_source(self):
        elements, _ = id_inputs()
        from tests.test_prompt_v317 import expanded_plan
        candidate = expanded_plan()
        candidate['schema_version'] = 'report-formal-plan/8'
        candidate['precondition_ids'] = []
        candidate['precondition_terms'] = []
        candidate['impact_context_terms'] = []
        candidate['derived_definitions'] = []
        candidate['impact_outcome'] = {
            'source_id': 'impact_revert',
            'predicate': {'kind': 'truth', 'symbol': 'fee_revert', 'value': True},
        }
        candidate['symbols']['swap_triggered'] = {
            'sort': 'bool', 'unit': None,
            'meaning': 'swap finalization is triggered',
            'checkpoint': 'swap_finalization',
            'entity_ids': ['caller'],
            'source_ids': ['intent_accept_buffer'],
        }
        candidate['pattern'] = {
            'kind': 'required_effect',
            'condition': {'kind': 'truth', 'symbol': 'swap_triggered', 'value': True},
            'effect': {'kind': 'truth', 'symbol': 'fee_revert', 'value': True},
        }
        formal = synthesize_id_formalization(candidate, elements)
        p_prop = formal['claims'][0]['properties']['preconditions']
        self.assertEqual(p_prop['source_ids'], ['intent_accept_buffer'])
        self.assertEqual(p_prop['expression'],
                         {'op': 'and', 'args': [
                             {'const': True}, {'var': 'swap_triggered'}]})
        catalog = build_catalog(TEXT)
        hydrated = hydrate_formalization(formal, catalog, TEXT)
        semantic_core.validate_formalization(
            hydrated, hydrate_elements(elements, catalog, TEXT), TEXT)

    def test_no_explicit_p_is_compiled_as_unconditional_true(self):
        elements_raw, _ = id_inputs()
        from tests.test_prompt_v317 import expanded_plan
        candidate = expanded_plan()
        candidate['schema_version'] = 'report-formal-plan/7'
        candidate['precondition_ids'] = []
        candidate['precondition_terms'] = []
        formal = synthesize_id_formalization(candidate, elements_raw)
        self.assertEqual(
            formal['claims'][0]['properties']['preconditions']['expression'],
            {'const': True})

    def test_unknown_impact_is_rejected_before_formalization(self):
        elements, _ = id_inputs(); bad = plan(); bad['impact_ids'] = ['invented']
        with self.assertRaisesRegex(ValueError, 'invalid plan impact IDs'):
            synthesize_id_formalization(bad, elements)

    def test_precondition_cannot_be_encoded_with_impact_only_symbol(self):
        elements, _ = id_inputs()
        bad = plan()
        bad['precondition_terms'][0]['predicate'] = {
            'kind': 'truth', 'symbol': 'fee_revert', 'value': False}
        with self.assertRaisesRegex(ValueError, 'P predicate symbol not grounded'):
            synthesize_id_formalization(bad, elements)

    def test_precondition_may_share_symbol_grounded_by_another_selected_p(self):
        elements, _ = id_inputs()
        candidate = plan()
        candidate['precondition_ids'].append('assume_nonnegative')
        candidate['precondition_terms'].append({
            'source_id': 'assume_nonnegative',
            'predicate': {'kind': 'comparison', 'left': 'paid_fee', 'operator': 'ge',
                          'right': {'const': 0}}})
        self.assertEqual(synthesize_id_formalization(candidate, elements)
                         ['schema_version'], 'report-formalization/2')

    def test_v35_formalize_only_calls_model_once_and_replays(self):
        elements, _ = id_inputs(); candidate = plan()

        def fake(payload, output, model, prompt):
            request = json.loads(payload)
            self.assertIn('allowed_statement_ids', request)
            self.assertNotIn('effect_coverage', prompt)
            (output / 'model-claim.json').write_text(json.dumps(candidate))
            return copy.deepcopy(candidate)

        with tempfile.TemporaryDirectory() as work:
            root = Path(work)
            report = root / 'report.md'; report.write_text(TEXT)
            saved = root / 'elements.json'; saved.write_text(json.dumps(elements))
            output = root / 'output'
            argv = ['semantic_pipeline.py', '--report', str(report), '--formalize-only',
                    '--elements', str(saved), '--allow-report-upload', '--model', 'synthetic_control',
                    '--prompt-version', 'semantic-v3.5', '--output', str(output)]
            with patch('sys.argv', argv), patch.object(pipeline.r, 'extract', side_effect=fake) as call, \
                    patch('sys.stdout', io.StringIO()):
                pipeline.main()
            self.assertEqual(call.call_count, 1)
            self.assertEqual(json.loads((output / 'formal-plan.json').read_text()), candidate)
            self.assertTrue((output / 'formalization-ids.json').is_file())
            self.assertTrue(verify_semantic.verify(output)['offline_verified'])

    def test_mechanical_salvage_run_replays_in_verify(self):
        # S19 wiring: --mechanical-salvage runs used to write
        # mechanical-salvage.json that verify never re-applied, so every
        # salvaged run failed replay with 'neural formal plan changed'.  The
        # replay now re-applies the drop against the saved audited log.
        elements, _ = id_inputs(); candidate = plan()
        candidate['symbols']['zero_address'] = {
            'sort': 'int', 'unit': None, 'meaning': 'Unused placeholder symbol',
            'checkpoint': 'call_entry', 'entity_ids': [], 'source_ids': []}

        def fake(payload, output, model, prompt):
            (output / 'model-claim.json').write_text(json.dumps(candidate))
            return copy.deepcopy(candidate)

        with tempfile.TemporaryDirectory() as work:
            root = Path(work)
            report = root / 'report.md'; report.write_text(TEXT)
            saved = root / 'elements.json'; saved.write_text(json.dumps(elements))
            output = root / 'output'
            argv = ['semantic_pipeline.py', '--report', str(report), '--formalize-only',
                    '--elements', str(saved), '--mechanical-salvage',
                    '--allow-report-upload', '--model', 'synthetic_control',
                    '--prompt-version', 'semantic-v3.5', '--output', str(output)]
            with patch('sys.argv', argv), patch.object(pipeline.r, 'extract', side_effect=fake), \
                    patch('sys.stdout', io.StringIO()):
                pipeline.main()
            salvage_log = output / 'neural-formalization' / 'mechanical-salvage.json'
            self.assertTrue(salvage_log.is_file())
            repairs = json.loads(salvage_log.read_text())
            self.assertEqual([row['symbol'] for row in repairs], ['zero_address'])
            saved_plan = json.loads((output / 'formal-plan.json').read_text())
            self.assertNotIn('zero_address', saved_plan['symbols'])
            self.assertTrue(verify_semantic.verify(output)['offline_verified'])

    def test_prompt_delegates_mechanics_to_program(self):
        text = prompts.formal_prompt('ids', 'core')
        self.assertIn('program,\nnot you, will generate AST, coverage, formula_sources, SMT', text)
        self.assertIn('condition_forbids_effect', text)
        self.assertIn('effect_requires_any_authorization', text)
        self.assertNotIn('report-formalization/2', text)

    def test_v36_requires_exact_precondition_term_sources(self):
        text = prompts_v36.formal_prompt('ids', 'core')
        self.assertIn('exactly one entry for every precondition_ids ID', text)
        self.assertIn('never use a security_intent, impact, action or root_cause ID', text)
        self.assertIn('Select exactly one direct\nimpact', text)

    def test_v37_structures_unresolved_and_only_blocking_items_gate(self):
        elements, _ = id_inputs()
        candidate = plan()
        candidate['schema_version'] = 'report-formal-plan/2'
        candidate['unresolved'] = [
            {'category': 'missing_report_definition',
             'description': 'The report does not define the fee tolerance.',
             'source_ids': ['intent_accept_buffer'], 'blocks_formalization': True},
            {'category': 'missing_checkpoint',
             'description': 'A more precise observation checkpoint would improve replay.',
             'source_ids': ['impact_revert'], 'blocks_formalization': False},
        ]
        review = structured_unresolved_review(candidate, elements)
        self.assertEqual(review['blocking_count'], 1)
        self.assertEqual(review['advisory_count'], 1)
        formal = synthesize_id_formalization(candidate, elements)
        self.assertEqual(formal['claims'][0]['unresolved'], [
            '[missing_report_definition] The report does not define the fee tolerance.'
        ])

    def test_v37_rejects_unstructured_or_unknown_unresolved_category(self):
        elements, _ = id_inputs()
        candidate = plan()
        candidate['schema_version'] = 'report-formal-plan/2'
        candidate['unresolved'] = [
            {'category': 'symbolic_value_not_concrete',
             'description': 'The address is symbolic.',
             'source_ids': ['pre_overpay'], 'blocks_formalization': False},
        ]
        with self.assertRaisesRegex(ValueError, 'invalid structured unresolved category'):
            synthesize_id_formalization(candidate, elements)

    def test_v37_prompt_excludes_normal_symbolic_conditions(self):
        text = prompts_v37.formal_prompt('ids', 'core')
        self.assertIn('report-formal-plan/2', text)
        self.assertIn('blocks_formalization:boolean', text)
        self.assertIn('Concrete values are NOT required for symbolic addresses', text)
        self.assertIn('a Boolean\noutcome lacks a numeric definition', text)

    def test_v37_pipeline_preserves_advisory_without_blocking_claim(self):
        elements, _ = id_inputs()
        candidate = plan()
        candidate['schema_version'] = 'report-formal-plan/2'
        candidate['unresolved'] = [{
            'category': 'missing_checkpoint',
            'description': 'A narrower checkpoint would improve downstream binding.',
            'source_ids': ['impact_revert'],
            'blocks_formalization': False,
        }]

        def fake(payload, output, model, prompt):
            (output / 'model-claim.json').write_text(json.dumps(candidate))
            return copy.deepcopy(candidate)

        with tempfile.TemporaryDirectory() as work:
            root = Path(work)
            report = root / 'report.md'; report.write_text(TEXT)
            saved = root / 'elements.json'; saved.write_text(json.dumps(elements))
            output = root / 'output'
            argv = ['semantic_pipeline.py', '--report', str(report), '--formalize-only',
                    '--elements', str(saved), '--allow-report-upload', '--model', 'synthetic_control',
                    '--prompt-version', 'semantic-v3.7', '--output', str(output)]
            with patch('sys.argv', argv), patch.object(pipeline.r, 'extract', side_effect=fake), \
                    patch('sys.stdout', io.StringIO()):
                pipeline.main()
            review = json.loads((output / 'unresolved-review.json').read_text())
            self.assertEqual(review['advisory_count'], 1)
            self.assertEqual(json.loads((output / 'formalization.json').read_text())
                             ['claims'][0]['unresolved'], [])
            interface = json.loads((output / 'stage3-spec.json').read_text())
            self.assertEqual(interface['unresolved_review_path'], 'unresolved-review.json')
            self.assertTrue(verify_semantic.verify(output)['offline_verified'])


class MixedUnitGateSemanticsTests(unittest.TestCase):
    """blind-batch_06 (S18): the type/unit gate's mul mechanics decide which
    faithful encodings exist.  symbol-times-symbol always joins the units
    (no cancellation is inferred), so a unit-carrying scaling symbol is
    structurally unpassable; an inlined literal inherits the other
    operand's unit, so the scaled comparison passes when both compared
    symbols share one raw unit.  The repair teaching rests on exactly
    these two facts."""

    def setUp(self):
        # Other pipeline tests toggle this module-level compatibility switch;
        # restore the unit gate so results do not depend on test order.
        report_math.set_unit_guard(True)

    def test_scaling_symbol_product_unit_is_unpassable(self):
        symbols = {
            'pending_reward_amount': {'sort': 'int', 'unit': 'reward_token'},
            'precision_factor': {'sort': 'int', 'unit': 'dimensionless'},
            'total_shares': {'sort': 'int', 'unit': 'shares'},
        }
        relation = {'op': 'lt', 'args': [
            {'op': 'mul', 'args': [{'var': 'pending_reward_amount'},
                                   {'var': 'precision_factor'}]},
            {'var': 'total_shares'}]}
        # The exact blind-batch_06 message: operator plus BOTH operand
        # types, so the retry hint can name the failing comparison.
        with self.assertRaisesRegex(
                ValueError,
                r'type/unit mismatch: lt int dimensionless\*reward_token int shares'):
            report_math.expr_type(relation, symbols)

    def test_inlined_scaling_constant_passes_with_same_raw_units(self):
        symbols = {
            'pending_reward_amount': {'sort': 'int', 'unit': 'raw'},
            'total_shares': {'sort': 'int', 'unit': 'raw'},
        }
        relation = {'op': 'lt', 'args': [
            {'op': 'mul', 'args': [{'var': 'pending_reward_amount'},
                                   {'const': 1000000000000}]},
            {'var': 'total_shares'}]}
        self.assertEqual(report_math.expr_type(relation, symbols),
                         ('bool', None))


if __name__ == '__main__':
    unittest.main()
