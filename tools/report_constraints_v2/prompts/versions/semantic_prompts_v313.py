"""semantic-v3.13: compound qualifiers and report-grounded product relations."""

import semantic_prompts_v312 as v312


PROMPT_VERSION = 'semantic-v3.13'

_ACTION_CHECK = '''Return only the requested schema. Do not add placeholder,
note, explanation, or alternative fields. Complete every required array; do not
emit a partial object. Include exactly one security_intent and one or two direct
impact statements when supported by this already-screened report.
attack_steps MUST contain action IDs only. Never place a
precondition, root_cause, impact, or security_intent ID in attack_steps; those
facts remain in statements but are not execution-step IDs.\n'''

ELEMENT_PROMPT = v312.ELEMENT_PROMPT.replace(
    'semantic-v3.12', PROMPT_VERSION).replace(
    'Return JSON only, exactly:', _ACTION_CHECK + 'Return JSON only, exactly:')
ID_ELEMENT_PROMPT = v312.ID_ELEMENT_PROMPT.replace(
    'semantic-v3.12', PROMPT_VERSION).replace(
    'Return JSON only, exactly:', _ACTION_CHECK + 'Return JSON only, exactly:')

_OLD_PREDICATE_SENTENCE = '''Every condition/effect/authorization/trigger is one truth, comparison, or divisible_by predicate in the format above.
The program constructs implication, negation, conjunction, disjunction and equality.'''

_EXTENDED_PREDICATES = '''Every condition/effect/authorization/trigger is one PREDICATE. A PREDICATE may be
one truth, comparison, or divisible_by predicate in the format above, or a bounded
compound predicate:
{"kind":"all_of","terms":[PREDICATE,PREDICATE,...]}
{"kind":"any_of","terms":[PREDICATE,PREDICATE,...]}
Use 2..4 terms and nesting depth at most 4. Use all_of when the report requires
multiple simultaneous qualifiers such as direct-call context AND available balance;
never drop an explicit authorization, payment, temporal, or call-context qualifier.

For a report-explicit proportional/product comparison, a PREDICATE may instead be:
{"kind":"relation","left":QEXPR,"operator":"eq|ne|lt|le|gt|ge","right":QEXPR}
where QEXPR is {"symbol":INT_SYMBOL}, {"const":INTEGER}, or
{"op":"mul","args":[QEXPR,QEXPR]}. Use this only when the report supplies the
quantities and relationship. Preserve comparison direction. Product units on both
sides must match; do not invent cancellation, division, constants, or a formula from
domain knowledge. Prefer a report-grounded relation over a free Boolean paraphrase.
The program constructs implication, negation, conjunction, disjunction, arithmetic
products and equality.'''

FORMAL_PLAN_PROMPT = v312.FORMAL_PLAN_PROMPT.replace(
    'TASK VERSION: semantic-v3.12', 'TASK VERSION: semantic-v3.13').replace(
    _OLD_PREDICATE_SENTENCE, _EXTENDED_PREDICATES)
ID_FORMAL_PROMPT = FORMAL_PLAN_PROMPT
FORMAL_PROMPT = FORMAL_PLAN_PROMPT
CORE_SCOPE = v312.CORE_SCOPE
FULL_SCOPE = CORE_SCOPE


def formal_prompt(evidence_mode, scope):
    if evidence_mode != 'ids' or scope != 'core':
        raise ValueError('semantic-v3.13 supports ID/core mode only')
    return FORMAL_PLAN_PROMPT.removesuffix('DATA:\n') + CORE_SCOPE + '\nDATA:\n'
