"""Evidence IDs and report-only countermodel controls; no model-service calls."""
import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import z3
from lib import ingest as e
from cli import semantic_pipeline as p
from lib.semantic_core import validate_elements, validate_formalization
from lib.solving import solve_queries, verify_witness
from tests.test_report_only import fixture, TEXT as CONTROL_TEXT
from cli import batch_verify as verify_semantic

HERE = Path(__file__).resolve().parents[1]
TEXT = (HERE / 'results/report_only/brix_fee_assistant_final/extraction-input.txt').read_text()


def id_inputs():
    return (json.loads((HERE / 'samples/brix_fee/ids/elements.json').read_text()),
            json.loads((HERE / 'samples/brix_fee/ids/formalization.json').read_text()))


class EvidenceTests(unittest.TestCase):
    def test_catalog_is_deterministic_and_exact(self):
        catalog = e.build_catalog(TEXT)
        self.assertEqual(catalog, e.build_catalog(TEXT))
        for row in catalog['fragments']:
            self.assertEqual(TEXT[row['start']:row['end']], row['text'])

    def test_long_lines_bounded_without_text_rewrite(self):
        text = '  ' + 'x' * 1500 + '\n'
        rows = e.build_catalog(text)['fragments']
        self.assertTrue(all(len(x['text']) <= 700 for x in rows))
        self.assertEqual(''.join(x['text'] for x in rows), 'x' * 1500)

    def test_unknown_id_rejected(self):
        with self.assertRaises(ValueError): e.resolve(['unknown'], e.build_catalog(TEXT), TEXT)

    def test_duplicate_id_rejected(self):
        catalog = e.build_catalog(TEXT); ident = catalog['fragments'][0]['id']
        with self.assertRaises(ValueError): e.resolve([ident, ident], catalog, TEXT)

    def test_cross_report_id_rejected(self):
        ident = e.build_catalog('other report')['fragments'][0]['id']
        with self.assertRaises(ValueError): e.resolve([ident], e.build_catalog(TEXT), TEXT)

    def test_tampered_catalog_rejected(self):
        catalog = e.build_catalog(TEXT); ident = catalog['fragments'][0]['id']
        catalog['fragments'][0]['start'] += 1
        with self.assertRaises(ValueError): e.resolve([ident], catalog, TEXT)

    def test_id_hydration_keeps_formula_unchanged(self):
        elements, formal = id_inputs(); catalog = e.build_catalog(TEXT)
        resolved = e.hydrate_formalization(formal, catalog, TEXT)
        original = json.loads((HERE / 'samples/brix_fee/formalization.json').read_text())
        for name in ('preconditions', 'safety', 'effects'):
            self.assertEqual(resolved['claims'][0]['properties'][name]['expression'], original['claims'][0]['properties'][name]['expression'])
        validate_formalization(resolved, e.hydrate_elements(elements, catalog, TEXT), TEXT)

    def test_model_cannot_mix_quotes_and_ids(self):
        elements, _ = id_inputs(); elements['entities'][0]['evidence'] = ['invented text']
        with self.assertRaises(ValueError): e.hydrate_elements(elements, e.build_catalog(TEXT), TEXT)

    def test_unknown_entity_evidence_id_stops_hydration(self):
        elements, _ = id_inputs(); elements['entities'][0]['evidence_ids'] = ['invented']
        with self.assertRaises(ValueError): e.hydrate_elements(elements, e.build_catalog(TEXT), TEXT)

    def test_default_id_neural_orchestration_is_synthetic_only(self):
        elements, _ = id_inputs()
        formal = {
            'schema_version': 'report-formal-plan/4',
            'relation_class': 'progress_or_liveness',
            'precondition_ids': ['pre_overpay'],
            'intent_id': 'intent_accept_buffer',
            'impact_ids': ['impact_revert'],
            'symbols': {
                'paid_fee': {'sort': 'int', 'unit': 'native_wei',
                             'meaning': 'Native fee supplied by the caller',
                             'checkpoint': 'call_entry',
                             'entity_ids': ['caller', 'native_fee'],
                             'source_ids': ['pre_overpay']},
                'required_fee': {'sort': 'int', 'unit': 'native_wei',
                                 'meaning': 'Required native fee',
                                 'checkpoint': 'call_entry',
                                 'entity_ids': ['messenger', 'native_fee'],
                                 'source_ids': ['pre_overpay']},
                'fee_revert': {'sort': 'bool', 'unit': None,
                               'meaning': 'Fee mismatch revert',
                               'checkpoint': 'call_exit',
                               'entity_ids': ['caller', 'messenger'],
                               'source_ids': ['impact_revert']},
            },
            'precondition_terms': [{
                'source_id': 'pre_overpay',
                'predicate': {'kind': 'comparison', 'left': 'paid_fee',
                              'operator': 'gt', 'right': {'symbol': 'required_fee'}},
            }],
            'derived_definitions': [],
            'pattern': {
                'kind': 'relation_obligation',
                'condition': {'kind': 'comparison', 'left': 'paid_fee',
                              'operator': 'gt', 'right': {'symbol': 'required_fee'}},
                'relation': {'kind': 'truth', 'symbol': 'fee_revert', 'value': False},
            },
            'assumptions': [],
            'unresolved': [],
            'limitations': [],
        }
        def fake(text, output, model, prompt):
            data = json.loads(text)
            if output.name == 'neural-elements':
                self.assertIn('fragments', data)
                value = elements
            else:
                self.assertEqual(set(data), {
                    'elements', 'evidence_catalog', 'allowed_statement_ids'})
                self.assertEqual(data['elements']['schema_version'], 'report-elements/2')
                value = formal
            (output / 'model-claim.json').write_text(json.dumps(value))
            return copy.deepcopy(value)
        with tempfile.TemporaryDirectory() as work:
            source = Path(work) / 'report.md'; source.write_text(TEXT)
            output = Path(work) / 'out'
            with patch('sys.argv', ['semantic_pipeline.py', '--report', str(source), '--extract', '--allow-report-upload', '--model', 'synthetic_control', '--output', str(output)]), patch.object(p.r, 'extract', side_effect=fake) as call, patch('sys.stdout', io.StringIO()):
                self.assertEqual(p.main(), 2)
                self.assertEqual(call.call_count, 2)
            self.assertTrue(verify_semantic.verify(output)['offline_verified'])

    def test_id_saved_bundle_offline_verifies(self):
        self.assertTrue(verify_semantic.verify(HERE / 'results/semantic/brix_fee_ids_offline_01')['offline_verified'])

    def test_review_only_can_continue_without_claiming_semantic_truth(self):
        elements, formal = id_inputs()
        with tempfile.TemporaryDirectory() as work:
            root = Path(work)
            report = root / 'report.md'; report.write_text(TEXT)
            element_path = root / 'elements.json'; element_path.write_text(json.dumps(elements))
            formal_path = root / 'formalization.json'; formal_path.write_text(json.dumps(formal))
            output = root / 'continued'
            argv = ['semantic_pipeline.py', '--report', str(report),
                    '--elements', str(element_path), '--formalization', str(formal_path),
                    '--prompt-version', 'semantic-v3.12', '--continue-on-review',
                    '--output', str(output)]
            with patch('sys.argv', argv), patch('sys.stdout', io.StringIO()):
                self.assertEqual(p.main(), 0)
            status = json.loads((output / 'status.json').read_text())
            interface = json.loads((output / 'stage3-spec.json').read_text())
            self.assertEqual(status['acceptance_status'], 'needs_review')
            self.assertTrue(status['stage2_can_continue'])
            self.assertTrue(status['warnings'])
            self.assertTrue(interface['stage2_can_continue'])
            self.assertFalse(interface['execution_ready'])
            self.assertFalse(json.loads((output / 'auto-triage.json').read_text())[
                'semantic_truth_verified'])
            self.assertTrue(verify_semantic.verify(output)['offline_verified'])


