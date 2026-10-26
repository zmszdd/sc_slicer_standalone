#!/usr/bin/env python3
"""Summarize live-24b vs live-24 vs live-23 paired outcomes (zero model calls)."""
import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
LIVE24 = HERE.parent / 'prompt_live24_relation_trace_frozen_10'
LIVE23 = HERE.parent / 'prompt_live23_relation_context_generation_frozen_10'


def key(row):
    return (row['case_id'], row['impact_id'], row['intent_id'])


def end_state(row):
    if not row.get('generated'):
        return 'no_rule'
    status = row.get('fidelity_status')
    if status == 'passed':
        return 'passed'
    if status == 'needs_review':
        return 'needs_review'
    if status == 'failed':
        return 'failed'
    return 'audit_unavailable'


def load(path):
    data = json.loads((path / 'PAIRED_RESULTS.json').read_text())
    return {key(row): row for row in data['results']}


def main():
    b = load(HERE)
    a24 = load(LIVE24)
    a23 = load(LIVE23)
    assert set(b) == set(a24) == set(a23)

    def counts(rows):
        return Counter(end_state(rows[k]) for k in rows)

    for label, rows in (('live-23', a23), ('live-24', a24), ('live-24b', b)):
        c = counts(rows)
        generated = sum(c[s] for s in ('passed', 'needs_review', 'failed'))
        passed = c['passed']
        print(f"{label}: generated {generated}/52, passed {passed}/52 "
              f"({passed / 52:.1%} of pairs, "
              f"{passed}/{generated} = {passed / generated:.1%} of generated) "
              f"needs_review {c['needs_review']} failed {c['failed']} "
              f"no_rule {c['no_rule']} audit_unavailable {c['audit_unavailable']}")

    calls = json.loads((HERE / 'PAIRED_RESULTS.json').read_text())
    print(f"live-24b model calls: {calls['external_model_invocations']}")

    # paired transitions 24 -> 24b
    transitions = Counter()
    for k in b:
        transitions[(end_state(a24[k]), end_state(b[k]))] += 1
    print('\ntransitions live-24 -> live-24b:')
    for (frm, to), n in sorted(transitions.items()):
        print(f'  {frm} -> {to}: {n}')

    # salvage usage: pairs where a response-normalization.json exists
    salvaged = []
    for run_dir in sorted((HERE / 'live-24b').rglob('neural-formalization')):
        norm = run_dir / 'response-normalization.json'
        if norm.is_file():
            salvaged.append(run_dir)
    print(f"\nresponse-normalization records: {len(salvaged)}")
    for run_dir in salvaged:
        pair_dir = run_dir.parent.parent
        result = json.loads((pair_dir / 'result.json').read_text())
        print(f"  {pair_dir.parent.name}/{pair_dir.name}: "
              f"generated={result['generated']} "
              f"status={result.get('fidelity_status')}")

    # no-rule family attribution for 24b
    print('\nlive-24b no-rule errors:')
    for k in sorted(b):
        if not b[k].get('generated'):
            print(f"  {k[0]} / {k[1]} / {k[2]}: {b[k].get('error_type')}: "
                  f"{str(b[k].get('error'))[:160]}")


if __name__ == '__main__':
    main()
