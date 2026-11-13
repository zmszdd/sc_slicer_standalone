"""Shared code4rena finding lookup for the blind-set pipelines.

The canonical, complete per-finding data (``body`` + ``proof_of_concept``) lives
in ``c4_pipeline_output/<project>/<batch>/findings.json`` and is keyed by
``number`` / ``submission_index``. The API dump under
``code4rena_reports/<project>/submission_<id>.json`` uses a different id scheme
and is only a partial mirror, so it must not be the primary source.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FLATTEN_ROOT = ROOT / 'c4_pipeline_output'


def matching_finding(case: dict) -> dict | None:
    project_id = str(case.get('project_id') or '')
    project = str(case.get('project') or '')
    keys = {str(case.get('finding_key') or ''),
            str(case.get('finding_uid') or ''),
            str(case.get('finding_key') or '')}
    keys = {k for k in keys if k}
    for proj_dir in FLATTEN_ROOT.iterdir():
        if not proj_dir.is_dir():
            continue
        name = proj_dir.name
        if project_id not in name and project not in name:
            continue
        for batch in sorted(proj_dir.iterdir()):
            fj = batch / 'findings.json'
            if not fj.is_file():
                continue
            try:
                findings = json.loads(fj.read_text())
            except json.JSONDecodeError:
                continue
            if not isinstance(findings, list):
                continue
            for finding in findings:
                if not isinstance(finding, dict):
                    continue
                row_keys = {str(finding.get('number') or ''),
                            str(finding.get('submission_index') or ''),
                            str(finding.get('uid') or '')}
                if keys & row_keys:
                    return finding
    return None
