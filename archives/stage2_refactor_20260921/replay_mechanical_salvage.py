"""Offline replay of saved model output after opt-in mechanical salvage.

No model call. Output is a new directory; source runs remain untouched.
"""
import argparse
import json
from fidelity import check_numeric_plan, check_address_plan
from pathlib import Path
import subprocess
import sys

from mechanical_salvage import (normalize_attack_step_roles, normalize_element_ids,
                                drop_unused_invalid_symbols)
from plan_synthesizer import synthesize_id_formalization
from semantic_pipeline import load_report, write_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case-dir', type=Path, required=True)
    parser.add_argument('--source-run', type=Path, required=True)
    parser.add_argument('--plan', type=Path,
                        help='optional saved model plan from another matching run')
    parser.add_argument('--prompt-version', choices=('semantic-v3.12', 'semantic-v3.13',
                                                     'semantic-v3.14', 'semantic-v3.15',
                                                     'semantic-v3.16', 'semantic-v3.17'),
                        default='semantic-v3.12')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('output already exists; replay never overwrites a run')
    text, raw, provenance = load_report(case_dir=args.case_dir)
    source_provenance = json.loads((args.source_run / 'provenance.json').read_text())
    if provenance['report_sha256'] != source_provenance['report_sha256'] or \
            provenance['report_input_sha256'] != source_provenance['report_input_sha256']:
        parser.error('source run does not match this report/input')

    elements_raw = json.loads((args.source_run / 'neural-elements/model-claim.json').read_text())
    elements, element_repairs = normalize_element_ids(elements_raw)
    elements, role_repairs = normalize_attack_step_roles(elements)
    element_repairs.extend(role_repairs)
    args.output.mkdir(parents=True)
    elements_path = args.output / 'elements-ids.json'
    write_json(elements_path, elements)
    record = {'schema_version': 'stage2-mechanical-replay/1',
              'source_run': str(args.source_run.resolve()),
              'report_sha256': provenance['report_sha256'],
              'input_sha256': provenance['report_input_sha256'],
              'element_repairs': element_repairs, 'plan_repairs': [],
              'formalization_precheck': 'not_attempted', 'external_model_calls': 0}

    plan_path = args.plan or args.source_run / 'neural-formalization/model-claim.json'
    command = [sys.executable, str(Path(__file__).with_name('semantic_pipeline.py')),
               '--case-dir', str(args.case_dir), '--elements', str(elements_path),
               '--origin', 'external_model', '--prompt-version', args.prompt_version,
               '--output', str(args.output / 'pipeline')]
    if plan_path.is_file():
        plan_raw = json.loads(plan_path.read_text())
        record['source_plan'] = str(plan_path.resolve())
        plan, record['plan_repairs'] = drop_unused_invalid_symbols(plan_raw)
        write_json(args.output / 'formal-plan.json', plan)
        try:
            formal = synthesize_id_formalization(plan, elements)
            check_numeric_plan(plan, elements)
            check_address_plan(plan, elements)
            record['formalization_precheck'] = 'passed'
            formal_path = args.output / 'formalization-ids.json'
            write_json(formal_path, formal)
            command.extend(['--formalization', str(formal_path)])
        except (ValueError, KeyError, TypeError) as exc:
            record['formalization_precheck'] = 'failed'
            record['blocking_error'] = str(exc)
            command.append('--elements-only')
    else:
        command.append('--elements-only')
    completed = subprocess.run(command, check=False, capture_output=True, text=True)
    record['offline_pipeline_exit_code'] = completed.returncode
    record['offline_pipeline_status'] = (json.loads((args.output / 'pipeline/status.json').read_text())
                                         if (args.output / 'pipeline/status.json').is_file() else None)
    write_json(args.output / 'replay-status.json', record)
    print(json.dumps(record, ensure_ascii=False))
    return completed.returncode


if __name__ == '__main__':
    raise SystemExit(main())
