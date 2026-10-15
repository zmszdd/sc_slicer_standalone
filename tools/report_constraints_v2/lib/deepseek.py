#!/usr/bin/env python3
"""DeepSeek 连接唯一定义处（single source of truth）。

与官方 DeepSeek API 有关的一切只在本文件：配置（模型、白名单、端点、
密钥路径、解码参数）、密钥读取、代理策略、HTTP 传输。其他模块
（cli/semantic_pipeline.py、tests）只 import 本文件，不再各自持有副本。

* **模型选择优先级**（高 → 低，解析在 cli/semantic_pipeline.py）
  1. ``--model`` CLI 显式覆盖（校验 ``DEEPSEEK_MODELS`` 白名单后传入）
  2. DeepSeek 官方通道默认 ``DEFAULT_DEEPSEEK_MODEL``
  3. opencode 通道回退：``config/llm.env`` 的 ``MODEL_NAME``（非 DeepSeek，
     定义在 cli/semantic_pipeline.py 的 ``configured_model``）
* **密钥**：``DEEPSEEK_KEY_FILE`` 为 0o600 本地文件（git 忽略；内容永不
  打印）；``load_deepseek_key`` 只做存在性/权限/格式校验。
* **代理**：``proxy_policy`` 三态开关（environment / direct / 显式 URL），
  拒绝 SOCKS；``proxy_in_effect`` 给诊断日志输出脱敏后的实际端点。
* **解码**：``DEEPSEEK_TEMPERATURE`` 必须为 0——实测同一 prompt 在官方
  默认温度下 4/4 次输出互不相同，非零温度会把 pass/fail 变成抽样属性
  而非报告属性；``DEEPSEEK_MAX_TOKENS`` 限制单次响应长度。
"""
import http.client
import json
import stat
import subprocess
import time
from pathlib import Path
from urllib import error as urlerror
from urllib import request as urlrequest
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[3]  # 仓库根

# DeepSeek 官方通道配置。
DEFAULT_DEEPSEEK_MODEL = 'deepseek-flash'
DEEPSEEK_MODELS = {'deepseek-flash', 'deepseek-v4-pro'}  # 官方通道白名单
DEEPSEEK_KEY_FILE = ROOT / 'config/stage2_deepseek.local.env'
DEEPSEEK_CHAT_URL = 'https://api.deepseek.com/chat/completions'
DEEPSEEK_TEMPERATURE = 0
DEEPSEEK_MAX_TOKENS = 8192


class TransientModelError(RuntimeError):
    """A provider transport failure for which one bounded retry is safe."""


def load_deepseek_key(path=None):
    """Read one local, git-ignored secret file; never execute shell contents."""
    path = Path(path) if path is not None else DEEPSEEK_KEY_FILE
    if not path.is_file():
        raise RuntimeError('stage-2 DeepSeek key file missing; see config/stage2_deepseek.local.env.example')
    if stat.S_IMODE(path.stat().st_mode) & 0o077:
        raise RuntimeError('stage-2 DeepSeek key file must be private (chmod 600)')
    values = []
    for line in path.read_text().splitlines():
        if line.strip().startswith('DEEPSEEK_API_KEY='):
            value = line.split('=', 1)[1].strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
                value = value[1:-1]
            values.append(value)
    if len(values) != 1 or not values[0] or any(c.isspace() for c in values[0]):
        raise RuntimeError('stage-2 DeepSeek API key is missing or malformed')
    return values[0]


class _NoRedirect(urlrequest.HTTPRedirectHandler):
    def redirect_request(self, *_args, **_kwargs):
        return None


def _redacted_proxy(value):
    """scheme://host:port only; never the credentials a proxy URL may carry."""
    if not value:
        return None
    parts = urlsplit(value)
    if not parts.hostname:
        return '(unparsable)'
    return f'{parts.scheme}://{parts.hostname}:{parts.port}'


def proxy_policy(value='environment'):
    """Normalize the proxy switch into (policy, explicit_url).

    'environment' honours the ambient *_proxy variables (historical default,
    read implicitly by urllib); 'direct' ignores them entirely; an http(s)://
    URL uses exactly that proxy.  urllib has no SOCKS support, so a socks5://
    value is rejected up front instead of surfacing as a mystery network error.
    """
    if value in ('environment', 'direct'):
        return value, None
    parts = urlsplit(value)
    if parts.scheme not in ('http', 'https') or not parts.hostname:
        raise ValueError(
            f'unsupported proxy {value!r}: use "environment", "direct", or an '
            'http(s):// URL (urllib has no SOCKS support)')
    return 'explicit', value


def _deepseek_opener(proxy='environment'):
    """Opener for the official transport; decides whether ambient proxies apply.

    'direct' passes an EMPTY ProxyHandler: that both registers no proxy and stops
    build_opener from installing the default env-reading ProxyHandler.
    """
    policy, explicit = proxy_policy(proxy)
    if policy == 'environment':
        return urlrequest.build_opener(_NoRedirect)
    if policy == 'direct':
        return urlrequest.build_opener(_NoRedirect, urlrequest.ProxyHandler({}))
    return urlrequest.build_opener(
        _NoRedirect, urlrequest.ProxyHandler({'http': explicit, 'https': explicit}))


