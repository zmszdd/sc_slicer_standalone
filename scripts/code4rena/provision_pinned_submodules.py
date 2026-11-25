#!/usr/bin/env python3
"""Restore pinned submodule snapshots for frozen negative stage-1 cases.

The stage-1 repository cache contains main-repository gitlinks but no checked
out objects for most submodules.  This tool reads each gitlink from the cached
main repository, fetches exactly that commit from the URL recorded in
``.gitmodules``, and installs the checked-out tree at the gitlink path.  It
does not sample cases, change labels, or use donor versions.
"""
from __future__ import annotations

import argparse
import configparser
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parents[1]
REPO_CACHE = ROOT / 'c4_pipeline_output' / '_github_repos_by_project'
CASES_DEFAULT = (ROOT / 'tools' / 'stage3' / 'evaluation' / 'metrics'
                 / 'official_negative_stage1_cases_20261121.json')
STATUS_DEFAULT = (ROOT / 'c4_pipeline_output'
                  / 'official_negative_neutral_entrypoints_20261121'
                  / 'neutral_entrypoint_status.json')
CACHE_DEFAULT = (ROOT / 'c4_pipeline_output' / '_pinned_submodule_cache')
AUDIT_DEFAULT = (ROOT / 'c4_pipeline_output'
                 / 'pinned_submodule_restore_20261121.json')


def _run(args: list[str], cwd: Path | None = None,
         timeout: int = 300) -> tuple[int, str]:
    env = os.environ.copy()
    env.setdefault('GIT_TERMINAL_PROMPT', '0')
    result = subprocess.run(args, cwd=cwd, env=env, timeout=timeout,
                            text=True, capture_output=True)
    return result.returncode, (result.stdout + result.stderr).strip()


def _repo_root(case: dict) -> Path | None:
    source = Path(case.get('source_path') or '')
    for parent in source.parents:
        if ((parent / 'foundry.toml').is_file()
                or (parent / 'hardhat.config.js').is_file()
                or (parent / 'hardhat.config.ts').is_file()):
            return parent
    return None


def _blocked_repos(cases_file: Path, status_file: Path) -> dict[str, str]:
    cases = json.loads(cases_file.read_text())['cases']
    rows = json.loads(status_file.read_text())['rows']
    blocked = {str(row['case']) for row in rows
               if row.get('status') != 'flatten_pass'}
    repos: dict[str, str] = {}
    for case in cases:
        if str(case['case']) not in blocked:
            continue
        repo = _repo_root(case)
        if repo is not None:
            repos[str(repo)] = str(case['case']).split('__')[0]
    return repos


def _submodule_specs(repo: Path) -> list[dict[str, str]]:
    gitmodules = repo / '.gitmodules'
    if not gitmodules.is_file():
        return []
    parser = configparser.ConfigParser()
    parser.optionxform = str.lower
    parser.read_string(gitmodules.read_text(
        encoding='utf-8', errors='replace'))
    specs = []
    for name, values in parser.items():
        if not name.startswith('submodule "'):
            continue
        path = values.get('path')
        url = values.get('url')
        if not path or not url:
            continue
        code, output = _run(['git', '-C', str(repo), 'ls-files', '-s', '--', path])
        parts = output.split()
        if code != 0 or len(parts) < 2 or parts[0] != '160000':
            continue
        specs.append({'path': path, 'url': url.rstrip('/'), 'sha': parts[1]})
    return specs


def _current_sha(path: Path) -> str | None:
    if not (path / '.git').exists():
        return None
    code, output = _run(['git', '-C', str(path), 'rev-parse', 'HEAD'])
    return output.strip() if code == 0 and len(output.strip()) == 40 else None


def _bare_repo(cache: Path, url: str, sha: str) -> Path:
    key = hashlib.sha256(f'{url}\0{sha}'.encode()).hexdigest()
    return cache / key[:2] / key[2:]


def _fetch_commit(bare: Path, url: str, sha: str) -> str | None:
    if not (bare / 'HEAD').is_file():
        code, output = _run(['git', 'init', '-q', '--bare', str(bare)])
        if code != 0:
            return output
    code, output = _run(['git', '-C', str(bare), 'cat-file', '-e',
                         f'{sha}^{{commit}}'])
    if code != 0:
        code, output = _run(['git', '-C', str(bare), 'fetch', '-q',
                             '--depth=1', url, sha], timeout=600)
        if code != 0:
            return output
    code, output = _run(['git', '-C', str(bare), 'cat-file', '-e',
                         f'{sha}^{{commit}}'])
    return None if code == 0 else output


def _checkout(bare: Path, sha: str, target: Path) -> str | None:
    with tempfile.TemporaryDirectory(prefix='pinned-submodule-') as tmp:
        worktree = Path(tmp) / 'tree'
        worktree.mkdir()
        code, output = _run(['git', f'--git-dir={bare}',
                             f'--work-tree={worktree}', 'checkout', '-f',
                             sha, '--', '.'])
        if code != 0:
            return output
        if not any(worktree.iterdir()):
            return 'checkout produced an empty tree'
        if target.exists():
            shutil.rmtree(target)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(worktree, target,
                        ignore=shutil.ignore_patterns('.git'))
    return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cases-file', type=Path, default=CASES_DEFAULT)
    parser.add_argument('--status-file', type=Path, default=STATUS_DEFAULT)
    parser.add_argument('--cache', type=Path, default=CACHE_DEFAULT)
    parser.add_argument('--audit', type=Path, default=AUDIT_DEFAULT)
    args = parser.parse_args(argv)

    args.cache.mkdir(parents=True, exist_ok=True)
    repos = _blocked_repos(args.cases_file, args.status_file)
    rows = []
    for repo_text, project in sorted(repos.items(), key=lambda item: item[1]):
        repo = Path(repo_text)
        specs = _submodule_specs(repo)
        for spec in specs:
            target = repo / spec['path']
            current = _current_sha(target)
            row = {
                'project': project,
                'repo': repo_text,
                'path': spec['path'],
                'url': spec['url'],
                'pinned_sha': spec['sha'],
                'current_sha': current,
                'result': '',
                'detail': '',
            }
            if current is None and target.exists() and any(target.iterdir()):
                row['replaced_non_git_content'] = True
            if current == spec['sha']:
                row['result'] = 'already_pinned'
            else:
                bare = _bare_repo(args.cache, spec['url'], spec['sha'])
                error = _fetch_commit(bare, spec['url'], spec['sha'])
                if error is None:
                    error = _checkout(bare, spec['sha'], target)
                row['result'] = 'restored' if error is None else 'failed'
                row['detail'] = (error or '')[-2000:]
                row['source'] = str(bare)
            rows.append(row)
            print(f'{project} {spec["path"]}: {row["result"]}', flush=True)

    summary = {'total': len(rows)}
    for row in rows:
        summary[row['result']] = summary.get(row['result'], 0) + 1
    args.audit.parent.mkdir(parents=True, exist_ok=True)
    args.audit.write_text(json.dumps({
        'schema_version': 'pinned-submodule-restore/1',
        'cases_file': str(args.cases_file.resolve()),
        'status_file': str(args.status_file.resolve()),
        'summary': summary,
        'rows': rows,
    }, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if summary.get('failed', 0) == 0 else 1


if __name__ == '__main__':
    raise SystemExit(main())
