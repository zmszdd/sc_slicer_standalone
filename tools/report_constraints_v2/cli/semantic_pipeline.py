"""Report -> grounded core elements -> candidate formulas -> automatic acceptance.

Offline by default. DeepSeek extraction is consent-gated and first runs a mandatory
input-sufficiency call; ready reports then use two P/I/V/formalization calls.
No slicer invocation, code binding, formula repair or report-truth classification.
"""
import argparse
import copy
import json
from fidelity import check_numeric_plan, check_address_plan
from pathlib import Path
import subprocess

import report_only as r
from semantic_core import compile_bundle, validate_elements
from prompts.registry import (
    ADDRESS_GUARD_VERSIONS, ALLOWED_STATEMENT_ID_VERSIONS, CORE_COUNT_VERSIONS,
    DEFAULT_VERSION, ID_NORMALIZATION_VERSIONS, LEAN_FORMAL_INPUT_VERSIONS,
    LOCAL_REPAIR_VERSIONS, NUMERIC_GUARD_VERSIONS, PLAN_VERSIONS,
    PROMPT_MODULES, PROTOCOL_IDENTIFIER_EXCLUSION_VERSIONS,
    REFERENCED_CATALOG_VERSIONS, RELATION_ALIGNMENT_VERSIONS,
    STEP_NORMALIZATION_VERSIONS, STRICT_PIV_VERSIONS,
    STRUCTURED_UNRESOLVED_VERSIONS,
)
from prompts.active import resolve_prompt_set
from evidence_catalog import build_catalog, hydrate_elements, hydrate_formalization
from plan_synthesizer import (classified_relation_alignment, structured_unresolved_review,
                              synthesize_id_formalization)
from symbolic_queries import solve_queries
from review import attach_review
from review import from_bundle as triage_bundle, from_failure as triage_failure
from mechanical_salvage import (normalize_attack_step_roles, normalize_element_ids,
                                drop_unused_invalid_symbols)
from report_readiness import PROMPT as READINESS_PROMPT, model_payload, validate_readiness


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def model_catalog(catalog, allowed_ids=None):
    """Keep all exact ID/text pairs; offsets stay in the saved full catalog."""
    allowed = set(allowed_ids) if allowed_ids is not None else None
    return {'schema_version': catalog['schema_version'], 'source_sha256': catalog['source_sha256'],
            'fragments': [{'id': row['id'], 'text': row['text']} for row in catalog['fragments']
                          if allowed is None or row['id'] in allowed]}


def referenced_evidence_ids(elements):
    """Mechanical v3.1 payload reduction; it does not choose semantic facts."""
    ids = set(elements['scope']['evidence_ids'])
    for item in elements['entities'] + elements['statements']:
        ids.update(item['evidence_ids'])
    return ids


def allowed_statement_ids(elements):
    """Deterministic formal-step vocabulary; models may copy but never create IDs."""
    rows = elements['statements']
    return {
        'preconditions': [row['id'] for row in rows if row['kind'] in ('precondition', 'assumption')],
        'safety': [row['id'] for row in rows if row['kind'] == 'security_intent'],
        'effects': [row['id'] for row in rows if row['kind'] == 'impact'],
    }


def lean_formal_input(elements):
    """Second step needs grounded statement meanings/IDs, not duplicated prose.

    The full numbered catalog stays local for hydration and evidence checks.
    This is a transport reduction, not a different set of report claims.
    """
    return {
        'schema_version': 'report-formal-input/lean-1',
        'scope': {key: elements['scope'][key] for key in ('flow', 'environment')},
        'entities': [{key: row[key] for key in ('id', 'name', 'role')}
                     for row in elements['entities']],
        'statements': [{key: row[key] for key in ('id', 'kind', 'text', 'modality',
                                                'entity_ids')}
                       for row in elements['statements']],
        'ambiguities': elements['ambiguities'],
        'allowed_statement_ids': allowed_statement_ids(elements),
    }


def compact_json(value):
    return json.dumps(value, ensure_ascii=False, separators=(',', ':'))


def formal_repair_fields(exc):
    """Return the smallest top-level plan area allowed to change on retry."""
    message = str(exc)
    if message in ('fixed relation template mismatch',
                   'expanded relation template mismatch',
                   'relation class and pattern mismatch'):
        return ('pattern',)
    if message == 'relation repeats cancellable observable on both sides':
        return ('pattern', 'symbols', 'derived_definitions', 'unresolved', 'limitations')
    if ('derived definition' in message or
            message == 'referenced derived symbol lacks definition'):
        return ('derived_definitions', 'symbols')
    if message in ('P predicate symbol not grounded by selected preconditions',
                   'P predicate symbol not grounded by its own source',
                   'distinct P sources reuse identical predicate',
                   'P terms must cover selected preconditions exactly once') or \
            message.startswith('numeric P '):
        return ('precondition_ids', 'precondition_terms', 'symbols',
                'assumptions', 'unresolved', 'limitations')
    if message == 'core relation observables lack intent/impact grounding':
        return ('impact_ids', 'symbols', 'derived_definitions', 'pattern',
                'unresolved', 'limitations')
    if (message.startswith('impact qualifier missing from formal plan') or
            message in ('invalid impact context terms',
                   'invalid impact context term',
                   'impact context source not selected',
                   'invalid impact qualifier types',
                   'impact context symbol not grounded by its own source')):
        return ('impact_context_terms', 'symbols', 'pattern',
                'unresolved', 'limitations')
    if message == 'type/unit mismatch' or message in (
            'bounded relation type/unit mismatch',
            'correspondence type/unit mismatch',
            'proportional relation type/unit mismatch'):
        return ('relation_class', 'symbols', 'precondition_terms',
                'derived_definitions', 'impact_context_terms', 'pattern',
                'assumptions', 'unresolved', 'limitations')
    if message in ('invalid truth binding', 'truth binding requires bool symbol',
                   'unknown predicate symbol', 'unknown comparison symbol',
                   'invalid plan symbol', 'missing plan quantity unit',
                   'invalid quantity expression', 'invalid quantity binding',
                   'invalid quantity relation',
                   'invalid predicate binding', 'trivial self-comparison predicate'):
        return ('symbols', 'precondition_terms', 'derived_definitions', 'pattern',
                'unresolved', 'limitations')
    # Preserve semantic selection/classification even for an unfamiliar local
    # structural error. A later fresh run, rather than a repair, may reconsider it.
    return ('symbols', 'precondition_terms', 'derived_definitions', 'pattern',
            'assumptions', 'unresolved', 'limitations')


