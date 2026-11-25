import io
import json
import unittest
import urllib.error
from unittest import mock

from lib import llm


class LlmRateLimitTest(unittest.TestCase):
    def test_429_is_retried_with_bounded_backoff(self):
        class FakeResponse:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self, _limit):
                payload = {'choices': [{'message': {'content': '{"ok":true}'}}]}
                return json.dumps(payload).encode()

        rate_limit = urllib.error.HTTPError(
            'https://opencode.ai/inference', 429, 'rate limit',
            {'Retry-After': '0'}, None)
        with mock.patch.object(llm.urlrequest, 'urlopen',
                               side_effect=[rate_limit, FakeResponse()]) as urlopen, \
                mock.patch.object(llm, 'load_key', return_value='test-key'), \
                mock.patch.object(llm.time, 'sleep') as sleep:
            claim = llm.chat_json('system', 'user')
        self.assertEqual(claim, {'ok': True})
        self.assertEqual(urlopen.call_count, 2)
        sleep.assert_called_once_with(0.0)

    def test_usage_limit_429_fails_immediately(self):
        body = json.dumps({
            'type': 'error',
            'error': {
                'type': 'GoUsageLimitError',
                'message': 'OpenCode Go usage limit reached (weekly)',
            },
        }).encode()
        usage_limit = urllib.error.HTTPError(
            'https://opencode.ai/inference', 429, 'rate limit',
            {'Retry-After': '0'}, io.BytesIO(body))
        with mock.patch.object(llm.urlrequest, 'urlopen',
                               side_effect=usage_limit) as urlopen, \
                mock.patch.object(llm, 'load_key', return_value='test-key'), \
                mock.patch.object(llm.time, 'sleep') as sleep:
            with self.assertRaises(llm.LLMError) as raised:
                llm.chat_json('system', 'user')
        self.assertEqual(urlopen.call_count, 1)
        sleep.assert_not_called()
        self.assertIn('usage limit reached', str(raised.exception).lower())

    def test_402_fails_immediately(self):
        billing = urllib.error.HTTPError(
            'https://opencode.ai/inference', 402, 'payment required',
            {}, io.BytesIO(b'insufficient quota'))
        with mock.patch.object(llm.urlrequest, 'urlopen',
                               side_effect=billing) as urlopen, \
                mock.patch.object(llm, 'load_key', return_value='test-key'), \
                mock.patch.object(llm.time, 'sleep') as sleep:
            with self.assertRaises(llm.LLMError) as raised:
                llm.chat_json('system', 'user')
        self.assertEqual(urlopen.call_count, 1)
        sleep.assert_not_called()
        self.assertIn('402', str(raised.exception))


if __name__ == '__main__':
    unittest.main()
