"""Classified relation plan and prompt regressions; no external model calls."""
import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from lib import report_only as report_math
from cli import semantic_pipeline as pipeline
from prompts.versions import semantic_prompts_v314 as previous
from prompts.versions import semantic_prompts_v315 as current
from lib.plan_synthesizer import (_pattern_expressions, CLASSIFIED_PLAN_VERSION,
                              classified_relation_alignment, synthesize_id_formalization)
from tests.test_evidence_ids import id_inputs, TEXT
from tests.test_plan_synthesizer import plan
from cli import batch_verify as verify_semantic


class PromptV315Tests(unittest.TestCase):
    def test_prompt_adds_relation_taxonomy_without_changing_v314(self):
        old = previous.formal_prompt('ids', 'core')
        new = current.formal_prompt('ids', 'core')
        self.assertNotIn('report-formal-plan/3', old)
        self.assertIn('semantic-v3.15', new)
        self.assertIn('report-formal-plan/3', new)
        self.assertIn('relation_class', new)
        for name in ('bounded_value', 'monotonicity', 'conservation',
                     'proportional_fairness', 'state_correspondence',
                     'temporal_validity', 'sequence_preservation',
                     'data_structure_integrity', 'progress_or_liveness',
                     'range_capacity'):
            self.assertIn(name, new)
        self.assertIn('one to four direct impact', current.ID_ELEMENT_PROMPT)
        self.assertIn('may reference ONLY a symbol declared with sort:"bool"', new)
        self.assertIn('Every symbol referenced anywhere', new)
        self.assertIn('state_correspondence uses relation_obligation', new)
        self.assertIn('select the impact that most directly negates', new)
        self.assertIn('Validation bypass', new)
        self.assertIn('Never write truth(address_field)', new)

    def test_relation_obligation_supports_addition(self):
        symbols = {
            'enabled': {'sort': 'bool', 'unit': None},
            'assets': {'sort': 'int', 'unit': 'token'},
            'fees': {'sort': 'int', 'unit': 'token'},
            'reported_total': {'sort': 'int', 'unit': 'token'},
        }
        pattern = {
            'kind': 'relation_obligation',
            'condition': {'kind': 'truth', 'symbol': 'enabled', 'value': True},
            'relation': {
                'kind': 'relation',
                'left': {'op': 'add', 'args': [
                    {'symbol': 'assets'}, {'symbol': 'fees'}]},
                'operator': 'eq',
                'right': {'symbol': 'reported_total'},
            },
        }
        safety, violation = _pattern_expressions(pattern, symbols)
        self.assertEqual(report_math.expr_type(safety, symbols), ('bool', None))
        self.assertEqual(report_math.expr_type(violation, symbols), ('bool', None))

    def test_exact_power_of_two_operand_compiles_to_integer(self):
        symbols = {
            'enabled': {'sort': 'bool', 'unit': None},
            'supply': {'sort': 'int', 'unit': 'token'},
        }
        pattern = {
            'kind': 'relation_obligation',
            'condition': {'kind': 'truth', 'symbol': 'enabled', 'value': True},
            'relation': {
                'kind': 'comparison', 'left': 'supply', 'operator': 'lt',
                'right': {'power_of_two': 127, 'offset': -1},
            },
        }
        safety, _ = _pattern_expressions(pattern, symbols)
        relation = safety['args'][1]
        self.assertEqual(relation['args'][1], {'const': 2**127 - 1})

    def test_malformed_comparison_left_is_a_clean_validation_error(self):
        symbols = {'amount': {'sort': 'int', 'unit': 'token'}}
        pattern = {
            'kind': 'relation_obligation',
            'condition': {'kind': 'comparison',
                          'left': {'symbol': 'amount'}, 'operator': 'gt',
                          'right': {'const': 0}},
            'relation': {'kind': 'comparison', 'left': 'amount', 'operator': 'gt',
                         'right': {'const': 0}},
        }
        with self.assertRaisesRegex(ValueError, 'unknown comparison symbol'):
            _pattern_expressions(pattern, symbols)

    def test_trivial_self_comparison_is_rejected(self):
        symbols = {
            'active': {'sort': 'bool', 'unit': None},
            'amount': {'sort': 'int', 'unit': 'token'},
        }
        pattern = {
            'kind': 'relation_obligation',
            'condition': {'kind': 'truth', 'symbol': 'active', 'value': True},
            'relation': {'kind': 'comparison', 'left': 'amount', 'operator': 'eq',
                         'right': {'symbol': 'amount'}},
        }
        with self.assertRaisesRegex(ValueError, 'trivial self-comparison predicate'):
            _pattern_expressions(pattern, symbols)

    def test_monotonicity_and_conservation_compile(self):
        symbols = {
            'trigger': {'sort': 'bool', 'unit': None},
            'before': {'sort': 'int', 'unit': 'token'},
            'after': {'sort': 'int', 'unit': 'token'},
            'delta': {'sort': 'int', 'unit': 'token'},
        }
        truth = {'kind': 'truth', 'symbol': 'trigger', 'value': True}
        patterns = [
            {'kind': 'monotonicity', 'trigger': truth, 'before_symbol': 'before',
             'after_symbol': 'after', 'direction': 'nondecreasing'},
            {'kind': 'conservation', 'trigger': truth,
             'before': {'op': 'add', 'args': [
                 {'symbol': 'before'}, {'symbol': 'delta'}]},
             'after': {'symbol': 'after'}},
        ]
        for pattern in patterns:
            safety, violation = _pattern_expressions(pattern, symbols)
            self.assertEqual(report_math.expr_type(safety, symbols), ('bool', None))
            self.assertEqual(report_math.expr_type(violation, symbols), ('bool', None))

    def test_relation_class_must_match_pattern(self):
        elements, _ = id_inputs()
        candidate = plan()
        candidate['schema_version'] = CLASSIFIED_PLAN_VERSION
        candidate['relation_class'] = 'monotonicity'
        with self.assertRaisesRegex(ValueError, 'relation class and pattern mismatch'):
            synthesize_id_formalization(candidate, elements)

    def test_element_layer_accepts_four_impacts_but_plan_selects_one(self):
        elements, _ = id_inputs()
        base_impact = next(row for row in elements['statements']
                           if row['kind'] == 'impact')
        elements['statements'] = [row for row in elements['statements']
                                  if row['kind'] != 'impact']
        impact_ids = []
        for index in range(4):
            row = copy.deepcopy(base_impact)
            row['id'] = f'impact_branch_{index}'
            elements['statements'].append(row)
            impact_ids.append(row['id'])
        from lib.ingest import build_catalog
        pipeline.validate_core_element_candidate(
            elements, build_catalog(TEXT), TEXT,
            require_core_counts=True, max_core_impacts=4)
        candidate = plan()
        candidate['schema_version'] = CLASSIFIED_PLAN_VERSION
        candidate['relation_class'] = 'progress_or_liveness'
        candidate['impact_ids'] = [impact_ids[0]]
        candidate['symbols']['fee_revert']['source_ids'] = [
            candidate['intent_id'], impact_ids[0]]
        formal = synthesize_id_formalization(candidate, elements)
        self.assertEqual(formal['claims'][0]['impact_ids'], [impact_ids[0]])
        candidate['impact_ids'] = impact_ids[:2]
        with self.assertRaisesRegex(ValueError, 'invalid plan impact IDs'):
            synthesize_id_formalization(candidate, elements)

    def test_classified_relation_requires_intent_and_all_impacts(self):
        elements, _ = id_inputs()
        candidate = plan()
        candidate['schema_version'] = CLASSIFIED_PLAN_VERSION
        candidate['relation_class'] = 'progress_or_liveness'
        with self.assertRaisesRegex(ValueError,
                                    'core relation observables lack intent/impact grounding'):
            synthesize_id_formalization(candidate, elements)
        candidate['symbols']['fee_revert']['source_ids'].append(candidate['intent_id'])
        review = classified_relation_alignment(candidate, elements)
        self.assertTrue(review['passed'])
        self.assertEqual(review['core_observables'], ['fee_revert'])

    def test_v315_pipeline_and_offline_replay(self):
        elements, _ = id_inputs()
        candidate = plan()
        candidate['schema_version'] = CLASSIFIED_PLAN_VERSION
        candidate['relation_class'] = 'progress_or_liveness'
        candidate['symbols']['fee_revert']['source_ids'].append(candidate['intent_id'])

        def fake(_payload, output, _model, _prompt):
            (output / 'model-claim.json').write_text(json.dumps(candidate))
            return copy.deepcopy(candidate)

        with tempfile.TemporaryDirectory() as work:
            root = Path(work)
            report = root / 'report.md'
            report.write_text(TEXT)
            saved = root / 'elements.json'
            saved.write_text(json.dumps(elements))
            output = root / 'output'
            argv = ['semantic_pipeline.py', '--report', str(report), '--formalize-only',
                    '--elements', str(saved), '--allow-report-upload',
                    '--prompt-version', 'semantic-v3.15', '--output', str(output)]
            with patch('sys.argv', argv), patch.object(pipeline, 'configured_model', return_value='synthetic_control'), \
                    patch.object(pipeline.r, 'extract', side_effect=fake), \
                    patch('sys.stdout', io.StringIO()):
                pipeline.main()
            self.assertEqual(json.loads((output / 'formal-plan.json').read_text())
                             ['relation_class'], 'progress_or_liveness')
            self.assertTrue(json.loads((output / 'relation-alignment.json').read_text())
                            ['passed'])
            self.assertTrue(verify_semantic.verify(output)['offline_verified'])


if __name__ == '__main__':
    unittest.main()