def validate_local_repair(previous, repaired, mutable_fields):
    """Reject a retry that silently changes unrelated semantic decisions."""
    if not isinstance(previous, dict) or not isinstance(repaired, dict):
        raise ValueError('local repair requires plan objects')
    if set(previous) != set(repaired):
        raise ValueError('local repair changed plan schema')
    mutable = set(mutable_fields)
    changed = {key for key in previous if previous[key] != repaired[key]}
    if not changed:
        raise ValueError('local repair made no change')
    if not changed <= mutable:
        raise ValueError('local repair changed frozen fields')
    return sorted(changed)


def local_repair_payload(original_payload, previous, exc, mutable_fields):
    """Build an audited, bounded repair request without asking for a new plan."""
    may_reclassify = 'relation_class' in mutable_fields
    return compact_json({
        'task': ('replan_relation_locally' if may_reclassify else
                 'repair_previous_formal_plan_locally'),
        'original_input': json.loads(original_payload),
        'previous_plan': previous,
        'repair_error': str(exc),
        'mutable_top_level_fields': list(mutable_fields),
        'requirements': [
            'Return the complete plan JSON object, not a patch.',
            'Change only mutable_top_level_fields.',
            ('Keep intent_id and impact_ids fixed. relation_class may change only '
             'to resolve the stated type/unit conflict.' if may_reclassify else
             'Keep relation_class, intent_id and all other frozen fields byte-for-byte equivalent.'),
            'Correct only the stated deterministic validation failure.',
        ],
    })


