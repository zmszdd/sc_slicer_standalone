"""Local pre-flight and stage-2 input preview. Never calls a model.

    preview.py screen --case-dir DIR [--case-dir DIR ...] [--output FILE]
    preview.py report (--case-dir DIR | --report FILE)
    preview.py plan --case-dir DIR --elements FILE
    preview.py prompt [--version VERSION] --part definitions|element|formal
"""
import argparse
import json
from pathlib import Path
import sys

from prompts.active import resolve_prompt_set
from prompts.definitions import render_definitions
from prompts.registry import DEFAULT_VERSION, SELECTABLE_VERSIONS


def screen_case(case_dir):
    from evidence_catalog import build_catalog
    from semantic_pipeline import load_report

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


def screen_main():
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


def preview_main():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_subparsers(dest='mode', required=True)
    report = modes.add_parser('report', help='preview the first-step report prose')
    source = report.add_mutually_exclusive_group(required=True)
    source.add_argument('--case-dir', type=Path)
    source.add_argument('--report', type=Path)
    plan = modes.add_parser('plan', help='preview the second-step lean JSON')
    plan.add_argument('--case-dir', type=Path, required=True)
    plan.add_argument('--elements', type=Path, required=True,
                      help='existing report-elements/2 JSON from the same case')
    prompt = modes.add_parser('prompt', help='preview canonical definitions or an exact resolved prompt')
    prompt.add_argument('--version', choices=SELECTABLE_VERSIONS, default=DEFAULT_VERSION)
    prompt.add_argument('--part', choices=('definitions', 'element', 'formal'),
                        default='definitions')
    args = parser.parse_args()
    if args.mode == 'prompt':
        if args.part == 'definitions':
            print(json.dumps({
                'version': args.version,
                'part': args.part,
                'external_model_called': False,
            }, ensure_ascii=False), file=sys.stderr)
            print(render_definitions(), end='')
            return 0
        resolved = resolve_prompt_set(args.version)
        print(json.dumps({
            'version': args.version,
            'part': args.part,
            'sha256': resolved.sha256(args.part),
            'bytes': len(resolved.text(args.part).encode()),
            'external_model_called': False,
        }, ensure_ascii=False), file=sys.stderr)
        print(resolved.text(args.part), end='')
        return 0
    from evidence_catalog import build_catalog, hydrate_elements
    from semantic_core import validate_elements
    from semantic_pipeline import compact_json, lean_formal_input, load_report

    if args.mode == 'report':
        text, _, provenance = load_report(case_dir=args.case_dir,
                                          report_path=args.report)
        print(json.dumps({
            'report_input_policy': provenance['report_input_policy'],
            'report_input_sha256': provenance['report_input_sha256'],
            'bytes': len(text.encode()),
            'external_model_called': False,
        }, ensure_ascii=False), file=sys.stderr)
        print(text)
        return 0
    text, _, _ = load_report(case_dir=args.case_dir)
    raw = json.loads(args.elements.read_text())
    if raw.get('schema_version') != 'report-elements/2':
        print('lean preview requires report-elements/2', file=sys.stderr)
        return 2
    elements = hydrate_elements(raw, build_catalog(text), text)
    validate_elements(elements, text)
    print(compact_json(lean_formal_input(raw)))
    return 0


MODES = ('screen', 'report', 'plan', 'prompt')


def main():
    """Dispatch on the leading mode token; bare invocation means screen."""
    mode = 'screen'
    if len(sys.argv) > 1 and sys.argv[1] in MODES:
        mode = sys.argv.pop(1)
    if mode == 'screen':
        screen_main()
        return 0
    sys.argv.insert(1, mode)
    preview_main()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