def proxy_in_effect(proxy='environment'):
    """The proxy this policy will really use, redacted; None means direct."""
    policy, explicit = proxy_policy(proxy)
    if policy == 'explicit':
        return _redacted_proxy(explicit)
    if policy == 'direct':
        return None
    found = urlrequest.getproxies()
    return _redacted_proxy(found.get('https') or found.get('http'))


def extract_deepseek(text, output, model, prompt, *, key_path=None, opener=None,
                     proxy='environment'):
    """Direct official API transport; same candidate JSON contract as extract().

    ``proxy`` is the transport switch; see ``proxy_policy()``.
    """
    if model not in DEEPSEEK_MODELS:
        raise ValueError('unsupported official DeepSeek model identifier')
    key = load_deepseek_key(key_path)
    request_body = json.dumps({
        'model': model,
        'messages': [{'role': 'system', 'content': prompt},
                     {'role': 'user', 'content': text}],
        'response_format': {'type': 'json_object'},
        'thinking': {'type': 'disabled'},
        # Bounded decoding: constants and measured rationale live at the top
        # of this module (DEEPSEEK_TEMPERATURE / DEEPSEEK_MAX_TOKENS).
        'temperature': DEEPSEEK_TEMPERATURE,
        'max_tokens': DEEPSEEK_MAX_TOKENS,
        'stream': False,
    }, ensure_ascii=False).encode()
    request = urlrequest.Request(
        DEEPSEEK_CHAT_URL, data=request_body, method='POST',
        headers={'Content-Type': 'application/json', 'Authorization': 'Bearer ' + key})
    opener = opener or _deepseek_opener(proxy)
    proxy_endpoint = proxy_in_effect(proxy)
    started = time.monotonic()
    try:
        with opener.open(request, timeout=240) as response:
            body = response.read(4_000_001)
    except urlerror.HTTPError as exc:
        (output / 'model-runtime-diagnostic.json').write_text(json.dumps({
            'schema_version': 'model-runtime-diagnostic/1',
            'provider': 'deepseek', 'category': 'http_error',
            'http_status': exc.code, 'proxy_in_effect': proxy_endpoint,
            'raw_provider_output_saved': False,
        }, indent=2) + '\n')
        # 2026-10-15 blind-batch_08 attribution: gateway-family statuses
        # (502/503/504) are server-side overload, not candidate defects --
        # surfaced repeatedly during a DeepSeek outage window while the
        # classifier-style hard failure killed otherwise healthy runs.
        # They stay retryable so the existing bounded retry absorbs them.
        if exc.code in (502, 503, 504):
            raise TransientModelError(
                f'DeepSeek HTTP {exc.code}; response body not saved') from None
        raise RuntimeError(f'DeepSeek HTTP {exc.code}; response body not saved') from None
    except (TimeoutError, urlerror.URLError, OSError, http.client.IncompleteRead) as exc:
        timed_out = isinstance(exc, TimeoutError) or (
            isinstance(exc, urlerror.URLError) and isinstance(exc.reason, TimeoutError))
        interrupted = isinstance(exc, http.client.IncompleteRead)
        (output / 'model-runtime-diagnostic.json').write_text(json.dumps({
            'schema_version': 'model-runtime-diagnostic/1',
            'provider': 'deepseek',
            'category': ('timeout' if timed_out else
                         'incomplete_response' if interrupted else 'network'),
            'proxy_in_effect': proxy_endpoint,
            'raw_provider_output_saved': False,
        }, indent=2) + '\n')
        if timed_out:
            raise subprocess.TimeoutExpired('DeepSeek API', 240) from None
        if interrupted:
            raise TransientModelError('DeepSeek response interrupted; details not saved') from None
        raise RuntimeError('DeepSeek network failure; details not saved') from None
    if len(body) > 4_000_000:
        raise RuntimeError('DeepSeek response exceeds local size limit')
    try:
        response = json.loads(body)
        choice = response['choices'][0]
        content = choice['message']['content']
    except (ValueError, KeyError, IndexError, TypeError):
        # 2026-10-15 blind-batch_08 attribution: during a DeepSeek outage
        # window the endpoint answered valid-JSON-but-wrong-shape bodies
        # (empty/absent choices) alongside 503s.  A malformed envelope is
        # server-side degradation, not a candidate defect -- the same
        # retryable class as an interrupted body, so bounded retry absorbs
        # it instead of killing the whole run.
        raise TransientModelError(
            'DeepSeek response envelope invalid; raw body not saved') from None
    if not isinstance(content, str):
        raise RuntimeError('DeepSeek response content missing')
    (output / 'model-response.txt').write_text(content)
    usage = response.get('usage')
    (output / 'model-usage.json').write_text(json.dumps({
        'provider': 'deepseek', 'model': response.get('model', model),
        'elapsed_seconds': round(time.monotonic() - started, 3),
        'proxy_in_effect': proxy_endpoint,
        'usage': usage if isinstance(usage, dict) else None,
    }, ensure_ascii=False, indent=2))
    if choice.get('finish_reason') != 'stop':
        raise RuntimeError('DeepSeek response did not finish normally')
    claim = json.loads(content)
    if not isinstance(claim, dict):
        raise ValueError('DeepSeek JSON response must be an object')
    (output / 'model-claim.json').write_text(json.dumps(claim, ensure_ascii=False, indent=2))
    return claim
