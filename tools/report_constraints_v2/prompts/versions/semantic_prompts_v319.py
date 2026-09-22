"""semantic-v3.19: make the access-control relation cite the selected impact.

v3.16 fixes one template per relation_class and v3.18 removed the inherited legacy
pattern-kind text.  That left a narrower contradiction in the same class guidance:
for access control it said ``relation`` *is the required authorization*, while the
grounding rule requires every selected impact_id to be cited by a symbol appearing
in ``relation`` (condition-only triggers explicitly do not count).  An authorization
predicate is naturally sourced from preconditions, so both rules cannot hold at once
and the prompt never stated precedence.

Measured before this version (5 cases x 10 formalization samples, schema
report-formal-plan/4): the only plans that passed validation were the ones that BREAK
the class rule by building ``relation`` from the absence of the impact's observable.
``olas_permissionless_sweep`` wrote ``relation = caller_is_authorized`` in 10/10
samples -- never passing once -- and pushed the impact onto a condition-only trigger
in 7 of them; ``panoptic_builder_init`` passed 7/10 by writing
``relation = builder_admin_overwritten == false``.  v3.19 states the precedence and
the recipe, and changes nothing else.
"""
import semantic_prompts_v318 as v318


PROMPT_VERSION = 'semantic-v3.19'

# v3.18 inherited (via v3.16 <- v3.15) class guidance that pinned relation to a
# predicate only preconditions can source.
_LEGACY_ACCESS_CONTROL_RULE = """For access
control, condition is the protected action/effect and relation is the required
authorization."""

_FIXED_ACCESS_CONTROL_RULE = """For access
control, condition is the protected action/effect together with the absent or
bypassed guard. Relation must cite the selected impact on a relation symbol, so
when the impact is a consequence such as a revert, loss, or grief rather than a
missing authorization, relation is the ABSENCE of the impact's own observable
instead of the authorization predicate; an authorization-only relation that
leaves the impact uncited is not acceptable."""

FORMAL_PLAN_PROMPT = v318.FORMAL_PLAN_PROMPT.replace(
    _LEGACY_ACCESS_CONTROL_RULE, _FIXED_ACCESS_CONTROL_RULE)
ID_FORMAL_PROMPT = FORMAL_PLAN_PROMPT
FORMAL_PROMPT = FORMAL_PLAN_PROMPT
CORE_SCOPE = v318.CORE_SCOPE
FULL_SCOPE = CORE_SCOPE
ID_ELEMENT_PROMPT = v318.ID_ELEMENT_PROMPT.replace('semantic-v3.18', PROMPT_VERSION)
ELEMENT_PROMPT = v318.ELEMENT_PROMPT.replace('semantic-v3.18', PROMPT_VERSION)


def formal_prompt(evidence_mode, scope):
    if evidence_mode != 'ids' or scope != 'core':
        raise ValueError('semantic-v3.19 supports ID/core mode only')
    return FORMAL_PLAN_PROMPT.removesuffix('DATA:\n') + CORE_SCOPE + '\nDATA:\n'
