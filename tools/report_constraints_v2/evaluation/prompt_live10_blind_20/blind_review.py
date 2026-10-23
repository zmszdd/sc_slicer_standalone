#!/usr/bin/env python3
"""Report-only shadow plus impact-by-impact review for semantic-live-10."""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STAGE2 = HERE.parents[1]
sys.path.insert(0, str(STAGE2))
for directory in (STAGE2 / 'lib', STAGE2 / 'cli'):
    sys.path.insert(0, str(directory))
from lib.deepseek import extract_deepseek  # noqa: E402

SHADOW_PROMPT = '''You independently analyze this vulnerability report before seeing machine output.
Return JSON only:
{"case_id":"string","core_claim":{"P":"before-action conditions","I":"required property and scope","V":"reported violation"},"distinct_impacts":[{"description":"one distinct report-claimed harmful outcome","evidence_quote":"verbatim fragment","kind":"direct|downstream|mechanism|unclear"}]}
List materially distinct outcomes the report claims. Merge only paraphrases of the same outcome. Keep mechanisms separate from harms and label them mechanism. Preserve stated qualifiers, conditions and causal order. This phase receives only the report; do not infer facts not stated in it.'''

COMPARE_PROMPT = '''You audit a stage-two result using the report, a report-only impact inventory written before machine output was shown, and machine artifacts.
Return JSON only:
{"case_id":"string","impact_inventory":{"rating":"complete|partial|inaccurate","items":[{"shadow_impact":"string","coverage_item_ids":["string"],"claim_ids":["string"],"disposition":"formalized|unformalized|missing|wrong_claim","reason":"string"}],"omissions_or_errors":["string"]},"claim_ratings":[{"claim_id":"string","impact_id":"string","P":{"rating":"pass|partial|fail|not_evaluable","reason":"string"},"I":{"rating":"pass|partial|fail|not_evaluable","reason":"string"},"V":{"rating":"pass|partial|fail|not_evaluable","reason":"string"}}],"overall":"faithful|weakened|unfaithful","main_defect":"string"}

For inventory completeness, every report-claimed harm in the shadow list must have a corresponding coverage row and a unique claim ID. Do not count a mechanism as a harm; a clearly marked downstream harm still needs its own claim or an explicit unformalized disposition. Check whether the formal claim actually expresses its linked impact; an ID link or status label alone is insufficient. `unformalized` with a concrete reason is honest bookkeeping but not completed coverage. For P/I/V, pass means materially faithful to its cited report facts and correctly scoped; partial means a material relation, qualifier or state is weakened; fail means contradiction, invention or critical omission; not_evaluable means no formula was produced. Judge each impact claim separately. Solver success does not establish semantic correctness. Cite concrete report evidence in each reason.'''

def load(path):
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return None

def main():
    all_results=[]
    for run in sorted(p for p in (HERE/'runs').iterdir()
                      if p.is_dir() and (p/'status.json').is_file()):
        case=run.name
        report=(run/'extraction-input.txt').read_text()
        shadow_dir=HERE/'blind-review'/case/'shadow'; shadow_dir.mkdir(parents=True,exist_ok=True)
        shadow=extract_deepseek('REPORT TEXT:\n'+report+'\n',shadow_dir,
                                'deepseek-flash',prompt=SHADOW_PROMPT,proxy='direct')
        shadow['case_id']=case
        (shadow_dir/'shadow.json').write_text(json.dumps(shadow,ensure_ascii=False,indent=2)+'\n')
        elements=load(run/'elements.json')
        formal=load(run/'formalization.json')
        spec=load(run/'stage3-spec.json')
        status=load(run/'status.json')
        payload='\n'.join([
            'REPORT TEXT:\n'+report,
            'REPORT-ONLY SHADOW INVENTORY (created before machine output was shown):\n'+json.dumps(shadow,ensure_ascii=False,indent=2),
            'MACHINE EXTRACTED ELEMENTS:\n'+json.dumps(elements,ensure_ascii=False,indent=2),
            'MACHINE FORMAL CLAIMS:\n'+json.dumps(formal,ensure_ascii=False,indent=2),
            'STAGE3 IMPACT COVERAGE AND CLAIM STATUS:\n'+json.dumps({'report_impact_coverage':spec.get('report_impact_coverage'),'claims':spec.get('claims')},ensure_ascii=False,indent=2),
            'MECHANICAL STATUS (not semantic proof):\n'+json.dumps(status,ensure_ascii=False,indent=2),
        ])
        compare_dir=HERE/'blind-review'/case/'compare'; compare_dir.mkdir(parents=True,exist_ok=True)
        result=extract_deepseek(payload,compare_dir,'deepseek-flash',
                                prompt=COMPARE_PROMPT,proxy='direct')
        result['case_id']=case
        all_results.append(result)
        print(json.dumps({'case_id':case,'inventory':(result.get('impact_inventory') or {}).get('rating'),
                          'claims':len(result.get('claim_ratings',[])),'overall':result.get('overall')},ensure_ascii=False),flush=True)
    (HERE/'BLIND_REVIEW.json').write_text(json.dumps({
        'schema_version':'stage2-live10-blind20-review/1',
        'reviewer_kind':'same_model_two_phase_report_only_shadow',
        'model':'deepseek-flash',
        'limitation':'The reviewer is the same model family as generation, not an independent human gold standard. The shadow phase sees report text only before the comparison phase.',
        'cases':all_results,
    },ensure_ascii=False,indent=2)+'\n')

if __name__=='__main__':
    main()
