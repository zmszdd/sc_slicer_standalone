"""semantic-v3.15: classified safety relations and richer deterministic synthesis."""

import semantic_prompts_v314 as v314


PROMPT_VERSION = 'semantic-v3.15'

_ELEMENT_CARDINALITY = '''A report may contain several direct effects of one root
cause. Include one to four direct impact statements when supported. Keep secondary
economic consequences separate from the direct state, value, or execution effects.
'''
ELEMENT_PROMPT = v314.ELEMENT_PROMPT.replace(
    'semantic-v3.14', PROMPT_VERSION).replace(
    'Include exactly one security_intent and one or two direct\nimpact statements',
    'Include exactly one security_intent and one to four direct\nimpact statements').replace(
    'Return only the requested schema.',
    _ELEMENT_CARDINALITY + 'Return only the requested schema.')
ID_ELEMENT_PROMPT = v314.ID_ELEMENT_PROMPT.replace(
    'semantic-v3.14', PROMPT_VERSION).replace(
    'Include exactly one security_intent and one or two direct\nimpact statements',
    'Include exactly one security_intent and one to four direct\nimpact statements').replace(
    'Return only the requested schema.',
    _ELEMENT_CARDINALITY + 'Return only the requested schema.')

_OLD_SELECTION = '''Select actual BEFORE conditions for P; do not select implementation causes, results
or security intent as P. Select exactly one security_intent and one or two direct
impact IDs for the core V.'''
_NEW_SELECTION = '''Select actual BEFORE conditions for P; do not select implementation causes, results
or security intent as P. Select exactly one security_intent and exactly one direct
impact ID for this single core claim. Other extracted impacts remain available for
future claims; defer them rather than mixing different relations.'''

_OLD_SINGLE_IMPACT = '''Select exactly one direct
impact for the single core V and defer secondary consequences to limitations.'''
_NEW_SINGLE_IMPACT = '''Select exactly one direct impact for this single core V and
defer all other impacts to limitations. The element layer may preserve up to four
direct impacts, but this plan must formalize one relation at a time.'''

_OLD_PATTERNS = '''Choose exactly one pattern:
1 condition_forbids_effect: condition implies NOT effect; V is condition AND effect.
2 condition_requires_effect: condition implies effect; V is condition AND NOT effect.
3 effect_requires_any_authorization: effect implies OR of authorization_terms; V is
  effect AND no authorization term.
4 state_preservation: trigger implies after_symbol == before_symbol; V is trigger
  AND inequality.'''
_NEW_PATTERNS = '''Choose exactly one relation_class describing the report's safety relation:
access_control | value_relation | bounded_value | monotonicity | conservation |
proportional_fairness | state_correspondence | temporal_validity |
sequence_preservation | data_structure_integrity | progress_or_liveness |
range_capacity.

Then choose one compatible pattern:
1 condition_forbids_effect: condition implies NOT effect; V is condition AND effect.
2 condition_requires_effect: condition implies effect; V is condition AND NOT effect.
3 effect_requires_any_authorization: effect implies OR of authorization_terms; V is
  effect AND no authorization term.
4 state_preservation: trigger implies after_symbol == before_symbol; V is trigger
  AND inequality. This legacy equality pattern is not used by classified v3 plans.
5 relation_obligation: condition implies relation; V is condition AND NOT relation.
  Use for value_relation, bounded_value, proportional_fairness,
  state_correspondence, temporal_validity, sequence/data-structure relations, or
  range_capacity. Object fields: kind, condition, relation.
6 monotonicity: trigger implies after >= before for direction nondecreasing, or
  after <= before for nonincreasing. Object fields: kind, trigger, before_symbol,
  after_symbol, direction.
7 conservation: trigger implies after QEXPR == before QEXPR; V is inequality.
  Object fields: kind, trigger, before, after.

Compatibility is enforced by the program. access_control uses authorization or a
forbidden effect; progress_or_liveness uses requires/forbids; all other classes use
the correspondingly named pattern or relation_obligation as described above.'''

_ALIGNMENT_RULE = '''For the selected pattern, identify its CORE OBSERVABLES:
the effect variables for requires/forbids; effect plus authorization variables for
access control; relation variables for relation_obligation; before/after variables
for monotonicity or conservation. Collectively, those core symbols' source_ids MUST
include intent_id and EVERY selected impact_id. Trigger/condition-only variables do
not count. This proves evidence linkage, not truth. Do not attach unrelated statement
IDs merely to pass the check; if the report does not connect an impact to the selected
relation, defer that impact or return blocking unsupported_relation.

'''

_OLD_QEXPR = '''where QEXPR is {"symbol":INT_SYMBOL}, {"const":INTEGER}, or
{"op":"mul","args":[QEXPR,QEXPR]}.'''
_NEW_QEXPR = '''where QEXPR is {"symbol":INT_SYMBOL}, {"const":INTEGER}, or
{"op":"add"|"sub"|"mul","args":[QEXPR,QEXPR]}. add/sub operands must share
units; multiplication uses the program's derived product units.'''

