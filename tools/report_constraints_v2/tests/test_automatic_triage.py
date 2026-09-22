"""Offline checks for bounded formal-step retry and transparent routing."""
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from review import attach_review, from_bundle, from_failure
from semantic_pipeline import formal_retry_hint, request_formalization


class FormalRetryTests(unittest.TestCase):
    def test_empty_response_retries_once_and_preserves_attempts(self):
        calls = []

        def fake_extract(payload, folder, model, prompt):
            calls.append(folder.name)
            if len(calls) == 1:
                raise json.JSONDecodeError('empty', '', 0)
            return {'schema_version': 'test'}

        with tempfile.TemporaryDirectory() as work:
            root = Path(work)
            candidate, formal, review = request_formalization(
                '{}', 'PROMPT', 'test-model', root, 1, False, None,
                extract_fn=fake_extract)
            self.assertEqual(candidate, formal)
            self.assertIsNone(review)
            self.assertEqual(calls, ['neural-formalization', 'neural-formalization-retry-1'])
            attempts = json.loads((root / 'formalization-attempts.json').read_text())
            self.assertEqual([x['outcome'] for x in attempts],
                             ['retryable_failure', 'accepted_for_validation'])

    def test_invalid_plan_retries_without_local_repair(self):
        with tempfile.TemporaryDirectory() as work:
            root = Path(work)
            attempts = []
            sent_prompts = []

            def fake_extract(payload, folder, model, prompt):
                sent_prompts.append(prompt)
                return {'raw_plan': True}

            with patch('semantic_pipeline.synthesize_id_formalization',
                       side_effect=[ValueError('missing plan quantity unit'), {'valid': True}]):
                _, formal, _ = request_formalization(
                    '{}', 'PROMPT', 'test-model', root, 1, True, {},
                    extract_fn=fake_extract, attempts=attempts)
            self.assertEqual(formal, {'valid': True})
            self.assertEqual(len(attempts), 2)
            self.assertEqual(attempts[0]['error'], 'missing plan quantity unit')
            self.assertNotIn('dimensionless', sent_prompts[0])
            self.assertIn('dimensionless', sent_prompts[1])

    def test_two_retries_are_bounded_and_each_attempt_is_preserved(self):
        calls = []

        def fake_extract(_payload, folder, _model, _prompt):
            calls.append(folder.name)
            return {'raw_plan': True}

        with tempfile.TemporaryDirectory() as work:
            root = Path(work)
            with patch('semantic_pipeline.synthesize_id_formalization',
                       side_effect=[ValueError('invalid truth binding'),
                                    ValueError('unknown comparison symbol'),
                                    {'valid': True}]):
                _, formal, _ = request_formalization(
                    '{}', 'PROMPT', 'test-model', root, 2, True, {},
                    extract_fn=fake_extract)
            self.assertEqual(formal, {'valid': True})
            self.assertEqual(calls, ['neural-formalization',
                                     'neural-formalization-retry-1',
                                     'neural-formalization-retry-2'])
            attempts = json.loads((root / 'formalization-attempts.json').read_text())
            self.assertEqual([row['outcome'] for row in attempts],
                             ['retryable_failure', 'retryable_failure',
                              'accepted_for_validation'])

    def test_timeout_without_retry_is_recorded(self):
        def timeout(*_):
            raise subprocess.TimeoutExpired('model', 240)

        with tempfile.TemporaryDirectory() as work:
            root = Path(work)
            with self.assertRaises(subprocess.TimeoutExpired):
                request_formalization('{}', 'PROMPT', 'test-model', root, 0,
                                      False, None, extract_fn=timeout)
            attempts = json.loads((root / 'formalization-attempts.json').read_text())
            self.assertEqual(attempts[0]['error'], 'model timeout')

    def test_model_error_is_not_retried(self):
        calls = []

        def model_error(*_):
            calls.append(1)
            raise RuntimeError('tool use/model error; rejected')

        with tempfile.TemporaryDirectory() as work:
            root = Path(work)
            with self.assertRaises(RuntimeError):
                request_formalization('{}', 'PROMPT', 'test-model', root, 1,
                                      False, None, extract_fn=model_error)
            self.assertEqual(len(calls), 1)
            attempts = json.loads((root / 'formalization-attempts.json').read_text())
            self.assertEqual(attempts[0]['outcome'], 'non_retryable_failure')

    def test_schema_feedback_is_fixed_and_nonsemantic(self):
        self.assertIn('top-level "kind"', formal_retry_hint(ValueError('unknown synthesis pattern')))
        self.assertIn('lowercase snake_case', formal_retry_hint(ValueError('invalid plan symbol')))
        self.assertIn('ONLY a declared sort:"bool"',
                      formal_retry_hint(ValueError('truth binding requires bool symbol')))
        self.assertIn('must be declared in symbols',
                      formal_retry_hint(ValueError('unknown predicate symbol')))
        self.assertIn('state_correspondence uses relation_obligation',
                      formal_retry_hint(ValueError('relation class and pattern mismatch')))
        self.assertIn('most directly negates', formal_retry_hint(
            ValueError('core relation observables lack intent/impact grounding')))
        self.assertIn('x==x', formal_retry_hint(
            ValueError('trivial self-comparison predicate')))
        secret = 'USER_REPORT_SECRET'
        self.assertNotIn(secret, formal_retry_hint(ValueError(secret)))


