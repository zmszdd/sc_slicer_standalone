"""Opt-in, auditable mechanical repairs, plus their offline replay CLI.

As a library: only identifier case and unused invalid symbol declarations are
touched; raw model responses stay unchanged and ordinary semantic/type guards
still run. semantic_pipeline uses these under --mechanical-salvage.

As a CLI:
    mechanical_salvage.py --case-dir DIR --source-run DIR --output DIR
"""
import argparse
import copy
import json
import subprocess
import sys
from pathlib import Path

from semantic_core import identifier
from fidelity import check_address_plan, check_numeric_plan
from plan_synthesizer import synthesize_id_formalization


def normalize_element_ids(raw):
    result = copy.deepcopy(raw)
    changes = []
    if not isinstance(result, dict) or result.get('schema_version') != 'report-elements/2':
        return result, changes
    for collection, label in (('entities', 'entity'), ('statements', 'statement')):
        rows = result.get(collection)
        if not isinstance(rows, list) or not all(isinstance(row, dict) for row in rows):
            return copy.deepcopy(raw), []
        names = [row.get('id') for row in rows]
        mapping = {}
        for name in names:
            if not isinstance(name, str):
                return copy.deepcopy(raw), []
            if identifier(name):
                mapping[name] = name
            elif name.lower() != name and identifier(name.lower()):
                mapping[name] = name.lower()
            else:
                return copy.deepcopy(raw), []
        # Collision or repeated original IDs are not safe to resolve mechanically.
        if len(mapping) != len(names) or len(set(mapping.values())) != len(names):
            return copy.deepcopy(raw), []
        for row in rows:
            old = row['id']
            row['id'] = mapping[old]
            if old != row['id']:
                changes.append({'kind': 'lowercase_identifier', 'type': label,
                                'from': old, 'to': row['id']})
        if collection == 'entities':
            for statement in result.get('statements', []):
                if isinstance(statement, dict) and isinstance(statement.get('entity_ids'), list):
                    statement['entity_ids'] = [mapping.get(x, x) for x in statement['entity_ids']]
        else:
            if isinstance(result.get('attack_steps'), list):
                result['attack_steps'] = [mapping.get(x, x) for x in result['attack_steps']]
    return result, changes


def normalize_attack_step_roles(raw):
    """Remove known non-action statement IDs from the redundant step index.

    Statements and their semantic roles are left untouched. Unknown IDs remain
    in place so the ordinary validator still rejects an ungrounded reference.
    """
    result = copy.deepcopy(raw)
    changes = []
    if not isinstance(result, dict) or result.get('schema_version') != 'report-elements/2':
        return result, changes
    statements = result.get('statements')
    steps = result.get('attack_steps')
    if not isinstance(statements, list) or not isinstance(steps, list) or \
            not all(isinstance(row, dict) for row in statements) or \
            not all(isinstance(step, str) for step in steps):
        return copy.deepcopy(raw), []
    roles = {}
    for row in statements:
        statement_id, kind = row.get('id'), row.get('kind')
        if not isinstance(statement_id, str) or not isinstance(kind, str) or \
                statement_id in roles:
            return copy.deepcopy(raw), []
        roles[statement_id] = kind
    kept = []
    for step in steps:
        if step in roles and roles[step] != 'action':
            changes.append({
                'kind': 'drop_non_action_attack_step_reference',
                'statement_id': step,
                'statement_kind': roles[step],
                'reason': 'attack_steps is an action-only index; statement content is unchanged',
            })
        else:
            kept.append(step)
    result['attack_steps'] = kept
    return result, changes


def _predicate_symbols(value):
    """Return only structured symbol references, never free-text mentions."""
    used = set()
    if isinstance(value, dict):
        for key, item in value.items():
            if key in ('symbol', 'left', 'dividend', 'before_symbol', 'after_symbol'):
                if isinstance(item, str):
                    used.add(item)
            used.update(_predicate_symbols(item))
    elif isinstance(value, list):
        for item in value:
            used.update(_predicate_symbols(item))
    return used


def drop_unused_invalid_symbols(raw):
    result = copy.deepcopy(raw)
    changes = []
    if not isinstance(result, dict) or not isinstance(result.get('symbols'), dict):
        return result, changes
    used = _predicate_symbols(result.get('precondition_terms'))
    used.update(_predicate_symbols(result.get('pattern')))
    for name, item in list(result['symbols'].items()):
        # A declaration with no entity binding is invalid. It is harmless to
        # remove only if no predicate references it. Never invent a binding.
        if name not in used and isinstance(item, dict) and item.get('entity_ids') == []:
            del result['symbols'][name]
            changes.append({'kind': 'drop_unreferenced_invalid_symbol', 'symbol': name,
                            'reason': 'empty entity_ids and no structured predicate reference'})
    return result, changes


def replay_main():
    # Imported lazily: semantic_pipeline imports this module.
    from semantic_pipeline import load_report, write_json
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


    raise SystemExit(main())


if __name__ == '__main__':
    replay_main()
