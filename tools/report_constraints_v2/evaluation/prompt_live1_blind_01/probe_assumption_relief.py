#!/usr/bin/env python3
"""Offline (zero model calls) probe: does assumption_numeric_relief unblock
the two numeric-gate rejections of prompt_live1_blind_01?

Re-runs the deterministic stage on the SAVED retry-1 model claims -- the frozen
run outcomes are NOT rewritten; this only demonstrates that the same plan the
model already produced would have passed with the semantic-live-2 gate.
"""

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STAGE2 = HERE.parents[1]
for directory in (STAGE2 / 'lib', STAGE2 / 'cli'):
    sys.path.insert(0, str(directory))

from salvage import check_numeric_plan  # noqa: E402
from plan_synthesizer import synthesize_id_formalization  # noqa: E402

CASES = (
    'Kinetiq_k8aVPPVguSE__NozCq8ZgtXD__nayg2eGrYFC',
    'Intuition_2VUsxVJwReb__aayBh4TiWVT__JfcE4eZnVpe',
)


def verdict(plan, elements, relax):
    try:
        check_numeric_plan(plan, elements, relax_assumptions=relax)
        return 'pass'
    except ValueError as exc:
        return str(exc)


def main():
    results = []
    for case in CASES:
        run = HERE / 'runs' / case
        plan = json.loads((run / 'neural-formalization-retry-1/model-claim.json').read_text())
        elements = json.loads((run / 'elements-ids.json').read_text())
        strict = verdict(plan, elements, relax=False)
        relaxed = verdict(plan, elements, relax=True)
        synthesis = 'not_attempted'
        if relaxed == 'pass':
            try:
                synthesize_id_formalization(plan, elements)
                synthesis = 'pass'
            except (ValueError, KeyError, TypeError) as exc:
                synthesis = str(exc)
        results.append({
            'case_id': case,
            'strict_gate': strict,
            'relaxed_gate': relaxed,
            'relaxed_synthesis': synthesis,
            'source': 'neural-formalization-retry-1/model-claim.json (saved, unchanged)',
        })
    report = {
        'schema_version': 'stage2-live1-assumption-relief-probe/1',
        'date': '2026-10-06',
        'model_calls': 0,
        'purpose': ('Prove the assumption_numeric_relief fix addresses the '
                    'Kinetiq/Intuition numeric-gate rejections without touching '
                    'the frozen run outcomes.'),
        'results': results,
    }
    (HERE / 'PROBE_ASSUMPTION_RELIEF.json').write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(report['results'], ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
