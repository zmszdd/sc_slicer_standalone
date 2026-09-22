"""semantic-v3.10: explicit P numeric-bound fidelity plus v3.9 scenario rules."""

import semantic_prompts_v39 as v39


PROMPT_VERSION = 'semantic-v3.10'
ELEMENT_PROMPT = v39.ELEMENT_PROMPT.replace(
    'TASK VERSION: semantic-v3.9', 'TASK VERSION: semantic-v3.10')
ID_ELEMENT_PROMPT = v39.ID_ELEMENT_PROMPT.replace(
    'TASK VERSION: semantic-v3.9', 'TASK VERSION: semantic-v3.10')
FORMAL_PLAN_PROMPT = v39.FORMAL_PLAN_PROMPT.replace(
    'TASK VERSION: semantic-v3.9', 'TASK VERSION: semantic-v3.10').replace(
    'P predicates are either:',
    '''For every selected P/assumption statement that says x < N, x >= N,
"less than N", "at least N", etc., its OWN precondition_terms predicate must
encode that same numeric literal and comparator direction. A Boolean flag
named after the phrase is not a formalization of the bound. Do not weaken a
threshold to a larger/smaller convenient constant; do not hide a numeric
relation in an ungrounded bool. If several bounds occur in one statement and
one predicate cannot encode them faithfully, do not claim it is formalized.
Include every extracted P/assumption source ID in precondition_terms. For
condition_forbids_effect and condition_requires_effect, pattern must have
exactly kind, condition, effect; both must be complete predicates. Never
return a kind-only pattern.
P predicates are either:''')
ID_FORMAL_PROMPT = FORMAL_PLAN_PROMPT
FORMAL_PROMPT = FORMAL_PLAN_PROMPT
CORE_SCOPE = v39.CORE_SCOPE
FULL_SCOPE = CORE_SCOPE


def formal_prompt(evidence_mode, scope):
    if evidence_mode != 'ids' or scope != 'core':
        raise ValueError('semantic-v3.10 supports ID/core mode only')
    return FORMAL_PLAN_PROMPT.removesuffix('DATA:\n') + CORE_SCOPE + '\nDATA:\n'
