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

from prompts.registry import (DEFAULT_VERSION, FEATURE_NAMES, SELECTABLE_VERSIONS,
                              feature_enabled)
from prompts.active import resolve_prompt_set

from lib import report_only as r
from lib.salvage import check_numeric_plan, check_address_plan
from lib.salvage import mixed_unit_scaling_review
from lib.semantic_core import (compile_bundle, normalize_readiness,
                           normalize_truth_binding, require,
                           validate_elements)
from lib.plan_synthesizer import (check_distinct_p_predicates, classified_relation_alignment,
                              faithfulness_mismatches, identical_p_predicates,
                              intent_scope_review, placeholder_predicate_review,
                              relax_unsupported_relation, requirement_source_review,
                              structured_unresolved_review, symbol_table_review,
                              synthesize_id_formalization,
                              validate_faithfulness_verdict)
from lib.ingest import (PROMPT as READINESS_PROMPT, build_catalog,
                              hydrate_elements, hydrate_formalization,
                              model_payload as readiness_payload,
                              validate_readiness)
from lib.solving import solve_queries, verify_witness
from lib.solving import attach_review
from lib.salvage import normalize_attack_step_roles, normalize_element_ids
from cli.semantic_pipeline import validate_core_element_candidate


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
    parser.add_argument('--formal-retries', type=int, choices=(0, 1), default=1)
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
    per_case_calls = (3 if args.provider == 'deepseek' else 2) + \
        (args.readiness_retries if args.provider == 'deepseek' else 0) + \
        args.element_retries + args.formal_retries
    summary = {'schema_version': 'real-semantic-batch/1', 'provider': args.provider,
               'model': args.model, 'prompt_version': args.prompt_version,
               'maximum_model_invocations': per_case_calls * len(ids),
               'retry_count': ((args.readiness_retries if args.provider == 'deepseek' else 0) +
                               args.element_retries + args.formal_retries),
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
                             'neural-formalization-retry-2'},
            'invalid formalization artifact directory')
    return directory / artifact_dir / 'model-claim.json'


def verify(directory):
    checks_performed = []
    provenance = json.loads((directory / 'provenance.json').read_text())
    # Replay feature gates from the run's own record.  Runs without the key
    # (pre-live-prompt outputs) fall back to the frozen version matrix, which
    # is time-invariant; live runs always record their decisions.  Runs with
    # no prompt version at all (older offline provenance) keep the historical
    # all-disabled semantics.
    recorded_features = provenance.get('prompt_features')
    if recorded_features is not None:
        features = recorded_features
    else:
        version = provenance.get('prompt_version')
        features = ({name: False for name in FEATURE_NAMES} if version is None else
                    {name: feature_enabled(version, name)
                     for name in FEATURE_NAMES})
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
                            'report-json-input/4'),
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
                    max_core_impacts=(4 if features['relation_alignment'] else 2))
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
        require(prompt_text.startswith(READINESS_PROMPT) and
                prompt_text.endswith(expected_payload),
                'readiness prompt/payload mismatch')
        checks_performed.append('input_readiness')
    bundle = compile_bundle(elements, formal, text,
                            strict_piv=features['strict_piv'],
                            verdict_v2=(provenance.get('claim_verdict_policy')
                                        == 'signals-v2'),
                            require_complete_piv=(
                                provenance.get('acceptance_policy_version') ==
                                'complete-piv-v1'))
    bundle['provenance'] = provenance
    saved = json.loads((directory / 'constraints.json').read_text())
    if 'observability_review' in saved:
        require(attach_review(bundle, formal) == json.loads((directory / 'observability-review.json').read_text()),
                'observability review replay mismatch')
    bundle['external_model_invocations'] = saved['external_model_invocations']
    for claim in bundle['claims']:
        require(claim.pop('smt') == (directory / (claim['id'] + '.smt2')).read_text(), 'SMT replay mismatch')
    require(bundle == saved, 'bundle replay mismatch')
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
            require(neural_elements == raw_elements,
                    'neural elements changed')
        if features['plan_synthesis']:
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
                claim, changes = normalize_truth_binding(claim, raw_elements)
                require(changes == json.loads(normalization_log.read_text())['changes'],
                        'plan normalization audit changed')
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
            require(synthesize_id_formalization(plan, raw_elements) == raw_formal,
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
            if features['numeric_guard']:
                check_numeric_plan(
                    plan, raw_elements,
                    exclude_protocol_identifiers=features['protocol_identifier_exclusion'],
                    # Runs recorded before the feature existed (their
                    # prompt_features predates the key) replay with the
                    # strict gate they were produced under.
                    relax_assumptions=features.get('assumption_numeric_relief', False))
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
                    verdict = {'checks': artifact['checks']}
                    validate_faithfulness_verdict(verdict, plan)
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
            base = {'symbols': {name: {k: v for k, v in item.items() if k != 'entity_ids'} for name, item in formal['symbols'].items()},
                    'properties': {name: {k: v for k, v in item.items() if k != 'source_ids'} for name, item in claim['properties'].items()},
                    'assumptions': claim['assumptions'], 'unresolved': claim['unresolved']}
            replay = solve_queries(base, text)
            require(set(replay) == set(solver_results[claim['id']]), 'solver query set mismatch')
            for name, result in solver_results[claim['id']].items():
                query_path = directory / result['path']
                require(query_path.resolve().is_relative_to(directory.resolve()), 'query path outside result directory')
                require(r.sha(query_path.read_bytes()) == result['sha256'], 'query hash mismatch')
                require(query_path.read_text() == replay[name]['smt'] and result['status'] == replay[name]['status'], 'query replay mismatch')
                if result['status'] == 'sat': verify_witness(base, name, result['witness'])
                else: require(result['witness'] is None, 'non-SAT query has witness')
    interface = json.loads((directory / 'stage3-spec.json').read_text())
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
    # S17 adds the faithfulness verdict the same way (tamper-evident).
    for key in ('requirement_source_review', 'intent_scope_review',
                'placeholder_predicate_review', 'semantic_faithfulness_audit'):
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
