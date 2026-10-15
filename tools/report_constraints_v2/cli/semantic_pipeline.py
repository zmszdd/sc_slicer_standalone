"""Report -> grounded core elements -> candidate formulas -> automatic acceptance.

Offline by default. DeepSeek extraction is consent-gated and first runs a mandatory
input-sufficiency call; ready reports then use two P/I/V/formalization calls.
No slicer invocation, code binding, formula repair or report-truth classification.

DeepSeek 连接与模型通路（白名单、端点、密钥、解码参数）唯一定义于
lib/deepseek.py；opencode 通道回退模型见本文件 configured_model()。
"""
import argparse
import copy
import functools
import json
from lib.salvage import check_numeric_plan, check_address_plan
from pathlib import Path
import subprocess

from lib import report_only as r
from lib.deepseek import (DEFAULT_DEEPSEEK_MODEL, DEEPSEEK_MODELS, TransientModelError,
                      extract_deepseek, load_deepseek_key, proxy_in_effect,
                      proxy_policy)
from lib.semantic_core import (NORMALIZE, compile_bundle, normalize_readiness,
                           normalize_truth_binding, validate_elements)
from prompts.registry import (DEFAULT_VERSION, PROMPT_MODULES, SELECTABLE_VERSIONS,
                              features_for)
from prompts.active import resolve_prompt_set
from prompts.current import FAITHFULNESS_AUDIT_PROMPT
from lib.ingest import build_catalog, hydrate_elements, hydrate_formalization
from lib.plan_synthesizer import (check_distinct_p_predicates, classified_relation_alignment,
                              faithfulness_mismatches, intent_scope_review,
                              predicate_binding_symbols, relax_unsupported_relation,
                              placeholder_predicate_review,
                              requirement_source_review, structured_unresolved_review,
                              symbol_table_review, synthesize_id_formalization,
                              validate_faithfulness_verdict)
from lib.solving import solve_queries
from lib.solving import attach_review
from lib.solving import from_bundle as triage_bundle, from_failure as triage_failure
from lib.salvage import (example_pinning_review, mixed_unit_scaling_review,
                                normalize_attack_step_roles,
                                normalize_element_ids, drop_unused_invalid_symbols)
from lib.stage3_consistency import binding_contract
from lib.ingest import PROMPT as READINESS_PROMPT, model_payload, validate_readiness


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



def _numeric_p_hint(message):
    # The gate's message names the offending source and literals
    # (": <source_id> states 50, 100"); surface it so the retry repairs
    # THAT source instead of guessing (final_holdout_02: Kinetiq).
    detail = message.split(': ', 1)[1] if ': ' in message else ''
    pointer = f'Failing source: {detail}\n' if detail else ''
    return ('\nRETRY FEEDBACK: Include EVERY extracted P/assumption source ID '
            'in precondition_terms. If its statement contains an explicit '
            'numeric comparison, its OWN P predicate must encode the SAME '
            'literal and comparison direction, written as '
            'right:{"const":N} with N a literal that appears in the cited '
            'report text. Do not use a Boolean placeholder or weaker '
            'threshold. Do not compute the constant: a bound stated as a '
            '12-bit width or bit range binds to 12 (the text literal), '
            'never 4096 or a mask; an enum bound like type == 1 uses '
            '{"const":1}, never a named symbol for the constant. For 2^N '
            '+/- K use the exact power_of_two/offset operand, never '
            'floating point or scientific notation. If the text has no '
            'plain numeric literal for the bound, record it in unresolved '
            'instead of inventing a constant. If the statement compares two '
            'report quantities (balances exceed reserves), encode that '
            'symbol-vs-symbol comparison directly with NO constant: a '
            'constant absent from the cited text is invented even when '
            'semantically equivalent. Keep report facts unchanged.\n'
            + pointer)


def _type_unit_hint(message):
    # The checker's message names the operator and BOTH operand types
    # (": eq on int HYPE and int kHYPE"); surface it so the retry rewrites
    # THAT comparison instead of guessing (blind-batch_02: Kinetiq retry-1
    # changed symbols blindly and missed the mismatching comparison).
    detail = message.split(': ', 1)[1] if ': ' in message else ''
    pointer = f'Failing comparison: {detail}\n' if detail else ''
    return ('\nRETRY FEEDBACK: The selected quantities have incompatible '
            'units. Do not relabel units or define a quotient with '
            'multiplication. Keep intent_id and impact_ids fixed. For '
            'share/price proportionality, express the invariant as the '
            'cross-multiplied relation (for example shares_received * '
            'total_assets <= deposit_amount * total_supply) and never '
            'define a derived symbol whose product units are then compared '
            'against a plain share quantity. When the report itself states '
            'a formula that mixes units around an explicit scaling '
            'constant (for example "pending * 1e12 < totalShares"), inline '
            'that constant as {"const": N} inside the mul -- a literal '
            'operand inherits the other operand\'s unit, so no product '
            'unit is formed -- and declare both compared quantities with '
            'one shared raw unit; never declare a unit-carrying scaling '
            'symbol, because symbol-times-symbol always produces a joined '
            'product unit that no plain unit can equal. The numeric gate '
            'checks each P predicate against its own cited statement: '
            'attach the scaled relation to the term whose statement '
            'literally states the constant, and when no cited statement '
            'states it, record the fact in unresolved instead of forcing '
            'it. If the current relation_class '
            'cannot express the report relation with add/sub/mul and '
            'matching units, this bounded repair may choose a more '
            'suitable relation_class and its compiler-fixed template, or '
            'return blocking unsupported_relation.\n'
            + pointer)


