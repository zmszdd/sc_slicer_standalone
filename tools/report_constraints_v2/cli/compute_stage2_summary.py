#!/usr/bin/env python3
"""从 stage-2 batch 输出聚合出 stage2-wide-eval 汇总（替换陈旧的 SUMMARY.json）。

用法（cwd = tools/report_constraints_v2）：
    python -m cli.compute_stage2_summary \
        --runs-root /tmp/recall_rerun_88_final_1793789722 \
        --out evaluation/goldset_v2_pos91/SUMMARY.json
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def aggregate(runs_root: Path) -> dict:
    rows = []
    for batch_dir in sorted(Path(runs_root).glob('batch_*')):
        summary_path = batch_dir / 'batch-summary.json'
        if not summary_path.is_file():
            continue
        data = json.loads(summary_path.read_text())
        for result in data.get('results', []):
            status = result.get('status') or {}
            rows.append(status)

    n_reports = len(rows)
    at_least_one_candidate = sum(
        1 for r in rows if (r.get('formalized_impact_count') or 0) > 0)
    complete_reports = sum(
        1 for r in rows if r.get('rule_formalization_status') == 'complete')
    zero_output_reports = sum(
        1 for r in rows if (r.get('formalized_impact_count') or 0) == 0)
    impact_total = sum(r.get('impact_count') or 0 for r in rows)
    impact_formalized = sum(r.get('formalized_impact_count') or 0 for r in rows)
    logical_total = sum(r.get('logically_complete_denominator') or 0 for r in rows)
    logical_formalized = sum(
        int(round((r.get('logically_complete_denominator') or 0)
                  * (r.get('logically_complete_formalization_rate') or 0)))
        for r in rows)
    stage2_can_continue = sum(1 for r in rows if r.get('stage2_can_continue'))

    return {
        'schema_version': 'stage2-wide-eval/1',
        'name': 'goldset_v2_pos91',
        'n_reports': n_reports,
        'at_least_one_candidate': at_least_one_candidate,
        'complete_reports': complete_reports,
        'zero_output_reports': zero_output_reports,
        'impact_total': impact_total,
        'impact_formalized': impact_formalized,
        'impact_formalization_rate':
            impact_formalized / impact_total if impact_total else 0.0,
        'logically_complete_total': logical_total,
        'logically_complete_formalized': logical_formalized,
        'logically_complete_rate':
            logical_formalized / logical_total if logical_total else 0.0,
        'stage2_can_continue': stage2_can_continue,
        'report_level': {
            'complete': complete_reports,
            'partial': at_least_one_candidate - complete_reports,
            'zero_output': zero_output_reports,
        },
        'zero_output_cases': [],  # per-case names not carried in batch summary
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runs-root', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args(argv)

    summary = aggregate(args.runs_root)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
