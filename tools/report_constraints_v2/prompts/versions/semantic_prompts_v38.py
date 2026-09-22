"""semantic-v3.8: conservative evidence grounding and fixed-divisor arithmetic."""

import semantic_prompts_v37 as v37


PROMPT_VERSION = 'semantic-v3.8'

ELEMENT_PROMPT = v37.ELEMENT_PROMPT.replace(
    'TASK VERSION: semantic-v3.7', 'TASK VERSION: semantic-v3.8').replace(
    '"Anyone can call" supports an\nunauthorized-caller condition.',
    '''Only an EXPLICIT report statement that anyone can call supports an
unauthorized-caller condition; do not infer this from a function name.''').replace(
    'Return JSON only, exactly:',
    '''Before output, audit EACH precondition against its own cited fragments.
For EACH precondition, check whether its cited fragments actually entail every
actor, permission, state, time, quantity and direction in its text. A valid ID
alone is not support. Omit unsupported qualifiers, especially "anyone",
"unauthorized", or permissionlessness unless the report says so. A documentation
requirement describes what SHOULD hold; it is not a fact that the submitted input
already satisfies that requirement. If no supported actual trigger is available,
leave it out and explain the gap in ambiguities.
Return JSON only, exactly:''')
ID_ELEMENT_PROMPT = v37.ID_ELEMENT_PROMPT.replace(
    'TASK VERSION: semantic-v3.7', 'TASK VERSION: semantic-v3.8').replace(
    '"Anyone can call" supports an\nunauthorized-caller condition.',
    '''Only an EXPLICIT report statement that anyone can call supports an
unauthorized-caller condition; do not infer this from a function name.''').replace(
    'Return JSON only, exactly:',
    '''Before output, audit EACH precondition against its own cited fragments.
For EACH precondition, check whether its cited fragments actually entail every
actor, permission, state, time, quantity and direction in its text. A valid ID
alone is not support. Omit unsupported qualifiers, especially "anyone",
"unauthorized", or permissionlessness unless the report says so. A documentation
requirement describes what SHOULD hold; it is not a fact that the submitted input
already satisfies that requirement. If no supported actual trigger is available,
leave it out and explain the gap in ambiguities.
Return JSON only, exactly:''')

FORMAL_PLAN_PROMPT = v37.FORMAL_PLAN_PROMPT.replace(
    'TASK VERSION: semantic-v3.7', 'TASK VERSION: semantic-v3.8').replace(
    'P predicates are either:',
    '''Do not put a documentation requirement or desired behavior in actual P.
If the report gives a positive fixed integer divisor (including an unambiguous
time-unit conversion), express divisibility with
{"kind":"divisible_by","dividend":INT_SYMBOL,"divisor":POSITIVE_INTEGER,
"value":true_or_false}. This means dividend % divisor == 0 when value is true,
or != 0 when false. The dividend unit must match the divisor's report unit.
Use it for a report-supported numeric relation; do not replace a known relation
with an undefined Boolean flag. If no supported positive divisor is known,
record unsupported_relation as blocking and do not invent a numeric constant.
Every int symbol needs a nonempty unit string; use "dimensionless" for unitless
encoded numeric values. Only bool/address symbols use unit:null.
Symbol keys must be lowercase snake_case, never raw uppercase constants.
The pattern object itself must start with "kind"; never wrap it in another
"pattern" object.

P predicates are either:''').replace(
    'Every condition/effect/authorization/trigger is one predicate in the format above.',
    'Every condition/effect/authorization/trigger is one truth, comparison, or divisible_by predicate in the format above.')

ID_FORMAL_PROMPT = FORMAL_PLAN_PROMPT
FORMAL_PROMPT = FORMAL_PLAN_PROMPT
CORE_SCOPE = v37.CORE_SCOPE
FULL_SCOPE = CORE_SCOPE


def formal_prompt(evidence_mode, scope):
    if evidence_mode != 'ids' or scope != 'core':
        raise ValueError('semantic-v3.8 supports ID/core mode only')
    return FORMAL_PLAN_PROMPT.removesuffix('DATA:\n') + CORE_SCOPE + '\nDATA:\n'
