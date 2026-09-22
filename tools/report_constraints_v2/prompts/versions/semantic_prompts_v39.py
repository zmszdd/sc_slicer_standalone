"""semantic-v3.9: keep hypothetical triggers distinct from witnessed history."""

import semantic_prompts_v38 as v38


PROMPT_VERSION = 'semantic-v3.9'


def _elements(prompt):
    return prompt.replace('TASK VERSION: semantic-v3.8',
                          'TASK VERSION: semantic-v3.9').replace(
        'Return JSON only, exactly:',
        '''P is an antecedent describing a possible report scenario, not proof that
the scenario was observed. An explicit "if/when X, then failure" supports X
as a conditional P. Preserve the conditional reading; do not convert it into
"X already occurred in a real transaction". Conversely, do not add a prior
transaction, historical state transition, actor, or permission that the cited
fragments do not support. If a prior state is needed, cite the report fragments
that actually establish that state or omit the extra claim. Keep distinct
conditions atomic rather than mixing a supported trigger with an unsupported
history claim in one statement.
Return JSON only, exactly:''')


ELEMENT_PROMPT = _elements(v38.ELEMENT_PROMPT)
ID_ELEMENT_PROMPT = _elements(v38.ID_ELEMENT_PROMPT)
FORMAL_PLAN_PROMPT = v38.FORMAL_PLAN_PROMPT.replace(
    'TASK VERSION: semantic-v3.8', 'TASK VERSION: semantic-v3.9')
ID_FORMAL_PROMPT = FORMAL_PLAN_PROMPT
FORMAL_PROMPT = FORMAL_PLAN_PROMPT
CORE_SCOPE = v38.CORE_SCOPE
FULL_SCOPE = CORE_SCOPE


def formal_prompt(evidence_mode, scope):
    if evidence_mode != 'ids' or scope != 'core':
        raise ValueError('semantic-v3.9 supports ID/core mode only')
    return FORMAL_PLAN_PROMPT.removesuffix('DATA:\n') + CORE_SCOPE + '\nDATA:\n'
