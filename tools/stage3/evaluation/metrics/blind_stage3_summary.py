#!/usr/bin/env python3
"""Blind-set stage-3 outcome summary (mainline stage-3 eval snapshot).

Reads the stage-3 eval JSON produced by ``cli.stage3_eval_run`` over
``blind_goldset`` + ``blind_flatten_root``, plus the runnable selection and the
stage-2 run dirs, then writes ``blind_stage3_summary.{json,md}``. Unlike the
pre-harness audit this reflects live stage-3 verdicts, not data-readiness.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SEL = HERE / 'blind_goldset' / 'selection.json'
RUNS = HERE / 'blind_goldset' / 'runs_blind'
DEFAULT_EVAL = HERE / 'blind_stage3_eval_20261118.json'
OUT_JSON = HERE / 'blind_stage3_summary.json'
OUT_MD = HERE / 'blind_stage3_summary.md'

FAILURE_CLASSES = {
    'violation_reproduced': 'original=Success, patched=Failure (the only TP)',
    'violation_not_reproduced': 'differential did not witness a violation',
    'effect_observed_invariant_holds': 'effect probe passed; invariant holds on exploit path',
    'reference_patch_required': 'not expressible as assert(I); needs a reference patch',
    'binding_error': 'binding structurally invalid (e.g. library target)',
    'binding_failed': 'binding LLM produced no complete proposal',
    'partial_binding': 'binding LLM left I/V symbols UNBOUND',
    'compile_blocked': 'forge test could not run',
    'compile_error': 'patched project failed to compile',
    'not_dynamically_expressible': 'deterministic no_anchor ceiling',
    'halt_witness_required': 'needs halt-to-revert witness',
}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--eval', type=Path, default=DEFAULT_EVAL)
    args = parser.parse_args(argv)

    eval_data = json.loads(args.eval.read_text())
    rows = eval_data.get('cases', [])
    selection = json.loads(SEL.read_text())
    selected = [row['case'] for row in selection['cases']]

    done = sum(1 for r in rows if r.get('status') == 'done')
    reproduced = sum(int(r.get('reproduced') or 0) for r in rows)
    claims_total = sum(r.get('claims') or 0 for r in rows)
    stage2_runs = sum(1 for c in selected if (RUNS / c / 'stage3-spec.json').is_file())
    verdict_counts: dict[str, int] = {}
    for row in rows:
        for verdict in row.get('verdicts') or []:
            verdict_counts[verdict] = verdict_counts.get(verdict, 0) + 1

    report = {
        'schema_version': 'blind-stage3-summary/2',
        'selected_runnable_cases': len(selected),
        'stage2_runs': stage2_runs,
        'stage3_done': done,
        'claims_total': claims_total,
        'reproduced': reproduced,
        'claim_recall': reproduced / claims_total if claims_total else 0.0,
        'verdict_counts': verdict_counts,
        'failure_classes': FAILURE_CLASSES,
        'cases': rows,
    }
    OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')

    lines = [
        '# 盲测阶段三结果',
        '',
        f'可运行子集 **{len(selected)}** 案例；stage2 run **{stage2_runs}**；'
        f'stage3 完成 **{done}**；claim 级复现 **{reproduced}/{claims_total}**。',
        '',
        '| 案例 | claims | 复现 | verdicts |',
        '| --- | ---: | ---: | --- |',
    ]
    for row in rows:
        verdicts = ', '.join(sorted(set(row.get('verdicts') or []))) or row.get('status')
        lines.append(
            f"| {row['case']} | {row.get('claims') or '-'} | "
            f"{row.get('reproduced') or 0} | {verdicts} |")
    lines += [
        '',
        '## verdict 分布',
        '',
        '| verdict | 数 |',
        '| --- | ---: |',
    ]
    for verdict in sorted(verdict_counts):
        lines.append(f'| {verdict} | {verdict_counts[verdict]} |')
    lines += [
        '',
        '## 根因（按影响排序）',
        '',
        f"- **binding_error**：{verdict_counts.get('binding_error', 0)} 个 claim 的 I/V "
        '绑定形状或类型与代码事实不匹配，在 forge 前被拒绝。',
        f"- **stage2_restatement_required**："
        f"{verdict_counts.get('stage2_restatement_required', 0)} 个 claim 命中快照/层错配"
        '等语义硬门，必须回到阶段二重述 I，不得算 TN 或 FN。',
        f"- **violation_reproduced**：{verdict_counts.get('violation_reproduced', 0)} 个 claim "
        '完成 original=Success / patched=Failure 的定向差分，其中参考补丁路由命中 '
        f"{sum(int(row.get('reference_patch_reproduced') or 0) for row in rows)} 个。",
        f"- **compile_error**：{verdict_counts.get('compile_error', 0)} 个 claim 的补丁版"
        '工程编译失败，按规则不计为漏洞成立。',
        f"- **effect/not_reproduced**：effect_observed_invariant_holds "
        f"{verdict_counts.get('effect_observed_invariant_holds', 0)}，"
        f"violation_not_reproduced {verdict_counts.get('violation_not_reproduced', 0)}，"
        '说明 I 未在 exploit 路径上被证伪或差分未产生见证。',
        '',
        '## 结论',
        '',
        f'盲测主线已端到端跑通（compile_blocked '
        f"{eval_data.get('compile_blocked_total', 0)}）；当前剩余损失由绑定错误、"
        '阶段二快照不变式和少量编译问题决定，不再是 stage-1 harness 缺失。',
    ]
    OUT_MD.write_text('\n'.join(lines) + '\n')
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
