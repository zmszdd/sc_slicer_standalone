"""semantic-v3.3: v3.2 plus a deterministic statement-ID vocabulary."""

import semantic_prompts_v32 as v32


PROMPT_VERSION = "semantic-v3.3"

ELEMENT_PROMPT = v32.ELEMENT_PROMPT.replace(
    "TASK VERSION: semantic-v3.2", "TASK VERSION: semantic-v3.3")

ID_RULE = '''DATA includes allowed_statement_ids generated mechanically from the accepted first
step. Copy every property source ID from its matching list only. In particular,
claim impact_ids and every effect_coverage.statement_id MUST be exact members of
allowed_statement_ids.effects. Never invent a descriptive impact label or rename an
ID. Each effect_coverage row has exactly statement_id, status and reason; it has no
impact_id field. Recheck these IDs character-for-character before returning.

'''

FORMAL_PROMPT = v32.FORMAL_PROMPT.replace(
    "TASK VERSION: semantic-v3.2", "TASK VERSION: semantic-v3.3").replace(
        "Return JSON only and exactly:\n", ID_RULE + "Return JSON only and exactly:\n")

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

CORE_SCOPE = v32.CORE_SCOPE
FULL_SCOPE = v32.FULL_SCOPE


def formal_prompt(evidence_mode, scope):
    if evidence_mode not in ("ids", "quotes") or scope not in ("core", "full"):
        raise ValueError("unknown evidence mode or formalization scope")
    prompt = ID_FORMAL_PROMPT if evidence_mode == "ids" else FORMAL_PROMPT
    scope_text = CORE_SCOPE if scope == "core" else FULL_SCOPE
    return prompt.removesuffix("DATA:\n") + scope_text + "\nDATA:\n"
