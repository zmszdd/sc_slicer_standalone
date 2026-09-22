"""Semantic schema/gate regressions; not model accuracy evaluations."""
import ast
import copy
import io
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

import semantic_core as s
from semantic_core import (BOUNDARY, NORMALIZE, REJECT, WARN, classify,
                           entry_for, exact_entry_for, normalize_readiness)
import semantic_pipeline as p
import verify_semantic

HERE = Path(__file__).resolve().parents[1]
TEXT = (HERE / 'results/report_only/brix_fee_assistant_final/extraction-input.txt').read_text()


def inputs():
    return (json.loads((HERE / 'samples/brix_fee/elements.json').read_text()),
            json.loads((HERE / 'samples/brix_fee/formalization.json').read_text()))


class SemanticTests(unittest.TestCase):
    def test_elements_grounded(self):
        elements, _ = inputs()
        spans = s.validate_elements(elements, TEXT)
        self.assertIn('intent_accept_buffer', spans['statements'])

    def test_duplicate_quote_records_all_occurrences(self):
        result = s.evidence_spans(['fee'], 'fee and fee')
        self.assertEqual([x['start'] for x in result[0]['occurrences']], [0, 8])

    def test_fake_evidence_rejected(self):
        elements, _ = inputs(); elements['scope']['evidence'] = ['not in report']
        with self.assertRaises(ValueError): s.validate_elements(elements, TEXT)

    def test_duplicate_id_rejected(self):
        elements, _ = inputs(); elements['entities'].append(copy.deepcopy(elements['entities'][0]))
        with self.assertRaises(ValueError): s.validate_elements(elements, TEXT)

    def test_unknown_actor_rejected(self):
        elements, _ = inputs(); elements['statements'][0]['entity_ids'] = ['invented']
        with self.assertRaises(ValueError): s.validate_elements(elements, TEXT)

    def test_attack_order_only_actions(self):
        elements, _ = inputs(); elements['attack_steps'] = ['cause_equality']
        with self.assertRaises(ValueError): s.validate_elements(elements, TEXT)

    def test_safety_source_cannot_be_bug_impact(self):
        elements, formal = inputs()
        formal['claims'][0]['properties']['safety']['source_ids'] = ['impact_revert']
        with self.assertRaises(ValueError): s.compile_bundle(elements, formal, TEXT)

    def test_potential_effect_not_upgraded(self):
        elements, formal = inputs()
        next(x for x in elements['statements'] if x['id'] == 'impact_revert')['modality'] = 'potential'
        with self.assertRaises(ValueError): s.compile_bundle(elements, formal, TEXT)

    def test_missing_predicate_mapping_rejected(self):
        elements, formal = inputs(); formal['claims'][0]['formula_sources']['safety'] = {}
        with self.assertRaises(ValueError): s.compile_bundle(elements, formal, TEXT)

    def test_nonexistent_formula_path_rejected(self):
        elements, formal = inputs(); formal['claims'][0]['formula_sources']['safety']['args.99'] = ['intent_accept_buffer']
        with self.assertRaises(ValueError): s.compile_bundle(elements, formal, TEXT)

    def test_claim_cannot_silently_ignore_impact_coverage(self):
        elements, formal = inputs(); formal['claims'][0]['effect_coverage'].pop()
        with self.assertRaises(ValueError): s.compile_bundle(elements, formal, TEXT)

    def test_unit_mismatch_rejected(self):
        elements, formal = inputs(); formal['symbols']['quoted_fee']['unit'] = 'token_shares'
        with self.assertRaises(ValueError): s.compile_bundle(elements, formal, TEXT)

    def test_partial_effect_is_explicit_not_full_success(self):
        elements, formal = inputs(); result = s.compile_bundle(elements, formal, TEXT)
        self.assertEqual(result['core_formalization_status'], 'formalized_candidate')
        self.assertEqual(result['acceptance_status'], 'needs_review')
        self.assertFalse(result['execution_ready'])
        self.assertEqual(result['claims'][0]['semantic_relationship']['queries']['P_and_V_and_not_I'], 'sat')

    def test_inverted_safety_gated_automatically(self):
        elements, formal = inputs()
        claim = formal['claims'][0]
        claim['properties']['safety']['expression'] = copy.deepcopy(claim['properties']['effects']['expression'])
        claim['formula_sources']['safety'] = {path: ['intent_accept_buffer'] for path in
            s.predicate_paths(claim['properties']['safety']['expression'], formal['symbols'])}
        result = s.compile_bundle(elements, formal, TEXT, strict_piv=True)
        self.assertEqual(result['acceptance_status'], 'needs_review')
        self.assertEqual(result['claims'][0]['semantic_relationship']['queries']['P_and_V_and_not_I'], 'unsat')

    def test_missing_v_does_not_invalidate_core_i(self):
        elements, formal = inputs(); claim = formal['claims'][0]
        claim['properties']['effects']['expression'] = None
        claim['formula_sources']['effects'] = {}
        for row in claim['effect_coverage']: row['status'] = 'unformalized'
        result = s.compile_bundle(elements, formal, TEXT)
        self.assertEqual(result['core_formalization_status'], 'formalized_candidate')

    def test_unassigned_impacts_reported(self):
        elements, formal = inputs(); claim = formal['claims'][0]
        claim['impact_ids'].remove('impact_ux')
        claim['effect_coverage'] = [row for row in claim['effect_coverage'] if row['statement_id'] != 'impact_ux']
        self.assertIn('impact_ux', s.compile_bundle(elements, formal, TEXT)['unassigned_impact_ids'])

    def test_extracted_precondition_cannot_be_silently_dropped_from_formal_p(self):
        elements, formal = inputs()
        extra = copy.deepcopy(next(x for x in elements['statements'] if x['id'] == 'pre_overpay'))
        extra['id'] = 'pre_additional_core_condition'
        extra['text'] = 'A second report-supported prior condition for the same core scenario.'
        elements['statements'].append(extra)
        result = s.compile_bundle(elements, formal, TEXT, strict_piv=True)
        self.assertEqual(result['unassigned_precondition_ids'], ['pre_additional_core_condition'])
        self.assertIn('extracted preconditions not used by formal P', ' '.join(result['report_warnings']))
        self.assertEqual(result['acceptance_status'], 'needs_review')

    def test_multiple_claims_not_silently_merged(self):
        elements, formal = inputs(); extra = copy.deepcopy(formal['claims'][0]); extra['id'] = 'separate_claim'
        formal['claims'].append(extra)
        self.assertEqual(len(s.compile_bundle(elements, formal, TEXT)['claims']), 2)

    def test_external_report_requires_no_poc(self):
        with tempfile.TemporaryDirectory() as work:
            report = Path(work) / 'report.md'; report.write_text(TEXT)
            text, _, provenance = p.load_report(report_path=report)
            self.assertEqual(text, TEXT)
            self.assertFalse(provenance['paired_case_checked'])

    def test_json_input_uses_report_fields_only(self):
        with tempfile.TemporaryDirectory() as work:
            report = Path(work) / 'report.json'
            report.write_text(json.dumps({
                'title': 'Report title',
                'body': '## Finding description and impact\nLOSS\n## Mitigation\nSECRET_FIX',
                'proof_of_concept': 'SECRET_POC',
                'raw': 'SECRET_RAW',
            }))
            text, _, provenance = p.load_report(report_path=report)
            self.assertEqual(text, 'Report title\n\n## Finding description and impact\nLOSS')
            self.assertNotIn('SECRET_', text)
            self.assertEqual(provenance['report_input_policy']['source_format'], 'report.json')
            self.assertFalse(provenance['contract_file_read'])

    def test_case_directory_does_not_require_or_read_contract(self):
        with tempfile.TemporaryDirectory() as work:
            case = Path(work)
            (case / 'report.json').write_text(json.dumps({
                'title': 'Independent report input',
                'body': '## Finding description and impact\nA stated loss occurs.',
            }))
            text, _, provenance = p.load_report(case_dir=case)
            self.assertIn('A stated loss occurs.', text)
            self.assertFalse(provenance['contract_file_read'])
            self.assertFalse(provenance['paired_case_checked'])

    def test_extract_requires_consent_without_model_call(self):
        with patch('sys.argv', ['semantic_pipeline.py', '--report', 'unused.md', '--extract', '--output', 'unused']), patch.object(p.r, 'extract') as call, patch('sys.stderr', io.StringIO()):
            with self.assertRaises(SystemExit): p.main()
            call.assert_not_called()

    def test_legacy_quotes_full_mode_is_rejected_before_model_call(self):
        # All retained plan-synthesis versions support only grounded ID/core mode.
        with tempfile.TemporaryDirectory() as work:
            report = Path(work) / 'report.md'; report.write_text(TEXT)
            output = Path(work) / 'result'
            argv = ['semantic_pipeline.py', '--report', str(report), '--extract',
                    '--allow-report-upload', '--evidence-mode', 'quotes',
                    '--formalization-scope', 'full', '--model', 'synthetic_control',
                    '--output', str(output)]
            with patch('sys.argv', argv), patch.object(p.r, 'extract') as call, \
                    patch('sys.stderr', io.StringIO()), self.assertRaises(SystemExit):
                p.main()
            call.assert_not_called()
            self.assertFalse(output.exists())

    def test_invalid_elements_stop_before_second_neural_call(self):
        with tempfile.TemporaryDirectory() as work:
            report = Path(work) / 'report.md'; report.write_text(TEXT)
            with patch('sys.argv', ['semantic_pipeline.py', '--report', str(report), '--extract', '--allow-report-upload', '--model', 'synthetic_control', '--output', str(Path(work) / 'result')]), patch.object(p.r, 'extract', return_value={}) as call, patch('sys.stdout', io.StringIO()):
                self.assertEqual(p.main(), 2)
                self.assertEqual(call.call_count, 1)

    def test_saved_bundle_replay(self):
        directory = HERE / 'results/semantic/brix_fee_offline_01'
        self.assertTrue(verify_semantic.verify(directory)['offline_verified'])

    def test_tampered_bundle_rejected(self):
        directory = HERE / 'results/semantic/brix_fee_offline_01'
        with tempfile.TemporaryDirectory() as work:
            copied = Path(work) / 'case'; shutil.copytree(directory, copied)
            (copied / 'elements.json').write_text('{}')
            with self.assertRaises(ValueError): verify_semantic.verify(copied)