#: 受限修复错误的单一注册表：每行 = (matcher, mutable_fields, retry_hint)。
#: matcher 为精确字符串、精确字符串元组（任一命中）、('prefix', s) 或
#: ('contains', s)。mutable_fields 是本次重试允许改动的最小 top-level 计划
#: 区域；retry_hint 是固定反馈文本（或 message -> str 的可调用），None 表示
#: 落到默认。同一错误家族的"哪些字段可改"与"重试怎么反馈"**只能**在这里
#: 同表维护——历史上它们是两张平行表，靠人工保持同步。
_PATTERN_ONLY = ('pattern',)
_CANCELLABLE = ('pattern', 'symbols', 'derived_definitions', 'unresolved', 'limitations')
_DERIVED_DEFS = ('derived_definitions', 'symbols')
#: Numeric-gate repairs routinely need to rewrite the failing comparison
#: predicate itself (restore an explicit bound the first attempt hid),
#: so pattern joins the mutable set here.
_NUMERIC_P = ('precondition_ids', 'precondition_terms', 'symbols',
              'assumptions', 'pattern', 'unresolved', 'limitations')
_IMPACT_CORE = ('impact_ids', 'symbols', 'derived_definitions', 'pattern',
                'unresolved', 'limitations')
_IMPACT_CONTEXT = ('impact_context_terms', 'symbols', 'pattern',
                   'unresolved', 'limitations')
_TYPE_UNIT = ('relation_class', 'symbols', 'precondition_terms',
              'derived_definitions', 'impact_context_terms', 'pattern',
              'assumptions', 'unresolved', 'limitations')
_SYMBOL_SCOPE = ('symbols', 'precondition_terms', 'derived_definitions',
                 'pattern', 'unresolved', 'limitations')
#: Preserve semantic selection/classification even for an unfamiliar local
#: structural error. A later fresh run, rather than a repair, may reconsider it.
_SEMANTIC_SCOPE = ('symbols', 'precondition_terms', 'derived_definitions', 'pattern',
                   'assumptions', 'unresolved', 'limitations')
_FORMAL_DEFAULT_HINT = (
    '\nRETRY FEEDBACK: Previous plan failed deterministic schema/type checks. '
    'Return one valid JSON plan, following the exact schema. '
    'Do not invent report facts.\n')


def _audit_mismatch_hint(message):
    """S17: the one hint that embeds model-derived text, deliberately.

    The verdict rows are the pipeline's own validated artifact (enum verdict
    plus a one-line reason), and the repair loop needs the named defect to
    act on -- the same reason ``local_repair_payload`` already ships
    ``repair_error``.  Free prose from providers never travels here.
    """
    return ('\nRETRY FEEDBACK: A semantic cross-audit judged part of the plan '
            'unfaithful to its cited report statement. Rewrite the affected '
            'P predicate so its direction, constants, and symbols encode what '
            'the statement itself asserts; if the statement cannot be encoded '
            'faithfully, move that fact to assumptions or unresolved instead '
            'of inverting it. Keep every other report fact unchanged.\n'
            'Audit findings: ' + message + '\n')