def formal_retry_hint(exc):
    """Use only fixed schema feedback; never echo model or provider text."""
    if isinstance(exc, subprocess.TimeoutExpired):
        return '\nRETRY FEEDBACK: Previous call timed out. Return only concise valid JSON.\n'
    if isinstance(exc, json.JSONDecodeError):
        return '\nRETRY FEEDBACK: Previous answer was not valid JSON. Return one JSON object only.\n'
    if str(exc) == 'missing plan quantity unit':
        return ('\nRETRY FEEDBACK: Every int symbol needs a nonempty unit string. '
                'For a unitless encoded number use "dimensionless"; '
                'only bool/address symbols use null. Keep report semantics unchanged.\n')
    if str(exc) == 'unknown synthesis pattern':
        return ('\nRETRY FEEDBACK: pattern must be one object with a top-level '
                '"kind" field, e.g. {"kind":"condition_forbids_effect", '
                '"condition":..., "effect":...}. Never nest it in another '
                '"pattern" object. Keep report semantics unchanged.\n')
    if str(exc) == 'invalid condition pattern':
        return ('\nRETRY FEEDBACK: For kind="condition_forbids_effect" or '
                '"condition_requires_effect", pattern must contain EXACTLY '
                'kind, condition, effect. condition and effect must each be a '
                'complete predicate object. Do not omit either field. '
                'Keep report semantics unchanged.\n')
    if str(exc) == 'invalid plan symbol':
        return ('\nRETRY FEEDBACK: Every symbols key must be lowercase snake_case '
                '(e.g. epoch_duration_seconds); every symbol object must have '
                'exactly sort, unit, meaning, checkpoint, entity_ids, source_ids. '
                'Use the same renamed key in predicates. Keep report semantics unchanged.\n')
    if str(exc) in ('invalid truth binding', 'truth binding requires bool symbol'):
        return ('\nRETRY FEEDBACK: Audit every predicate reference before returning. '
                'Every referenced symbol must be declared in symbols. A '
                'kind="truth" predicate may reference ONLY a declared sort:"bool" '
                'symbol and value must be true or false. For int/address symbols use '
                'comparison or relation with an explicit right operand; never treat '
                'an integer/address as Boolean. If the cited report fact explicitly '
                'says an operation/event occurred, declare a separate bool occurrence '
                'symbol grounded by that source; otherwise omit that P selection '
                'rather than inventing a trigger. Keep report semantics unchanged.\n')
    if str(exc) in ('unknown predicate symbol', 'unknown comparison symbol'):
        return ('\nRETRY FEEDBACK: Every symbol referenced by precondition_terms or '
                'pattern must be declared in symbols with the exact required object '
                'fields. Do not refer to an undeclared fair/expected/convenience '
                'variable. If the report does not ground that quantity, choose a '
                'narrower report-supported relation or mark unsupported_relation '
                'blocking. Keep report semantics unchanged.\n')
    if str(exc) in ('invalid quantity binding', 'invalid quantity expression'):
        return ('\nRETRY FEEDBACK: A QEXPR is symbol, integer const, exact '
                'power_of_two, or add/sub/mul with EXACTLY two args. Nest binary '
                'operations instead of returning three args. For ratios or '
                'proportional fairness, do not divide: cross-multiply both sides '
                'so their units match. Change only the malformed expression and '
                'its directly required symbols/definitions.\n')
    if str(exc) == 'relation class and pattern mismatch':
        return ('\nRETRY FEEDBACK: relation_class and pattern must be compatible. '
                'state_correspondence uses relation_obligation with observable '
                'equality/inequality; monotonicity uses monotonicity; conservation '
                'uses conservation or relation_obligation; value/bound/fairness/'
                'sequence/data/range relations use relation_obligation; access_control '
                'uses authorization or forbidden-effect; progress_or_liveness uses '
                'requires/forbids. Keep report semantics unchanged.\n')
    if str(exc) == 'fixed relation template mismatch':
        return ('\nRETRY FEEDBACK: Use the compiler-fixed template for the existing '
                'relation_class. monotonicity uses kind="monotonicity"; conservation '
                'uses kind="conservation"; every other class uses '
                'kind="relation_obligation" with condition and relation. Do not '
                'change relation_class, intent_id or impact_ids.\n')
    if str(exc) == 'expanded relation template mismatch':
        return ('\nRETRY FEEDBACK: Use the typed template fixed for the existing '
                'relation_class: authorization_guard, bounded_relation, '
                'monotonicity, conservation, proportional_relation, '
                'correspondence, temporal_order, required_effect, or the allowed '
                'relation_obligation fallback. Do not change intent_id or impact_ids.\n')
    if str(exc) == 'P predicate symbol not grounded by its own source':
        return ('\nRETRY FEEDBACK: Audit each P term separately. Every symbol used '
                'by that term must include that exact term source_id in source_ids. '
                'Add the source only when its report statement truly supports the '
                'symbol; otherwise declare a source-specific observable or remove '
                'that P selection. Do not borrow a different P source.\n')
    if str(exc) == 'distinct P sources reuse identical predicate':
        return ('\nRETRY FEEDBACK: Two different P sources used the same predicate. '
                'Keep only the clearest source if they express one fact, or encode '
                'each source with its own report-supported observable.\n')
    if str(exc) == 'impact context symbol not grounded by its own source':
        return ('\nRETRY FEEDBACK: Every symbol in an impact_context_terms predicate '
                'must cite that exact selected impact ID. Declare an impact-specific '
                'observable for what the impact text says; add the impact ID to an '
                'existing symbol only when that impact really supports its meaning.\n')
    if str(exc).startswith('impact qualifier missing from formal plan'):
        return ('\nRETRY FEEDBACK: impact_context_terms did not cover every explicit '
                'qualifier type detected in the selected impact. The repair_error '
                'lists the missing temporal/threshold/state types by impact ID. Add '
                'report-grounded predicates for those exact types without replacing '
                'the selected impact or intent.\n')
    if str(exc) == 'type/unit mismatch' or str(exc) in (
            'bounded relation type/unit mismatch',
            'correspondence type/unit mismatch',
            'proportional relation type/unit mismatch'):
        return ('\nRETRY FEEDBACK: The selected quantities have incompatible units. '
                'Do not relabel units or define a quotient with multiplication. Keep '
                'intent_id and impact_ids fixed. If the current relation_class cannot '
                'express the report relation with add/sub/mul and matching units, this '
                'bounded repair may choose a more suitable relation_class and its '
                'compiler-fixed template, or return blocking unsupported_relation.\n')
    if str(exc) == 'relation repeats cancellable observable on both sides':
        return ('\nRETRY FEEDBACK: The relation repeats the same unknown '
                'multiplicative observable on both sides, making the intended '
                'comparison vacuous or sign-dependent. For proportional fairness, '
                'compare distinct actual and full/expected quantities, e.g. '
                'actual_reward * total_duration versus full_reward * '
                'contributed_duration. Preserve the selected intent and impact.\n')
    if str(exc) == 'referenced derived symbol lacks definition':
        return ('\nRETRY FEEDBACK: Every referenced symbol whose checkpoint starts '
                'with "derived" needs exactly one derived_definitions entry. Define '
                'it with a report-grounded add/sub/mul quantity expression and cite '
                'selected source IDs. Do not replace it with an unconstrained name.\n')
    if 'derived definition' in str(exc):
        return ('\nRETRY FEEDBACK: Repair only derived_definitions and, if required, '
                'the corresponding symbol metadata. Definitions must target declared '
                'int symbols, be acyclic, preserve units, and use report-grounded '
                'base symbols and selected source IDs.\n')
    if str(exc).startswith('local repair '):
        return ('\nRETRY FEEDBACK: This is a local repair. Return the complete plan '
                'but change only mutable_top_level_fields. All frozen fields must '
                'remain structurally identical to previous_plan.\n')
    if str(exc).startswith('numeric P '):
        return ('\nRETRY FEEDBACK: Include EVERY extracted P/assumption source ID '
                'in precondition_terms. If its statement contains an explicit '
                'numeric comparison, its OWN P predicate must encode the SAME '
                'literal and comparison direction. Do not use a Boolean '
                'placeholder or weaker threshold. For 2^N +/- K use the exact '
                'power_of_two/offset operand, never floating point or scientific '
                'notation. Keep report facts unchanged.\n')
    if str(exc).startswith('zero-address '):
        return ('\nRETRY FEEDBACK: A report claim explicitly mentions '
                'address(0)/zero address. Declare zero_address and the relevant '
                'observable recipient/owner address as sort:address symbols. '
                'Use a comparison predicate eq/ne with '
                'right:{"symbol":"zero_address"} for that P, I condition, '
                'or direct ownership V effect. Do not use a Boolean placeholder. '
                'Keep report facts unchanged.\n')
    if str(exc) == 'P predicate symbol not grounded by selected preconditions':
        return ('\nRETRY FEEDBACK: A P predicate used a symbol not grounded by that '
                'P set. Every symbol referenced by a P predicate must include at '
                'least one selected precondition_id in its source_ids. Never '
                'encode a precondition as the absence/presence of the later impact. '
                'Keep report facts unchanged.\n')
    if str(exc) == 'trivial self-comparison predicate':
        return ('\nRETRY FEEDBACK: Never use x==x, x!=x, x<=x, x>=x or an '
                'equivalent self-comparison as P, trigger, condition, or relation. '
                'It is tautological/contradictory and does not encode a report fact. '
                'Compare distinct observable fields, or use a separately declared '
                'report-grounded bool occurrence symbol for an event/action trigger. '
                'Keep report semantics unchanged.\n')
    if str(exc) == 'core relation observables lack intent/impact grounding':
        return ('\nRETRY FEEDBACK: The core relation observables must collectively '
                'cite every selected impact_id in their symbol source_ids. The '
                'selected intent already grounds the I property in fixed-plan v4; '
                'older schemas may additionally require it on an observable. First '
                'reselect, from the supplied impact statements, '
                'the ONE impact that most directly negates the selected intent; '
                'prefer a failed/passed check or mismatched observable over its '
                'downstream economic consequence. Do not use trigger-only symbols '
                'or attach unrelated IDs merely to pass. Defer impacts that do not '
                'describe the same relation. Keep relation_class/pattern compatible. '
                'Keep report facts unchanged.\n')
    return ('\nRETRY FEEDBACK: Previous plan failed deterministic schema/type checks. '
            'Return one valid JSON plan, following the exact schema. '
            'Do not invent report facts.\n')


