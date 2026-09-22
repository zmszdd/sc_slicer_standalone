"""semantic-v3.12: preserve the report's exception and the direct bad result."""

import semantic_prompts_v311 as v311


PROMPT_VERSION = 'semantic-v3.12'
_INTENT_CHECK = '''For I, state the narrow observable boundary directly falsified by V.
Do not promise full business success when the report only establishes a narrower
failure, and do not merge a suggested repair into the security property.\n'''
ELEMENT_PROMPT = v311.ELEMENT_PROMPT.replace('semantic-v3.11', PROMPT_VERSION).replace(
    'Return JSON only, exactly:', _INTENT_CHECK + 'Return JSON only, exactly:')
ID_ELEMENT_PROMPT = v311.ID_ELEMENT_PROMPT.replace('semantic-v3.11', PROMPT_VERSION).replace(
    'Return JSON only, exactly:', _INTENT_CHECK + 'Return JSON only, exactly:')

_QUALIFIER_CHECK = '''A lawful version of the operation must satisfy I. Preserve
explicit "without", "unless", "only if" and payment/authorization exceptions
in predicates. Do not treat a normal intermediate state as V. If the core
contrast cannot be expressed, set blocking unresolved: unsupported_relation;
do not defer the essential bad result.\n\n'''

FORMAL_PLAN_PROMPT = v311.FORMAL_PLAN_PROMPT.replace(
    'TASK VERSION: semantic-v3.11', 'TASK VERSION: semantic-v3.12').replace(
    'Choose exactly one pattern:', _QUALIFIER_CHECK + 'Choose exactly one pattern:')
ID_FORMAL_PROMPT = FORMAL_PLAN_PROMPT
FORMAL_PROMPT = FORMAL_PLAN_PROMPT
CORE_SCOPE = v311.CORE_SCOPE
FULL_SCOPE = CORE_SCOPE


def formal_prompt(evidence_mode, scope):
    if evidence_mode != 'ids' or scope != 'core':
        raise ValueError('semantic-v3.12 supports ID/core mode only')
    return FORMAL_PLAN_PROMPT.removesuffix('DATA:\n') + CORE_SCOPE + '\nDATA:\n'
