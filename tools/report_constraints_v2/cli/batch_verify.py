"""Bounded real-report batch runner, and read-only offline replay verifier.

合并自两个模块（S9），函数体逐字未改；仅三处结构性调整：
  1. HERE 深度 +1（本文件在 cli/ 下，semantic_pipeline.py 的子进程调用需指向阶段二根 shim）
  2. verify_semantic 的模块级 argparse 包成 verify_main()
  3. 统一 __main__ 分派器（见文件末尾）

  - run_semantic_batch.py : bounded real-report batch, five cases max with explicit
                            provider/retry controls -> `batch` 命令, main()
  - verify_semantic.py    : read-only replay of grounded semantic outputs and manifest
                            hashes -> `verify` 命令, verify_main()
"""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import copy
import json
from pathlib import Path
import subprocess
import sys
import time

from prompts.registry import (DEFAULT_VERSION, FEATURE_NAMES, LIVE_VERSION_NAMES,
                              SELECTABLE_VERSIONS,
                              feature_enabled)
from prompts.active import resolve_prompt_set
from prompts.current import (IMPACT_APPLICABILITY_PROMPT,
                             IMPACT_APPLICABILITY_PROMPT_V2,
                             IMPACT_APPLICABILITY_PROMPT_V15)
from prompts.live16_snapshot import (
    IMPACT_APPLICABILITY_PROMPT as IMPACT_APPLICABILITY_PROMPT_V16)

from lib import report_only as r
from lib.salvage import check_numeric_plan, check_address_plan
from lib.salvage import (drop_unused_invalid_symbols, example_pinning_review,
                         salvage_formal_response,
                         mixed_unit_scaling_review)
from lib.semantic_core import (compile_bundle, normalize_readiness,
                           impact_claim_set, normalize_truth_binding, require, symbols_for_claim,
                           validate_elements)
from lib.multi_impact import (claim_id_for_impact,
                              claim_id_for_impact_intent,
                              apply_multi_intent_coverage,
                              impact_intent_key,
                              merge_claim_formalizations)
from lib.impact_cards import (applicability_by_impact, applicability_payload,
                              build_impact_card,
                              explicit_intent_ids, validate_applicability,
                              final_formalization_scope, formalization_scope,
                              target_elements,
                              not_applicable_impacts_for,
                              target_formal_input,
                              MAX_SELECTED_INTENT_RULES)
from lib.impact_inventory import (MAX_IMPACTS, merge_impact_inventory,
                                  validate_impact_inventory)
from lib.plan_synthesizer import (check_distinct_p_predicates, classified_relation_alignment,
                              faithfulness_mismatches, faithfulness_status,
                              identical_p_predicates,
                              intent_scope_review, placeholder_predicate_review,
                              relax_unsupported_relation, requirement_source_review,
                              structured_unresolved_review, symbol_table_review,
                              synthesize_id_formalization,
                              validate_faithfulness_verdict)
from lib.ingest import (PROMPT as READINESS_PROMPT, build_catalog,
                              explicit_impact_evidence_ids,
                              hydrate_elements, hydrate_formalization,
                              model_payload as readiness_payload,
                              validate_readiness)
from lib.solving import solve_queries, verify_witness
from lib.solving import attach_review
from lib.salvage import normalize_attack_step_roles, normalize_element_ids
from cli.semantic_pipeline import (allowed_statement_ids, compact_json,
                                   faithfulness_relation_context,
                                   lean_formal_input, model_catalog,
                                   numeric_fact_inventory, referenced_evidence_ids,
                                   restore_frozen_repair_fields,
                                   restore_frozen_referenced_symbols,
                                   stage2_assessment,
                                   validate_core_element_candidate)


# ------------------- 节选自 run_semantic_batch.py -------------------

HERE = Path(__file__).resolve().parents[1]  # 阶段二根目录（shim 所在），不是本文件目录；见下方 semantic_pipeline.py 子进程调用


