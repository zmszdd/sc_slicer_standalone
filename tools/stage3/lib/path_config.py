"""Resolve external mainline paths from environment/local configuration.

This module contains no evaluation logic.  It exists so a cloned repository
can point at a different flatten corpus, Code4rena output tree, or forge-std
checkout without editing protocol-controlled source files.
"""
from __future__ import annotations

import os
from pathlib import Path

SCHEMA_VERSION = 'mainline-path-config/1'

ROOT = Path(__file__).resolve().parents[3]
CONFIG_LOCAL = ROOT / 'config' / 'paths.local.env'
CONFIG_DEFAULT = ROOT / 'config' / 'paths.env'


def _read_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.is_file():
        return values
    for line in path.read_text().splitlines():
        text = line.strip()
        if not text or text.startswith('#') or '=' not in text:
            continue
        key, value = text.split('=', 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def _config() -> dict[str, str]:
    values = _read_env_file(CONFIG_DEFAULT)
    values.update(_read_env_file(CONFIG_LOCAL))
    return values


def get(name: str, default: str | None = None) -> str | None:
    value = os.environ.get(name)
    if value is None:
        value = _config().get(name)
    if value is None:
        return default
    return value.replace('${SC_ROOT}', str(ROOT)).replace('$SC_ROOT', str(ROOT))


def _path(name: str, default: Path | None = None) -> Path:
    value = get(name)
    if value:
        return Path(value).expanduser().resolve()
    if default is not None:
        return Path(default).expanduser().resolve()
    raise RuntimeError(
        f'{name} is not configured; set it in the environment or '
        f'{CONFIG_LOCAL.relative_to(ROOT)}')


def repo_root() -> Path:
    return ROOT


def c4_output_root() -> Path:
    return _path('C4_OUTPUT_ROOT', ROOT / 'c4_pipeline_output')


def code4rena_reports_root() -> Path:
    return _path('CODE4RENA_REPORTS_ROOT', ROOT / 'code4rena_reports')


def verified_flatten_root() -> Path:
    return _path(
        'VERIFIED_FLATTEN_ROOT',
        c4_output_root() / 'verified_flatten_pass_1568_exact_cases')


def negative_flatten_root() -> Path:
    return _path(
        'NEGATIVE_FLATTEN_ROOT',
        c4_output_root() / 'objective_negative_flatten_1_7_16')


def negative_flatten_summary() -> Path:
    return _path(
        'NEGATIVE_FLATTEN_SUMMARY',
        negative_flatten_root() / 'input-summary.json')


def forge_std_candidates() -> tuple[Path, ...]:
    value = get('FORGE_STD_CANDIDATES')
    if not value:
        return ()
    return tuple(Path(item).expanduser().resolve()
                 for item in value.split(os.pathsep) if item.strip())


def describe() -> dict:
    return {
        'schema_version': SCHEMA_VERSION,
        'repo_root': str(ROOT),
        'c4_output_root': str(c4_output_root()),
        'verified_flatten_root': str(verified_flatten_root()),
        'negative_flatten_root': str(negative_flatten_root()),
        'negative_flatten_summary': str(negative_flatten_summary()),
        'forge_std_candidates': [str(path)
                                 for path in forge_std_candidates()],
    }
