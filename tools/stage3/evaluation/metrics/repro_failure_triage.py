#!/usr/bin/env python3
"""复现失败（FN）逐例归因：把每个判例有效但未复现的案例按根因分层。

根因签名来自 stage3 最新 run 的 stage3-summary.json：
  * invariant_holds_on_exploit_path  -- exploit 原/补丁都 Success，且
        P_and_T=sat、P_and_T_and_not_I=unsat、P_and_T_and_V=unsat。
        含义：阶段二安全不变量 I 在 exploit 路径上恒成立，注入 assert(!P||I)
        后 PoC 仍通过——是阶段二不变量保真度问题，不是阶段三差分机制问题。
  * poc_not_witnessed               -- exploit original != Success，前置条件没被见证。
  * patch_no_effect                 -- 原/补丁都 Success，但 code query 缺失/未知。
  * non_dynamic_{...}               -- 未到动态终态，按 verdict/status 分层。
  * mixed_non_dynamic              -- 多 claim 状态不一致：附 claim_breakdown
    （不再用案例级严格多数把 mixed 压成 ceiling_dominated）。
"""
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]  # tools/stage3
DEFAULT_EVAL = ROOT / 'evaluation' / 'metrics' / 'positive_eval_105.json'
DEFAULT_GT = ROOT / 'evaluation' / 'metrics' / 'judge_ground_truth.json'
RUNS = ROOT / 'runs'
P2_AUTO = ROOT / 'evaluation' / 'metrics' / 'p2_auto_reproductions_20261110.json'
VALID = {'valid', 'fixed', 'wontfix'}
DYNAMIC = ('violation_reproduced', 'violation_not_reproduced')


def latest_summary(case: str) -> dict | None:
    dirs = sorted((RUNS / d for d in RUNS.iterdir() if d.name.startswith(case + '__')),
                  key=lambda p: p.stat().st_mtime, reverse=True) if RUNS.is_dir() else []
    for d in dirs:
        sp = d / 'stage3-summary.json'
        if sp.is_file():
            return json.loads(sp.read_text())
    return None


def classify_verdict(verdict: str | None, summary: dict | None) -> str:
    """Map one claim-level verdict to a specific root-cause bucket.

    The old catch-all ``mixed_non_dynamic`` hid single-claim terminal verdicts
    such as ``preconditions_infeasible_on_code`` and
    ``effect_observed_invariant_holds``. Both are dynamic terminals: the former
    means P was not witnessed on code, the latter means I held vacuously on the
    exploit path.
    """
    verdict = verdict or ''
    if verdict in DYNAMIC:
        if not summary:
            return 'dynamic:no_summary'
        fg = summary.get('forge') or {}
        exp = fg.get('exploit') or {}
        orig = (exp.get('original') or {}).get('status')
        patched = (exp.get('patched') or {}).get('status')
        cq = summary.get('code_query_results') or {}
        if (orig == 'Success' and patched == 'Success'
                and cq.get('P_and_T') == 'sat'
                and cq.get('P_and_T_and_not_I') == 'unsat'
                and cq.get('P_and_T_and_V') == 'unsat'):
            return 'invariant_holds_on_exploit_path'
        if orig != 'Success':
            return 'poc_not_witnessed'
        if orig == 'Success' and patched == 'Success':
            return 'patch_no_effect'
        return 'dynamic:other'
    named = {
        'effect_observed_invariant_holds': 'invariant_holds_on_exploit_path',
        'preconditions_infeasible_on_code': 'poc_not_witnessed',
        'patch_no_effect': 'patch_no_effect',
        'partial_binding': 'partial_binding',
        'inconclusive': 'inconclusive',
        'not_dynamically_expressible': 'not_dynamically_expressible',
        'reference_patch_required': 'reference_patch_required',
        'compile_error': 'compile_error',
        'compile_blocked': 'compile_blocked',
        'binding_failed': 'binding_failed',
        'binding_error': 'binding_error',
        'halt_witness_required': 'halt_witness_required',
    }
    if verdict in named:
        return named[verdict]
    return f'other:{verdict or "empty"}'


