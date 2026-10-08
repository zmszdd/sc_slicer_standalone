"""Numeric/address fidelity guards, and opt-in mechanical salvage + replay CLI.

合并自两个模块（S8），函数体逐字未改（仅一处 __file__ 深度修正）：
  - fidelity.py            : numeric and zero-address fidelity guards for report
                             formal plans (merged from numeric_fidelity.py +
                             address_fidelity.py on 2026-09-21).
  - mechanical_salvage.py  : opt-in, auditable mechanical repairs, plus their
                             offline replay CLI (salvage-replay).
"""
import argparse
import copy
import json
import re
import subprocess
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path

from semantic_core import identifier, normalize_truth_binding
from plan_synthesizer import synthesize_id_formalization
# NOTE(S8): `from fidelity import check_address_plan, check_numeric_plan` was DROPPED:
# both names are defined in THIS file now, so that import became a self-import via the
# fidelity shim -> "cannot import name ... from partially initialized module".


# ------------------- 节选自 fidelity.py -------------------

POWER_OF_TWO = r'2\s*\^\s*\{?\d+\}?(?:\s*[+-]\s*\d+)?'
NUMBER = (r'(?:' + POWER_OF_TWO +
          r'|-?(?:0[xX][0-9a-fA-F]+|(?:\d{1,3}(?:,\d{3})+|\d+)'
          r'(?:\.\d+)?(?:[eE][+-]?\d+)?))')
PLAIN_NUMBER = re.compile(r'(?<![A-Za-z0-9_])' + NUMBER + r'(?![A-Za-z0-9_])')
PROTOCOL_IDENTIFIER = re.compile(
    r'\b(?:ERC|EIP|BIP|BEP|CAIP|SIP|SLIP|TIP)-\d+\b', re.IGNORECASE)
SYMBOLIC = re.compile(r'(?P<op><=|>=|==|!=|<|>)\s*(?P<number>' + NUMBER + r')')
WORDS = re.compile(
    r'\b(?P<op>less than|smaller than|below|under|at most|no more than|'
    r'greater than|more than|above|at least|no less than|equal to)\s+'
    r'(?P<number>' + NUMBER + r')\b', re.IGNORECASE)
OPERATORS = {'<': 'lt', '<=': 'le', '>': 'gt', '>=': 'ge', '==': 'eq', '!=': 'ne',
             'less than': 'lt', 'smaller than': 'lt', 'below': 'lt', 'under': 'lt',
             'at most': 'le', 'no more than': 'le', 'greater than': 'gt',
             'more than': 'gt', 'above': 'gt', 'at least': 'ge',
             'no less than': 'ge', 'equal to': 'eq'}
REVERSED = {'lt': 'gt', 'le': 'ge', 'gt': 'lt', 'ge': 'le', 'eq': 'eq', 'ne': 'ne'}


def number(value):
    if isinstance(value, bool):
        raise ValueError('boolean is not a numeric bound')
    if isinstance(value, str):
        compact = re.sub(r'[\s{},]', '', value)
        power = re.fullmatch(r'2\^(\d+)(?:([+-])(\d+))?', compact)
        if power:
            result = 1 << int(power.group(1))
            if power.group(2):
                delta = int(power.group(3))
                result += delta if power.group(2) == '+' else -delta
            return Decimal(result)
        if compact.lower().startswith(('0x', '-0x')):
            return Decimal(int(compact, 16))
        value = compact
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError('invalid numeric bound') from exc


def explicit_bounds(text):
    found = []
    for pattern in (SYMBOLIC, WORDS):
        for match in pattern.finditer(text):
            found.append((OPERATORS[match.group('op').lower()], number(match.group('number'))))
    return set(found)


