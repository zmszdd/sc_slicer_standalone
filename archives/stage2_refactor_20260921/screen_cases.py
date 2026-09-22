"""Offline preflight for Stage-2 inputs; never inspects generated P/I/V artifacts.

This command checks only objective input integrity before any model call. The mandatory
DeepSeek semantic sufficiency gate runs inside semantic_pipeline.py immediately before
P/I/V extraction.
"""
import argparse
import json
from pathlib import Path

from evidence_catalog import build_catalog
from semantic_pipeline import load_report


def screen_case(case_dir):
    case_dir = Path(case_dir)
    result = {
        'case_dir': str(case_dir.resolve()),
        'decision': None,
        'dimensions': {},
        'warnings': [],
        'external_model_calls': 0,
    }
    try:
        text, _, source = load_report(case_dir=case_dir)
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        result['decision'] = 'exclude_invalid_input'
        result['dimensions']['input_integrity'] = 'failed'
        result['warnings'].append(f'input: {type(exc).__name__}: {exc}')
        return result
    catalog = build_catalog(text)
    result['dimensions'].update({
        'input_integrity': 'passed',
        'paired_identity_checked': source['paired_case_checked'],
        'input_sha256': source['report_input_sha256'],
        'prose_characters': len(text),
        'evidence_fragments': len(catalog['fragments']),
    })
    if not source['paired_case_checked']:
        result['warnings'].append('paired identity not checked')
    result['decision'] = 'requires_semantic_input_screen'
    result['warnings'].append(
        'offline integrity passed; subject/action/effect/safety-basis sufficiency is not yet decided')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case-dir', type=Path, action='append', required=True,
                        help='repeat for each report case')
    parser.add_argument('--output', type=Path, help='new JSON result file; default: stdout only')
    args = parser.parse_args()
    cases = [screen_case(case) for case in args.case_dir]
    counts = {}
    for case in cases:
        counts[case['decision']] = counts.get(case['decision'], 0) + 1
    summary = {
        'schema_version': 'stage2-input-preflight/1',
        'model_calls': 0,
        'counts': counts,
        'cases': cases,
    }
    output = json.dumps(summary, ensure_ascii=False, indent=2) + '\n'
    if args.output:
        with args.output.open('x') as stream:
            stream.write(output)
    print(output, end='')


if __name__ == '__main__':
    main()
