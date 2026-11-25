#!/usr/bin/env python3
"""Provision the reference-patch data work queue for pending M1 cases.

Reads the dev-105 positive eval, finds cases whose claims route to
``reference_patch_required``, and pulls repo / line-of-code links from the
flatten corpus ``metadata.json`` / ``report.json``. It writes
``reference_patch_provision_queue.json`` with one entry per case so a human or
fetch script can fill ``base``/``fix`` refs and drop a ``reference_sources.json``
into ``cases/<case>/``.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STAGE3 = HERE.parents[1]
if str(STAGE3) not in sys.path:
    sys.path.insert(0, str(STAGE3))

from lib.reference_patch import (REFERENCE_SOURCES, PATCHED_DIR,
                                 has_reference_patch)  # noqa: E402
from lib.path_config import verified_flatten_root  # noqa: E402

POSITIVE = HERE / 'positive_eval_105.json'
FLATTEN_DEFAULT = verified_flatten_root()
OUT = HERE / 'reference_patch_provision_queue.json'


def _repo_from_lines(lines: list[str]) -> str | None:
    for line in lines or []:
        if 'github.com' not in line:
            continue
        before_hash = line.split('#')[0]
        parts = before_hash.split('/blob/')
        if len(parts) == 2:
            return parts[0]
    return None


def _load_sources(case_dir: Path) -> dict:
    path = case_dir / REFERENCE_SOURCES
    try:
        value = json.loads(path.read_text())
    except (OSError, ValueError):
        return {}
    return value if isinstance(value, dict) else {}


def provision_record(*, case: str, project: str, repo: str | None,
                     lines: list[str], case_dir: Path) -> dict:
    sources = _load_sources(case_dir)
    if sources.get('repo'):
        repo = str(sources['repo'])
    base = sources.get('base')
    fix = sources.get('fix')
    ready = bool(has_reference_patch(case_dir))
    materialized = (case_dir / PATCHED_DIR).is_dir()
    if (case_dir / 'patched.diff').is_file():
        source_kind = 'local_diff'
    elif sources.get('patched_src'):
        source_kind = 'patched_src'
    elif sources.get('diff'):
        source_kind = 'manifest_diff'
    elif repo and base and fix:
        source_kind = 'git_refs'
    elif materialized:
        source_kind = 'materialized_tree'
    else:
        source_kind = None
    reasons = []
    if (source_kind == 'patched_src'
            and not Path(str(sources.get('patched_src'))).is_dir()):
        ready = False
        reasons.append('patched_src_not_found')
    if (source_kind == 'manifest_diff'
            and not Path(str(sources.get('diff'))).is_file()):
        ready = False
        reasons.append('diff_not_found')
    if (source_kind == 'git_refs'
            and not (repo and Path(str(repo)).is_dir())):
        ready = False
        reasons.append('repo_not_local_or_missing')
    if not ready:
        if not sources:
            reasons.append('missing_reference_sources')
        if not repo:
            reasons.append('missing_repo')
        if not base:
            reasons.append('missing_base_ref')
        if not fix:
            reasons.append('missing_fix_ref')
    return {
        'case': case,
        'project': project,
        'repo': repo,
        'lines_of_code': lines,
        'base': base,
        'fix': fix,
        'source_kind': source_kind,
        'ready_to_materialize': ready,
        'materialized': materialized,
        'provisioned': ready,
        'reasons': reasons,
    }


def main() -> int:
    positive = json.loads(POSITIVE.read_text())
    pending = []
    for row in positive.get('cases', []):
        verdicts = row.get('verdicts') or []
        if 'reference_patch_required' not in verdicts:
            continue
        case = row.get('case')
        meta = FLATTEN_DEFAULT / case / 'metadata.json'
        repo = None
        lines: list[str] = []
        project = case.split('__')[0]
        if meta.is_file():
            metadata = json.loads(meta.read_text())
            project = metadata.get('project') or project
            report_path = metadata.get('report_source_path')
            if report_path:
                report = Path(report_path)
                # report_source_path points at findings.json; the sibling report
                # is the corpus report.json.
                corpus_report = FLATTEN_DEFAULT / case / 'report.json'
                if corpus_report.is_file():
                    src = json.loads(corpus_report.read_text()).get('source_record') or {}
                    lines = src.get('lines_of_code') or []
                    repo = _repo_from_lines(lines)
        pending.append(provision_record(
            case=case, project=project, repo=repo, lines=lines,
            case_dir=STAGE3 / 'cases' / case))
    payload = {
        'schema_version': 'reference-patch-provision/2',
        'generated': '2026-11-17',
        'count': len(pending),
        'note': ('provisioned=true means a deterministic reference-patch '
                 'source exists (patched/, patched.diff, or a complete '
                 'reference_sources.json). It does not mean a git repo is '
                 'merely reachable.'),
        'cases': pending,
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n')
    print(f'{len(pending)} cases -> {OUT}')
    for case_row in pending:
        print(('OK ' if case_row['provisioned'] else 'NO-REPO ') + case_row['case'])
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