class CountermodelTests(unittest.TestCase):
    def test_safety_countermodel_is_checked(self):
        claim = fixture(); results = solve_queries(claim, CONTROL_TEXT)
        self.assertEqual(results['P_and_not_I']['status'], 'sat')
        self.assertTrue(verify_witness(claim, 'P_and_not_I', results['P_and_not_I']['witness']))

    def test_unsat_has_no_countermodel(self):
        claim = fixture(); claim['properties']['safety']['expression'] = {'const': True}
        result = solve_queries(claim, CONTROL_TEXT)['P_and_not_I']
        self.assertEqual(result['status'], 'unsat'); self.assertIsNone(result['witness'])

    def test_query_smt_can_replay(self):
        for result in solve_queries(fixture(), CONTROL_TEXT).values():
            solver = z3.Solver(); solver.add(z3.parse_smt2_string(result['smt']))
            self.assertEqual(str(solver.check()), result['status'])

    def test_tampered_countermodel_rejected(self):
        claim = fixture(); witness = solve_queries(claim, CONTROL_TEXT)['P_and_not_I']['witness']
        witness['fee_revert']['value'] = False
        with self.assertRaises(ValueError): verify_witness(claim, 'P_and_not_I', witness)

    def test_address_countermodel_is_identity_not_integer(self):
        claim = fixture()
        for name in ('paid', 'quoted'): claim['symbols'][name]['sort'] = 'address'; claim['symbols'][name]['unit'] = None
        claim['properties']['safety']['expression'] = {'op': 'eq', 'args': [{'var': 'paid'}, {'var': 'quoted'}]}
        witness = solve_queries(claim, CONTROL_TEXT)['P_and_not_I']['witness']
        self.assertTrue(verify_witness(claim, 'P_and_not_I', witness))


if __name__ == '__main__': unittest.main()
