"""Report -> grounded impacts -> P/I/V formulas -> generated fidelity review.

Offline by default. DeepSeek extraction is consent-gated and first runs a mandatory
input-sufficiency call; ready reports then extract evidence-grounded elements and
formalize each impact. A generated semantic audit checks source translation and
report-supported P/I/V relationships. No slicer invocation, code binding, or report-truth
classification. Formula repair is limited to one field-scoped attempt.

DeepSeek 连接与模型通路（白名单、端点、密钥、解码参数）唯一定义于
lib/deepseek.py；opencode 通道回退模型见本文件 configured_model()。
"""
import argparse
import copy
import functools
import json
import re
from lib.salvage import check_numeric_plan, check_address_plan
from pathlib import Path
import subprocess

from lib import report_only as r
from lib.deepseek import (DEFAULT_DEEPSEEK_MODEL, DEEPSEEK_MODELS, TransientModelError,
                      extract_deepseek, load_deepseek_key, proxy_in_effect,
                      proxy_policy)
from lib.semantic_core import (NORMALIZE, compile_bundle, normalize_readiness,
                           impact_claim_set, normalize_truth_binding, symbols_for_claim,
                           validate_elements)
from prompts.registry import (DEFAULT_VERSION, PROMPT_MODULES, SELECTABLE_VERSIONS,
                              features_for)
from prompts.active import resolve_prompt_set
from prompts.current import (FAITHFULNESS_AUDIT_PROMPT,
                             IMPACT_APPLICABILITY_PROMPT,
                             IMPACT_INVENTORY_PROMPT)
from lib.ingest import build_catalog, hydrate_elements, hydrate_formalization
from lib.impact_inventory import (MAX_IMPACTS, merge_impact_inventory,
                                  validate_impact_inventory)
from lib.plan_synthesizer import (check_distinct_p_predicates, classified_relation_alignment,
                              faithfulness_mismatches, faithfulness_repair_mismatches,
                              faithfulness_status, intent_scope_review,
                              predicate_binding_symbols, relax_unsupported_relation,
                              placeholder_predicate_review,
                              reject_vacuous_safety,
                              requirement_source_review, structured_unresolved_review,
                              symbol_table_review, synthesize_id_formalization,
                              validate_faithfulness_verdict)
from lib.solving import solve_queries
from lib.multi_impact import (claim_id_for_impact,
                              claim_id_for_impact_intent,
                              apply_multi_intent_coverage,
                              impact_intent_key,
                              merge_claim_formalizations)
from lib.impact_cards import (APPLICABILITY_SCHEMA_VERSION,
                              applicability_by_impact, applicability_payload,
                              build_impact_card,
                              explicit_intent_ids, validate_applicability,
                              target_elements, target_formal_input)
from lib.solving import attach_review
from lib.solving import from_bundle as triage_bundle, from_failure as triage_failure
from lib.salvage import (example_pinning_review, mixed_unit_scaling_review,
                                merge_appended_relationship_trace,
                                normalize_attack_step_roles,
                                normalize_element_ids, drop_unused_invalid_symbols)
from lib.stage3_consistency import binding_contract
from lib.ingest import (PROMPT as READINESS_PROMPT, explicit_impact_evidence_ids,
                        model_payload, validate_impact_evidence,
                        validate_readiness)


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def stage2_assessment(readiness=None, bundle=None, elements=None,
                      eligible_impact_ids=None,
                      impact_formalization_records=None):
    """Separate report narrative sufficiency from the observed rule result.

    A ready input only means the report has enough narrative evidence to try
    formalization. It does not predict that the current generator can produce
    every P/I/V rule. Keep incomplete impacts explicit for later review.
    """
    if readiness is None:
        narrative = {'status': 'not_assessed', 'missing_dimensions': [],
                     'summary': 'Narrative sufficiency was not assessed.'}
    else:
        narrative = {
            'status': ('sufficient' if readiness.get('decision') == 'ready'
                       else 'insufficient'),
            'missing_dimensions': list(readiness.get('missing_dimensions', [])),
            'summary': readiness.get('summary', ''),
        }

    if eligible_impact_ids is not None:
        eligible_ids = list(dict.fromkeys(eligible_impact_ids))
        if bundle is None:
            pending = [
                {'impact_id': impact_id, 'status': 'not_attempted',
                 'reason': 'Complete P/I/V source evidence is eligible; '
                           'rule formalization was not attempted.'}
                for impact_id in eligible_ids
            ]
            return {
                'schema_version': 'stage2-assessment/2',
                'narrative_sufficiency': narrative,
                'rule_formalization': {
                    'status': 'not_attempted',
                    'denominator_policy': 'complete_report_supported_piv_only',
                    'eligibility_basis': 'selected_evidence_backed_piv_sources',
                    'eligible_complete_piv_impact_ids': eligible_ids,
                    'eligible_complete_piv_count': len(eligible_ids),
                    'formalized_complete_piv_count': 0,
                    'formalization_rate': None,
                    'impact_count': len(eligible_ids),
                    'formalized_impact_count': 0,
                    'pending_impacts': pending,
                },
            }

        coverage = bundle.get('report_impact_coverage', [])
        coverage_by_id = {row.get('impact_id'): row for row in coverage
                          if row.get('impact_id')}
        limitations = bundle.get('formalization_limitations_declared', [])
        omitted_reasons = {}
        for row in coverage:
            impact_id = row.get('impact_id')
            if not impact_id:
                continue
            prefix = impact_id + ': '
            note = next((item for item in limitations
                         if isinstance(item, str) and item.startswith(prefix)), None)
            if note is not None:
                omitted_reasons[impact_id] = note[len(prefix):]
        formalized = sum(
            coverage_by_id.get(impact_id, {}).get('status') == 'formalized'
            for impact_id in eligible_ids)
        partial = sum(
            coverage_by_id.get(impact_id, {}).get('status') == 'partial'
            for impact_id in eligible_ids)
        if not eligible_ids:
            result = 'not_applicable'
        elif formalized == len(eligible_ids):
            result = 'complete'
        elif formalized or partial:
            result = 'partial'
        else:
            result = 'none'
        pending = []
        for impact_id in eligible_ids:
            row = coverage_by_id.get(impact_id)
            if row is not None and row.get('status') == 'formalized':
                continue
            pending.append({
                'impact_id': impact_id,
                'status': row.get('status') if row else 'unformalized',
                'reason': ((row or {}).get('reason') or
                           omitted_reasons.get(impact_id) or
                           'Complete P/I/V sources were selected, but no complete '
                           'rule was produced.'),
            })
        assessment = {
            'schema_version': 'stage2-assessment/2',
            'narrative_sufficiency': narrative,
            'rule_formalization': {
                'status': result,
                'denominator_policy': 'complete_report_supported_piv_only',
                'eligibility_basis': 'selected_evidence_backed_piv_sources',
                'eligible_complete_piv_impact_ids': eligible_ids,
                'eligible_complete_piv_count': len(eligible_ids),
                'formalized_complete_piv_count': formalized,
                'formalization_rate': (formalized / len(eligible_ids)
                                       if eligible_ids else None),
                # Compatibility aliases now use the eligible denominator only.
                'impact_count': len(eligible_ids),
                'formalized_impact_count': formalized,
                'partial_impact_count': partial,
                'candidate_acceptance_status': bundle.get('acceptance_status'),
                'pending_impacts': pending,
            },
        }
        if impact_formalization_records is not None:
            pair_mode = any('intent_id' in row
                            for row in impact_formalization_records)
            if pair_mode:
                records = {}
                for row in impact_formalization_records:
                    if row.get('impact_id') in set(eligible_ids):
                        records.setdefault(row['impact_id'], []).append(row)
            else:
                records = {row.get('impact_id'): [row]
                           for row in impact_formalization_records
                           if row.get('impact_id') in set(eligible_ids)}
            failure_counts = {}
            i_source_pair_count = 0
            generated = set()
            latest_audit = {}
            for impact_id in eligible_ids:
                rows = records.get(impact_id, [])
                if pair_mode:
                    rows = [row for row in rows if row.get('intent_id')]
                    i_source_pair_count += len(rows)
                for row in rows:
                    key = ((impact_id, row.get('intent_id')) if pair_mode
                           else impact_id)
                    family = row.get('failure_family')
                    if family:
                        failure_counts[family] = failure_counts.get(family, 0) + 1
                    for attempt in row.get('attempts', []):
                        if attempt.get('rule_generated'):
                            generated.add(key)
                    last_attempt = (row.get('attempts') or [None])[-1]
                    if last_attempt and last_attempt.get('rule_generated'):
                        audit = last_attempt.get('semantic_faithfulness_audit')
                        if audit is not None:
                            latest_audit[key] = audit
            fidelity_passed = sum(
                audit.get('verdict_consistent') is True
                for audit in latest_audit.values())
            fidelity_statuses = {}
            for key, audit in latest_audit.items():
                if audit.get('fidelity_status'):
                    fidelity_statuses[key] = audit['fidelity_status']
                elif audit.get('status') == 'unavailable':
                    fidelity_statuses[key] = 'unavailable'
                else:
                    # Historical snapshots predate the needs_review category.
                    fidelity_statuses[key] = (
                        'passed' if audit.get('verdict_consistent') is True
                        else 'failed')
            fidelity_failed = sum(value == 'failed'
                                  for value in fidelity_statuses.values())
            fidelity_needs_review = sum(value == 'needs_review'
                                        for value in fidelity_statuses.values())
            fidelity_unavailable = sum(value == 'unavailable'
                                       for value in fidelity_statuses.values())
            has_fidelity_status_v2 = any(
                'fidelity_status' in audit for audit in latest_audit.values())
            fidelity_denominator = (i_source_pair_count if pair_mode
                                    else len(eligible_ids))
            assessment['rule_formalization'].update({
                'rule_generated_count': len(generated),
                'fidelity_passed_count': fidelity_passed,
                'fidelity_failed_count': fidelity_failed,
                'fidelity_not_completed_count': max(
                    0, fidelity_denominator - fidelity_passed - fidelity_failed -
                    (fidelity_needs_review + fidelity_unavailable
                     if has_fidelity_status_v2 else 0)),
                'failure_counts_by_stage': failure_counts,
            })
            if has_fidelity_status_v2:
                assessment['rule_formalization'].update({
                    'fidelity_needs_review_count': fidelity_needs_review,
                    'fidelity_unavailable_count': fidelity_unavailable,
                })
            if pair_mode:
                assessment['rule_formalization']['i_source_pair_count'] = i_source_pair_count
                assessment['rule_formalization']['rule_generation_count_unit'] = (
                    'impact_intent_pair')
                assessment['rule_formalization']['fidelity_count_unit'] = (
                    'impact_intent_pair')
                generated_complete = 0
                fidelity_complete = 0
                for impact_id in eligible_ids:
                    rows = [row for row in records.get(impact_id, [])
                            if row.get('intent_id')]
                    if rows and all(row.get('status') == 'formalized_candidate'
                                    for row in rows):
                        generated_complete += 1
                    if rows and all(row.get('status') == 'formalized_candidate' and
                                    row.get('fidelity_status') == 'passed'
                                    for row in rows):
                        fidelity_complete += 1
                assessment['rule_formalization'].update({
                    'generated_complete_piv_impact_count': generated_complete,
                    'fidelity_passed_complete_piv_impact_count': fidelity_complete,
                })
        return assessment

    if bundle is None:
        pending = []
        if elements is not None:
            pending = [
                {'impact_id': row['id'], 'status': 'not_attempted',
                 'reason': 'Rule formalization was not attempted.'}
                for row in elements.get('statements', [])
                if row.get('kind') == 'impact'
            ]
        return {
            'schema_version': 'stage2-assessment/1',
            'narrative_sufficiency': narrative,
            'rule_formalization': {
                'status': 'not_attempted', 'impact_count': len(pending),
                'formalized_impact_count': 0, 'pending_impacts': pending,
            },
        }

    coverage = bundle.get('report_impact_coverage', [])
    limitations = bundle.get('formalization_limitations_declared', [])
    omitted_reasons = {}
    for row in coverage:
        impact_id = row.get('impact_id')
        if not impact_id:
            continue
        prefix = impact_id + ': '
        note = next((item for item in limitations
                     if isinstance(item, str) and item.startswith(prefix)), None)
        if note is not None:
            omitted_reasons[impact_id] = note[len(prefix):]
    formalized = sum(row.get('status') == 'formalized' for row in coverage)
    partial = sum(row.get('status') == 'partial' for row in coverage)
    if coverage and formalized == len(coverage):
        result = 'complete'
    elif formalized or partial:
        result = 'partial'
    else:
        result = 'none'
    pending = [
        {'impact_id': row.get('impact_id'), 'status': row.get('status'),
         'reason': row.get('reason') or omitted_reasons.get(row.get('impact_id'))
         or 'No complete P/I/V rule was produced.'}
        for row in coverage if row.get('status') != 'formalized'
    ]
    return {
        'schema_version': 'stage2-assessment/1',
        'narrative_sufficiency': narrative,
        'rule_formalization': {
            'status': result, 'impact_count': len(coverage),
            'formalized_impact_count': formalized,
            'partial_impact_count': partial,
            'candidate_acceptance_status': bundle.get('acceptance_status'),
            'pending_impacts': pending,
        },
    }


