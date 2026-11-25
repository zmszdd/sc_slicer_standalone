#!/usr/bin/env python3
"""Blind-set data readiness audit.

Separates the two real blockers that ``blind_readiness`` previously collapsed
into "missing PoC skeleton":

  1. finding body present locally (code4rena submission dump + PoC code block)
  2. contract skeleton built and compiling (sol_resurrect output)

A case is stage-ready only when both hold; otherwise it gets an explicit
blocker string so the blind run is driven by data, not by hand.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'scripts' / 'code4rena'))
from findings_lookup import matching_finding

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
BLIND = HERE / 'blind_set.json'
REPORTS = ROOT / 'code4rena_reports'
BUILD_STATUS = HERE / 'blind_build_status.json'
OUT_JSON = HERE / 'blind_data_audit.json'
OUT_MD = HERE / 'blind_data_audit.md'
POC_STATUS = HERE / 'blind_poc_harness_status.json'
FLATTEN_ROOT = HERE / 'blind_flatten_root'

_CODE_BLOCK_RE = re.compile(r'```(?:solidity|sol)?\s*\n(.*?)```', re.S | re.I)


def _submission_for(case: dict) -> dict | None:
    return matching_finding(case)


def _report_draft(sub: dict) -> dict:
    body = sub.get('body') or ''
    title = sub.get('title') or ''
    match = re.search(r'##\s*(Impact|Finding description and impact)\b',
                      body, re.IGNORECASE)
    if match:
        description = body[:match.start()].strip()
        impact = body[match.end():].strip() or title
    else:
        description = body.strip()
    return {
        'title': title,
        'description': description[:4000],
        'impact': impact[:2000],
    }


def _poc_blocks(body: str) -> list[str]:
    return [m.group(1).strip() for m in _CODE_BLOCK_RE.finditer(body)]


def _harness_has_test(case_dir: Path) -> bool:
    """A resurrected harness is stage-3 runnable only when it declares a
    ``test_*`` entrypoint; a stub that merely compiles cannot drive
    ``forge test`` and is still a blocker for e2e differential."""
    for test in (case_dir / 'test' / 'Resurrected.t.sol',
                 case_dir / 'Resurrected.t.sol'):
        if not test.is_file():
            continue
        text = test.read_text(errors='replace')
        if re.search(r'\bfunction\s+test[A-Za-z0-9_]*\s*\(', text):
            return True
    return False


def _artifact_has_test(path: Path) -> bool:
    if not path.is_file():
        return False
    return bool(re.search(r'\bfunction\s+test[A-Za-z0-9_]*\s*\(',
                          path.read_text(errors='replace')))


def main() -> int:
    blind = json.loads(BLIND.read_text())
    build_rows = {
        r['case']: r for r in json.loads(BUILD_STATUS.read_text()).get('rows', [])
    }
    poc_rows = {
        r['case']: r for r in json.loads(POC_STATUS.read_text()).get('rows', [])
    } if POC_STATUS.is_file() else {}
    rows = []
    for case in blind['cases']:
        sub = _submission_for(case)
        body = ((sub.get('proof_of_concept') or '') + '\n'
                + (sub.get('proofOfConcept') or '') + '\n'
                + (sub.get('body') or '')) if sub else ''
        poc = _poc_blocks(body)
        build = build_rows.get(case['case'], {})
        poc_cls = poc_rows.get(case['case'], {})
        pilot_dir = ROOT / 'runs' / 'sol_resurrect' / 'blind_pilot' / case['case']
        canonical = FLATTEN_ROOT / case['case'] / 'contract.flattened.t.sol'
        stage1_route = build.get('stage1_route')
        if canonical.is_file():
            stage1_route = 'flatten_root'
        harness_ready = bool(build.get('test_entrypoint')) \
            or _harness_has_test(pilot_dir) \
            or _artifact_has_test(canonical)
        poc_action = poc_cls.get('action', 'no_poc_code')
        skeleton_compile = build.get('contract_compile') or build.get('compile')
        if canonical.is_file() and stage1_route == 'flatten_root':
            skeleton_compile = skeleton_compile or 'unverified'
        blockers = []
        if sub is None:
            blockers.append('missing_submission_dump')
        if not poc:
            blockers.append('no_poc_code_block')
        if poc_action == 'fork_rpc':
            blockers.append('poc_forks_live_rpc')
        if poc_action == 'snippet_only' and not harness_ready:
            blockers.append('poc_is_snippet_not_harness')
        if skeleton_compile != 'ok':
            blockers.append('contract_skeleton_not_compiling')
        if not harness_ready:
            blockers.append('no_test_entrypoint_in_harness')
        stage_ready = not blockers
        rows.append({
            'case': case['case'],
            'project': case['project'],
            'finding_key': case.get('finding_key'),
            'submission_present': sub is not None,
            'submission_path': None,
            'poc_code_blocks': len(poc),
            'poc_action': poc_action,
            'stage1_route': stage1_route,
            'stage1_artifact': str(canonical) if canonical.is_file() else None,
            'contract_built': bool(build.get('built')) or canonical.is_file(),
            'contract_compile': skeleton_compile,
            'harness_has_test': harness_ready,
            'blockers': blockers,
            'stage_ready': stage_ready,
        })

    report = {
        'schema_version': 'blind-data-audit/1',
        'generated': '2026-11-13',
        'total': len(rows),
        'stage_ready': sum(1 for r in rows if r['stage_ready']),
        'submission_present': sum(1 for r in rows if r['submission_present']),
        'poc_present': sum(1 for r in rows if r['poc_code_blocks'] > 0),
        'contract_compiling': sum(
            1 for r in rows if r['contract_compile'] == 'ok'),
        'canonical_stage1': sum(
            1 for r in rows if r['stage1_route'] == 'flatten_root'),
        'rows': rows,
    }
    OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')

    lines = [
        '# 盲测数据就绪审计',
        '',
        f"样本 **{report['total']}**；submission 在本地 **{report['submission_present']}**；"
        f"含 PoC 代码块 **{report['poc_present']}**；"
        f"合约骨架可编译 **{report['contract_compiling']}**；"
        f"正式 flatten 阶段一产物 **{report['canonical_stage1']}**；"
        f"完全就绪 **{report['stage_ready']}**。",
        '',
        '| case | project | submission | PoC 块 | PoC 动作 | 阶段一路径 | 编译 | test | blockers |',
        '| --- | --- | ---: | ---: | --- | --- | --- | --- | --- |',
    ]
    for r in rows:
        lines.append(
            f"| {r['case']} | {r['project']} | "
            f"{'Y' if r['submission_present'] else 'N'} | {r['poc_code_blocks']} | "
            f"{r['poc_action']} | {r.get('stage1_route') or '-'} | "
            f"{r['contract_compile']} | "
            f"{'Y' if r['harness_has_test'] else 'N'} | "
            f"{', '.join(r['blockers']) or '-'} |")
    OUT_MD.write_text('\n'.join(lines) + '\n')

    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