_FORMAL_ERROR_RULES = (
    (('missing plan quantity unit'), _SYMBOL_SCOPE,
     '\nRETRY FEEDBACK: Every int symbol needs a nonempty unit string. '
     'For a unitless encoded number use "dimensionless"; '
     'only bool/address symbols use null. Keep report semantics unchanged.\n'),
    ('unknown synthesis pattern', _SEMANTIC_SCOPE,
     '\nRETRY FEEDBACK: pattern must be one object with a top-level '
     '"kind" field, e.g. {"kind":"condition_forbids_effect", '
     '"condition":..., "effect":...}. Never nest it in another '
     '"pattern" object. Keep report semantics unchanged.\n'),
    ('invalid condition pattern', _SEMANTIC_SCOPE,
     '\nRETRY FEEDBACK: For kind="condition_forbids_effect" or '
     '"condition_requires_effect", pattern must contain EXACTLY '
     'kind, condition, effect. condition and effect must each be a '
     'complete predicate object. Do not omit either field. '
     'Keep report semantics unchanged.\n'),
    ('invalid compound predicate', _SEMANTIC_SCOPE,
     '\nRETRY FEEDBACK: all_of/any_of take a terms list of 2..8 complete '
     'predicates (nesting depth at most 4). The report, not the schema, sets '
     'the count: encode every selected fact, and when more than 8 simultaneous '
     'qualifiers are required, nest one compound inside another instead of '
     'dropping a fact. Keep report semantics unchanged.\n'),
    ('invalid plan symbol', _SYMBOL_SCOPE,
     '\nRETRY FEEDBACK: Every symbols key must be lowercase snake_case '
     '(e.g. epoch_duration_seconds); every symbol object must have '
     'exactly sort, unit, meaning, checkpoint, entity_ids, source_ids. '
     'Use the same renamed key in predicates. Keep report semantics unchanged.\n'),
    (('invalid truth binding', 'truth binding requires bool symbol'), _SYMBOL_SCOPE,
     '\nRETRY FEEDBACK: Audit every predicate reference before returning. '
     'Every referenced symbol must be declared in symbols. A '
     'kind="truth" predicate may reference ONLY a declared sort:"bool" '
     'symbol and value must be true or false. For int/address symbols use '
     'comparison or relation with an explicit right operand; never treat '
     'an integer/address as Boolean. If the cited report fact explicitly '
     'says an operation/event occurred, declare a separate bool occurrence '
     'symbol grounded by that source; otherwise omit that P selection '
     'rather than inventing a trigger. Keep report semantics unchanged.\n'),
    (('unknown predicate symbol', 'unknown comparison symbol'), _SYMBOL_SCOPE,
     '\nRETRY FEEDBACK: Every symbol referenced by precondition_terms or '
     'pattern must be declared in symbols with the exact required object '
     'fields. Do not refer to an undeclared fair/expected/convenience '
     'variable. If the report does not ground that quantity, choose a '
     'narrower report-supported relation or mark unsupported_relation '
     'blocking. Keep report semantics unchanged.\n'),
    (('invalid quantity binding', 'invalid quantity expression'), _SYMBOL_SCOPE,
     '\nRETRY FEEDBACK: A QEXPR is symbol, integer const, exact '
     'power_of_two, or add/sub/mul with EXACTLY two args. Nest binary '
     'operations instead of returning three args. For ratios or '
     'proportional fairness, do not divide: cross-multiply both sides '
     'so their units match. Pattern slots typed as quantities take '
     'ONLY a QEXPR: kind="conservation" before/after are the conserved '
     'QUANTITIES (the invariant is before == after), never comparison '
     'predicates; an equality between two distinct observables at one '
     'checkpoint is kind="correspondence" (observed_symbol vs '
     'expected_symbol) or a relation_obligation relation, not a '
     'quantity slot. Change only the malformed expression and its '
     'directly required symbols/definitions.\n'),
    (('invalid quantity relation', 'invalid predicate binding'), _SYMBOL_SCOPE, None),
    ('relation class and pattern mismatch', _PATTERN_ONLY,
     '\nRETRY FEEDBACK: relation_class and pattern must be compatible. '
     'state_correspondence uses relation_obligation with observable '
     'equality/inequality; monotonicity uses monotonicity; conservation '
     'uses conservation or relation_obligation; value/bound/fairness/'
     'sequence/data/range relations use relation_obligation; access_control '
     'uses authorization or forbidden-effect; progress_or_liveness uses '
     'requires/forbids. Keep report semantics unchanged.\n'),
    ('fixed relation template mismatch', _PATTERN_ONLY,
     '\nRETRY FEEDBACK: Use the compiler-fixed template for the existing '
     'relation_class. monotonicity uses kind="monotonicity"; conservation '
     'uses kind="conservation"; every other class uses '
     'kind="relation_obligation" with condition and relation. Do not '
     'change relation_class, intent_id or impact_ids.\n'),
    ('expanded relation template mismatch', _PATTERN_ONLY,
     '\nRETRY FEEDBACK: Use the typed template fixed for the existing '
     'relation_class: authorization_guard, bounded_relation, '
     'monotonicity, conservation, proportional_relation, '
     'correspondence, temporal_order, required_effect, or the allowed '
     'relation_obligation fallback. Do not change intent_id or impact_ids.\n'),
    ('P predicate symbol not grounded by its own source', _NUMERIC_P,
     '\nRETRY FEEDBACK: Audit each P term separately. Every symbol used '
     'by that term must include that exact term source_id in source_ids. '
     'Add the source only when its report statement truly supports the '
     'symbol; otherwise declare a source-specific observable or remove '
     'that P selection. Do not borrow a different P source.\n'),
    ('distinct P sources reuse identical predicate', _NUMERIC_P,
     '\nRETRY FEEDBACK: Two different P sources used one predicate -- exact, '
     'mirrored (a ne b versus b ne a), or same-symbol zero bounds (x > 0 '
     'versus x != 0). Keep only the clearest source if they express one fact, '
     'or encode each source with its own report-supported observable.\n'),
    (('prefix', 'semantic faithfulness mismatch'), _SEMANTIC_SCOPE,
     _audit_mismatch_hint),
    ('P terms must cover selected preconditions exactly once', _NUMERIC_P, None),
    ('impact context symbol not grounded by its own source', _IMPACT_CONTEXT,
     '\nRETRY FEEDBACK: Every symbol in an impact_context_terms predicate '
     'must cite that exact selected impact ID. Declare an impact-specific '
     'observable for what the impact text says; add the impact ID to an '
     'existing symbol only when that impact really supports its meaning.\n'),
    (('invalid impact context terms', 'invalid impact context term',
      'impact context source not selected', 'invalid impact qualifier types'),
     _IMPACT_CONTEXT, None),
    (('prefix', 'impact qualifier missing from formal plan'), _IMPACT_CONTEXT,
     '\nRETRY FEEDBACK: impact_context_terms did not cover every explicit '
     'qualifier type detected in the selected impact. The repair_error '
     'lists the missing temporal/threshold/state types by impact ID. Add '
     'report-grounded predicates for those exact types without replacing '
     'the selected impact or intent.\n'),
    (('prefix', 'type/unit mismatch'), _TYPE_UNIT, _type_unit_hint),
    (('bounded relation type/unit mismatch', 'correspondence type/unit mismatch',
      'proportional relation type/unit mismatch'), _TYPE_UNIT, _type_unit_hint),
    ('relation repeats cancellable observable on both sides', _CANCELLABLE,
     '\nRETRY FEEDBACK: The relation repeats the same unknown '
     'multiplicative observable on both sides, making the intended '
     'comparison vacuous or sign-dependent. For proportional fairness, '
     'compare distinct actual and full/expected quantities, e.g. '
     'actual_reward * total_duration versus full_reward * '
     'contributed_duration. Preserve the selected intent and impact.\n'),
    ('referenced derived symbol lacks definition', _DERIVED_DEFS,
     '\nRETRY FEEDBACK: Every referenced symbol whose checkpoint starts '
     'with "derived" needs exactly one derived_definitions entry. Define '
     'it with a report-grounded add/sub/mul quantity expression and cite '
     'selected source IDs. Do not replace it with an unconstrained name.\n'),
    (('contains', 'derived definition'), _DERIVED_DEFS,
     '\nRETRY FEEDBACK: Repair only derived_definitions and, if required, '
     'the corresponding symbol metadata. Definitions must target declared '
     'int symbols, be acyclic, preserve units, and use report-grounded '
     'base symbols and selected source IDs.\n'),
    ('local repair made no change', _SEMANTIC_SCOPE,
     '\nRETRY FEEDBACK: The previous repair attempt returned a plan '
     'byte-identical to previous_plan, which repairs nothing. Produce a '
     'concrete, visible difference inside mutable_top_level_fields that '
     'answers repair_error: rewrite the offending predicate, term, or '
     'definition -- not its wording elsewhere. If you cannot repair it, '
     'change the plan so the unrepairable part is honestly relocated '
     '(move the fact to assumptions, or add a blocking unresolved item) '
     'instead of resubmitting the same object.\n'),
    (('prefix', 'local repair '), _SEMANTIC_SCOPE,
     '\nRETRY FEEDBACK: This is a local repair. Return the complete plan '
     'but change only mutable_top_level_fields. All frozen fields must '
     'remain structurally identical to previous_plan.\n'),
    (('prefix', 'numeric P '), _NUMERIC_P, _numeric_p_hint),
    (('prefix', 'zero-address '), _SEMANTIC_SCOPE,
     '\nRETRY FEEDBACK: A report claim explicitly mentions '
     'address(0)/zero address. Declare zero_address and the relevant '
     'observable recipient/owner address as sort:address symbols. '
     'Use a comparison predicate eq/ne with '
     'right:{"symbol":"zero_address"} for that P, I condition, '
     'or direct ownership V effect. Do not use a Boolean placeholder. '
     'Keep report facts unchanged.\n'),
    ('P predicate symbol not grounded by selected preconditions', _NUMERIC_P,
     '\nRETRY FEEDBACK: A P predicate used a symbol not grounded by that '
     'P set. Every symbol referenced by a P predicate must include '
     'at least one selected precondition_id in its source_ids. Never '
     'encode a precondition as the absence/presence of the later impact. '
     'Keep report facts unchanged.\n'),
    ('trivial self-comparison predicate', _SYMBOL_SCOPE,
     '\nRETRY FEEDBACK: Never use x==x, x!=x, x<=x, x>=x or an '
     'equivalent self-comparison as P, trigger, condition, or relation. '
     'It is tautological/contradictory and does not encode a report fact. '
     'Compare distinct observable fields, or use a separately declared '
     'report-grounded bool occurrence symbol for an event/action trigger. '
     'Keep report semantics unchanged.\n'),
    ('core relation observables lack intent/impact grounding', _IMPACT_CORE,
     '\nRETRY FEEDBACK: The core relation observables must collectively '
     'cite every selected impact_id in their symbol source_ids. The '
     'selected intent already grounds the I property in fixed-plan v4; '
     'older schemas may additionally require it on an observable. First '
     'reselect, from the supplied impact statements, '
     'the ONE impact that most directly negates the selected intent; '
     'prefer a failed/passed check or mismatched observable over its '
     'downstream economic consequence. Do not use trigger-only symbols '
     'or attach unrelated IDs merely to pass. Defer impacts that do not '
     'describe the same relation. Keep relation_class/pattern compatible. '
     'Keep report facts unchanged.\n'),
)