def model_catalog(catalog, allowed_ids=None, impact_source_ids=None):
    """Keep all exact ID/text pairs; offsets stay in the saved full catalog."""
    allowed = set(allowed_ids) if allowed_ids is not None else None
    result = {'schema_version': catalog['schema_version'],
              'source_sha256': catalog['source_sha256'],
              'fragments': [{'id': row['id'], 'text': row['text']}
                            for row in catalog['fragments']
                            if allowed is None or row['id'] in allowed]}
    if impact_source_ids is not None:
        result['impact_source_ids'] = list(impact_source_ids)
    return result


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


_REPORT_NUMBER = re.compile(
    r'(?<![A-Za-z0-9_])(?:[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?)(?![A-Za-z0-9_])')
_COMPARATOR_CUE = re.compile(
    r'\b(?:at\s+least|at\s+most|greater\s+than|less\s+than|more\s+than|'
    r'fewer\s+than|equal(?:s|ed)?\s+to|above|below|exceeds?|under|over)\b|'
    r'(?<![<>=!])[<>]=?|==|!=', re.IGNORECASE)
_LOGICAL_CUE = re.compile(r'\b(?:and|or|either|both|unless|not)\b', re.IGNORECASE)
_UNIT_CUE = re.compile(
    r'%|\b(?:percent(?:age)?|bps|basis\s+points?|wei|ether|eth|usd|tokens?|'
    r'shares?|seconds?|minutes?|hours?|days?|blocks?|epochs?|digits?|bits?)\b',
    re.IGNORECASE)


def numeric_fact_inventory(elements):
    """Expose report-stated numeric facts before formula construction.

    This is a locator, not a semantic parser: it preserves the exact source
    text around each literal and never assigns a unit or comparator itself.
    The model must interpret those facts from the statement and evidence.
    """
    inventory = []
    for row in elements.get('statements', []):
        facts = []
        text = row.get('text', '')
        for match in _REPORT_NUMBER.finditer(text):
            start, end = match.span()
            context_start, context_end = max(0, start - 48), min(len(text), end + 48)
            context = text[context_start:context_end]
            facts.append({
                'literal': match.group(0),
                'source_context': context,
                'comparator_cues': list(dict.fromkeys(
                    cue.group(0) for cue in _COMPARATOR_CUE.finditer(context))),
                'logical_cues': list(dict.fromkeys(
                    cue.group(0).lower() for cue in _LOGICAL_CUE.finditer(context))),
                'unit_or_scale_cues': list(dict.fromkeys(
                    cue.group(0) for cue in _UNIT_CUE.finditer(context))),
            })
        if facts:
            inventory.append({'source_id': row['id'], 'kind': row['kind'],
                              'numeric_facts': facts})
    return inventory


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
        'numeric_fact_inventory': numeric_fact_inventory(elements),
    }


def formal_failure_family(message):
    """Separate formula/schema failures from report-semantic failures."""
    value = str(message).lower()
    if value.startswith('semantic faithfulness mismatch'):
        return 'semantic_fidelity'
    if 'direct p/i/v relationship is absent or infeasible' in value:
        return 'direct_relation_infeasible'
    if any(token in value for token in ('numeric p ', 'quantity binding',
                                        'quantity expression', 'type/unit mismatch',
                                        'invalid compound predicate',
                                        'invalid predicate binding')):
        return 'formula_construction'
    if any(token in value for token in ('source', 'grounded', 'coverage',
                                        'impact qualifier')):
        return 'evidence_or_coverage'
    return 'schema_or_validation'


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
            'semantically equivalent. Preserve whether multiple comparisons '
            'are joined by OR or AND; use any_of for alternatives and all_of '
            'only for simultaneous requirements. Keep report facts unchanged.\n'
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
_IMPACT_CORE = ('impact_ids', 'impact_outcome', 'symbols', 'derived_definitions', 'pattern',
                'unresolved', 'limitations')
_IMPACT_CONTEXT = ('impact_context_terms', 'impact_outcome', 'symbols', 'pattern',
                   'unresolved', 'limitations')
_TYPE_UNIT = ('relation_class', 'symbols', 'precondition_terms',
              'derived_definitions', 'impact_context_terms', 'impact_outcome', 'pattern',
              'assumptions', 'unresolved', 'limitations')
_SYMBOL_SCOPE = ('symbols', 'precondition_terms', 'derived_definitions',
                 'impact_outcome', 'pattern', 'unresolved', 'limitations')
_FAITHFULNESS_SCOPE = ('precondition_terms', 'symbols', 'derived_definitions',
                       'impact_context_terms', 'impact_outcome', 'pattern')
#: Preserve semantic selection/classification even for an unfamiliar local
#: structural error. A later fresh run, rather than a repair, may reconsider it.
_SEMANTIC_SCOPE = ('symbols', 'precondition_terms', 'derived_definitions', 'pattern',
                   'impact_context_terms', 'impact_outcome', 'assumptions', 'unresolved', 'limitations')
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
    return ('\nRETRY FEEDBACK: A semantic cross-audit found that a P, I, V, or '
            'P/I/V relation does not preserve its cited report statement. Repair '
            'the actual formula: for P, change the relevant precondition_terms; '
            'for I, change the safety pattern; for V, change impact_outcome or its '
            'impact qualifiers. Never use an impact-only result as an I guard or '
            'required relation. Update symbols or derived_definitions only '
            'when their meaning/value/unit is part of the error. Preserve the '
            'statement\'s exact comparator direction, numeric literal, unit, '
            'and/or connective and negation scope. Do not spend this repair only '
            'changing assumptions, limitations, or unresolved text. If the stated '
            'relation cannot be represented, do not retain a misleading formula; '
            'the impact must remain pending for review. Keep unrelated report facts '
            'unchanged.\nAudit findings: ' + message + '\n')


def _piv_relationship_hint(message):
    return ('\nRETRY FEEDBACK: The compiled report-only P/I/V checks found an '
            'infeasible or missing relation. Change only the formula fields '
            'needed to make the cited preconditions, safety property, and '
            'direct impact jointly express the report scenario. If one field is '
            'observed at multiple steps, split it into separate symbols with '
            'distinct checkpoint descriptions (for example, balance_before and '
            'balance_after); never bind values from different steps to one '
            'symbol. Preserve step order, exact values, units, comparison '
            'direction, and OR/AND grouping. '
            'Do not weaken or replace a report-supported relation. If it cannot '
            'be represented, leave this impact unresolved.\nCheck findings: '
            + message + '\n')


def _direct_witness_hint(message):
    return ('\nRETRY FEEDBACK: The generated V does not directly falsify I under P. '
            'Repair impact_outcome (and only when necessary its supporting '
            'impact_context_terms, pattern, symbols, or derived_definitions) so '
            'the selected Impact states the concrete observed counterpart of the '
            "pattern's desired relation: the forbidden completion, the out-of-range "
            'value, the mismatched before/after state, or the denied required '
            'authorization. V must be the Impact\'s own report-stated observable, '
            'not a formula copied from I and not a downstream profit/loss proxy. '
            'If the report gives only an indirect consequence and no stated V '
            'directly contradicts I under the frozen P, do not weaken V or invent '
            'a bridge predicate; keep the frozen IDs and let this candidate be '
            'rejected rather than accepting an indirect-consequence V.\n'
            'Check findings: ' + message + '\n')

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
     'relation_class and use exactly its required fields: access_control -> '
     'authorization_guard(effect, authorization); bounded_value/range_capacity -> '
     'bounded_relation(condition, value, operator, bound); proportional_fairness -> '
     'proportional_relation(condition, left, operator, right); state_correspondence -> '
     'correspondence(condition, observed_symbol, expected_symbol); temporal_validity -> '
     'temporal_order(condition, earlier_symbol, later_symbol, strict); '
     'sequence_preservation/progress_or_liveness -> required_effect(condition, effect); '
     'monotonicity -> monotonicity(trigger, before_symbol, after_symbol, direction); '
     'conservation -> conservation(trigger, before, after); value_relation and '
     'data_structure_integrity -> relation_obligation(condition, relation). Do not '
     'change relation_class, intent_id, or impact_ids.\n'),
    (('invalid temporal order pattern', 'invalid correspondence pattern'),
     _PATTERN_ONLY,
     '\nRETRY FEEDBACK: Keep the selected relation_class and supply the exact fields '
     'for its fixed template. temporal_order requires condition, earlier_symbol, '
     'later_symbol, and strict (JSON boolean); correspondence requires condition, '
     'observed_symbol, and expected_symbol. The referenced symbols must be declared.\n'),
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
    (('prefix', 'semantic faithfulness mismatch'), _FAITHFULNESS_SCOPE,
     _audit_mismatch_hint),
    (('prefix', 'P/I/V relationship check failed:'), _FAITHFULNESS_SCOPE,
     _piv_relationship_hint),
    (('prefix', 'direct P/I/V relationship is absent or infeasible'),
     _FAITHFULNESS_SCOPE, _direct_witness_hint),
    ('local repair did not change P/I/V formula fields', _FAITHFULNESS_SCOPE,
     '\nRETRY FEEDBACK: The focused repair changed metadata but left the failing '
     'P/I/V expression unchanged. Change the relevant precondition_terms for P '
     'or pattern for I/V, preserving report wording, comparator direction, units, '
     'exact constants, and logical connectives.\n'),
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
     'lists missing types such as temporal, trigger, threshold, '
     'comparison_direction, scope, duration_or_repetition, range, or rate_or_cost '
     'by impact ID. Add '
     'report-grounded predicates for those exact types without replacing '
     'the selected impact or intent.\n'),
    ('unexpected formal plan fields', _IMPACT_CONTEXT,
     '\nRETRY FEEDBACK: This schema requires the impact_context_terms array, '
     'even when empty. Include it. For the selected impact, encode every detected '
     'qualifier type in one impact-grounded predicate and preserve trigger, '
     'direction, scope, duration, range, and rate.\n'),
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


