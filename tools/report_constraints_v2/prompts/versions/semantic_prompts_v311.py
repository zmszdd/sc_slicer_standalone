"""semantic-v3.11: v3.10 literal-bound checks plus explicit zero-address identity."""

import semantic_prompts_v310 as v310


PROMPT_VERSION = 'semantic-v3.11'
ELEMENT_PROMPT = v310.ELEMENT_PROMPT.replace(
    'TASK VERSION: semantic-v3.10', 'TASK VERSION: semantic-v3.11')
ID_ELEMENT_PROMPT = v310.ID_ELEMENT_PROMPT.replace(
    'TASK VERSION: semantic-v3.10', 'TASK VERSION: semantic-v3.11')
FORMAL_PLAN_PROMPT = v310.FORMAL_PLAN_PROMPT.replace(
    'TASK VERSION: semantic-v3.10', 'TASK VERSION: semantic-v3.11').replace(
    'P predicates are either:',
    '''When a selected P, I trigger, or direct ownership/recipient V explicitly
mentions address(0)/zero address, express the relation with address symbols:
declare zero_address (sort:address, unit:null, meaning:"address(0)") and an
observable address-valued symbol such as recipient or owner_after, then use
{"kind":"comparison","left":ADDRESS_SYMBOL,"operator":"eq" or "ne",
"right":{"symbol":"zero_address"}}. Do not replace address equality with
an undefined Boolean like transfer_to_zero or ownership_zero. Use eq for the
zero-address scenario and ne only when the report explicitly requires nonzero.
This is a report-level identity constraint; runtime binding is deferred.
P predicates are either:''')
ID_FORMAL_PROMPT = FORMAL_PLAN_PROMPT
FORMAL_PROMPT = FORMAL_PLAN_PROMPT
CORE_SCOPE = v310.CORE_SCOPE
FULL_SCOPE = CORE_SCOPE


def formal_prompt(evidence_mode, scope):
    if evidence_mode != 'ids' or scope != 'core':
        raise ValueError('semantic-v3.11 supports ID/core mode only')
    return FORMAL_PLAN_PROMPT.removesuffix('DATA:\n') + CORE_SCOPE + '\nDATA:\n'