def _match_formal_error(message, matcher):
    """matcher: 精确串 / 精确串元组（任一） / ('prefix'|'contains', 串)。"""
    if isinstance(matcher, tuple) and len(matcher) == 2 and \
            matcher[0] in ('prefix', 'contains') and isinstance(matcher[1], str):
        return message.startswith(matcher[1]) if matcher[0] == 'prefix' \
            else matcher[1] in message
    if isinstance(matcher, tuple):
        return message in matcher
    return message == matcher


def formal_repair_fields(exc):
    """Return the smallest top-level plan area allowed to change on retry."""
    message = str(exc)
    for matcher, mutable_fields, _hint in _FORMAL_ERROR_RULES:
        if _match_formal_error(message, matcher):
            return mutable_fields
    return _SEMANTIC_SCOPE


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
    message = str(exc)
    for matcher, _fields, hint in _FORMAL_ERROR_RULES:
        if _match_formal_error(message, matcher):
            return hint(message) if callable(hint) else (hint or _FORMAL_DEFAULT_HINT)
    return _FORMAL_DEFAULT_HINT


def element_retry_hint(_exc):
    """Fixed feedback avoids echoing model output or report content."""
    return ('\nRETRY FEEDBACK: Previous elements JSON failed deterministic structure '
            'or grounding checks. Return exactly the requested top-level keys; no '
            'placeholder/note keys. Include exactly one security_intent and at least '
            'one direct impact when the screened report supports them. attack_steps '
            'may reference action statements only. Use only supplied evidence IDs.\n')


def _audit_retry_feedback(_exc):
    return ('\nRETRY FEEDBACK: Previous verdict JSON failed shape or coverage '
            'validation. Return exactly {"checks":[{"source_id":ID,"verdict":'
            '"consistent"|"inverted"|"wrong_constant"|"wrong_symbol"|'
            '"other_mismatch","reason":ONE_SHORT_SENTENCE}]} covering every '
            'listed source_id exactly once.\n')


def faithfulness_audit_input(elements, plan):
    """Narrow cross-audit payload: per P source, its statement text, the
    predicate claiming to encode it, and only the meanings of the symbols
    that predicate uses.  Nothing else from the plan or report travels to
    the auditor, so the audit judges faithfulness and nothing else."""
    statements = {row['id']: row for row in elements['statements']}
    rows = []
    for term in plan['precondition_terms']:
        names = predicate_binding_symbols(term['predicate'])
        rows.append({
            'source_id': term['source_id'],
            'statement_text': statements[term['source_id']]['text'],
            'predicate': term['predicate'],
            'symbol_meanings': {name: {
                'sort': plan['symbols'][name]['sort'],
                'unit': plan['symbols'][name]['unit'],
                'meaning': plan['symbols'][name]['meaning'],
            } for name in sorted(names)},
        })
    return compact_json({
        'schema_version': 'faithfulness-audit-input/1',
        'relation_class': plan.get('relation_class'),
        'sources': rows,
    })


def request_faithfulness_audit(payload, model, output, plan, extract_fn,
                               on_attempt=None):
    """One bounded semantic cross-audit call; only format failures retry."""
    def accept(raw, call_dir, record):
        validate_faithfulness_verdict(raw, plan)
        return raw
    accepted, _ = _bounded_model_call(
        payload, FAITHFULNESS_AUDIT_PROMPT, model, output, 1,
        'faithfulness-audit', 'faithfulness-audit-attempts.json', accept,
        _audit_retry_feedback, 'accepted_for_routing', extract_fn=extract_fn,
        on_attempt=on_attempt)
    return accepted