class SemanticFaithfulnessMismatch(ValueError):
    """Validated audit findings retained for role-scoped formula repair."""

    def __init__(self, message, mismatches):
        super().__init__(message)
        self.mismatches = tuple(dict(row) for row in mismatches)


def formal_repair_fields(exc):
    """Return the smallest top-level plan area allowed to change on retry."""
    if isinstance(exc, SemanticFaithfulnessMismatch):
        fields_by_role = {
            'P': {'precondition_terms', 'symbols', 'derived_definitions'},
            'I': {'pattern', 'symbols', 'derived_definitions'},
            'V': {'impact_outcome', 'impact_context_terms', 'symbols',
                  'derived_definitions'},
            # A relation-level finding can involve interactions among all three
            # formulas, but source IDs and relation classification stay frozen.
            'PIV': {'precondition_terms', 'pattern', 'impact_outcome',
                    'impact_context_terms', 'symbols', 'derived_definitions'},
        }
        roles = {row.get('role') for row in exc.mismatches}
        if roles and roles <= set(fields_by_role):
            return tuple(sorted(set().union(*(fields_by_role[role]
                                              for role in roles))))
        return ('precondition_terms', 'pattern', 'impact_outcome',
                'impact_context_terms', 'symbols', 'derived_definitions')
    message = str(exc)
    for matcher, mutable_fields, _hint in _FORMAL_ERROR_RULES:
        if _match_formal_error(message, matcher):
            return mutable_fields
    return _SEMANTIC_SCOPE


def validate_local_repair(previous, repaired, mutable_fields,
                          require_formula_change=False):
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
    formula_fields = {'precondition_terms', 'pattern', 'symbols',
                      'derived_definitions', 'impact_context_terms', 'impact_outcome'}
    if require_formula_change and not changed.intersection(formula_fields):
        raise ValueError('local repair did not change P/I/V formula fields')
    return sorted(changed)


def restore_frozen_repair_fields(previous, repaired, mutable_fields):
    """Keep a local repair's unauthorized top-level edits from leaking through.

    A repair response is a full plan, so models sometimes rewrite caveats or
    other unrelated fields despite the allow-list. Restore those fields from
    the audited plan, then validate that the formula actually changed inside
    the allowed scope. Schema/key changes remain errors.
    """
    if not isinstance(previous, dict) or not isinstance(repaired, dict):
        raise ValueError('local repair requires plan objects')
    if set(previous) != set(repaired):
        raise ValueError('local repair changed plan schema')
    mutable = set(mutable_fields)
    restored = []
    for key in previous:
        if key not in mutable and previous[key] != repaired[key]:
            repaired[key] = copy.deepcopy(previous[key])
            restored.append(key)
    return repaired, sorted(restored)


