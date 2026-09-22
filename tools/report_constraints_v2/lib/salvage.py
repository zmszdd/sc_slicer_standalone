"""Numeric and zero-address fidelity guards for report formal plans.

Merged from numeric_fidelity.py and address_fidelity.py (2026-09-21); both
were the same layer with the same entry point name.
"""
from decimal import Decimal, InvalidOperation
import re


POWER_OF_TWO = r'2\s*\^\s*\{?\d+\}?(?:\s*[+-]\s*\d+)?'
NUMBER = (r'(?:' + POWER_OF_TWO +
          r'|-?(?:0[xX][0-9a-fA-F]+|(?:\d{1,3}(?:,\d{3})+|\d+)'
          r'(?:\.\d+)?(?:[eE][+-]?\d+)?))')
PLAIN_NUMBER = re.compile(r'(?<![A-Za-z0-9_])' + NUMBER + r'(?![A-Za-z0-9_])')
PROTOCOL_IDENTIFIER = re.compile(
    r'\b(?:ERC|EIP|BIP|BEP|CAIP|SIP|SLIP|TIP)-\d+\b', re.IGNORECASE)
SYMBOLIC = re.compile(r'(?P<op><=|>=|==|!=|<|>)\s*(?P<number>' + NUMBER + r')')
WORDS = re.compile(
    r'\b(?P<op>less than|smaller than|below|under|at most|no more than|'
    r'greater than|more than|above|at least|no less than|equal to)\s+'
    r'(?P<number>' + NUMBER + r')\b', re.IGNORECASE)
OPERATORS = {'<': 'lt', '<=': 'le', '>': 'gt', '>=': 'ge', '==': 'eq', '!=': 'ne',
             'less than': 'lt', 'smaller than': 'lt', 'below': 'lt', 'under': 'lt',
             'at most': 'le', 'no more than': 'le', 'greater than': 'gt',
             'more than': 'gt', 'above': 'gt', 'at least': 'ge',
             'no less than': 'ge', 'equal to': 'eq'}
REVERSED = {'lt': 'gt', 'le': 'ge', 'gt': 'lt', 'ge': 'le', 'eq': 'eq', 'ne': 'ne'}


def number(value):
    if isinstance(value, bool):
        raise ValueError('boolean is not a numeric bound')
    if isinstance(value, str):
        compact = re.sub(r'[\s{},]', '', value)
        power = re.fullmatch(r'2\^(\d+)(?:([+-])(\d+))?', compact)
        if power:
            result = 1 << int(power.group(1))
            if power.group(2):
                delta = int(power.group(3))
                result += delta if power.group(2) == '+' else -delta
            return Decimal(result)
        if compact.lower().startswith(('0x', '-0x')):
            return Decimal(int(compact, 16))
        value = compact
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError('invalid numeric bound') from exc


def explicit_bounds(text):
    found = []
    for pattern in (SYMBOLIC, WORDS):
        for match in pattern.finditer(text):
            found.append((OPERATORS[match.group('op').lower()], number(match.group('number'))))
    return set(found)


def predicate_bound(predicate):
    if not isinstance(predicate, dict):
        return None
    if predicate.get('kind') in ('all_of', 'any_of'):
        bounds = [bound for item in predicate.get('terms', [])
                  if (bound := predicate_bound(item)) is not None]
        return bounds[0] if len(bounds) == 1 else None
    if predicate.get('kind') != 'comparison':
        return None
    left, right = predicate.get('left'), predicate.get('right')
    operator = predicate.get('operator')
    if operator not in REVERSED:
        return None
    if isinstance(right, dict) and isinstance(left, str):
        if set(right) == {'const'}:
            return operator, number(right['const'])
        if set(right) == {'power_of_two', 'offset'}:
            return operator, number(
                f"2^{right['power_of_two']}{right['offset']:+d}")
    if isinstance(left, dict) and set(left) == {'const'} and isinstance(right, str):
        return REVERSED[operator], number(left['const'])
    return None


def explicit_numbers(text, exclude_protocol_identifiers=False):
    """All explicit numeric literals, used only to prevent invented P constants."""
    if exclude_protocol_identifiers:
        text = PROTOCOL_IDENTIFIER.sub(lambda match: ' ' * len(match.group(0)), text)
    return {number(match.group(0)) for match in PLAIN_NUMBER.finditer(text)}


