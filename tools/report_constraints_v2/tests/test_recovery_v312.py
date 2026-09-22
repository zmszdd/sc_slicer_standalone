"""Stage-2 recovery and qualifier-preservation regressions (offline only)."""
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import z3

import report_only as report
from plan_synthesizer import _pattern_expressions
from semantic_pipeline import (compact_json, lean_formal_input, model_catalog,
                               referenced_evidence_ids, request_elements)
from evidence_catalog import build_catalog
from prompts.versions import semantic_prompts_v311 as previous
from prompts.versions import semantic_prompts_v312 as current


class RecoveryTests(unittest.TestCase):
    def test_json_failure_retries_once_and_keeps_artifacts(self):
        paths = []

        def fake_extract(payload, directory, model, prompt):
            paths.append(directory)
            if len(paths) == 1:
                (directory / 'model-response.txt').write_text('{"broken":')
                raise json.JSONDecodeError('truncated', '{"broken":', 10)
            return {'schema_version': 'report-elements/2'}

        with tempfile.TemporaryDirectory() as work:
            root = Path(work)
            result, attempts = request_elements('input', 'prompt', 'fake', root, 1,
                                                extract_fn=fake_extract)
            self.assertEqual(result['schema_version'], 'report-elements/2')
            self.assertEqual([x['outcome'] for x in attempts],
                             ['retryable_failure', 'parsed_json'])
            self.assertEqual(len(paths), 2)
            self.assertTrue((paths[0] / 'model-response.txt').is_file())
            self.assertIn('RETRY FEEDBACK', (paths[1] / 'prompt.txt').read_text())

    def test_timeout_not_retried_by_default(self):
        with tempfile.TemporaryDirectory() as work:
            root = Path(work)

            def timeout(*_args):
                raise subprocess.TimeoutExpired('fake', 1)

            with self.assertRaises(subprocess.TimeoutExpired):
                request_elements('input', 'prompt', 'fake', root, 0,
                                 extract_fn=timeout)
            self.assertEqual(len(json.loads((root / 'element-attempts.json').read_text())), 1)

    def test_structurally_incomplete_elements_retry_once(self):
        calls = []

        def fake_extract(*_args):
            calls.append(1)
            return {'complete': len(calls) == 2}

        def validate(candidate):
            if not candidate['complete']:
                raise ValueError('incomplete candidate')

        with tempfile.TemporaryDirectory() as work:
            root = Path(work)
            result, attempts = request_elements(
                'input', 'prompt', 'fake', root, 1,
                extract_fn=fake_extract, validate_fn=validate)
            self.assertTrue(result['complete'])
            self.assertEqual([row['outcome'] for row in attempts],
                             ['retryable_failure', 'parsed_json'])
            retry_prompt = (root / 'neural-elements-retry-1/prompt.txt').read_text()
            self.assertIn('no placeholder/note keys', retry_prompt)

    def test_runtime_failure_not_retried(self):
        with tempfile.TemporaryDirectory() as work:
            root = Path(work)

            def unavailable(*_args):
                raise RuntimeError('provider unavailable')

            with self.assertRaises(RuntimeError):
                request_elements('input', 'prompt', 'fake', root, 1,
                                 extract_fn=unavailable)
            self.assertEqual(len(json.loads((root / 'element-attempts.json').read_text())), 1)

    def test_new_prompt_preserves_exception_without_changing_frozen_prompt(self):
        self.assertIn('without', current.FORMAL_PLAN_PROMPT)
        self.assertIn('lawful version', current.FORMAL_PLAN_PROMPT)
        self.assertNotIn('lawful version', previous.FORMAL_PLAN_PROMPT)
        self.assertIn('semantic-v3.12', current.ID_ELEMENT_PROMPT)
        self.assertIn('narrow observable boundary', current.ID_ELEMENT_PROMPT)

    def test_existing_pattern_can_distinguish_lawful_and_bad_outcomes(self):
        # Synthetic control: proves the grammar can express the qualifier;
        # it does not prove that a model will choose it for a real report.
        symbols = {'authorized': {'sort': 'bool', 'unit': None},
                   'completed': {'sort': 'bool', 'unit': None}}
        safety, violation = _pattern_expressions({
            'kind': 'condition_forbids_effect',
            'condition': {'kind': 'truth', 'symbol': 'authorized', 'value': False},
            'effect': {'kind': 'truth', 'symbol': 'completed', 'value': True},
        }, symbols)
        variables = {'authorized': z3.Bool('authorized'),
                     'completed': z3.Bool('completed')}
        valid = z3.Solver()
        valid.add(variables['authorized'], variables['completed'],
                  report.lower(safety, variables))
        self.assertEqual(valid.check(), z3.sat)
        bad = z3.Solver()
        bad.add(z3.Not(variables['authorized']), variables['completed'],
                report.lower(violation, variables),
                z3.Not(report.lower(safety, variables)))
        self.assertEqual(bad.check(), z3.sat)

    def test_timeout_diagnostic_records_counts_not_partial_report(self):
        partial = b'{"type":"step_start"}\n{"type":"text","part":{"text":"SECRET"}}\n'
        with tempfile.TemporaryDirectory() as work:
            root = Path(work)
            with patch('report_only.subprocess.run', side_effect=
                       subprocess.TimeoutExpired('fake', 240, output=partial)):
                with self.assertRaises(subprocess.TimeoutExpired):
                    report.extract('report text', root, 'fake', 'prompt')
            diagnostic = (root / 'model-timeout-diagnostic.json').read_text()
            self.assertNotIn('SECRET', diagnostic)
            self.assertEqual(json.loads(diagnostic)['event_counts']['text'], 1)

    def test_lean_input_preserves_statement_meanings_without_duplicate_quotes(self):
        root = Path(__file__).resolve().parents[1] / 'evaluation/fresh_holdout_01/runs/' \
            'Brix_Money_qy7NXr77sDh__cSNXN84Wruw__JeqwSynbkaB'
        elements = json.loads((root / 'elements-ids.json').read_text())
        catalog = build_catalog((root / 'extraction-input.txt').read_text())
        lean = lean_formal_input(elements)
        full = {'elements': elements,
                'evidence_catalog': model_catalog(catalog, referenced_evidence_ids(elements))}
        self.assertEqual([x['id'] for x in lean['statements']],
                         [x['id'] for x in elements['statements']])
        self.assertEqual([x['text'] for x in lean['statements']],
                         [x['text'] for x in elements['statements']])
        self.assertNotIn('evidence_catalog', lean)
        self.assertLess(len(compact_json(lean)), len(compact_json(full)))


if __name__ == '__main__':
    unittest.main()