# ======================================================================
# Normalization boundary (S13).  Same-function tests live in the file that
# tests the module holding the code.
# ======================================================================
STAGE2 = HERE


LIB_MODULES = ('lib/ingest.py', 'lib/semantic_core.py', 'lib/plan_synthesizer.py',
               'lib/report_only.py')
RAISED = ('ValueError', 'RuntimeError')


def _literal(node):
    """The statically visible message text, including an f-string's literal parts."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.JoinedStr):
        return ''.join(part.value for part in node.values
                       if isinstance(part, ast.Constant)
                       and isinstance(part.value, str))
    if isinstance(node, ast.BinOp):
        return _literal(node.left) or _literal(node.right)
    return None


def rejection_messages():
    """Every message the lib layer can use to abort a run, derived from source."""
    found = {}
    for relative in LIB_MODULES:
        tree = ast.parse((STAGE2 / relative).read_text(encoding='utf-8'))
        for node in ast.walk(tree):
            message = None
            if isinstance(node, ast.Call):
                name = (getattr(node.func, 'id', None)
                        or getattr(node.func, 'attr', None))
                if name == 'require' and len(node.args) >= 2:
                    message = _literal(node.args[1])
            elif isinstance(node, ast.Raise) and isinstance(node.exc, ast.Call):
                if getattr(node.exc.func, 'id', None) in RAISED and node.exc.args:
                    message = _literal(node.exc.args[0])
            if message:
                found.setdefault(message, f'{relative}:{node.lineno}')
    return found


class BoundaryCoverageTest(unittest.TestCase):
    """The boundary is only real if nothing can bypass it."""

    def test_every_rejection_message_is_classified(self):
        """A new ``require(...)`` must declare its mode or this test fails."""
        # exact_entry_for, not entry_for: a truncated entry must NOT count as
        # declared, otherwise the boundary can lose a point without failing here.
        unlisted = sorted(message for message in rejection_messages()
                          if exact_entry_for(message) is None)
        self.assertEqual(
            unlisted, [],
            f'{len(unlisted)} rejection message(s) absent from BOUNDARY: '
            + '; '.join(repr(m) for m in unlisted[:5]))

    def test_entries_are_unique_and_use_known_modes(self):
        messages = [entry[0] for entry in BOUNDARY]
        self.assertEqual(len(messages), len(set(messages)),
                         'duplicate BOUNDARY entry')
        for entry in BOUNDARY:
            with self.subTest(message=entry[0]):
                self.assertIn(entry[1], (NORMALIZE, WARN, REJECT))

    def test_warn_is_empty_by_design(self):
        """Declared-uncertainty semantics live in compile_bundle (S12), not here."""
        self.assertEqual([e for e in BOUNDARY if e[1] == WARN], [])

    def test_unlisted_messages_default_to_reject(self):
        """The default is the historical behaviour, so nothing normalizes by accident."""
        self.assertEqual(classify('a rejection nobody wrote down'), REJECT)


class ReadinessNormalizationTest(unittest.TestCase):
    """The one proven in-boundary fix: pure position, no semantic change."""

    @staticmethod
    def _nested():
        return {'schema_version': 'report-readiness/1', 'decision': 'ready',
                'dimensions': {'affected_subject': {'status': 'present'},
                               'missing_dimensions': [], 'summary': 'ok'}}

    def test_hoists_nested_telemetry(self):
        normalized, changes = normalize_readiness(self._nested())
        self.assertEqual(sorted(normalized), ['decision', 'dimensions',
                                              'missing_dimensions',
                                              'schema_version', 'summary'])
        self.assertEqual(sorted(normalized['dimensions']), ['affected_subject'])
        self.assertEqual(changes, ['hoisted missing_dimensions out of dimensions',
                                   'hoisted summary out of dimensions'])

    def test_a_well_formed_response_is_untouched(self):
        candidate = {'schema_version': 'report-readiness/1', 'decision': 'ready',
                     'dimensions': {'affected_subject': {'status': 'present'}},
                     'missing_dimensions': [], 'summary': 'ok'}
        self.assertEqual(normalize_readiness(candidate), (candidate, []))

    def test_top_level_values_are_never_overwritten(self):
        candidate = self._nested()
        candidate['summary'] = 'authoritative'
        normalized, changes = normalize_readiness(candidate)
        self.assertEqual(normalized['summary'], 'authoritative')
        self.assertEqual(changes, ['hoisted missing_dimensions out of dimensions'])

    def test_the_input_is_never_mutated(self):
        """Purity is what keeps the raw response auditable after a correction."""
        import copy
        candidate = self._nested()
        snapshot = copy.deepcopy(candidate)
        normalize_readiness(candidate)
        self.assertEqual(candidate, snapshot)

    def test_malformed_shapes_are_left_for_the_validator(self):
        for candidate in (None, 'text', {'dimensions': 'not-a-dict'},
                          {'decision': 'ready'}):
            with self.subTest(candidate=candidate):
                self.assertEqual(normalize_readiness(candidate), (candidate, []))


class ScreeningNormalizationWiringTest(unittest.TestCase):
    """Wiring guard: without this, deleting the call keeps every test green.

    The fixer's own tests above would still pass if ``cli/semantic_pipeline.py``
    stopped calling it, which is exactly the gap this class closes.
    """

    def test_a_nested_screening_response_does_not_abort_the_run(self):
        import io
        import json
        import sys
        import tempfile
        from unittest.mock import patch

        import semantic_pipeline as pipeline

        reached = {}

        def fake(payload, output, _model, _prompt, **_kwargs):
            if output.name == 'neural-input-screen':
                ids = [row['id'] for row in json.loads(payload)['fragments']]
                names = ('affected_subject', 'trigger_or_action',
                         'direct_effect', 'safety_relation_basis')
                # The exact slip observed on the gold-v1 blind run: the two
                # telemetry keys arrive one level too deep.
                return {'schema_version': 'report-readiness/1',
                        'decision': 'ready',
                        'dimensions': {name: {'status': 'present',
                                              'evidence_ids': [ids[0]],
                                              'reason': 'supported'}
                                       for name in names}
                        | {'missing_dimensions': [], 'summary': 'sufficient'}}
            reached['elements'] = True
            raise RuntimeError('stop after screening')

        with tempfile.TemporaryDirectory() as dirname:
            root = Path(dirname)
            source = root / 'report.md'
            source.write_text('# Finding description\n\nA body.\n')
            out = root / 'run'
            argv = ['semantic_pipeline.py', '--report', str(source), '--extract',
                    '--elements-only', '--provider', 'deepseek',
                    '--allow-report-upload', '--output', str(out)]
            previous = sys.argv
            try:
                sys.argv = argv
                with patch.object(pipeline.r, 'load_deepseek_key',
                                  return_value='test-key'), \
                        patch.object(pipeline.r, 'extract_deepseek',
                                     side_effect=fake), \
                        patch('sys.stdout', io.StringIO()):
                    pipeline.main()
            finally:
                sys.argv = previous

            self.assertTrue(reached.get('elements'),
                            'screening was rejected instead of normalized')
            log = json.loads(
                (out / 'neural-input-screen' / 'normalization-log.json').read_text())
            self.assertEqual(log['mode'], NORMALIZE)
            self.assertEqual(log['changes'],
                             ['hoisted missing_dimensions out of dimensions',
                              'hoisted summary out of dimensions'])
            provenance = json.loads((out / 'provenance.json').read_text())
            self.assertEqual(provenance['input_screening_normalizations'],
                             log['changes'])


if __name__ == '__main__': unittest.main()
