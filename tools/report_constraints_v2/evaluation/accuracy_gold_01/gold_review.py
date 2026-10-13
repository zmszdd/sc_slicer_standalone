#!/usr/bin/env python3
"""Two-phase blind gold review for stage-2 translation accuracy.

The corpus itself is claim-level ground truth (every case directory carries a
passing PoC test), so what accuracy needs is a translation-level gold standard.
This script builds one with deepseek-flash -- the same single model the whole
stage-2 zero-human pipeline uses, per the standing constraint -- through a
two-phase protocol that is blind to everything the pipeline and the prior
reviews concluded:

  Phase 1 (shadow): the judge sees ONLY the report input text and restates the
    core claim in its own words (BEFORE-conditions, required property, bad
    outcome). No machine artifact is in the payload, so this restatement
    cannot be anchored by the pipeline's choices.

  Phase 2 (compare): the judge sees the report, its OWN phase-1 restatement,
    and the machine artifacts (extracted elements plus the final formal plan
    for accepted candidates; the last formalization attempt and the rejection
    error for rejected runs). It rates each P/I/V dimension against its own
    restatement with its own vocabulary (faithful / weakened / unfaithful),
    never seeing the pipeline's acceptance status, the primary review, or the
    dual review.

Known limitation, disclosed rather than hidden: a same-model judge can carry
self-preference bias; the two-phase shadow design and the blind payload are
the mitigations, and the resulting number is a same-model blind gold
measurement, not a human gold standard.
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


BATCHES = [
    'prompt_live1_blind_01',
    'prompt_live2_blind_01',
    'prompt_live3_blind_01',
    'prompt_live4_blind_01',
    'final_holdout_01',
]


SHADOW_PROMPT = '''You translate vulnerability reports into precise claim statements. \
You receive ONLY the report text. Before any machine processing exists, write your own \
restatement of the report's single core security claim.

Return exactly one JSON object:
{"case_id": "string",
 "before_conditions": ["each factual condition that holds BEFORE the attack action, in your own words"],
 "required_property": "the property the report claims SHOULD hold, including who it protects and when it applies, in your own words",
 "bad_outcome": "the direct bad outcome the report says occurs instead, in your own words"}

Rules: conditions must be true before the attack; effects of the attack belong to the \
bad outcome; mechanism/root-cause detail is context, not a condition. Base every entry \
on concrete report fragments. Return JSON only.'''


CANDIDATE_PROMPT = '''You audit machine translations of vulnerability reports. You previously wrote your \
own restatement of this report (YOUR RESTATEMENT below). Now the machine's artifacts arrive. \
Judge ONLY against the report text and your own restatement; the machine's mechanical \
success says nothing about faithfulness.

Return exactly one JSON object:
{"case_id": "string",
 "element_preconditions": {"rating": "faithful|weakened|unfaithful", "reason": "string"},
 "element_required_property": {"rating": "faithful|weakened|unfaithful", "reason": "string"},
 "element_bad_outcome": {"rating": "faithful|weakened|unfaithful", "reason": "string"},
 "formula_preconditions": {"rating": "faithful|weakened|unfaithful", "reason": "string"},
 "formula_required_property": {"rating": "faithful|weakened|unfaithful", "reason": "string"},
 "formula_bad_outcome": {"rating": "faithful|weakened|unfaithful", "reason": "string"},
 "constants_not_in_report": ["numeric constants used in the formal plan that do not appear in the report text"],
 "collapsed_facts": ["pairs of machine-extracted facts encoded by one repeated identical predicate"],
 "overall": "faithful|weakened|unfaithful"}

Rating scale:
- faithful: captures the report's fact/property/outcome without material loss or distortion
- weakened: direction is right but a material condition, scope, or observable is dropped, narrowed, or paraphrased into something weaker
- unfaithful: wrong fact, wrong direction, fabricated relation, circular encoding, or a critical report condition missing

Rules: a free Boolean is acceptable only when the report states the qualitative condition \
without a numeric definition; two facts sharing one identical predicate means one fact is \
unrepresented; every numeric bound constant must occur in the report text. Return JSON only.'''


REJECTED_PROMPT = '''You audit a machine pipeline's REFUSAL. You previously wrote your own restatement \
of this report (YOUR RESTATEMENT below). The pipeline produced the machine artifacts below \
and then REFUSED to accept the formalization, citing the rejection error given. Judge whether \
the refusal was correct, using only the report text and your own restatement.

Return exactly one JSON object:
{"case_id": "string",
 "rejection_verdict": "correct_catch|misfire|honest_abstain",
 "reason": "string",
 "what_the_machine_should_have_done": "string"}

Verdicts:
- correct_catch: the machine's final formal attempt genuinely misrepresents the report \
(wrong fact or direction, fabricated relation, hidden bound, self-contradiction), so \
refusing to emit it was right
- misfire: the attempt is faithful (or repairable in an obvious way the machine was told \
about), and the refusal was mechanical over-strictness that blocked a faithful translation
- honest_abstain: the pipeline stopped before formalization because the report itself \
lacks the basis for a checkable claim, which is the honest outcome

Return JSON only.'''


def last_attempt_plan(run):
    plan = run / 'formal-plan.json'
    if plan.is_file():
        return plan.read_text(), 'final formal plan'
    attempts = sorted(run.glob('neural-formalization-retry-*'),
                      key=lambda p: int(p.name.rsplit('-', 1)[-1]))
    dirs = (attempts + [run / 'neural-formalization']) if attempts else \
        [run / 'neural-formalization']
    for d in reversed(dirs):
        claim = d / 'model-claim.json'
        if claim.is_file():
            return claim.read_text(), f'last formalization attempt ({d.name})'
    return None, None


def rejection_error(status):
    error = status.get('error')
    if error:
        return str(error)
    warnings = status.get('warnings') or []
    if warnings:
        return '; '.join(str(w) for w in warnings)
    return str(status.get('core_formalization_status'))


def main():
    evaluation = STAGE2 / 'evaluation'
    records = []
    for batch in BATCHES:
        runs_root = evaluation / batch / 'runs'
        if not runs_root.is_dir():
            continue
        for run in sorted(runs_root.iterdir()):
            if not (run / 'status.json').is_file():
                continue
            status = json.loads((run / 'status.json').read_text())
            candidate = status.get('acceptance_status') == 'candidate_checks_passed'
            case = f'{batch}::{run.name}'
            out = HERE / 'gold-review' / case.replace('::', '__')
            out.mkdir(parents=True, exist_ok=True)
            report = (run / 'extraction-input.txt').read_text()

            # Phase 1: shadow restatement, artifacts invisible.
            shadow_dir = out / 'shadow'
            shadow_dir.mkdir(exist_ok=True)
            shadow = extract_deepseek(
                f'REPORT TEXT:\n{report}\n', shadow_dir, 'deepseek-flash',
                prompt=SHADOW_PROMPT, proxy='direct')
            shadow['case_id'] = case

            # Phase 2: comparison against the judge's own restatement.
            judge_dir = out / 'judge'
            judge_dir.mkdir(exist_ok=True)
            parts = [f'REPORT TEXT:\n{report}\n',
                     'YOUR RESTATEMENT (you wrote this before seeing any machine '
                     f'output):\n{json.dumps(shadow, ensure_ascii=False, indent=1)}\n']
            elements_path = run / 'elements-ids.json'
            if elements_path.is_file():
                parts.append('MACHINE EXTRACTED ELEMENTS (JSON):\n'
                             + elements_path.read_text() + '\n')
            else:
                parts.append('MACHINE EXTRACTED ELEMENTS: none (the pipeline '
                             'stopped before extraction)\n')
            if candidate:
                parts.append('MACHINE FORMAL PLAN (JSON):\n'
                             + (run / 'formal-plan.json').read_text() + '\n')
                claim = extract_deepseek(
                    '\n'.join(parts), judge_dir, 'deepseek-flash',
                    prompt=CANDIDATE_PROMPT, proxy='direct')
                kind = 'candidate'
            else:
                plan_text, plan_label = last_attempt_plan(run)
                if plan_text:
                    parts.append(f'MACHINE {plan_label.upper()} (JSON, rejected):\n'
                                 + plan_text + '\n')
                else:
                    parts.append('MACHINE FORMAL ATTEMPT: none (the pipeline '
                                 'stopped before formalization)\n')
                parts.append(f'REJECTION ERROR:\n{rejection_error(status)}\n')
                claim = extract_deepseek(
                    '\n'.join(parts), judge_dir, 'deepseek-flash',
                    prompt=REJECTED_PROMPT, proxy='direct')
                kind = 'rejected'
            claim['case_id'] = case
            claim['engineering_route'] = kind
            claim['batch'] = batch
            records.append(claim)
            headline = (claim.get('overall') or
                        claim.get('rejection_verdict') or '?')
            print(json.dumps({'case': case[:60], 'judge': headline},
                             ensure_ascii=False))
    (HERE / 'GOLD_REVIEW.json').write_text(
        json.dumps({'schema_version': 'stage2-accuracy-gold-review/1',
                    'reviewer_kind': 'same_model_two_phase_blind_gold',
                    'model': 'deepseek-flash',
                    'protocol': ('phase 1 shadow restatement from report only; '
                                 'phase 2 rating against the shadow; blind to '
                                 'pipeline acceptance, primary review, and dual '
                                 'review; disclosed same-model self-preference '
                                 'limitation'),
                    'cases': records}, ensure_ascii=False, indent=2) + '\n')


if __name__ == '__main__':
    main()
