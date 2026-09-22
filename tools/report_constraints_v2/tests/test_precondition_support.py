"""Offline schema and provenance checks for optional P-support audit."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import preconditions as audit
from preconditions import (PROMPT, audited_triage, make_payload,
                                        validate_response)


class PreconditionSupportTests(unittest.TestCase):
    def setUp(self):
        self.elements = {'schema_version': 'report-elements/2', 'statements': [
            {'id': 'p_actor', 'kind': 'precondition', 'text': 'Anyone may call.',
             'evidence_ids': ['e1']},
            {'id': 'i_loss', 'kind': 'impact', 'text': 'Funds lost.',
             'evidence_ids': ['e2']}],
        }
        self.catalog = {'source_sha256': 'a' * 64, 'fragments': [
            {'id': 'e1', 'text': 'A function exists.'},
            {'id': 'e2', 'text': 'Funds were lost.'}]}

    def test_only_preconditions_and_cited_text_are_sent(self):
        payload = make_payload(self.elements, self.catalog)
        self.assertEqual(len(payload['items']), 1)
        self.assertEqual(payload['items'][0]['evidence'][0]['text'], 'A function exists.')
        self.assertEqual(payload['scenario_context'][0]['text'], 'Funds lost.')
        self.assertNotIn('Funds were lost.', str(payload))

    def test_assumptions_cannot_bypass_p_audit(self):
        self.elements['statements'].append({
            'id': 'a_input', 'kind': 'assumption', 'text': 'Input is nonzero.',
            'evidence_ids': ['e1']})
        payload = make_payload(self.elements, self.catalog)
        self.assertEqual([item['statement_id'] for item in payload['items']],
                         ['p_actor', 'a_input'])

    def test_unknown_evidence_or_incomplete_response_rejected(self):
        payload = make_payload(self.elements, self.catalog)
        with self.assertRaises(ValueError):
            validate_response({'schema_version': 'precondition-support/5',
                               'items': []}, payload)
        self.elements['statements'][0]['evidence_ids'] = ['invented']
        with self.assertRaises(ValueError):
            make_payload(self.elements, self.catalog)

    def test_empty_precondition_set_rejected_before_model_call(self):
        self.elements['statements'] = self.elements['statements'][1:]
        with self.assertRaisesRegex(ValueError, 'at least one P input'):
            make_payload(self.elements, self.catalog)

    def test_support_result_never_becomes_gold(self):
        payload = make_payload(self.elements, self.catalog)
        result = validate_response({'schema_version': 'precondition-support/5',
                                    'items': [{'statement_id': 'p_actor',
                                               'evidence_verdict': 'unsupported',
                                               'role_verdict': 'before_condition',
                                               'reason': 'Snippet does not state access.'}]}, payload)
        self.assertEqual(result['needs_review_ids'], ['p_actor'])
        self.assertFalse(result['is_independent_gold'])

    def test_supported_bad_result_in_p_still_needs_review(self):
        payload = make_payload(self.elements, self.catalog)
        result = validate_response({'schema_version': 'precondition-support/5',
                                    'items': [{'statement_id': 'p_actor',
                                               'evidence_verdict': 'supported',
                                               'role_verdict': 'contains_action_or_result',
                                               'reason': 'Text is sourced but describes the bad result.'}]},
                                   payload)
        self.assertEqual(result['needs_review_ids'], ['p_actor'])

    def test_prompt_distinguishes_conditional_trigger_from_actual_occurrence(self):
        self.assertIn('P is an ANTECEDENT', PROMPT)
        self.assertIn('DOES support X as a', PROMPT)
        self.assertIn('extra historical claim', PROMPT)

    def test_audit_only_downroutes_candidate(self):
        review = {'schema_version': 'precondition-support-review/5',
                  'needs_review_ids': ['p_mixed']}
        candidate = {'schema_version': 'stage2-auto-triage/1',
                     'route': 'candidate', 'reasons': []}
        result = audited_triage(candidate, review)
        self.assertEqual(result['route'], 'review')
        self.assertEqual(candidate['route'], 'candidate')
        self.assertFalse(result['semantic_truth_verified'])
        review_route = audited_triage({**candidate, 'route': 'review'}, review)
        self.assertEqual(review_route['route'], 'review')
        self.assertEqual(audited_triage(candidate, {**review, 'needs_review_ids': []})['route'],
                         'candidate')

    def test_empty_model_response_writes_failure_status(self):
        with tempfile.TemporaryDirectory() as root:
            run_dir = Path(root) / 'run'
            run_dir.mkdir()
            (run_dir / 'elements-ids.json').write_text(json.dumps(self.elements))
            (run_dir / 'evidence-catalog.json').write_text(json.dumps(self.catalog))
            output = Path(root) / 'audit'
            argv = ['preconditions.py', '--run-dir', str(run_dir),
                    '--output', str(output), '--allow-report-upload']
            with patch('sys.argv', argv), patch.object(audit.r, 'extract',
                                                      side_effect=ValueError('empty response')):
                with self.assertRaisesRegex(ValueError, 'empty response'):
                    audit.audit_main()
            status = json.loads((output / 'status.json').read_text())
            self.assertEqual(status['status'], 'failed')
            self.assertFalse(status['is_independent_gold'])


if __name__ == '__main__':
    unittest.main()
