#!/usr/bin/env python3
"""Aggregate per-case stage-2 metrics from a set of run directories.

Usage: python3 evaluation/aggregate_blind.py <run_dir_or_parent> [more...]
If a parent directory is given, all child run dirs are scanned.
"""
import json, sys
from pathlib import Path

def run_dirs(args):
    out = []
    for a in args:
        p = Path(a)
        if p.is_dir():
            if (p / 'status.json').exists():
                out.append(p)
            else:
                out.extend(sorted(d for d in p.iterdir() if (d/'status.json').exists()))
    return out

def load(p):
    with open(p) as f:
        return json.load(f)

def main():
    dirs = run_dirs(sys.argv[1:])
    rows = []
    for d in dirs:
        status = load(d / 'status.json')
        assess = None
        ap = d / 'stage2-assessment.json'
        if ap.exists():
            assess = load(ap)
        rf = (assess or {}).get('rule_formalization') or {}
        rows.append({
            'case': d.name,
            'impacts': status.get('impact_count'),
            'formalized': status.get('formalized_impact_count'),
            'acceptance': status.get('acceptance_status'),
            'stage2_can_continue': status.get('stage2_can_continue'),
            'calls': status.get('external_model_invocations'),
            'exit': status.get('exit_code'),
            'pending': status.get('pending_impact_count'),
            'fidelity_failed': rf.get('fidelity_failed_count', 0),
            'fidelity_needs_review': rf.get('fidelity_needs_review_count', 0),
            'fidelity_not_completed': rf.get('fidelity_not_completed_count', 0),
            'failure_stages': rf.get('failure_counts_by_stage', {}),
        })
    if not rows:
        print('no run dirs'); return
    denom = [r for r in rows if (r['impacts'] or 0) > 0]
    total_imp = sum(r['impacts'] or 0 for r in rows)
    total_form = sum(r['formalized'] or 0 for r in rows)
    candidate = sum(1 for r in rows if r['acceptance'] == 'candidate_checks_passed')
    cont = sum(1 for r in rows if r['stage2_can_continue'] is True)
    cont_denom = sum(1 for r in denom if r['stage2_can_continue'] is True)
    calls = sum(r['calls'] or 0 for r in rows)
    fail = {}
    for r in rows:
        for k, v in (r['failure_stages'] or {}).items():
            fail[k] = fail.get(k, 0) + v
    ff = sum(r['fidelity_failed'] for r in rows)
    fnr = sum(r['fidelity_needs_review'] for r in rows)
    fnc = sum(r['fidelity_not_completed'] for r in rows)
    print(f"reports={len(rows)} denominator_reports={len(denom)}")
    print(f"impact_denominator={total_imp} formalized_impacts={total_form} rate={total_form/total_imp if total_imp else 0:.4f}")
    print(f"candidate_checks_passed_reports={candidate}/{len(rows)}")
    print(f"stage2_can_continue={cont}/{len(denom)} (all={cont}/{len(rows)})")
    print(f"model_calls={calls}")
    print(f"fidelity_failed={ff} fidelity_needs_review={fnr} fidelity_not_completed={fnc}")
    print(f"failure_counts_by_stage={fail}")
    print('--- per case ---')
    for r in sorted(rows, key=lambda x: x['case']):
        print(f"{r['case'][:44]:<46} imp={r['impacts']} form={r['formalized']} acc={r['acceptance']:<24} cont={r['stage2_can_continue']} calls={r['calls']}")

if __name__ == '__main__':
    main()