def element_retry_hint(_exc):
    """Fixed feedback avoids echoing model output or report content."""
    return ('\nRETRY FEEDBACK: Previous elements JSON failed deterministic structure '
            'or grounding checks. Return exactly the requested top-level keys; no '
            'placeholder/note keys. Include exactly one security_intent and at least '
            'one direct impact when the screened report supports them. attack_steps '
            'may reference action statements only. Use only supplied evidence IDs.\n')


def validate_core_element_candidate(candidate, catalog, text, normalize_steps=False,
                                    require_core_counts=False, normalize_ids=False,
                                    max_core_impacts=2):
    """Validate a neural ID candidate before accepting the extraction call."""
    checked = candidate
    if normalize_ids:
        checked, _ = normalize_element_ids(checked)
    if normalize_steps:
        checked, _ = normalize_attack_step_roles(checked)
    hydrated = hydrate_elements(checked, catalog, text)
    validate_elements(hydrated, text)
    if not require_core_counts:
        return
    kinds = [row['kind'] for row in checked['statements']]
    if kinds.count('security_intent') != 1:
        raise ValueError('elements require exactly one security intent')
    if not 1 <= kinds.count('impact') <= max_core_impacts:
        raise ValueError(f'elements require one to {max_core_impacts} direct impacts')


def request_elements(payload, prompt, model, output, retries, extract_fn=None,
                     validate_fn=None):
    """Bounded recovery for transport/JSON failures; preserve every attempt."""
    extract_fn = extract_fn or r.extract
    attempts = []
    feedback = ''
    for attempt in range(retries + 1):
        call_dir = output / ('neural-elements' if attempt == 0 else
                             f'neural-elements-retry-{attempt}')
        call_dir.mkdir()
        attempt_prompt = prompt + feedback
        (call_dir / 'prompt.txt').write_text(attempt_prompt + payload)
        record = {'attempt': attempt + 1, 'artifact_dir': call_dir.name}
        attempts.append(record)
        try:
            result = extract_fn(payload, call_dir, model, attempt_prompt)
            if validate_fn is not None:
                validate_fn(result)
            record['outcome'] = 'parsed_json'
            write_json(output / 'element-attempts.json', attempts)
            return result, attempts
        except (json.JSONDecodeError, subprocess.TimeoutExpired, r.TransientModelError,
                ValueError, KeyError, TypeError) as exc:
            record.update({'outcome': 'retryable_failure',
                           'error_type': type(exc).__name__,
                           'error': 'model timeout' if isinstance(exc, subprocess.TimeoutExpired)
                           else str(exc)})
            write_json(output / 'element-attempts.json', attempts)
            if attempt == retries:
                raise
            feedback = element_retry_hint(exc)
        except (RuntimeError, OSError) as exc:
            record.update({'outcome': 'non_retryable_failure',
                           'error_type': type(exc).__name__, 'error': str(exc)})
            write_json(output / 'element-attempts.json', attempts)
            raise
    raise AssertionError('unreachable')


