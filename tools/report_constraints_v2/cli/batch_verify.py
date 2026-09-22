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
import json
from pathlib import Path
import subprocess
import sys
import time

from prompts.registry import (
    ADDRESS_GUARD_VERSIONS, DEFAULT_VERSION, ID_NORMALIZATION_VERSIONS,
    NUMERIC_GUARD_VERSIONS, PLAN_VERSIONS, PROMPT_MODULES,
    PROTOCOL_IDENTIFIER_EXCLUSION_VERSIONS, RELATION_ALIGNMENT_VERSIONS,
    STRICT_PIV_VERSIONS, STRUCTURED_UNRESOLVED_VERSIONS,
)

import report_only as r
from fidelity import check_numeric_plan, check_address_plan
from semantic_core import compile_bundle, require, validate_elements
from plan_synthesizer import (classified_relation_alignment, structured_unresolved_review,
                              synthesize_id_formalization)
from evidence_catalog import build_catalog, hydrate_elements, hydrate_formalization
from symbolic_queries import solve_queries, verify_witness
from review import attach_review
from mechanical_salvage import normalize_attack_step_roles, normalize_element_ids


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
    parser.add_argument('--element-retries', type=int, choices=(0, 1), default=0)
    parser.add_argument('--formal-retries', type=int, choices=(0, 1), default=0)
    parser.add_argument('--lean-formal-input', action='store_true')
    parser.add_argument('--continue-on-review', action='store_true')
    parser.add_argument('--prompt-version', choices=tuple(PROMPT_MODULES),
                        default=DEFAULT_VERSION)
    args = parser.parse_args()
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
        args.element_retries + args.formal_retries
    summary = {'schema_version': 'real-semantic-batch/1', 'provider': args.provider,
               'model': args.model, 'prompt_version': args.prompt_version,
               'maximum_model_invocations': per_case_calls * len(ids),
               'retry_count': args.element_retries + args.formal_retries,
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
    provenance = json.loads((directory / 'provenance.json').read_text())
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
    formal = json.loads((directory / 'formalization.json').read_text())
    if (directory / 'evidence-catalog.json').exists():
        catalog = json.loads((directory / 'evidence-catalog.json').read_text())
        require(catalog == build_catalog(text), 'catalog mismatch')
        if (directory / 'elements-ids.json').exists():
            require(hydrate_elements(json.loads((directory / 'elements-ids.json').read_text()), catalog, text) == elements, 'ID element resolution mismatch')
        if (directory / 'formalization-ids.json').exists():
            require(hydrate_formalization(json.loads((directory / 'formalization-ids.json').read_text()), catalog, text) == formal, 'ID formal resolution mismatch')
    bundle = compile_bundle(elements, formal, text,
                            strict_piv=(provenance.get('prompt_version') in
                                        STRICT_PIV_VERSIONS),
                            verdict_v2=(provenance.get('claim_verdict_policy')
                                        == 'signals-v2'))
    bundle['provenance'] = provenance
    saved = json.loads((directory / 'constraints.json').read_text())
    if 'observability_review' in saved:
        require(attach_review(bundle, formal) == json.loads((directory / 'observability-review.json').read_text()),
                'observability review replay mismatch')
    bundle['external_model_invocations'] = saved['external_model_invocations']
    for claim in bundle['claims']:
        require(claim.pop('smt') == (directory / (claim['id'] + '.smt2')).read_text(), 'SMT replay mismatch')
    require(bundle == saved, 'bundle replay mismatch')
    if provenance['candidate_origin'] == 'external_model':
        raw_elements = json.loads((directory / ('elements-ids.json' if (directory / 'elements-ids.json').exists() else 'elements.json')).read_text())
        raw_formal = json.loads((directory / ('formalization-ids.json' if (directory / 'formalization-ids.json').exists() else 'formalization.json')).read_text())
        if (directory / 'neural-elements/model-claim.json').exists():
            neural_elements = json.loads(
                (directory / 'neural-elements/model-claim.json').read_text())
            if (directory / 'element-format-normalization.json').exists():
                changes = []
                if provenance.get('prompt_version') in ID_NORMALIZATION_VERSIONS:
                    neural_elements, id_changes = normalize_element_ids(neural_elements)
                    changes.extend(id_changes)
                neural_elements, step_changes = normalize_attack_step_roles(neural_elements)
                changes.extend(step_changes)
                require(changes == json.loads(
                    (directory / 'element-format-normalization.json').read_text()),
                    'element normalization audit changed')
            require(neural_elements == raw_elements,
                    'neural elements changed')
        if provenance.get('prompt_version') in PLAN_VERSIONS:
            plan = json.loads((directory / 'formal-plan.json').read_text())
            require(json.loads(accepted_model_claim_path(directory).read_text()) == plan,
                    'neural formal plan changed')
            require(synthesize_id_formalization(plan, raw_elements) == raw_formal,
                    'deterministic formal synthesis changed')
            if provenance.get('prompt_version') in RELATION_ALIGNMENT_VERSIONS:
                require(classified_relation_alignment(plan, raw_elements) ==
                        json.loads((directory / 'relation-alignment.json').read_text()),
                        'classified relation alignment changed')
            if provenance.get('prompt_version') in NUMERIC_GUARD_VERSIONS:
                check_numeric_plan(
                    plan, raw_elements,
                    exclude_protocol_identifiers=(
                        provenance.get('prompt_version') in
                        PROTOCOL_IDENTIFIER_EXCLUSION_VERSIONS))
            if provenance.get('prompt_version') in ADDRESS_GUARD_VERSIONS:
                check_address_plan(plan, raw_elements)
            if provenance.get('prompt_version') in STRUCTURED_UNRESOLVED_VERSIONS:
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
    for row in interface['claims']:
        require(row['predicates_sha256'] == r.sha((directory / row['predicates_path']).read_bytes()), 'interface SMT hash mismatch')
    require(interface['execution_ready'] is False, 'unexpected execution-ready claim')
    return {'offline_verified': True, 'model_calls': 0, 'candidate_origin': provenance['candidate_origin'],
            'core_formalization_status': bundle['core_formalization_status'],
            'acceptance_status': bundle['acceptance_status'], 'consistency_verdict': 'not_evaluated'}


def verify_main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    print(json.dumps(verify(parser.parse_args().directory), indent=2))


if __name__ == '__main__':
    if sys.argv[1:2] == ['verify']:
        del sys.argv[1]           # strip the prefix injected by STAGE2_ARG_PREFIX
        raise SystemExit(verify_main())
    raise SystemExit(main())