def discover_manifest(root, limit, parser):
    """Build the same manifest shape from a directory of case folders."""
    if not root.is_dir():
        parser.error(f'--reports-root is not a directory: {root}')
    cases = [{'id': report.parent.name, 'case_directory': report.parent.name}
             for report in sorted(root.glob('*/report.json'))]
    if not cases:
        parser.error(f'no */report.json found under {root}')
    if len(cases) > limit:
        print(f'discovered {len(cases)} cases; taking the first {limit} '
              f'(raise --max-cases to include more)', flush=True)
        cases = cases[:limit]
    return {'data_root': str(root), 'cases': cases}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path,
                        help='explicit case list (mutually exclusive with --reports-root)')
    parser.add_argument('--reports-root', type=Path,
                        help='discover <dir>/<case>/report.json automatically')
    parser.add_argument('--max-cases', type=int, default=5)
    parser.add_argument('--resume', action='store_true',
                        help='reuse --output and skip cases that already have status.json')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--allow-report-upload', action='store_true')
    parser.add_argument('--provider', choices=('opencode', 'deepseek'), default='opencode')
    parser.add_argument('--model', default='opencode-go/deepseek-v4-flash')
    parser.add_argument('--concurrency', type=int, choices=(1, 2), default=2)
    parser.add_argument('--readiness-retries', type=int, choices=(0, 1), default=1)
    parser.add_argument('--element-retries', type=int, choices=(0, 1), default=1)
    parser.add_argument('--formal-retries', type=int, choices=(0, 1, 2), default=1)
    parser.add_argument('--lean-formal-input', action='store_true')
    parser.add_argument('--continue-on-review', action='store_true')
    parser.add_argument('--claim-verdict', choices=('legacy', 'signals'),
                        default='legacy',
                        help='forwarded to every run subprocess; legacy keeps the '
                             'historical veto on report-declared uncertainty')
    parser.add_argument('--deepseek-proxy', metavar='POLICY', default='environment',
                        help='forwarded to every run subprocess; see '
                             'cli/semantic_pipeline.py --deepseek-proxy')
    parser.add_argument('--prompt-version', choices=SELECTABLE_VERSIONS,
                        default=DEFAULT_VERSION)
    args = parser.parse_args()
    # Child pipelines run with cwd=HERE.  Resolve once in the caller so a
    # user-supplied relative output does not become relative to a different
    # directory in the child and leave the parent looking in the wrong tree.
    args.output = args.output.resolve()
    if not args.allow_report_upload:
        parser.error('explicit consent required; no model calls made')
    if (args.manifest is None) == (args.reports_root is None):
        parser.error('provide exactly one of --manifest or --reports-root')
    manifest = (json.loads(args.manifest.read_text()) if args.manifest
                else discover_manifest(args.reports_root, args.max_cases, parser))
    if set(manifest) != {'data_root', 'cases'} or not 1 <= len(manifest['cases']) <= 5:
        parser.error('manifest must contain one to five cases only')
    ids = [row['id'] for row in manifest['cases']]
    if len(set(ids)) != len(ids):
        parser.error('duplicate case ID')
    for row in manifest['cases']:
        if set(row) != {'id', 'case_directory'}:
            parser.error('manifest may contain IDs/paths only, never reference answers')
        for value in row.values():
            if not value or Path(value).name != value or value in ('.', '..'):
                parser.error('case IDs/paths must be single safe path components')
        if not (Path(manifest['data_root']) / row['case_directory'] / 'report.json').is_file():
            parser.error('report not found')
    args.output.mkdir(parents=True, exist_ok=args.resume)
    (args.output / 'case-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')

    def run(row):
        output = args.output / row['id']
        if args.resume and (output / 'status.json').is_file():
            print('SKIP ' + row['id'], flush=True)
            return {'case_id': row['id'], 'exit_code': None, 'resumed': True,
                    'status': json.loads((output / 'status.json').read_text())}
        if args.resume and output.exists():
            # Incomplete run: keep the evidence, but the pipeline needs a
            # non-existent directory, so move it aside instead of deleting.
            parked = output.with_name(output.name + '.incomplete-' +
                                      time.strftime('%Y%m%dT%H%M%SZ', time.gmtime()))
            output.rename(parked)
            print(f'PARKED {output.name} -> {parked.name}', flush=True)
        command = [sys.executable, '-m', 'cli.semantic_pipeline',
                   '--case-dir', str(Path(manifest['data_root']) / row['case_directory']),
                   '--extract', '--allow-report-upload', '--provider', args.provider,
                   '--model', args.model,
                   '--prompt-version', args.prompt_version,
                   '--evidence-mode', 'ids', '--formalization-scope', 'core',
                   '--output', str(output)]
        # Must be forwarded: the child writes provenance.claim_verdict_policy,
        # and `verify` replays from that value. Dropping it would silently pin
        # every batch run back to the legacy verdict.
        command.extend(['--claim-verdict', args.claim_verdict])
        command.extend(['--deepseek-proxy', args.deepseek_proxy])
        if args.readiness_retries and args.provider == 'deepseek':
            command.extend(['--readiness-retries', str(args.readiness_retries)])
        if args.element_retries:
            command.extend(['--element-retries', str(args.element_retries)])
        if args.formal_retries:
            command.extend(['--formal-retries', str(args.formal_retries)])
        if args.lean_formal_input:
            command.append('--lean-formal-input')
        if args.continue_on_review:
            command.append('--continue-on-review')
        print('START ' + row['id'], flush=True)
        proc = subprocess.run(command, capture_output=True, text=True,
                              cwd=str(HERE))
        # stdout contains pipeline status, not credentials or environment dumps.
        (output / 'pipeline-stdout.txt').write_text(proc.stdout)
        path = output / 'status.json'
        status = json.loads(path.read_text()) if path.exists() else {'error': 'missing pipeline status'}
        result = {'case_id': row['id'], 'exit_code': proc.returncode, 'status': status}
        print(json.dumps(result), flush=True)
        return result

    results = []
    with ThreadPoolExecutor(max_workers=args.concurrency) as pool:
        futures = [pool.submit(run, row) for row in manifest['cases']]
        for future in as_completed(futures):
            results.append(future.result())
    results.sort(key=lambda row: ids.index(row['case_id']))
    # S17: request_faithfulness_audit runs with retries=1 (call + at most one
    # format retry) whenever the prompt version carries the feature, so the
    # budget must count it or `maximum_model_invocations` under-reports.
    audit_calls = (2 if feature_enabled(args.prompt_version,
                                        'semantic_faithfulness_audit') else 0)
    impact_claims = feature_enabled(args.prompt_version, 'impact_level_claims')
    impact_inventory = feature_enabled(args.prompt_version, 'impact_inventory_stage')
    formal_passes = (MAX_SELECTED_INTENT_RULES
                     if feature_enabled(args.prompt_version, 'multi_i_claims')
                     else MAX_IMPACTS if impact_claims else 1)
    applicability_calls = 2 if impact_claims else 0  # call plus one schema retry
    readiness_calls = ((1 + args.readiness_retries)
                       if args.provider == 'deepseek' else 0)
    inventory_calls = ((1 + args.element_retries) if impact_inventory else 0)
    element_calls = 1 + args.element_retries
    formal_attempts = (1 + args.formal_retries +
                       (1 if feature_enabled(args.prompt_version,
                                             'local_repair') else 0))
    per_case_calls = readiness_calls + inventory_calls + element_calls + \
        applicability_calls + \
        formal_passes * formal_attempts * (1 + audit_calls)
    summary = {'schema_version': 'real-semantic-batch/1', 'provider': args.provider,
               'model': args.model, 'prompt_version': args.prompt_version,
               'maximum_model_invocations': per_case_calls * len(ids),
               'maximum_impact_claims_per_case': formal_passes,
               'retry_count': ((args.readiness_retries if args.provider == 'deepseek' else 0) +
                               args.element_retries + args.formal_retries +
                               (1 if impact_claims else 0) +
                               (1 if impact_claims and feature_enabled(
                                   args.prompt_version, 'local_repair') else 0)),
               'concurrency': args.concurrency,
               'reference_answers_provided_to_model': False,
               'results': results, 'semantic_accuracy_percentage': None}
    (args.output / 'batch-summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    skipped = [row['case_id'] for row in results if row.get('resumed')]
    lines = ['# 阶段二批量运行汇总', '',
             f'- 提供方/模型: {args.provider} / {args.model}',
             f'- Prompt 版本: {args.prompt_version}',
             f'- 案例数: {len(ids)}（新跑 {len(ids) - len(skipped)}，续跑跳过 {len(skipped)}）',
             f'- 输出目录: {args.output}', '',
             '| 案例 | 退出码 | 验收状态 |', '| --- | ---: | --- |']
    for row in results:
        status = row.get('status') or {}
        label = (status.get('acceptance_status') or status.get('formalization_status')
                 or status.get('error') or 'unknown')
        lines.append(f"| {row['case_id']} | {row.get('exit_code')} | {label} |")
    lines += ['', 'Z3 结果只证明生成公式内部关系，不代表报告语义正确或 PoC 一致。',
              '`needs_review` 不是通过。']
    (args.output / 'batch-summary.md').write_text('\n'.join(lines) + '\n')
    print('BATCH COMPLETE', flush=True)


# ------------------- 节选自 verify_semantic.py -------------------

def accepted_model_claim_path(directory):
    attempts_path = directory / 'formalization-attempts.json'
    if not attempts_path.exists():
        return directory / 'neural-formalization/model-claim.json'
    attempts = json.loads(attempts_path.read_text())
    accepted = [row for row in attempts if row.get('outcome') == 'accepted_for_validation']
    require(len(accepted) == 1, 'formalization attempt count mismatch')
    artifact_dir = accepted[0].get('artifact_dir')
    require(artifact_dir in {'neural-formalization', 'neural-formalization-retry-1',
                             'neural-formalization-retry-2',
                             'neural-formalization-retry-3'},
            'invalid formalization artifact directory')
    return directory / artifact_dir / 'model-claim.json'


def verify_multi_intent_plans(directory, raw_elements, raw_formal, features,
                              *, acceptance_policy_version=None,
                              source_scoped_cards=False, catalog=None,
                              provenance=None):
    """Zero-call replay for one independent rule per selected (Impact, I)."""
    directory = Path(directory)
    plan_set = json.loads((directory / 'formal-plan.json').read_text())
    require(plan_set.get('schema_version') == 'report-formal-plan-set/2' and
            isinstance(plan_set.get('claims'), list),
            'invalid multi-intent formal plan set')
    impact_ids = [row['id'] for row in raw_elements['statements']
                  if row['kind'] == 'impact']
    applicability = validate_applicability(
        json.loads((directory / 'impact-applicability.json').read_text()),
        raw_elements)
    require(applicability == json.loads(
        (directory / 'impact-applicability.json').read_text()),
        'saved Impact applicability failed deterministic replay')
    applicability_rows = applicability_by_impact(applicability)
    expected_cards = [build_impact_card(raw_elements, impact_id, applicability)
                      for impact_id in impact_ids]
    cards_path = directory / 'semantic-cards.json'
    require(cards_path.is_file() and json.loads(cards_path.read_text()) == {
        'schema_version': 'stage2-impact-semantic-cards/1',
        'cards': expected_cards,
    }, 'semantic Impact cards changed')

    expected_pairs = []
    for impact_id in impact_ids:
        disposition = applicability_rows[impact_id]
        if disposition['status'] == 'selected':
            expected_pairs.extend((impact_id, intent_id)
                                  for intent_id in disposition['intent_ids'])
        else:
            expected_pairs.append((impact_id, None))
    entries = plan_set['claims']
    actual_pairs = [(row.get('impact_id'), row.get('intent_id')) for row in entries]
    require(actual_pairs == expected_pairs,
            'impact/I plan set omitted, duplicated, or reordered a frozen source pair')

    attempts_path = directory / 'impact-applicability-attempts.json'
    intent_candidates = applicability_payload(raw_elements, catalog)[
        'explicit_intent_candidates']
    if intent_candidates:
        require(attempts_path.is_file(),
                'Impact applicability call/retry record missing')
        applicability_attempts = json.loads(attempts_path.read_text())
        require(1 <= len(applicability_attempts) <= 2 and
                [row.get('attempt') for row in applicability_attempts] ==
                list(range(1, len(applicability_attempts) + 1)) and
                [row.get('artifact_dir') for row in applicability_attempts] ==
                ['impact-applicability'] +
                (['impact-applicability-retry-1']
                 if len(applicability_attempts) == 2 else []) and
                (len(applicability_attempts) == 1 or
                 applicability_attempts[0].get('outcome') == 'retryable_failure'),
                'Impact applicability retry history changed')
        accepted = [row for row in applicability_attempts
                    if row.get('outcome') == 'accepted_for_validation']
        require(len(accepted) == 1 and accepted[0] is applicability_attempts[-1],
                'Impact applicability accepted response record missing')
        response_path = directory / accepted[0]['artifact_dir'] / 'model-claim.json'
        require(response_path.is_file() and validate_applicability(
            json.loads(response_path.read_text()), raw_elements) == applicability,
            'Impact applicability response does not match saved selection')
        prompt_path = directory / 'impact-applicability' / 'prompt.txt'
        expected_payload = compact_json(applicability_payload(raw_elements, catalog))
        applicability_prompt = (
            IMPACT_APPLICABILITY_PROMPT_V2
            if features.get('direct_v_prescreen', False) else
            IMPACT_APPLICABILITY_PROMPT
            if features.get('multi_i_claims', False) else
            IMPACT_APPLICABILITY_PROMPT_V16
            if features.get('frozen_piv_sources', False) else
            IMPACT_APPLICABILITY_PROMPT_V15)
        require(prompt_path.is_file() and prompt_path.read_text() ==
                applicability_prompt + expected_payload,
                'Impact applicability request escaped report-supported candidates')
    else:
        require(not attempts_path.exists() and
                not (directory / 'impact-applicability').exists() and
                all(row['status'] == 'explicit_but_insufficient' and
                    not row['precondition_ids'] and not row['intent_ids'] and
                    row['reason'] ==
                    'No report-supported, non-inferred security intent is available.'
                    for row in applicability['impacts']),
                'empty-intent applicability should be deterministic and call-free')

    successful, failures, redundant = [], [], []
    expected_reviews = {name: {} for name in (
        'relation-alignment', 'requirement-source-review', 'intent-scope-review',
        'example-pinning-review', 'placeholder-predicate-review',
        'mixed-unit-scaling-review', 'symbol-table-review', 'unresolved-review',
        'semantic-faithfulness-audit')}
    base_prompt = (directory / 'prompt-formal.txt').read_text()

    def pair_target(impact_id, intent_id):
        return (directory / 'impact-formalizations' / impact_id /
                'intents' / intent_id)

    for entry in entries:
        impact_id, intent_id = entry['impact_id'], entry['intent_id']
        disposition = applicability_rows[impact_id]
        impact_root = directory / 'impact-formalizations' / impact_id
        require((impact_root / 'semantic-card.json').is_file() and
                json.loads((impact_root / 'semantic-card.json').read_text()) ==
                build_impact_card(raw_elements, impact_id, applicability),
                'impact source card changed')
        if intent_id is None:
            require(disposition['status'] != 'selected' and
                    entry.get('claim_id') is None,
                    'selected Impact omitted its I-source rule pair')
            saved = json.loads((impact_root / 'status.json').read_text())
            require(saved.get('status') == entry.get('status') and
                    saved.get('reason') == entry.get('reason') and
                    saved.get('failure_family') == entry.get('failure_family'),
                    'unselected Impact disposition changed')
            failures.append((impact_id, None, entry['reason']))
            continue

        require(disposition['status'] == 'selected' and
                intent_id in disposition['intent_ids'],
                'formalization used an I source outside frozen applicability')
        target = pair_target(impact_id, intent_id)
        claim_id = claim_id_for_impact_intent(impact_id, intent_id)
        require(entry.get('claim_id') == claim_id,
                'Impact/I claim ID changed')
        attempt_log = target / 'formalization-attempts.json'
        require(attempt_log.is_file() and
                json.loads(attempt_log.read_text()) == entry.get('attempts'),
                'Impact/I formalization attempt record changed')
        card = build_impact_card(raw_elements, impact_id, applicability,
                                 intent_id=intent_id)
        require((target / 'semantic-card.json').is_file() and
                json.loads((target / 'semantic-card.json').read_text()) == card and
                entry.get('semantic_card_path') ==
                f'impact-formalizations/{impact_id}/intents/{intent_id}/semantic-card.json',
                'Impact/I semantic card changed')
        scoped_elements = target_elements(raw_elements, impact_id, card)
        selected_p = disposition['precondition_ids']
        if entry.get('status') != 'formalized_candidate':
            require(entry.get('status') == 'unformalized',
                    'unknown Impact/I disposition')
            saved = json.loads((target / 'status.json').read_text())
            require(saved.get('status') == 'unformalized' and
                    saved.get('impact_id') == impact_id and
                    saved.get('intent_id') == intent_id and
                    saved.get('claim_id') == claim_id and
                    saved.get('reason') == entry.get('reason') and
                    saved.get('failure_family') == entry.get('failure_family') and
                    saved.get('attempts') == entry.get('attempts'),
                    'failed Impact/I status changed')
            failures.append((impact_id, intent_id, entry['reason']))
            continue

        require(entry.get('formal_plan_path') ==
                f'impact-formalizations/{impact_id}/intents/{intent_id}/formal-plan.json',
                'Impact/I formal plan path changed')
        status = json.loads((target / 'status.json').read_text())
        require(status.get('status') == 'formalized_candidate' and
                status.get('attempts') == entry.get('attempts') and
                status.get('fidelity_status') == entry.get('fidelity_status'),
                'successful Impact/I status changed')
        # The saved request must contain exactly this card and the one frozen I.
        if provenance and provenance.get('lean_formal_input'):
            base = lean_formal_input(raw_elements)
        else:
            allowed = (referenced_evidence_ids(raw_elements)
                       if features.get('referenced_catalog') else None)
            base = {'elements': raw_elements,
                    'evidence_catalog': model_catalog(catalog, allowed)}
            if features.get('allowed_statement_ids'):
                base['allowed_statement_ids'] = allowed_statement_ids(raw_elements)
            base['numeric_fact_inventory'] = numeric_fact_inventory(raw_elements)
        base['numeric_fact_inventory'] = numeric_fact_inventory(raw_elements)
        target_input = target_formal_input(base, scoped_elements, card)
        if features.get('relation_context_generation', False):
            target_input['relation_context'] = faithfulness_relation_context(
                raw_elements, catalog,
                excluded_source_ids=set(selected_p) | {intent_id, impact_id})
        payload = compact_json(target_input)
        suffix = ('\nTARGET IMPACT ID: ' + impact_id +
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
        sent_prompt = target / 'neural-formalization' / 'prompt.txt'
        require(sent_prompt.is_file() and sent_prompt.read_text() ==
                base_prompt + suffix + payload,
                'saved Impact/I formal request escaped its frozen sources')
        plan = json.loads((target / 'formal-plan.json').read_text())
        require(plan.get('precondition_ids') == selected_p and
                plan.get('intent_id') == intent_id and
                plan.get('impact_ids') == [impact_id],
                'formal plan changed the frozen P/I/V source pair')
        claim_path = accepted_model_claim_path(target)
        raw_claim = json.loads(claim_path.read_text())
        # A salvaged response must replay: re-apply the deterministic
        # transform to the untouched raw response and require the saved
        # claim to equal the merged result (v3.20 normalization contract).
        normalization_path = claim_path.parent / 'response-normalization.json'
        if normalization_path.exists():
            raw_response = (claim_path.parent / 'model-response.txt').read_text()
            salvaged = salvage_formal_response(raw_response)
            require(salvaged is not None,
                    'response normalization record has no matching raw response')
            require(salvaged[0] == raw_claim,
                    'salvaged model claim differs from saved claim')
            require(json.loads(normalization_path.read_text()) == salvaged[1],
                    'response normalization record changed')
        # semantic-live-24 emits the plan inside a `formal_plan` envelope with
        # `relationship_trace` as a sibling.  The generator unwraps that
        # envelope before validation; replay must apply the same deterministic
        # unwrap so historical flat plans and the new two-key envelope both
        # reach the identical normalized plan.
        if isinstance(raw_claim, dict) and isinstance(raw_claim.get('formal_plan'), dict):
            raw_claim = raw_claim['formal_plan']
        # The generator strips the audit-only trace before writing the plan;
        # a salvaged flat response may still carry it as a top-level sibling,
        # so replay drops it the same way before comparing to the saved plan.
        if features.get('relationship_trace'):
            raw_claim.pop('relationship_trace', None)
        if features.get('fidelity_only_rules'):
            raw_claim['precondition_ids'] = list(selected_p)
            raw_claim['intent_id'] = intent_id
            raw_claim['impact_ids'] = [impact_id]
        # semantic-live local repair: an accepted retry restores non-mutable
        # top-level fields from the previously audited plan, so the raw
        # model-claim alone cannot reproduce the saved plan.  Replay that
        # deterministic restoration from the prior attempt's generated rule
        # candidate before applying the remaining normalization transforms.
        accepted_attempt = next(
            row for row in entry.get('attempts', [])
            if row.get('outcome') == 'accepted_for_validation')
        accepted_index = entry['attempts'].index(accepted_attempt)
        needs_restore = (accepted_attempt.get('repair_mode') is not None or
                         bool(accepted_attempt.get('restored_frozen_fields')))
        if needs_restore:
            # The accepted retry always restores non-mutable fields from the
            # plan that was frozen as the repair base.  A normal field-scoped
            # repair uses the immediately previous generated candidate; a
            # fresh_restate retry uses the last generated candidate before the
            # null-repair attempt (which produces no generated-rule artifact).
            # Walk backward so both paths replay the same repair_base.
            prev_attempt = None
            prev_artifact = None
            for row in reversed(entry['attempts'][:accepted_index]):
                repair_base_path = (target / row['artifact_dir'] /
                                    'repair-base.json')
                generated_path = (target / row['artifact_dir'] /
                                  'generated-rule-candidate.json')
                if repair_base_path.is_file():
                    prev_attempt, prev_artifact = row, repair_base_path
                    break
                if generated_path.is_file():
                    prev_attempt, prev_artifact = row, generated_path
                    break
                model_claim_path = (target / row['artifact_dir'] /
                                    'model-claim.json')
                if model_claim_path.is_file():
                    prev_attempt, prev_artifact = row, model_claim_path
                    break
            require(prev_attempt is not None,
                    'local repair accepted without a generated prior plan')
            prev_record = json.loads(prev_artifact.read_text())
            prev_plan = (
                prev_record['formal_plan']
                if isinstance(prev_record, dict) and
                isinstance(prev_record.get('formal_plan'), dict) else
                prev_record)
            mutable_fields = tuple(accepted_attempt.get(
                'mutable_top_level_fields') or ())
            if not mutable_fields:
                for row in reversed(entry['attempts'][:accepted_index]):
                    if row.get('mutable_top_level_fields') is not None:
                        mutable_fields = tuple(row['mutable_top_level_fields'])
                        break
            raw_claim, restored = restore_frozen_repair_fields(
                copy.deepcopy(prev_plan), raw_claim, mutable_fields)
            require(restored == accepted_attempt.get('restored_frozen_fields', []),
                    'local repair field restoration replay changed')
            raw_claim, frozen_restores = restore_frozen_referenced_symbols(
                copy.deepcopy(prev_plan), raw_claim, mutable_fields)
            restore_log_path = claim_path.parent / 'frozen-symbol-restore.json'
            if restore_log_path.exists():
                require(frozen_restores == json.loads(restore_log_path.read_text()),
                        'frozen symbol restoration replay changed')
            else:
                require(frozen_restores == [],
                        'frozen symbol restoration replay missing')
        for filename, transform, message in (
                ('normalization-log.json', lambda x: normalize_truth_binding(
                    x, scoped_elements,
                    allow_named_symbol=features.get('fidelity_only_rules', False)),
                 'Impact/I normalization replay changed'),
                ('mechanical-salvage.json', lambda x: drop_unused_invalid_symbols(x),
                 'Impact/I mechanical salvage replay changed'),
                ('partial-formalization.json', lambda x: relax_unsupported_relation(x, scoped_elements),
                 'Impact/I partial formalization replay changed')):
            audit_path = claim_path.parent / filename
            if audit_path.exists():
                raw_claim, changes = transform(raw_claim)
                saved_changes = json.loads(audit_path.read_text())
                if filename == 'normalization-log.json':
                    saved_changes = saved_changes['changes']
                require(changes == saved_changes, message)
        redundant.extend(identical_p_predicates(plan))
        normalized_model_plan = copy.deepcopy(raw_claim)
        model_formal = synthesize_id_formalization(
            normalized_model_plan, scoped_elements, claim_id=claim_id,
            include_unselected_limitations=False,
            fidelity_only=features.get('fidelity_only_rules', False),
            direct_witness_effects=features.get('direct_witness_effects', False))
        replayed_formal = synthesize_id_formalization(
            plan, scoped_elements, claim_id=claim_id,
            include_unselected_limitations=False,
            fidelity_only=features.get('fidelity_only_rules', False),
            direct_witness_effects=features.get('direct_witness_effects', False))
        # Fidelity-only synthesis applies deterministic schema hydration to
        # symbol entity/source bookkeeping. Compare the saved post-normalized
        # plan only after replaying that same normalization.
        require(normalized_model_plan == plan and model_formal == replayed_formal,
                'saved Impact/I plan differs from normalized model response')
        require(replayed_formal ==
                json.loads((target / 'formalization-ids.json').read_text()),
            'Impact/I deterministic synthesis changed')
        generated_candidate_path = (claim_path.parent /
                                    'generated-rule-candidate.json')
        require(generated_candidate_path.is_file() and
                json.loads(generated_candidate_path.read_text()) == {
                    'schema_version': 'stage2-generated-rule-candidate/1',
                    'formal_plan': plan,
                    'formalization': replayed_formal,
                }, 'saved generated rule candidate changed')
        if features['numeric_guard']:
            check_numeric_plan(plan, scoped_elements,
                               exclude_protocol_identifiers=features[
                                   'protocol_identifier_exclusion'],
                               relax_assumptions=features.get(
                                   'assumption_numeric_relief', False),
                               symbolic_numeric_relief=features.get(
                                   'symbolic_numeric_relief', False))
        if features['address_guard']:
            check_address_plan(plan, scoped_elements)
        if features.get('duplicate_predicate_gate', False):
            check_distinct_p_predicates(plan)
        if features.get('semantic_faithfulness_audit', False):
            audit_path = target / 'semantic-faithfulness-audit.json'
            if audit_path.is_file():
                artifact = json.loads(audit_path.read_text())
                if artifact.get('schema_version') in (
                        'semantic-faithfulness-audit/3',
                        'semantic-faithfulness-audit/4'):
                    expected_relation_context = faithfulness_relation_context(
                        raw_elements, catalog,
                        excluded_source_ids=set(selected_p) |
                        {intent_id, impact_id})
                    require(artifact.get('relation_context', []) ==
                            expected_relation_context,
                            'saved P/I/V relation context is not report-grounded')
                if artifact.get('schema_version') == 'semantic-faithfulness-audit/4':
                    trace_path = target / 'relationship-trace.json'
                    require(trace_path.is_file() and
                            artifact.get('relationship_trace') ==
                            json.loads(trace_path.read_text()),
                            'saved relationship trace differs from generated trace')
                if (features.get('fidelity_only_rules') and
                        artifact.get('status') == 'unavailable'):
                    require(entry.get('fidelity_status') == 'unavailable' and
                            artifact.get('verdict_consistent') is None,
                            'Impact/I unavailable fidelity status changed')
                else:
                    verdict = {'checks': artifact['checks']}
                    if 'piv_relation' in artifact:
                        verdict['piv_relation'] = artifact['piv_relation']
                    validate_faithfulness_verdict(
                        verdict, plan, include_relations='piv_relation' in artifact)
                    mismatches = faithfulness_mismatches(verdict)
                    if features.get('fidelity_only_rules'):
                        expected_fidelity = (
                            faithfulness_status(verdict)
                            if 'fidelity_status' in artifact else
                            'passed' if not mismatches else 'failed')
                        require(artifact.get('status') == 'completed' and
                                artifact.get('verdict_consistent') ==
                                (expected_fidelity == 'passed') and
                                artifact.get('fidelity_status', expected_fidelity) ==
                                expected_fidelity and
                                entry.get('fidelity_status') == expected_fidelity,
                                'Impact/I fidelity status disagrees with saved audit')
                    else:
                        require(not mismatches,
                                'Impact/I semantic faithfulness mismatch')
                expected_reviews['semantic-faithfulness-audit'][
                    impact_intent_key(impact_id, intent_id)] = artifact
            else:
                require(not features.get('fidelity_only_rules') and
                        not plan.get('precondition_terms'),
                        'Impact/I semantic faithfulness audit missing')
        if features['structured_unresolved']:
            expected_reviews['unresolved-review'][impact_intent_key(
                impact_id, intent_id)] = structured_unresolved_review(
                    plan, scoped_elements)
        if features['relation_alignment']:
            expected_reviews['relation-alignment'][impact_intent_key(
                impact_id, intent_id)] = classified_relation_alignment(
                    plan, scoped_elements,
                    allow_missing=features.get('frozen_piv_sources', False))
        if features.get('requirement_source_review', False):
            expected_reviews['requirement-source-review'][impact_intent_key(
                impact_id, intent_id)] = requirement_source_review(
                    scoped_elements, plan)
        if features.get('intent_scope_review', False):
            expected_reviews['intent-scope-review'][impact_intent_key(
                impact_id, intent_id)] = intent_scope_review(plan, scoped_elements)
        if features.get('placeholder_predicate_review', False):
            expected_reviews['placeholder-predicate-review'][impact_intent_key(
                impact_id, intent_id)] = placeholder_predicate_review(
                    scoped_elements, plan)
        if features.get('mixed_unit_scaling_review', False):
            expected_reviews['mixed-unit-scaling-review'][impact_intent_key(
                impact_id, intent_id)] = mixed_unit_scaling_review(plan, scoped_elements)
        if features.get('symbol_table_review', False):
            expected_reviews['symbol-table-review'][impact_intent_key(
                impact_id, intent_id)] = symbol_table_review(plan)
        successful.append((impact_id, intent_id,
                           synthesize_id_formalization(
                               plan, scoped_elements, claim_id=claim_id,
                               include_unselected_limitations=False,
                               fidelity_only=features.get(
                                   'fidelity_only_rules', False),
                               direct_witness_effects=features.get(
                                   'direct_witness_effects', False))))

    merged = merge_claim_formalizations(
        successful, raw_elements, failures, include_failed_claims=False)
    require(merged == raw_formal,
            'multi-intent P/I/V formalization merge changed')
    for name, by_pair in expected_reviews.items():
        path = directory / (name + '.json')
        if by_pair:
            expected = {'schema_version': 'stage2-impact-review-set/2',
                        'by_impact_intent': by_pair}
            require(path.is_file() and json.loads(path.read_text()) == expected,
                    name + ' multi-intent replay mismatch')
        else:
            require(not path.exists(), name + ' unexpected multi-intent review')
    return redundant


def verify_multi_impact_plans(directory, raw_elements, raw_formal, features,
                              acceptance_policy_version=None,
                              source_scoped_cards=False, catalog=None,
                              provenance=None):
    """Replay isolated impact plans and their deterministic merge."""
    plan_set = json.loads((directory / 'formal-plan.json').read_text())
    require(plan_set.get('schema_version') == 'report-formal-plan-set/1' and
            isinstance(plan_set.get('claims'), list),
            'invalid multi-impact formal plan set')
    impact_ids = [row['id'] for row in raw_elements['statements']
                  if row['kind'] == 'impact']
    applicability = None
    applicability_contract = (provenance or {}).get(
        'impact_semantic_card_contract') == 'impact-applicability-v1'
    if applicability_contract:
        saved_applicability = json.loads(
            (directory / 'impact-applicability.json').read_text())
        applicability = validate_applicability(saved_applicability, raw_elements)
        require(applicability == saved_applicability,
                'saved Impact applicability failed deterministic replay')
        attempts_path = directory / 'impact-applicability-attempts.json'
        intent_candidates = applicability_payload(raw_elements, catalog)[
            'explicit_intent_candidates']
        if intent_candidates:
            require(attempts_path.is_file(),
                    'Impact applicability call/retry record missing')
            applicability_attempts = json.loads(attempts_path.read_text())
            require(1 <= len(applicability_attempts) <= 2 and
                    [row.get('attempt') for row in applicability_attempts] ==
                    list(range(1, len(applicability_attempts) + 1)) and
                    [row.get('artifact_dir') for row in applicability_attempts] ==
                    ['impact-applicability'] +
                    (['impact-applicability-retry-1']
                     if len(applicability_attempts) == 2 else []) and
                    (len(applicability_attempts) == 1 or
                     applicability_attempts[0].get('outcome') == 'retryable_failure'),
                    'Impact applicability retry history changed')
            accepted_attempts = [row for row in applicability_attempts
                                 if row.get('outcome') == 'accepted_for_validation']
            require(len(accepted_attempts) == 1 and
                    accepted_attempts[0] is applicability_attempts[-1],
                    'Impact applicability accepted response record missing')
            response_path = (directory / accepted_attempts[0]['artifact_dir'] /
                             'model-claim.json')
            require(response_path.is_file() and
                    validate_applicability(json.loads(response_path.read_text()),
                                           raw_elements) == applicability,
                    'Impact applicability response does not match saved selection')
            prompt_path = directory / 'impact-applicability/prompt.txt'
            expected_payload = compact_json(applicability_payload(raw_elements, catalog))
            applicability_prompt = (
                IMPACT_APPLICABILITY_PROMPT_V2
                if provenance.get('prompt_features', {}).get(
                    'direct_v_prescreen', False) else
                IMPACT_APPLICABILITY_PROMPT
                if provenance.get('prompt_features', {}).get('frozen_piv_sources', False)
                else IMPACT_APPLICABILITY_PROMPT_V15)
            require(prompt_path.is_file() and prompt_path.read_text() ==
                    applicability_prompt + expected_payload,
                    'Impact applicability request escaped report-supported candidates')
        else:
            require(all(row['status'] == 'explicit_but_insufficient' and
                        not row['precondition_ids'] and not row['intent_ids'] and
                        row['reason'] ==
                        'No report-supported, non-inferred security intent is available.'
                        for row in applicability['impacts']) and
                    not attempts_path.exists() and
                    not (directory / 'impact-applicability').exists(),
                    'empty-intent applicability should be deterministic and call-free')
    entries = plan_set['claims']
    require([row.get('impact_id') for row in entries] == impact_ids,
            'impact plan set order/coverage changed')
    successful, failures, redundant = [], [], []
    expected_reviews = {name: {} for name in (
        'relation-alignment', 'requirement-source-review', 'intent-scope-review',
        'example-pinning-review', 'placeholder-predicate-review',
        'mixed-unit-scaling-review', 'symbol-table-review', 'unresolved-review',
        'semantic-faithfulness-audit')}
    if source_scoped_cards:
        expected_cards = [build_impact_card(raw_elements, impact_id, applicability)
                          for impact_id in impact_ids]
        cards_path = directory / 'semantic-cards.json'
        require(cards_path.is_file() and json.loads(cards_path.read_text()) == {
            'schema_version': 'stage2-impact-semantic-cards/1',
            'cards': expected_cards,
        }, 'semantic Impact cards changed')

    def verify_scoped_request(target, impact_id, scoped_elements, card):
        """Check that the saved first request matches its source-scoped card."""
        if not source_scoped_cards:
            return
        if (applicability is not None and applicability_by_impact(
                applicability)[impact_id]['status'] != 'selected'):
            return
        if (applicability is None and not explicit_intent_ids(raw_elements)):
            return
        selected = (applicability_by_impact(applicability).get(impact_id)
                    if applicability else None)
        if (features.get('frozen_piv_sources', False) and selected and
                len(selected.get('intent_ids', [])) != 1):
            return
        if provenance.get('lean_formal_input'):
            base = lean_formal_input(raw_elements)
        else:
            allowed_evidence = (referenced_evidence_ids(raw_elements)
                                if features.get('referenced_catalog') else None)
            base = {'elements': raw_elements,
                    'evidence_catalog': model_catalog(catalog, allowed_evidence)}
            if features.get('allowed_statement_ids'):
                base['allowed_statement_ids'] = allowed_statement_ids(raw_elements)
            base['numeric_fact_inventory'] = numeric_fact_inventory(raw_elements)
        base['numeric_fact_inventory'] = numeric_fact_inventory(raw_elements)
        payload = compact_json(target_formal_input(base, scoped_elements, card))
        if features.get('frozen_piv_sources', False) and selected:
            suffix = ('\nTARGET IMPACT ID: ' + impact_id +
                      '\nThe applicability stage already identified and froze '
                      'the P/I/V sources for this complete Impact. Copy every '
                      'selected P source into precondition_ids and use the sole '
                      'selected I source as intent_id; do not make a second source '
                      'selection. Preserve this Impact as V. Frozen P IDs: ' +
                      compact_json(selected['precondition_ids']) + '. Frozen I ID: ' +
                      compact_json(selected['intent_ids'][0]) + '. Convert these sources '
                      'directly into the rule representation. Do not reassess '
                      'applicability/completeness or return the Impact as unresolved '
                      'because you would prefer different sources. If the rule '
                      'grammar cannot express a frozen source, report that as a '
                      'blocking representation limitation while keeping all frozen '
                      'source IDs.\n')
        else:
            suffix = ('\nTARGET IMPACT ID: ' + impact_id +
                      '\nUse the supplied semantic_card as the scope and evidence index. '
                      'The card is not a semantic verdict: select only its listed, '
                      'report-supported P/I sources, preserve the selected Impact '
                      'wording and qualifiers, and do not use another Impact. '
                      'Do not use inferred intent sources. If the cited report '
                      'statements do not support a complete P/I/V relation, leave '
                      'the Impact unresolved instead of inventing the missing relation.\n')
        prompt_path = target / 'neural-formalization' / 'prompt.txt'
        require(prompt_path.is_file() and prompt_path.read_text().startswith(
            (directory / 'prompt-formal.txt').read_text() + suffix + payload),
            'saved formal request escaped its Impact semantic card')

    for entry in entries:
        impact_id = entry['impact_id']
        target = directory / 'impact-formalizations' / impact_id
        claim_id = claim_id_for_impact(impact_id)
        require(entry.get('claim_id') == claim_id, 'impact claim ID changed')
        if entry.get('status') in ('unformalized', 'explicit_but_insufficient',
                                   'needs_review'):
            status = json.loads((target / 'status.json').read_text())
            require(status.get('status') == entry.get('status') and
                    status.get('reason') == entry.get('reason'),
                    'pending impact disposition changed')
            if source_scoped_cards:
                require(status.get('failure_family') == entry.get('failure_family'),
                        'pending impact failure family changed')
            if source_scoped_cards:
                expected_card = build_impact_card(raw_elements, impact_id, applicability)
                frozen = expected_card.get('formalizability', {}).get(
                    'applicability', {})
                if (features.get('frozen_piv_sources', False) and
                        applicability_contract and
                        frozen.get('status') == 'selected' and len(
                        frozen.get('intent_ids', [])) != 1):
                    require(entry.get('status') == 'unformalized' and
                            entry.get('failure_family') == 'unsupported_rule_schema' and
                            'multiple applicable I sources' in entry.get('reason', ''),
                            'multi-I Impact was not recorded as a representation failure')
                if entry.get('status') == 'explicit_but_insufficient':
                    require((applicability is None or
                             applicability_by_impact(applicability)[impact_id]['status'] ==
                             'explicit_but_insufficient') and
                            (applicability is not None or
                             not explicit_intent_ids(raw_elements)) and
                            entry.get('failure_family') ==
                            ('no_applicable_explicit_intent' if applicability is not None
                             else 'missing_report_supported_intent') and
                            entry.get('reason') ==
                            (applicability_by_impact(applicability)[impact_id]['reason']
                             if applicability is not None else
                             expected_card['formalizability']['reason']),
                            'explicit Impact insufficiency disposition is unsupported')
                if entry.get('status') == 'needs_review':
                    require(applicability is not None and
                            applicability_by_impact(applicability)[impact_id]['status'] ==
                            'needs_review' and entry.get('failure_family') ==
                            'impact_applicability_uncertain' and
                            entry.get('reason') == applicability_by_impact(
                                applicability)[impact_id]['reason'],
                            'Impact applicability review disposition is unsupported')
                require((target / 'semantic-card.json').is_file() and
                        json.loads((target / 'semantic-card.json').read_text()) ==
                        expected_card and
                        entry.get('semantic_card_path') ==
                        f'impact-formalizations/{impact_id}/semantic-card.json',
                        'pending impact semantic card changed')
                verify_scoped_request(
                    target, impact_id, target_elements(
                        raw_elements, impact_id,
                        expected_card if applicability_contract else None),
                    expected_card)
            failures.append((impact_id, entry['reason']))
            continue
        require(entry.get('status') == 'formalized_candidate',
                'unknown impact formalization status')
        if features.get('frozen_piv_sources', False) and applicability_contract:
            status = json.loads((target / 'status.json').read_text())
            require(status.get('status') == 'formalized_candidate' and
                    status.get('attempts') == entry.get('attempts'),
                    'successful frozen-source disposition changed')
        if source_scoped_cards:
            expected_card = build_impact_card(raw_elements, impact_id, applicability)
            require((target / 'semantic-card.json').is_file() and
                    json.loads((target / 'semantic-card.json').read_text()) ==
                    expected_card and
                    entry.get('semantic_card_path') ==
                    f'impact-formalizations/{impact_id}/semantic-card.json',
                    'formalized impact semantic card changed')
            verify_scoped_request(
                target, impact_id, target_elements(
                    raw_elements, impact_id,
                    expected_card if applicability_contract else None),
                expected_card)
        expected_path = f'impact-formalizations/{impact_id}/formal-plan.json'
        require(entry.get('formal_plan_path') == expected_path,
                'impact formal plan path changed')
        plan = json.loads((target / 'formal-plan.json').read_text())
        require(plan.get('impact_ids') == [impact_id],
                'impact plan targets a different effect')
        if features.get('frozen_piv_sources', False):
            frozen = expected_card['formalizability']['applicability']
            require(set(plan.get('precondition_ids', [])) ==
                    set(frozen.get('precondition_ids', [])) and
                    len(plan.get('precondition_ids', [])) ==
                    len(frozen.get('precondition_ids', [])) and
                    len(frozen.get('intent_ids', [])) == 1 and
                    plan.get('intent_id') == frozen['intent_ids'][0],
                    'formal plan changed frozen P/I source selection')
        audit_elements = (target_elements(
            raw_elements, impact_id,
            expected_card if applicability_contract else None)
                          if source_scoped_cards else raw_elements)
        claim_path = accepted_model_claim_path(target)
        raw_claim = json.loads(claim_path.read_text())
        normalization_log = claim_path.parent / 'normalization-log.json'
        if normalization_log.exists():
            raw_claim, changes = normalize_truth_binding(
                raw_claim, raw_elements,
                allow_named_symbol=features.get('fidelity_only_rules', False))
            require(changes == json.loads(normalization_log.read_text())['changes'],
                    'impact plan normalization changed')
        salvage_log = claim_path.parent / 'mechanical-salvage.json'
        if salvage_log.exists():
            raw_claim, repairs = drop_unused_invalid_symbols(raw_claim)
            require(repairs == json.loads(salvage_log.read_text()),
                    'impact mechanical salvage changed')
        partial_log = claim_path.parent / 'partial-formalization.json'
        if partial_log.exists():
            raw_claim, relaxed = relax_unsupported_relation(raw_claim, raw_elements)
            require(relaxed == json.loads(partial_log.read_text()),
                    'impact partial formalization changed')
        elif features.get('partial_formalization', False):
            require(not relax_unsupported_relation(copy.deepcopy(raw_claim), raw_elements)[1],
                    'impact partial formalization audit missing')
        require(raw_claim == plan, 'impact formal plan changed')
        redundant.extend(identical_p_predicates(plan))
        require(synthesize_id_formalization(
            plan, audit_elements, claim_id=claim_id,
            include_unselected_limitations=False,
            direct_witness_effects=features.get('direct_witness_effects', False)) ==
            json.loads((target / 'formalization-ids.json').read_text()),
            'impact formal synthesis changed')
        if features['numeric_guard']:
            check_numeric_plan(plan, audit_elements,
                               exclude_protocol_identifiers=features['protocol_identifier_exclusion'],
                               relax_assumptions=features.get('assumption_numeric_relief', False),
                               symbolic_numeric_relief=features.get('symbolic_numeric_relief', False))
        if features['address_guard']:
            check_address_plan(plan, audit_elements)
        if features.get('duplicate_predicate_gate', False):
            check_distinct_p_predicates(plan)
        if features.get('semantic_faithfulness_audit', False):
            audit_path = target / 'semantic-faithfulness-audit.json'
            if audit_path.is_file():
                artifact = json.loads(audit_path.read_text())
                include_relations = 'piv_relation' in artifact
                verdict = {'checks': artifact['checks']}
                if include_relations:
                    verdict['piv_relation'] = artifact['piv_relation']
                validate_faithfulness_verdict(
                    verdict, plan, include_relations=include_relations)
                require(not faithfulness_mismatches(verdict),
                        'impact semantic faithfulness audit mismatch')
                expected_reviews['semantic-faithfulness-audit'][impact_id] = artifact
            else:
                require(not plan.get('precondition_terms'),
                        'impact semantic faithfulness audit missing')
        if features['structured_unresolved']:
            expected_reviews['unresolved-review'][impact_id] = structured_unresolved_review(plan, audit_elements)
        if features['relation_alignment']:
            expected_reviews['relation-alignment'][impact_id] = classified_relation_alignment(
                plan, audit_elements,
                allow_missing=features.get('frozen_piv_sources', False))
        if features.get('requirement_source_review', False):
            expected_reviews['requirement-source-review'][impact_id] = requirement_source_review(audit_elements, plan)
        if features.get('intent_scope_review', False):
            expected_reviews['intent-scope-review'][impact_id] = intent_scope_review(plan, audit_elements)
        if features.get('placeholder_predicate_review', False):
            expected_reviews['placeholder-predicate-review'][impact_id] = placeholder_predicate_review(audit_elements, plan)
        if features.get('mixed_unit_scaling_review', False):
            expected_reviews['mixed-unit-scaling-review'][impact_id] = mixed_unit_scaling_review(plan, audit_elements)
        if features.get('symbol_table_review', False):
            expected_reviews['symbol-table-review'][impact_id] = symbol_table_review(plan)
        if features.get('example_pinning_review', False):
            expected_reviews['example-pinning-review'][impact_id] = example_pinning_review(plan, raw_elements)
        successful.append((impact_id, synthesize_id_formalization(
            plan, audit_elements, claim_id=claim_id,
            include_unselected_limitations=False,
            direct_witness_effects=features.get('direct_witness_effects', False))))

    # complete-piv-v1 stores only fully formalized claims in the rule bundle;
    # failed impacts remain in the plan/status records. Older artifacts kept
    # explicit unformalized bookkeeping claims, so preserve that replay shape
    # when their provenance predates the policy.
    include_failed_claims = acceptance_policy_version != 'complete-piv-v1'
    merged = merge_claim_formalizations(
        successful, raw_elements, failures,
        include_failed_claims=include_failed_claims)
    require(merged == raw_formal, 'multi-impact formalization merge changed')
    for name, by_impact in expected_reviews.items():
        path = directory / (name + '.json')
        if by_impact:
            expected = {'schema_version': 'stage2-impact-review-set/1',
                        'by_impact': by_impact}
            require(path.is_file() and json.loads(path.read_text()) == expected,
                    name + ' multi-impact replay mismatch')
        else:
            require(not path.exists(), name + ' unexpected multi-impact review')
    return redundant


def verify_empty_impact_run(directory, text, provenance, features):
    """Replay an extraction deliberately stopped because no V source existed."""
    checks = []
    catalog = json.loads((directory / 'evidence-catalog.json').read_text())
    require(catalog == build_catalog(text), 'catalog mismatch')
    allowed_ids = explicit_impact_evidence_ids(catalog, text)
    inventory = validate_impact_inventory(
        json.loads((directory / 'impact-inventory.json').read_text()),
        allowed_ids, catalog)
    require(not inventory['impacts'], 'empty-impact stop contains impacts')
    checks.append('empty_impact_inventory')

    prompt_element = (directory / 'prompt-element.txt').read_text()
    prompt_formal = (directory / 'prompt-formal.txt').read_text()
    prompt_impact = (directory / 'prompt-impact.txt').read_text()
    require(r.sha(prompt_element.encode()) == provenance.get('element_prompt_sha256'),
            'element prompt snapshot hash mismatch')
    require(r.sha(prompt_formal.encode()) == provenance.get('formal_prompt_sha256'),
            'formal prompt snapshot hash mismatch')
    require(r.sha(prompt_impact.encode()) == provenance.get(
        'impact_inventory_prompt_sha256'),
        'Impact inventory prompt snapshot hash mismatch')
    if allowed_ids:
        impact_sent = directory / 'impact-inventory' / 'prompt.txt'
        require(impact_sent.is_file() and
                impact_sent.read_text().startswith(prompt_impact),
                'Impact inventory prompt snapshot was not the text sent')
        sent_payload = json.loads(
            impact_sent.read_text()[len(prompt_impact):])
        require([row['id'] for row in sent_payload.get('fragments', [])] ==
                allowed_ids,
                'Impact inventory input escaped the marked-section catalog')
    element_attempts = sorted(
        directory.glob('neural-elements-retry-*'),
        key=lambda path: int(path.name.rsplit('-', 1)[-1]))
    element_dir = element_attempts[-1] if element_attempts else directory / 'neural-elements'
    element_sent = element_dir / 'prompt.txt'
    require(element_sent.is_file() and
            element_sent.read_text().startswith(prompt_element),
            'core element prompt snapshot was not the text sent')
    model_core = json.loads((element_dir / 'model-claim.json').read_text())
    require((directory / 'elements-core-ids.json').is_file() and
            json.loads((directory / 'elements-core-ids.json').read_text()) == model_core,
            'core element snapshot differs from model response')
    discarded = [row for row in model_core.get('statements', [])
                 if isinstance(row, dict) and row.get('kind') == 'impact']
    discarded_path = directory / 'discarded-core-impact-statements.json'
    if discarded:
        require(discarded_path.is_file() and json.loads(
            discarded_path.read_text()) == {
                'schema_version': 'stage2-discarded-core-impacts/1',
                'reason': 'Impact statements are sourced only from the restricted inventory pass.',
                'statements': discarded},
            'discarded core impact audit changed')
    else:
        require(not discarded_path.exists(),
                'unexpected discarded core impact audit')
    merged = merge_impact_inventory(model_core, inventory)
    changes = []
    if features.get('id_normalization'):
        merged, id_changes = normalize_element_ids(merged)
        changes.extend(id_changes)
    if features.get('step_normalization'):
        merged, step_changes = normalize_attack_step_roles(merged)
        changes.extend(step_changes)
    normalization_path = directory / 'element-format-normalization.json'
    if normalization_path.is_file():
        require(changes == json.loads(normalization_path.read_text()),
                'element normalization audit changed')
    else:
        require(not changes, 'element normalization audit missing')
    salvage_path = directory / 'mechanical-salvage-elements.json'
    if salvage_path.is_file():
        merged, repairs = normalize_element_ids(merged)
        require(repairs == json.loads(salvage_path.read_text()),
                'element mechanical salvage audit changed')
    raw_elements = json.loads((directory / 'elements-ids.json').read_text())
    require(merged == raw_elements, 'merged elements changed')
    elements = hydrate_elements(raw_elements, catalog, text)
    validate_core_element_candidate(
        raw_elements, catalog, text,
        normalize_steps=features['step_normalization'],
        normalize_ids=features['id_normalization'],
        require_core_counts=features['core_count'],
        max_core_impacts=(MAX_IMPACTS if features.get('impact_inventory_stage')
                          else 4),
        max_core_intents=(4 if features.get('impact_level_claims') else 1),
        impact_source_ids=[])
    require(elements == json.loads((directory / 'elements.json').read_text()),
            'hydrated elements changed')
    require(validate_elements(elements, text) == json.loads(
        (directory / 'evidence-spans.json').read_text()),
        'evidence spans changed')
    readiness_path = directory / 'input-readiness.json'
    readiness = (json.loads(readiness_path.read_text())
                 if readiness_path.is_file() else None)
    if readiness is not None:
        require(validate_readiness(readiness, catalog) == readiness,
                'readiness changed')
    saved_assessment = json.loads(
        (directory / 'stage2-assessment.json').read_text())
    assessment = stage2_assessment(
        readiness=readiness, elements=elements,
        eligible_impact_ids=([] if saved_assessment.get('schema_version') ==
                             'stage2-assessment/2' else None))
    require(assessment == saved_assessment,
        'stage 2 assessment replay mismatch')
    status = json.loads((directory / 'status.json').read_text())
    expected_inventory_status = (
        'empty' if inventory['schema_version'] == 'report-impact-inventory/1'
        else 'no_marked_impact_section' if not allowed_ids
        else 'needs_review' if inventory['ambiguities']
        else 'no_explicit_impact')
    expected_source_status = ('marked_section_present' if allowed_ids
                              else 'marked_section_absent')
    require(status.get('acceptance_status') == 'needs_impact_review' and
            status.get('impact_inventory_status') == expected_inventory_status and
            (inventory['schema_version'] == 'report-impact-inventory/1' or
             status.get('impact_source_status') == expected_source_status) and
            status.get('impact_count') == 0 and
            status.get('formalized_impact_count') == 0 and
            status.get('external_model_invocations') ==
            provenance.get('external_model_invocations'),
            'empty-impact status changed')
    checks.extend(['core_elements_merge', 'id_hydration', 'stage2_assessment',
                   'empty_impact_status'])
    return {'offline_verified': True, 'model_calls': 0,
            'checks_performed': checks, 'checks_skipped': [],
            'acceptance_status': status['acceptance_status'],
            'core_formalization_status': status['core_formalization_status'],
            'consistency_verdict': 'not_evaluated'}


def verify_readiness_stopped_run(directory, text, provenance, features):
    """Replay a readiness decision that stopped before element extraction."""
    catalog = json.loads((directory / 'evidence-catalog.json').read_text())
    require(catalog == build_catalog(text), 'catalog mismatch')
    readiness_path = directory / 'input-readiness.json'
    require(readiness_path.is_file(), 'saved input readiness missing')
    attempts_path = directory / 'readiness-attempts.json'
    require(attempts_path.is_file(), 'readiness attempt history missing')
    attempts = json.loads(attempts_path.read_text())
    require(1 <= len(attempts) <= 2 and
            [row.get('attempt') for row in attempts] ==
            list(range(1, len(attempts) + 1)) and
            [row.get('artifact_dir') for row in attempts] ==
            ['neural-input-screen'] +
            (['neural-input-screen-retry-1'] if len(attempts) == 2 else []) and
            all(row.get('outcome') == 'retryable_failure'
                for row in attempts[:-1]) and
            attempts[-1].get('outcome') == 'accepted_for_validation',
            'readiness retry history changed')
    accepted = directory / attempts[-1]['artifact_dir']
    raw_readiness = json.loads((accepted / 'model-claim.json').read_text())
    normalized, changes = normalize_readiness(raw_readiness)
    require(changes == provenance.get('input_screening_normalizations', []),
            'readiness normalization record changed')
    readiness = validate_readiness(normalized, catalog)
    require(readiness == json.loads(readiness_path.read_text()) and
            readiness['decision'] != 'ready',
            'saved readiness stop decision changed')
    sent_prompt = (accepted / 'prompt.txt').read_text()
    require(sent_prompt.startswith(READINESS_PROMPT) and
            sent_prompt.endswith(readiness_payload(catalog)),
            'readiness request escaped the evidence catalog')

    status = json.loads((directory / 'status.json').read_text())
    dimension_statuses = {
        item['status'] for item in readiness['dimensions'].values()}
    uncertain_only = ('missing' not in dimension_statuses and
                       'uncertain' in dimension_statuses)
    expected_status = ('needs_input_review' if uncertain_only
                       else 'excluded_before_extraction')
    require(status.get('acceptance_status') == expected_status and
            status.get('input_screening_status') ==
            ('uncertain' if uncertain_only else 'missing_information') and
            status.get('missing_dimensions') == readiness['missing_dimensions'] and
            status.get('external_model_invocations') ==
            provenance.get('external_model_invocations'),
            'readiness stop status changed')
    assessment = stage2_assessment(readiness=readiness)
    require(assessment == json.loads(
        (directory / 'stage2-assessment.json').read_text()),
        'readiness stop assessment changed')
    for filename, key in (('prompt-element.txt', 'element_prompt_sha256'),
                          ('prompt-formal.txt', 'formal_prompt_sha256'),
                          ('prompt-impact.txt', 'impact_inventory_prompt_sha256')):
        path = directory / filename
        if path.is_file() and provenance.get(key) is not None:
            require(r.sha(path.read_bytes()) == provenance[key],
                    filename + ' snapshot hash mismatch')
    require(not (directory / 'elements.json').exists() and
            not (directory / 'impact-inventory.json').exists(),
            'readiness-stopped run unexpectedly performed extraction')
    return {'offline_verified': True, 'model_calls': 0,
            'checks_performed': ['evidence_catalog', 'readiness_attempts',
                                 'input_readiness', 'stage2_assessment',
                                 'readiness_stop_status'],
            'checks_skipped': [],
            'acceptance_status': expected_status,
            'core_formalization_status': status.get(
                'core_formalization_status'),
            'consistency_verdict': 'not_evaluated'}


def verify(directory):
    checks_performed = []
    replay_adjustments = []
    provenance = json.loads((directory / 'provenance.json').read_text())
    # Replay feature gates from the run's own record.  Runs without the key
    # (pre-live-prompt outputs) fall back to the frozen version matrix, which
    # is time-invariant; live runs always record their decisions.  Runs with
    # no prompt version at all (older offline provenance) keep the historical
    # all-disabled semantics.
    recorded_features = provenance.get('prompt_features')
    if recorded_features is not None:
        version = provenance.get('prompt_version')
        features = {
            name: recorded_features.get(
                name, feature_enabled(version, name) if version is not None else False)
            for name in FEATURE_NAMES
        }
        # Runs recorded before a live feature existed must replay with that
        # feature off, never with the current live default. Otherwise a later
        # prompt/denominator change would silently rewrite historical replay.
        for name in FEATURE_NAMES:
            if name not in recorded_features:
                features[name] = False
    else:
        version = provenance.get('prompt_version')
        features = ({name: False for name in FEATURE_NAMES} if version is None else
                    {name: feature_enabled(version, name)
                     for name in FEATURE_NAMES})
    r.set_unit_guard(features.get('unit_guard', True))
    raw = (directory / 'original-report').read_bytes()
    require(r.sha(raw) == provenance['report_sha256'], 'report snapshot hash mismatch')
    text = (directory / 'extraction-input.txt').read_text()
    require(r.sha(text.encode()) == provenance['report_input_sha256'], 'prose hash mismatch')
    try:
        report = json.loads(raw)
        body = report['body']
    except json.JSONDecodeError:
        report = None
        body = raw.decode()
    policy = provenance.get('report_input_policy', {})
    if report is not None and policy.get('source_format') == 'report.json':
        version = policy.get('policy_version')
        require(version in (None, 'report-json-input/2', 'report-json-input/3',
                            'report-json-input/4', 'report-json-input/5'),
                'unknown report input policy')
        current_policy = version is not None
        expected_text, expected_policy = r.report_json_input(
            report, deduplicate_title=current_policy,
            input_policy_version=int(version.rsplit('/', 1)[1]) if version else 2)
        require(policy == expected_policy, 'report input policy changed')
    else:
        # Historical outputs predate the report.json title/body allow-list.
        require(policy.get('policy_version') in (None, 'legacy-prose/2', 'legacy-prose/3'),
                'unknown prose input policy')
        expected_text = r.prose_only(
            body, resume_sections=policy.get('policy_version') is not None,
            plain_section_exclusion=policy.get('policy_version') == 'legacy-prose/3')
    require(text == expected_text, 'prose not derived from saved report')
    status_path = directory / 'status.json'
    if (status_path.is_file() and
            json.loads(status_path.read_text()).get('acceptance_status') in
            ('needs_input_review', 'excluded_before_extraction')):
        return verify_readiness_stopped_run(
            directory, text, provenance, features)
    if (features.get('impact_inventory_stage') and status_path.is_file() and
            json.loads(status_path.read_text()).get('acceptance_status') ==
            'needs_impact_review'):
        return verify_empty_impact_run(directory, text, provenance, features)
    elements = json.loads((directory / 'elements.json').read_text())
    require(validate_elements(elements, text) == json.loads((directory / 'evidence-spans.json').read_text()), 'evidence spans changed')
    checks_performed.append('report_and_grounded_elements')
    formal = json.loads((directory / 'formalization.json').read_text())
    # ID-era runs resolve element/formal IDs through the catalog; every
    # pipeline mode of that era writes one, so a missing file is an
    # unverifiable artifact, never a reason to silently skip ID resolution
    # checks.  Pre-catalog runs carry no *-ids.json artifacts at all, so
    # they have no ID resolution to replay -- a catalog cannot be demanded
    # of an era that never wrote one.
    if ((directory / 'elements-ids.json').exists()
            or (directory / 'formalization-ids.json').exists()):
        require((directory / 'evidence-catalog.json').is_file(),
                'evidence catalog missing; ID grounding cannot be replayed')
        catalog = json.loads((directory / 'evidence-catalog.json').read_text())
        require(catalog == build_catalog(text), 'catalog mismatch')
        checks_performed.append('evidence_catalog')
        impact_inventory = None
        if features.get('impact_inventory_stage'):
            impact_ids = explicit_impact_evidence_ids(catalog, text)
            inventory_path = directory / 'impact-inventory.json'
            require(inventory_path.is_file(), 'Impact inventory missing')
            impact_inventory = validate_impact_inventory(
                json.loads(inventory_path.read_text()), impact_ids, catalog)
            impact_prompt = directory / 'prompt-impact.txt'
            require(impact_prompt.is_file() and
                    r.sha(impact_prompt.read_bytes()) ==
                    provenance.get('impact_inventory_prompt_sha256'),
                    'Impact inventory prompt snapshot hash mismatch')
            sent_impact = directory / 'impact-inventory' / 'prompt.txt'
            if impact_ids:
                require(sent_impact.is_file() and
                        sent_impact.read_text().startswith(impact_prompt.read_text()),
                        'Impact inventory prompt snapshot was not the text sent')
                sent_text = sent_impact.read_text()
                sent_payload = json.loads(sent_text[len(impact_prompt.read_text()):])
                require([row['id'] for row in sent_payload.get('fragments', [])] ==
                        impact_ids,
                        'Impact inventory input escaped the marked-section catalog')
            checks_performed.append('impact_inventory_source_boundary')
        raw_elements = None
        if (directory / 'elements-ids.json').exists():
            raw_elements = json.loads((directory / 'elements-ids.json').read_text())
            require(hydrate_elements(raw_elements, catalog, text) == elements,
                    'ID element resolution mismatch')
            if features['core_count']:
                validate_core_element_candidate(
                    raw_elements, catalog, text,
                    normalize_steps=features['step_normalization'],
                    normalize_ids=features['id_normalization'],
                    require_core_counts=True,
                    max_core_impacts=(MAX_IMPACTS
                                      if features.get('impact_inventory_stage') else
                                      4 if features['relation_alignment'] else 2),
                    max_core_intents=(4 if features.get('impact_level_claims') else 1),
                    impact_source_ids=(explicit_impact_evidence_ids(catalog, text)
                                       if features.get('impact_section_scope')
                                       else None))
                checks_performed.append('core_element_candidate_gate')
        if (directory / 'formalization-ids.json').exists():
            require(hydrate_formalization(json.loads(
                (directory / 'formalization-ids.json').read_text()), catalog, text) == formal,
                'ID formal resolution mismatch')
        checks_performed.append('id_hydration')
    else:
        catalog = None

    if provenance.get('candidate_origin') == 'external_model':
        # Newer runs snapshot the exact prompt text next to their artifacts;
        # replay then never re-resolves an editable live prompt.  Runs without
        # snapshots (pre-live-prompt outputs) resolve the frozen module, which
        # is time-invariant.  A live run whose snapshots were deleted fails
        # honestly: deleting them forfeits replay.
        snapshots = (directory / 'prompt-element.txt',
                     directory / 'prompt-formal.txt')
        if all(path.is_file() for path in snapshots):
            require(r.sha(snapshots[0].read_bytes()) ==
                    provenance.get('element_prompt_sha256'),
                    'element prompt snapshot hash mismatch')
            require(r.sha(snapshots[1].read_bytes()) ==
                    provenance.get('formal_prompt_sha256'),
                    'formal prompt snapshot hash mismatch')
            if features.get('impact_inventory_stage'):
                impact_prompt = directory / 'prompt-impact.txt'
                require(impact_prompt.is_file() and
                        r.sha(impact_prompt.read_bytes()) ==
                        provenance.get('impact_inventory_prompt_sha256'),
                        'Impact inventory prompt snapshot hash mismatch')
            sent = directory / 'neural-elements' / 'prompt.txt'
            if sent.is_file():
                # Cross-check that the snapshot was the text actually sent:
                # the first attempt's prompt.txt is prompt + payload, no
                # feedback section.
                require(sent.read_text().startswith(snapshots[0].read_text()),
                        'element prompt snapshot was not the text sent')
            checks_performed.append('prompt_snapshots')
        elif provenance.get('prompt_version') is None:
            # Pre-versioning runs (multi-report pilot era) never recorded
            # which prompt produced them and no frozen module holds their
            # text.  The exact text sent survives inside the run directory;
            # replay requires it (deleting it forfeits replay) but cannot
            # cross-check it against an archive that never contained it.
            require((accepted_model_claim_path(directory).parent / 'prompt.txt').is_file(),
                    'sent formal prompt missing; pre-versioning replay forfeited')
            if (directory / 'neural-elements').is_dir():
                require((directory / 'neural-elements' / 'prompt.txt').is_file(),
                        'sent element prompt missing; pre-versioning replay forfeited')
            checks_performed.append('pre_versioning_sent_prompts')
        else:
            prompts = resolve_prompt_set(
                provenance['prompt_version'],
                provenance.get('requested_evidence_mode', 'ids'),
                provenance.get('requested_formalization_scope', 'core'))
            # Runs of the sha-recording era compare the recorded hash against
            # the frozen module.  Older versioned runs never recorded hashes,
            # but the run directory kept the exact text sent to the model:
            # cross-check that text against the frozen module, which turns
            # the archive's time-invariance from an assumption into a
            # verified fact.
            if provenance.get('element_prompt_sha256') is not None:
                require(provenance['element_prompt_sha256'] == prompts.sha256('element'),
                        'element prompt hash mismatch')
            elif (directory / 'neural-elements').is_dir():
                # The run performed its own element extraction: the sent
                # prompt must survive and match the frozen module.  Deleting
                # it forfeits replay.
                sent_element = directory / 'neural-elements' / 'prompt.txt'
                require(sent_element.is_file(),
                        'sent element prompt missing; replay forfeited')
                require(sent_element.read_text().startswith(prompts.element_prompt),
                        'sent element prompt not rendered by frozen module')
            # else: this run inherited its elements (elements_source) and no
            # element prompt was sent or recorded here, so there is nothing
            # to verify.
            if provenance.get('formal_prompt_sha256') is not None:
                require(provenance['formal_prompt_sha256'] == prompts.sha256('formal'),
                        'formal prompt hash mismatch')
            else:
                sent_formal = accepted_model_claim_path(directory).parent / 'prompt.txt'
                require(sent_formal.is_file(),
                        'formal prompt evidence missing; replay forfeited')
                require(sent_formal.read_text().startswith(prompts.formal_prompt),
                        'sent formal prompt not rendered by frozen module')
            checks_performed.append('resolved_prompt_hashes')

    if provenance.get('input_screening'):
        require(provenance['input_screening'] == 'deepseek-report-readiness-v1',
                'unknown input screening policy')
        require((directory / 'input-readiness.json').is_file(),
                'saved input readiness missing')
        attempts_path = directory / 'readiness-attempts.json'
        if attempts_path.is_file():
            attempts = json.loads(attempts_path.read_text())
            accepted = [row for row in attempts
                        if row.get('outcome') == 'accepted_for_validation']
            require(len(accepted) == 1, 'readiness attempt count mismatch')
            artifact_dir = accepted[0].get('artifact_dir')
        else:
            # Compatibility with pre-retry runs.
            artifact_dir = 'neural-input-screen'
        require(isinstance(artifact_dir, str) and
                artifact_dir.startswith('neural-input-screen'),
                'invalid readiness artifact directory')
        screen = directory / artifact_dir
        raw_readiness = json.loads((screen / 'model-claim.json').read_text())
        normalized_readiness, changes = normalize_readiness(raw_readiness)
        log_path = screen / 'normalization-log.json'
        if changes:
            require(log_path.is_file() and
                    json.loads(log_path.read_text()).get('changes') == changes,
                    'readiness normalization audit changed')
        else:
            require(not log_path.exists(), 'unexpected readiness normalization log')
        require(validate_readiness(normalized_readiness, catalog) == json.loads(
            (directory / 'input-readiness.json').read_text()),
            'input readiness replay mismatch')
        prompt_text = (screen / 'prompt.txt').read_text()
        expected_payload = readiness_payload(catalog)
        # The readiness prompt is also a frozen external-model artifact. Old
        # versioned runs may predate the current wording, while their saved
        # payload must still exactly match the verified evidence catalog.
        require(prompt_text.endswith(expected_payload),
                'readiness payload mismatch')
        if provenance.get('prompt_version') in LIVE_VERSION_NAMES:
            require(prompt_text.startswith(READINESS_PROMPT),
                    'live readiness prompt mismatch')
        checks_performed.append('input_readiness')
    bundle = compile_bundle(elements, formal, text,
                            strict_piv=features['strict_piv'],
                            verdict_v2=(provenance.get('claim_verdict_policy')
                                        == 'signals-v2'),
                            require_complete_piv=(
                                provenance.get('acceptance_policy_version') ==
                                'complete-piv-v1' and not features.get(
                                    'fidelity_only_rules', False)),
                            enforce_units=features.get('unit_guard', True),
                            fidelity_only_rules=features.get(
                                'fidelity_only_rules', False))
    if features.get('multi_i_claims', False):
        applicability_for_coverage = validate_applicability(
            json.loads((directory / 'impact-applicability.json').read_text()),
            elements)
        pair_records = json.loads(
            (directory / 'formal-plan.json').read_text()).get('claims', [])
        if features.get('gate_direct_v_denominator', False):
            coverage_scope = final_formalization_scope(
                applicability_for_coverage, pair_records)
        else:
            coverage_scope = None
        bundle = apply_multi_intent_coverage(
            bundle, applicability_for_coverage, pair_records,
            require_fidelity=features.get('fidelity_only_rules', False),
            formalization_scope=coverage_scope,
            continue_on_review=bool(provenance.get('continue_on_review')))
    bundle['provenance'] = provenance
    saved = json.loads((directory / 'constraints.json').read_text())
    if 'observability_review' in saved:
        require(attach_review(bundle, formal) == json.loads((directory / 'observability-review.json').read_text()),
                'observability review replay mismatch')
    bundle['external_model_invocations'] = saved['external_model_invocations']
    for claim in bundle['claims']:
        generated_smt = claim.pop('smt')
        saved_smt = (directory / (claim['id'] + '.smt2')).read_text()
        # SMT-LIB ignores leading/trailing whitespace around commands. Older
        # solver builds emitted one extra indent on a declaration, so compare
        # command lines after trimming their outer whitespace while retaining
        # every token and command boundary.
        require([line.strip() for line in generated_smt.splitlines()] ==
                [line.strip() for line in saved_smt.splitlines()],
                'SMT replay mismatch')
    # Older frozen bundles predate the explicit report-impact inventory. Keep
    # their exact replay contract; newly generated bundles include and replay it.
    if 'report_impact_coverage' not in saved:
        bundle.pop('report_impact_coverage', None)
    if bundle != saved:
        # A short-lived complete-piv-v1 build labeled an empty rule bundle as
        # candidate_checks_passed. Keep those already-written artifacts
        # replayable without preserving the incorrect verdict in the verifier
        # result: accept only this one-field legacy difference, and report the
        # recomputed status to callers.
        empty_candidate_status_legacy = (
            provenance.get('acceptance_policy_version') == 'complete-piv-v1' and
            not bundle['claims'] and
            bundle['core_formalization_status'] == 'partial' and
            bundle['acceptance_status'] == 'needs_review' and
            saved.get('core_formalization_status') == 'partial' and
            saved.get('acceptance_status') == 'candidate_checks_passed')
        if empty_candidate_status_legacy:
            legacy_bundle = copy.deepcopy(bundle)
            legacy_bundle['acceptance_status'] = saved['acceptance_status']
            require(legacy_bundle == saved, 'bundle replay mismatch')
            replay_adjustments.append({
                'field': 'acceptance_status',
                'recorded': saved['acceptance_status'],
                'recomputed': bundle['acceptance_status'],
                'reason': 'empty_rule_bundle_cannot_pass_candidate_checks',
            })
        else:
            require(False, 'bundle replay mismatch')
    assessment_path = directory / 'stage2-assessment.json'
    if assessment_path.is_file():
        readiness_path = directory / 'input-readiness.json'
        readiness = (json.loads(readiness_path.read_text())
                     if readiness_path.is_file() else None)
        applicability_path = directory / 'impact-applicability.json'
        eligible_impact_ids = None
        applicability_for_assessment = None
        not_applicable_impacts = None
        assessment_scope = None
        impact_formalization_records = None
        if provenance.get('prompt_features', {}).get('frozen_piv_sources', False):
            plan_set_path = directory / 'formal-plan.json'
            if plan_set_path.is_file():
                impact_formalization_records = json.loads(
                    plan_set_path.read_text()).get('claims', [])
        if applicability_path.is_file():
            applicability_for_assessment = validate_applicability(
                json.loads(applicability_path.read_text()), elements)
            if features.get('gate_direct_v_denominator', False):
                assessment_scope = final_formalization_scope(
                    applicability_for_assessment, impact_formalization_records)
                eligible_impact_ids = list(assessment_scope)
                not_applicable_impacts = not_applicable_impacts_for(
                    applicability_for_assessment, impact_formalization_records)
            else:
                eligible_impact_ids = [
                    row['impact_id'] for row in applicability_for_assessment['impacts']
                    if row['status'] == 'selected']
        expected_assessment = stage2_assessment(
            readiness=readiness, bundle=bundle,
            eligible_impact_ids=eligible_impact_ids,
            impact_formalization_records=impact_formalization_records,
            not_applicable_impacts=not_applicable_impacts,
            formalization_scope=assessment_scope,
            gate_direct_denominator=features.get(
                'gate_direct_v_denominator', False))
        saved_assessment = json.loads(assessment_path.read_text())
        if replay_adjustments and expected_assessment.get('rule_formalization', {}).get(
                'candidate_acceptance_status') == 'needs_review':
            # Preserve the saved assessment for exact historical replay while
            # keeping the corrected verdict visible in replay_adjustments.
            expected_assessment['rule_formalization'][
                'candidate_acceptance_status'] = replay_adjustments[0]['recorded']
        require(expected_assessment == saved_assessment,
                'stage 2 assessment replay mismatch')
        checks_performed.append('stage2_assessment')
    redundant_p_predicates = []
    if provenance['candidate_origin'] == 'external_model':
        raw_elements = json.loads((directory / ('elements-ids.json' if (directory / 'elements-ids.json').exists() else 'elements.json')).read_text())
        raw_formal = json.loads((directory / ('formalization-ids.json' if (directory / 'formalization-ids.json').exists() else 'formalization.json')).read_text())
        # An element retry overwrites elements-ids.json with the LAST attempt's
        # claim, so the replay comparison must read that same attempt rather
        # than always the first one.
        element_retry_dirs = sorted(
            directory.glob('neural-elements-retry-*'),
            key=lambda path: int(path.name.rsplit('-', 1)[-1]))
        element_claim = ((element_retry_dirs[-1] if element_retry_dirs
                          else directory / 'neural-elements') / 'model-claim.json')
        if element_claim.is_file():
            neural_elements = json.loads(element_claim.read_text())
            if features.get('impact_inventory_stage'):
                core_snapshot = directory / 'elements-core-ids.json'
                require(core_snapshot.is_file() and
                        json.loads(core_snapshot.read_text()) == neural_elements,
                        'core element snapshot differs from model response')
                discarded = [row for row in neural_elements.get('statements', [])
                             if isinstance(row, dict) and row.get('kind') == 'impact']
                discarded_path = directory / 'discarded-core-impact-statements.json'
                if discarded:
                    require(discarded_path.is_file() and json.loads(
                        discarded_path.read_text()) == {
                            'schema_version': 'stage2-discarded-core-impacts/1',
                            'reason': 'Impact statements are sourced only from the restricted inventory pass.',
                            'statements': discarded},
                        'discarded core impact audit changed')
                else:
                    require(not discarded_path.exists(),
                            'unexpected discarded core impact audit')
                neural_elements = merge_impact_inventory(
                    neural_elements, impact_inventory)
            if (directory / 'element-format-normalization.json').exists():
                changes = []
                if features['id_normalization']:
                    neural_elements, id_changes = normalize_element_ids(neural_elements)
                    changes.extend(id_changes)
                neural_elements, step_changes = normalize_attack_step_roles(neural_elements)
                changes.extend(step_changes)
                require(changes == json.loads(
                    (directory / 'element-format-normalization.json').read_text()),
                    'element normalization audit changed')
            # Mechanical salvage (element side): a --mechanical-salvage run
            # re-applied normalize_element_ids to the model's raw claim and
            # persisted the drops; the log exists only when something was
            # dropped, so pre-feature and no-repair runs skip untouched.
            salvage_elements_log = directory / 'mechanical-salvage-elements.json'
            if salvage_elements_log.exists():
                neural_elements, repairs = normalize_element_ids(neural_elements)
                require(repairs == json.loads(salvage_elements_log.read_text()),
                        'element mechanical salvage audit changed')
            require(neural_elements == raw_elements,
                    'neural elements changed')
        if features['plan_synthesis'] and features.get('impact_level_claims', False):
            verify_fn = (verify_multi_intent_plans
                         if features.get('multi_i_claims', False)
                         else verify_multi_impact_plans)
            redundant_p_predicates = verify_fn(
                directory, raw_elements, raw_formal, features,
                acceptance_policy_version=provenance.get(
                    'acceptance_policy_version'),
                source_scoped_cards=(provenance.get(
                    'impact_semantic_card_contract') in
            ('source-scoped-v1', 'impact-applicability-v1',
             'impact-applicability-multi-i-v1')),
                catalog=catalog, provenance=provenance)
        elif features['plan_synthesis']:
            plan = json.loads((directory / 'formal-plan.json').read_text())
            # Reported, not enforced: see identical_p_predicates().
            redundant_p_predicates = identical_p_predicates(plan)
            claim_path = accepted_model_claim_path(directory)
            claim = json.loads(claim_path.read_text())
            # Boundary NORMALIZE: the live pipeline declares the boolean an
            # undeclared `truth` symbol names, persists the amended plan, and
            # records what moved beside the raw response.  Replay re-applies that
            # declared transform -- and audits the record -- so the equality below
            # stays strict for every OTHER change.  Mirrors the
            # `element-format-normalization.json` handling above.
            normalization_log = claim_path.parent / 'normalization-log.json'
            if normalization_log.exists():
                claim, changes = normalize_truth_binding(
                    claim, raw_elements,
                    allow_named_symbol=features.get('fidelity_only_rules', False))
                require(changes == json.loads(normalization_log.read_text())['changes'],
                        'plan normalization audit changed')
            # Mechanical salvage (formalization side): the live run applied
            # drop_unused_invalid_symbols between the normalize and partial
            # boundaries; the log exists only when a symbol was dropped, so
            # runs without the flag or without repairs skip untouched.
            salvage_log = claim_path.parent / 'mechanical-salvage.json'
            if salvage_log.exists():
                claim, repairs = drop_unused_invalid_symbols(claim)
                require(repairs == json.loads(salvage_log.read_text()),
                        'mechanical salvage audit changed')
            # semantic-live-5: replay the partial-formalization boundary the
            # same way -- the saved log is the audited record of the relax.
            partial_log = claim_path.parent / 'partial-formalization.json'
            if partial_log.exists():
                claim, relaxed = relax_unsupported_relation(claim, raw_elements)
                require(relaxed == json.loads(partial_log.read_text()),
                        'partial formalization audit changed')
            elif features.get('partial_formalization', False):
                require(not relax_unsupported_relation(
                    copy.deepcopy(claim), raw_elements)[1],
                    'partial formalization audit missing')
            require(claim == plan, 'neural formal plan changed')
            require(synthesize_id_formalization(
                plan, raw_elements,
                direct_witness_effects=features.get(
                    'direct_witness_effects', False)) == raw_formal,
                    'deterministic formal synthesis changed')
            if features['relation_alignment']:
                require(classified_relation_alignment(plan, raw_elements) ==
                        json.loads((directory / 'relation-alignment.json').read_text()),
                        'classified relation alignment changed')
            if features.get('requirement_source_review', False):
                require(requirement_source_review(raw_elements, plan) == json.loads(
                    (directory / 'requirement-source-review.json').read_text()),
                    'requirement source review replay mismatch')
            if features.get('intent_scope_review', False):
                require(intent_scope_review(plan, raw_elements) == json.loads(
                    (directory / 'intent-scope-review.json').read_text()),
                    'intent scope review replay mismatch')
            if features.get('placeholder_predicate_review', False):
                require(placeholder_predicate_review(raw_elements, plan) ==
                        json.loads((directory / 'placeholder-predicate-review.json').read_text()),
                        'placeholder predicate review replay mismatch')
            # S18: both reviews are zero-model-call advisories; runs recorded
            # before the feature (their prompt_features predates the key)
            # simply have no artifact to replay.
            if features.get('mixed_unit_scaling_review', False):
                require(mixed_unit_scaling_review(plan, raw_elements) ==
                        json.loads((directory / 'mixed-unit-scaling-review.json').read_text()),
                        'mixed unit scaling review replay mismatch')
            if features.get('symbol_table_review', False):
                require(symbol_table_review(plan) ==
                        json.loads((directory / 'symbol-table-review.json').read_text()),
                        'symbol table review replay mismatch')
            if features.get('example_pinning_review', False):
                require(example_pinning_review(plan, raw_elements) ==
                        json.loads((directory / 'example-pinning-review.json').read_text()),
                        'example pinning review replay mismatch')
            if features['numeric_guard']:
                check_numeric_plan(
                    plan, raw_elements,
                    exclude_protocol_identifiers=features['protocol_identifier_exclusion'],
                    # Runs recorded before the feature existed (their
                    # prompt_features predates the key) replay with the
                    # strict gate they were produced under.
                    relax_assumptions=features.get('assumption_numeric_relief', False),
                    symbolic_numeric_relief=features.get('symbolic_numeric_relief', False))
            if features['address_guard']:
                check_address_plan(plan, raw_elements)
            # semantic-live-5: the duplicate-predicate defect family was
            # previously visible only in this verifier's output; live runs now
            # reject it at generation time.  Old runs replay without the gate
            # (their recorded features predate the key) and stay report-only.
            if features.get('duplicate_predicate_gate', False):
                check_distinct_p_predicates(plan)
            # S17: verify never makes a model call -- the recorded audit
            # verdict is revalidated against the plan's P sources and must
            # carry zero mismatches.  Runs recorded before the feature (their
            # prompt_features predates the key) have no verdict file and no
            # audit was claimed for them.
            if features.get('semantic_faithfulness_audit', False):
                audit_path = directory / 'semantic-faithfulness-audit.json'
                if audit_path.is_file():
                    artifact = json.loads(audit_path.read_text())
                    if artifact.get('schema_version') == 'semantic-faithfulness-audit/4':
                        trace_path = directory / 'relationship-trace.json'
                        require(trace_path.is_file() and
                                artifact.get('relationship_trace') ==
                                json.loads(trace_path.read_text()),
                                'saved relationship trace differs from generated trace')
                    verdict = {'checks': artifact['checks']}
                    include_relations = 'piv_relation' in artifact
                    if include_relations:
                        verdict['piv_relation'] = artifact['piv_relation']
                    validate_faithfulness_verdict(
                        verdict, plan, include_relations=include_relations)
                    require(not faithfulness_mismatches(verdict),
                            'semantic faithfulness audit mismatch on replay')
                else:
                    require(not plan.get('precondition_terms'),
                            'semantic faithfulness audit artifact missing')
            if features['structured_unresolved']:
                require(structured_unresolved_review(plan, raw_elements) ==
                        json.loads((directory / 'unresolved-review.json').read_text()),
                        'structured unresolved review changed')
        else:
            require(json.loads((directory / 'neural-formalization/model-claim.json').read_text()) == raw_formal,
                    'neural formulas changed')
    if (directory / 'solver-results.json').exists():
        solver_results = json.loads((directory / 'solver-results.json').read_text())['claims']
        require(set(solver_results) == {claim['id'] for claim in formal['claims']}, 'solver claim set mismatch')
        for claim in formal['claims']:
            claim_symbols = (symbols_for_claim(claim, formal['symbols'])
                             if impact_claim_set(formal) else formal['symbols'])
            base = {'symbols': {name: {k: v for k, v in item.items() if k != 'entity_ids'} for name, item in claim_symbols.items()},
                    'properties': {name: {k: v for k, v in item.items() if k != 'source_ids'} for name, item in claim['properties'].items()},
                    'assumptions': claim['assumptions'], 'unresolved': claim['unresolved']}
            replay = solve_queries(base, text)
            require(set(replay) == set(solver_results[claim['id']]), 'solver query set mismatch')
            for name, result in solver_results[claim['id']].items():
                query_path = directory / result['path']
                require(query_path.resolve().is_relative_to(directory.resolve()), 'query path outside result directory')
                require(r.sha(query_path.read_bytes()) == result['sha256'], 'query hash mismatch')
                saved_query = query_path.read_text()
                replay_query = replay[name]['smt']
                require([line.strip() for line in saved_query.splitlines()] ==
                        [line.strip() for line in replay_query.splitlines()] and
                        result['status'] == replay[name]['status'],
                        'query replay mismatch')
                if result['status'] == 'sat': verify_witness(base, name, result['witness'])
                else: require(result['witness'] is None, 'non-SAT query has witness')
    interface = json.loads((directory / 'stage3-spec.json').read_text())
    if provenance.get('impact_semantic_card_contract') in (
            'source-scoped-v1', 'impact-applicability-v1',
            'impact-applicability-multi-i-v1'):
        require(interface.get('semantic_cards_path') == 'semantic-cards.json' and
                interface.get('semantic_cards_sha256') == r.sha(
                    (directory / 'semantic-cards.json').read_bytes()),
                'interface semantic cards hash mismatch')
    if 'report_impact_coverage' in interface:
        saved_coverage = saved.get('report_impact_coverage', [])
        stage3_coverage = interface['report_impact_coverage']
        complete_coverage = [row for row in saved_coverage
                             if row.get('status') == 'formalized']
        # Legacy interfaces included every extracted impact in this audit
        # field. New interfaces expose only impacts that have a complete rule.
        require(stage3_coverage in (saved_coverage, complete_coverage),
                'stage3 impact coverage differs from bundle')
        if features.get('multi_i_claims', False):
            expected_claim_ids = {
                claim_id for row in complete_coverage
                for claim_id in row.get('claim_ids', [])}
            require({row['claim_id'] for row in interface.get('claims', [])} ==
                    expected_claim_ids,
                    'stage3 claims do not match complete Impact/I coverage')
    if 'observability_review_sha256' in interface:
        require(interface['observability_review_sha256'] == r.sha((directory / 'observability-review.json').read_bytes()),
                'interface observability review hash mismatch')
    if 'catalog_sha256' in interface:
        require(interface['catalog_sha256'] == r.sha((directory / 'evidence-catalog.json').read_bytes()), 'interface catalog hash mismatch')
    if 'solver_results_sha256' in interface:
        require(interface['solver_results_sha256'] == r.sha((directory / 'solver-results.json').read_bytes()), 'interface solver results hash mismatch')
    require(interface['spec_sha256'] == r.sha((directory / 'constraints.json').read_bytes()), 'interface spec hash mismatch')
    require(interface['elements_sha256'] == r.sha((directory / 'elements.json').read_bytes()), 'interface elements hash mismatch')
    # semantic-live-5: advisory reviews are hash-chained into the interface;
    # S17 adds the faithfulness verdict and S18/S19 the three advisories the
    # same way (tamper-evident).
    for key in ('semantic_cards', 'requirement_source_review', 'intent_scope_review',
                'placeholder_predicate_review', 'semantic_faithfulness_audit',
                'mixed_unit_scaling_review', 'symbol_table_review',
                'example_pinning_review'):
        if key + '_path' in interface:
            require(interface[key + '_sha256'] == r.sha(
                (directory / interface[key + '_path']).read_bytes()),
                'interface ' + key + ' hash mismatch')
    for row in interface['claims']:
        require(row['predicates_sha256'] == r.sha((directory / row['predicates_path']).read_bytes()), 'interface SMT hash mismatch')
    require(interface['execution_ready'] is False, 'unexpected execution-ready claim')
    checks_performed.extend(['bundle_and_smt_replay', 'stage3_interface_hashes'])
    return {'offline_verified': True, 'model_calls': 0,
            'checks_performed': checks_performed, 'checks_skipped': [],
            'candidate_origin': provenance['candidate_origin'],
            'core_formalization_status': bundle['core_formalization_status'],
            'acceptance_status': bundle['acceptance_status'],
            'replay_adjustments': replay_adjustments,
            'redundant_p_predicates': redundant_p_predicates,
            'consistency_verdict': 'not_evaluated'}


def verify_main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    print(json.dumps(verify(parser.parse_args().directory), indent=2))


if __name__ == '__main__':
    if sys.argv[1:2] == ['verify']:
        del sys.argv[1]           # strip the prefix injected by STAGE2_ARG_PREFIX
        raise SystemExit(verify_main())
    raise SystemExit(main())
