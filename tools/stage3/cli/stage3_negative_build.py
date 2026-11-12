#!/usr/bin/env python3
"""一键构造单个负样本：fix 提取 -> 打补丁 -> 差分验证。

从“一个已复现的正样本 claim”自动构造 code-fix 负样本，并可选地跑
``stage3_pipeline`` 验证终态 verdict。三个子步骤都在独立子进程里，单点失败
不影响其它。

流程：
  1. ``stage3_fix_llm``    从 report.json 提取 {old:new} 修复（verbatim 门禁）
  2. ``stage3_make_negative`` 用该修复打补丁，生成负样本 case
  3. ``stage3_pipeline``    （--validate）跑差分，输出 verdict

用法（cwd = tools/stage3）：
    python -m cli.stage3_negative_build \
        --positive-case cases/<case> \
        --binding cases/<case>/bindings/<claim>.json \
        --report <flatten>/<case>/report.json \
        --out /tmp/<case>_neg --validate
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]  # tools/stage3


def load_fix(path: Path) -> dict:
    return json.loads(path.read_text())


def run_step(cmd: list[str], label: str) -> str:
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=str(ROOT))
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or '').strip()
        raise SystemExit(f'{label} 失败: {detail[:800]}')
    return (proc.stdout or '').strip()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--positive-case', type=Path, required=True)
    parser.add_argument('--binding', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--fix-json', type=Path,
                        help='复用已提取的 fix.json，跳过 stage3_fix_llm')
    parser.add_argument('--validate', action='store_true',
                        help='构造后跑 stage3_pipeline 验证 verdict')
    parser.add_argument('--max-fix-rounds', type=int, default=3,
                        help='修复重试轮数（--fix-json 时恒为 1）')
    args = parser.parse_args(argv)

    positive = Path(args.positive_case).resolve()
    src = positive / 'src' / 'Contract.sol'
    binding = Path(args.binding).resolve()
    out = Path(args.out).resolve()

    if out.exists():
        raise SystemExit(f'输出目录已存在: {out}')

    if args.fix_json:
        max_rounds = 1
        precomputed_fix = load_fix(Path(args.fix_json))
    else:
        max_rounds = args.max_fix_rounds
        precomputed_fix = None

    def propose_fix_round(round_no: int, hint: str | None):
        fix_path = out.parent / f'{out.name}.fix.r{round_no}.json'
        cmd = [sys.executable, '-m', 'cli.stage3_fix_llm',
               '--report', str(Path(args.report).resolve()),
               '--src', str(src), '--out', str(fix_path),
               '--binding', str(binding)]
        if hint:
            cmd += ['--hint', hint]
        run_step(cmd, 'stage3_fix_llm')
        return load_fix(fix_path)

    def validate_case(case_dir: Path) -> tuple[str | None, str | None]:
        proc = subprocess.run([sys.executable, '-m', 'cli.stage3_pipeline',
                               '--case-dir', str(case_dir)],
                              capture_output=True, text=True, cwd=str(ROOT))
        if proc.returncode != 0:
            detail = (proc.stderr or proc.stdout or '').strip()
            raise SystemExit(f'stage3_pipeline 失败: {detail[:800]}')
        try:
            summary = json.loads(proc.stdout)
        except json.JSONDecodeError as exc:
            raise SystemExit(f'stage3_pipeline 输出不是 JSON: {exc}') from exc
        verdict = summary.get('consistency_verdict')
        compile_error = None
        if verdict in ('compile_blocked', 'compile_error'):
            ce = summary.get('compile_error') or {}
            compile_error = (ce.get('original') or ce.get('patched')
                             or ce.get('kind'))
        return verdict, compile_error

    rejected_root = out.parent / '.neg_rejected'
    attempts = []
    hint = None
    final_verdict = None
    discard_reason = None
    for round_no in range(1, max_rounds + 1):
        if precomputed_fix is not None:
            fix = precomputed_fix
        else:
            fix = propose_fix_round(round_no, hint)
        if not fix.get('applicable'):
            reason = (f'修复不可适用: {fix.get("reason")} '
                      f'(missing_old={len(fix.get("missing_old", []))}, '
                      f'missing_poc_old={len(fix.get("missing_poc_old", []))})')
            attempts.append({'round': round_no, 'verdict': None, 'reason': reason})
            hint = reason
            discard_reason = 'applicable_false'
            continue
        run_step([sys.executable, '-m', 'cli.stage3_make_negative',
                  '--positive', str(positive),
                  '--binding', str(binding),
                  '--out', str(out),
                  '--fix', json.dumps(fix['fix'], ensure_ascii=False),
                  '--fix-poc', json.dumps(fix.get('fix_poc', {}), ensure_ascii=False)],
                 'stage3_make_negative')
        if args.validate:
            verdict, compile_error = validate_case(out)
        else:
            verdict, compile_error = None, None
        attempts.append({'round': round_no, 'verdict': verdict,
                         'reason': fix.get('reason')})
        if args.validate and verdict == 'violation_not_reproduced':
            final_verdict = verdict
            (out / 'verdict.json').write_text(
                json.dumps({'case': out.name, 'verdict': verdict,
                            'accepted': True, 'attempts': attempts},
                           ensure_ascii=False, indent=2) + '\n')
            print(f'accepted negative case: {out} verdict={verdict}')
            return 0
        hint = (f'previous fix produced verdict={verdict}; ')
        if compile_error:
            hint += (f'compile error: {str(compile_error)[:600]}. ')
        hint += (f'previous replacement (do NOT reuse): '
                 f'{json.dumps(fix.get("fix", {}), ensure_ascii=False)[:400]}. ')
        hint += ('produce a different, complete fix that compiles and removes '
                 'the vulnerability (do not repeat the same replacement).')
        rejected_root.mkdir(parents=True, exist_ok=True)
        rejected = rejected_root / f'{out.name}.r{round_no}'
        import shutil
        shutil.move(str(out), str(rejected))
        final_verdict = verdict
        if verdict == 'violation_reproduced':
            discard_reason = 'still_reproduced'
        elif compile_error:
            discard_reason = 'compile_blocked'
        else:
            discard_reason = verdict or 'unknown'

    discarded = out.parent / f'{out.name}.discarded.json'
    discarded.write_text(json.dumps({
        'case': out.name,
        'discarded': True,
        'reason': 'no attempt reached the required terminal verdict',
        'required_verdict': 'violation_not_reproduced',
        'last_verdict': final_verdict,
        'discard_reason': discard_reason,
        'attempts': attempts,
    }, ensure_ascii=False, indent=2) + '\n')
    print(f'discarded negative case: {out.name} '
          f'(last_verdict={final_verdict}, attempts={len(attempts)})')
    return 1


if __name__ == '__main__':
    raise SystemExit(main())
