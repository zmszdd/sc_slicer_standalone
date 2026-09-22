"""semantic-v3.18: remove the inherited legacy pattern-kind guidance.

v3.16 fixes one template per relation_class (monotonicity, conservation, and
relation_obligation for every other class), but the formal prompt still carried
text inherited from v3.15 that (a) specified the fields of the legacy
condition_*_effect shapes and (b) told the model to *use* one of them for
"a valid operation should complete but instead reverts" -- which is exactly the
progress_or_liveness scenario the fixed template reserves for relation_obligation.

Measured before this version: the two progress_or_liveness cases emitted the
legacy kind in 7 of 10 formalization samples each (3/10 obeyed), while the three
other classes obeyed 10/10. v3.18 removes the contradiction and nothing else.
"""
import semantic_prompts_v316 as v316


PROMPT_VERSION = 'semantic-v3.18'

# The three regions v3.16 inherited that name the legacy shapes.
_LEGACY_POLARITY = '''For condition_requires_effect, effect is a DESIRED outcome and V makes it false.
For condition_forbids_effect, effect is a FORBIDDEN outcome and V makes it true.
Thus, if the report says a valid operation should complete but instead reverts,
use "condition forbids revert" or "condition requires completion"; NEVER encode
"condition requires revert" as I. Apply the same polarity rule to all domains.'''

_FIXED_POLARITY = '''Every class expresses this polarity through the single kind the program
fixed for it. Never substitute a legacy condition/effect shape of your own. Thus,
if the report says a valid operation should complete but instead reverts, the
progress_or_liveness class MUST keep kind relation_obligation and state the
completion obligation in its relation predicate; NEVER encode "condition requires
revert" as I. Apply the same polarity rule to all domains.'''

_LEGACY_FIELD_SPEC = '''For
condition_forbids_effect and condition_requires_effect, pattern must have
exactly kind, condition, effect; both must be complete predicates. Never
return a kind-only pattern.'''

_FIXED_FIELD_SPEC = '''The
pattern must carry exactly the fields its compiler-fixed kind requires, and every
one of them must be a complete predicate. Never return a kind-only pattern.'''

_LEGACY_AUDIT_MENTION = '''monotonicity uses the monotonicity pattern; never use condition_forbids_effect for
   state_correspondence merely to describe desired event fields.'''

_FIXED_AUDIT_MENTION = '''monotonicity uses the monotonicity pattern. Never bend a class's fixed kind merely to
   fit the prose of a desired event field.'''

FORMAL_PLAN_PROMPT = (v316.FORMAL_PLAN_PROMPT
                      .replace(_LEGACY_POLARITY, _FIXED_POLARITY)
                      .replace(_LEGACY_FIELD_SPEC, _FIXED_FIELD_SPEC)
                      .replace(_LEGACY_AUDIT_MENTION, _FIXED_AUDIT_MENTION))
ID_FORMAL_PROMPT = FORMAL_PLAN_PROMPT
FORMAL_PROMPT = FORMAL_PLAN_PROMPT
CORE_SCOPE = v316.CORE_SCOPE
FULL_SCOPE = CORE_SCOPE

ID_ELEMENT_PROMPT = v316.ID_ELEMENT_PROMPT.replace('semantic-v3.16', PROMPT_VERSION)
ELEMENT_PROMPT = v316.ELEMENT_PROMPT.replace('semantic-v3.16', PROMPT_VERSION)


def formal_prompt(evidence_mode, scope):
    if evidence_mode != 'ids' or scope != 'core':
        raise ValueError('semantic-v3.18 supports ID/core mode only')
    return FORMAL_PLAN_PROMPT.removesuffix('DATA:\n') + CORE_SCOPE + '\nDATA:\n'
