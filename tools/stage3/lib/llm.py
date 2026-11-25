"""Minimal OpenAI-compatible JSON client for stage-3 binding proposal.

Self-contained (does not import stage-2).  The provider is resolved from
``config/llm.env`` (``LLM_PROVIDER`` / ``MODEL_NAME`` / ``API_BASE_URL``):

* ``opencode`` -- the OpenCode Go OpenAI-compatible endpoint.  This is the
  current mainline provider; it needs ``OPENCODE_API_KEY`` and an
  ``x-opencode-session`` header.
* ``deepseek`` -- the legacy official DeepSeek endpoint/key.

The client is used only for *proposal* generation; every returned binding
still passes the deterministic lint before any forge run.
"""
from __future__ import annotations

import http.client
import json
import os
import stat
import time
import uuid
from pathlib import Path
from urllib import error as urlerror
from urllib import request as urlrequest

REPO_ROOT = Path(__file__).resolve().parents[3]  # repository root
CONFIG_FILE = REPO_ROOT / 'config' / 'llm.env'
LOCAL_ENV_FILE = REPO_ROOT / 'config' / 'opencode.local.env'
KEY_FILE = REPO_ROOT / 'config' / 'stage2_deepseek.local.env'
OPENCODE_KEY_FIELDS = ('OPENCODE_API_KEY', 'OPENAI_API_KEY')
DEEPSEEK_CHAT_URL = 'https://api.deepseek.com/chat/completions'
OPENCODE_CHAT_URL = 'https://opencode.ai/inference/go/openai/v1/chat/completions'
DEFAULT_OPENCODE_MODEL = 'deepseek-v4.1-flash'
DEFAULT_DEEPSEEK_MODEL = 'deepseek-flash'
TEMPERATURE = 0
MAX_TOKENS = 8192
REQUEST_TIMEOUT = float(os.environ.get('LLM_REQUEST_TIMEOUT', '240'))
MAX_ATTEMPTS = max(1, int(os.environ.get('LLM_MAX_ATTEMPTS', '3')))
TERMINAL_429_MARKERS = (
    'gousagelimiterror',
    'usage limit reached',
    'insufficient_quota',
    'quota_exceeded',
    'billing_hard_limit',
)


class LLMError(RuntimeError):
    pass


def _read_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.is_file():
        return values
    for line in path.read_text().splitlines():
        text = line.strip()
        if not text or text.startswith('#') or '=' not in text:
            continue
        key, value = text.split('=', 1)
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
            value = value[1:-1]
        values[key.strip()] = value
    return values


def _config() -> dict[str, str]:
    cfg: dict[str, str] = {}
    cfg.update(_read_env_file(CONFIG_FILE))
    cfg.update(_read_env_file(LOCAL_ENV_FILE))
    return cfg


def _provider() -> str:
    return (_config().get('LLM_PROVIDER') or 'deepseek').strip().lower()


def _configured_model() -> str:
    cfg = _config()
    model = (cfg.get('MODEL_NAME') or '').strip()
    if not model:
        return (DEFAULT_OPENCODE_MODEL if _provider() == 'opencode'
                else DEFAULT_DEEPSEEK_MODEL)
    # ``opencode-go/<model>`` is the CLI-facing alias; the HTTP API expects the
    # bare id (for example ``deepseek-v4.1-flash``).
    if model.startswith('opencode-go/'):
        model = model.split('/', 1)[1]
    return model


MODEL = _configured_model()


def _load_deepseek_key() -> str:
    path = KEY_FILE
    if not path.is_file():
        raise LLMError('DeepSeek key file missing: ' + str(path))
    _require_private(path)
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


def _require_private(path: Path) -> None:
    if (path.is_file()
            and stat.S_IMODE(path.stat().st_mode) & 0o077):
        raise LLMError(f'key file must be private (chmod 600): {path}')


def _file_defines_key(path: Path) -> bool:
    if not path.is_file():
        return False
    for line in path.read_text().splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith('#') or '=' not in stripped:
            continue
        if stripped.split('=', 1)[0].strip() in OPENCODE_KEY_FIELDS:
            return True
    return False


def _load_opencode_key() -> str:
    env_key = os.environ.get('OPENCODE_API_KEY')
    if env_key:
        return env_key
    for path in (CONFIG_FILE, LOCAL_ENV_FILE):
        if _file_defines_key(path):
            _require_private(path)
    cfg = _config()
    key = cfg.get('OPENCODE_API_KEY') or cfg.get('OPENAI_API_KEY')
    if not key:
        raise LLMError('OpenCode API key missing: set OPENCODE_API_KEY in '
                       'config/llm.env or the environment')
    return key