class TriageTests(unittest.TestCase):
    @staticmethod
    def complete_review_bundle():
        return {'core_formalization_status': 'formalized_candidate',
                'acceptance_status': 'needs_review',
                'report_warnings': ['secondary impact deferred'],
                'claims': [{'id': 'core_claim', 'review_reasons': ['scope needs review'],
                            'properties': {key: {'expression': {'var': key}}
                                           for key in ('preconditions', 'safety', 'effects')},
                            'semantic_relationship': {'queries': {
                                'P_and_V': 'sat', 'P_and_V_and_not_I': 'sat',
                                'P_and_V_and_I': 'unsat'}}}]}

    def test_candidate_is_not_semantic_truth(self):
        result = from_bundle({'core_formalization_status': 'formalized_candidate',
                              'acceptance_status': 'candidate_checks_passed',
                              'report_warnings': [], 'claims': []})
        self.assertEqual(result['route'], 'candidate')
        self.assertFalse(result['semantic_truth_verified'])

    def test_review_and_abstain_are_distinct(self):
        base = {'report_warnings': ['ambiguous scope'], 'claims': []}
        self.assertEqual(from_bundle({**base, 'core_formalization_status': 'formalized_candidate',
                                      'acceptance_status': 'needs_review'})['route'], 'review')
        self.assertEqual(from_bundle({**base, 'core_formalization_status': 'partial',
                                      'acceptance_status': 'needs_review'})['route'], 'abstain')
        self.assertEqual(from_failure({'error_type': 'TimeoutExpired',
                                       'error': 'model timeout'})['route'], 'pipeline_failure')

    def test_a_rejected_bundle_abstains(self):
        """A contradiction must not be routed as a review item."""
        bundle = {'core_formalization_status': 'formalized_candidate',
                  'acceptance_status': 'rejected', 'report_warnings': [],
                  'claims': [{'id': 'core_claim', 'review_reasons': [],
                              'semantic_relationship': {'queries': {
                                  'P_and_V': 'sat', 'P_and_V_and_not_I': 'sat',
                                  'P_and_V_and_I': 'unsat'}}}]}
        result = from_bundle(bundle)
        self.assertEqual(result['route'], 'abstain')
        self.assertFalse(result['stage2_can_continue'])

    def test_infeasible_core_abstains_even_when_structurally_formalized(self):
        bundle = {'core_formalization_status': 'formalized_candidate',
                  'acceptance_status': 'needs_review', 'report_warnings': [],
                  'claims': [{'id': 'core_claim', 'review_reasons': [],
                              'semantic_relationship': {'queries': {'P_and_V': 'unsat'}}}]}
        result = from_bundle(bundle)
        self.assertEqual(result['route'], 'abstain')
        self.assertIn('P AND V is not feasible', result['reasons'][-1])

    def test_review_can_continue_with_explicit_warnings(self):
        result = from_bundle(self.complete_review_bundle())
        self.assertEqual(result['route'], 'review')
        self.assertTrue(result['stage2_can_continue'])
        self.assertIn('secondary impact deferred', result['reasons'])
        self.assertFalse(result['semantic_truth_verified'])

    def test_missing_core_or_blocking_unresolved_cannot_continue(self):
        bundle = self.complete_review_bundle()
        bundle['claims'][0]['properties']['effects']['expression'] = None
        self.assertFalse(from_bundle(bundle)['stage2_can_continue'])
        bundle = self.complete_review_bundle()
        bundle['claims'][0]['semantic_relationship']['queries']['P_and_V_and_I'] = 'sat'
        self.assertFalse(from_bundle(bundle)['stage2_can_continue'])
        bundle = self.complete_review_bundle()
        self.assertFalse(from_bundle(bundle, {'blocks_candidate_acceptance': True})[
            'stage2_can_continue'])
        bundle['provenance'] = {'prompt_version': 'semantic-v3.12'}
        bundle['claims'][0]['unresolved'] = ['[unsupported_relation] core relation absent']
        self.assertFalse(from_bundle(bundle)['stage2_can_continue'])



class ObservabilityReviewGateTest(unittest.TestCase):
    """The review gate may escalate severity, never soften a rejection.

    ``attach_review`` used to overwrite ``acceptance_status`` with
    ``needs_review`` whenever the observability review warned, which would have
    talked a bundle the compiler rejected for a contradictory P back up to a
    review item -- exactly the tier the contradiction rule exists to escape.
    """

    @staticmethod
    def _isolated_safety_bundle():
        """A bundle whose safety side uses a bool nothing else defines."""
        formal = {'symbols': {'guard': {'sort': 'bool'},
                              'reverted': {'sort': 'bool'},
                              'extra': {'sort': 'bool'}},
                  'claims': [{'id': 'core_claim', 'properties': {
                      'preconditions': {'expression': {'var': 'guard'}},
                      'safety': {'expression': {'op': 'and', 'args': [
                          {'op': 'not', 'args': [{'var': 'reverted'}]},
                          {'var': 'extra'}]}},
                      'effects': {'expression': {'var': 'reverted'}}}}]}
        bundle = {'acceptance_status': 'rejected',
                  'claims': [{'id': 'core_claim',
                              'formalization_status': 'formalized_candidate',
                              'review_reasons': [],
                              'semantic_relationship': {'queries': {}}}]}
        return bundle, formal

    def test_a_rejection_survives_a_review_warning(self):
        bundle, formal = self._isolated_safety_bundle()
        result = attach_review(bundle, formal)
        self.assertEqual(result['review_status'], 'needs_review')
        self.assertEqual(bundle['acceptance_status'], 'rejected')

    def test_a_review_warning_still_escalates_a_clean_bundle(self):
        bundle, formal = self._isolated_safety_bundle()
        bundle['acceptance_status'] = 'candidate_checks_passed'
        result = attach_review(bundle, formal)
        self.assertEqual(result['review_status'], 'needs_review')
        self.assertEqual(bundle['acceptance_status'], 'needs_review')

if __name__ == '__main__':
    unittest.main()
