#!/usr/bin/env python3
"""Blind-set stage-3 outcome summary + failure-class root-cause analysis.

Reads the two blind eval snapshots (before/after the ``no_anchor`` ceiling fix)
and the data audit, then writes ``blind_stage3_summary.{json,md}``. The point is
a data-driven answer to "why is cross-project e2e recall still low": the blind
set is not yet e2e-runnable because no case has a ``test_*`` harness, and the
two pipeline bugs that previously masqueraded as ``not_dynamically_expressible``
have been fixed so the remaining blockers are honest downstream verdicts.
"""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
BEFORE = HERE / 'blind_stage3_eval_before_fix.json'
AFTER = HERE / 'blind_stage3_eval_after_fix.json'
AUDIT = HERE / 'blind_data_audit.json'
POC_STATUS = HERE / 'blind_poc_harness_status.json'
OUT_JSON = HERE / 'blind_stage3_summary.json'
OUT_MD = HERE / 'blind_stage3_summary.md'

FAILURE_CLASSES = {
    'not_dynamically_expressible': 'deterministic no_anchor ceiling discarded a '
                                    'claim before LLM binding (fixed)',
    'binding_error': 'binding is structurally invalid (e.g. library target '
                     'misclassified as contract)',
    'partial_binding': 'binding LLM left I/V symbols UNBOUND',
    'compile_blocked': 'forge test could not run (no test entrypoint, or slice '
                       'compile failure)',
    'binding_failed': 'binding LLM produced no complete proposal',
    'compile_error': 'patched project failed to compile after injection',
    'violation_reproduced': 'original=Success, patched=Failure (the only TP)',
}


def _rows(path: Path) -> list[dict]:
    data = json.loads(path.read_text())
    return data.get('cases', [])


def _verdict_counts(rows: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        for verdict in row.get('verdicts') or []:
            counts[verdict] = counts.get(verdict, 0) + 1
    return counts


def main() -> int:
    before = _rows(BEFORE)
    after = _rows(AFTER)
    audit = json.loads(AUDIT.read_text())
    poc_status = json.loads(POC_STATUS.read_text()) if POC_STATUS.is_file() else {}

    report = {
        'schema_version': 'blind-stage3-summary/1',
        'generated': '2026-11-13',
        'cases_total': len(after),
        'claims_total': sum(r.get('claims', 0) for r in after),
        'reproduced': sum(r.get('reproduced', 0) for r in after),
        'e2e_recall': (sum(r.get('reproduced', 0) for r in after)
                       / max(1, sum(r.get('claims', 0) for r in after))),
        'before_fix_verdicts': _verdict_counts(before),
        'after_fix_verdicts': _verdict_counts(after),
        'audit': {
            'stage_ready': audit.get('stage_ready'),
            'submission_present': audit.get('submission_present'),
            'poc_present': audit.get('poc_present'),
            'contract_compiling': audit.get('contract_compiling'),
        },
        'poc_by_action': poc_status.get('by_action', {}),
        'cases': after,
        'failure_classes': FAILURE_CLASSES,
    }
    OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')

    vc = report['after_fix_verdicts']
    lines = [
        '# 盲测阶段三结果与根因',
        '',
        f"盲测 stage2 通过的 4 案例共 **{report['claims_total']}** claim，"
        f"动态复现 **{report['reproduced']}**，端到端召回 "
        f"**{report['e2e_recall']:.0%}**。",
        '',
        '| 案例 | claims | 复现 | 主要 verdict |',
        '| --- | ---: | ---: | --- |',
    ]
    for row in after:
        verdicts = ', '.join(sorted(set(row.get('verdicts') or [])))
        lines.append(
            f"| {row['case']} | {row.get('claims')} | "
            f"{row.get('reproduced')} | {verdicts} |")
    lines += [
        '',
        '## 修复前后 verdict 分布',
        '',
        '| verdict | 修复前 | 修复后 |',
        '| --- | ---: | ---: |',
    ]
    for verdict in sorted(set(report['before_fix_verdicts']) | set(vc)):
        lines.append(
            f"| {verdict} | {report['before_fix_verdicts'].get(verdict, 0)} | "
            f"{vc.get(verdict, 0)} |")
    lines += [
        '',
        '## 根因（按影响排序）',
        '',
        f"- **无 test 入口（硬阻塞）**：盲测 audit `stage_ready={report['audit']['stage_ready']}`，"
        f"PoC 动作分布 {report['poc_by_action']}（`no_poc_code` 33 / `snippet_only` 4 / "
        f"`fork_rpc` 3 / `self_contained` 0）。"
        f"所有案例 `Resurrected.t.sol` 都没有 `test_*` 函数；`forge test` 报 "
        "`No tests found`，差分无法运行。合约级 flatten 只含 `src` 不含 PoC 测试。"
        "实测 Sequence__144：submission 的 PoC 代码块可 `forge flatten` 成含 "
        "`testCrossWalletReplayAttack` 的 harness，但该 PoC 依赖 `vm.envUint`/`vm.rpc` "
        "fork 本地 RPC，不是自包含测试；sol_resurrect 产出为空壳 stub。",
        f"- **`no_anchor` 过度路由（已修）**：确定性模糊匹配把 "
        "「zero shares」映射不到 `_mint`/`balanceOf`，硬路由成 "
        "`not_dynamically_expressible`（修复前 5/10）。现在只有 `low` 可观测性才硬路由，"
        "其余交给 binding LLM。",
        f"- **library/contract 定位（已修）**：patch 注入只匹配 `contract`，"
        "`library SessionSig` 触发 `binding_error`；已扩展到 `abstract contract`/`library`。",
        f"- **UNBOUND 符号**：`partial_binding` {vc.get('partial_binding', 0)} 例，"
        "binding LLM 未完成 I/V 绑定，走 fn_work_queue 的 rebind。",
        f"- **stage2 实体类型误判**：`contract` vs `library` 的语义提取错位。",
        '',
        '## 结论',
        '',
        '盲测跨项目 e2e 目前无法测出真实召回，因为测试 harness 未就绪；'
        '在 harness 补齐前不应据此调 dev 指标。两个 pipeline 级根因已修复，'
        '剩余为数据就绪与绑定质量。',
    ]
    OUT_MD.write_text('\n'.join(lines) + '\n')
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