def predicate_bound(predicate):
    if not isinstance(predicate, dict):
        return None
    if predicate.get('kind') in ('all_of', 'any_of'):
        bounds = [bound for item in predicate.get('terms', [])
                  if (bound := predicate_bound(item)) is not None]
        return bounds[0] if len(bounds) == 1 else None
    if predicate.get('kind') != 'comparison':
        return None
    left, right = predicate.get('left'), predicate.get('right')
    operator = predicate.get('operator')
    if operator not in REVERSED:
        return None
    if isinstance(right, dict) and isinstance(left, str):
        if set(right) == {'const'}:
            return operator, number(right['const'])
        if set(right) == {'power_of_two', 'offset'}:
            return operator, number(
                f"2^{right['power_of_two']}{right['offset']:+d}")
    if isinstance(left, dict) and set(left) == {'const'} and isinstance(right, str):
        return REVERSED[operator], number(left['const'])
    return None


HEX_IDENTIFIER = re.compile(r'(?<![A-Za-z0-9_])-?0[xX][0-9a-fA-F]+(?![A-Za-z0-9_])')


def explicit_numbers(text, exclude_protocol_identifiers=False):
    """All explicit numeric literals, used only to prevent invented P constants."""
    if exclude_protocol_identifiers:
        text = PROTOCOL_IDENTIFIER.sub(lambda match: ' ' * len(match.group(0)), text)
    # A 0x-prefixed constant is a storage-slot or protocol identifier (live-3 and
    # live-4 Monetrix: slot 0x811), never a semantic bound the plan must echo.
    # Real hex bounds stay enforced: explicit_bounds still parses them.
    text = HEX_IDENTIFIER.sub(lambda match: ' ' * len(match.group(0)), text)
    return {number(match.group(0)) for match in PLAIN_NUMBER.finditer(text)}


def predicate_constants(predicate):
    if not isinstance(predicate, dict):
        return set()
    found = set()
    if set(predicate) == {'const'} and type(predicate['const']) is int:
        found.add(number(predicate['const']))
    if set(predicate) == {'power_of_two', 'offset'}:
        found.add(number(f"2^{predicate['power_of_two']}{predicate['offset']:+d}"))
    for value in predicate.values():
        if isinstance(value, dict):
            found |= predicate_constants(value)
        elif isinstance(value, list):
            for item in value:
                found |= predicate_constants(item)
    return found


def _numeric_detail(source_id, literals=(), bounds=()):
    """Name the offending source and its literals, for repair feedback.

    The numeric gate's messages used to stop at the family name, so a retry
    had no pointer to WHICH source or WHICH literals (final_holdout_02:
    Kinetiq's second attempt replaced the missing source instead of adding
    it).  The message keeps its declared prefix; only the tail grows.
    """
    parts = [source_id]
    if literals:
        parts.append('states ' + ', '.join(sorted(str(v) for v in literals)))
    if bounds:
        parts.append('bounds ' + ', '.join(
            f'{op} {value}' for op, value in sorted(bounds, key=str)))
    return ': ' + '; '.join(parts)


def check_numeric_plan(plan, elements, exclude_protocol_identifiers=False,
                       relax_assumptions=False):
    """Assumption statements carry context, not constraints: with
    ``relax_assumptions`` an un-encoded assumption no longer has to enter P
    (its numbers may merely restate literals already bound in P terms or name
    chain constants).  Fidelity checks on statements that ARE encoded are not
    relaxed, and preconditions stay fully strict either way."""
    statements = {row['id']: row for row in elements['statements']
                  if row['kind'] in ('precondition', 'assumption')}
    terms = {row['source_id']: row['predicate'] for row in plan['precondition_terms']}
    for source_id, statement in statements.items():
        unencoded_assumption = (relax_assumptions and
                                statement['kind'] == 'assumption' and
                                source_id not in terms)
        bounds = explicit_bounds(statement['text'])
        literals = explicit_numbers(
            statement['text'],
            exclude_protocol_identifiers=exclude_protocol_identifiers)
        if not bounds:
            if source_id not in terms:
                if literals and not unencoded_assumption:
                    raise ValueError('numeric P source missing from plan'
                                     + _numeric_detail(source_id, literals))
                continue
            constants = predicate_constants(terms[source_id])
            if literals and constants and not constants <= literals:
                raise ValueError('numeric P literal changed'
                                 + _numeric_detail(source_id, literals))
            continue
        if source_id not in terms:
            if not unencoded_assumption:
                raise ValueError('numeric P source missing from plan'
                                 + _numeric_detail(source_id, bounds=bounds))
            continue
        bound = predicate_bound(terms[source_id])
        if bound is None:
            raise ValueError('numeric P bound hidden by non-comparison predicate')
        if len(bounds) != 1 or bound not in bounds:
            raise ValueError('numeric P literal or direction changed'
                             + _numeric_detail(source_id, literals, bounds))


