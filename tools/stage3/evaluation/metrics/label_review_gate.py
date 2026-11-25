#!/usr/bin/env python3
"""Quarantine frozen negative cases whose current runs reproduce a violation.

An official invalid finding that currently and terminally reproduces the
reported vulnerability is a label-quality signal, not a false positive or a
true negative.  This gate records the signal for manual adjudication and
blocks only the publication label; it never edits sample labels, run verdicts,
or the authoritative confusion matrix.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STAGE3 = HERE.parents[1]
if str(STAGE3) not in sys.path:
    sys.path.insert(0, str(STAGE3))
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from lib import mainline_protocol  # noqa: E402
from current_denominator import classify_claim  # noqa: E402

SCHEMA_VERSION = 'label-review-gate/1'
SAMPLE = HERE / 'mainline_sample_mini.json'
RUNS = STAGE3 / 'runs'
OUT_JSON = HERE / 'label_review_gate.json'
OUT_MD = HERE / 'label_review_gate.md'


def _load(path: Path) -> dict:
    try:
        payload = json.loads(Path(path).read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _default_roots() -> list[Path]:
    roots = [RUNS]
    roots.extend(sorted(HERE.glob('mainline_negative_*_rejected_runs')))
    return roots


def build(sample_path: Path = SAMPLE,
          run_roots: list[Path] | None = None) -> dict:
    sample = _load(Path(sample_path))
    negatives = {str(case) for case in sample.get('negative_cases') or []}
    roots = list(run_roots if run_roots is not None else _default_roots())
    found: dict[str, dict] = {}
    for root in roots:
        root = Path(root)
        if not root.is_dir():
            continue
        for run_dir in sorted(root.iterdir()):
            if not run_dir.is_dir():
                continue
            case = next((candidate for candidate in negatives
                         if run_dir.name.startswith(candidate + '__')), None)
            if case is None:
                continue
            summary = _load(run_dir / 'stage3-summary.json')
            if not summary:
                continue
            verdict = str(summary.get('consistency_verdict') or '')
            if verdict != 'violation_reproduced':
                continue
            classified = classify_claim({
                'consistency_verdict': verdict,
                'summary': summary,
                'label': 'negative',
            })
            if classified['bucket'] != 'eligible_current':
                continue
            previous = found.get(case)
            run_id = str(summary.get('run_id') or run_dir.name)
            if previous is None or run_id < previous['run_id']:
                found[case] = {
                    'case': case,
                    'status': 'label_review_required',
                    'claim_id': str(summary.get('claim_id') or ''),
                    'run_id': run_id,
                    'verdict': verdict,
                    'metric_eligibility': classified['metric_eligibility'],
                    'source': str(root),
                }
    cases = [found[case] for case in sorted(found)]
    return {
        'schema_version': SCHEMA_VERSION,
        'protocol': mainline_protocol.current(),
        'sample': str(Path(sample_path).resolve()),
        'sources': [str(Path(root).resolve()) for root in roots],
        'count': len(cases),
        'cases': cases,
        'policy': 'terminal current-protocol violation_reproduced on a frozen '
                  'negative is a label-review signal; it is not converted to '
                  'FP or TN and only blocks publication until adjudicated.',
    }


def markdown(report: dict) -> str:
    lines = [
        '# Negative label-review gate', '',
        f"- protocol: `{report['protocol']['version']}`",
        f"- cases requiring review: **{report['count']}**", '',
        '| case | claim | run |', '| --- | --- | --- |',
    ]
    for row in report['cases']:
        lines.append(f"| `{row['case']}` | `{row['claim_id']}` | "
                     f"`{row['run_id']}` |")
    if not report['cases']:
        lines.append('| - | - | - |')
    lines += ['', report['policy'], '']
    return '\n'.join(lines)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sample', type=Path, default=SAMPLE)
    parser.add_argument('--runs-root', type=Path, action='append', default=None)
    parser.add_argument('--out-json', type=Path, default=OUT_JSON)
    parser.add_argument('--out-md', type=Path, default=OUT_MD)
    args = parser.parse_args(argv)
    report = build(args.sample, args.runs_root)
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(report, ensure_ascii=False,
                                        indent=2) + '\n', encoding='utf-8')
    args.out_md.write_text(markdown(report), encoding='utf-8')
    print(json.dumps({
        'schema_version': SCHEMA_VERSION,
        'count': report['count'],
        'cases': [row['case'] for row in report['cases']],
        'out_json': str(args.out_json),
    }, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
