#!/usr/bin/env python3
"""Generate report drafts and runnable pipeline manifests from code4rena findings.

With ``--flatten-root`` pointing at the verified flatten index
(``verified_flatten_pass_1568_exact_cases``), each valid+sufficient high/medium
finding is joined to its flattened case through the authoritative ``index.csv``
keyed by ``(submission_uid, finding_uid)``:

* ``findings.json[].uid``              -> ``index.csv.submission_uid``
* ``findings.json[].raw.finding.uid``  -> ``index.csv.finding_uid``

A matched finding produces a manifest ready for ``pipeline-run --skip-stage1``:
the flattened PoC is passed straight through to stage-3 and the binding is left
empty for the runner's auto-bind step. Unmatched findings fall back to the
previous TODO skeleton so nothing is silently dropped.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]  # repo root
sys.path.insert(0, str(ROOT / 'tools' / 'pipeline'))

from lib.manifest import build_manifest_from_case  # noqa: E402


def _report_draft(finding: dict) -> dict:
    body = finding.get('body') or ''
    impact = finding.get('title', '')
    match = re.search(r'##\s*(Impact|Finding description and impact)\b', body,
                      re.IGNORECASE)
    if match:
        description = body[:match.start()].strip()
        impact = body[match.end():].strip() or impact
    else:
        description = body.strip()
    if not description:
        description = finding.get('title', '')
    return {
        'title': finding.get('title', ''),
        'description': description[:4000],
        'impact': impact[:2000],
    }


def _finding_keys(finding: dict) -> tuple[str | None, str | None]:
    """Extract the (submission_uid, finding_uid) pair used by index.csv."""
    raw = finding.get('raw') or {}
    fnd = raw.get('finding') or {}
    return (finding.get('uid'), fnd.get('uid'))


def _load_flatten_index(flatten_root: Path) -> dict[tuple[str, str], dict]:
    path = flatten_root / 'index.csv'
    if not path.is_file():
        return {}
    index: dict[tuple[str, str], dict] = {}
    with path.open(newline='') as handle:
        for row in csv.DictReader(handle):
            sub = (row.get('submission_uid') or '').strip()
            fid = (row.get('finding_uid') or '').strip()
            if sub and fid:
                index[(sub, fid)] = row
    return index


def _manifest_needs_input(finding: dict, binding_rounds: int) -> dict:
    """Emit a non-runnable placeholder with an explicit blocker.

    The previous ``TODO_`` skeleton silently dropped unmatched findings. This
    keeps the finding on the record with a machine-readable reason so nothing
    disappears from the summary.
    """
    uid = finding['uid']
    return {
        'schema_version': 'pipeline-manifest/1',
        'kind': 'needs_input',
        'case_id': f'c4_{uid}',
        'blockers': ['needs_flatten'],
        'reason': ('no verified flatten index entry for this finding; provide '
                   'contract.flattened.t.sol and re-run with --flatten-root'),
        'stage1': {
            'input': None,
            'contract': None,
            'variable': None,
            'function': None,
            'level': 2,
            'compile_guarantee': True,
            'output_slice': None,
        },
        'stage2': {
            'run_dir': None,
        },
        'stage3': {
            'binding_rounds': binding_rounds,
            'test': None,
            'case_dir': None,
        },
    }


def _infer_test_function(flatten: Path) -> str | None:
    """Return the PoC ``test_*`` function name from a flattened source file."""
    try:
        source = flatten.read_text()
    except OSError:
        return None
    match = re.search(r'\bfunction\s+(test_[A-Za-z0-9_]+)\s*\(', source)
    return match.group(1) if match else None


def _manifest_from_index_row(row: dict, flatten_root: Path, out: Path,
                             report_path: Path, contract: str | None,
                             variable: str | None,
                             binding_rounds: int) -> dict:
    case_key = row.get('key') or row.get('case_dir')
    flatten = flatten_root / row['case_dir'] / 'contract.flattened.t.sol'
    test_name = row.get('test_name') or _infer_test_function(flatten)
    manifest = build_manifest_from_case(
        case_id=case_key,
        src=flatten,
        test=None,
        out_dir=out,
        report=report_path,
        stage2_output=out / 'stage2' / case_key,
        contract=contract,
        variable=variable,
        function=test_name,
        binding=None,
        binding_rounds=binding_rounds,
        case_dir=out / 'cases' / case_key,
    )
    manifest['kind'] = 'runnable'
    return manifest


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--findings', required=True, help='findings.json path')
    parser.add_argument('--out-dir', required=True)
    parser.add_argument('--max-cases', type=int, default=0)
    parser.add_argument('--flatten-root', default=None,
                        help='verified flatten root with index.csv; fills '
                             'runnable manifests for matched findings')
    parser.add_argument('--contract', default=None,
                        help='stage-1 target contract override (slicing only)')
    parser.add_argument('--variable', default=None,
                        help='stage-1 target variable override (slicing only)')
    parser.add_argument('--binding-rounds', type=int, default=3)
    args = parser.parse_args(argv)

    findings_path = Path(args.findings)
    if not findings_path.is_file():
        raise SystemExit(f'findings not found: {findings_path}')
    data = json.loads(findings_path.read_text())
    if not isinstance(data, list):
        raise SystemExit('findings.json must be a JSON array')

    out = Path(args.out_dir).resolve()
    reports = out / 'reports'
    manifests = out / 'manifests'
    needs_input_dir = manifests / 'needs_input'
    reports.mkdir(parents=True, exist_ok=True)
    manifests.mkdir(parents=True, exist_ok=True)
    needs_input_dir.mkdir(parents=True, exist_ok=True)

    flatten_root = Path(args.flatten_root).resolve() if args.flatten_root else None
    index = _load_flatten_index(flatten_root) if flatten_root else {}

    selected = [x for x in data
                if x.get('validity') == 'valid'
                and x.get('quality') == 'sufficient'
                and x.get('severity') in ('high', 'medium')]
    if args.max_cases > 0:
        selected = selected[:args.max_cases]

    matched = 0
    unmatched = 0
    needs_input_reasons = {}
    for finding in selected:
        uid = finding['uid']
        report_path = (reports / f'{uid}.report.json').resolve()
        report_path.write_text(
            json.dumps(_report_draft(finding), ensure_ascii=False, indent=2) + '\n')

        row = index.get(_finding_keys(finding)) if index else None
        if row is not None:
            manifest = _manifest_from_index_row(
                row, flatten_root, out, report_path,
                args.contract, args.variable, args.binding_rounds)
            matched += 1
        else:
            manifest = _manifest_needs_input(finding, args.binding_rounds)
            unmatched += 1
            for blocker in manifest.get('blockers') or ['needs_input']:
                needs_input_reasons[blocker] = needs_input_reasons.get(blocker, 0) + 1
        target_dir = manifests if row is not None else needs_input_dir
        (target_dir / f'{uid}.pipeline.json').write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')

    summary = {
        'schema_version': 'manifest-gen-summary/1',
        'findings': str(findings_path),
        'total_findings': len(data),
        'selected': len(selected),
        'flatten_root': str(flatten_root) if flatten_root else None,
        'flatten_matched': matched,
        'flatten_unmatched': unmatched,
        'reports_written': len(selected),
        'manifests_written': len(selected),
        'runnable_manifests': matched,
        'needs_input_manifests': unmatched,
        'needs_input_reasons': needs_input_reasons,
        'note': ('flatten-matched manifests run with pipeline-run --skip-stage1 '
                 'and auto-bind stage-3; unmatched findings are written to '
                 'manifests/needs_input/ with an explicit blocker and skipped '
                 'by pipeline-batch'),
    }
    out_path = out / 'manifest-gen-summary.json'
    out_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