ZERO = re.compile(r'address\s*\(\s*0\s*\)|\bzero[ -]address\b', re.I)
ZERO_INPUT = re.compile(
    r'\b(?:recipient|destination|_to)\b\s*(?:is|=|==|input is|argument is)\s*'
    r'(?:the\s+)?(?:address\s*\(\s*0\s*\)|zero[ -]address)'
    r'|\brecipient\b.{0,80}\b(?:is|equals)\s+(?:the\s+)?'
    r'(?:address\s*\(\s*0\s*\)|zero[ -]address)'
    r'|\bspecifying\s+(?:address\s*\(\s*0\s*\)|zero[ -]address)\s+'
    r'as\s+(?:the\s+)?recipient'
    r'|\btransfer(?:red)?\b.{0,80}\bto\s+'
    r'(?:address\s*\(\s*0\s*\)|zero[ -]address)', re.I | re.S)
OWNER_ZERO = re.compile(
    r'\b(?:owner|ownership|recipient)\b.{0,100}'
    r'(?:address\s*\(\s*0\s*\)|\bzero[ -]address\b)', re.I | re.S)


def zero_relation(predicate, symbols):
    if isinstance(predicate, dict) and predicate.get('kind') in ('all_of', 'any_of'):
        return any(zero_relation(item, symbols) for item in predicate.get('terms', []))
    if not isinstance(predicate, dict) or predicate.get('kind') != 'comparison' or \
            predicate.get('operator') not in ('eq', 'ne'):
        return False
    left, right = predicate.get('left'), predicate.get('right')
    zero = symbols.get('zero_address')
    return (isinstance(left, str) and left != 'zero_address' and
            isinstance(right, dict) and right == {'symbol': 'zero_address'} and
            isinstance(zero, dict) and zero.get('sort') == 'address' and
            ZERO.search(zero.get('meaning', '')) is not None and
            isinstance(symbols.get(left), dict) and symbols[left].get('sort') == 'address')


def check_address_plan(plan, elements):
    statements = {row['id']: row for row in elements['statements']}
    symbols = plan['symbols']
    terms = {row['source_id']: row['predicate'] for row in plan['precondition_terms']}
    for source_id, statement in statements.items():
        if statement['kind'] in ('precondition', 'assumption') and ZERO_INPUT.search(statement['text']):
            if not zero_relation(terms.get(source_id), symbols):
                raise ValueError('zero-address P relation not observable')
    intent = statements[plan['intent_id']]
    pattern = plan['pattern']
    if ZERO.search(intent['text']):
        if not zero_relation(pattern.get('condition'), symbols):
            raise ValueError('zero-address I condition not observable')
    for source_id in plan['impact_ids']:
        if OWNER_ZERO.search(statements[source_id]['text']):
            if not zero_relation(pattern.get('effect'), symbols):
                raise ValueError('zero-address V ownership effect not observable')


def _eq_pinned_constants(predicate):
    """Constants an equality comparison pins to a symbol (exact scoping)."""
    if not isinstance(predicate, dict) or predicate.get('kind') != 'comparison' \
            or predicate.get('operator') != 'eq':
        return set()
    right = predicate.get('right')
    if isinstance(right, dict) and set(right) == {'const'} \
            and type(right['const']) is int:
        return {number(right['const'])}
    return set()