def _bounded_model_call(payload, prompt, model, output, retries, call_prefix,
                        attempts_file, accept, retry_feedback, accepted_outcome,
                        extract_fn=None, on_attempt=None):
    """Shared scaffolding for every bounded, audited model call.

    Each attempt keeps its own artifact directory and one record in
    ``attempts_file``.  ``accept(raw, call_dir, record)`` validates the raw
    model answer (raising ValueError/KeyError/TypeError to request a retry)
    and returns the accepted value.  ``retry_feedback(exc)`` produces the
    fixed retry prompt suffix; transport/JSON failures are retryable,
    RuntimeError/OSError are not.
    """
    extract_fn = extract_fn or r.extract
    attempts = []
    feedback = ''
    for attempt in range(retries + 1):
        call_dir = output / (call_prefix if attempt == 0 else
                             f'{call_prefix}-retry-{attempt}')
        call_dir.mkdir()
        attempt_prompt = prompt + feedback
        (call_dir / 'prompt.txt').write_text(attempt_prompt + payload)
        record = {'attempt': attempt + 1, 'artifact_dir': call_dir.name}
        attempts.append(record)
        try:
            if on_attempt is not None:
                on_attempt()
            raw = extract_fn(payload, call_dir, model, attempt_prompt)
            accepted = accept(raw, call_dir, record)
            record['outcome'] = accepted_outcome
            write_json(output / attempts_file, attempts)
            return accepted, attempts
        except (json.JSONDecodeError, subprocess.TimeoutExpired,
                TransientModelError, ValueError, KeyError, TypeError) as exc:
            record.update({'outcome': 'retryable_failure',
                           'error_type': type(exc).__name__,
                           'error': ('model timeout' if isinstance(
                               exc, subprocess.TimeoutExpired) else str(exc))})
            write_json(output / attempts_file, attempts)
            if attempt == retries:
                raise
            feedback = retry_feedback(exc)
        except (RuntimeError, OSError) as exc:
            record.update({'outcome': 'non_retryable_failure',
                           'error_type': type(exc).__name__, 'error': str(exc)})
            write_json(output / attempts_file, attempts)
            raise
    raise AssertionError('unreachable')


def _readiness_retry_feedback(_exc):
    return ('\nRETRY FEEDBACK: Previous readiness answer failed '
            'deterministic JSON/schema/evidence validation. Return only '
            'the requested compact JSON using supplied evidence IDs.\n')


def request_readiness(payload, prompt, model, output, retries, catalog,
                      extract_fn=None, on_attempt=None):
    """Run the pre-extraction sufficiency gate with bounded, audited retries."""
    def accept(raw, call_dir, record):
        normalized, changes = normalize_readiness(raw)
        readiness = validate_readiness(normalized, catalog)
        if changes:
            write_json(call_dir / 'normalization-log.json', {
                'schema_version': 'stage2-normalization-log/1',
                'stage': 'input-screening', 'mode': NORMALIZE,
                'changes': changes})
            record['normalizations'] = changes
        return readiness, changes
    accepted, _ = _bounded_model_call(
        payload, prompt, model, output, retries, 'neural-input-screen',
        'readiness-attempts.json', accept, _readiness_retry_feedback,
        'accepted_for_validation', extract_fn=extract_fn, on_attempt=on_attempt)
    return accepted


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
                     validate_fn=None, on_attempt=None):
    """Bounded recovery for transport/JSON failures; preserve every attempt."""
    def accept(raw, call_dir, record):
        if validate_fn is not None:
            validate_fn(raw)
        return raw
    return _bounded_model_call(
        payload, prompt, model, output, retries, 'neural-elements',
        'element-attempts.json', accept, element_retry_hint, 'parsed_json',
        extract_fn=extract_fn, on_attempt=on_attempt)


