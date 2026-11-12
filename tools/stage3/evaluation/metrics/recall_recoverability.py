#!/usr/bin/env python3
"""自动召回可恢复性分层（2026-11-10）。

对判例有效但自动口径未复现的 FN 案例，按 exploit_test 函数体的 PoC 形态分层，
交叉最新 stage3 verdict / 编译错误 / UNBOUND 符号，给出可执行的恢复优先级。

PoC 形态判定只读 exploit_test 函数体（排除 Vm 接口里的 expectRevert 声明）：
  * state_assert_test   -- 用 assert*/assertEq/... 校验状态：首选自动可修。
  * revert_expected_test -- 用 vm.expectRevert：漏洞 revert 与注入断言 revert
                            无法被差分区分，多数只能走参考补丁上限（M1）。
  * other_test          -- 无明显断言：需逐例判断。
  * no_body             -- 无 stage2 产物 / 无测试骨架：先补 stage2。

只读，不改任何口径数据文件。
"""
from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]  # tools/stage3
CASES = ROOT / 'cases'
RUNS = ROOT / 'runs'
VALID = {'valid', 'fixed', 'wontfix'}

GT = HERE / 'judge_ground_truth.json'
PE = HERE / 'positive_eval_105.json'
JUDGE = HERE / 'judge_anchored_metrics.json'
P2_AUTO = HERE / 'p2_auto_reproductions_20261110.json'
OUT_JSON = HERE / 'recall_recoverability.json'
OUT_MD = HERE / 'recall_recoverability.md'


def latest_summary(case: str):
    dirs = [d for d in RUNS.iterdir() if d.name.startswith(case + '__')]
    dirs.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    for d in dirs:
        sp = d / 'stage3-summary.json'
        if sp.is_file():
            try:
                return json.loads(sp.read_text())
            except json.JSONDecodeError:
                continue
    return None


def exploit_test_body(case: str) -> tuple[str | None, str | None]:
    """Return (test_body, exploit_test_name) or (None, None)."""
    src = CASES / case / 'src'
    if not src.is_dir():
        return None, None
    text = ''
    for sol in src.glob('*.sol'):
        try:
            text += sol.read_text(errors='ignore') + '\n'
        except OSError:
            continue
    bindings = CASES / case / 'bindings'
    probe = None
    if bindings.is_dir():
        for bf in bindings.glob('*.json'):
            try:
                probe = json.loads(bf.read_text()).get('probe')
            except (OSError, json.JSONDecodeError):
                continue
            if probe:
                break
    if not probe:
        return None, None
    name = probe.get('exploit_test')
    if not name:
        return None, None
    m = re.search(rf'function\s+{re.escape(name)}\s*\([^)]*\)\s*[^{{]*\{{', text)
    if not m:
        return None, name
    start = m.end() - 1
    depth = 0
    for j in range(start, len(text)):
        if text[j] == '{':
            depth += 1
        elif text[j] == '}':
            depth -= 1
            if depth == 0:
                return text[start:j], name
    return text[start:], name


def poc_shape(case: str) -> str:
    body, _ = exploit_test_body(case)
    if body is None:
        return 'no_body'
    if 'expectRevert' in body:
        return 'revert_expected_test'
    if re.search(r'assert(?:Eq|True|False|Le|Ge|Lt|Gt)?\s*\(', body):
        return 'state_assert_test'
    return 'other_test'


def unbound_symbols(case: str) -> list[str]:
    bindings = CASES / case / 'bindings'
    out: list[str] = []
    if not bindings.is_dir():
        return out
    for bf in bindings.glob('*.json'):
        try:
            b = json.loads(bf.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        for name, entry in (b.get('bindings') or {}).items():
            if str(entry.get('solidity_expr') or '').strip() == 'UNBOUND':
                out.append(name)
    return out


def main() -> dict:
    gt = {r['case']: r for r in json.loads(GT.read_text()).get('cases', [])}
    pe = {r['case']: r for r in json.loads(PE.read_text()).get('cases', [])}
    judge = json.loads(JUDGE.read_text())
    tp_base = {r['case'] for r in judge.get('tp_rows', [])}
    p2 = {r['case'] for r in json.loads(P2_AUTO.read_text()).get('cases', [])
          if r.get('verdict') == 'violation_reproduced'}

    fn = []
    for case, row in pe.items():
        if gt.get(case, {}).get('validity') not in VALID:
            continue
        if case in tp_base or case in p2:
            continue
        fn.append(case)

    rows = []
    for case in fn:
        s = latest_summary(case)
        verdict = s.get('consistency_verdict') if s else 'no_summary'
        ce = s.get('compile_error') if s else None
        ce_kind = ce.get('kind') if isinstance(ce, dict) else None
        rows.append({
            'case': case,
            'project': case.split('__')[0],
            'poc_shape': poc_shape(case),
            'verdict': verdict,
            'compile_error_kind': ce_kind,
            'unbound_symbols': unbound_symbols(case),
        })

    by_shape = defaultdict(list)
    for r in rows:
        by_shape[r['poc_shape']].append(r)

    report = {
        'schema_version': 'recall-recoverability/1',
        'fn_total': len(rows),
        'by_poc_shape': {
            shape: {
                'count': len(items),
                'cases': sorted(r['case'] for r in items),
            }
            for shape, items in sorted(by_shape.items(), key=lambda kv: -len(kv[1]))
        },
        'rows': rows,
    }
    OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')

    lines = [
        '# 自动召回可恢复性分层',
        '',
        f'判例有效但自动口径未复现：**{len(rows)}** 例',
        '',
        '| PoC 形态 | 数量 | 自动可修性 |',
        '| --- | ---: | --- |',
        '| state_assert_test | %d | 首选：绑定/快照修复 |' % len(by_shape['state_assert_test']),
        '| revert_expected_test | %d | 部分可修，多数走参考补丁上限 |' % len(by_shape['revert_expected_test']),
        '| other_test | %d | 逐例判断 |' % len(by_shape['other_test']),
        '| no_body | %d | 先补 stage2 产物 |' % len(by_shape['no_body']),
        '',
        '## 明细',
        '',
        '| case | PoC 形态 | 最新 verdict | compile_error | UNBOUND |',
        '| --- | --- | --- | --- | ---: |',
    ]
    for r in sorted(rows, key=lambda x: (x['poc_shape'], x['case'])):
        lines.append(
            f"| {r['case']} | {r['poc_shape']} | {r['verdict']} | "
            f"{r['compile_error_kind'] or ''} | {len(r['unbound_symbols'])} |")
    OUT_MD.write_text('\n'.join(lines) + '\n')

    print(f'FN total = {len(rows)}')
    for shape, items in sorted(by_shape.items(), key=lambda kv: -len(kv[1])):
        print(f'  {shape}: {len(items)}')
    print(f'json -> {OUT_JSON}')
    print(f'md   -> {OUT_MD}')
    return report


if __name__ == '__main__':
    main()
