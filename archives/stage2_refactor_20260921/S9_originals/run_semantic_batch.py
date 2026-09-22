"""Bounded real-report batch: five cases max with explicit provider/retry controls."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from pathlib import Path
import subprocess
import sys
import time

from prompts.registry import DEFAULT_VERSION, PROMPT_MODULES

HERE = Path(__file__).resolve().parent


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
        command = [sys.executable, str(HERE / 'semantic_pipeline.py'),
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
        proc = subprocess.run(command, capture_output=True, text=True)
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


if __name__ == '__main__':
    main()
