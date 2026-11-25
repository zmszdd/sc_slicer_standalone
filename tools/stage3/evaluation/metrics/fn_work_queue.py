#!/usr/bin/env python3
"""Prioritized FN work queue derived from triage + recoverability artifacts.

Turns the two read-only FN analyses into an executable queue: every
judge-valid-but-unreproduced case gets exactly one next action and a
recoverability classification, so the stage-3 loop can be driven mechanically
instead of by eyeballing two markdown tables.

Actions:
  * rebind                 -- state_assert_test with binding/UNBOUND repair room
  * stage2_rerun           -- stage-2 product missing or invariant vacuous on path
  * reference_patch        -- hard ceiling: needs an M1 reference patch
  * effect_predicate       -- revert_expected_test whose effect predicate must be
                              witnessed independently (otherwise goes to ceiling)
  * witness_poc            -- original PoC does not reach Success; fix harness
  * retry_inconclusive     -- LLM verdict abstained; re-run with repair hint
"""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
TRIAGE = HERE / 'repro_failure_triage.json'
RECOVER = HERE / 'recall_recoverability.json'
OUT_JSON = HERE / 'fn_work_queue.json'
OUT_MD = HERE / 'fn_work_queue.md'
TRIGGER_AUDIT = HERE / 'stage2_trigger_audit.json'

# Action priority: lower runs first.
PRIORITY = {
    'rebind': 0,
    'stage2_rerun': 1,
    'witness_poc': 2,
    'retry_inconclusive': 3,
    'effect_predicate': 4,
    'reference_patch': 5,
}

RECOVERABLE = {'rebind', 'stage2_rerun', 'witness_poc', 'retry_inconclusive',
               'effect_predicate'}
CEILING = {'reference_patch'}


def _trigger_flagged() -> set[str]:
    if not TRIGGER_AUDIT.is_file():
        return set()
    try:
        audit = json.loads(TRIGGER_AUDIT.read_text())
    except json.JSONDecodeError:
        return set()
    return {r['case'] for r in audit.get('rows', [])}


def _action(row: dict, triage_bucket: str | None) -> str:
    shape = row.get('poc_shape')
    verdict = row.get('verdict') or ''
    compile_kind = row.get('compile_error_kind') or ''
    unbound = len(row.get('unbound_symbols') or [])
    breakdown = row.get('breakdown') or {}

    if shape == 'no_body':
        return 'stage2_rerun'
    if triage_bucket in ('invariant_holds_on_exploit_path', 'stage2:no_stage2_run'):
        return 'stage2_rerun'
    if triage_bucket in ('reference_patch_required', 'not_dynamically_expressible'):
        return 'reference_patch'
    if triage_bucket == 'poc_not_witnessed':
        return 'witness_poc'
    if triage_bucket == 'inconclusive' or verdict == 'inconclusive':
        return 'retry_inconclusive'
    if shape == 'state_assert_test':
        if verdict == 'effect_observed_invariant_holds':
            return 'stage2_rerun'
        return 'rebind'
    if shape == 'revert_expected_test':
        if verdict in ('effect_observed_invariant_holds', 'violation_not_reproduced'):
            return 'effect_predicate'
        if unbound or compile_kind == 'binding_compile_failure' or 'binding' in verdict:
            return 'rebind'
        return 'effect_predicate'
    if unbound or compile_kind == 'binding_compile_failure':
        return 'rebind'
    return 'reference_patch'


