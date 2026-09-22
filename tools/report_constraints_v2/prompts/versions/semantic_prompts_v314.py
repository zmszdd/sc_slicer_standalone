"""semantic-v3.14: explicit safety/violation polarity discipline."""

import semantic_prompts_v313 as v313


PROMPT_VERSION = 'semantic-v3.14'
_QUANTITATIVE_PRESERVATION = '''When the report gives an equation, proportional
relationship, explicit bound, or expected-versus-actual values, preserve its
operands, operator/direction, and numeric literals in atomic statements. Do not
compress `expected 100, actual 50` or an explicit share formula into only "unfair"
or "under-minted". Keep the narrow quantitative fact even if a broader economic
impact is also extracted.\n'''
ELEMENT_PROMPT = v313.ELEMENT_PROMPT.replace(
    'semantic-v3.13', PROMPT_VERSION).replace(
    'Return only the requested schema.',
    _QUANTITATIVE_PRESERVATION + 'Return only the requested schema.')
ID_ELEMENT_PROMPT = v313.ID_ELEMENT_PROMPT.replace(
    'semantic-v3.13', PROMPT_VERSION).replace(
    'Return only the requested schema.',
    _QUANTITATIVE_PRESERVATION + 'Return only the requested schema.')

_POLARITY_CHECK = '''Use only statement/entity IDs present in DATA everywhere,
including unresolved.source_ids; never emit placeholders such as not_applicable.
For each precondition_terms item, its predicate must encode selected BEFORE facts,
and every predicate symbol must include at least one selected precondition_id in
source_ids. Prefer the same source_id; another selected P is allowed when two P
statements describe the same observable quantity.
Never encode a BEFORE condition as the absence or presence of the later impact.

Before choosing a pattern, perform this polarity check internally:
1. Rewrite the selected security_intent as "under CONDITION, the DESIRED outcome
   must hold" or "under CONDITION, the FORBIDDEN outcome must not hold".
2. The pattern's generated safety formula MUST express that intended sentence,
   never the vulnerable behavior, root cause, or reported bad outcome.
3. The program-generated V MUST describe the selected impact and directly make
   that safety formula false under P.
For condition_requires_effect, effect is a DESIRED outcome and V makes it false.
For condition_forbids_effect, effect is a FORBIDDEN outcome and V makes it true.
Thus, if the report says a valid operation should complete but instead reverts,
use "condition forbids revert" or "condition requires completion"; NEVER encode
"condition requires revert" as I. Apply the same polarity rule to all domains.
If the report does not support a direction-preserving encoding, return a blocking
unsupported_relation item instead of reversing I and V.

'''

FORMAL_PLAN_PROMPT = v313.FORMAL_PLAN_PROMPT.replace(
    'TASK VERSION: semantic-v3.13', 'TASK VERSION: semantic-v3.14').replace(
    'Choose exactly one pattern:', _POLARITY_CHECK + 'Choose exactly one pattern:')
ID_FORMAL_PROMPT = FORMAL_PLAN_PROMPT
FORMAL_PROMPT = FORMAL_PLAN_PROMPT
CORE_SCOPE = v313.CORE_SCOPE
FULL_SCOPE = CORE_SCOPE


def formal_prompt(evidence_mode, scope):
    if evidence_mode != 'ids' or scope != 'core':
        raise ValueError('semantic-v3.14 supports ID/core mode only')
    return FORMAL_PLAN_PROMPT.removesuffix('DATA:\n') + CORE_SCOPE + '\nDATA:\n'