def predicate_constants(predicate):
    if not isinstance(predicate, dict):
        return set()
    found = set()
    if set(predicate) == {'const'} and type(predicate['const']) is int:
        found.add(number(predicate['const']))
    if set(predicate) == {'power_of_two', 'offset'}:
        found.add(number(f"2^{predicate['power_of_two']}{predicate['offset']:+d}"))
    for value in predicate.values():
        if isinstance(value, dict):
            found |= predicate_constants(value)
        elif isinstance(value, list):
            for item in value:
                found |= predicate_constants(item)
    return found


def check_numeric_plan(plan, elements, exclude_protocol_identifiers=False):
    statements = {row['id']: row for row in elements['statements']
                  if row['kind'] in ('precondition', 'assumption')}
    terms = {row['source_id']: row['predicate'] for row in plan['precondition_terms']}
    for source_id, statement in statements.items():
        bounds = explicit_bounds(statement['text'])
        literals = explicit_numbers(
            statement['text'],
            exclude_protocol_identifiers=exclude_protocol_identifiers)
        if not bounds:
            if source_id not in terms:
                if literals:
                    raise ValueError('numeric P source missing from plan')
                continue
            constants = predicate_constants(terms[source_id])
            if literals and constants and not constants <= literals:
                raise ValueError('numeric P literal changed')
            continue
        if source_id not in terms:
            raise ValueError('numeric P source missing from plan')
        bound = predicate_bound(terms[source_id])
        if bound is None:
            raise ValueError('numeric P bound hidden by non-comparison predicate')
        if len(bounds) != 1 or bound not in bounds:
            raise ValueError('numeric P literal or direction changed')


ZERO = re.compile(r'address\s*\(\s*0\s*\)|\bzero[ -]address\b', re.I)
ZERO_INPUT = re.compile(
    r'\b(?:recipient|destination|_to)\b\s*(?:is|=|==|input is|argument is)\s*'
    r'(?:the\s+)?(?:address\s*\(\s*0\s*\)|zero[ -]address)'
    r'|\brecipient\b.{0,80}\b(?:is|equals)\s+(?:the\s+)?'
    r'(?:address\s*\(\s*0\s*\)|zero[ -]address)'
    r'|\bspecifying\s+(?:address\s*\(\s*0\s*\)|zero[ -]address)\s+'
    r'as\s+(?:the\s+)?recipient'
    r'|\btransfer(?:red)?\b.{0,80}\bto\s+'
    r'(?:address\s*\(\s*0\s*\)|zero[ -]address)', re.I | re.S)
OWNER_ZERO = re.compile(
    r'\b(?:owner|ownership|recipient)\b.{0,100}'
    r'(?:address\s*\(\s*0\s*\)|\bzero[ -]address\b)', re.I | re.S)


def zero_relation(predicate, symbols):
    if isinstance(predicate, dict) and predicate.get('kind') in ('all_of', 'any_of'):
        return any(zero_relation(item, symbols) for item in predicate.get('terms', []))
    if not isinstance(predicate, dict) or predicate.get('kind') != 'comparison' or \
            predicate.get('operator') not in ('eq', 'ne'):
        return False
    left, right = predicate.get('left'), predicate.get('right')
    zero = symbols.get('zero_address')
    return (isinstance(left, str) and left != 'zero_address' and
            isinstance(right, dict) and right == {'symbol': 'zero_address'} and
            isinstance(zero, dict) and zero.get('sort') == 'address' and
            ZERO.search(zero.get('meaning', '')) is not None and
            isinstance(symbols.get(left), dict) and symbols[left].get('sort') == 'address')


def check_address_plan(plan, elements):
    statements = {row['id']: row for row in elements['statements']}
    symbols = plan['symbols']
    terms = {row['source_id']: row['predicate'] for row in plan['precondition_terms']}
    for source_id, statement in statements.items():
        if statement['kind'] in ('precondition', 'assumption') and ZERO_INPUT.search(statement['text']):
            if not zero_relation(terms.get(source_id), symbols):
                raise ValueError('zero-address P relation not observable')
    intent = statements[plan['intent_id']]
    pattern = plan['pattern']
    if ZERO.search(intent['text']):
        if not zero_relation(pattern.get('condition'), symbols):
            raise ValueError('zero-address I condition not observable')
    for source_id in plan['impact_ids']:
        if OWNER_ZERO.search(statements[source_id]['text']):
            if not zero_relation(pattern.get('effect'), symbols):
                raise ValueError('zero-address V ownership effect not observable')
