#!/usr/bin/env python3
"""Build the canonical mainline readiness report from existing artifacts.

This is a read-only aggregator.  It never calls a model, forge, or the network.
Its job is to make the fail-closed gates visible before any metric refresh:

* stage 1: compile + test entrypoint + self-contained PoC shape;
* stage 2: formalization contract + weak-invariant routing;
* stage 3: binding/execution readiness and current protocol eligibility.
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
STAGE3 = HERE.parents[1]
if str(STAGE3) not in sys.path:
    sys.path.insert(0, str(STAGE3))

from lib.mainline_status import (SCHEMA_VERSION as CASE_SCHEMA,
                                 claim_status, from_canonical_row,
                                 load_json, summarize)
from lib.stage2_contract import decide as stage2_decide, load as stage2_load
from lib.weak_invariant import diagnose as weak_diagnose, gate as weak_gate

ROOT = HERE.parents[3]
BLIND_AUDIT = HERE / 'blind_data_audit.json'
DEV24_RESULTS = HERE / 'dev24_results.json'
CURRENT = HERE / 'current_denominator.json'
CASES = STAGE3 / 'cases'
RUNS = STAGE3 / 'runs'
BLIND_EVAL = HERE / 'blind_stage3_eval_20261118.json'
OUT_JSON = HERE / 'mainline_status.json'
OUT_MD = HERE / 'mainline_status.md'


def _blind_rows() -> list[dict]:
    payload = load_json(BLIND_AUDIT)
    return [from_canonical_row(row, _case_claims(row.get('case')))
            for row in payload.get('rows') or []]


def _binding_ready(binding: dict, required: list[str] | None = None) -> bool:
    entries = binding.get('bindings') or {}
    patch = binding.get('patch') or {}
    if not isinstance(entries, dict) or not entries:
        return False
    if not (patch.get('functions') or patch.get('function')):
        return False
    for entry in entries.values():
        if not isinstance(entry, dict):
            return False
        if not str(entry.get('solidity_expr') or '').strip():
            return False
    if required and any(symbol not in entries for symbol in required):
        return False
    return True


_EVAL_CACHE: dict[tuple[str, str], dict] | None = None


def _eval_index() -> dict[tuple[str, str], dict]:
    global _EVAL_CACHE
    if _EVAL_CACHE is not None:
        return _EVAL_CACHE
    payload = load_json(BLIND_EVAL)
    index: dict[tuple[str, str], dict] = {}
    for row in payload.get('cases') or []:
        if not isinstance(row, dict):
            continue
        case = row.get('case')
        verdicts = row.get('verdicts') or []
        for claim_id, verdict in zip(row.get('claim_ids') or [], verdicts):
            index[(case, claim_id)] = {
                'status': row.get('status'),
                'consistency_verdict': verdict,
            }
    _EVAL_CACHE = index
    return index


def _latest_execution(case: str, claim_id: str,
                      eval_index: dict[tuple[str, str], dict]) -> dict:
    prefix = f'mainline_gate_{case}__{claim_id}__'
    candidates = [path for path in RUNS.glob(f'{prefix}*')
                  if path.is_dir() and (path / 'stage3-summary.json').is_file()]
    if candidates:
        latest = max(candidates, key=lambda path: path.stat().st_mtime)
        summary = load_json(latest / 'stage3-summary.json')
        return {
            'status': 'done' if summary.get('consistency_verdict') else 'failed',
            'consistency_verdict': summary.get('consistency_verdict'),
            'run_id': latest.name,
        }
    return eval_index.get((case, claim_id), {})


def _case_claims(case: str | None) -> list[dict]:
    if not case:
        return []
    case_dir = CASES / case
    stage2_dir = case_dir / 'stage2_run'
    spec_path = stage2_dir / 'stage3-spec.json'
    formal_path = stage2_dir / 'formalization.json'
    if not spec_path.is_file() or not formal_path.is_file():
        return []
    spec = load_json(spec_path)
    formal = load_json(formal_path)
    bindings_dir = case_dir / 'bindings'
    eval_index = _eval_index()
    rows = []
    for claim in spec.get('claims') or []:
        if not isinstance(claim, dict) or not claim.get('claim_id'):
            continue
        claim_id = claim['claim_id']
        gate = stage2_decide(stage2_load(stage2_dir, claim_id))
        if gate.get('status') == 'missing':
            gate = {**gate, 'blocking': True,
                    'category': 'stage2_contract_missing'}
        binding_path = bindings_dir / f'{claim_id}.json'
        fixed_path = bindings_dir / f'{claim_id}.fixed.json'
        if fixed_path.is_file():
            binding_path = fixed_path
        binding = load_json(binding_path)
        required = [
            row.get('symbol') for row in
            ((claim.get('binding_contract') or {}).get('symbols') or [])
            if isinstance(row, dict) and row.get('symbol')]
        weak = weak_gate(weak_diagnose(formal, claim_id, binding))
        rows.append(claim_status(
            claim_id=claim_id,
            stage2_gate=gate,
            weak_gate=weak,
            binding_ready=_binding_ready(binding, required),
            execution=_latest_execution(case, claim_id, eval_index),
        ))
    return rows


def _dev24_summary() -> dict:
    payload = load_json(DEV24_RESULTS)
    results = payload.get('results') or []
    summary = payload.get('summary') or {}
    return {
        'cases': len(results),
        'done': payload.get('done'),
        'failed': payload.get('failed'),
        'positive_tp': summary.get('tp'),
        'positive': summary.get('positive'),
        'negative_fp': summary.get('fp'),
        'negative_unresolved': summary.get('negative_unresolved'),
        'gate': payload.get('gate') or {},
        'note': ('dev24 is a failure-oriented regression set; it does not '
                 'establish the current four metrics'),
    }


def _current_summary() -> dict:
    payload = load_json(CURRENT)
    return {
        'refresh_ready': bool(payload.get('refresh_ready')),
        'dev252': (payload.get('dev252') or {}).get('counts') or {},
        'dev24': (payload.get('dev24') or {}).get('counts') or {},
        'negative5': (payload.get('negative5') or {}).get('counts') or {},
    }


def build_report() -> dict:
    blind = _blind_rows()
    blockers = Counter()
    for row in blind:
        for blocker in row.get('blockers') or []:
            blockers[blocker.split(':', 1)[-1]] += 1
    return {
        'schema_version': 'mainline-status-report/1',
        'case_schema_version': CASE_SCHEMA,
        'blind': {
            'summary': summarize(blind),
            'blockers': dict(blockers.most_common()),
            'rows': blind,
        },
        'dev24': _dev24_summary(),
        'current_denominator': _current_summary(),
    }


def _md(report: dict) -> str:
    blind = report['blind']
    summary = blind['summary']
    lines = [
        '# 主线就绪状态', '',
        '本报告只聚合现有产物，不调用模型、forge 或网络。', '',
        '## Blind 40', '',
        f"- cases: {summary['cases']}",
        f"- data_ready: {summary['data_ready']}",
        f"- claim_ready: {summary['claim_ready']}",
        f"- binding_ready: {summary['binding_ready']}",
        f"- execution_ready: {summary['execution_ready']}",
        f"- eligible_for_metrics: {summary['eligible_for_metrics']}", '',
        f"- claims: {summary['claims']}",
        f"- claims_ready: {summary['claims_ready']}",
        f"- claims_eligible: {summary['claims_eligible']}", '',
        '### 主要 blockers', '',
        '| blocker | cases |', '| --- | ---: |',
    ]
    for blocker, count in blind['blockers'].items():
        lines.append(f'| `{blocker}` | {count} |')
    dev = report['dev24']
    current = report['current_denominator']
    lines += [
        '', '## Dev24 回归', '',
        f"- done: {dev['done']}/{dev['cases']}",
        f"- positive TP: {dev['positive_tp']}/{dev['positive']}",
        f"- negative FP: {dev['negative_fp']}",
        f"- negative unresolved: {dev['negative_unresolved']}", '',
        '## Current denominator', '',
        f"- refresh_ready: {current['refresh_ready']}",
        f"- dev252: {current['dev252']}",
        f"- dev24: {current['dev24']}",
        f"- negative5: {current['negative5']}", '',
        '## 结论', '',
        f"Blind 40 中 {summary['data_ready']} 个案例已有正式 flatten 阶段一产物，"
        f"{summary['claims_eligible']}/{summary['claims']} 个 claim 满足可计入指标条件。",
        '剩余 30 个案例的 stage-1 缺口已收敛为数据天花板：'
        '无 PoC 代码块、PoC 是 diff 片段、依赖 live RPC、或 Hardhat/依赖缺失；'
        '这些案例不得进入阶段二/三，也不得进入模型分母。',
        '`current_denominator.refresh_ready` 仍为 false，因此本轮只刷新盲测与就绪报告，'
        '不刷新 dev252 全量四指标。',
    ]
    return '\n'.join(lines) + '\n'


def main() -> int:
    report = build_report()
    OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    OUT_MD.write_text(_md(report))
    print(json.dumps(report['blind']['summary'], ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
