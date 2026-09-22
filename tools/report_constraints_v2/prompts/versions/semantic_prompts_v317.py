"""semantic-v3.17: typed deterministic templates and semantic binding guards."""

import semantic_prompts_v316 as v316


PROMPT_VERSION = 'semantic-v3.17'

_EXPANDED_PATTERNS = '''Choose exactly one relation_class describing the report's
safety relation:
access_control | value_relation | bounded_value | monotonicity | conservation |
proportional_fairness | state_correspondence | temporal_validity |
sequence_preservation | data_structure_integrity | progress_or_liveness |
range_capacity.

The program fixes one typed template from relation_class; do NOT substitute another:
- access_control -> authorization_guard with effect and authorization predicates;
- bounded_value or range_capacity -> bounded_relation with condition, value QEXPR,
  operator lt|le|gt|ge, and bound QEXPR;
- monotonicity -> monotonicity with trigger, before_symbol, after_symbol, direction;
- conservation -> conservation with trigger, before QEXPR and after QEXPR;
- proportional_fairness -> proportional_relation with condition, left QEXPR,
  operator eq|le|ge and right QEXPR; cross-multiply instead of dividing;
- state_correspondence -> correspondence with condition, observed_symbol and
  expected_symbol; the compiler enforces equality;
- temporal_validity -> temporal_order with condition, earlier_symbol, later_symbol
  and strict boolean; the compiler enforces earlier < later when strict, else <=;
- sequence_preservation or progress_or_liveness -> required_effect with condition
  and effect predicates;
- value_relation or data_structure_integrity -> relation_obligation with condition
  and relation predicates.

The compiler constructs I and its direct negation witness V. Never encode the
vulnerable outcome as the desired authorization, bound, correspondence, ordering,
completion, or relation.'''

_BINDING_GUARDS = '''Each precondition term is source-local: every symbol used by
that term MUST include that exact source_id in its symbol source_ids. Two distinct
precondition sources MUST NOT reuse an identical predicate. If two sentences really
support one fact, select the clearest source instead of duplicating the predicate.

Preserve report qualifiers on the selected impact. For temporal, threshold, ordering,
or state qualifiers such as after/before/once/until/while, even if, only when, exceeds,
below, above, at least, or at most, add an impact_context_terms entry whose source_id
is that impact, whose qualifier_types is a nonempty subset of
["temporal","threshold","state"], and whose predicate directly encodes all listed
qualifiers. Every symbol in that predicate MUST cite the same impact source. The
compiler conjoins this context to both I's applicability and V. Use [] only when the
selected impact has no such qualifier; never replace a qualifier with an unrelated
generic call Boolean.

Protocol and standard identifiers such as ERC-4337 or EIP-191 are labels, not numeric
bounds. Do not create numeric predicates or constants for the digits in such labels.

'''

FORMAL_PLAN_PROMPT = v316.FORMAL_PLAN_PROMPT.replace(
    'TASK VERSION: semantic-v3.16', 'TASK VERSION: semantic-v3.17').replace(
    v316._FIXED_PATTERNS, _EXPANDED_PATTERNS).replace(
    'schema_version:"report-formal-plan/4";',
    'schema_version:"report-formal-plan/5";').replace(
    'derived_definitions:[{symbol:NAME,expression:QEXPR,source_ids:[IDs]}];\npattern:',
    'derived_definitions:[{symbol:NAME,expression:QEXPR,source_ids:[IDs]}];\n'
    'impact_context_terms:[{source_id:IMPACT_ID,qualifier_types:['
    '"temporal"|"threshold"|"state"],predicate:PREDICATE}];\npattern:').replace(
    'Return JSON only, exactly:',
    _BINDING_GUARDS + 'Return JSON only, exactly:')

ID_ELEMENT_PROMPT = v316.ID_ELEMENT_PROMPT.replace('semantic-v3.16', PROMPT_VERSION)
ELEMENT_PROMPT = v316.ELEMENT_PROMPT.replace('semantic-v3.16', PROMPT_VERSION)
ID_FORMAL_PROMPT = FORMAL_PLAN_PROMPT
FORMAL_PROMPT = FORMAL_PLAN_PROMPT
CORE_SCOPE = v316.CORE_SCOPE
FULL_SCOPE = CORE_SCOPE


def formal_prompt(evidence_mode, scope):
    if evidence_mode != 'ids' or scope != 'core':
        raise ValueError('semantic-v3.17 supports ID/core mode only')
    return FORMAL_PLAN_PROMPT.removesuffix('DATA:\n') + CORE_SCOPE + '\nDATA:\n'
