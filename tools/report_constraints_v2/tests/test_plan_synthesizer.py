"""Deterministic v3.5 plan synthesis controls; no external calls."""
import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from evidence_catalog import build_catalog, hydrate_elements, hydrate_formalization
from plan_synthesizer import (_pattern_expressions, structured_unresolved_review,
                              synthesize_id_formalization)
import report_only as report_math
import semantic_core
import semantic_pipeline as pipeline
from prompts.versions import semantic_prompts_v35 as prompts
from prompts.versions import semantic_prompts_v36 as prompts_v36
from prompts.versions import semantic_prompts_v37 as prompts_v37
from tests.test_evidence_ids import id_inputs, TEXT
import verify_semantic


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


if __name__ == '__main__':
    unittest.main()
