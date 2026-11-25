#!/usr/bin/env python3
"""Detect trigger/liveness predicates that stage-2 placed in I or V.

These symbols name that an action was called, is callable, reverts, or
occurred. They are P-side scenario facts and cannot be dynamically observed as
an invariant/effect, so stage-3 binding reliably lands in partial_binding or
trivially-constant binding errors. The audit feeds fn_work_queue so such cases
are routed to stage2_rerun instead of endless rebind.
"""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
STAGE3 = HERE.parents[1]
CASES = STAGE3 / 'cases'
OUT_JSON = HERE / 'stage2_trigger_audit.json'
OUT_MD = HERE / 'stage2_trigger_audit.md'

# Conservative trigger/liveness tokens. Words like cancelled/removed/executed
# are real state-change observables and are deliberately excluded.
TRIGGER_TOKENS = (
    'callable by anyone', 'callable_by', 'permissionless', 'can be called',
    'is called', 'is invoked', 'invoked', 'reverts', 'revert', 'rejected as',
    'rejects', 'occurrence', 'occurred', 'trigger', 'restricted function',
    'function called', 'callable', 'calls ', 'called',
)


def _is_trigger(meaning: str) -> bool:
    text = str(meaning or '').lower()
    return any(token in text for token in TRIGGER_TOKENS)


def main() -> dict:
    rows = []
    if not CASES.is_dir():
        print(f'no cases dir: {CASES}')
        return {'rows': rows}

    for case_dir in sorted(CASES.iterdir()):
        if not case_dir.is_dir():
            continue
        spec_path = case_dir / 'stage2_run' / 'stage3-spec.json'
        if not spec_path.is_file():
            continue
        try:
            spec = json.loads(spec_path.read_text())
        except json.JSONDecodeError:
            continue
        for claim in spec.get('claims', []):
            contract = claim.get('binding_contract') or {}
            flagged = []
            for sym in contract.get('symbols', []):
                appears = set(sym.get('appears_in') or [])
                if not (appears & {'I', 'V'}):
                    continue
                if not _is_trigger(sym.get('meaning') or ''):
                    continue
                flagged.append({
                    'symbol': sym.get('symbol'),
                    'appears_in': sorted(appears),
                    'meaning': sym.get('meaning'),
                })
            if flagged:
                rows.append({
                    'case': case_dir.name,
                    'claim_id': claim.get('claim_id'),
                    'flagged_symbols': flagged,
                })

    report = {
        'schema_version': 'stage2-trigger-audit/1',
        'generated': '2026-11-13',
        'trigger_in_iv_cases': len({r['case'] for r in rows}),
        'flagged_claims': len(rows),
        'rows': rows,
    }
    OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')

    lines = [
        '# stage2 触发谓词误入 I/V 审计',
        '',
        f'触发/活跃性谓词被放进 I/V 的 claim 数：**{len(rows)}**；',
        f'涉及案例数：**{report["trigger_in_iv_cases"]}**。',
        '',
        '| case | claim_id | 触发谓词 | 角色 |',
        '| --- | --- | --- | --- |',
    ]
    for row in rows:
        for sym in row['flagged_symbols']:
            lines.append(
                f"| {row['case']} | {row['claim_id']} | "
                f"{sym['symbol']} | {'/'.join(sym['appears_in'])} |")
    OUT_MD.write_text('\n'.join(lines) + '\n')

    print(f'trigger-in-I/V cases = {report["trigger_in_iv_cases"]}')
    print(f'flagged claims = {len(rows)}')
    print(f'json -> {OUT_JSON}')
    print(f'md   -> {OUT_MD}')
    return report


if __name__ == '__main__':
    main()
