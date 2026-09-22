"""Replay v3.1 consistency artifacts/ratings and error classes; no model calls."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
MODULE=HERE.parents[1]
sys.path.insert(0,str(MODULE))
for _d in (MODULE / 'lib', MODULE / 'cli'):
    _s = str(_d)
    if _s not in sys.path:
        sys.path.insert(0, _s)
import report_only as r
from evidence_catalog import build_catalog,hydrate_elements,hydrate_formalization
from semantic_core import validate_elements,validate_formalization
from verify_semantic import verify

DIMENSIONS=("scope_actors","preconditions","safety_intent","formal_I","core_V","qualifiers_coverage")
VALUES=("pass","partial","fail","not_evaluable")
ERROR_CLASSES=("precondition_incomplete_or_contaminated","obligation_strength_or_scope",
               "v_does_not_force_not_i","modality_upgrade","schema_missing_or_extra","timeout")

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def evaluate():
    frozen=json.loads((HERE/'FROZEN_INPUTS.json').read_text())
    ratings=json.loads((HERE/'ratings.json').read_text())
    manifest=json.loads((HERE/'cases.json').read_text())
    for path,expected in ((HERE/'REFERENCE.md',frozen['reference_sha256']),
                          (HERE/'cases.json',frozen['cases_sha256']),
                          (MODULE/'prompts/versions/semantic_prompts_v31.py',
                           frozen['prompt_sha256'])):
        if sha(path)!=expected: raise ValueError('frozen input changed: '+path.name)
    if ratings['reference_sha256']!=frozen['reference_sha256']: raise ValueError('reference mismatch')
    ids=[x['id'] for x in manifest['cases']]
    reviewed={x['id']:x for x in ratings['cases']}
    if set(reviewed)!=set(ids) or len(reviewed)!=len(ids): raise ValueError('ratings coverage')
    root=MODULE/'results/semantic/prompt_v31_consistency_model_02'
    batch=json.loads((root/'batch-summary.json').read_text())
    results=[]; usage=[]
    for case_id in ids:
        manual=reviewed[case_id]
        if set(manual['ratings'])!=set(DIMENSIONS) or any(v not in VALUES for v in manual['ratings'].values()):
            raise ValueError('invalid rating')
        if not set(manual['error_classes'])<=set(ERROR_CLASSES): raise ValueError('invalid error class')
        directory=root/case_id
        provenance=json.loads((directory/'provenance.json').read_text())
        if provenance.get('prompt_version')!=frozen['prompt_version']: raise ValueError('wrong prompt')
        raw=(directory/'original-report').read_bytes(); text=(directory/'extraction-input.txt').read_text()
        if r.sha(raw)!=provenance['report_sha256'] or r.sha(text.encode())!=provenance['report_input_sha256']:
            raise ValueError('input hash mismatch')
        if text!=r.prose_only(json.loads(raw)['body']): raise ValueError('prose mismatch')
        catalog=json.loads((directory/'evidence-catalog.json').read_text())
        if catalog!=build_catalog(text): raise ValueError('catalog mismatch')
        raw_elements=json.loads((directory/'elements-ids.json').read_text())
        if sha(directory/'neural-elements/model-claim.json')!=manual['elements_candidate_sha256']:
            raise ValueError('elements changed')
        elements=hydrate_elements(raw_elements,catalog,text)
        if elements!=json.loads((directory/'elements.json').read_text()): raise ValueError('elements hydration')
        validate_elements(elements,text)
        raw_formal=json.loads((directory/'formalization-ids.json').read_text())
        if sha(directory/'neural-formalization/model-claim.json')!=manual['formalization_candidate_sha256']:
            raise ValueError('formal changed')
        formal=hydrate_formalization(raw_formal,catalog,text)
        if formal!=json.loads((directory/'formalization.json').read_text()): raise ValueError('formal hydration')
        formal_error=None
        try: validate_formalization(formal,elements,text)
        except ValueError as exc: formal_error=str(exc)
        status=json.loads((directory/'status.json').read_text())
        if status.get('error_type')=='ValueError' and formal_error!=status.get('error'):
            raise ValueError('rejection mismatch')
        replay=None
        if (directory/'constraints.json').exists():
            if formal_error: raise ValueError('invalid candidate reached bundle')
            replay=verify(directory)
        for path in directory.glob('neural-*/model-usage.json'):
            usage.extend(json.loads(path.read_text())['steps'])
        results.append({**manual,'pipeline_status':status,'elements_grounding_replayed':True,
                        'formal_validation_error_replayed':formal_error,'formal_pipeline_replay':replay,
                        'complete_semantic_pass':all(v=='pass' for v in manual['ratings'].values())})
    batch_rows={x['case_id']:x['status'] for x in batch['results']}
    if any(batch_rows[x['id']]!=x['pipeline_status'] for x in results): raise ValueError('batch mismatch')
    counts={d:{v:sum(x['ratings'][d]==v for x in results) for v in VALUES} for d in DIMENSIONS}
    error_counts={name:sum(name in x['error_classes'] for x in results) for name in ERROR_CLASSES}
    extraction_dims=tuple(d for d in DIMENSIONS if d!='formal_I')
    extraction_pass=sum(counts[d]['pass'] for d in extraction_dims)
    return {'schema_version':'prompt-v31-consistency-evaluation/1','prompt_version':frozen['prompt_version'],
            'reviewer':ratings['reviewer'],'reference_status':ratings['reference_status'],
            'distinct_reports':len(ids),'actual_model_invocations':sum(x['pipeline_status']['external_model_invocations'] for x in results),
            'evaluation_model_invocations':0,'metric_counts':counts,'error_class_case_counts':error_counts,
            'preliminary_extraction_strict_pass_cells':extraction_pass,
            'preliminary_extraction_total_cells':len(ids)*len(extraction_dims),
            'preliminary_extraction_strict_pass_percentage':100*extraction_pass/(len(ids)*len(extraction_dims)),
            'preliminary_formal_I_pass_count':counts['formal_I']['pass'],
            'preliminary_formal_I_pass_percentage':100*counts['formal_I']['pass']/len(ids),
            'formal_pipeline_completed_count':sum(x['formal_pipeline_replay'] is not None for x in results),
            'complete_semantic_pass_count':sum(x['complete_semantic_pass'] for x in results),
            'timeout_case_count':sum(x['pipeline_status'].get('error_type')=='TimeoutExpired' for x in results),
            'recorded_usage_file_count':len(usage),'reported_total_tokens':sum(s['tokens']['total'] for s in usage),
            'reported_cost_not_verified_bill':round(sum(s['cost'] for s in usage),8),
            'general_accuracy_percentage':None,
            'limitations':['Five selected findings, not a random population sample.',
                           'Assistant-preliminary reference/grading; not expert-confirmed ground truth.',
                           'Repeated projects/writing styles may correlate errors; recurrence is not independence.',
                           'Different reports prevent strict score comparison with prior batches.',
                           'No code transition T or PoC/report consistency verdict.'],
            'results':results}

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument('--output',type=Path)
    args=parser.parse_args(); rendered=json.dumps(evaluate(),ensure_ascii=False,indent=2)+'\n'
    if args.output:
        with args.output.open('x') as stream: stream.write(rendered)
    print(rendered,end='')
