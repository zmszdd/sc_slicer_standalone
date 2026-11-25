#!/usr/bin/env python3
"""Build stage1 data-prep inputs for the frozen official negative pool.

The case ids, labels and project allocation come from
``official_negative_pool_20261121.json``.  This script only materialises what
the existing Code4rena flatten and standalone-PoC scripts need; it never
selects, relabels or reorders evaluation cases.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import unquote

HERE = Path(__file__).resolve().parent
STAGE3 = HERE.parents[1]
ROOT = STAGE3.parents[1]
POOL = HERE / 'official_negative_pool_20261121.json'
CACHE_ROOT = ROOT / 'c4_pipeline_output' / '_github_repos_by_project'
FINDINGS_ROOT = ROOT / 'c4_pipeline_output'
SUBMISSIONS_OUT = HERE / 'official_negative_submissions_20261121.json'
CASES_OUT = HERE / 'official_negative_stage1_cases_20261121.json'
MD_OUT = HERE / 'official_negative_stage1_cases_20261121.md'

GITHUB_BLOB = re.compile(
    r'https://github\.com/(?P<owner>[^/]+)/(?P<repo>[^/]+)/blob/'
    r'(?P<ref>[^/]+)/(?P<path>[^#]+)')
CONTRACT_DECL = re.compile(r'^\s*(?:abstract\s+)?contract\s+([A-Za-z_]\w*)',
                           re.M)
DECLARATION = re.compile(r'^\s*(contract|library|interface)\s+([A-Za-z_]\w*)',
                         re.M)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read_source(path: Path) -> str:
    try:
        return path.read_text(encoding='utf-8', errors='replace')
    except OSError:
        return ''


def _candidate_sources(project_id: str, urls: list[str]) -> list[tuple[Path, str]]:
    cache = CACHE_ROOT / project_id
    candidates: list[tuple[Path, str]] = []
    seen: set[Path] = set()
    for url in urls:
        match = GITHUB_BLOB.match(url.strip())
        if not match:
            continue
        owner = match.group('owner')
        repo = match.group('repo')
        rel = unquote(match.group('path'))
        if cache.is_dir():
            for checkout in sorted(cache.iterdir()):
                if not checkout.name.startswith(f'{owner}__{repo}__'):
                    continue
                source = checkout / rel
                resolved = source.resolve()
                if source.is_file() and resolved not in seen:
                    seen.add(resolved)
                    candidates.append((resolved, url))
    return candidates


def _contract_score(path: Path, finding: dict) -> int:
    text = _read_source(path)
    contracts = CONTRACT_DECL.findall(text)
    if not contracts:
        return -100
    other_decls = [name for kind, name in DECLARATION.findall(text)
                   if kind != 'contract']
    evidence = ' '.join(str(finding.get(field) or '')
                        for field in ('title', 'body', 'proof_of_concept'))
    score = 10 + 2 * len(contracts) - min(8, len(other_decls))
    for name in contracts:
        if re.search(r'\b' + re.escape(name) + r'\b', evidence):
            score += 12
    stem = path.stem
    if re.search(r'\b' + re.escape(stem) + r'\b', evidence):
        score += 4
    return score


def _resolve_source(project_id: str, urls: list[str],
                    finding: dict | None = None) -> tuple[str, str, str]:
    candidates = _candidate_sources(project_id, urls)
    current = candidates[0] if candidates else (None, '')
    current_path = current[0]
    current_has_contract = bool(
        current_path and CONTRACT_DECL.search(_read_source(current_path)))
    if current_has_contract:
        reason = 'first_available_contract_source'
    elif finding is not None and candidates:
        ranked = sorted(
            ((_contract_score(path, finding), path, url)
             for path, url in candidates),
            key=lambda row: (-row[0], urls.index(row[2]) if row[2] in urls
                             else len(urls)))
        best_score, best_path, best_url = ranked[0]
        if best_score > -100:
            current_path, current_url = best_path, best_url
            reason = 'contract_source_from_finding_urls'
        else:
            reason = 'library_only_available'
    else:
        reason = 'first_available_source' if current_path else 'needs_clone'
    source_url = current[1]
    for url in urls:
        if current_path is not None and _candidate_matches(current_path, url,
                                                             project_id):
            source_url = url
            break
    return (str(current_path) if current_path else '',
            source_url or (urls[0] if urls else ''), reason)


def _candidate_matches(path: Path, url: str, project_id: str) -> bool:
    match = GITHUB_BLOB.match(url.strip())
    if not match:
        return False
    cache = CACHE_ROOT / project_id
    rel = unquote(match.group('path'))
    prefix = f"{match.group('owner')}__{match.group('repo')}__"
    return any(checkout.name.startswith(prefix) and
               (checkout / rel).resolve() == path
               for checkout in cache.iterdir() if checkout.is_dir())


def _resolve_sorted(project: str, submission_number: str,
                    preferred: Path | None) -> str:
    roots = []
    if preferred is not None:
        roots.append(preferred.parent)
    roots.extend(path for path in FINDINGS_ROOT.iterdir()
                 if path.is_dir() and not path.name.startswith('_')
                 and path.name.rsplit('_', 1)[-1] == project.rsplit('_', 1)[-1])
    for root in roots:
        sorted_dir = root / 'flatten_sorted'
        if not sorted_dir.is_dir():
            continue
        for path in sorted(sorted_dir.glob(f'{submission_number}__*.sorted.sol')):
            return str(path.resolve())
    return ''


def build(pool_path: Path = POOL) -> dict:
    pool = json.loads(Path(pool_path).read_text())
    if str(pool.get('schema_version') or '').split('/')[0] != 'official-negative-pool':
        raise SystemExit(f'unsupported negative pool: {pool_path}')

    cases = []
    submissions = []
    for row in pool.get('selected') or []:
        case_id = str(row['case'])
        project = str(row['project'])
        finding_uid = case_id.split('__')[1]
        submission_uid = case_id.split('__')[2]
        submission_number = str(row.get('submission_number') or '')
        source_file = Path(row['source'])
        findings = json.loads((ROOT / source_file).read_text()
                              if not source_file.is_absolute() else source_file.read_text())
        finding = next((item for item in findings
                        if str(item.get('uid')) == submission_uid), None)
        if finding is None:
            raise SystemExit(f'finding row not found for {case_id}')
        raw = finding.get('raw') or {}
        project_id = str(raw.get('auditUid')
                         or finding.get('project_id')
                         or project.rsplit('_', 1)[-1])
        urls = [str(url) for url in (finding.get('lines_of_code') or [])
                if 'github.com' in str(url)]
        source_path, source_url, source_reason = _resolve_source(
            project_id, urls, finding)
        sorted_path = _resolve_sorted(project, submission_number,
                                      (ROOT / source_file).resolve())
        cases.append({
            'case': case_id,
            'project': project,
            'project_id': project_id,
            'finding_key': submission_number,
            'finding_uid': finding_uid,
            'submission_uid': submission_uid,
            'severity': finding.get('severity'),
            'title': finding.get('title'),
            'source_path': source_path,
            'source_url': source_url,
            'source_selection_reason': source_reason,
            'sorted_flatten_path': sorted_path,
            'repo_status': 'local' if source_path else 'needs_clone',
            'pool_case': case_id,
        })
        submissions.append(raw)

    return {
        'schema_version': 'official-negative-stage1/1',
        'pool': str(pool_path),
        'pool_sha256': _sha256(Path(pool_path)),
        'policy': ('Deterministic stage1 data-prep view of the frozen pool; '
                   'no case selection or relabelling.'),
        'counts': {
            'cases': len(cases),
            'local_repos': sum(1 for row in cases
                               if row['repo_status'] == 'local'),
            'needs_clone': sum(1 for row in cases
                               if row['repo_status'] == 'needs_clone'),
            'sorted_ready': sum(1 for row in cases
                                if row['sorted_flatten_path']),
        },
        'cases': cases,
        'submissions': submissions,
    }


def markdown(report: dict) -> str:
    counts = report['counts']
    lines = [
        '# Official negative stage1 inputs', '',
        f"- pool: `{report['pool']}`",
        f"- pool sha256: `{report['pool_sha256']}`", '',
        '| item | value |', '| --- | ---: |',
        f"| cases | {counts['cases']} |",
        f"| local repos | {counts['local_repos']} |",
        f"| needs clone | {counts['needs_clone']} |",
        f"| sorted flatten ready | {counts['sorted_ready']} |", '',
        '| repo status | count |',
        '| --- | ---: |',
    ]
    by_status: dict[str, int] = {}
    for row in report['cases']:
        by_status[row['repo_status']] = by_status.get(row['repo_status'], 0) + 1
    for status, count in sorted(by_status.items()):
        lines.append(f'| {status} | {count} |')
    return '\n'.join(lines) + '\n'


def main(argv=None) -> dict:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pool', type=Path, default=POOL)
    parser.add_argument('--submissions-out', type=Path, default=SUBMISSIONS_OUT)
    parser.add_argument('--cases-out', type=Path, default=CASES_OUT)
    parser.add_argument('--markdown', type=Path, default=MD_OUT)
    args = parser.parse_args(argv)
    report = build(args.pool)
    args.submissions_out.write_text(
        json.dumps(report.pop('submissions'), ensure_ascii=False, indent=2) + '\n')
    args.cases_out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    args.markdown.write_text(markdown(report))
    print(json.dumps(report['counts'], ensure_ascii=False, indent=2))
    return report


if __name__ == '__main__':
    main()
