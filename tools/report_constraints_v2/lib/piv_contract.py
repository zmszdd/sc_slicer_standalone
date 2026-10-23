"""Shared machine and prompt contract for report-grounded P/I/V claims."""

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
        'state transition and delimit when the reported violation is claimed.'),
    includes=(
        'actor or authorization state',
        'relevant prior protocol state',
        'input, asset, value, time, order, or bound conditions'),
    excludes=(
        'the checked action itself', 'implementation root cause',
        'desired safety behavior',
        'vulnerable return, revert, post-state, mismatch, loss, or downstream effect'),
    formal_role='A conjunction of report-grounded predicates evaluated before V.',
)

I = PropertyDefinition(
    symbol='I',
    name='Report-claimed safety property',
    meaning=(
        'The narrowest report-supported property that should hold in the stated '
        'scope when its applicability condition is met.'),
    includes=(
        'authorization, bound, value, state-correspondence, conservation, '
        'monotonicity, ordering, temporal, integrity, or progress relations',
        'an explicit applicability condition and desired observable relation when needed'),
    excludes=(
        'a system-wide slogan not supported by the report',
        'the implementation root cause',
        'the vulnerable behavior presented as desired behavior'),
    formal_role='Usually applicability_condition implies desired_relation.',
)

V = PropertyDefinition(
    symbol='V',
    name='Direct violation witness',
    meaning=(
        'A report-supported, directly observable behavior, return, or state/value '
        'change claimed for the scenario, defined independently of I. Whether it '
        'violates I must be checked by the P AND V AND I check; that contradiction '
        'is not assumed by the definition of V.'),
    includes=(
        'unauthorized completion or state change',
        'forbidden success or failure',
        'out-of-bound value or incorrect before/after relation',
        'a direct mismatch between expected and observed behavior'),
    excludes=(
        'implementation root cause by itself', 'generic severity',
        'downstream profit, loss, or denial when it is only a consequence'),
    formal_role='A constructive report-grounded witness checked against P and I.',
)

PIV_DEFINITIONS = (P, I, V)
PIV_PROPERTY_BY_SYMBOL = {
    'P': 'preconditions',
    'I': 'safety',
    'V': 'effects',
}
PIV_PROPERTY_NAMES = tuple(PIV_PROPERTY_BY_SYMBOL.values())
PIV_PROPERTY_SOURCE_KINDS = {
    'preconditions': frozenset({'precondition', 'assumption'}),
    'safety': frozenset({'security_intent'}),
    'effects': frozenset({'impact'}),
}

STATE_CHECKPOINT_RULES = (
    'Treat every observable as a value at a named checkpoint, not as a timeless '
    'quantity. When a report describes the same field before and after an action, '
    'use separate symbols such as pending_assets_before_claim and '
    'pending_assets_after_claim, with distinct checkpoint descriptions and '
    'evidence. Never bind two values from different steps to one symbol. Preserve '
    'the reported step order; if a required checkpoint or value cannot be assigned '
    'from the report, leave that impact pending instead of guessing.'
)


def render_definitions() -> str:
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


def render_prompt_contract() -> str:
    """One normative contract shared by both active generation prompts."""
    return (
        'CANONICAL P/I/V CONTRACT\n' + render_definitions() +
        '\nSTATE CHECKPOINT RULE\n' + STATE_CHECKPOINT_RULES + '\n'
    )


def property_source_kinds(property_name):
    """Return the only report statement kinds allowed to ground a P/I/V role."""
    return PIV_PROPERTY_SOURCE_KINDS[property_name]
