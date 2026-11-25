#!/usr/bin/env python3
"""Aggregate stage-2 failures for the mainline sample.

The mainline executor continues past individual stage-2 failures, so this
script scans ``mainline_stage2_out/*/status.json`` and emits the non-continuable
cases with a root-cause label.  It is the visibility layer for the P1 problem
"stage-2 report parsing caps the recall ceiling".
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE / 'mainline_stage2_out'
OUT_JSON = HERE / 'mainline_stage2_failures.json'
OUT_MD = HERE / 'mainline_stage2_failures.md'


def label(status: dict) -> str:
    error = status.get('error') or ''
    if 'HTTP 402' in error:
        return 'stage2_http_402'
    if status.get('core_formalization_status') == 'not_attempted':
        if status.get('impact_inventory_status') == 'no_marked_impact_section':
            return 'report_no_marked_impact_section'
        return 'stage2_not_attempted'
    if 'invalid symbol count' in error:
        return 'invalid_symbol_count'
    if 'formal property missing source' in error:
        return 'formal_property_missing_source'
    if 'core P/I/V is not fully formalized' in (status.get('continuation_blockers') or []):
        return 'core_piv_not_fully_formalized'
    if status.get('core_formalization_status') == 'failed':
        return 'stage2_failed'
    return 'needs_review'


def main() -> dict:
    rows = []
    counter = Counter()
    for status_path in sorted(ROOT.glob('*/status.json')):
        try:
            status = json.loads(status_path.read_text())
        except (json.JSONDecodeError, OSError):
            continue
        if status.get('stage2_can_continue') is True:
            continue
        reason = label(status)
        counter[reason] += 1
        rows.append({
            'case': status_path.parent.name,
            'root_cause': reason,
            'core_formalization_status': status.get('core_formalization_status'),
            'impact_count': status.get('impact_count'),
            'formalized_impact_count': status.get('formalized_impact_count'),
            'error': status.get('error'),
            'warnings': status.get('warnings') or [],
        })
    out = {
        'schema_version': 'mainline-stage2-failures/1',
        'source': str(ROOT),
        'total': len(rows),
        'root_cause_distribution': dict(counter),
        'rows': rows,
    }
    OUT_JSON.write_text(json.dumps(out, ensure_ascii=False, indent=2) + '\n')
    md = f"# 主口径 stage2 失败归因\n\n总数：{len(rows)}\n\n| 根因 | 数量 |\n| --- | ---: |\n"
    for reason, count in counter.most_common():
        md += f'| {reason} | {count} |\n'
    md += '\n| case | 根因 | 错误/警告 |\n| --- | --- | --- |\n'
    for row in rows:
        detail = (row.get('error') or '; '.join(row.get('warnings') or []))[:120]
        md += f"| {row['case']} | {row['root_cause']} | {detail} |\n"
    OUT_MD.write_text(md)
    print(f'stage2 failures: {len(rows)} {dict(counter)}')
    return out


if __name__ == '__main__':
    main()
