"""semantic-v3.4: v3.3 plus exact claim/coverage set equality."""

import semantic_prompts_v33 as v33


PROMPT_VERSION = "semantic-v3.4"

ELEMENT_PROMPT = v33.ELEMENT_PROMPT.replace(
    "TASK VERSION: semantic-v3.3", "TASK VERSION: semantic-v3.4")

COVERAGE_RULE = '''For each claim, the set of effect_coverage.statement_id values MUST equal the
set of that claim's impact_ids exactly: one row per claimed impact, no duplicate,
missing or extra row. An unclaimed/deferred impact belongs only in limitations; do
not emit an effect_coverage row for it. Check this set equality before returning.

'''

FORMAL_PROMPT = v33.FORMAL_PROMPT.replace(
    "TASK VERSION: semantic-v3.3", "TASK VERSION: semantic-v3.4").replace(
        "Return JSON only and exactly:\n", COVERAGE_RULE + "Return JSON only and exactly:\n")

ID_ELEMENT_PROMPT = ELEMENT_PROMPT.replace("report-elements/1", "report-elements/2").replace(
    "evidence:[exact contiguous report quotes]", "evidence_ids:[fragment IDs]").replace(
    "evidence:[exact quotes]", "evidence_ids:[fragment IDs]").replace("REPORT:\n", '''
DATA is a numbered prose catalog. Return evidence_ids only, never quotations. Use
only supplied IDs; select multiple IDs only when support spans fragments. REPORT:\n''')

ID_FORMAL_PROMPT = FORMAL_PROMPT.replace("report-formalization/1", "report-formalization/2").replace(
    "evidence:exact_quote", "evidence_ids:[fragment IDs]").replace(
    "evidence:[exact source quotes]", "evidence_ids:[source fragment IDs]").replace("DATA:\n", '''
Return evidence_ids, not quotations. Each property may use only fragment IDs from
its source statements; null properties use evidence_ids:[]. DATA:\n''')

CORE_SCOPE = v33.CORE_SCOPE
FULL_SCOPE = v33.FULL_SCOPE


def formal_prompt(evidence_mode, scope):
    if evidence_mode not in ("ids", "quotes") or scope not in ("core", "full"):
        raise ValueError("unknown evidence mode or formalization scope")
    prompt = ID_FORMAL_PROMPT if evidence_mode == "ids" else FORMAL_PROMPT
    scope_text = CORE_SCOPE if scope == "core" else FULL_SCOPE
    return prompt.removesuffix("DATA:\n") + scope_text + "\nDATA:\n"
