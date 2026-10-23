"""Offline security and transport tests; never calls DeepSeek."""
import io
import http.client
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from urllib import request as urlrequest
from urllib.error import HTTPError

from lib import deepseek
from lib import report_only as report
from cli import semantic_pipeline as pipeline
from cli.batch_verify import verify as verify_semantic


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
                deepseek.load_deepseek_key(key)
            self.make_key(root)
            os.chmod(key, 0o644)
            with self.assertRaisesRegex(RuntimeError, 'chmod 600'):
                deepseek.load_deepseek_key(key)

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
            result = deepseek.extract_deepseek('report fragment', root,
                                             'deepseek-flash', 'Return JSON:',
                                             key_path=key, opener=opener)
            self.assertEqual(result, {'ok': True})
            self.assertEqual(opener.request.full_url, deepseek.DEEPSEEK_CHAT_URL)
            self.assertEqual(opener.timeout, 240)
            self.assertEqual(opener.request.get_header('Authorization'),
                             'Bearer sk-test-only')
            sent = json.loads(opener.request.data)
            self.assertEqual(sent['messages'][1]['content'], 'report fragment')
            self.assertEqual(sent['response_format'], {'type': 'json_object'})
            self.assertEqual(sent['thinking'], {'type': 'disabled'})
            self.assertEqual(sent['temperature'], deepseek.DEEPSEEK_TEMPERATURE)
            self.assertEqual(sent['max_tokens'], deepseek.DEEPSEEK_MAX_TOKENS)
            for name in ('model-response.txt', 'model-usage.json', 'model-claim.json'):
                self.assertNotIn('sk-test-only', (root / name).read_text())

    def test_http_error_does_not_save_secret_or_provider_body(self):
        with tempfile.TemporaryDirectory() as dirname:
            root = Path(dirname)
            key = self.make_key(root)

            class ErrorOpener:
                def open(self, *_args, **_kwargs):
                    raise HTTPError(deepseek.DEEPSEEK_CHAT_URL, 401, 'unauthorized',
                                    {}, io.BytesIO(b'SECRET SERVER BODY'))

            with self.assertRaisesRegex(RuntimeError, 'HTTP 401'):
                deepseek.extract_deepseek('text', root, 'deepseek-flash', 'JSON:',
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
                deepseek.extract_deepseek('text', root, 'deepseek-flash', 'JSON:',
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

            with self.assertRaisesRegex(deepseek.TransientModelError,
                                        'response interrupted'):
                deepseek.extract_deepseek('text', root, 'deepseek-flash', 'JSON:',
                                        key_path=key, opener=InterruptedOpener())
            diagnostic = json.loads((root / 'model-runtime-diagnostic.json').read_text())
            self.assertEqual(diagnostic['category'], 'incomplete_response')
            self.assertNotIn('partial secret response', json.dumps(diagnostic))

    def test_gateway_http_status_is_retryable(self):
        # 2026-10-15 blind-batch_08 attribution: DeepSeek answered 503
        # during an outage window; the hard RuntimeError killed runs whose
        # candidates were fine.  Gateway statuses stay retryable; 401 stays
        # fatal (the test above pins that one).
        with tempfile.TemporaryDirectory() as dirname:
            root = Path(dirname)
            key = self.make_key(root)

            class UnavailableOpener:
                def open(self, *_args, **_kwargs):
                    raise HTTPError(deepseek.DEEPSEEK_CHAT_URL, 503,
                                    'service unavailable', {}, io.BytesIO(b''))

            with self.assertRaisesRegex(deepseek.TransientModelError, 'HTTP 503'):
                deepseek.extract_deepseek('text', root, 'deepseek-flash', 'JSON:',
                                        key_path=key, opener=UnavailableOpener())

    def test_malformed_envelope_is_retryable(self):
        # 2026-10-15 blind-batch_08 attribution: the endpoint also answered
        # valid-JSON-but-wrong-shape bodies (no usable choices) during the
        # same outage window; a malformed envelope is server-side
        # degradation, so it rides the same retryable class as an
        # interrupted body instead of failing the whole run.
        with tempfile.TemporaryDirectory() as dirname:
            root = Path(dirname)
            key = self.make_key(root)
            opener = FakeOpener({'error': {'message': 'server overloaded'}})
            with self.assertRaisesRegex(deepseek.TransientModelError,
                                        'envelope invalid'):
                deepseek.extract_deepseek('text', root, 'deepseek-flash', 'JSON:',
                                        key_path=key, opener=opener)
            self.assertFalse((root / 'model-claim.json').exists())

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
            def fake_deepseek(payload, output, _model, _prompt, **_kwargs):
                # semantic_pipeline binds proxy= via functools.partial,
                # so a stand-in for extract_deepseek must absorb it.
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

            with patch('sys.argv', argv), patch.object(pipeline, 'load_deepseek_key',
                    return_value='test-key'), patch.object(pipeline, 'extract_deepseek',
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

            def insufficient(payload, output, _model, _prompt, **_kwargs):
                # semantic_pipeline binds proxy= via functools.partial,
                # so a stand-in for extract_deepseek must absorb it.
                ids = [row['id'] for row in json.loads(payload)['fragments']]
                result = {'schema_version': 'report-readiness/1',
                        'decision': 'insufficient', 'dimensions': {
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
                (output / 'model-claim.json').write_text(json.dumps(result))
                return result

            with patch('sys.argv', argv), patch.object(pipeline, 'load_deepseek_key',
                    return_value='test-key'), patch.object(pipeline, 'extract_deepseek',
                    side_effect=insufficient) as direct:
                self.assertEqual(pipeline.main(), 2)
            direct.assert_called_once()
            self.assertFalse((out / 'elements.json').exists())
            status = json.loads((out / 'status.json').read_text())
            self.assertEqual(status['acceptance_status'], 'excluded_before_extraction')
            self.assertTrue(verify_semantic(out)['offline_verified'])


class DeepSeekProxyPolicyTest(unittest.TestCase):
    """The transport switch must really control whether ambient proxies apply.

    Regression: the environment carried HTTPS_PROXY pointing at a port that
    closes HTTP CONNECT.  urllib honoured it implicitly and every call died with
    the opaque message "DeepSeek network failure; details not saved".
    """

    def make_key(self, root, value='sk-test-only'):
        path = root / 'stage2_deepseek.local.env'
        path.write_text('DEEPSEEK_API_KEY=' + value + '\n')
        path.chmod(0o600)
        return path

    def _live_handlers(self, opener):
        return [h for h in opener.handlers
                if isinstance(h, urlrequest.ProxyHandler) and h.proxies]

    def test_direct_ignores_ambient_proxy_variables(self):
        with patch.dict(os.environ, {'https_proxy': 'http://127.0.0.1:9'}, clear=False):
            self.assertEqual(self._live_handlers(deepseek._deepseek_opener('direct')), [])

    def test_environment_honours_ambient_proxy_variables(self):
        """Negative proof: if the switch were ignored this would also be empty."""
        with patch.dict(os.environ, {'https_proxy': 'http://127.0.0.1:9'}, clear=False):
            self.assertNotEqual(
                self._live_handlers(deepseek._deepseek_opener('environment')), [])

    def test_explicit_url_overrides_the_environment(self):
        with patch.dict(os.environ, {'https_proxy': 'http://127.0.0.1:9'}, clear=False):
            live = self._live_handlers(deepseek._deepseek_opener('http://proxy.internal:3128'))
            self.assertEqual(len(live), 1)
            self.assertEqual(live[0].proxies['https'], 'http://proxy.internal:3128')

    def test_socks5_is_rejected_up_front(self):
        """urllib cannot speak SOCKS; failing here beats an opaque network error."""
        with self.assertRaisesRegex(ValueError, 'no SOCKS support'):
            deepseek.proxy_policy('socks5://127.0.0.1:7897')

    def test_recorded_endpoint_is_redacted(self):
        self.assertEqual(deepseek._redacted_proxy('http://u:p@proxy:3128'),
                         'http://proxy:3128')
        self.assertIsNone(deepseek.proxy_in_effect('direct'))

    def test_pipeline_binds_the_proxy_policy_through_to_the_transport(self):
        """The switch is only real if cli/semantic_pipeline.py binds it through.

        The fakes above absorb **kwargs, so deleting the binding would leave
        every other assertion green while the flag silently did nothing.
        """
        seen = []
        with tempfile.TemporaryDirectory() as dirname:
            root = Path(dirname)
            source = root / 'report.md'
            source.write_text('# Finding description\n\nA buffered fee body.\n')
            argv = ['semantic_pipeline.py', '--report', str(source), '--extract',
                    '--elements-only', '--provider', 'deepseek',
                    '--deepseek-proxy', 'direct', '--allow-report-upload',
                    '--output', str(root / 'run')]

            def fake(payload, output, _model, _prompt, **kwargs):
                seen.append(kwargs)
                raise RuntimeError('stop after the first transport call')

            with patch('sys.argv', argv), \
                    patch.object(pipeline, 'load_deepseek_key',
                                 return_value='test-key'), \
                    patch.object(pipeline, 'extract_deepseek', side_effect=fake):
                pipeline.main()
        self.assertTrue(seen, 'the transport was never reached')
        self.assertEqual(seen[0], {'proxy': 'direct'})

    def test_network_diagnostic_records_the_proxy_in_effect(self):
        with tempfile.TemporaryDirectory() as dirname:
            root = Path(dirname)
            key = self.make_key(root)

            class RefusingOpener:
                def open(self, *_args, **_kwargs):
                    raise OSError('connection refused')

            policy = 'http://proxy.example:3128'
            with self.assertRaisesRegex(RuntimeError, 'network failure'):
                deepseek.extract_deepseek('text', root, 'deepseek-flash', 'JSON:',
                                        key_path=key, opener=RefusingOpener(),
                                        proxy=policy)
            diagnostic = json.loads(
                (root / 'model-runtime-diagnostic.json').read_text())
            self.assertEqual(diagnostic['category'], 'network')
            self.assertEqual(diagnostic['proxy_in_effect'], policy)



class DeepSeekSingleSourceTests(unittest.TestCase):
    """lib/deepseek.py 是 DeepSeek 连接的唯一定义处。

    回归防线：若有人把连接函数或常量复制回 report_only / semantic_pipeline
    出现第二份副本，两处会悄悄分叉（一边改了另一边没改），直到某次调用
    用到过期副本才暴露。这里断言连接代码只在 lib/deepseek.py。
    """

    def test_report_only_no_longer_carries_deepseek_symbols(self):
        for name in ('extract_deepseek', 'load_deepseek_key', 'proxy_policy',
                     'proxy_in_effect', 'TransientModelError', 'DEEPSEEK_MODELS',
                     'DEEPSEEK_CHAT_URL', 'DEEPSEEK_KEY_FILE'):
            self.assertFalse(hasattr(report, name), name)

    def test_default_model_is_whitelisted(self):
        self.assertIn(deepseek.DEFAULT_DEEPSEEK_MODEL, deepseek.DEEPSEEK_MODELS)
        self.assertIn('deepseek-flash', deepseek.DEEPSEEK_MODELS)

    def test_pipeline_binds_the_deepseek_module_functions(self):
        self.assertIs(pipeline.extract_deepseek, deepseek.extract_deepseek)
        self.assertIs(pipeline.load_deepseek_key, deepseek.load_deepseek_key)
        self.assertIs(pipeline.proxy_policy, deepseek.proxy_policy)
        self.assertIs(pipeline.DEFAULT_DEEPSEEK_MODEL, deepseek.DEFAULT_DEEPSEEK_MODEL)
        self.assertTrue(callable(pipeline.configured_model))

    def test_decoding_is_deterministic_and_bounded(self):
        self.assertEqual(deepseek.DEEPSEEK_TEMPERATURE, 0)
        self.assertEqual(deepseek.DEEPSEEK_MAX_TOKENS, 8192)


if __name__ == '__main__':
    unittest.main()
