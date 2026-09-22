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
from semantic_core import (BOUNDARY, MAX_PLAN_SYMBOLS, NORMALIZE, REJECT, WARN,
                           classify, entry_for, exact_entry_for,
                           normalize_readiness, normalize_truth_binding)
import plan_synthesizer
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



class TruthBindingNormalizationTest(unittest.TestCase):
    """The second in-boundary fix: declare the boolean the plan already names.

    Observed on a real run: the entry for ``p_domain_separator_computed_once``
    carried ``{"kind": "truth", "symbol": "domain_separator_computed_once",
    "value": true}`` -- the name is exactly that entry's own ``source_id``
    without its ``p_`` prefix -- and the plan never declared the symbol, so
    ``_predicate`` raised ``invalid truth binding``.
    """

    @staticmethod
    def _statement(identifier, kind, text):
        return {'id': identifier, 'kind': kind, 'text': text,
                'modality': 'asserted', 'entity_ids': ['contract'],
                'evidence_ids': ['e_0001']}

    @classmethod
    def elements(cls):
        return {
            'scope': {'flow': 'domain separator'},
            'statements': [
                cls._statement('p_separator_cached_once', 'precondition',
                               'The contract computes its DOMAIN_SEPARATOR once.'),
                cls._statement('p_chain_id_changes', 'precondition',
                               'The chain ID later changes.'),
                cls._statement('si_separator_matches_chain', 'security_intent',
                               'The separator should match the current chain.'),
                cls._statement('i_signature_mismatch', 'impact',
                               'Signatures become invalid.')],
            'entities': [{'id': 'contract', 'name': 'Contract',
                          'role': 'contract'}]}

    @staticmethod
    def _bool_symbol(meaning, checkpoint, sources):
        return {'sort': 'bool', 'unit': None, 'meaning': meaning,
                'checkpoint': checkpoint, 'entity_ids': ['contract'],
                'source_ids': list(sources)}

    @classmethod
    def declared(cls):
        """The two booleans the fix is allowed to add, spelled out correctly."""
        return {
            'separator_cached_once': cls._bool_symbol(
                'The contract computes its DOMAIN_SEPARATOR once.',
                'separator_cached_once', ['p_separator_cached_once']),
            'chain_id_changes': cls._bool_symbol(
                'The chain ID later changes.', 'chain_id_changes',
                ['p_chain_id_changes'])}

    @classmethod
    def plan(cls):
        return {
            'schema_version': 'report-formal-plan/4',
            'relation_class': 'state_correspondence',
            'precondition_ids': ['p_separator_cached_once', 'p_chain_id_changes'],
            'intent_id': 'si_separator_matches_chain',
            'impact_ids': ['i_signature_mismatch'],
            'symbols': {'signature_valid': cls._bool_symbol(
                'whether a signature verifies', 'signature_valid',
                ['si_separator_matches_chain', 'i_signature_mismatch'])},
            'precondition_terms': [
                {'source_id': 'p_separator_cached_once',
                 'predicate': {'kind': 'truth', 'symbol': 'separator_cached_once',
                               'value': True}},
                {'source_id': 'p_chain_id_changes',
                 'predicate': {'kind': 'truth', 'symbol': 'chain_id_changes',
                               'value': True}}],
            'pattern': {
                'kind': 'relation_obligation',
                'condition': {'kind': 'truth', 'symbol': 'separator_cached_once',
                              'value': True},
                'relation': {'kind': 'truth', 'symbol': 'signature_valid',
                             'value': True}},
            'derived_definitions': [],
            'assumptions': [], 'unresolved': [], 'limitations': []}

    # ---- the fix ----

    def test_message_is_declared_as_normalize(self):
        self.assertEqual(classify('invalid truth binding'), NORMALIZE)

    def test_the_unfixed_plan_fails_with_the_declared_message(self):
        with self.assertRaisesRegex(ValueError, 'invalid truth binding'):
            plan_synthesizer.synthesize_id_formalization(self.plan(),
                                                        self.elements())

    def test_declaring_the_named_symbol_lets_the_plan_validate(self):
        fixed, changes = normalize_truth_binding(self.plan(), self.elements())
        plan_synthesizer.synthesize_id_formalization(fixed, self.elements())
        self.assertEqual([change['symbol'] for change in changes],
                         ['separator_cached_once', 'chain_id_changes'])
        self.assertEqual(changes[0], {
            'kind': 'declare_truth_symbol', 'symbol': 'separator_cached_once',
            'source_id': 'p_separator_cached_once',
            'reason': 'a truth predicate named it but the plan never declared it'})

    def test_the_declaration_invents_nothing(self):
        """sort is forced by the ``truth`` kind; the rest is the source's own."""
        fixed, _ = normalize_truth_binding(self.plan(), self.elements())
        self.assertEqual(fixed['symbols']['separator_cached_once'],
                         self.declared()['separator_cached_once'])

    def test_the_input_is_never_mutated(self):
        candidate = self.plan()
        snapshot = copy.deepcopy(candidate)
        normalize_truth_binding(candidate, self.elements())
        self.assertEqual(candidate, snapshot)

    def test_a_correctly_declared_plan_is_untouched(self):
        candidate = self.plan()
        candidate['symbols'].update(self.declared())
        plan_synthesizer.synthesize_id_formalization(candidate, self.elements())
        self.assertEqual(normalize_truth_binding(candidate, self.elements()),
                         (candidate, []))

    def test_malformed_inputs_are_left_for_the_validator(self):
        for candidate, elements in ((None, self.elements()), ({}, self.elements()),
                                    (self.plan(), None), (self.plan(), {}),
                                    ({'symbols': {}}, self.elements())):
            with self.subTest(candidate=candidate, elements=elements):
                self.assertEqual(normalize_truth_binding(candidate, elements),
                                 (candidate, []))

    # ---- refusals: the ORIGINAL error must survive, unfixed ----

    def _refuse(self, mutate, added, expected):
        """Mutate the plan, normalize, and prove the defect is still reported."""
        candidate = self.plan()
        mutate(candidate)
        declared_before = set(candidate['symbols'])
        fixed, _ = normalize_truth_binding(candidate, self.elements())
        self.assertNotIn(added, set(fixed['symbols']) - declared_before)
        with self.assertRaisesRegex(ValueError, expected):
            plan_synthesizer.synthesize_id_formalization(fixed, self.elements())

    def test_a_paraphrased_name_is_refused(self):
        """``separator_immutable`` is not the source's own ID: it would be invented."""
        def rename(plan):
            plan['precondition_terms'][0]['predicate']['symbol'] = \
                'separator_immutable'
        self._refuse(rename, 'separator_immutable', 'invalid truth binding')

    def test_a_non_bool_value_is_refused(self):
        def number(plan):
            plan['precondition_terms'][0]['predicate']['value'] = 1
        self._refuse(number, 'separator_cached_once', 'invalid truth binding')

    def test_extra_predicate_keys_are_refused(self):
        def extra(plan):
            plan['precondition_terms'][0]['predicate']['note'] = 'because'
        self._refuse(extra, 'separator_cached_once', 'invalid truth binding')

    def test_an_integer_used_as_a_flag_is_refused(self):
        """Sub-case A: the prompt already prescribes the occurrence symbol."""
        def redeclare(plan):
            plan['symbols']['separator_cached_once'] = {
                'sort': 'int', 'unit': 'dimensionless', 'meaning': 'cached id',
                'checkpoint': 'cached_id', 'entity_ids': ['contract'],
                'source_ids': ['p_separator_cached_once']}
        candidate = self.plan()
        redeclare(candidate)
        fixed, _ = normalize_truth_binding(candidate, self.elements())
        self.assertEqual(fixed['symbols']['separator_cached_once'],
                         candidate['symbols']['separator_cached_once'],
                         'an integer declaration must be left exactly as written')
        with self.assertRaisesRegex(ValueError,
                                    'truth binding requires bool symbol'):
            plan_synthesizer.synthesize_id_formalization(fixed, self.elements())

    def test_a_source_without_an_entity_binding_is_refused(self):
        """Nothing is invented -- an unbound declaration would be."""
        elements = self.elements()
        elements['statements'][0]['entity_ids'] = []
        declared_before = set(self.plan()['symbols'])
        fixed, changes = normalize_truth_binding(self.plan(), elements)
        self.assertNotIn('separator_cached_once',
                         set(fixed['symbols']) - declared_before)
        # The other term is well formed, so it is still declared.
        self.assertEqual([change['symbol'] for change in changes],
                         ['chain_id_changes'])

    # ---- the cap is duplicated, so pin it to the validator ----

    def test_the_cap_constant_matches_the_schema(self):
        def with_symbols(count):
            plan = self.plan()
            plan['symbols'].update(self.declared())
            fillers = count - len(plan['symbols'])
            self.assertGreaterEqual(fillers, 0)
            for index in range(fillers):
                plan['symbols'][f'filler_{index}'] = self._bool_symbol(
                    'unused', f'filler_{index}', ['p_chain_id_changes'])
            self.assertEqual(len(plan['symbols']), count)
            return plan

        plan_synthesizer.synthesize_id_formalization(
            with_symbols(MAX_PLAN_SYMBOLS), self.elements())
        with self.assertRaisesRegex(ValueError, 'invalid plan symbols'):
            plan_synthesizer.synthesize_id_formalization(
                with_symbols(MAX_PLAN_SYMBOLS + 1), self.elements())

    def test_the_fixer_refuses_to_exceed_the_cap(self):
        """Better to leave the original error than trade it for another one."""
        plan = self.plan()
        self.assertEqual(sorted(plan['symbols']), ['signature_valid'])
        while len(plan['symbols']) < MAX_PLAN_SYMBOLS - 1:
            index = len(plan['symbols'])
            plan['symbols'][f'filler_{index}'] = self._bool_symbol(
                'unused', f'filler_{index}', ['p_chain_id_changes'])
        # MAX_PLAN_SYMBOLS - 1 declared + the 2 the fix would add > the cap.
        self.assertEqual(len(plan['symbols']), MAX_PLAN_SYMBOLS - 1)
        fixed, changes = normalize_truth_binding(plan, self.elements())
        self.assertEqual(changes, [])
        self.assertEqual(fixed, plan)