def _rationale(action: str, row: dict, triage_bucket: str | None) -> str:
    verdict = row.get('verdict') or ''
    if action == 'rebind':
        return ('binding repairable: run stage3_verdict_loop to re-propose '
                f"({row.get('unbound_symbols') or 0} UNBOUND, "
                f"compile={row.get('compile_error_kind') or '-'})")
    if action == 'stage2_rerun':
        if row.get('case') in _trigger_flagged() and verdict == 'effect_observed_invariant_holds':
            return ('stage-2 placed a trigger/liveness predicate in I or V; '
                    're-run stage-2 with the corrected role rule')
        return ('stage-2 product missing or invariant holds vacuously on the '
                f'exploit path ({triage_bucket or row.get("verdict")})')
    if action == 'reference_patch':
        return ('multi-contract / unobservable should-be semantics: build an '
                'M1 reference patch rather than auto-assert')
    if action == 'effect_predicate':
        return ('revert_expected_test: effect V must be witnessed independently; '
                'otherwise route to reference-patch ceiling')
    if action == 'witness_poc':
        return ('original PoC is not Success: repair the test harness first')
    if action == 'retry_inconclusive':
        return 'LLM verdict abstained: retry with repair hint'
    return ''


def main() -> dict:
    triage = json.loads(TRIAGE.read_text())
    recover = json.loads(RECOVER.read_text())

    triage_rows = {r['case']: r for r in triage.get('rows', [])}
    recover_rows = {r['case']: r for r in recover.get('rows', [])}
    cases = set(recover_rows) | set(triage_rows)

    queue = []
    for case in cases:
        rr = recover_rows.get(case, {})
        tr = triage_rows.get(case, {})
        bucket = tr.get('bucket')
        action = _action(rr, bucket)
        queue.append({
            'case': case,
            'project': rr.get('project') or case.split('__')[0],
            'priority': PRIORITY[action],
            'action': action,
            'recoverable': action in RECOVERABLE,
            'poc_shape': rr.get('poc_shape') or 'no_body',
            'verdict': rr.get('verdict') or '',
            'compile_error_kind': rr.get('compile_error_kind') or '',
            'unbound_symbols': rr.get('unbound_symbols') or [],
            'triage_bucket': bucket,
            'rationale': _rationale(action, rr, bucket),
        })

    queue.sort(key=lambda r: (r['priority'], r['poc_shape'], r['case']))
    recoverable = [r for r in queue if r['recoverable']]
    ceiling = [r for r in queue if not r['recoverable']]

    report = {
        'schema_version': 'fn-work-queue/1',
        'generated': '2026-11-13',
        'fn_total': len(queue),
        'recoverable_total': len(recoverable),
        'ceiling_total': len(ceiling),
        'by_action': defaultdict(int),
        'queue': queue,
    }
    for r in queue:
        report['by_action'][r['action']] += 1
    report['by_action'] = dict(sorted(
        report['by_action'].items(), key=lambda kv: PRIORITY[kv[0]]))
    OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')

    lines = [
        '# 自动召回 FN 工作队列',
        '',
        f'判例有效但自动口径未复现：**{len(queue)}** 例；'
        f'可恢复 **{len(recoverable)}** / 天花板 **{len(ceiling)}**。',
        '',
        '| 优先级 | 动作 | 数量 |',
        '| --- | --- | ---: |',
    ]
    for action, count in sorted(report['by_action'].items(),
                                key=lambda kv: PRIORITY[kv[0]]):
        lines.append(f'| P{action_map(action)} | {action} | {count} |')
    lines += ['', '## 队列', '',
              '| case | 动作 | PoC 形态 | verdict | UNBOUND | 依据 |',
              '| --- | --- | --- | --- | ---: | --- |']
    for r in queue:
        lines.append(
            f"| {r['case']} | {r['action']} | {r['poc_shape']} | "
            f"{r['verdict'] or '-'} | {len(r['unbound_symbols'])} | "
            f"{r['rationale']} |")
    OUT_MD.write_text('\n'.join(lines) + '\n')

    print(f'FN total = {len(queue)}')
    print(f'recoverable = {len(recoverable)}')
    print(f'ceiling = {len(ceiling)}')
    for action, count in sorted(report['by_action'].items(),
                                key=lambda kv: PRIORITY[kv[0]]):
        print(f'  {action}: {count}')
    print(f'json -> {OUT_JSON}')
    print(f'md   -> {OUT_MD}')
    return report


def action_map(action: str) -> str:
    return str(PRIORITY.get(action, 9))


if __name__ == '__main__':
    main()
