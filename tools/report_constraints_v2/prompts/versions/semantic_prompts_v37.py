"""semantic-v3.7: structured unresolved items without symbolic-value false alarms."""

import semantic_prompts_v36 as v36


PROMPT_VERSION = 'semantic-v3.7'

ELEMENT_PROMPT = v36.ELEMENT_PROMPT.replace(
    'TASK VERSION: semantic-v3.6', 'TASK VERSION: semantic-v3.7')
ID_ELEMENT_PROMPT = v36.ID_ELEMENT_PROMPT.replace(
    'TASK VERSION: semantic-v3.6', 'TASK VERSION: semantic-v3.7')

FORMAL_PLAN_PROMPT = v36.FORMAL_PLAN_PROMPT.replace(
    'TASK VERSION: semantic-v3.6', 'TASK VERSION: semantic-v3.7').replace(
    'schema_version:"report-formal-plan/1";',
    'schema_version:"report-formal-plan/2";').replace(
    'assumptions:[strings];unresolved:[strings];limitations:[strings].',
    '''assumptions:[strings];
unresolved:[{category:"missing_report_definition"|"ambiguous_actor"|
"ambiguous_condition"|"missing_unit"|"unsupported_relation"|"missing_checkpoint",
description:string,source_ids:[statement IDs],blocks_formalization:boolean}];
limitations:[strings].''').replace(
    'Use at most 8 symbols, 6 P terms, 4 strings per caveat list. DATA:\n',
    '''Use at most 8 symbols, 6 P terms, 4 assumptions, 4 unresolved items and 4 limitations.
An unresolved item must identify report information genuinely missing or ambiguous for
the selected P/I/V. Concrete values are NOT required for symbolic addresses or integers.
Do not report these as unresolved: symbolic addresses lack concrete constants; a Boolean
outcome lacks a numeric definition; code/PoC binding has not happened; an SMT variable
has no concrete model value. source_ids must point to the affected selected statement(s).
Set blocks_formalization true only when no faithful selected formula can be built without
inventing the missing meaning. Nonblocking clarification may be retained for audit only.
DATA:\n''')

ID_FORMAL_PROMPT = FORMAL_PLAN_PROMPT
FORMAL_PROMPT = FORMAL_PLAN_PROMPT
CORE_SCOPE = v36.CORE_SCOPE
FULL_SCOPE = CORE_SCOPE


def formal_prompt(evidence_mode, scope):
    if evidence_mode != 'ids' or scope != 'core':
        raise ValueError('semantic-v3.7 supports ID/core mode only')
    return FORMAL_PLAN_PROMPT.removesuffix('DATA:\n') + CORE_SCOPE + '\nDATA:\n'
