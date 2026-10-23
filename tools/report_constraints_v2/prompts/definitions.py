"""Prompt-facing exports of the shared P/I/V contract."""

from lib.piv_contract import (
    I,
    P,
    PIV_DEFINITIONS,
    PropertyDefinition,
    STATE_CHECKPOINT_RULES,
    V,
    render_definitions,
    render_prompt_contract,
)


ELEMENT_CONTRACT_MARKERS = (
    'P contains report-supported input/state conditions that exist before the result.',
    'I intent is the narrow behavior that SHOULD hold',
    'V is the report-stated harmful outcome associated with the target scenario.',
)

FORMAL_CONTRACT_MARKERS = (
    'Select actual BEFORE conditions for P',
    'vulnerable outcome as the desired',
    'STATE CHECKPOINT RULE',
    'use separate symbols such as pending_assets_before_claim and',
)
