#!/usr/bin/env python3
"""Aggregate blind stage-2 batch results into one summary artifact."""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT_JSON = HERE / 'blind_stage2_summary.json'
OUT_MD = HERE / 'blind_stage2_summary.md'
BATCH_DIRS = [Path('/tmp/blind_stage2_b0v5'), Path('/tmp/blind_stage2_b1v2')]


def main() -> int:
    rows = []
    for batch in BATCH_DIRS:
        for case_dir in sorted(batch.iterdir()):
            if not case_dir.is_dir():
                continue
            status_path = case_dir / 'status.json'
            if not status_path.is_file():
                continue
            status = json.loads(status_path.read_text())
            rows.append({
                'case': case_dir.name,
                'core_formalization_status': status.get('core_formalization_status'),
                'acceptance_status': status.get('acceptance_status'),
                'stage2_can_continue': status.get('stage2_can_continue'),
                'formalization_rate': status.get('formalization_rate'),
                'impact_count': status.get('impact_count'),
                'formalized_impact_count': status.get('formalized_impact_count'),
                'pending_impact_count': status.get('pending_impact_count'),
                'external_model_invocations': status.get('external_model_invocations'),
                'error': status.get('error'),
                'warnings': status.get('warnings') or [],
            })
    rows.sort(key=lambda r: r['case'])
    passed = sum(1 for r in rows if r['acceptance_status'] == 'candidate_checks_passed')
    can_continue = sum(1 for r in rows if r['stage2_can_continue'])
    report = {
        'schema_version': 'blind-stage2-summary/1',
        'generated': '2026-11-13',
        'total': len(rows),
        'candidate_checks_passed': passed,
        'stage2_can_continue': can_continue,
        'rows': rows,
    }
    OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')

    lines = [
        '# 盲测阶段二摘要',
        '',
        f'共 **{len(rows)}** 例；`candidate_checks_passed` **{passed}**；'
        f'`stage2_can_continue` **{can_continue}**。',
        '',
        '| case | 核心状态 | 验收 | 可续 | 规则化率 | 影响 |',
        '| --- | --- | --- | ---: | ---: | ---: |',
    ]
    for r in rows:
        rate = r['formalization_rate']
        rate_s = '-' if rate is None else f'{rate:.0%}'
        lines.append(
            f"| {r['case']} | {r['core_formalization_status']} | "
            f"{r['acceptance_status']} | {bool(r['stage2_can_continue'])} | "
            f"{rate_s} | {r['formalized_impact_count']}/{r['impact_count']} |")
    OUT_MD.write_text('\n'.join(lines) + '\n')
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
