#!/usr/bin/env python3
"""Paired live-23 retest over the exact live-21 frozen P/I/V source pairs."""
import concurrent.futures
import functools
import json
import sys
import threading
from pathlib import Path

STAGE2 = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(STAGE2))
for path in (STAGE2 / 'lib', STAGE2 / 'cli'):
    sys.path.insert(0, str(path))

from cli.semantic_pipeline import (  # noqa: E402
    allowed_statement_ids, faithfulness_relation_context, load_report,
    numeric_fact_inventory, request_formalization,
)
from cli.semantic_pipeline import lean_formal_input  # noqa: E402
from lib.deepseek import extract_deepseek  # noqa: E402
from lib.impact_cards import (  # noqa: E402
    build_impact_card, target_elements, target_formal_input,
)
from prompts.active import resolve_prompt_set  # noqa: E402

HERE = Path(__file__).resolve().parent
SOURCE_ROOT = Path('/root/poc_repro_work/verified_flatten_pass_1568_exact_cases')
INPUT_RUNS = STAGE2 / 'evaluation/prompt_live20_live16_paired_retest_10/runs'
FROZEN = STAGE2 / 'evaluation/prompt_live21_frozen_sources_paired/FROZEN_SOURCE_PAIRS.json'
MODEL = 'deepseek-flash'
PROVIDER = functools.partial(extract_deepseek, proxy='direct')
CALLS = 0
CALL_LOCK = threading.Lock()


def counted_extract(payload, output, model, prompt):
    global CALLS
    with CALL_LOCK:
        CALLS += 1
    return PROVIDER(payload, output, model, prompt)


def read_json(path):
    return json.loads(Path(path).read_text())


def make_prompt(prompt, impact_id, intent_id, p_ids):
    return (prompt + '\nTARGET IMPACT ID: ' + impact_id +
            '\nTARGET INTENT SOURCE ID: ' + intent_id +
            '\nThis is one independent P/I/V claim for this Impact and this '
            'single I source. Other selected I sources for this Impact are '
            'formalized separately; do not combine them with AND/OR or treat '
            'them as alternatives. The applicability stage froze every source. '
            'Copy every selected P ID into precondition_ids, use exactly the '
            'TARGET INTENT ID as intent_id, and preserve this Impact as V. '
            'Do not reselect, omit, replace, supplement, or reassess sources. '
            'Frozen P IDs: ' + json.dumps(p_ids) +
            '. Frozen I ID: ' + json.dumps(intent_id) +
            '. Frozen Impact ID: ' + json.dumps(impact_id) +
            '. Convert this one P/I/V directly into the rule representation. '
            'Do not apply a formalisability, numeric, unit, satisfiability, or '
            'coverage screen. Return the generated rule candidate; the single '
            'post-generation audit will assess source transcription and the '
            'P/I/V relationship. Keep the frozen source IDs even if a formula '
            'needs review.\n')


