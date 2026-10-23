#!/usr/bin/env python3
"""Same-model heterogeneous-prompt semantic review for the current fidelity measurement.

The generation prompt and the primary (assistant) review share one author and
one framing, so a second review that merely re-reads them inherits their blind
spots.  This script instead asks deepseek-flash -- the same single model the
whole pipeline uses, per the stage-2 zero-human constraint -- through a
structurally different auditor prompt with its own rating language and its own
judgment checklist.  Agreement between the two reviews then reflects the
artifact, not the phrasing.

For each run directory it assembles the report text, the extracted elements,
the formal plan (candidates only), and the mechanical outcome, sends one
request, and stores the raw response under dual-review/<case>/.
"""

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STAGE2 = HERE.parents[1]
sys.path.insert(0, str(STAGE2))
for directory in (STAGE2 / 'lib', STAGE2 / 'cli'):
    sys.path.insert(0, str(directory))

from lib.deepseek import extract_deepseek  # noqa: E402


REVIEW_PROMPT = '''You audit machine translations of vulnerability reports into formal claims. \
For the supplied case you receive the report text, the extracted semantic elements, and (when \
formalization succeeded) the formal plan, plus the mechanical outcome. Judge each stage against \
the report text alone; treat code or exploit details inside the report as context, not as extra \
requirements.

Return exactly one JSON object with this shape:
{"case_id": "string",
 "preconditions_before_action": {"rating": "pass|partial|fail|not_evaluable", "reason": "string"},
 "claimed_required_property": {"rating": "pass|partial|fail|not_evaluable", "reason": "string"},
 "reported_bad_outcome": {"rating": "pass|partial|fail|not_evaluable", "reason": "string"},
 "formal_preconditions": {"rating": "pass|partial|fail|not_evaluable", "reason": "string"},
 "formal_required_property": {"rating": "pass|partial|fail|not_evaluable", "reason": "string"},
 "formal_bad_outcome": {"rating": "pass|partial|fail|not_evaluable", "reason": "string"},
 "most_serious_defect": "string"}

Rating scale:
- pass: faithful to the report and correctly scoped
- partial: the direction is right but a material condition, scope, or observable is weakened or omitted
- fail: misclassified, contradicted, circular, or missing a critical report condition
- not_evaluable: that stage produced no artifact to judge

Judgment checklist (apply silently, do not echo it):
1. "preconditions_before_action" covers the extracted BEFORE-facts: nothing that is itself an \
observation of the attack's outcome may appear among them.
2. "claimed_required_property" covers the extracted requirement, including its applicability \
scope: a requirement narrowed to the one attacker/victim configuration of the incident when the \
report states a general rule is a partial at best.
3. "reported_bad_outcome" covers the extracted direct harm.
4. For the formal stage additionally check: every numeric constant bound in a comparison must \
occur in the report text; comparison directions must match the report; two different extracted \
facts collapsing into one repeated predicate means one fact is no longer represented; a solver \
finding is never evidence of semantic correctness.
When the formal stage produced no artifact, rate its three formal_* fields "not_evaluable". \
Base every reason on concrete report fragments.'''


def outcome_summary(run):
    status = json.loads((run / 'status.json').read_text())
    return {
        'core_formalization_status': status.get('core_formalization_status'),
        'acceptance_status': status.get('acceptance_status'),
        'input_screening_status': status.get('input_screening_status'),
    }


def payload(run):
    report = (run / 'extraction-input.txt').read_text()
    parts = [f'REPORT TEXT:\n{report}\n']
    elements_path = run / 'elements-ids.json'
    if elements_path.is_file():
        parts.append('EXTRACTED ELEMENTS (JSON):\n'
                     + elements_path.read_text() + '\n')
    else:
        parts.append('EXTRACTED ELEMENTS: none (pipeline stopped at input screening)\n')
    plan_path = run / 'formal-plan.json'
    if plan_path.is_file():
        parts.append('FORMAL PLAN (JSON):\n' + plan_path.read_text() + '\n')
    else:
        parts.append('FORMAL PLAN: none (the pipeline rejected the formalization; '
                     'rate the three formal_* fields not_evaluable)\n')
    parts.append('MECHANICAL OUTCOME (JSON):\n'
                 + json.dumps(outcome_summary(run), indent=2) + '\n')
    return '\n'.join(parts)


def main():
    runs = sorted(path for path in (HERE / 'runs').iterdir()
                  if path.is_dir() and (path / 'status.json').is_file())
    results = []
    for run in runs:
        case = run.name
        out = HERE / 'dual-review' / case
        out.mkdir(parents=True, exist_ok=True)
        claim = extract_deepseek(payload(run), out, 'deepseek-flash',
                                 prompt=REVIEW_PROMPT, proxy='direct')
        claim['case_id'] = case
        results.append(claim)
        print(json.dumps({'case': case,
                          'formal_required_property':
                              claim.get('formal_required_property', {}).get('rating')},
                         ensure_ascii=False))
    (HERE / 'DUAL_REVIEW.json').write_text(
        json.dumps({'schema_version': 'stage2-live4-dual-review/1',
                    'reviewer_kind': 'same_model_heterogeneous_prompt',
                    'model': 'deepseek-flash',
                    'ratings': results}, ensure_ascii=False, indent=2) + '\n')


if __name__ == '__main__':
    main()
