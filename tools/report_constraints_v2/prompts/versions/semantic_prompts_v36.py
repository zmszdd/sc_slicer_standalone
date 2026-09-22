"""semantic-v3.6: v3.5 plan synthesis with stricter P-plan consistency."""

import semantic_prompts_v35 as v35


PROMPT_VERSION = 'semantic-v3.6'

ELEMENT_PROMPT = v35.ELEMENT_PROMPT.replace(
    'TASK VERSION: semantic-v3.5', 'TASK VERSION: semantic-v3.6')
ID_ELEMENT_PROMPT = v35.ID_ELEMENT_PROMPT.replace(
    'TASK VERSION: semantic-v3.5', 'TASK VERSION: semantic-v3.6')

FORMAL_PLAN_PROMPT = v35.FORMAL_PLAN_PROMPT.replace(
    'TASK VERSION: semantic-v3.5', 'TASK VERSION: semantic-v3.6').replace(
    'P predicates are either:',
    '''precondition_terms must contain exactly one entry for every precondition_ids ID,
and no other entries. Every source_id in precondition_terms must therefore be copied
from precondition_ids; never use a security_intent, impact, action or root_cause ID
as a P-term source. Select only preconditions that can be represented by the predicate
grammar below; put other contextual facts in assumptions. Select exactly one direct
impact for the single core V and defer secondary consequences to limitations.

P predicates are either:''')

ID_FORMAL_PROMPT = FORMAL_PLAN_PROMPT
FORMAL_PROMPT = FORMAL_PLAN_PROMPT
CORE_SCOPE = v35.CORE_SCOPE
FULL_SCOPE = CORE_SCOPE


def formal_prompt(evidence_mode, scope):
    if evidence_mode != 'ids' or scope != 'core':
        raise ValueError('semantic-v3.6 supports ID/core mode only')
    return FORMAL_PLAN_PROMPT.removesuffix('DATA:\n') + CORE_SCOPE + '\nDATA:\n'