def request_formalization(payload, prompt, model, output, retries, plan_mode,
                          elements, structured=False, extract_fn=None, attempts=None,
                          numeric_guard=False, address_guard=False,
                          mechanical_salvage=False, local_repair=False,
                          exclude_protocol_identifiers=False):
    """Retry malformed responses or perform a bounded, field-scoped plan repair.

    Each attempt keeps its own raw model artifacts. A rejected plan is never
    silently treated as successful. In local-repair mode, parsed plans freeze all
    unrelated top-level fields and the model receives the prior plan plus an
    explicit allow-list of fields it may change.
    """
    extract_fn = extract_fn or r.extract
    attempts = attempts if attempts is not None else []
    feedback = ''
    repair_base = None
    mutable_fields = ()
    repair_error = None
    for attempt in range(retries + 1):
        call_dir = output / ('neural-formalization' if attempt == 0 else
                             f'neural-formalization-retry-{attempt}')
        call_dir.mkdir(exist_ok=True)
        attempt_prompt = prompt + feedback
        attempt_payload = payload
        if local_repair and repair_base is not None:
            attempt_payload = local_repair_payload(
                payload, repair_base, repair_error, mutable_fields)
            attempt_prompt += ('\nLOCAL REPAIR MODE: repair the supplied previous_plan. '
                               'Do not reconsider frozen semantic decisions.\n')
        (call_dir / 'prompt.txt').write_text(attempt_prompt + attempt_payload)
        record = {'attempt': attempt + 1, 'artifact_dir': call_dir.name}
        if local_repair and repair_base is not None:
            record.update({'repair_mode': ('bounded_semantic_replan'
                                           if 'relation_class' in mutable_fields
                                           else 'field_scoped'),
                           'mutable_top_level_fields': list(mutable_fields)})
        attempts.append(record)
        candidate = None
        try:
            candidate = extract_fn(attempt_payload, call_dir, model, attempt_prompt)
            if local_repair and repair_base is not None:
                record['changed_top_level_fields'] = validate_local_repair(
                    repair_base, candidate, mutable_fields)
            if plan_mode:
                if mechanical_salvage:
                    candidate, repairs = drop_unused_invalid_symbols(candidate)
                    if repairs:
                        write_json(call_dir / 'mechanical-salvage.json', repairs)
                formal = synthesize_id_formalization(candidate, elements)
                if numeric_guard:
                    check_numeric_plan(
                        candidate, elements,
                        exclude_protocol_identifiers=exclude_protocol_identifiers)
                if address_guard:
                    check_address_plan(candidate, elements)
                if structured:
                    review = structured_unresolved_review(candidate, elements)
                else:
                    review = None
            else:
                formal, review = candidate, None
            record['outcome'] = 'accepted_for_validation'
            write_json(output / 'formalization-attempts.json', attempts)
            return candidate, formal, review
        except (json.JSONDecodeError, subprocess.TimeoutExpired, r.TransientModelError, ValueError,
                KeyError, TypeError) as exc:
            record.update({'outcome': 'retryable_failure', 'error_type': type(exc).__name__,
                           'error': 'model timeout' if isinstance(exc, subprocess.TimeoutExpired)
                           else str(exc)})
            write_json(output / 'formalization-attempts.json', attempts)
            if attempt == retries:
                raise
            if local_repair and isinstance(candidate, dict):
                can_promote = repair_base is None
                if repair_base is not None:
                    try:
                        validate_local_repair(repair_base, candidate, mutable_fields)
                        can_promote = True
                    except ValueError:
                        can_promote = False
                if can_promote:
                    repair_base = copy.deepcopy(candidate)
                mutable_fields = tuple(sorted(
                    set(mutable_fields) | set(formal_repair_fields(exc))))
                repair_error = exc
            feedback = formal_retry_hint(exc)
        except (RuntimeError, OSError) as exc:
            record.update({'outcome': 'non_retryable_failure',
                           'error_type': type(exc).__name__, 'error': str(exc)})
            write_json(output / 'formalization-attempts.json', attempts)
            raise
    raise AssertionError('unreachable')


def load_report(case_dir=None, report_path=None, input_policy_version=4):
    provenance = {'code_provided_to_model': False, 'contract_file_read': False,
                  'paired_case_checked': False}
    if case_dir:
        report_path = case_dir / 'report.json'
        report = json.loads(report_path.read_text())
        meta_path = case_dir / 'metadata.json'
        if meta_path.is_file():
            meta = json.loads(meta_path.read_text())
            pairing = report.get('pairing', {})
            if meta['report_match_status'] != 'exact_submission' or pairing.get('match_status') != 'exact_submission':
                raise ValueError('case is not exact paired')
            for key in ('submission_uid', 'finding_uid'):
                if report.get(key) != meta[key] or any(pairing.get(p + key) != meta[key]
                                                       for p in ('requested_', 'source_')):
                    raise ValueError('pairing identity mismatch')
            provenance.update({'case_id': meta['key'], 'submission_uid': meta['submission_uid'],
                               'finding_uid': meta['finding_uid'], 'target_test': meta.get('test_name'),
                               'declared_code_sha256': meta.get('contract_sha256'),
                               'paired_case_checked': True})
    else:
        report = json.loads(report_path.read_text()) if report_path.suffix == '.json' else None
    if report is not None:
        text, input_policy = r.report_json_input(report, input_policy_version=input_policy_version)
    else:
        # Compatibility for saved/manual experiments. New stage-2 runs use JSON.
        text = r.prose_only(report_path.read_text(), plain_section_exclusion=True)
        if not text: raise ValueError('empty prose')
        input_policy = {'source_format': 'legacy_markdown_or_text',
                        'policy_version': 'legacy-prose/3',
                        'selected_fields': ['document_prose'],
                        'excluded_fields': ['fenced_code', 'proof_of_concept',
                                            'recommended_mitigation']}
    raw = report_path.read_bytes()
    provenance.update({'report_path': str(report_path.resolve()), 'report_sha256': r.sha(raw),
                       'report_input_sha256': r.sha(text.encode()),
                       'report_input_policy': input_policy})
    return text, raw, provenance


