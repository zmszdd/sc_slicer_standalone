#!/usr/bin/env python3
"""Two-phase blind gold review for the 2026-10-13 live end-to-end smoke runs.

Adapted from evaluation/accuracy_gold_01/gold_review.py (frozen protocol,
prompts kept verbatim) with three smoke-specific changes:

  1. argv is a list of run directories (no BATCHES table) -- smoke runs are
     one-off, never a pre-registered batch.
  2. import fixed: extract_deepseek moved to lib/deepseek.py in the
     DeepSeek single-source refactor; the frozen script still imports it
     from lib.report_only and no longer runs.
  3. rejected runs get BOTH judge calls: the frozen REJECTED_PROMPT verdict
     (correct_catch/misfire) plus a CANDIDATE_PROMPT rating of the rejected
     attempt itself, so "was the extraction faithful" and "was refusing it
     right" are answered separately.

Blindness is the same as the frozen protocol: Phase 1 sees ONLY the report
text; Phase 2 sees the report, the judge's own restatement, and the machine
artifacts. Disclosed limitation likewise: same model (deepseek-flash) as the
pipeline itself, so self-preference cannot be excluded.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STAGE2 = HERE.parents[1]
sys.path.insert(0, str(STAGE2))

from lib.deepseek import extract_deepseek  # noqa: E402


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


def audit_run(run):
    status = json.loads((run / 'status.json').read_text())
    candidate = status.get('acceptance_status') == 'candidate_checks_passed'
    case = run.name
    out = HERE / 'gold-review' / case
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
    record = {'case_id': case, 'run_dir': str(run),
              'engineering_route': 'candidate' if candidate else 'rejected',
              'shadow': shadow}
    if candidate:
        parts.append('MACHINE FORMAL PLAN (JSON):\n'
                     + (run / 'formal-plan.json').read_text() + '\n')
        judge_dir = out / 'judge'
        judge_dir.mkdir(exist_ok=True)
        claim = extract_deepseek(
            '\n'.join(parts), judge_dir, 'deepseek-flash',
            prompt=CANDIDATE_PROMPT, proxy='direct')
        record['faithfulness'] = claim
    else:
        plan_text, plan_label = last_attempt_plan(run)
        if plan_text:
            parts.append(f'MACHINE {plan_label.upper()} (JSON, rejected):\n'
                         + plan_text + '\n')
        else:
            parts.append('MACHINE FORMAL ATTEMPT: none (the pipeline '
                         'stopped before formalization)\n')
        parts.append(f'REJECTION ERROR:\n{rejection_error(status)}\n')
        judge_dir = out / 'judge'
        judge_dir.mkdir(exist_ok=True)
        verdict = extract_deepseek(
            '\n'.join(parts), judge_dir, 'deepseek-flash',
            prompt=REJECTED_PROMPT, proxy='direct')
        record['rejection_verdict'] = verdict
        # Separately rate the rejected attempt's faithfulness (elements +
        # the rejected plan), so extraction quality is measured even when
        # the gate refuses the formalization.
        rating_dir = out / 'judge-rejected-faithfulness'
        rating_dir.mkdir(exist_ok=True)
        rating = extract_deepseek(
            '\n'.join(parts), rating_dir, 'deepseek-flash',
            prompt=CANDIDATE_PROMPT, proxy='direct')
        record['rejected_attempt_faithfulness'] = rating
    return record


def main():
    runs = [Path(a).resolve() for a in sys.argv[1:]]
    if not runs:
        raise SystemExit('usage: gold_review_smoke.py <run-dir> [<run-dir> ...]')
    records = []
    for run in runs:
        if not (run / 'status.json').is_file():
            print(f'skip {run.name}: no status.json', flush=True)
            continue
        records.append(audit_run(run))
        headline = [records[-1].get('faithfulness', {}).get('overall'),
                    records[-1].get('rejection_verdict', {}).get('rejection_verdict')]
        print(json.dumps({'case': run.name, 'judge': headline},
                         ensure_ascii=False), flush=True)
    (HERE / 'SMOKE_GOLD_REVIEW.json').write_text(
        json.dumps({'schema_version': 'stage2-accuracy-gold-review/1',
                    'reviewer_kind': 'same_model_two_phase_blind_gold',
                    'model': 'deepseek-flash',
                    'smoke_runs': [str(r) for r in runs],
                    'protocol': ('phase 1 shadow restatement from report only; '
                                 'phase 2 rating against the shadow; blind to '
                                 'pipeline acceptance; rejected runs additionally '
                                 'get a candidate-style faithfulness rating of the '
                                 'rejected attempt; disclosed same-model '
                                 'self-preference limitation'),
                    'cases': records}, ensure_ascii=False, indent=2) + '\n')


if __name__ == '__main__':
    main()
