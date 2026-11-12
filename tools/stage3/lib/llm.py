"""Minimal DeepSeek JSON client for stage-3 binding proposal.

Self-contained (does not import stage-2): reads the same local secret the
stage-2 pipeline uses, posts to the official chat-completions endpoint with
deterministic decoding, and returns the parsed JSON object. It is used only
for *proposal* generation; every returned binding still passes the
deterministic lint before any forge run.
"""
from __future__ import annotations

import http.client
import json
import stat
from pathlib import Path
from urllib import error as urlerror
from urllib import request as urlrequest

REPO_ROOT = Path(__file__).resolve().parents[3]  # repository root
KEY_FILE = REPO_ROOT / 'config' / 'stage2_deepseek.local.env'
CHAT_URL = 'https://api.deepseek.com/chat/completions'
MODEL = 'deepseek-flash'
TEMPERATURE = 0
MAX_TOKENS = 8192


class LLMError(RuntimeError):
    pass


def load_key() -> str:
    path = KEY_FILE
    if not path.is_file():
        raise LLMError('DeepSeek key file missing: ' + str(path))
    if stat.S_IMODE(path.stat().st_mode) & 0o077:
        raise LLMError('DeepSeek key file must be private (chmod 600)')
    values = []
    for line in path.read_text().splitlines():
        if line.strip().startswith('DEEPSEEK_API_KEY='):
            value = line.split('=', 1)[1].strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
                value = value[1:-1]
            values.append(value)
    if len(values) != 1 or not values[0]:
        raise LLMError('DeepSeek API key is missing or malformed')
    return values[0]


def chat_json(system: str, user: str, *, model: str = MODEL,
              max_tokens: int = MAX_TOKENS) -> dict:
    key = load_key()
    body = json.dumps({
        'model': model,
        'messages': [{'role': 'system', 'content': system},
                     {'role': 'user', 'content': user}],
        'response_format': {'type': 'json_object'},
        'thinking': {'type': 'disabled'},
        'temperature': TEMPERATURE,
        'max_tokens': max_tokens,
        'stream': False,
    }, ensure_ascii=False).encode()
    req = urlrequest.Request(
        CHAT_URL, data=body, method='POST',
        headers={'Content-Type': 'application/json',
                 'Authorization': 'Bearer ' + key})
    try:
        with urlrequest.urlopen(req, timeout=240) as response:
            raw = response.read(4_000_001)
    except urlerror.HTTPError as exc:
        raise LLMError(f'DeepSeek HTTP {exc.code}') from None
    except (urlerror.URLError, OSError, http.client.IncompleteRead) as exc:
        raise LLMError(f'DeepSeek network failure: {exc}') from None
    try:
        envelope = json.loads(raw)
        content = envelope['choices'][0]['message']['content']
    except (ValueError, KeyError, IndexError, TypeError):
        raise LLMError('DeepSeek response envelope invalid') from None
    if not isinstance(content, str):
        raise LLMError('DeepSeek response content missing')
    try:
        claim = json.loads(content)
    except ValueError:
        raise LLMError('DeepSeek content is not valid JSON') from None
    if not isinstance(claim, dict):
        raise LLMError('DeepSeek JSON response must be an object')
    return claim