class TruthBindingNormalizationWiringTest(unittest.TestCase):
    """Wiring guard: without this, deleting the call keeps every other test green.

    The fixer's own tests above would still pass if ``request_formalization``
    stopped calling it, which is exactly the gap this class closes.
    """

    def test_a_plan_naming_an_undeclared_symbol_is_normalized(self):
        elements = TruthBindingNormalizationTest.elements()
        raw = TruthBindingNormalizationTest.plan()
        seen = {}

        def fake(_payload, call_dir, _model, _prompt, **_kwargs):
            seen['raw'] = list((call_dir / 'model-claim.json').parent.glob('*'))
            return copy.deepcopy(raw)

        with tempfile.TemporaryDirectory() as dirname:
            out = Path(dirname)
            candidate, formal, _review = p.request_formalization(
                '{}', 'PROMPT', 'deepseek-flash', out, 0, True, elements,
                extract_fn=fake, attempts=[])
            self.assertIn('separator_cached_once', candidate['symbols'],
                          'the normalization never ran')
            log = json.loads(
                (out / 'neural-formalization' / 'normalization-log.json')
                .read_text())
            self.assertEqual(log['mode'], NORMALIZE)
            self.assertEqual(log['stage'], 'formalization')
            self.assertEqual([c['symbol'] for c in log['changes']],
                             ['separator_cached_once', 'chain_id_changes'])
            attempts = json.loads(
                (out / 'formalization-attempts.json').read_text())
            self.assertEqual(attempts[0]['normalizations'], log['changes'])
            # The persisted plan is the normalized one, which is what makes the
            # zero-call replay in ``cli/batch_verify.py`` reproduce this run.
            self.assertIsNotNone(formal)


if __name__ == '__main__': unittest.main()
