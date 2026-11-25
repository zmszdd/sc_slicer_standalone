#!/usr/bin/env python3
"""Fail-fast provider health probe for Stage-2 and binding LLM calls.

The probe uses the same config, key, endpoint, model and request shape as
``tools/stage3/lib/llm.py`` but with a short timeout.  It never mutates
evaluation artifacts and is intentionally outside ``make verify`` because a
provider outage is an external condition, not a protocol regression.
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

STAGE3 = Path(__file__).resolve().parents[2]
if str(STAGE3) not in sys.path:
    sys.path.insert(0, str(STAGE3))

from lib import llm  # noqa: E402


def _classify(status: int | None, body: str) -> str:
    lower = body.lower()
    if 'gousagelimiterror' in lower or 'usage limit reached' in lower:
        return 'usage_limit'
    if status == 401:
        return 'invalid_credentials'
    if status == 402:
        return 'quota_or_billing'
    if status == 403:
        return 'access_blocked'
    if status == 429:
        return 'rate_limited'
    if status is not None and status >= 500:
        return 'provider_server_error'
    if '1010' in lower:
        return 'access_blocked'
    return 'request_failed'


def probe(timeout: float = 15.0) -> dict:
    provider = llm._provider()
    model = llm.MODEL
    started = time.monotonic()
    payload = {
        'model': model,
        'messages': [{
            'role': 'user',
            'content': 'Reply with exactly this JSON object: {"ok":true}',
        }],
        'response_format': {'type': 'json_object'},
        'temperature': 0,
        'max_tokens': 16,
        'stream': False,
        'thinking': {'type': 'disabled'},
    }
    try:
        key = llm.load_key()
        url, headers = llm._chat_url_and_headers(key)
        request = urllib.request.Request(
            url, data=json.dumps(payload).encode('utf-8'), method='POST',
            headers=headers)
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read(4_000).decode('utf-8', 'replace')
            status = int(response.status)
    except urllib.error.HTTPError as exc:
        body = exc.read(600).decode('utf-8', 'replace')
        return {
            'ok': False,
            'provider': provider,
            'model': model,
            'status': exc.code,
            'reason': _classify(exc.code, body),
            'detail': body[:300],
            'elapsed_ms': int((time.monotonic() - started) * 1000),
        }
    except Exception as exc:
        return {
            'ok': False,
            'provider': provider,
            'model': model,
            'status': None,
            'reason': 'network_or_config',
            'detail': f'{type(exc).__name__}: {exc}'[:300],
            'elapsed_ms': int((time.monotonic() - started) * 1000),
        }
    try:
        envelope = json.loads(raw)
        content = envelope['choices'][0]['message']['content']
        json.loads(content)
        ok = True
        reason = 'ok'
        detail = 'json_response_valid'
    except (ValueError, KeyError, IndexError, TypeError) as exc:
        ok = False
        reason = 'invalid_response'
        detail = f'{type(exc).__name__}: {raw[:300]}'
    return {
        'ok': ok,
        'provider': provider,
        'model': model,
        'status': status,
        'reason': reason,
        'detail': detail,
        'elapsed_ms': int((time.monotonic() - started) * 1000),
    }


def main() -> int:
    timeout = float(os.environ.get('PROVIDER_PROBE_TIMEOUT', '15'))
    result = probe(timeout)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result['ok'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