_EXACT_POWER = '''For an exact report bound written as 2^N or 2^N +/- K, never
convert it to floating point or scientific notation. In a comparison operand use
{"power_of_two":N,"offset":K}, with offset 0 when absent. The program expands it
to an exact integer. Use this encoding only when the report explicitly states that
power expression.

'''

_TYPE_DISCIPLINE = '''Before returning JSON, perform this mechanical type audit:
1. Every symbol referenced anywhere in precondition_terms or pattern MUST be a key
   in symbols. Do not refer to an undeclared convenience or benchmark variable.
2. {"kind":"truth",...} may reference ONLY a symbol declared with sort:"bool".
   For int or address symbols use comparison/relation with an explicit right operand;
   never use an integer or address as a Boolean condition. If the report explicitly
   establishes that an operation/event/state transition occurred, a separate
   sort:"bool" occurrence symbol may encode that trigger; do not reuse one of the
   operation's address or integer values as its occurrence flag.
3. Every selected precondition_id has exactly one precondition_terms entry. If a
   selected fact cannot be represented faithfully, move it to assumptions and do
   not keep it in precondition_ids.
   Never satisfy this requirement with x==x, x!=x, x<=x, x>=x or another
   self-comparison; such a predicate carries no report information.
4. Check that relation_class is compatible with pattern. In particular,
   state_correspondence uses relation_obligation with observable equality/inequality;
   monotonicity uses the monotonicity pattern; never use condition_forbids_effect for
   state_correspondence merely to describe desired event fields.
5. Do not invent an undefined expected/fair/reference quantity. A symbolic quantity
   is allowed only when a selected report statement grounds its meaning and source_ids.
   Otherwise choose a narrower observable relation or return blocking
   unsupported_relation without pretending the missing quantity is defined.
6. When several impacts are available, select the impact that most directly negates
   the chosen intent. Do not select a downstream economic consequence when another
   impact directly states that the forbidden check/state/event occurred.

Two generic binding templates (illustrative names only):
- Validation bypass: if the intent says a forbidden input must be rejected and an
  impact says the check passed, select that check-passed impact. Use a grounded bool
  such as check_passed for the effect and a report-grounded forbidden-input bool or
  comparison for the condition. The safety relation forbids check_passed; do not
  select a later loss merely because it follows the bypass.
- State/event correspondence: use a grounded bool occurrence trigger only when the
  report states the update/emission occurred. Represent stored and emitted fields as
  address/int symbols, and require emitted_field == stored_or_declared_field with
  relation_obligation. Never write truth(address_field). Core emitted/stored symbols'
  source_ids must cite the selected intent and direct mismatch impact where those
  statements jointly define the correspondence.

'''

_OLD_SCHEMA = '''schema_version:"report-formal-plan/2";
precondition_ids:[IDs];intent_id:ID;impact_ids:[IDs];'''
_NEW_SCHEMA = '''schema_version:"report-formal-plan/3";
relation_class:"access_control"|"value_relation"|"bounded_value"|"monotonicity"|
"conservation"|"proportional_fairness"|"state_correspondence"|
"temporal_validity"|"sequence_preservation"|"data_structure_integrity"|
"progress_or_liveness"|"range_capacity";
precondition_ids:[IDs];intent_id:ID;impact_ids:[exactly one ID];'''

FORMAL_PLAN_PROMPT = v314.FORMAL_PLAN_PROMPT.replace(
    'TASK VERSION: semantic-v3.14', 'TASK VERSION: semantic-v3.15').replace(
    _OLD_SELECTION, _NEW_SELECTION).replace(
    _OLD_SINGLE_IMPACT, _NEW_SINGLE_IMPACT).replace(
    _OLD_PATTERNS, _NEW_PATTERNS).replace(
    _OLD_QEXPR, _NEW_QEXPR).replace(
    _OLD_SCHEMA, _NEW_SCHEMA).replace(
    'Return JSON only, exactly:',
    _ALIGNMENT_RULE + _EXACT_POWER + _TYPE_DISCIPLINE +
    'Return JSON only, exactly:')
ID_FORMAL_PROMPT = FORMAL_PLAN_PROMPT
FORMAL_PROMPT = FORMAL_PLAN_PROMPT
CORE_SCOPE = v314.CORE_SCOPE
FULL_SCOPE = CORE_SCOPE


def formal_prompt(evidence_mode, scope):
    if evidence_mode != 'ids' or scope != 'core':
        raise ValueError('semantic-v3.15 supports ID/core mode only')
    return FORMAL_PLAN_PROMPT.removesuffix('DATA:\n') + CORE_SCOPE + '\nDATA:\n'