def run_one(pair):
    case_id = pair['case_id']
    impact_id = pair['impact_id']
    intent_id = pair['intent_id']
    p_ids = pair['precondition_ids']
    source_dir = INPUT_RUNS / case_id
    elements = read_json(source_dir / 'elements-ids.json')
    catalog = read_json(source_dir / 'evidence-catalog.json')
    applicability = read_json(source_dir / 'impact-applicability.json')
    text, raw, provenance = load_report(case_dir=SOURCE_ROOT / case_id)

    version = 'semantic-live-23'
    run_dir = HERE / 'live-23' / case_id / impact_id / intent_id
    run_dir.mkdir(parents=True, exist_ok=False)
    card = build_impact_card(elements, impact_id, applicability, intent_id)
    scoped = target_elements(elements, impact_id, card)
    base = lean_formal_input(elements)
    base['numeric_fact_inventory'] = numeric_fact_inventory(elements)
    base['allowed_statement_ids'] = allowed_statement_ids(elements)
    payload = target_formal_input(base, scoped, card)
    relation_context = faithfulness_relation_context(
        elements, catalog, excluded_source_ids=set(p_ids) | {intent_id, impact_id})
    payload['relation_context'] = relation_context
    prompt_set = resolve_prompt_set(version, 'ids', 'core')
    prompt = make_prompt(prompt_set.formal_prompt, impact_id, intent_id, p_ids)

    (run_dir / 'semantic-card.json').write_text(json.dumps(card, indent=2) + '\n')
    (run_dir / 'input-elements.json').write_text(json.dumps(scoped, indent=2) + '\n')
    (run_dir / 'input-payload.json').write_text(json.dumps(payload, indent=2) + '\n')
    (run_dir / 'relation-context.json').write_text(
        json.dumps(relation_context, indent=2, ensure_ascii=False) + '\n')
    record = {'case_id': case_id, 'impact_id': impact_id,
              'intent_id': intent_id, 'precondition_ids': p_ids,
              'prompt_version': version,
              'relation_context_statement_count': len(relation_context)}
    try:
        plan, formal, _ = request_formalization(
            json.dumps(payload, separators=(',', ':')), prompt, MODEL, run_dir,
            retries=1, plan_mode=True, elements=scoped, structured=False,
            extract_fn=counted_extract, attempts=[], numeric_guard=False,
            address_guard=False, mechanical_salvage=False, local_repair=True,
            exclude_protocol_identifiers=False, relax_assumptions=True,
            duplicate_predicate_gate=False, partial_formalization=False,
            faithfulness_audit=counted_extract, faithfulness_audit_model=MODEL,
            faithfulness_audit_on_attempt=None, audit_relations=True,
            candidate_gate=None,
            frozen_source_ids={'precondition_ids': p_ids,
                               'intent_id': intent_id,
                               'impact_ids': [impact_id]},
            fidelity_only_rules=True, relation_context=relation_context,
            synthesis_claim_id=f'impact_claim_{impact_id}_{intent_id}')
        audit = read_json(run_dir / 'semantic-faithfulness-audit.json')
        record.update({'generated': True,
                       'fidelity_passed': audit.get('verdict_consistent'),
                       'fidelity_status': audit.get('fidelity_status'),
                       'audit': audit,
                       'formal_plan': plan,
                       'formalization': formal})
    except Exception as exc:
        audit_path = run_dir / 'semantic-faithfulness-audit.json'
        if audit_path.exists():
            record['audit'] = read_json(audit_path)
        record.update({'generated': False, 'error_type': type(exc).__name__,
                       'error': str(exc)})
    (run_dir / 'result.json').write_text(json.dumps(record, indent=2) + '\n')
    return record


def main():
    frozen = read_json(FROZEN)
    pairs = frozen['pairs']
    if len(pairs) != 52:
        raise RuntimeError(f'expected 52 frozen source pairs, found {len(pairs)}')
    (HERE / 'FROZEN_SOURCE_PAIRS.json').write_text(
        json.dumps(frozen, indent=2) + '\n')
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(run_one, pair) for pair in pairs]
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            results.append(result)
            print(json.dumps({
                'case': result['case_id'], 'impact': result['impact_id'],
                'intent': result['intent_id'], 'version': result['prompt_version'],
                'generated': result['generated'],
                'fidelity_status': result.get('fidelity_status'),
            }, ensure_ascii=False), flush=True)
    output = {
        'schema_version': 'stage2-frozen-source-live23-relation-context-generation/1',
        'source_run': 'prompt_live21_frozen_sources_paired',
        'model': MODEL, 'provider': 'deepseek',
        'external_model_invocations': CALLS,
        'frozen_source_pair_count': len(pairs), 'results': results,
    }
    (HERE / 'PAIRED_RESULTS.json').write_text(json.dumps(output, indent=2) + '\n')


if __name__ == '__main__':
    main()
