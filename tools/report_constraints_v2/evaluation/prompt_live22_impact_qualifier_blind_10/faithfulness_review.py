#!/usr/bin/env python3
"""Review generated P/I/V claims for report fidelity only."""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STAGE2 = HERE.parents[1]
sys.path.insert(0, str(STAGE2))
for directory in (STAGE2 / 'lib', STAGE2 / 'cli'):
    sys.path.insert(0, str(directory))
from lib.deepseek import extract_deepseek  # noqa: E402

SHADOW_PROMPT = '''Analyze only this vulnerability report, before seeing machine output.
Return JSON only:
{"case_id":"string","core_claim":{"P":{"text":"before-action conditions","evidence_quote":"verbatim or empty"},"I":{"text":"report-supported required property","evidence_quote":"verbatim or empty"},"V":{"text":"reported violation or outcome","evidence_quote":"verbatim or empty"}}}
Summarize the report's central P/I/V meaning. Preserve explicit conditions and qualifiers. Mark an item unclear in its text when the report does not state it. Do not add assumptions or infer code behavior. This is a report-only reference, not a completeness inventory.'''

FAITHFULNESS_PROMPT = '''Evaluate only whether the generated P/I/V formulas are faithful to the vulnerability report.
You receive the report, an independent report-only P/I/V summary, extracted report statements, and generated claims.
Return JSON only, exactly:
{"case_id":"string","claim_ratings":[{"claim_id":"string","P":{"rating":"pass|partial|fail|not_evaluable","reason":"one concise sentence grounded in report evidence"},"I":{"rating":"pass|partial|fail|not_evaluable","reason":"one concise sentence grounded in report evidence"},"V":{"rating":"pass|partial|fail|not_evaluable","reason":"one concise sentence grounded in report evidence"}}],"overall":"faithful|weakened|unfaithful|not_evaluable","main_fidelity_issue":"string"}

Judge the meaning of each generated expression against the report facts and the independent summary. Pass means materially supported by the report with its important conditions and direction preserved. Partial means the expression is report-related but weakens, omits, or broadens a material condition, scope, state, or qualifier. Fail means it contradicts the report or adds an unsupported material fact. If that role has no generated expression, use not_evaluable.

Do not rate impact-list completeness, number of claims, whether an impact was selected, formalization status, solver results, SMT consistency, or readiness for a later stage. Do not penalize a claim for other report effects that it does not represent. Do not treat a missing formula as unfaithful; mark only that role not_evaluable. Do not infer correctness from a consistent audit label. Cite the report's wording for every partial or fail rating.

Overall uses only evaluable P/I/V ratings: if none are evaluable, return not_evaluable; otherwise any fail makes overall unfaithful, else any partial makes it weakened, else faithful.'''


def load(path):
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return None


def review_call(payload, base_dir, model, prompt):
    """Keep malformed review responses and make one bounded retry."""
    last_error = None
    for attempt in range(2):
        call_dir = (base_dir if attempt == 0 and not base_dir.exists()
                    else base_dir / f'retry-{attempt + 1}')
        call_dir.mkdir(parents=True, exist_ok=True)
        try:
            return extract_deepseek(payload, call_dir, model, prompt), attempt + 1
        except (ValueError, KeyError, TypeError) as exc:
            last_error = exc
    raise ValueError(f'blind review failed after two calls: {last_error}')


def main():
    all_results = []
    review_root = HERE / 'faithfulness-review-candidates'
    for run in sorted(p for p in (HERE / 'runs').iterdir()
                      if p.is_dir() and (p / 'status.json').is_file()
                      and json.loads((p / 'status.json').read_text()).get('acceptance_status') == 'candidate_checks_passed'):
        case = run.name
        report = (run / 'extraction-input.txt').read_text()
        shadow_dir = review_root / case / 'shadow'
        saved_shadow = load(shadow_dir / 'shadow.json')
        shadow_calls = 0
        if saved_shadow is not None:
            shadow = saved_shadow
        else:
            try:
                shadow, shadow_calls = review_call(
                    'REPORT TEXT:\n' + report + '\n', shadow_dir,
                    'deepseek-flash', SHADOW_PROMPT)
                shadow['case_id'] = case
                (shadow_dir / 'shadow.json').write_text(
                    json.dumps(shadow, ensure_ascii=False, indent=2) + '\n')
            except ValueError as exc:
                all_results.append({'case_id': case, 'overall': 'not_evaluable',
                                    'review_error': str(exc),
                                    'review_calls': shadow_calls})
                continue
        elements = load(run / 'elements.json')
        formal = load(run / 'formalization.json')
        payload = '\n'.join([
            'REPORT TEXT:\n' + report,
            'INDEPENDENT REPORT-ONLY P/I/V SUMMARY:\n' +
            json.dumps(shadow, ensure_ascii=False, indent=2),
            'EXTRACTED REPORT STATEMENTS:\n' +
            json.dumps(elements, ensure_ascii=False, indent=2),
            'GENERATED P/I/V CLAIMS:\n' +
            json.dumps(formal, ensure_ascii=False, indent=2),
        ])
        compare_dir = review_root / case / 'compare'
        saved_result = load(compare_dir / 'model-claim.json')
        compare_calls = 0
        if saved_result is not None:
            result = saved_result
        else:
            try:
                result, compare_calls = review_call(
                    payload, compare_dir, 'deepseek-flash', FAITHFULNESS_PROMPT)
            except ValueError as exc:
                all_results.append({'case_id': case, 'overall': 'not_evaluable',
                                    'review_error': str(exc),
                                    'review_calls': shadow_calls + compare_calls})
                continue
        result['case_id'] = case
        result['review_calls'] = len(list(
            (review_root / case).rglob('model-usage.json')))
        all_results.append(result)
        print(json.dumps({'case_id': case,
                          'claims': len(result.get('claim_ratings', [])),
                          'overall': result.get('overall')},
                         ensure_ascii=False), flush=True)
        (HERE / 'FAITHFULNESS_CANDIDATES.json').write_text(json.dumps({
            'schema_version': 'stage2-live22-impact-qualifier-piv-faithfulness-review/1',
            'review_standard': 'piv_report_fidelity_only',
            'reviewer_kind': 'same_model_two_phase_report_only_reference',
            'model': 'deepseek-flash',
            'excluded_from_rating': [
                'impact inventory completeness', 'formalization status',
                'solver results', 'stage continuation readiness',
            ],
            'limitation': ('The reviewer is the same model family as generation; '
                           'this is not an independent human gold standard.'),
            'cases': all_results,
        }, ensure_ascii=False, indent=2) + '\n')
    (HERE / 'FAITHFULNESS_CANDIDATES.json').write_text(json.dumps({
        'schema_version': 'stage2-live22-impact-qualifier-piv-faithfulness-review/1',
        'review_standard': 'piv_report_fidelity_only',
        'reviewer_kind': 'same_model_two_phase_report_only_reference',
        'model': 'deepseek-flash',
        'excluded_from_rating': [
            'impact inventory completeness', 'formalization status',
            'solver results', 'stage continuation readiness',
        ],
        'limitation': ('The reviewer is the same model family as generation; '
                       'this is not an independent human gold standard.'),
        'cases': all_results,
    }, ensure_ascii=False, indent=2) + '\n')


if __name__ == '__main__':
    main()