def classify_case(row: dict, summary: dict | None) -> tuple[str, dict]:
    """Classify a case from its per-claim verdict list.

    Returns ``(bucket, breakdown)`` where ``breakdown`` is
    ``{bucket: [claim_id, ...]}``. True multi-claim heterogeneity is reported as
    ``mixed_non_dynamic`` with its breakdown instead of being collapsed into an
    opaque bucket.
    """
    status = row.get('status')
    if status != 'done':
        return f'stage2:{status}', {}
    verdicts = row.get('verdicts') or []
    claim_ids = (row.get('claim_ids') or row.get('bound_claim_ids') or [])
    if claim_ids and len(claim_ids) == len(verdicts):
        pairs = list(zip(claim_ids, verdicts))
    else:
        pairs = [(f'claim-{i}', v) for i, v in enumerate(verdicts, 1)]
    claim_buckets = [(cid, classify_verdict(v, summary)) for cid, v in pairs]
    by_bucket: dict[str, list[str]] = defaultdict(list)
    for cid, bucket in claim_buckets:
        by_bucket[bucket].append(cid)
    unique = set(bucket for _, bucket in claim_buckets)
    if len(unique) == 1:
        return next(iter(unique)), dict(by_bucket)
    return 'mixed_non_dynamic', dict(by_bucket)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--positive-eval', type=Path, default=DEFAULT_EVAL)
    parser.add_argument('--judge-ground-truth', type=Path, default=DEFAULT_GT)
    parser.add_argument('--out-json', type=Path,
                        default=ROOT / 'evaluation' / 'metrics' / 'repro_failure_triage.json')
    parser.add_argument('--out-md', type=Path,
                        default=ROOT / 'evaluation' / 'metrics' / 'repro_failure_triage.md')
    args = parser.parse_args(argv)

    eval_data = json.loads(args.positive_eval.read_text())
    gt = json.loads(args.judge_ground_truth.read_text())
    judges = {r['case']: r for r in gt.get('cases', [])}

    p2_auto = {
        r['case'] for r in (json.loads(P2_AUTO.read_text()).get('cases', [])
                            if P2_AUTO.is_file() else [])
        if r.get('verdict') == 'violation_reproduced'
    }
    fn_rows = []
    for row in eval_data.get('cases', []):
        if judges.get(row.get('case'), {}).get('validity') not in VALID:
            continue
        if row.get('case') in p2_auto:
            continue
        if int(row.get('reproduced') or 0) > 0:
            continue
        summary = latest_summary(row['case'])
        bucket, breakdown = classify_case(row, summary)
        fn_rows.append({'case': row['case'], 'bucket': bucket,
                        'project': row['case'].split('__')[0],
                        'claim_breakdown': breakdown})

    buckets = Counter(r['bucket'] for r in fn_rows)
    report = {
        'fn_total': len(fn_rows),
        'buckets': dict(buckets),
        'rows': fn_rows,
    }
    args.out_json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')

    lines = ['# 复现失败（FN）根因分层', '']
    lines.append(f'判例有效但未复现：**{len(fn_rows)}** 例')
    lines.append('')
    lines.append('| 根因 | 数量 |')
    lines.append('| --- | ---: |')
    for k, v in buckets.most_common():
        lines.append(f'| {k} | {v} |')
    lines.append('')
    lines.append('## 明细')
    lines.append('')
    lines.append('| case | 根因 | claim 级拆分 |')
    lines.append('| --- | --- | --- |')
    for r in sorted(fn_rows, key=lambda x: (x['bucket'], x['case'])):
        breakdown = '; '.join(f'{k}:{len(v)}'
                              for k, v in sorted(r.get('claim_breakdown', {}).items()))
        lines.append(f"| {r['case']} | {r['bucket']} | {breakdown} |")
    args.out_md.write_text('\n'.join(lines) + '\n')

    print(f'FN total = {len(fn_rows)}')
    for k, v in buckets.most_common():
        print(f'  {k}: {v}')
    print(f'json -> {args.out_json}')
    print(f'md   -> {args.out_md}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