def local_repair_payload(original_payload, previous, exc, mutable_fields):
    """Build an audited, bounded repair request without asking for a new plan."""
    may_reclassify = 'relation_class' in mutable_fields
    roles = (sorted({row.get('role') for row in exc.mismatches
                     if row.get('role') in ('P', 'I', 'V', 'PIV')})
             if isinstance(exc, SemanticFaithfulnessMismatch) else [])
    role_requirements = {
        'P': 'For a P finding, change only its own precondition term and supporting symbol definitions.',
        'I': ('For an I finding, repair the safety pattern from the selected intent. '
              'Do not gate I on a V-only impact result or use that result as the required relation.'),
        'V': 'For a V finding, repair impact_outcome or its impact qualifiers; keep I unchanged.',
        'PIV': ('For a relation finding, repair only the P/I/V formula fields needed by '
                'the stated finding; keep every source ID and relation class fixed.'),
    }
    requirements = [
        'Return the complete plan JSON object, not a patch.',
        'Change only mutable_top_level_fields.',
        ('Keep intent_id and impact_ids fixed. relation_class may change only '
         'to resolve the stated type/unit conflict.' if may_reclassify else
         'Keep relation_class, intent_id, precondition_ids and impact_ids byte-for-byte equivalent.'),
        'Correct only the stated deterministic validation failure.',
    ]
    requirements.extend(role_requirements[role] for role in roles)
    return compact_json({
        'task': ('replan_relation_locally' if may_reclassify else
                 'repair_previous_formal_plan_locally'),
        'original_input': json.loads(original_payload),
        'previous_plan': previous,
        'repair_error': str(exc),
        'repair_roles': roles,
        'mutable_top_level_fields': list(mutable_fields),
        'requirements': requirements,
        'normalization_note': ('The caller restores every top-level field outside '
                               'mutable_top_level_fields from previous_plan; edits '
                               'outside the allow-list have no effect.'),
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
            'placeholder/note keys. Include one to four security_intent statements and at least '
            'one direct impact when the screened report supports them. Each impact must retain '
            'the report-stated outcome, amount/range, unit, trigger, causal detail and '
            'qualifiers; do not collapse a quantified or conditional effect into a bare '
            'Boolean label. Split distinct harms and list omitted supported harms in '
            'ambiguities. attack_steps '
            'may reference action statements only. Use only supplied evidence IDs.\n')


def _audit_retry_feedback(_exc, include_relations=False):
    if include_relations:
        return ('\nRETRY FEEDBACK: Return the exact P/I/V audit schema. Include one '
                'check for every listed source_id and role (P, I, V), plus a '
                'piv_relation verdict of consistent, weakened, or mismatch.\n')
    return ('\nRETRY FEEDBACK: Previous verdict JSON failed shape or coverage '
            'validation. Return exactly {"checks":[{"source_id":ID,"verdict":'
            '"consistent"|"inverted"|"wrong_constant"|"wrong_symbol"|'
            '"other_mismatch","reason":ONE_SHORT_SENTENCE}]} covering every '
            'listed source_id exactly once.\n')


def faithfulness_audit_input(elements, plan, formal=None, include_relations=False,
                             relation_context=None, relationship_trace=None):
    """Narrow cross-audit payload: per P source, its statement text, the
    predicate claiming to encode it, and only the meanings of the symbols
    that predicate uses. For relation review, exact cited action/root-cause
    excerpts provide bounded context without changing frozen P/I/V sources."""
    statements = {row['id']: row for row in elements['statements']}
    rows = []
    terms_by_source = {}
    for term in plan['precondition_terms']:
        # The fidelity-only schema permits incomplete P terms so generation
        # itself does not pre-filter a frozen P/I/V source set. Preserve one
        # audit row per frozen P source and let the post-generation auditor see
        # an omitted term as predicate=null.
        terms_by_source.setdefault(term['source_id'], term)
    for source_id in plan['precondition_ids']:
        term = terms_by_source.get(source_id)
        predicate = term['predicate'] if term else None
        names = predicate_binding_symbols(predicate) if predicate is not None else set()
        rows.append({
            'source_id': source_id,
            **({'role': 'P'} if include_relations else {}),
            'statement_text': statements[source_id]['text'],
            'predicate': predicate,
            'symbol_meanings': {name: {
                'sort': plan['symbols'][name]['sort'],
                'unit': plan['symbols'][name]['unit'],
                'meaning': plan['symbols'][name]['meaning'],
            } for name in sorted(names)},
        })
    if include_relations:
        if formal is None or len(formal.get('claims', [])) != 1:
            raise ValueError('P/I/V faithfulness audit requires one synthesized claim')
        claim = formal['claims'][0]
        expressions = {
            'I': (plan['intent_id'], claim['properties']['safety']['expression']),
            'V': (plan['impact_ids'][0], claim['properties']['effects']['expression']),
        }
        for role, (source_id, expression) in expressions.items():
            names = _expression_symbols(expression)
            rows.append({
                'source_id': source_id, 'role': role,
                'statement_text': statements[source_id]['text'],
                'predicate': expression,
                'symbol_meanings': {name: {
                    'sort': plan['symbols'][name]['sort'],
                    'unit': plan['symbols'][name]['unit'],
                    'meaning': plan['symbols'][name]['meaning'],
                } for name in sorted(names)},
            })
    output = {
        'schema_version': ('faithfulness-audit-input/4'
                           if include_relations and relationship_trace is not None
                           else 'faithfulness-audit-input/3' if include_relations
                           else 'faithfulness-audit-input/1'),
        'relation_class': plan.get('relation_class'),
        'sources': rows,
    }
    if include_relations:
        output['piv_relation'] = {
            'P': claim['properties']['preconditions']['expression'],
            'I': claim['properties']['safety']['expression'],
            'V': claim['properties']['effects']['expression'],
        }
        if relation_context:
            output['relation_context'] = relation_context
        if relationship_trace is not None:
            output['relationship_trace'] = relationship_trace
    return compact_json(output)


def faithfulness_relation_context(elements, catalog, excluded_source_ids=()):
    """Collect exact report excerpts for the explicitly described causal bridge.

    Only evidence cited by extracted action/root-cause statements is included.
    These excerpts help assess the P/I/V link; they cannot replace or modify any
    frozen P, I, or V source.
    """
    if not isinstance(catalog, dict):
        return []
    fragments = {row.get('id'): row.get('text')
                 for row in catalog.get('fragments', [])
                 if isinstance(row, dict) and row.get('id') and
                 isinstance(row.get('text'), str)}
    excluded = set(excluded_source_ids)
    rows = []
    seen = set()
    for statement in elements.get('statements', []):
        if statement.get('kind') not in ('action', 'root_cause'):
            continue
        statement_id = statement.get('id')
        if statement_id in excluded:
            continue
        evidence = []
        for evidence_id in statement.get('evidence_ids', statement.get('evidence', [])):
            if evidence_id in seen or evidence_id not in fragments:
                continue
            seen.add(evidence_id)
            evidence.append({'evidence_id': evidence_id,
                             'text': fragments[evidence_id]})
        if evidence:
            rows.append({'statement_id': statement_id,
                         'role': statement['kind'], 'evidence': evidence})
    return rows


def _expression_symbols(expression):
    if expression is None:
        return set()
    if isinstance(expression, dict):
        if set(expression) == {'var'}:
            return {expression['var']}
        return set().union(*(_expression_symbols(value)
                             for value in expression.values()))
    if isinstance(expression, list):
        return set().union(*(_expression_symbols(value) for value in expression))
    return set()


def request_faithfulness_audit(payload, model, output, plan, extract_fn,
                               on_attempt=None, include_relations=False):
    """One bounded semantic cross-audit call; only format failures retry."""
    def accept(raw, call_dir, record):
        validate_faithfulness_verdict(raw, plan, include_relations=include_relations)
        return raw
    accepted, _ = _bounded_model_call(
        payload, FAITHFULNESS_AUDIT_PROMPT, model, output, 1,
        'faithfulness-audit', 'faithfulness-audit-attempts.json', accept,
        (lambda exc: _audit_retry_feedback(exc, include_relations)),
        'accepted_for_routing', extract_fn=extract_fn,
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


def request_impact_inventory(payload, prompt, model, output, retries,
                             allowed_ids, evidence_catalog, extract_fn=None,
                             on_attempt=None):
    """Extract impact facts from a catalog already restricted to Impact text."""
    def accept(raw, call_dir, record):
        return validate_impact_inventory(raw, allowed_ids, evidence_catalog)

    accepted, _ = _bounded_model_call(
        payload, prompt, model, output, retries, 'impact-inventory',
        'impact-inventory-attempts.json', accept,
        lambda _exc: ('\nRETRY FEEDBACK: Return the exact Impact inventory schema. '
                      'Use only the supplied Impact fragment IDs; do not infer or '
                      'include evidence from other report sections. Copy each text '
                      'as an exact continuous excerpt; do not paraphrase, summarize, '
                      'or join separated wording. Only whitespace and Markdown '
                      'presentation may differ.\n'),
        'accepted_for_validation', extract_fn=extract_fn, on_attempt=on_attempt)
    return accepted


def request_impact_applicability(elements, catalog, model, output, extract_fn=None,
                                 on_attempt=None):
    """Select report-grounded P/I sources for each explicit Impact once."""
    impacts = [row for row in elements.get('statements', [])
               if row.get('kind') == 'impact']
    i_sources = [row for row in elements.get('statements', [])
                 if row.get('kind') == 'security_intent' and
                 row.get('modality') in ('asserted', 'potential') and
                 row.get('evidence_ids', row.get('evidence'))]
    payload = compact_json(applicability_payload(elements, catalog))
    if not i_sources:
        return {'schema_version': APPLICABILITY_SCHEMA_VERSION, 'impacts': [
            {'impact_id': row['id'], 'status': 'explicit_but_insufficient',
             'precondition_ids': [], 'intent_ids': [],
             'reason': 'No report-supported, non-inferred security intent is available.'}
            for row in impacts]}, []

    def accept(raw, _call_dir, _record):
        return validate_applicability(raw, elements)

    result, attempts = _bounded_model_call(
        payload, IMPACT_APPLICABILITY_PROMPT, model, output, 1,
        'impact-applicability', 'impact-applicability-attempts.json', accept,
        lambda _exc: ('\nRETRY FEEDBACK: Return exactly one valid entry for every Impact. '
                      'Use only evidence-backed P/assumption IDs and explicit asserted/'
                      'potential I IDs from the payload. Do not infer. The total number '
                      'of selected (Impact, I) pairs cannot exceed 64; if the report '
                      'supports more, return a schema error rather than omitting or '
                      'truncating any source.\n'),
        'accepted_for_validation', extract_fn=extract_fn, on_attempt=on_attempt)
    return result, attempts


def validate_core_element_candidate(candidate, catalog, text, normalize_steps=False,
                                    require_core_counts=False, normalize_ids=False,
                                    max_core_impacts=2, max_core_intents=1,
                                    impact_source_ids=None):
    """Validate a neural ID candidate before accepting the extraction call."""
    checked = candidate
    if normalize_ids:
        checked, _ = normalize_element_ids(checked)
    if normalize_steps:
        checked, _ = normalize_attack_step_roles(checked)
    hydrated = hydrate_elements(checked, catalog, text)
    validate_elements(hydrated, text)
    if impact_source_ids is not None:
        validate_impact_evidence(checked, impact_source_ids)
    if not require_core_counts:
        return
    kinds = [row['kind'] for row in checked['statements']]
    if not 1 <= kinds.count('security_intent') <= max_core_intents:
        raise ValueError(f'elements require one to {max_core_intents} security intents')
    minimum_impacts = 1 if impact_source_ids is None or impact_source_ids else 0
    if not minimum_impacts <= kinds.count('impact') <= max_core_impacts:
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
                          faithfulness_audit_on_attempt=None,
                          audit_relations=False, candidate_gate=None,
                          frozen_source_ids=None,
                          fidelity_only_rules=False,
                          relation_context=None,
                          relationship_trace_enabled=False,
                          synthesis_claim_id='core_claim'):
    """Retry malformed responses or perform a bounded, field-scoped plan repair.

    Each attempt keeps its own raw model artifacts. A rejected plan is never
    silently treated as successful. In local-repair mode, parsed plans freeze all
    unrelated top-level fields and the model receives the prior plan plus an
    explicit allow-list of fields it may change.

    When ``faithfulness_audit`` is supplied, the audit runs after deterministic
    synthesis. Legacy modes treat a mismatch as retryable; fidelity-only mode
    records the verdict and retains the generated rule without repair or rejection.
    """
    extract_fn = extract_fn or r.extract
    attempts = attempts if attempts is not None else []
    feedback = ''
    repair_base = None
    mutable_fields = ()
    repair_error = None
    attempt = 0
    max_retries = retries
    null_reprompt_granted = False
    fresh_restate = False
    while attempt <= max_retries:
        call_dir = output / ('neural-formalization' if attempt == 0 else
                             f'neural-formalization-retry-{attempt}')
        call_dir.mkdir(exist_ok=True)
        attempt_prompt = prompt + feedback
        attempt_payload = payload
        if local_repair and repair_base is not None and not fresh_restate:
            attempt_payload = local_repair_payload(
                payload, repair_base, repair_error, mutable_fields)
            attempt_prompt += ('\nLOCAL REPAIR MODE: repair the supplied previous_plan. '
                               'Do not reconsider frozen semantic decisions.\n')
        (call_dir / 'prompt.txt').write_text(attempt_prompt + attempt_payload)
        record = {'attempt': attempt + 1, 'artifact_dir': call_dir.name}
        if fresh_restate:
            record['fresh_restate'] = True
            record['mutable_top_level_fields'] = list(mutable_fields)
            fresh_restate = False
        if local_repair and repair_base is not None and not record.get('fresh_restate'):
            record.update({'repair_mode': ('bounded_semantic_replan'
                                           if 'relation_class' in mutable_fields
                                           else 'field_scoped'),
                           'mutable_top_level_fields': list(mutable_fields)})
        attempts.append(record)
        candidate = None
        relationship_trace = None
        try:
            if on_attempt is not None:
                on_attempt()
            try:
                candidate = extract_fn(attempt_payload, call_dir, model,
                                       attempt_prompt)
            except json.JSONDecodeError:
                # live-24 paired attribution: the model sometimes closes the
                # flat formal-plan object and appends the audit-only
                # relationship_trace key outside the brace. Relocating that
                # one key is a mechanical, content-gated repair; the raw
                # response stays in model-response.txt and the transform is
                # logged for offline replay. Anything else re-raises.
                raw_path = call_dir / 'model-response.txt'
                salvaged = None
                if raw_path.is_file():
                    salvaged = merge_appended_relationship_trace(
                        raw_path.read_text())
                if salvaged is None:
                    raise
                candidate, normalization = salvaged
                write_json(call_dir / 'model-claim.json', candidate)
                write_json(call_dir / 'response-normalization.json',
                           normalization)
                record['response_normalization'] = normalization['transform']
            if relationship_trace_enabled and isinstance(candidate, dict):
                relationship_trace = candidate.pop('relationship_trace', None)
                if not isinstance(relationship_trace, dict):
                    relationship_trace = {
                        'status': 'insufficient', 'links': [],
                        'gap': 'Generator did not return a valid relationship_trace.'}
                write_json(call_dir / 'relationship-trace.json',
                           relationship_trace)
                write_json(output / 'relationship-trace.json',
                           relationship_trace)
            # semantic-live-24 asks the model to return exactly two top-level
            # keys: `formal_plan` plus the sibling `relationship_trace`.  The
            # plan fields live inside `formal_plan`; keep the raw response
            # untouched and deterministically unwrap the envelope before any
            # schema/source validation.  Flat responses (all historical
            # prompt versions) pass through unchanged.
            if isinstance(candidate, dict) and isinstance(candidate.get('formal_plan'), dict):
                candidate = candidate['formal_plan']
            if frozen_source_ids is not None and not fidelity_only_rules:
                if not isinstance(candidate, dict):
                    raise ValueError('formal plan must be a JSON object')
                expected_p = list(frozen_source_ids.get('precondition_ids', []))
                actual_p = candidate.get('precondition_ids', [])
                if (not isinstance(actual_p, list) or
                        set(actual_p) != set(expected_p) or
                        len(actual_p) != len(expected_p)):
                    raise ValueError(
                        'formal plan did not preserve all frozen P source IDs')
                if candidate.get('intent_id') != frozen_source_ids.get('intent_id'):
                    raise ValueError(
                        'formal plan did not preserve the frozen I source ID')
                if candidate.get('impact_ids') != frozen_source_ids.get('impact_ids'):
                    raise ValueError(
                        'formal plan did not preserve the frozen Impact ID')
            elif frozen_source_ids is not None:
                if not isinstance(candidate, dict):
                    raise ValueError('formal plan must be a JSON object')
                # Applicability has already frozen the source set. Canonicalize
                # these identifiers instead of rejecting a generated rule for
                # trying to select sources again; fidelity is evaluated below.
                source_normalizations = {}
                for field, source_key in (
                        ('precondition_ids', 'precondition_ids'),
                        ('intent_id', 'intent_id'), ('impact_ids', 'impact_ids')):
                    expected = frozen_source_ids.get(source_key)
                    if expected is None:
                        continue
                    if candidate.get(field) != expected:
                        source_normalizations[field] = {
                            'from': candidate.get(field), 'to': expected}
                        candidate[field] = copy.deepcopy(expected)
                if source_normalizations:
                    record['frozen_source_normalizations'] = source_normalizations
            if local_repair and repair_base is not None:
                require_formula_change = bool(
                    repair_error and str(repair_error).startswith(
                        'semantic faithfulness mismatch'))
                candidate, restored = restore_frozen_repair_fields(
                    repair_base, candidate, mutable_fields)
                if restored:
                    record['restored_frozen_fields'] = restored
                record['changed_top_level_fields'] = validate_local_repair(
                    repair_base, candidate, mutable_fields,
                    require_formula_change=require_formula_change)
            if plan_mode:
                # Boundary NORMALIZE: the model named the boolean after the
                # precondition that asserts it and only forgot to declare it.
                # The raw response stays untouched in model-claim.json.
                amended, normalized = normalize_truth_binding(
                    candidate, elements,
                    allow_named_symbol=fidelity_only_rules)
                if normalized:
                    write_json(call_dir / 'normalization-log.json', {
                        'schema_version': 'stage2-normalization-log/1',
                        'stage': 'formalization', 'mode': NORMALIZE,
                        'changes': normalized})
                    record['normalizations'] = normalized
                    candidate = amended
                if mechanical_salvage and not fidelity_only_rules:
                    candidate, repairs = drop_unused_invalid_symbols(candidate)
                    if repairs:
                        write_json(call_dir / 'mechanical-salvage.json', repairs)
                if partial_formalization and not fidelity_only_rules:
                    # Boundary-normalize the unsupported_relation contradiction:
                    # a plan that already represents the relation as a bool
                    # symbol cannot honestly also declare it blocking.
                    candidate, relaxed = relax_unsupported_relation(candidate, elements)
                    if relaxed:
                        write_json(call_dir / 'partial-formalization.json', relaxed)
                formal = synthesize_id_formalization(
                    candidate, elements, claim_id=synthesis_claim_id,
                    fidelity_only=fidelity_only_rules)
                record['rule_generated'] = True
                # Save the rule before any post-generation audit. An audit
                # verdict must never erase a successfully generated candidate.
                write_json(call_dir / 'generated-rule-candidate.json', {
                    'schema_version': 'stage2-generated-rule-candidate/1',
                    'formal_plan': candidate,
                    'formalization': formal,
                })
                if duplicate_predicate_gate and not fidelity_only_rules:
                    check_distinct_p_predicates(candidate)
                if faithfulness_audit is not None and plan_mode:
                    # This is the only semantic check in the rule-generation
                    # chain. Artifacts nest inside this
                    # formalization attempt's directory; the run-level verdict
                    # file below is the replay artifact (batch_verify routes
                    # on it deterministically, never on a new model call).
                    try:
                        verdict = request_faithfulness_audit(
                            faithfulness_audit_input(elements, candidate, formal,
                                                     include_relations=audit_relations,
                                                     relation_context=relation_context,
                                                     relationship_trace=(
                                                         relationship_trace
                                                         if relationship_trace_enabled
                                                         else None)),
                            faithfulness_audit_model, call_dir, candidate,
                            extract_fn=faithfulness_audit,
                            on_attempt=faithfulness_audit_on_attempt,
                            include_relations=audit_relations)
                        mismatches = faithfulness_mismatches(verdict)
                        repair_findings = (faithfulness_repair_mismatches(verdict)
                                           if fidelity_only_rules else mismatches)
                        outcome = faithfulness_status(verdict)
                        record['semantic_faithfulness_audit'] = {
                            'status': 'completed',
                            'verdict_consistent': not mismatches,
                            'fidelity_status': outcome,
                            'checks': len(verdict['checks']),
                            'mismatches': mismatches,
                            'repair_findings': repair_findings,
                        }
                        write_json(output / 'semantic-faithfulness-audit.json', {
                            'schema_version': ('semantic-faithfulness-audit/4'
                                               if audit_relations and
                                               relationship_trace_enabled else
                                               'semantic-faithfulness-audit/3'
                                               if audit_relations else
                                               'semantic-faithfulness-audit/1'),
                            'status': 'completed',
                            'verdict_consistent': not mismatches,
                            'fidelity_status': outcome,
                            'checks': verdict['checks'],
                            **({'piv_relation': verdict['piv_relation']}
                               if audit_relations else {}),
                            **({'relation_context': relation_context}
                               if audit_relations and relation_context else {}),
                            **({'relationship_trace': relationship_trace}
                               if audit_relations and
                               relationship_trace_enabled else {}),
                            'mismatch_count': len(mismatches),
                            'repair_finding_count': len(repair_findings),
                        })
                        # In fidelity-only mode the audit is the sole semantic
                        # judge. When a bounded local-repair attempt is available,
                        # feed its source-specific findings back into the next
                        # generation. On the final attempt, retain the candidate
                        # and its failed audit so an unsuccessful repair remains
                        # visible instead of silently discarding the rule.
                        if (repair_findings and
                                (not fidelity_only_rules or
                                 (local_repair and attempt < max_retries))):
                            raise SemanticFaithfulnessMismatch(
                                'semantic faithfulness mismatch: ' + '; '.join(
                                f"{row['source_id']} {row['verdict']}: "
                                f"{row['reason'][:160]}" for row in repair_findings),
                                repair_findings)
                    except (ValueError, KeyError, TypeError, json.JSONDecodeError,
                            subprocess.TimeoutExpired, TransientModelError,
                            RuntimeError, OSError) as exc:
                        if (str(exc).startswith('semantic faithfulness mismatch') and
                                local_repair and attempt < max_retries):
                            raise
                        if not fidelity_only_rules:
                            raise
                        record['semantic_faithfulness_audit'] = {
                            'status': 'unavailable', 'verdict_consistent': None,
                            'fidelity_status': 'unavailable',
                            'error': str(exc), 'checks': 0, 'mismatches': [],
                        }
                        write_json(output / 'semantic-faithfulness-audit.json', {
                            'schema_version': ('semantic-faithfulness-audit/4'
                                               if audit_relations and
                                               relationship_trace_enabled else
                                               'semantic-faithfulness-audit/3'
                                               if audit_relations else
                                               'semantic-faithfulness-audit/1'),
                            'status': 'unavailable', 'verdict_consistent': None,
                            'fidelity_status': 'unavailable',
                            **({'relation_context': relation_context}
                               if audit_relations and relation_context else {}),
                            **({'relationship_trace': relationship_trace}
                               if audit_relations and
                               relationship_trace_enabled else {}),
                            'error': str(exc), 'checks': [], 'mismatch_count': None,
                        })
                # In fidelity-only mode the generated rule is retained after the
                # bounded audit-guided repair opportunity, regardless of the final
                # semantic verdict. Schema/type validation above is still required
                # to construct a usable rule artifact.
                if numeric_guard and not fidelity_only_rules:
                    check_numeric_plan(
                        candidate, elements,
                        exclude_protocol_identifiers=exclude_protocol_identifiers,
                        relax_assumptions=relax_assumptions)
                if address_guard and not fidelity_only_rules:
                    check_address_plan(candidate, elements)
                if candidate_gate is not None and not fidelity_only_rules:
                    candidate_gate(candidate, formal)
                relation_reasons = reject_vacuous_safety(
                    candidate, formal, claim_id=synthesis_claim_id)
                if relation_reasons:
                    raise ValueError(
                        'direct P/I/V relationship is absent or infeasible: ' +
                        '; '.join(relation_reasons))
                if structured and not fidelity_only_rules:
                    review = structured_unresolved_review(candidate, elements)
                else:
                    review = None
            else:
                formal, review = candidate, None
            record['validation_passed'] = True
            final_audit_failed = (
                record.get('semantic_faithfulness_audit', {}).get(
                    'verdict_consistent') is False)
            if repair_error is not None and not final_audit_failed:
                record['resolved_failure_family'] = formal_failure_family(repair_error)
                record['repair_error_resolved'] = str(repair_error)
            record['outcome'] = 'accepted_for_validation'
            write_json(output / 'formalization-attempts.json', attempts)
            return candidate, formal, review
        except (json.JSONDecodeError, subprocess.TimeoutExpired, TransientModelError, ValueError,
                KeyError, TypeError) as exc:
            record.update({'outcome': 'retryable_failure', 'error_type': type(exc).__name__,
                           'failure_family': formal_failure_family(exc),
                           'error': 'model timeout' if isinstance(exc, subprocess.TimeoutExpired)
                           else str(exc)})
            write_json(output / 'formalization-attempts.json', attempts)
            if (local_repair and str(exc) == 'local repair made no change'
                    and not null_reprompt_granted and repair_error is not None):
                # A byte-identical local repair cannot answer the feedback.
                # Grant one full restatement with the original defect retained.
                null_reprompt_granted = True
                max_retries += 1
                fresh_restate = True
                record['null_repair_reprompt'] = True
                feedback = (formal_retry_hint(repair_error) +
                            f'\nOriginal repair error: {repair_error}\n'
                            'Restate the complete plan: reconsider the failed '
                            'formula from the supplied report facts and return a '
                            'complete candidate plan.\n')
                write_json(output / 'formalization-attempts.json', attempts)
                attempt += 1
                continue
            if attempt == max_retries:
                if (local_repair and str(exc) == 'local repair made no change'
                        and repair_error is not None):
                    raise repair_error from exc
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
                if str(exc) != 'local repair made no change':
                    repair_error = exc
            feedback = formal_retry_hint(exc)
        except (RuntimeError, OSError) as exc:
            record.update({'outcome': 'non_retryable_failure',
                           'error_type': type(exc).__name__, 'error': str(exc)})
            write_json(output / 'formalization-attempts.json', attempts)
            raise
        attempt += 1
    raise AssertionError('unreachable')


def load_report(case_dir=None, report_path=None, input_policy_version=5):
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
    parser.add_argument('--formal-retries', type=int, choices=(0, 1), default=None,
                        help='allow at most one repair attempt; repair only the failed formula fields')
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
    neural_formalization = args.extract or args.formalize_only
    if args.formal_retries is None:
        args.formal_retries = 1 if neural_formalization else 0
    # Feature decisions are resolved once and recorded in provenance so that
    # offline replay of a run never depends on the current live prompt toggles.
    features = features_for(args.prompt_version)
    r.set_unit_guard(features.get('unit_guard', True))
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
    readiness = None
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
            if features.get('impact_level_claims') and features.get('impact_inventory_stage'):
                provenance['impact_semantic_card_contract'] = (
                    'impact-applicability-multi-i-v1'
                    if features.get('multi_i_claims') else
                    'impact-applicability-v1')
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
            if features.get('impact_inventory_stage'):
                provenance['impact_inventory_prompt_sha256'] = r.sha(
                    IMPACT_INVENTORY_PROMPT.encode())
            # Snapshot the exact prompt text into the run directory so offline
            # replay never has to re-resolve an editable live prompt.
            (args.output / 'prompt-element.txt').write_text(
                resolved_prompts.element_prompt)
            (args.output / 'prompt-formal.txt').write_text(
                resolved_prompts.formal_prompt)
            if features.get('impact_inventory_stage'):
                (args.output / 'prompt-impact.txt').write_text(
                    IMPACT_INVENTORY_PROMPT)
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
                    'narrative_sufficiency_status': 'insufficient',
                    'rule_formalization_status': 'not_attempted',
                    'external_model_invocations': calls,
                    'consistency_verdict': 'not_evaluated',
                }
                write_json(args.output / 'stage2-assessment.json',
                           stage2_assessment(readiness=readiness))
                write_json(args.output / 'status.json', status)
                print(json.dumps(status))
                return 2
        impact_sources = None
        impact_inventory = None
        eligible_impact_ids = None
        plan_records = None
        if args.extract:
            if args.evidence_mode == 'ids':
                impact_sources = (explicit_impact_evidence_ids(catalog, text)
                                  if features.get('impact_section_scope') else None)
                if features.get('impact_inventory_stage'):
                    if impact_sources:
                        impact_inventory = request_impact_inventory(
                            compact_json(model_catalog(
                                catalog, allowed_ids=impact_sources)),
                            IMPACT_INVENTORY_PROMPT, model, args.output,
                            args.element_retries, impact_sources, catalog,
                            extract_fn=extract_fn,
                            on_attempt=record_model_attempt)
                    else:
                        impact_inventory = {
                            'schema_version': 'report-impact-inventory/2',
                            'impacts': [],
                            'ambiguities': [
                                'No explicitly labeled Impact area; impacts were not inferred.'],
                        }
                    write_json(args.output / 'impact-inventory.json',
                               impact_inventory)
                    payload = compact_json(model_catalog(catalog))
                else:
                    impact_inventory = None
                    payload = compact_json(model_catalog(
                        catalog, impact_source_ids=impact_sources))
            else:
                impact_sources = None
                impact_inventory = None
                payload = text
            prompt = resolved_prompts.element_prompt
            if features.get('impact_inventory_stage'):
                prompt += ('\n\nCORE-ONLY EXTRACTION OVERRIDE: Do not output any '
                           'kind="impact" statement. Harmful outcomes are extracted '
                           'in the separate Impact inventory and inserted after this '
                           'pass. Continue to extract P, I, cause, entities and steps '
                           'using any report evidence that supports their roles.\n')
            elements_raw, _ = request_elements(
                payload, prompt, model, args.output, args.element_retries,
                extract_fn=extract_fn,
                validate_fn=(lambda candidate: validate_core_element_candidate(
                    ({**candidate, 'statements': [
                        row for row in candidate.get('statements', [])
                        if not isinstance(row, dict) or row.get('kind') != 'impact']}
                     if features.get('impact_inventory_stage') else candidate),
                    catalog, text,
                    normalize_steps=features['step_normalization'],
                    normalize_ids=features['id_normalization'],
                    require_core_counts=(features['core_count'] and
                                         not features.get('impact_inventory_stage')),
                    max_core_impacts=(MAX_IMPACTS
                                      if features.get('impact_inventory_stage') else
                                      4 if features['relation_alignment'] else 2),
                    max_core_intents=(4 if features.get('impact_level_claims')
                                      else 1),
                    impact_source_ids=(None if features.get('impact_inventory_stage')
                                       else impact_sources))
                    if args.evidence_mode == 'ids' else None),
                on_attempt=record_model_attempt)
            if impact_inventory is not None:
                write_json(args.output / 'elements-core-ids.json', elements_raw)
                core_impacts = [row for row in elements_raw.get('statements', [])
                                if isinstance(row, dict) and row.get('kind') == 'impact']
                if core_impacts:
                    write_json(args.output / 'discarded-core-impact-statements.json', {
                        'schema_version': 'stage2-discarded-core-impacts/1',
                        'reason': 'Impact statements are sourced only from the restricted inventory pass.',
                        'statements': core_impacts,
                    })
                elements_raw = merge_impact_inventory(elements_raw,
                                                      impact_inventory)
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
            if features.get('impact_inventory_stage'):
                validate_core_element_candidate(
                    elements_raw, catalog, text,
                    normalize_steps=features['step_normalization'],
                    normalize_ids=features['id_normalization'],
                    require_core_counts=features['core_count'],
                    max_core_impacts=(MAX_IMPACTS if features.get('impact_inventory_stage')
                                      else 4),
                    max_core_intents=(4 if features.get('impact_level_claims') else 1),
                    impact_source_ids=(impact_sources
                                       if impact_inventory['impacts'] else []))
            if features.get('impact_section_scope'):
                validate_impact_evidence(
                    elements_raw, explicit_impact_evidence_ids(catalog, text))
            write_json(args.output / 'elements-ids.json', elements_raw)
            elements = hydrate_elements(elements_raw, catalog, text)
        else:
            if args.extract and args.evidence_mode == 'ids': raise ValueError('ID mode requires report-elements/2')
            elements = elements_raw
        write_json(args.output / 'elements.json', elements)
        grounded = validate_elements(elements, text)
        write_json(args.output / 'evidence-spans.json', grounded)
        if args.elements_only:
            assessment = stage2_assessment(
                readiness=readiness, elements=elements, eligible_impact_ids=[])
            status = {'core_formalization_status': 'not_attempted', 'acceptance_status': 'elements_candidate',
                      'narrative_sufficiency_status': assessment['narrative_sufficiency']['status'],
                      'rule_formalization_status': 'not_attempted',
                      'external_model_invocations': calls, 'consistency_verdict': 'not_evaluated'}
            write_json(args.output / 'stage2-assessment.json', assessment)
            write_json(args.output / 'status.json', status)
            print(json.dumps(status)); return 0
        if (args.extract and features.get('impact_inventory_stage') and
                not impact_inventory['impacts']):
            assessment = stage2_assessment(
                readiness=readiness, elements=elements, eligible_impact_ids=[])
            if not impact_sources:
                inventory_status = 'no_marked_impact_section'
            elif impact_inventory['ambiguities']:
                inventory_status = 'needs_review'
            else:
                inventory_status = 'no_explicit_impact'
            status = {
                'core_formalization_status': 'not_attempted',
                'acceptance_status': 'needs_impact_review',
                'narrative_sufficiency_status': assessment['narrative_sufficiency']['status'],
                'rule_formalization_status': 'not_attempted',
                'impact_inventory_status': inventory_status,
                'impact_source_status': ('marked_section_present'
                                         if impact_sources else 'marked_section_absent'),
                'impact_completion_status': 'none',
                'impact_count': 0,
                'formalized_impact_count': 0,
                'external_model_invocations': calls,
                'consistency_verdict': 'not_evaluated',
            }
            write_json(args.output / 'stage2-assessment.json', assessment)
            write_json(args.output / 'status.json', status)
            print(json.dumps(status)); return 2
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
                # Keep a transparent numeric ledger alongside either payload
                # shape so the formula step can copy values/directions rather
                # than rediscovering them from compressed prose.
                formal_input['numeric_fact_inventory'] = numeric_fact_inventory(
                    elements_raw)
                payload = compact_json(formal_input)
            else:
                payload = compact_json({'elements': elements, 'report_prose': text})
            prompt = resolved_prompts.formal_prompt
            plan_mode = features['plan_synthesis']
            attempts = []
            def candidate_gate(_plan, formal_ids):
                """Apply the same compiled P/I/V gate before repair or acceptance."""
                hydrated = hydrate_formalization(formal_ids, catalog, text)
                candidate_bundle = compile_bundle(
                    elements, hydrated, text,
                    strict_piv=features['strict_piv'], verdict_v2=True,
                    require_complete_piv=True,
                    enforce_units=features.get('unit_guard', True),
                    fidelity_only_rules=features.get('fidelity_only_rules', False))
                candidate_triage = triage_bundle(candidate_bundle)
                if not candidate_triage['stage2_can_continue']:
                    blockers = candidate_triage.get('continuation_blockers', [])
                    reasons = candidate_triage.get('reasons', [])
                    details = blockers or reasons or ['compiled P/I/V checks failed']
                    raise ValueError('P/I/V relationship check failed: ' +
                                     '; '.join(details))

            if (features.get('impact_level_claims') and
                    features.get('multi_i_claims') and plan_mode and
                    args.evidence_mode == 'ids'):
                impact_ids = [row['id'] for row in elements_raw['statements']
                              if row['kind'] == 'impact']
                if not 1 <= len(impact_ids) <= MAX_IMPACTS:
                    raise ValueError(
                        f'impact-level claims require one to {MAX_IMPACTS} grounded impacts')
                applicability, applicability_attempts = request_impact_applicability(
                    elements_raw, catalog, model, args.output, extract_fn=extract_fn,
                    on_attempt=record_model_attempt)
                write_json(args.output / 'impact-applicability.json', applicability)
                eligible_impact_ids = [
                    row['impact_id'] for row in applicability['impacts']
                    if row['status'] == 'selected']
                successful, failures, plan_records, semantic_cards = [], [], [], []
                review_records = {name: {} for name in (
                    'relation_alignment', 'requirement_source_review',
                    'intent_scope_review', 'example_pinning_review',
                    'placeholder_predicate_review', 'mixed_unit_scaling_review',
                    'symbol_table_review', 'unresolved_review',
                    'semantic_faithfulness_audit')}
                dispositions = applicability_by_impact(applicability)
                for impact_id in impact_ids:
                    impact_root = args.output / 'impact-formalizations' / impact_id
                    impact_root.mkdir(parents=True, exist_ok=False)
                    full_card = build_impact_card(
                        elements_raw, impact_id, applicability)
                    semantic_cards.append(full_card)
                    write_json(impact_root / 'semantic-card.json', full_card)
                    disposition = dispositions[impact_id]
                    if disposition['status'] != 'selected':
                        reason = disposition['reason']
                        failures.append((impact_id, None, reason))
                        write_json(impact_root / 'status.json', {
                            'status': disposition['status'],
                            'failure_family': ('no_applicable_explicit_intent'
                                               if disposition['status'] ==
                                               'explicit_but_insufficient'
                                               else 'impact_applicability_uncertain'),
                            'reason': reason, 'attempts': []})
                        plan_records.append({
                            'impact_id': impact_id, 'intent_id': None,
                            'claim_id': None, 'status': disposition['status'],
                            'failure_family': ('no_applicable_explicit_intent'
                                               if disposition['status'] ==
                                               'explicit_but_insufficient'
                                               else 'impact_applicability_uncertain'),
                            'reason': reason,
                            'semantic_card_path': str((impact_root / 'semantic-card.json').relative_to(args.output))})
                        continue

                    selected_p = disposition['precondition_ids']
                    for intent_id in disposition['intent_ids']:
                        claim_id = claim_id_for_impact_intent(impact_id, intent_id)
                        record_key = impact_intent_key(impact_id, intent_id)
                        target_output = impact_root / 'intents' / intent_id
                        target_output.mkdir(parents=True, exist_ok=False)
                        pair_card = build_impact_card(
                            elements_raw, impact_id, applicability,
                            intent_id=intent_id)
                        write_json(target_output / 'semantic-card.json', pair_card)
                        target_elements_raw = target_elements(
                            elements_raw, impact_id, pair_card)
                        target_input = target_formal_input(
                            formal_input, target_elements_raw, pair_card)
                        relation_context = faithfulness_relation_context(
                            elements_raw, catalog,
                            excluded_source_ids=set(selected_p) |
                            {intent_id, impact_id})
                        # semantic-live-23 adds the same bounded excerpts to
                        # generation. Earlier prompt versions keep their exact
                        # historical inputs for reproducible replay.
                        if features.get('relation_context_generation', False):
                            target_input['relation_context'] = relation_context
                        target_payload = compact_json(target_input)
                        target_prompt = (prompt + '\nTARGET IMPACT ID: ' + impact_id +
                            '\nTARGET INTENT SOURCE ID: ' + intent_id +
                            '\nThis is one independent P/I/V claim for this Impact and this '
                            'single I source. Other selected I sources for this Impact are '
                            'formalized separately; do not combine them with AND/OR or treat '
                            'them as alternatives. The applicability stage froze every source. '
                            'Copy every selected P ID into precondition_ids, use exactly the '
                            'TARGET INTENT ID as intent_id, and preserve this Impact as V. '
                            'Do not reselect, omit, replace, supplement, or reassess sources. '
                            'Frozen P IDs: ' + compact_json(selected_p) +
                            '. Frozen I ID: ' + compact_json(intent_id) +
                            '. Frozen Impact ID: ' + compact_json(impact_id) +
                            '. Convert this one P/I/V directly into the rule representation. '
                            + ('Do not apply a formalisability, numeric, unit, satisfiability, '
                               'or coverage screen. Return the generated rule candidate; a '
                               'separate post-generation audit will assess P/I/V fidelity. '
                               'Keep the frozen source IDs even if a formula needs review.\n'
                               if features.get('fidelity_only_rules') else
                               'If the grammar cannot express a frozen source, record a blocking '
                               'representation limitation without changing the source IDs.\n'))
                        target_attempts = []
                        try:
                            target_plan, target_formal, target_unresolved = request_formalization(
                                target_payload, target_prompt, model, target_output,
                                args.formal_retries, True, target_elements_raw,
                                features['structured_unresolved'],
                                numeric_guard=features['numeric_guard'],
                                address_guard=features['address_guard'],
                                extract_fn=extract_fn, attempts=target_attempts,
                                mechanical_salvage=args.mechanical_salvage,
                                local_repair=features['local_repair'],
                                exclude_protocol_identifiers=features['protocol_identifier_exclusion'],
                                relax_assumptions=features['assumption_numeric_relief'],
                                duplicate_predicate_gate=features['duplicate_predicate_gate'],
                                partial_formalization=features['partial_formalization'],
                                on_attempt=record_model_attempt,
                                faithfulness_audit=audit_extract_fn,
                                faithfulness_audit_model=audit_model,
                                faithfulness_audit_on_attempt=record_model_attempt,
                                audit_relations=True,
                                candidate_gate=(None if features.get(
                                    'fidelity_only_rules') else candidate_gate),
                                frozen_source_ids={
                                    'precondition_ids': selected_p,
                                    'intent_id': intent_id,
                                    'impact_ids': [impact_id]},
                                fidelity_only_rules=features.get(
                                    'fidelity_only_rules', False),
                                relation_context=relation_context,
                                relationship_trace_enabled=features.get(
                                    'relationship_trace', False),
                                synthesis_claim_id=claim_id)
                            # request_formalization already returns the exact rule
                            # whose generated representation was fidelity-audited.
                            # Do not synthesize it a second time after the audit.
                            audit = next((row.get('semantic_faithfulness_audit')
                                          for row in reversed(target_attempts)
                                          if row.get('semantic_faithfulness_audit') is not None),
                                         None)
                            fidelity_status = (
                                audit.get('fidelity_status') or
                                (faithfulness_status({
                                    'checks': audit.get('checks', []),
                                    **({'piv_relation': audit['piv_relation']}
                                       if audit.get('piv_relation') else {})})
                                 if audit else 'unavailable'))
                            relation_reasons = reject_vacuous_safety(
                                target_plan, target_formal, claim_id=claim_id)
                            if relation_reasons:
                                raise ValueError(
                                    'direct P/I/V relationship is absent or infeasible: ' +
                                    '; '.join(relation_reasons))
                            successful.append((impact_id, intent_id, target_formal))
                            write_json(target_output / 'formal-plan.json', target_plan)
                            write_json(target_output / 'formalization-ids.json', target_formal)
                            write_json(target_output / 'status.json', {
                                'status': 'formalized_candidate',
                                'impact_id': impact_id, 'intent_id': intent_id,
                                'claim_id': claim_id,
                                'fidelity_status': fidelity_status,
                                'attempts': target_attempts})
                            plan_records.append({
                                'impact_id': impact_id, 'intent_id': intent_id,
                                'claim_id': claim_id, 'status': 'formalized_candidate',
                                'fidelity_status': fidelity_status,
                                'attempts': target_attempts,
                                'semantic_card_path': str((target_output / 'semantic-card.json').relative_to(args.output)),
                                'formal_plan_path': str((target_output / 'formal-plan.json').relative_to(args.output))})
                            if features['relation_alignment']:
                                review_records['relation_alignment'][record_key] = classified_relation_alignment(
                                    target_plan, target_elements_raw,
                                    allow_missing=features.get('frozen_piv_sources', False))
                            if features['requirement_source_review']:
                                review_records['requirement_source_review'][record_key] = requirement_source_review(
                                    target_elements_raw, target_plan)
                            if features['intent_scope_review']:
                                review_records['intent_scope_review'][record_key] = intent_scope_review(
                                    target_plan, target_elements_raw)
                            if features['example_pinning_review']:
                                review_records['example_pinning_review'][record_key] = example_pinning_review(
                                    target_plan, target_elements_raw)
                            if features['placeholder_predicate_review']:
                                review_records['placeholder_predicate_review'][record_key] = placeholder_predicate_review(
                                    target_elements_raw, target_plan)
                            if features['mixed_unit_scaling_review']:
                                review_records['mixed_unit_scaling_review'][record_key] = mixed_unit_scaling_review(
                                    target_plan, target_elements_raw)
                            if features['symbol_table_review']:
                                review_records['symbol_table_review'][record_key] = symbol_table_review(
                                    target_plan)
                            if target_unresolved is not None:
                                review_records['unresolved_review'][record_key] = target_unresolved
                            audit_path = target_output / 'semantic-faithfulness-audit.json'
                            if audit_path.is_file():
                                review_records['semantic_faithfulness_audit'][record_key] = json.loads(
                                    audit_path.read_text())
                        except ValueError as exc:
                            reason = f'No rule candidate produced after bounded generation: {exc}'
                            failure_family = formal_failure_family(exc)
                            failures.append((impact_id, intent_id, reason))
                            write_json(target_output / 'status.json', {
                                'status': 'unformalized', 'impact_id': impact_id,
                                'intent_id': intent_id, 'claim_id': claim_id,
                                'failure_family': failure_family, 'reason': reason,
                                'attempts': target_attempts})
                            plan_records.append({
                                'impact_id': impact_id, 'intent_id': intent_id,
                                'claim_id': claim_id, 'status': 'unformalized',
                                'failure_family': failure_family, 'reason': reason,
                                'attempts': target_attempts,
                                'semantic_card_path': str((target_output / 'semantic-card.json').relative_to(args.output))})

                model_candidate = {'schema_version': 'report-formal-plan-set/2',
                                   'claims': plan_records}
                write_json(args.output / 'semantic-cards.json', {
                    'schema_version': 'stage2-impact-semantic-cards/1',
                    'cards': semantic_cards,
                })
                formal_raw = merge_claim_formalizations(
                    successful, elements_raw, failures,
                    include_failed_claims=False)
                unresolved_rows = list(review_records['unresolved_review'].items())
                unresolved_review = ({
                    'blocks_candidate_acceptance': any(
                        review.get('blocks_candidate_acceptance')
                        for _, review in unresolved_rows),
                    'items': [dict(item, pair_id=pair_id)
                              for pair_id, review in unresolved_rows
                              for item in review.get('items', [])],
                } if unresolved_rows else None)
                write_json(args.output / 'formal-plan.json', model_candidate)
                write_json(args.output / 'formalization-ids.json', formal_raw)
                attempts = []
                for attempt_path in (args.output / 'impact-formalizations').glob(
                        '*/intents/*/formalization-attempts.json'):
                    attempts.extend(json.loads(attempt_path.read_text()))
                write_json(args.output / 'formalization-attempts.json', attempts)
                for name, by_pair in review_records.items():
                    if by_pair:
                        filename = ('unresolved-review.json' if name == 'unresolved_review'
                                    else name.replace('_', '-') + '.json')
                        write_json(args.output / filename, {
                            'schema_version': 'stage2-impact-review-set/2',
                            'by_impact_intent': by_pair})
            elif features.get('impact_level_claims') and plan_mode and args.evidence_mode == 'ids':
                impact_ids = [row['id'] for row in elements_raw['statements']
                              if row['kind'] == 'impact']
                if not 1 <= len(impact_ids) <= MAX_IMPACTS:
                    raise ValueError(
                        f'impact-level claims require one to {MAX_IMPACTS} grounded impacts')
                applicability, applicability_attempts = request_impact_applicability(
                    elements_raw, catalog, model, args.output, extract_fn=extract_fn,
                    on_attempt=record_model_attempt)
                write_json(args.output / 'impact-applicability.json', applicability)
                eligible_impact_ids = [
                    row['impact_id'] for row in applicability['impacts']
                    if row['status'] == 'selected']
                successful, failures, plan_records, semantic_cards = [], [], [], []
                review_records = {name: {} for name in (
                    'relation_alignment', 'requirement_source_review',
                    'intent_scope_review', 'example_pinning_review',
                    'placeholder_predicate_review', 'mixed_unit_scaling_review',
                    'symbol_table_review', 'unresolved_review',
                    'semantic_faithfulness_audit')}
                for impact_id in impact_ids:
                    target_output = args.output / 'impact-formalizations' / impact_id
                    target_output.mkdir(parents=True, exist_ok=False)
                    semantic_card = build_impact_card(
                        elements_raw, impact_id, applicability)
                    semantic_cards.append(semantic_card)
                    write_json(target_output / 'semantic-card.json', semantic_card)
                    target_elements_raw = target_elements(
                        elements_raw, impact_id, semantic_card)
                    disposition = applicability_by_impact(applicability)[impact_id]
                    if disposition['status'] != 'selected':
                        reason = disposition['reason']
                        failures.append((impact_id, reason))
                        write_json(target_output / 'status.json', {
                            'status': disposition['status'],
                            'failure_family': ('no_applicable_explicit_intent'
                                               if disposition['status'] ==
                                               'explicit_but_insufficient'
                                               else 'impact_applicability_uncertain'),
                            'reason': reason, 'attempts': []})
                        plan_records.append({'impact_id': impact_id,
                                             'claim_id': claim_id_for_impact(impact_id),
                                             'status': disposition['status'],
                                             'failure_family': ('no_applicable_explicit_intent'
                                                                if disposition['status'] ==
                                                                'explicit_but_insufficient'
                                                                else 'impact_applicability_uncertain'),
                                             'reason': reason,
                                             'semantic_card_path': str((target_output / 'semantic-card.json').relative_to(args.output))})
                        continue
                    target_input = target_formal_input(
                        formal_input, target_elements_raw, semantic_card)
                    target_payload = compact_json(target_input)
                    selected_p = semantic_card['formalizability']['applicability'][
                        'precondition_ids']
                    selected_i = semantic_card['formalizability']['applicability'][
                        'intent_ids']
                    if len(selected_i) != 1:
                        reason = (
                            'The identified Impact has multiple applicable I sources, '
                            'but the current rule schema represents one I property per '
                            'Impact; keep it in the complete-P/I/V denominator and '
                            'review the representation.')
                        failures.append((impact_id, reason))
                        write_json(target_output / 'status.json', {
                            'status': 'unformalized',
                            'failure_family': 'unsupported_rule_schema',
                            'reason': reason, 'attempts': []})
                        plan_records.append({
                            'impact_id': impact_id,
                            'claim_id': claim_id_for_impact(impact_id),
                            'status': 'unformalized',
                            'failure_family': 'unsupported_rule_schema',
                            'reason': reason,
                            'semantic_card_path': str((target_output / 'semantic-card.json').relative_to(args.output))})
                        continue
                    target_prompt = (prompt + '\nTARGET IMPACT ID: ' + impact_id +
                                     '\nThe applicability stage already identified and froze '
                                     'the P/I/V sources for this complete Impact. Copy every '
                                     'selected P source into precondition_ids and use the sole '
                                     'selected I source as intent_id; do not make a second source '
                                     'selection. Preserve this Impact as V. Frozen P IDs: ' +
                                     compact_json(selected_p) + '. Frozen I ID: ' +
                                     compact_json(selected_i[0]) + '. Convert these sources '
                                     'directly into the rule representation. Do not reassess '
                                     'applicability/completeness or return the Impact as unresolved '
                                     'because you would prefer different sources. If the rule '
                                     'grammar cannot express a frozen source, report that as a '
                                     'blocking representation limitation while keeping all frozen '
                                     'source IDs.\n')
                    target_attempts = []
                    try:
                        target_plan, target_formal, target_unresolved = request_formalization(
                            target_payload, target_prompt, model, target_output,
                            args.formal_retries, True, target_elements_raw,
                            features['structured_unresolved'],
                            numeric_guard=features['numeric_guard'],
                            address_guard=features['address_guard'],
                            extract_fn=extract_fn, attempts=target_attempts,
                            mechanical_salvage=args.mechanical_salvage,
                            local_repair=features['local_repair'],
                            exclude_protocol_identifiers=features['protocol_identifier_exclusion'],
                            relax_assumptions=features['assumption_numeric_relief'],
                            duplicate_predicate_gate=features['duplicate_predicate_gate'],
                            partial_formalization=features['partial_formalization'],
                            on_attempt=record_model_attempt,
                            faithfulness_audit=audit_extract_fn,
                            faithfulness_audit_model=audit_model,
                            faithfulness_audit_on_attempt=record_model_attempt,
                            audit_relations=True,
                            candidate_gate=candidate_gate,
                            frozen_source_ids={
                                'precondition_ids': selected_p,
                                'intent_id': selected_i[0],
                                'impact_ids': [impact_id]})
                        if (set(target_plan.get('precondition_ids', [])) !=
                                set(selected_p) or
                                len(target_plan.get('precondition_ids', [])) !=
                                len(selected_p)):
                            raise ValueError(
                                'formal plan did not preserve all frozen P source IDs')
                        if target_plan.get('intent_id') != selected_i[0]:
                            raise ValueError(
                                'formal plan did not preserve the frozen I source ID')
                        if target_plan.get('impact_ids') != [impact_id]:
                            raise ValueError('formal plan changed the supplied target impact')
                        claim_id = claim_id_for_impact(impact_id)
                        target_formal = synthesize_id_formalization(
                            target_plan, target_elements_raw, claim_id=claim_id,
                            include_unselected_limitations=False)
                        successful.append((impact_id, target_formal))
                        write_json(target_output / 'formal-plan.json', target_plan)
                        write_json(target_output / 'formalization-ids.json', target_formal)
                        write_json(target_output / 'status.json', {
                            'status': 'formalized_candidate',
                            'attempts': target_attempts})
                        plan_records.append({'impact_id': impact_id, 'claim_id': claim_id,
                                             'status': 'formalized_candidate',
                                             'attempts': target_attempts,
                                             'semantic_card_path': str((target_output / 'semantic-card.json').relative_to(args.output)),
                                             'formal_plan_path': str((target_output / 'formal-plan.json').relative_to(args.output))})
                        if features['relation_alignment']:
                            review_records['relation_alignment'][impact_id] = classified_relation_alignment(
                                target_plan, elements_raw,
                                allow_missing=features.get('frozen_piv_sources', False))
                        if features['requirement_source_review']:
                            review_records['requirement_source_review'][impact_id] = requirement_source_review(elements_raw, target_plan)
                        if features['intent_scope_review']:
                            review_records['intent_scope_review'][impact_id] = intent_scope_review(target_plan, elements_raw)
                        if features['example_pinning_review']:
                            review_records['example_pinning_review'][impact_id] = example_pinning_review(target_plan, elements_raw)
                        if features['placeholder_predicate_review']:
                            review_records['placeholder_predicate_review'][impact_id] = placeholder_predicate_review(elements_raw, target_plan)
                        if features['mixed_unit_scaling_review']:
                            review_records['mixed_unit_scaling_review'][impact_id] = mixed_unit_scaling_review(target_plan, elements_raw)
                        if features['symbol_table_review']:
                            review_records['symbol_table_review'][impact_id] = symbol_table_review(target_plan)
                        if target_unresolved is not None:
                            review_records['unresolved_review'][impact_id] = target_unresolved
                        audit_path = target_output / 'semantic-faithfulness-audit.json'
                        if audit_path.is_file():
                            review_records['semantic_faithfulness_audit'][impact_id] = json.loads(audit_path.read_text())
                    except ValueError as exc:
                        reason = f'No rule candidate produced after bounded generation: {exc}'
                        failure_family = formal_failure_family(exc)
                        failures.append((impact_id, reason))
                        write_json(target_output / 'status.json', {
                            'status': 'unformalized', 'failure_family': failure_family,
                            'reason': reason,
                            'attempts': target_attempts})
                        plan_records.append({'impact_id': impact_id,
                                             'claim_id': claim_id_for_impact(impact_id),
                                             'status': 'unformalized',
                                             'failure_family': failure_family,
                                             'reason': reason,
                                             'attempts': target_attempts,
                                             'semantic_card_path': str((target_output / 'semantic-card.json').relative_to(args.output))})
                        attempts.extend(target_attempts)
                model_candidate = {'schema_version': 'report-formal-plan-set/1',
                                   'claims': plan_records}
                write_json(args.output / 'semantic-cards.json', {
                    'schema_version': 'stage2-impact-semantic-cards/1',
                    'cards': semantic_cards,
                })
                formal_raw = merge_claim_formalizations(
                    successful, elements_raw, failures,
                    include_failed_claims=False)
                unresolved_rows = list(review_records['unresolved_review'].items())
                unresolved_review = ({
                    'blocks_candidate_acceptance': any(
                        review.get('blocks_candidate_acceptance') for _, review in unresolved_rows),
                    'items': [dict(item, impact_id=impact_id)
                              for impact_id, review in unresolved_rows
                              for item in review.get('items', [])],
                } if unresolved_rows else None)
                write_json(args.output / 'formal-plan.json', model_candidate)
                write_json(args.output / 'formalization-ids.json', formal_raw)
                attempts = []
                for target in impact_ids:
                    attempt_path = (args.output / 'impact-formalizations' /
                                    target / 'formalization-attempts.json')
                    if attempt_path.is_file():
                        attempts.extend(json.loads(attempt_path.read_text()))
                write_json(args.output / 'formalization-attempts.json', attempts)
                for name, by_impact in review_records.items():
                    if by_impact:
                        filename = ('unresolved-review.json' if name == 'unresolved_review'
                                    else name.replace('_', '-') + '.json')
                        write_json(args.output / filename, {
                            'schema_version': 'stage2-impact-review-set/1',
                            'by_impact': by_impact})
            else:
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
                    faithfulness_audit_on_attempt=record_model_attempt,
                    candidate_gate=candidate_gate)
            if plan_mode:
                if not features.get('impact_level_claims'):
                    write_json(args.output / 'formal-plan.json', model_candidate)
                if features['relation_alignment']:
                    if not features.get('impact_level_claims'):
                        write_json(args.output / 'relation-alignment.json',
                                   classified_relation_alignment(model_candidate, elements_raw))
                if features['requirement_source_review']:
                    if not features.get('impact_level_claims'):
                        write_json(args.output / 'requirement-source-review.json',
                                   requirement_source_review(elements_raw, model_candidate))
                if features['intent_scope_review']:
                    if not features.get('impact_level_claims'):
                        write_json(args.output / 'intent-scope-review.json',
                                   intent_scope_review(model_candidate, elements_raw))
                if features['example_pinning_review']:
                    if not features.get('impact_level_claims'):
                        write_json(args.output / 'example-pinning-review.json',
                                   example_pinning_review(model_candidate, elements_raw))
                if features['placeholder_predicate_review']:
                    if not features.get('impact_level_claims'):
                        write_json(args.output / 'placeholder-predicate-review.json',
                                   placeholder_predicate_review(elements_raw,
                                                                model_candidate))
                if features['mixed_unit_scaling_review']:
                    if not features.get('impact_level_claims'):
                        write_json(args.output / 'mixed-unit-scaling-review.json',
                                   mixed_unit_scaling_review(model_candidate,
                                                             elements_raw))
                if features['symbol_table_review']:
                    if not features.get('impact_level_claims'):
                        write_json(args.output / 'symbol-table-review.json',
                                   symbol_table_review(model_candidate))
                if unresolved_review is not None and not features.get('impact_level_claims'):
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
                                require_complete_piv=not features.get(
                                    'fidelity_only_rules', False),
                                enforce_units=features.get('unit_guard', True),
                                fidelity_only_rules=features.get(
                                    'fidelity_only_rules', False))
        if (features.get('multi_i_claims', False) and
                'applicability' in locals() and 'plan_records' in locals()):
            bundle = apply_multi_intent_coverage(
                bundle, applicability, plan_records,
                require_fidelity=features.get('fidelity_only_rules', False))
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
            claim_symbols = (symbols_for_claim(original, formal['symbols'])
                             if impact_claim_set(formal) else formal['symbols'])
            base = {'symbols': {name: {k: v for k, v in item.items() if k != 'entity_ids'}
                                for name, item in claim_symbols.items()},
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
        assessment = stage2_assessment(
            readiness=readiness, bundle=bundle,
            eligible_impact_ids=eligible_impact_ids,
            impact_formalization_records=plan_records)
        write_json(args.output / 'stage2-assessment.json', assessment)
        write_json(args.output / 'constraints.json', bundle)
        write_json(args.output / 'auto-triage.json', triage)
        write_json(args.output / 'solver-results.json', {'scope': 'REPORT SPEC ONLY; no code T', 'claims': queries})
        stage3_declarations = declarations
        if features.get('multi_i_claims', False):
            stage3_claim_ids = {
                claim_id for row in bundle['report_impact_coverage']
                if row['status'] == 'formalized'
                for claim_id in row.get('claim_ids', [])}
            stage3_declarations = [row for row in declarations
                                   if row['claim_id'] in stage3_claim_ids]
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
                     'claims': stage3_declarations,
                     # Stage three receives only impacts represented by a
                     # complete P/I/V claim. Incomplete items remain in the
                     # applicability and constraints audit, outside the score.
                     'report_impact_coverage': [
                         row for row in bundle['report_impact_coverage']
                         if row['status'] == 'formalized'],
                     'acceptance_status': bundle['acceptance_status'],
                     'stage2_can_continue': triage['stage2_can_continue'],
                     'execution_ready': False, 'code_alignment_status': 'not_attempted',
                     'required_next_steps': ['Review semantic intent, effect coverage and textual assumptions',
                                             'Bind symbols/checkpoints to the paired PoC, without changing report claims',
                                             'Build actual code transition T with machine arithmetic and revert semantics'],
                     'consistency_verdict': 'not_evaluated'}
        if (args.output / 'semantic-cards.json').is_file():
            interface.update({
                'semantic_cards_path': 'semantic-cards.json',
                'semantic_cards_sha256': r.sha(
                    (args.output / 'semantic-cards.json').read_bytes()),
            })
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
                     'mixed-unit-scaling-review.json', 'symbol-table-review.json',
                     'example-pinning-review.json'):
            if (args.output / name).is_file():
                interface[name.replace('-', '_').removesuffix('.json') + '_path'] = name
                interface[name.replace('-', '_').removesuffix('.json') + '_sha256'] = \
                    r.sha((args.output / name).read_bytes())
        interface['stage3_feedback_command'] = (
            'lib.stage3_consistency.ingest_feedback(<run-dir>, '
            '<stage3-consistency-feedback/1 JSON path>)')
        write_json(args.output / 'stage3-spec.json', interface)
        status = {key: bundle[key] for key in ('core_formalization_status', 'acceptance_status',
                                              'external_model_invocations', 'consistency_verdict')}
        status.update({'stage2_can_continue': triage['stage2_can_continue'],
                       'narrative_sufficiency_status': assessment['narrative_sufficiency']['status'],
                       'rule_formalization_status': assessment['rule_formalization']['status'],
                       'pending_impact_count': len(assessment['rule_formalization']['pending_impacts']),
                       'continuation_policy': 'warn_and_continue' if args.continue_on_review else 'strict_exit',
                       'warnings': triage['reasons'],
                       'continuation_blockers': triage['continuation_blockers']})
        if features.get('impact_inventory_stage'):
            rule_result = assessment['rule_formalization']
            impact_count = rule_result.get('eligible_complete_piv_count', 0)
            formalized_count = rule_result.get(
                'formalized_complete_piv_count', 0)
            status.update({
                'impact_inventory_status': ('needs_review'
                                            if impact_inventory['ambiguities']
                                            else 'extracted'),
                'impact_source_status': 'marked_section_present',
                'impact_completion_status': (
                    'not_applicable' if impact_count == 0 else
                    'complete' if formalized_count == impact_count else 'partial'),
                'impact_denominator_policy':
                    'complete_report_supported_piv_only',
                'impact_count': impact_count,
                'formalized_impact_count': formalized_count,
                'formalization_rate': rule_result.get('formalization_rate'),
            })
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