def request_formalization(payload, prompt, model, output, retries, plan_mode,
                          elements, structured=False, extract_fn=None, attempts=None,
                          numeric_guard=False, address_guard=False,
                          mechanical_salvage=False, local_repair=False,
                          exclude_protocol_identifiers=False,
                          relax_assumptions=False, duplicate_predicate_gate=False,
                          partial_formalization=False, on_attempt=None,
                          faithfulness_audit=None, faithfulness_audit_model=None,
                          faithfulness_audit_on_attempt=None):
    """Retry malformed responses or perform a bounded, field-scoped plan repair.

    Each attempt keeps its own raw model artifacts. A rejected plan is never
    silently treated as successful. In local-repair mode, parsed plans freeze all
    unrelated top-level fields and the model receives the prior plan plus an
    explicit allow-list of fields it may change.

    When ``faithfulness_audit`` (an extract transport) is supplied, every
    candidate that passes the deterministic gates is cross-audited before
    acceptance: a non-consistent verdict becomes a retryable ValueError and
    enters the same repair loop.
    """
    extract_fn = extract_fn or r.extract
    attempts = attempts if attempts is not None else []
    feedback = ''
    repair_base = None
    mutable_fields = ()
    repair_error = None
    null_reprompts = 0
    fresh_restate = False
    attempt = 0
    while attempt <= retries:
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
        if fresh_restate:
            record['fresh_restate'] = True
            fresh_restate = False
        if local_repair and repair_base is not None:
            record.update({'repair_mode': ('bounded_semantic_replan'
                                           if 'relation_class' in mutable_fields
                                           else 'field_scoped'),
                           'mutable_top_level_fields': list(mutable_fields)})
        attempts.append(record)
        candidate = None
        try:
            if on_attempt is not None:
                on_attempt()
            candidate = extract_fn(attempt_payload, call_dir, model, attempt_prompt)
            if local_repair and repair_base is not None:
                record['changed_top_level_fields'] = validate_local_repair(
                    repair_base, candidate, mutable_fields)
            if plan_mode:
                # Boundary NORMALIZE: the model named the boolean after the
                # precondition that asserts it and only forgot to declare it.
                # The raw response stays untouched in model-claim.json.
                amended, normalized = normalize_truth_binding(candidate, elements)
                if normalized:
                    write_json(call_dir / 'normalization-log.json', {
                        'schema_version': 'stage2-normalization-log/1',
                        'stage': 'formalization', 'mode': NORMALIZE,
                        'changes': normalized})
                    record['normalizations'] = normalized
                    candidate = amended
                if mechanical_salvage:
                    candidate, repairs = drop_unused_invalid_symbols(candidate)
                    if repairs:
                        write_json(call_dir / 'mechanical-salvage.json', repairs)
                if partial_formalization:
                    # Boundary-normalize the unsupported_relation contradiction:
                    # a plan that already represents the relation as a bool
                    # symbol cannot honestly also declare it blocking.
                    candidate, relaxed = relax_unsupported_relation(candidate, elements)
                    if relaxed:
                        write_json(call_dir / 'partial-formalization.json', relaxed)
                formal = synthesize_id_formalization(candidate, elements)
                if numeric_guard:
                    check_numeric_plan(
                        candidate, elements,
                        exclude_protocol_identifiers=exclude_protocol_identifiers,
                        relax_assumptions=relax_assumptions)
                if address_guard:
                    check_address_plan(candidate, elements)
                if duplicate_predicate_gate:
                    check_distinct_p_predicates(candidate)
                if faithfulness_audit is not None and candidate.get('precondition_terms'):
                    # S17: all gates above are syntactic; this call is the only
                    # semantic check in the chain.  Artifacts nest inside this
                    # formalization attempt's directory; the run-level verdict
                    # file below is the replay artifact (batch_verify routes
                    # on it deterministically, never on a new model call).
                    verdict = request_faithfulness_audit(
                        faithfulness_audit_input(elements, candidate),
                        faithfulness_audit_model, call_dir, candidate,
                        extract_fn=faithfulness_audit,
                        on_attempt=faithfulness_audit_on_attempt)
                    mismatches = faithfulness_mismatches(verdict)
                    record['semantic_faithfulness_audit'] = {
                        'verdict_consistent': not mismatches,
                        'checks': len(verdict['checks']),
                        'mismatches': mismatches,
                    }
                    if mismatches:
                        raise ValueError('semantic faithfulness mismatch: ' + '; '.join(
                            f"{row['source_id']} {row['verdict']}: "
                            f"{row['reason'][:160]}" for row in mismatches))
                    write_json(output / 'semantic-faithfulness-audit.json', {
                        'schema_version': 'semantic-faithfulness-audit/1',
                        'checks': verdict['checks'],
                        'mismatch_count': 0,
                    })
                if structured:
                    review = structured_unresolved_review(candidate, elements)
                else:
                    review = None
            else:
                formal, review = candidate, None
            record['outcome'] = 'accepted_for_validation'
            write_json(output / 'formalization-attempts.json', attempts)
            return candidate, formal, review
        except (json.JSONDecodeError, subprocess.TimeoutExpired, TransientModelError, ValueError,
                KeyError, TypeError) as exc:
            record.update({'outcome': 'retryable_failure', 'error_type': type(exc).__name__,
                           'error': 'model timeout' if isinstance(exc, subprocess.TimeoutExpired)
                           else str(exc)})
            write_json(output / 'formalization-attempts.json', attempts)
            if attempt == retries:
                if (local_repair and null_reprompts == 0 and
                        str(exc) == 'local repair made no change'):
                    # A byte-identical resubmission is a null response: it
                    # consumed a call without producing any new content, so
                    # granting exactly one reprompt (carrying the no-change
                    # prescription) stays inside the bounded-effort contract.
                    # final_holdout_02: GTE_Perps resubmitted identically on
                    # the final attempt, and the no-change prescription could
                    # never fire because no next attempt existed.
                    # blind-batch_07 escalation: repeating the identical repair
                    # request cannot produce new content (deepseek-v4-pro
                    # resubmitted byte-identically three times), so the grant
                    # reopens the frozen decisions -- the next attempt runs as
                    # a full restatement, not another local repair.
                    null_reprompts += 1
                    retries += 1
                    record['null_repair_reprompt'] = True
                    record['fresh_restate'] = True
                    fresh_restate = True
                    repair_base = None
                else:
                    raise
            if fresh_restate:
                # Escalated null-repair reprompt: the next attempt must be a
                # full restatement, so the resubmitted candidate is NOT
                # promoted to repair_base (the promote below would otherwise
                # re-freeze the very plan the model just returned unchanged).
                feedback = (
                    '\nRETRY FEEDBACK: Your previous local repair returned the '
                    'plan byte-identically -- a null response -- so its frozen '
                    'semantic decisions are now reopened. Restate the complete '
                    'plan from the original input and genuinely change the '
                    'fields involved in this previously reported failure: ' +
                    (str(repair_error) if repair_error is not None else
                     'the stated deterministic validation failure') + '\n')
            else:
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
                    if str(exc) != 'local repair made no change':
                        repair_error = exc
                    # A null repair must not replace the substantive error: the
                    # next repair request still needs the original defect (the
                    # no-change prescription itself travels via the retry hint).
                    # blind-batch-02 Kinetiq: the numeric error was overwritten by
                    # "local repair made no change" on retry 1, so retry 2 told
                    # the model to "answer repair_error" with no defect named.
                feedback = formal_retry_hint(exc)
        except (RuntimeError, OSError) as exc:
            record.update({'outcome': 'non_retryable_failure',
                           'error_type': type(exc).__name__, 'error': str(exc)})
            write_json(output / 'formalization-attempts.json', attempts)
            raise
        attempt += 1
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
    parser.add_argument('--deepseek-proxy', metavar='POLICY', default='environment',
                        help='official-transport proxy policy (--provider deepseek '
                             'only, ignored otherwise): "environment" honours the '
                             'ambient *_proxy variables, "direct" ignores them, or '
                             'give an http(s):// URL. main.py injects "direct"')
    parser.add_argument('--audit-provider', choices=('pipeline', 'opencode', 'deepseek'),
                        default='pipeline',
                        help='transport for the S17 semantic faithfulness cross-audit '
                             'call (live prompt only): "pipeline" reuses the main '
                             'provider, or override to audit one family with another')
    parser.add_argument('--audit-model',
                        help='model id for the faithfulness audit call; defaults to '
                             'the chosen audit provider\'s default model')
    parser.add_argument('--evidence-mode', choices=('ids', 'quotes'), default='ids',
                        help='neural mode defaults to source IDs; quotes is legacy compatibility')
    parser.add_argument('--formalization-scope', choices=('core', 'full'), default='core',
                        help='neural request scope: core formulas by default; deferred impacts remain review warnings')
    parser.add_argument('--formal-retries', type=int, choices=(0, 1, 2), default=0,
                        help='up to two audited retries for second-step empty/invalid JSON, timeout, or invalid plan')
    parser.add_argument('--element-retries', type=int, choices=(0, 1), default=0,
                        help='optional one retry for first-step timeout or invalid JSON; preserves both attempts')
    parser.add_argument('--readiness-retries', type=int, choices=(0, 1), default=0,
                        help='optional one audited retry for the pre-extraction sufficiency gate')
    parser.add_argument('--lean-formal-input', action='store_true',
                        help='v3.12 core plan: send statement text/IDs without duplicated evidence catalog')
    parser.add_argument('--mechanical-salvage', action='store_true',
                        help='opt-in: lowercase unambiguous IDs and drop unused symbols with empty entity bindings')
    parser.add_argument('--continue-on-review', action='store_true',
                        help='exit successfully when core P/I/V is complete; keep review warnings and never certify semantic truth')
    parser.add_argument('--prompt-version', choices=SELECTABLE_VERSIONS,
                        default=DEFAULT_VERSION)
    parser.add_argument('--claim-verdict', choices=('legacy', 'signals'),
                        default='legacy',
                        help='legacy: report ambiguities/limitations and non-asserted '
                             'modality veto every claim; signals: record them as '
                             'informational fields instead (main.py run/batch inject '
                             'signals)')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    # Feature decisions are resolved once and recorded in provenance so that
    # offline replay of a run never depends on the current live prompt toggles.
    features = features_for(args.prompt_version)
    if features['plan_synthesis'] and (
            args.evidence_mode != 'ids' or args.formalization_scope != 'core'):
        parser.error('plan-synthesis prompts support --evidence-mode ids --formalization-scope core only')
    if args.extract and args.formalize_only:
        parser.error('choose full extraction or formalize-only, not both')
    if args.formal_retries and not (args.extract or args.formalize_only):
        parser.error('--formal-retries requires neural formalization')
    if args.element_retries and not args.extract:
        parser.error('--element-retries requires --extract')
    if args.readiness_retries and not (args.extract and args.provider == 'deepseek'):
        parser.error('--readiness-retries requires DeepSeek full extraction')
    if args.lean_formal_input and (args.elements_only or
                                  not (args.extract or args.formalize_only) or
                                  not features['lean_formal_input'] or
                                  args.evidence_mode != 'ids'):
        parser.error('--lean-formal-input requires neural ID mode with a lean-input prompt version')
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
            if args.model and args.model not in DEEPSEEK_MODELS:
                parser.error('unsupported official DeepSeek model identifier')
            try:
                proxy_policy(args.deepseek_proxy)
            except ValueError as exc:
                parser.error(str(exc))
            try:
                load_deepseek_key()
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
                           'prompt_version': args.prompt_version,
                           'prompt_features': features})
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
                                                            if features['plan_synthesis']
                                                            else 'model_full_formalization'),
                               'reference_answers_provided_to_model': False})
            model = args.model or (DEFAULT_DEEPSEEK_MODEL if args.provider == 'deepseek'
                                   else configured_model())
            # partial keeps the three call sites' positional arity intact while
            # pinning the transport switch; tests patch deepseek.extract_deepseek
            # and their fakes must therefore accept the extra keyword.
            extract_fn = (functools.partial(extract_deepseek,
                                            proxy=args.deepseek_proxy)
                          if args.provider == 'deepseek' else r.extract)
            # S17: the cross-audit call is independently parameterizable so a
            # different model family can audit the generator (build phase:
            # GLM auditing DeepSeek; production: both DeepSeek, disclosed).
            audit_extract_fn, audit_model = None, None
            if features['semantic_faithfulness_audit']:
                audit_provider = (args.provider if args.audit_provider == 'pipeline'
                                  else args.audit_provider)
                audit_model = (args.audit_model or
                               (DEFAULT_DEEPSEEK_MODEL if audit_provider == 'deepseek'
                                else configured_model()))
                if (audit_provider == 'deepseek' and
                        audit_model not in DEEPSEEK_MODELS):
                    raise ValueError('unsupported audit model for deepseek transport')
                audit_extract_fn = (functools.partial(extract_deepseek,
                                                      proxy=args.deepseek_proxy)
                                    if audit_provider == 'deepseek' else r.extract)
                provenance.update({'audit_provider': audit_provider,
                                   'audit_model': audit_model})
            provenance.update({'model_provider': args.provider, 'model_name': model})
            if args.provider == 'deepseek':
                provenance['deepseek_proxy_policy'] = args.deepseek_proxy
                endpoint = proxy_in_effect(args.deepseek_proxy)
                if endpoint:
                    provenance['deepseek_proxy_endpoint'] = endpoint
            resolved_prompts = resolve_prompt_set(
                args.prompt_version, args.evidence_mode, args.formalization_scope)
            provenance.update({
                'prompt_resolution': 'prompts.active/1',
                'requested_evidence_mode': args.evidence_mode,
                'element_prompt_sha256': resolved_prompts.sha256('element'),
                'formal_prompt_sha256': resolved_prompts.sha256('formal'),
            })
            # Snapshot the exact prompt text into the run directory so offline
            # replay never has to re-resolve an editable live prompt.
            (args.output / 'prompt-element.txt').write_text(
                resolved_prompts.element_prompt)
            (args.output / 'prompt-formal.txt').write_text(
                resolved_prompts.formal_prompt)
        provenance['claim_verdict_policy'] = (
            'signals-v2' if args.claim_verdict == 'signals' else 'legacy')
        provenance['acceptance_policy_version'] = 'complete-piv-v1'
        write_json(args.output / 'provenance.json', provenance)
        (args.output / 'original-report').write_bytes(raw)
        (args.output / 'extraction-input.txt').write_text(text)
        catalog = build_catalog(text)
        write_json(args.output / 'evidence-catalog.json', catalog)

        def record_model_attempt():
            nonlocal calls
            calls += 1
            provenance['external_model_invocations'] = calls
            write_json(args.output / 'provenance.json', provenance)

        if args.extract and args.provider == 'deepseek':
            # Mandatory semantic input gate for the supported production path.
            # It sees only numbered report prose and runs before P/I/V extraction.
            screen_payload = model_payload(catalog)
            readiness, normalized = request_readiness(
                screen_payload, READINESS_PROMPT, model, args.output,
                args.readiness_retries, catalog, extract_fn=extract_fn,
                on_attempt=record_model_attempt)
            if normalized:
                provenance['input_screening_normalizations'] = normalized
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
            elements_raw, _ = request_elements(
                payload, prompt, model, args.output, args.element_retries,
                extract_fn=extract_fn,
                validate_fn=(lambda candidate: validate_core_element_candidate(
                    candidate, catalog, text,
                    normalize_steps=features['step_normalization'],
                    normalize_ids=features['id_normalization'],
                    require_core_counts=features['core_count'],
                    max_core_impacts=(4 if features['relation_alignment']
                                      else 2))
                    if args.evidence_mode == 'ids' else None),
                on_attempt=record_model_attempt)
        else:
            elements_raw = json.loads(args.elements.read_text())
        element_normalizations = []
        if features['id_normalization']:
            elements_raw, id_normalizations = normalize_element_ids(elements_raw)
            element_normalizations.extend(id_normalizations)
        if features['step_normalization']:
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
                               if features['referenced_catalog'] else None)
                    formal_input = {'elements': elements_raw,
                                    'evidence_catalog': model_catalog(catalog, allowed)}
                if (not args.lean_formal_input and
                        features['allowed_statement_ids']):
                    formal_input['allowed_statement_ids'] = allowed_statement_ids(elements_raw)
                payload = compact_json(formal_input)
            else:
                payload = compact_json({'elements': elements, 'report_prose': text})
            prompt = resolved_prompts.formal_prompt
            plan_mode = features['plan_synthesis']
            attempts = []
            model_candidate, formal_raw, unresolved_review = request_formalization(
                payload, prompt, model, args.output, args.formal_retries, plan_mode,
                elements_raw,
                features['structured_unresolved'],
                numeric_guard=features['numeric_guard'],
                address_guard=features['address_guard'],
                extract_fn=extract_fn, attempts=attempts,
                mechanical_salvage=args.mechanical_salvage,
                local_repair=features['local_repair'],
                exclude_protocol_identifiers=features['protocol_identifier_exclusion'],
                relax_assumptions=features['assumption_numeric_relief'],
                duplicate_predicate_gate=features['duplicate_predicate_gate'],
                partial_formalization=features['partial_formalization'],
                on_attempt=record_model_attempt,
                faithfulness_audit=audit_extract_fn,
                faithfulness_audit_model=audit_model,
                faithfulness_audit_on_attempt=record_model_attempt)
            if plan_mode:
                write_json(args.output / 'formal-plan.json', model_candidate)
                if features['relation_alignment']:
                    write_json(args.output / 'relation-alignment.json',
                               classified_relation_alignment(model_candidate, elements_raw))
                if features['requirement_source_review']:
                    write_json(args.output / 'requirement-source-review.json',
                               requirement_source_review(elements_raw, model_candidate))
                if features['intent_scope_review']:
                    write_json(args.output / 'intent-scope-review.json',
                               intent_scope_review(model_candidate, elements_raw))
                if features['example_pinning_review']:
                    write_json(args.output / 'example-pinning-review.json',
                               example_pinning_review(model_candidate, elements_raw))
                if features['placeholder_predicate_review']:
                    write_json(args.output / 'placeholder-predicate-review.json',
                               placeholder_predicate_review(elements_raw,
                                                            model_candidate))
                if features['mixed_unit_scaling_review']:
                    write_json(args.output / 'mixed-unit-scaling-review.json',
                               mixed_unit_scaling_review(model_candidate,
                                                         elements_raw))
                if features['symbol_table_review']:
                    write_json(args.output / 'symbol-table-review.json',
                               symbol_table_review(model_candidate))
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
                                strict_piv=features['strict_piv'],
                                verdict_v2=args.claim_verdict == 'signals',
                                require_complete_piv=True)
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
                                                               'P AND T AND V', 'P AND T AND NOT V'],
                                 'binding_contract': binding_contract(formal, original)})
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
        # semantic-live-5: advisory reviews are referenced the same way as the
        # unresolved review -- hash-chained into the interface so tampering
        # with them after the fact breaks verify.
        for name in ('requirement-source-review.json', 'intent-scope-review.json',
                     'placeholder-predicate-review.json',
                     'semantic-faithfulness-audit.json',
                     'mixed-unit-scaling-review.json', 'symbol-table-review.json'):
            if (args.output / name).is_file():
                interface[name.replace('-', '_').removesuffix('.json') + '_path'] = name
                interface[name.replace('-', '_').removesuffix('.json') + '_sha256'] = \
                    r.sha((args.output / name).read_bytes())
        interface['stage3_feedback_command'] = 'python main.py stage3-feedback <run-dir> --feedback <feedback.json>'
        write_json(args.output / 'stage3-spec.json', interface)
        status = {key: bundle[key] for key in ('core_formalization_status', 'acceptance_status',
                                              'external_model_invocations', 'consistency_verdict')}
        status.update({'stage2_can_continue': triage['stage2_can_continue'],
                       'continuation_policy': 'warn_and_continue' if args.continue_on_review else 'strict_exit',
                       'warnings': triage['reasons'],
                       'continuation_blockers': triage['continuation_blockers']})
        write_json(args.output / 'status.json', status)
        print(json.dumps(status))
        return 0 if (triage['route'] == 'candidate' or
                     args.continue_on_review and triage['stage2_can_continue']) else 2
    except (ValueError, KeyError, TypeError, RuntimeError, OSError, subprocess.TimeoutExpired) as exc:
        status = {'core_formalization_status': 'failed', 'acceptance_status': 'rejected',
                  'error_type': type(exc).__name__, 'error': str(exc) if not isinstance(exc, subprocess.TimeoutExpired) else 'model timeout',
                  'external_model_invocations': calls, 'consistency_verdict': 'not_evaluated'}
        write_json(args.output / 'status.json', status)
        write_json(args.output / 'auto-triage.json', triage_failure(status))
        print(json.dumps(status)); return 2


if __name__ == '__main__': raise SystemExit(main())