def example_pinning_review(plan, elements):
    """Flag P predicates whose pinned constants come from the impact example.

    A P equality that binds a symbol to a constant is a scoping decision.  It
    narrows the claim to the report's worked example when the pinned literal
    is example arithmetic: either it appears only in impact/PoC evidence (not
    in the term's own cited source), or -- the shape final_holdout_02's Hybra
    actually produced -- the model restated the example as precondition
    sources, so several distinct P terms pin constants that all appear in one
    impact statement's worked example.  Advisory only: the narrowing is
    visible and disclosed, never auto-rejected, and it is exactly the
    artefact stage 3 should see before binding, because an example-scoped P
    produces example-scoped verdicts.
    """
    statements = {row['id']: row for row in elements['statements']}
    impacts = {row['id']: explicit_numbers(row['text'])
               for row in elements['statements'] if row['kind'] == 'impact'}
    evidence_numbers = set().union(*impacts.values()) if impacts else set()

    # impact statements whose example numbers are pinned by >= 2 distinct
    # terms: the signature of a worked example being replayed as P facts.
    pinned_by_term = []
    for term in plan.get('precondition_terms') or []:
        if not isinstance(term, dict):
            continue
        pinned_by_term.append((term, _eq_pinned_constants(term.get('predicate'))))
    example_statement_hits = {}
    for term, constants in pinned_by_term:
        if not constants:
            continue
        for impact_id, numbers in impacts.items():
            overlap = constants & numbers
            if overlap:
                example_statement_hits.setdefault(impact_id, set()).update(overlap)
    multi_pin_impacts = {impact_id for impact_id, values
                         in example_statement_hits.items()
                         if len(values) >= 2}

    flagged = []
    for term, constants in pinned_by_term:
        if not constants:
            continue
        row = statements.get(term.get('source_id'))
        source_numbers = explicit_numbers(row['text']) if row else set()
        # (a) the literal is not in the term's own source, or (b) several
        # pinned example constants trace back to one worked example.
        foreign = constants - source_numbers
        if not foreign and not any(constants & impacts[i] for i in multi_pin_impacts):
            continue
        pinned = sorted(value for value in constants
                        if value in evidence_numbers)
        if not pinned:
            continue
        flagged.append({
            'statement_id': term.get('source_id'),
            'statement_kind': row.get('kind') if row else None,
            'pinned_constants': [str(value) for value in pinned],
            'constant_source': ('impact or PoC example text only'
                                if foreign else
                                'also restated as the precondition source; '
                                'example numbers trace to one impact statement'),
        })
    return {
        'schema_version': 'example-pinning-review/1',
        'advisory_only': True,
        'blocks_candidate_acceptance': False,
        'flagged_count': len(flagged),
        'flagged': flagged,
        'note': ('A flagged P equality pins constants that appear in the '
                 'impact/PoC worked example, narrowing the claim to the '
                 'example instance. Verify scope, or record the narrowing as '
                 'an assumption/limitation. This review never rewrites or '
                 'rejects the plan.'),
    }


# ------------------- 节选自 mechanical_salvage.py -------------------

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
    command = [sys.executable, '-m', 'cli.semantic_pipeline',
               '--case-dir', str(args.case_dir), '--elements', str(elements_path),
               '--origin', 'external_model', '--prompt-version', args.prompt_version,
               '--output', str(args.output / 'pipeline')]
    if plan_path.is_file():
        plan_raw = json.loads(plan_path.read_text())
        record['source_plan'] = str(plan_path.resolve())
        plan, record['plan_repairs'] = drop_unused_invalid_symbols(plan_raw)
        # Same boundary NORMALIZE the live pipeline applies, so this
        # offline replay reaches the same verdict as the run it replays.
        plan, truth_declarations = normalize_truth_binding(plan, elements)
        record['plan_repairs'] += truth_declarations
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
    completed = subprocess.run(command, check=False, capture_output=True, text=True,
                               cwd=str(Path(__file__).resolve().parents[1]))
    record['offline_pipeline_exit_code'] = completed.returncode
    record['offline_pipeline_status'] = (json.loads((args.output / 'pipeline/status.json').read_text())
                                         if (args.output / 'pipeline/status.json').is_file() else None)
    write_json(args.output / 'replay-status.json', record)
    print(json.dumps(record, ensure_ascii=False))
    return completed.returncode


    raise SystemExit(main())


if __name__ == '__main__':
    raise SystemExit(replay_main())