def load_key() -> str:
    """Return the API key for the configured provider."""
    if _provider() == 'opencode':
        return _load_opencode_key()
    return _load_deepseek_key()


def _http_detail(exc: urlerror.HTTPError) -> str:
    body = _read_http_body(exc)
    return _http_detail_code(exc.code, body)


def _read_http_body(exc: urlerror.HTTPError) -> str:
    try:
        return exc.read(600).decode('utf-8', 'replace').strip()
    except Exception:
        return ''


def _http_detail_code(status: int, body: str) -> str:
    return f'HTTP {status}' + (f': {body[:400]}' if body else '')


def _terminal_http_error(status: int, body: str) -> bool:
    lower = body.lower()
    if status in (401, 402, 403):
        return True
    return status == 429 and any(marker in lower
                                 for marker in TERMINAL_429_MARKERS)


def _backoff_seconds(exc: urlerror.HTTPError, attempt: int) -> float:
    headers = getattr(exc, 'headers', None)
    retry_after = headers.get('Retry-After') if headers else None
    if retry_after:
        try:
            return min(max(float(retry_after), 0.0), 60.0)
        except (TypeError, ValueError):
            pass
    return min(5.0 * (2 ** attempt), 60.0)


def _chat_url_and_headers(key: str) -> tuple[str, dict[str, str]]:
    if _provider() == 'opencode':
        cfg = _config()
        base = (cfg.get('API_BASE_URL')
                or 'https://opencode.ai/inference/go/openai/v1').rstrip('/')
        url = base + '/chat/completions'
        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + key,
            'User-Agent': 'codex-stage3/1.0',
            'x-opencode-session': (os.environ.get('OPENCODE_SESSION_ID')
                                   or 'stage3-' + uuid.uuid4().hex),
        }
        return url, headers
    return DEEPSEEK_CHAT_URL, {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + key,
        'User-Agent': 'codex-stage3/1.0',
    }


def chat_json(system: str, user: str, *, model: str = MODEL,
              max_tokens: int = MAX_TOKENS) -> dict:
    key = load_key()
    provider = _provider()
    payload = {
        'model': model,
        'messages': [{'role': 'system', 'content': system},
                     {'role': 'user', 'content': user}],
        'response_format': {'type': 'json_object'},
        'temperature': TEMPERATURE,
        'max_tokens': max_tokens,
        'stream': False,
    }
    # Disable provider-side chain-of-thought so the small JSON answer is not
    # truncated by the completion budget (both endpoints accept this field).
    payload['thinking'] = {'type': 'disabled'}
    url, headers = _chat_url_and_headers(key)

    def post(payload: dict) -> bytes:
        body = json.dumps(payload, ensure_ascii=False).encode()
        for attempt in range(MAX_ATTEMPTS):
            req = urlrequest.Request(url, data=body, method='POST', headers=headers)
            try:
                with urlrequest.urlopen(req, timeout=REQUEST_TIMEOUT) as response:
                    return response.read(4_000_001)
            except urlerror.HTTPError as exc:
                error_body = _read_http_body(exc)
                detail = _http_detail_code(exc.code, error_body)
                if _terminal_http_error(exc.code, error_body):
                    raise LLMError('LLM ' + detail) from None
                if exc.code == 429 and attempt < MAX_ATTEMPTS - 1:
                    time.sleep(_backoff_seconds(exc, attempt))
                    continue
                raise LLMError('LLM ' + detail) from None
            except (urlerror.URLError, OSError, http.client.IncompleteRead) as exc:
                raise LLMError(f'LLM network failure: {exc}') from None
        raise AssertionError('unreachable')

    try:
        raw = post(payload)
    except LLMError as exc:
        # Some providers (for example Kimi) reject an explicit disabled
        # thinking block; retry once without it rather than failing the case.
        if 'invalid thinking' in str(exc) and 'thinking' in payload:
            payload.pop('thinking', None)
            raw = post(payload)
        else:
            raise
    try:
        envelope = json.loads(raw)
        choice = envelope['choices'][0]
        content = choice['message']['content']
    except (ValueError, KeyError, IndexError, TypeError):
        raise LLMError('LLM response envelope invalid: '
                       + raw[:400].decode('utf-8', 'replace')) from None
    if not isinstance(content, str):
        raise LLMError('LLM response content missing')
    try:
        claim = json.loads(content)
    except ValueError:
        raise LLMError('LLM content is not valid JSON (finish_reason='
                       + str(choice.get('finish_reason'))
                       + '): ' + content[:400]) from None
    if not isinstance(claim, dict):
        raise LLMError('LLM JSON response must be an object')
    return claim
