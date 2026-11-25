#!/usr/bin/env python3
"""Deterministic mainline execution backlog (no LLM, no forge).

Splits the 350-case stratified positive sample into actionable buckets whose
counts sum to the sample size.  Every bucket maps to exactly one next action.

Writes ``mainline_backlog.json`` / ``.md``.  Safe to re-run; it only reads.
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from fullset_metrics import RunIndex

SAMPLE = HERE / 'mainline_sample_mini.json'
GT = HERE / 'judge_ground_truth.json'
POSITIVE_EVAL = HERE / 'positive_eval_161.json'
STAGE2_OUT = HERE / 'mainline_stage2_out'
RUNS = HERE.parents[1] / 'runs'
OUT_JSON = HERE / 'mainline_backlog.json'
OUT_MD = HERE / 'mainline_backlog.md'

ACTION = {
    'done': 'none',
    'rebind': 'stage3_verdict_loop',
    'stage2_rerun': 'fix_stage2_weak_invariant',
    'reference_patch': 'provide_reference_patch',
    'other': 'triage_individually',
    'stage3_ready': 'stage3_eval_run',
    'stage2_retry_402': 'run_mainline_stage2',
    'stage2_real_fail': 'fix_stage2',
}


def _claim_map() -> dict[str, list[str]]:
    if not POSITIVE_EVAL.is_file():
        return {}
    pe = json.loads(POSITIVE_EVAL.read_text())
    out = {}
    for row in pe.get('cases', []):
        case = row.get('case')
        ids = row.get('bound_claim_ids') or row.get('claim_ids') or []
        if case and ids:
            out[case] = ids
    return out


def _stage2_status(case: str) -> dict | None:
    path = STAGE2_OUT / case / 'status.json'
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return None


def _stage2_failure_label(status: dict) -> str:
    error = status.get('error') or ''
    if 'HTTP 402' in error:
        return 'stage2_http_402'
    if status.get('core_formalization_status') == 'not_attempted':
        if status.get('impact_inventory_status') == 'no_marked_impact_section':
            return 'report_no_marked_impact_section'
        return 'stage2_not_attempted'
    if 'core P/I/V is not fully formalized' in (status.get('continuation_blockers') or []):
        return 'core_piv_not_fully_formalized'
    if status.get('core_formalization_status') == 'failed':
        return 'stage2_failed'
    return 'needs_review'


def _verdict_bucket(verdict: str | None) -> str:
    if verdict in ('partial_binding', 'compile_error', 'binding_error'):
        return 'rebind'
    if verdict == 'effect_observed_invariant_holds':
        return 'stage2_rerun'
    if verdict in ('reference_patch_required', 'not_dynamically_expressible'):
        return 'reference_patch'
    return 'other'


def main() -> dict:
    sample = json.loads(SAMPLE.read_text())
    gt = {c['case'] for c in json.loads(GT.read_text()).get('cases', [])}
    positives = [c for c in sample.get('positive_cases', []) if c in gt]
    claim_map = _claim_map()
    index = RunIndex(RUNS, set(positives))

    buckets = {key: [] for key in ACTION}
    real_fail_counter: Counter[str] = Counter()

    for case in positives:
        if index.done(case):
            if (index.auto_reproduced(case, claim_map.get(case, []))
                    or index.refpatch_reproduced(case)):
                buckets['done'].append({'case': case, 'verdict': 'violation_reproduced'})
            else:
                summary = index.latest_auto(case) or {}
                verdict = summary.get('consistency_verdict')
                bucket = _verdict_bucket(verdict)
                buckets[bucket].append({'case': case, 'verdict': verdict})
            continue

        status = _stage2_status(case)
        if status is None or status.get('stage2_can_continue') is True:
            buckets['stage3_ready'].append({'case': case})
            continue

        label = _stage2_failure_label(status)
        if label == 'stage2_http_402':
            buckets['stage2_retry_402'].append({'case': case})
        else:
            real_fail_counter[label] += 1
            buckets['stage2_real_fail'].append(
                {'case': case, 'root_cause': label})

    out = {
        'schema_version': 'mainline-backlog/1',
        'sample': 'mainline_sample_mini.json',
        'positive_total': len(positives),
        'actions': ACTION,
        'counts': {key: len(buckets[key]) for key in ACTION},
        'stage2_real_fail_distribution': dict(real_fail_counter),
        'buckets': buckets,
    }
    OUT_JSON.write_text(json.dumps(out, ensure_ascii=False, indent=2) + '\n')

    md = f"""# 主口径执行 backlog（可重放、无 LLM/forge）

- 正样本：`mainline_sample_mini.json`，共 `{len(positives)}` 例。
- 各桶数量之和 = 正样本总数。

| 桶 | 数量 | 下一步动作 |
| --- | ---: | --- |
| done | {len(buckets['done'])} | 无需动作 |
| rebind | {len(buckets['rebind'])} | `stage3_verdict_loop` 重提绑定 |
| stage2_rerun | {len(buckets['stage2_rerun'])} | 修 stage2 弱不变量后重跑 |
| reference_patch | {len(buckets['reference_patch'])} | 提供 M1 参考补丁 |
| other | {len(buckets['other'])} | 逐例人工归因 |
| stage3_ready | {len(buckets['stage3_ready'])} | 跑 stage3（`run_mainline_stage3_consumer.py`） |
| stage2_retry_402 | {len(buckets['stage2_retry_402'])} | 修计费后重跑 stage2 |
| stage2_real_fail | {len(buckets['stage2_real_fail'])} | 修 stage2 形式化 |

## stage2 真失败分布

| 根因 | 数量 |
| --- | ---: |
"""
    for label, count in real_fail_counter.most_common():
        md += f'| {label} | {count} |\n'

    md += '\n## rebind 队列\n\n| case | verdict |\n| --- | --- |\n'
    for row in buckets['rebind']:
        md += f"| {row['case']} | {row['verdict']} |\n"

    md += '\n## stage2_rerun（弱不变量）\n\n| case | verdict |\n| --- | --- |\n'
    for row in buckets['stage2_rerun']:
        md += f"| {row['case']} | {row['verdict']} |\n"

    md += '\n## reference_patch（机制天花板）\n\n| case | verdict |\n| --- | --- |\n'
    for row in buckets['reference_patch']:
        md += f"| {row['case']} | {row['verdict']} |\n"

    OUT_MD.write_text(md)
    print(json.dumps(out['counts'], ensure_ascii=False))
    return out


if __name__ == '__main__':
    main()
