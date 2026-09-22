"""Offline security and transport tests; never calls DeepSeek."""
import io
import http.client
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

import report_only as report
import semantic_pipeline as pipeline


class FakeOpener:
    def __init__(self, response):
        self.response = response
        self.request = None
        self.timeout = None

    def open(self, request, timeout):
        self.request, self.timeout = request, timeout
        return io.BytesIO(json.dumps(self.response).encode())


class DeepSeekDirectTests(unittest.TestCase):
    def make_key(self, root, value='sk-test-only'):
        path = root / 'stage2_deepseek.local.env'
        path.write_text('DEEPSEEK_API_KEY=' + value + '\n')
        os.chmod(path, 0o600)
        return path

    def test_private_key_required(self):
        with tempfile.TemporaryDirectory() as dirname:
            root = Path(dirname)
            key = self.make_key(root, '')
            with self.assertRaisesRegex(RuntimeError, 'missing or malformed'):
                report.load_deepseek_key(key)
            self.make_key(root)
            os.chmod(key, 0o644)
            with self.assertRaisesRegex(RuntimeError, 'chmod 600'):
                report.load_deepseek_key(key)

    def test_json_request_and_sanitized_artifacts(self):
        with tempfile.TemporaryDirectory() as dirname:
            root = Path(dirname)
            key = self.make_key(root)
            opener = FakeOpener({
                'model': 'deepseek-flash', 'choices': [{
                    'finish_reason': 'stop',
                    'message': {'content': '{"ok":true}'}}],
                'usage': {'prompt_tokens': 10, 'completion_tokens': 5},
            })
            result = report.extract_deepseek('report fragment', root,
                                             'deepseek-flash', 'Return JSON:',
                                             key_path=key, opener=opener)
            self.assertEqual(result, {'ok': True})
            self.assertEqual(opener.request.full_url, report.DEEPSEEK_CHAT_URL)
            self.assertEqual(opener.timeout, 240)
            self.assertEqual(opener.request.get_header('Authorization'),
                             'Bearer sk-test-only')
            sent = json.loads(opener.request.data)
            self.assertEqual(sent['messages'][1]['content'], 'report fragment')
            self.assertEqual(sent['response_format'], {'type': 'json_object'})
            self.assertEqual(sent['thinking'], {'type': 'disabled'})
            for name in ('model-response.txt', 'model-usage.json', 'model-claim.json'):
                self.assertNotIn('sk-test-only', (root / name).read_text())

    def test_http_error_does_not_save_secret_or_provider_body(self):
        with tempfile.TemporaryDirectory() as dirname:
            root = Path(dirname)
            key = self.make_key(root)

            class ErrorOpener:
                def open(self, *_args, **_kwargs):
                    raise HTTPError(report.DEEPSEEK_CHAT_URL, 401, 'unauthorized',
                                    {}, io.BytesIO(b'SECRET SERVER BODY'))

            with self.assertRaisesRegex(RuntimeError, 'HTTP 401'):
                report.extract_deepseek('text', root, 'deepseek-flash', 'JSON:',
                                        key_path=key, opener=ErrorOpener())
            diagnostic = (root / 'model-runtime-diagnostic.json').read_text()
            self.assertNotIn('SECRET', diagnostic)
            self.assertNotIn('sk-test-only', diagnostic)
            self.assertEqual(json.loads(diagnostic)['http_status'], 401)

    def test_truncated_generation_not_accepted(self):
        with tempfile.TemporaryDirectory() as dirname:
            root = Path(dirname)
            key = self.make_key(root)
            opener = FakeOpener({'choices': [{
                'finish_reason': 'length', 'message': {'content': '{"partial":'}}]})
            with self.assertRaisesRegex(RuntimeError, 'did not finish normally'):
                report.extract_deepseek('text', root, 'deepseek-flash', 'JSON:',
                                        key_path=key, opener=opener)
            self.assertFalse((root / 'model-claim.json').exists())

    def test_interrupted_http_body_is_sanitized_and_retryable(self):
        with tempfile.TemporaryDirectory() as dirname:
            root = Path(dirname)
            key = self.make_key(root)

            class InterruptedBody(io.BytesIO):
                def read(self, *_args, **_kwargs):
                    raise http.client.IncompleteRead(b'partial secret response')

            class InterruptedOpener:
                def open(self, *_args, **_kwargs):
                    return InterruptedBody()

            with self.assertRaisesRegex(report.TransientModelError,
                                        'response interrupted'):
                report.extract_deepseek('text', root, 'deepseek-flash', 'JSON:',
                                        key_path=key, opener=InterruptedOpener())
            diagnostic = json.loads((root / 'model-runtime-diagnostic.json').read_text())
            self.assertEqual(diagnostic['category'], 'incomplete_response')
            self.assertNotIn('partial secret response', json.dumps(diagnostic))

    def test_pipeline_explicit_provider_dispatch_is_offline_testable(self):
        source = Path(__file__).resolve().parents[1] / 'evaluation/fresh_holdout_01/runs/' \
            'Brix_Money_qy7NXr77sDh__cSNXN84Wruw__JeqwSynbkaB'
        saved = json.loads((source / 'elements-ids.json').read_text())
        with tempfile.TemporaryDirectory() as dirname:
            out = Path(dirname) / 'run'
            argv = ['semantic_pipeline.py', '--report',
                    str(source / 'extraction-input.txt'), '--extract',
                    '--elements-only', '--provider', 'deepseek',
                    '--prompt-version', 'semantic-v3.12', '--allow-report-upload',
                    '--output', str(out)]
            def fake_deepseek(payload, output, _model, _prompt):
                if output.name == 'neural-input-screen':
                    ids = [row['id'] for row in json.loads(payload)['fragments']]
                    names = ('affected_subject', 'trigger_or_action', 'direct_effect',
                             'safety_relation_basis')
                    return {'schema_version': 'report-readiness/1', 'decision': 'ready',
                            'dimensions': {name: {'status': 'present',
                                                  'evidence_ids': [ids[min(i, len(ids) - 1)]],
                                                  'reason': 'supported'}
                                           for i, name in enumerate(names)},
                            'missing_dimensions': [], 'summary': 'sufficient'}
                return saved

            with patch('sys.argv', argv), patch.object(pipeline.r, 'load_deepseek_key',
                    return_value='test-key'), patch.object(pipeline.r, 'extract_deepseek',
                    side_effect=fake_deepseek) as direct, patch.object(pipeline.r, 'extract') as indirect:
                status = pipeline.main()
            self.assertEqual(status, 0)
            self.assertEqual(direct.call_count, 2)
            indirect.assert_not_called()
            self.assertEqual(json.loads((out / 'provenance.json').read_text())['model_provider'],
                             'deepseek')

    def test_insufficient_report_stops_before_piv_extraction(self):
        source = Path(__file__).resolve().parents[1] / 'evaluation/fresh_holdout_01/runs/' \
            'Brix_Money_qy7NXr77sDh__cSNXN84Wruw__JeqwSynbkaB/extraction-input.txt'
        with tempfile.TemporaryDirectory() as dirname:
            out = Path(dirname) / 'run'
            argv = ['semantic_pipeline.py', '--report', str(source), '--extract',
                    '--provider', 'deepseek', '--prompt-version', 'semantic-v3.12',
                    '--allow-report-upload', '--output', str(out)]

            def insufficient(payload, output, _model, _prompt):
                ids = [row['id'] for row in json.loads(payload)['fragments']]
                return {'schema_version': 'report-readiness/1', 'decision': 'insufficient',
                        'dimensions': {
                            'affected_subject': {'status': 'present', 'evidence_ids': [ids[0]],
                                                 'reason': 'named'},
                            'trigger_or_action': {'status': 'present', 'evidence_ids': [ids[0]],
                                                  'reason': 'named'},
                            'direct_effect': {'status': 'uncertain', 'evidence_ids': [ids[-1]],
                                              'reason': 'only generic loss'},
                            'safety_relation_basis': {'status': 'missing', 'evidence_ids': [],
                                                      'reason': 'no relation'},
                        },
                        'missing_dimensions': ['direct_effect', 'safety_relation_basis'],
                        'summary': 'insufficient'}

            with patch('sys.argv', argv), patch.object(pipeline.r, 'load_deepseek_key',
                    return_value='test-key'), patch.object(pipeline.r, 'extract_deepseek',
                    side_effect=insufficient) as direct:
                self.assertEqual(pipeline.main(), 2)
            direct.assert_called_once()
            self.assertFalse((out / 'elements.json').exists())
            status = json.loads((out / 'status.json').read_text())
            self.assertEqual(status['acceptance_status'], 'excluded_before_extraction')


if __name__ == '__main__':
    unittest.main()
