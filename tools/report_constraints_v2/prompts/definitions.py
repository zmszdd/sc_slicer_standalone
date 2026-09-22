"""Canonical P/I/V terminology for the active stage-2 prompt contract.

This module is deliberately independent from the frozen prompt versions.  It is
the short, human-readable source of truth for what P, I and V mean.  Historical
files under ``prompts/versions`` remain byte-for-byte reproducible.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class PropertyDefinition:
    symbol: str
    name: str
    meaning: str
    includes: tuple[str, ...]
    excludes: tuple[str, ...]
    formal_role: str


P = PropertyDefinition(
    symbol='P',
    name='Preconditions',
    meaning=(
        'Report-supported scenario facts that hold before the checked action or '
        'state transition and delimit when the reported violation is claimed.'
    ),
    includes=(
        'actor or authorization state',
        'relevant prior protocol state',
        'input, asset, value, time, order, or bound conditions',
    ),
    excludes=(
        'the checked action itself',
        'implementation root cause',
        'desired safety behavior',
        'vulnerable return, revert, post-state, mismatch, loss, or downstream effect',
    ),
    formal_role='A conjunction of report-grounded predicates that is evaluated before V.',
)

I = PropertyDefinition(
    symbol='I',
    name='Report-claimed safety property',
    meaning=(
        'The narrowest report-supported property that should hold in the stated '
        'scope when its applicability condition is met.'
    ),
    includes=(
        'authorization, bound, value, state-correspondence, conservation, monotonicity, '
        'ordering, temporal, integrity, or progress relations',
        'an explicit applicability condition and desired observable relation when needed',
    ),
    excludes=(
        'a system-wide slogan not supported by the report',
        'the implementation root cause',
        'the vulnerable behavior presented as desired behavior',
    ),
    formal_role='Usually condition implies desired_relation; specialized typed templates are allowed.',
)

V = PropertyDefinition(
    symbol='V',
    name='Direct violation witness',
    meaning=(
        'A report-supported, directly observable behavior, return, or state/value '
        'change that occurs in the claimed scenario and is presented as undesired. '
        'It is defined independently of I: that V contradicts I is an obligation to '
        'be established by the P AND V AND I check, not a definitional assumption.'
    ),
    includes=(
        'unauthorized completion or state change',
        'forbidden success or failure',
        'out-of-bound value or incorrect before/after relation',
        'a direct mismatch between expected and observed behavior',
    ),
    excludes=(
        'implementation root cause by itself',
        'generic severity',
        'downstream profit, loss, or denial that is a consequence rather than the '
        'protected relation itself',
    ),
    formal_role='A constructive witness of not-I, commonly condition AND NOT desired_relation.',
)

PIV_DEFINITIONS = (P, I, V)


def render_definitions() -> str:
    """Render the canonical contract for humans; this never calls a model."""
    blocks = []
    for item in PIV_DEFINITIONS:
        blocks.append(
            f'{item.symbol} — {item.name}\n'
            f'Definition: {item.meaning}\n'
            f'Includes: {"; ".join(item.includes)}.\n'
            f'Excludes: {"; ".join(item.excludes)}.\n'
            f'Formal role: {item.formal_role}'
        )
    return '\n\n'.join(blocks) + '\n'


# The active prompt resolver checks these phrases in the resolved production
# prompt.  This guards against accidentally selecting a prompt that has a schema
# but has lost the semantic distinction between P, I and V.
ELEMENT_CONTRACT_MARKERS = (
    'P contains report-supported input/state conditions that exist before the result.',
    'I intent is the narrow behavior that SHOULD hold',
    'V is the direct observable result that contradicts that intent',
)

FORMAL_CONTRACT_MARKERS = (
    'Select actual BEFORE conditions for P',
    'vulnerable outcome as the desired',
)
