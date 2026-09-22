"""semantic-v3.16: compiler-selected templates, derived values and local repair."""

import semantic_prompts_v315 as v315


PROMPT_VERSION = 'semantic-v3.16'

_ELEMENT_ROLE_RULE = '''Before assigning statement kinds, separate execution time:
precondition is true before the checked action/transition; root_cause describes the
faulty mechanism; impact is the bad return, revert, post-state, mismatch or loss.
Never duplicate a vulnerable result as a precondition merely because the report
states it as a fact. Preserve a mixed sentence as root_cause/impact and extract a
separate precondition only when the report actually supplies one.
'''
ELEMENT_PROMPT = v315.ELEMENT_PROMPT.replace(
    'semantic-v3.15', PROMPT_VERSION).replace(
    'Return only the requested schema.',
    _ELEMENT_ROLE_RULE + 'Return only the requested schema.')
ID_ELEMENT_PROMPT = v315.ID_ELEMENT_PROMPT.replace(
    'semantic-v3.15', PROMPT_VERSION).replace(
    'Return only the requested schema.',
    _ELEMENT_ROLE_RULE + 'Return only the requested schema.')

_FIXED_PATTERNS = '''Choose exactly one relation_class describing the report's
safety relation:
access_control | value_relation | bounded_value | monotonicity | conservation |
proportional_fairness | state_correspondence | temporal_validity |
sequence_preservation | data_structure_integrity | progress_or_liveness |
range_capacity.

The program fixes the logical template from relation_class; you do NOT choose among
templates:
- monotonicity MUST use kind monotonicity with trigger, before_symbol,
  after_symbol and direction;
- conservation MUST use kind conservation with trigger, before and after;
- every other class MUST use kind relation_obligation with condition and relation.

For relation_obligation, condition states when the desired property applies and
relation states the desired observable relationship. The program constructs
I = condition implies relation and V = condition AND NOT relation. For access
control, condition is the protected action/effect and relation is the required
authorization. For progress/liveness, condition is the valid operation scenario
and relation is successful completion or absence of the forbidden failure. Never
encode the vulnerable outcome as the desired relation.'''

_P_ROLE_RULE = '''P contains only facts true before the checked action or transition.
Do not select or encode the vulnerable return value, revert, corrupted post-state,
misreported value, loss, or other selected impact as P, even when the report also
states it as a factual sentence. Such observations belong to V/root cause. If a
statement mixes a before-condition and an impact, do not select it as P; record the
missing clean condition as unresolved instead.

'''

_DERIVED_RULE = '''Derived integer quantities must be defined, not merely named.
If a referenced symbol's checkpoint starts with "derived", include exactly one
derived_definitions entry for it. Each entry has:
{"symbol":NAME,"expression":QEXPR,"source_ids":[selected statement IDs]}.
QEXPR uses symbol/const/power_of_two or add/sub/mul exactly as specified below.
Examples include expected = underlying + offset, total = principal + fees, or
product = reserve_x * reserve_y. Use only report-supported operands and cite the
statements supporting the equation. A missing equation is blocking
unsupported_relation; never leave an expected/fair/reference symbol unconstrained.

'''

_CLASS_BINDING_RULES = '''Use these class-specific binding rules:
- proportional_fairness: avoid division. Cross-multiply both sides so units match,
  e.g. observed_reward * total_duration <= full_reward * contributed_duration.
- state_correspondence/value_relation: define every expected/reference quantity
  from report operands with derived_definitions.
- progress_or_liveness: condition states the valid execution scenario and relation
  states completion or the forbidden failure being false.
- access_control: condition states the protected effect/action and relation states
  the report-required authorization.
For kind="comparison", left is a NAME string, never {"symbol":NAME}. Use
kind="relation" only when left/right are QEXPR objects. add/sub/mul always have
exactly two args; nest operations for larger expressions.
When the report explicitly states a qualitative condition such as "deviation
exceeds tolerance", "tradeable portion filled", or "caller is unauthorized", a
grounded bool may represent it. Missing numeric operands do not make that Boolean
relation unsupported and MUST NOT create a blocking unresolved item; record a
nonblocking limitation about later code binding instead.
The condition and relation together must be a direct logical restatement of the
selected impact. Preserve qualifiers such as "even when deviation exceeds
tolerance", "after identical swaps", or "only dust remains". Do not replace an LP
value-loss impact with a root-cause Boolean such as reserves_consistent, and do not
replace a qualified validation-bypass impact with a generic function-call Boolean.

'''

_OLD_SCHEMA = '''schema_version:"report-formal-plan/3";
relation_class:"access_control"|"value_relation"|"bounded_value"|"monotonicity"|
"conservation"|"proportional_fairness"|"state_correspondence"|
"temporal_validity"|"sequence_preservation"|"data_structure_integrity"|
"progress_or_liveness"|"range_capacity";
precondition_ids:[IDs];intent_id:ID;impact_ids:[exactly one ID];'''
_NEW_SCHEMA = '''schema_version:"report-formal-plan/4";
relation_class:"access_control"|"value_relation"|"bounded_value"|"monotonicity"|
"conservation"|"proportional_fairness"|"state_correspondence"|
"temporal_validity"|"sequence_preservation"|"data_structure_integrity"|
"progress_or_liveness"|"range_capacity";
precondition_ids:[IDs];intent_id:ID;impact_ids:[exactly one ID];'''

FORMAL_PLAN_PROMPT = v315.FORMAL_PLAN_PROMPT.replace(
    'TASK VERSION: semantic-v3.15', 'TASK VERSION: semantic-v3.16').replace(
    v315._NEW_PATTERNS, _FIXED_PATTERNS).replace(
    _OLD_SCHEMA, _NEW_SCHEMA).replace(
    'Return JSON only, exactly:',
    _P_ROLE_RULE + _DERIVED_RULE + _CLASS_BINDING_RULES +
    'Return JSON only, exactly:').replace(
    'precondition_terms:[{source_id:ID,predicate:PREDICATE}];\npattern:',
    'precondition_terms:[{source_id:ID,predicate:PREDICATE}];\n'
    'derived_definitions:[{symbol:NAME,expression:QEXPR,source_ids:[IDs]}];\npattern:')

ID_FORMAL_PROMPT = FORMAL_PLAN_PROMPT
FORMAL_PROMPT = FORMAL_PLAN_PROMPT
CORE_SCOPE = v315.CORE_SCOPE
FULL_SCOPE = CORE_SCOPE


def formal_prompt(evidence_mode, scope):
    if evidence_mode != 'ids' or scope != 'core':
        raise ValueError('semantic-v3.16 supports ID/core mode only')
    return FORMAL_PLAN_PROMPT.removesuffix('DATA:\n') + CORE_SCOPE + '\nDATA:\n'
