#!/usr/bin/env python3
"""Two-phase blind review of the live7 batch, including impact coverage."""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STAGE2 = HERE.parents[1]
sys.path.insert(0, str(STAGE2))
for directory in (STAGE2 / 'lib', STAGE2 / 'cli'):
    sys.path.insert(0, str(directory))
from lib.deepseek import extract_deepseek  # noqa: E402

SHADOW_PROMPT = '''You independently analyze a vulnerability report before seeing any machine output.
Return exactly one JSON object:
{"case_id":"string",
 "core_claim":{"P":"before-attack conditions","I":"required security property and scope","V":"direct reported violation or outcome"},
 "direct_impacts":[{"description":"one distinct direct impact","evidence_quote":"verbatim report fragment","direct_or_downstream":"direct|downstream|unclear"}]}

List distinct direct harms explicitly stated in the report. Do not merge different harms just because they share a cause. Do not include recommendations, root causes, or downstream consequences as separate direct impacts unless the report presents them as impacts. This phase receives report text only; do not infer hidden system facts. JSON only.'''

COMPARE_PROMPT = '''You audit a stage-two translation using only the report, a report-only shadow analysis written before machine output was shown, and machine artifacts.
Return exactly one JSON object:
{"case_id":"string",
 "element_P":{"rating":"pass|partial|fail|not_evaluable","reason":"string"},
 "element_I":{"rating":"pass|partial|fail|not_evaluable","reason":"string"},
 "element_V":{"rating":"pass|partial|fail|not_evaluable","reason":"string"},
 "formal_P":{"rating":"pass|partial|fail|not_evaluable","reason":"string"},
 "formal_I":{"rating":"pass|partial|fail|not_evaluable","reason":"string"},
 "formal_V":{"rating":"pass|partial|fail|not_evaluable","reason":"string"},
 "impact_coverage":{"rating":"complete|partial|inaccurate|not_evaluable","matched_impacts":[{"shadow_impact":"string","coverage_item_ids":["string"],"claim_ids":["string"],"formalized":"yes|no|unclear","reason":"string"}],"omissions_or_errors":["string"]},
 "most_serious_defect":"string"}

For P/I/V, pass means materially faithful and correctly scoped; partial means directionally right but material scope/property/detail is weakened; fail means wrong, fabricated, contradictory, circular, or missing a critical condition; not_evaluable means no artifact. For impacts, each distinct report impact from the shadow list should map to one or more report_impact_coverage entries and then to a claim that actually represents that impact to count as formalized. A coverage row marked formalized is not enough by itself: inspect the associated claim's P/I/V and formal plan. A report impact listed as unformalized is transparent coverage bookkeeping but remains unformalized. Mark partial if impacts are omitted, duplicated in a confusing way, or acknowledged but not represented by a claim. Do not count downstream outcomes as distinct direct impacts. Cite concrete report fragments and IDs. Solver success is not semantic evidence. JSON only.'''

def read_json(path):
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return None

def main():
    runs = sorted(p for p in (HERE / 'runs').iterdir()
                  if p.is_dir() and (p / 'status.json').is_file())
    all_results = []
    for run in runs:
        case = run.name
        report = (run / 'extraction-input.txt').read_text()
        shadow_dir = HERE / 'blind-review' / case / 'shadow'
        shadow_dir.mkdir(parents=True, exist_ok=True)
        shadow = extract_deepseek('REPORT TEXT:\n' + report + '\n', shadow_dir,
                                  'deepseek-flash', prompt=SHADOW_PROMPT, proxy='direct')
        shadow['case_id'] = case
        (shadow_dir / 'shadow.json').write_text(
            json.dumps(shadow, ensure_ascii=False, indent=2) + '\n')

        elements = read_json(run / 'elements-ids.json')
        plan = read_json(run / 'formal-plan.json')
        spec = read_json(run / 'stage3-spec.json') or {}
        status = read_json(run / 'status.json') or {}
        payload = '\n'.join([
            'REPORT TEXT:\n' + report,
            'REPORT-ONLY SHADOW ANALYSIS (written before machine output was shown):\n' +
            json.dumps(shadow, ensure_ascii=False, indent=2),
            'MACHINE EXTRACTED P/I/V ELEMENTS:\n' + json.dumps(elements, ensure_ascii=False, indent=2),
            'MACHINE FORMAL PLAN:\n' + json.dumps(plan, ensure_ascii=False, indent=2),
            'STAGE3 REPORT IMPACT COVERAGE ONLY:\n' + json.dumps(spec.get('report_impact_coverage'), ensure_ascii=False, indent=2),
            'ENGINEERING STATUS (not semantic proof):\n' + json.dumps(status, ensure_ascii=False, indent=2),
        ])
        compare_dir = HERE / 'blind-review' / case / 'compare'
        compare_dir.mkdir(parents=True, exist_ok=True)
        result = extract_deepseek(payload, compare_dir, 'deepseek-flash',
                                  prompt=COMPARE_PROMPT, proxy='direct')
        result['case_id'] = case
        all_results.append(result)
        print(json.dumps({'case_id': case,
                          'impact_coverage': (result.get('impact_coverage') or {}).get('rating'),
                          'formal_I': (result.get('formal_I') or {}).get('rating')},
                         ensure_ascii=False), flush=True)
    (HERE / 'BLIND_REVIEW.json').write_text(json.dumps({
        'schema_version': 'stage2-live7-blind-review/1',
        'reviewer_kind': 'same_model_two_phase_report_only_shadow',
        'model': 'deepseek-flash',
        'limitation': 'Not an independent human gold standard; same model family evaluates generation. Shadow phase is blind to machine outputs; comparison phase uses the shadow and artifacts.',
        'cases': all_results,
    }, ensure_ascii=False, indent=2) + '\n')

if __name__ == '__main__':
    main()