def configured_model():
    for line in (r.ROOT / 'config/llm.env').read_text().splitlines():
        if line.strip().startswith('MODEL_NAME='):
            return line.strip().split('=', 1)[1].strip().strip('\"\'')
    raise ValueError('configured model identifier missing')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument('--case-dir', type=Path)
    source.add_argument('--report', type=Path,
                        help='report.json (canonical); Markdown/text remains legacy compatibility')
    parser.add_argument('--elements', type=Path, help='saved report-elements/1 JSON')
    parser.add_argument('--formalization', type=Path, help='saved report-formalization/1 JSON')
    parser.add_argument('--origin', choices=('assistant_review', 'external_model', 'synthetic_control'), default='assistant_review')
    parser.add_argument('--extract', action='store_true', help='two neural calls, not enabled by default')
    parser.add_argument('--formalize-only', action='store_true',
                        help='one neural formalization call from saved, already-grounded elements')
    parser.add_argument('--allow-report-upload', action='store_true')
    parser.add_argument('--elements-only', action='store_true')
    parser.add_argument('--provider', choices=('opencode', 'deepseek'), default='opencode',
                        help='stage-2 model transport; direct DeepSeek requires a private local key file')
    parser.add_argument('--model')
    parser.add_argument('--evidence-mode', choices=('ids', 'quotes'), default='ids',
                        help='neural mode defaults to source IDs; quotes is legacy compatibility')
    parser.add_argument('--formalization-scope', choices=('core', 'full'), default='core',
                        help='neural request scope: core formulas by default; deferred impacts remain review warnings')
    parser.add_argument('--formal-retries', type=int, choices=(0, 1, 2), default=0,
                        help='up to two audited retries for second-step empty/invalid JSON, timeout, or invalid plan')
    parser.add_argument('--element-retries', type=int, choices=(0, 1), default=0,
                        help='optional one retry for first-step timeout or invalid JSON; preserves both attempts')
    parser.add_argument('--lean-formal-input', action='store_true',
                        help='v3.12 core plan: send statement text/IDs without duplicated evidence catalog')
    parser.add_argument('--mechanical-salvage', action='store_true',
                        help='opt-in: lowercase unambiguous IDs and drop unused symbols with empty entity bindings')
    parser.add_argument('--continue-on-review', action='store_true',
                        help='exit successfully when core P/I/V is complete; keep review warnings and never certify semantic truth')
    parser.add_argument('--prompt-version', choices=tuple(PROMPT_MODULES),
                        default=DEFAULT_VERSION)
    parser.add_argument('--claim-verdict', choices=('legacy', 'signals'),
                        default='legacy',
                        help='legacy: report ambiguities/limitations and non-asserted '
                             'modality veto every claim; signals: record them as '
                             'informational fields instead (main.py run/batch inject '
                             'signals)')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.prompt_version in PLAN_VERSIONS and (
            args.evidence_mode != 'ids' or args.formalization_scope != 'core'):
        parser.error('plan-synthesis prompts support --evidence-mode ids --formalization-scope core only')
    if args.extract and args.formalize_only:
        parser.error('choose full extraction or formalize-only, not both')
    if args.formal_retries and not (args.extract or args.formalize_only):
        parser.error('--formal-retries requires neural formalization')
    if args.element_retries and not args.extract:
        parser.error('--element-retries requires --extract')
    if args.lean_formal_input and (args.elements_only or
                                  not (args.extract or args.formalize_only) or
                                  args.prompt_version not in LEAN_FORMAL_INPUT_VERSIONS or
                                  args.evidence_mode != 'ids'):
        parser.error('--lean-formal-input requires neural v3.12-v3.17 ID mode')
    neural_formalization = args.extract or args.formalize_only
    if args.provider == 'deepseek' and not neural_formalization:
        parser.error('--provider deepseek requires neural extraction or formalization')
    if neural_formalization:
        if not args.allow_report_upload: parser.error('external extraction requires explicit report-upload consent')
        if args.extract and (args.elements or args.formalization):
            parser.error('extract must not consume saved candidates')
        if args.formalize_only and (not args.elements or args.formalization or args.elements_only):
            parser.error('formalize-only requires --elements and forbids --formalization/--elements-only')
        if args.provider == 'deepseek':
            if args.model and args.model not in r.DEEPSEEK_MODELS:
                parser.error('unsupported official DeepSeek model identifier')
            try:
                r.load_deepseek_key()
            except RuntimeError as exc:
                parser.error(str(exc))
    elif not args.elements or (not args.elements_only and not args.formalization):
        parser.error('offline mode requires elements and formalization (or elements-only)')
    args.output.mkdir(parents=True, exist_ok=False)
    calls = 0
    try:
        text, raw, provenance = load_report(args.case_dir, args.report)
        provenance.update({'candidate_origin': 'external_model' if neural_formalization else args.origin,
                           'elements_source': str(args.elements) if args.elements else None,
                           'formalization_source': str(args.formalization) if args.formalization else None,
                           'prompt_version': args.prompt_version})
        unresolved_review = None
        if neural_formalization:
            provenance.update({'requested_formalization_scope': args.formalization_scope,
                               'formal_retries_allowed': args.formal_retries,
                               'element_retries_allowed': args.element_retries,
                               'lean_formal_input': args.lean_formal_input,
                               'mechanical_salvage': args.mechanical_salvage,
                               'model_catalog_view': 'exact_id_text_without_offsets',
                               'neural_mode': 'two_step' if args.extract else 'formalization_only',
                               'formalization_generation': ('deterministic_from_plan'
                                                            if args.prompt_version in PLAN_VERSIONS
                                                            else 'model_full_formalization'),
                               'reference_answers_provided_to_model': False})
            model = args.model or ('deepseek-flash' if args.provider == 'deepseek'
                                   else configured_model())
            extract_fn = r.extract_deepseek if args.provider == 'deepseek' else r.extract
            provenance.update({'model_provider': args.provider, 'model_name': model})
            resolved_prompts = resolve_prompt_set(
                args.prompt_version, args.evidence_mode, args.formalization_scope)
            provenance.update({
                'prompt_resolution': 'prompts.active/1',
                'element_prompt_sha256': resolved_prompts.sha256('element'),
                'formal_prompt_sha256': resolved_prompts.sha256('formal'),
            })
        provenance['claim_verdict_policy'] = (
            'signals-v2' if args.claim_verdict == 'signals' else 'legacy')
        write_json(args.output / 'provenance.json', provenance)
        (args.output / 'original-report').write_bytes(raw)
        (args.output / 'extraction-input.txt').write_text(text)
        catalog = build_catalog(text)
        write_json(args.output / 'evidence-catalog.json', catalog)
        if args.extract and args.provider == 'deepseek':
            # Mandatory semantic input gate for the supported production path.
            # It sees only numbered report prose and runs before P/I/V extraction.
            screen_dir = args.output / 'neural-input-screen'
            screen_dir.mkdir()
            screen_payload = model_payload(catalog)
            (screen_dir / 'prompt.txt').write_text(READINESS_PROMPT + screen_payload)
            calls += 1
            readiness = validate_readiness(
                extract_fn(screen_payload, screen_dir, model, READINESS_PROMPT), catalog)
            write_json(args.output / 'input-readiness.json', readiness)
            provenance['input_screening'] = 'deepseek-report-readiness-v1'
            write_json(args.output / 'provenance.json', provenance)
            if readiness['decision'] != 'ready':
                dimension_statuses = {
                    item['status'] for item in readiness['dimensions'].values()}
                uncertain_only = ('missing' not in dimension_statuses and
                                  'uncertain' in dimension_statuses)
                status = {
                    'core_formalization_status': 'not_attempted',
                    'acceptance_status': ('needs_input_review' if uncertain_only
                                          else 'excluded_before_extraction'),
                    'input_screening_status': ('uncertain' if uncertain_only
                                               else 'missing_information'),
                    'missing_dimensions': readiness['missing_dimensions'],
                    'external_model_invocations': calls,
                    'consistency_verdict': 'not_evaluated',
                }
                write_json(args.output / 'status.json', status)
                print(json.dumps(status))
                return 2
        if args.extract:
            payload = compact_json(model_catalog(catalog)) if args.evidence_mode == 'ids' else text
            prompt = resolved_prompts.element_prompt
            try:
                elements_raw, _ = request_elements(
                    payload, prompt, model, args.output, args.element_retries,
                    extract_fn=extract_fn,
                    validate_fn=(lambda candidate: validate_core_element_candidate(
                        candidate, catalog, text,
                        normalize_steps=args.prompt_version in STEP_NORMALIZATION_VERSIONS,
                        normalize_ids=args.prompt_version in ID_NORMALIZATION_VERSIONS,
                        require_core_counts=args.prompt_version in CORE_COUNT_VERSIONS,
                        max_core_impacts=(4 if args.prompt_version in RELATION_ALIGNMENT_VERSIONS
                                          else 2))
                        if args.evidence_mode == 'ids' else None))
            finally:
                attempts_path = args.output / 'element-attempts.json'
                if attempts_path.is_file():
                    calls += len(json.loads(attempts_path.read_text()))
        else:
            elements_raw = json.loads(args.elements.read_text())
        element_normalizations = []
        if args.prompt_version in ID_NORMALIZATION_VERSIONS:
            elements_raw, id_normalizations = normalize_element_ids(elements_raw)
            element_normalizations.extend(id_normalizations)
        if args.prompt_version in STEP_NORMALIZATION_VERSIONS:
            elements_raw, step_normalizations = normalize_attack_step_roles(elements_raw)
            element_normalizations.extend(step_normalizations)
        if element_normalizations:
            write_json(args.output / 'element-format-normalization.json',
                       element_normalizations)
        if args.mechanical_salvage and elements_raw.get('schema_version') == 'report-elements/2':
            elements_raw, repairs = normalize_element_ids(elements_raw)
            if repairs:
                write_json(args.output / 'mechanical-salvage-elements.json', repairs)
        if elements_raw.get('schema_version') == 'report-elements/2':
            write_json(args.output / 'elements-ids.json', elements_raw)
            elements = hydrate_elements(elements_raw, catalog, text)
        else:
            if args.extract and args.evidence_mode == 'ids': raise ValueError('ID mode requires report-elements/2')
            elements = elements_raw
        write_json(args.output / 'elements.json', elements)
        grounded = validate_elements(elements, text)
        write_json(args.output / 'evidence-spans.json', grounded)
        if args.elements_only:
            status = {'core_formalization_status': 'not_attempted', 'acceptance_status': 'elements_candidate',
                      'external_model_invocations': calls, 'consistency_verdict': 'not_evaluated'}
            write_json(args.output / 'status.json', status)
            print(json.dumps(status)); return 0
        if neural_formalization:
            if args.evidence_mode == 'ids':
                if args.lean_formal_input:
                    formal_input = lean_formal_input(elements_raw)
                else:
                    allowed = (referenced_evidence_ids(elements_raw)
                               if args.prompt_version in REFERENCED_CATALOG_VERSIONS else None)
                    formal_input = {'elements': elements_raw,
                                    'evidence_catalog': model_catalog(catalog, allowed)}
                if (not args.lean_formal_input and
                        args.prompt_version in ALLOWED_STATEMENT_ID_VERSIONS):
                    formal_input['allowed_statement_ids'] = allowed_statement_ids(elements_raw)
                payload = compact_json(formal_input)
            else:
                payload = compact_json({'elements': elements, 'report_prose': text})
            prompt = resolved_prompts.formal_prompt
            plan_mode = args.prompt_version in PLAN_VERSIONS
            attempts = []
            try:
                model_candidate, formal_raw, unresolved_review = request_formalization(
                    payload, prompt, model, args.output, args.formal_retries, plan_mode,
                    elements_raw,
                    args.prompt_version in STRUCTURED_UNRESOLVED_VERSIONS,
                    numeric_guard=args.prompt_version in NUMERIC_GUARD_VERSIONS,
                    address_guard=args.prompt_version in ADDRESS_GUARD_VERSIONS,
                    extract_fn=extract_fn, attempts=attempts,
                    mechanical_salvage=args.mechanical_salvage,
                    local_repair=args.prompt_version in LOCAL_REPAIR_VERSIONS,
                    exclude_protocol_identifiers=(
                        args.prompt_version in PROTOCOL_IDENTIFIER_EXCLUSION_VERSIONS))
            finally:
                calls += len(attempts)
            if plan_mode:
                write_json(args.output / 'formal-plan.json', model_candidate)
                if args.prompt_version in RELATION_ALIGNMENT_VERSIONS:
                    write_json(args.output / 'relation-alignment.json',
                               classified_relation_alignment(model_candidate, elements_raw))
                if unresolved_review is not None:
                    write_json(args.output / 'unresolved-review.json', unresolved_review)
        else:
            formal_raw = json.loads(args.formalization.read_text())
        if formal_raw.get('schema_version') == 'report-formalization/2':
            write_json(args.output / 'formalization-ids.json', formal_raw)
            formal = hydrate_formalization(formal_raw, catalog, text)
        else:
            if neural_formalization and args.evidence_mode == 'ids':
                raise ValueError('ID mode requires report-formalization/2')
            formal = formal_raw
        write_json(args.output / 'formalization.json', formal)
        bundle = compile_bundle(elements, formal, text,
                                strict_piv=args.prompt_version in STRICT_PIV_VERSIONS,
                                verdict_v2=args.claim_verdict == 'signals')
        observability = attach_review(bundle, formal)
        write_json(args.output / 'observability-review.json', observability)
        bundle['provenance'] = provenance
        bundle['external_model_invocations'] = calls
        declarations = []
        queries = {}
        for claim in bundle['claims']:
            filename = claim['id'] + '.smt2'
            (args.output / filename).write_text(claim.pop('smt'))
            original = next(x for x in formal['claims'] if x['id'] == claim['id'])
            base = {'symbols': {name: {k: v for k, v in item.items() if k != 'entity_ids'}
                                for name, item in formal['symbols'].items()},
                    'properties': {name: {k: v for k, v in item.items() if k != 'source_ids'}
                                   for name, item in original['properties'].items()},
                    'assumptions': original['assumptions'], 'unresolved': original['unresolved']}
            query_dir = args.output / 'queries' / claim['id']; query_dir.mkdir(parents=True)
            queries[claim['id']] = solve_queries(base, text)
            for name, result in queries[claim['id']].items():
                query_file = query_dir / (name + '.smt2')
                query_file.write_text(result.pop('smt'))
                result['path'] = str(query_file.relative_to(args.output))
                result['sha256'] = r.sha(query_file.read_bytes())
            declarations.append({'claim_id': claim['id'], 'predicates_path': filename,
                                 'predicates_sha256': r.sha((args.output / filename).read_bytes()),
                                 'formalization_status': claim['formalization_status'],
                                 'modality': claim['modality'], 'scope': claim['scope'],
                                 'report_queries': ['P AND V', 'P AND V AND NOT I', 'P AND V AND I'],
                                 'code_queries_after_binding': ['P AND T', 'P AND T AND NOT I',
                                                               'P AND T AND V', 'P AND T AND NOT V']})
        triage = triage_bundle(bundle, unresolved_review)
        write_json(args.output / 'constraints.json', bundle)
        write_json(args.output / 'auto-triage.json', triage)
        write_json(args.output / 'solver-results.json', {'scope': 'REPORT SPEC ONLY; no code T', 'claims': queries})
        interface = {'schema_version': 'stage3-semantic-spec/1',
                     'observability_review_path': 'observability-review.json',
                     'observability_review_sha256': r.sha((args.output / 'observability-review.json').read_bytes()),
                     'catalog_path': 'evidence-catalog.json',
                     'catalog_sha256': r.sha((args.output / 'evidence-catalog.json').read_bytes()),
                     'solver_results_path': 'solver-results.json',
                     'solver_results_sha256': r.sha((args.output / 'solver-results.json').read_bytes()),
                     'spec_path': 'constraints.json',
                     'spec_sha256': r.sha((args.output / 'constraints.json').read_bytes()),
                     'elements_path': 'elements.json', 'elements_sha256': r.sha((args.output / 'elements.json').read_bytes()),
                     'claims': declarations, 'acceptance_status': bundle['acceptance_status'],
                     'stage2_can_continue': triage['stage2_can_continue'],
                     'execution_ready': False, 'code_alignment_status': 'not_attempted',
                     'required_next_steps': ['Review semantic intent, effect coverage and textual assumptions',
                                             'Bind symbols/checkpoints to the paired PoC, without changing report claims',
                                             'Build actual code transition T with machine arithmetic and revert semantics'],
                     'consistency_verdict': 'not_evaluated'}
        if (args.output / 'unresolved-review.json').is_file():
            interface.update({
                'unresolved_review_path': 'unresolved-review.json',
                'unresolved_review_sha256': r.sha(
                    (args.output / 'unresolved-review.json').read_bytes()),
            })
        write_json(args.output / 'stage3-spec.json', interface)
        status = {key: bundle[key] for key in ('core_formalization_status', 'acceptance_status',
                                              'external_model_invocations', 'consistency_verdict')}
        status.update({'stage2_can_continue': triage['stage2_can_continue'],
                       'continuation_policy': 'warn_and_continue' if args.continue_on_review else 'strict_exit',
                       'warnings': triage['reasons'],
                       'continuation_blockers': triage['continuation_blockers']})
        write_json(args.output / 'status.json', status)
        print(json.dumps(status))
        return 0 if (bundle['acceptance_status'] == 'candidate_checks_passed' or
                     args.continue_on_review and triage['stage2_can_continue']) else 2
    except (ValueError, KeyError, TypeError, RuntimeError, OSError, subprocess.TimeoutExpired) as exc:
        status = {'core_formalization_status': 'failed', 'acceptance_status': 'rejected',
                  'error_type': type(exc).__name__, 'error': str(exc) if not isinstance(exc, subprocess.TimeoutExpired) else 'model timeout',
                  'external_model_invocations': calls, 'consistency_verdict': 'not_evaluated'}
        write_json(args.output / 'status.json', status)
        write_json(args.output / 'auto-triage.json', triage_failure(status))
        print(json.dumps(status)); return 2


if __name__ == '__main__': raise SystemExit(main())
