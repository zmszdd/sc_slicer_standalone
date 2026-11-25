"""Deterministic Stage-2 invariant restatement and final contract fallback.

Stage 2 can emit a single symbolic boolean for a report transition, or an
invariant that only observes one post-state snapshot.  Bound literally, those
expressions cannot express the falsifiable before/after relation claimed by the
report.  This module derives only source-report-grounded restatements from
already declared P/I/V symbols, verifies them with the shared formalization
and weak-invariant rules, and returns a final claim contract for Stage 3.

The module never calls a model, invents a symbol, weakens P/I, or changes a
verdict.  A restatement is accepted only when it removes a semantic blocker
without introducing a new one; otherwise the original semantics are preserved.
"""
from __future__ import annotations

import copy
import importlib.util
import json
import re
import sys
from pathlib import Path

from lib import execution_gate
from lib import weak_invariant

SCHEMA_VERSION = 'invariant-restatement/2'
LEGACY_SCHEMA_VERSION = 'stage2-deterministic-restatement/1'

RULES = ('changed', 'unchanged', 'increased', 'decreased', 'drained',
         'succeeds', 'fails', 'reverts', 'blocked', 'completes', 'authorized')
_SUFFIX_RE = re.compile(
    r'(?i)(?:^|[_\s])(' + '|'.join(RULES) + r')$')
_CHECKPOINT_WORDS = {'before', 'after', 'post', 'pre', 'entry', 'completion',
                     'input', 'output', 'initial', 'final', 'conclusion',
                     'execution', 'outcome', 'during', 'at', 'on'}
_STOP_WORDS = _CHECKPOINT_WORDS | {
    'the', 'and', 'for', 'with', 'that', 'this', 'from', 'into', 'must',
    'should', 'call', 'called', 'caller', 'value', 'values', 'state',
    'report', 'reported', 'user', 'users', 'protocol', 'contract',
}
_HASH_PREFIX_RE = re.compile(r'^[0-9a-f]{8,}_', re.I)
_CAMEL_RE = re.compile(r'[A-Z]?[a-z]+|[A-Z]+(?=[A-Z][a-z])|[0-9]+')
_STATE_RULES = {'changed', 'unchanged', 'increased', 'decreased', 'drained'}
_OUTCOME_RULES = {'succeeds', 'fails', 'reverts', 'blocked', 'completes'}
_BEFORE_WORDS = {'before', 'pre', 'prior', 'initial', 'input'}
_AFTER_WORDS = {'after', 'post', 'completion', 'complete', 'conclusion',
                'final', 'outcome', 'settled'}
_STATE_OPS = {
    'changed': 'neq',
    'unchanged': 'eq',
    'increased': 'gt',
    'decreased': 'gt',
    'drained': 'gt',
}
_NUMERIC_OPS = {'lt', 'le', 'gt', 'ge', 'eq', 'neq'}
_OPPOSITE_NUMERIC_OP = {
    'lt': 'ge', 'ge': 'lt', 'le': 'gt', 'gt': 'le',
    'eq': 'neq', 'neq': 'eq',
}
_CONFIG_BOUND_RE = re.compile(
    r'(?i)\b(max|min|limit|bound|cap|threshold|quota|allowed|required|'
    r'target|expected|maximum|minimum)\b')
_ROLE_BEFORE_RE = re.compile(
    r'(?i)\b(intended|expected|configured|reference|original|target|required)\b')
_ROLE_AFTER_RE = re.compile(
    r'(?i)\b(recipient|observed|actual|received|current|final|result)\b')
_RELATION_CUES = (
    ('unchanged', re.compile(
        r'\b(remain\w*|unchanged|preserv\w*|constant|same|intact|'
        r'not\s+(?:be\s+)?(?:changed|altered|modified))\b', re.I)),
    ('changed', re.compile(
        r'\b(change\w*|differ\w*|mutat\w*|updat\w*|vari\w*)\b', re.I)),
    ('increased', re.compile(
        r'\b(increas\w*|ris\w*|grow\w*|greater|above)\b', re.I)),
    ('decreased', re.compile(
        r'\b(decreas\w*|reduc\w*|drain\w*|drop\w*|lower|less)\b', re.I)),
)
_IDENT_L = r'(?<![A-Za-z0-9])'
_IDENT_R = r'(?![A-Za-z0-9])'
_SUCCESS_WORDS = re.compile(
    _IDENT_L + r'(succeed\w*|success\w*|complete\w*|completes|completed|'
    r'proceed\w*)' + _IDENT_R, re.I)
_FAILURE_WORDS = re.compile(
    _IDENT_L + r'(fail\w*|revert\w*|denied|blocked|prevent\w*|stopp\w*)'
    + _IDENT_R, re.I)
_AUTHORIZED_WORDS = re.compile(
    _IDENT_L + r'(authoriz\w*|permitted|privileged)' + _IDENT_R, re.I)
_UNAUTHORIZED_WORDS = re.compile(
    _IDENT_L + r'(unauthoriz\w*|unauthoris\w*|not\s+authoriz\w*|'
    r'non-authoriz\w*)' + _IDENT_R, re.I)
_NUMERIC_SORTS = {'int', 'uint', 'uint256', 'int256', 'uint128', 'int128',
                  'address'}
_AMOUNT_TOKENS = {'balance', 'asset', 'assets', 'fund', 'funds', 'token',
                  'tokens', 'ether', 'shares', 'amount', 'value'}
_SEMANTIC_CODES = {
    'I_SNAPSHOT_ONLY', 'I_SNAPSHOT_BARE_VAR', 'I_CHECKPOINT_COLLAPSED',
    'I_LAYER_MISMATCH', 'EFFECT_NOT_INDEPENDENT', 'I_V_POLARITY_ONLY',
    'I_V_RESTATEMENT', 'I_V_TAUTOLOGY', 'I_COPIED_FROM_P',
    'I_ONLY_REUSES_P',
}
_FORBIDDEN_CODES = {
    'I_TAUTOLOGY', 'V_TAUTOLOGY', 'I_CONTRADICTION', 'V_CONTRADICTION',
    'I_SELF_IMPLICATION', 'I_TRIVIAL_OPERAND', 'I_COPIED_FROM_V',
    'V_COPIED_FROM_I', 'CONSTANT_INVARIANT', 'CONSTANT_EFFECT',
    'CONSTANT_FALSE_PRECONDITION',
}
_RECIPE_BY_RULE = {
    'changed': 'state_before_after',
    'unchanged': 'state_before_after',
    'increased': 'state_before_after',
    'decreased': 'state_before_after',
    'drained': 'state_before_after',
    'succeeds': 'call_outcome',
    'fails': 'call_outcome',
    'reverts': 'call_outcome',
    'blocked': 'call_outcome',
    'completes': 'call_outcome',
    'authorized': 'authorization_context',
    'snapshot': 'state_before_after',
    'layer': 'state_before_after',
}
_FORMALIZATION_AUDIT = None
_REPORT_LIB = (Path(__file__).resolve().parents[2] /
               'report_constraints_v2' / 'lib')


def _formalization_rules():
    """Load the shared Stage-2 audit without shadowing stage3's ``lib``."""
    global _FORMALIZATION_AUDIT
    if _FORMALIZATION_AUDIT is not None:
        return _FORMALIZATION_AUDIT
    if 'lib.piv_contract' not in sys.modules:
        spec = importlib.util.spec_from_file_location(
            'lib.piv_contract', _REPORT_LIB / 'piv_contract.py')
        module = importlib.util.module_from_spec(spec)
        sys.modules['lib.piv_contract'] = module
        spec.loader.exec_module(module)
    name = 'sc_slicer_stage2_formalization_audit'
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(
            name, _REPORT_LIB / 'formalization_audit.py')
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
    _FORMALIZATION_AUDIT = sys.modules[name]
    return _FORMALIZATION_AUDIT


def load_observability(stage2_dir: Path, claim_id: str) -> dict | None:
    path = Path(stage2_dir) / 'observability-contract.json'
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text())
    except (OSError, ValueError):
        return None
    claims = payload.get('claims') or {}
    if isinstance(claims, dict):
        row = claims.get(claim_id)
        return row if isinstance(row, dict) else None
    if isinstance(claims, list):
        return next((row for row in claims if isinstance(row, dict)
                     and row.get('claim_id') == claim_id), None)
    return None


def _tokens(value) -> set[str]:
    text = _HASH_PREFIX_RE.sub('', str(value or ''))
    return {token.lower() for token in _CAMEL_RE.findall(text)
            if len(token) >= 2 and not re.fullmatch(r'[0-9a-f]{8,}', token, re.I)}


def _content_tokens(value) -> set[str]:
    return _tokens(value) - _STOP_WORDS


def _checkpoint_layer(checkpoint) -> str:
    value = str(checkpoint or '').lower()
    before = any(word in value for word in _BEFORE_WORDS)
    after = any(word in value for word in _AFTER_WORDS)
    if before and after:
        first = re.split(r'[\s_\-/,]+', value)[0]
        if first in _BEFORE_WORDS:
            return 'before'
        if first in _AFTER_WORDS:
            return 'after'
        return 'other'
    if before:
        return 'before'
    if after:
        return 'after'
    return 'other'


def _claim(formal: dict, claim_id: str) -> dict | None:
    return next((row for row in (formal or {}).get('claims') or []
                 if isinstance(row, dict) and row.get('id') == claim_id), None)


def _expression(claim: dict | None, role: str):
    if not claim:
        return None
    properties = claim.get('properties') or {}
    return (properties.get(role) or {}).get('expression')


def _vars(node) -> set[str]:
    if not isinstance(node, dict):
        return set()
    if 'var' in node:
        return {str(node['var'])}
    found = set()
    for value in node.values():
        if isinstance(value, dict):
            found |= _vars(value)
        elif isinstance(value, list):
            for item in value:
                found |= _vars(item)
    return found


def _walk(node):
    if not isinstance(node, dict):
        return
    yield node
    for value in node.values():
        if isinstance(value, dict):
            yield from _walk(value)
        elif isinstance(value, list):
            for item in value:
                yield from _walk(item)


def _meta(formal: dict, declaration: dict | None, symbol: str) -> dict:
    result = copy.deepcopy(
        (formal.get('symbols') or {}).get(symbol) or {})
    rows = (((declaration or {}).get('binding_contract') or {})
            .get('symbols') or [])
    row = next((item for item in rows if isinstance(item, dict)
                and item.get('symbol') == symbol), None)
    if row:
        for key, value in row.items():
            if value not in (None, '', []) or key not in result:
                result[key] = copy.deepcopy(value)
    return result


def _sort(meta: dict) -> str:
    return str(meta.get('sort') or '').strip().lower()


def _split_suffix(symbol: str) -> tuple[str, str | None]:
    match = _SUFFIX_RE.search(symbol)
    if not match:
        return symbol, None
    base = re.sub(r'[_\s]+$', '', symbol[:match.start()])
    return base or symbol, match.group(1).lower()


def _symbol_tokens(symbol: str, meta: dict) -> set[str]:
    value = _content_tokens(symbol)
    value |= _content_tokens(meta.get('meaning'))
    for entity in meta.get('entity_ids') or []:
        value |= _content_tokens(entity)
    result = set(value)
    for token in value:
        for prefix in ('un', 'non'):
            if token.startswith(prefix) and len(token) > len(prefix) + 2:
                result.add(token[len(prefix):])
    return result


def _pair_index(symbols: dict, metas: dict[str, dict]) -> list[dict]:
    before: dict[str, set[str]] = {}
    after: dict[str, set[str]] = {}
    for name, meta in metas.items():
        layer = _checkpoint_layer(meta.get('checkpoint'))
        tokens = _content_tokens(_HASH_PREFIX_RE.sub('', name))
        tokens |= {token for token in _content_tokens(meta.get('entity_ids'))
                   if token in _content_tokens(meta.get('meaning'))}
        if not tokens:
            continue
        if layer == 'before':
            before[name] = tokens
        elif layer == 'after':
            after[name] = tokens
    rows = []
    for before_name, before_tokens in before.items():
        for after_name, after_tokens in after.items():
            shared = before_tokens & after_tokens
            if not shared:
                continue
            score = len(shared) / len(before_tokens | after_tokens)
            if score < 0.5:
                continue
            rows.append({'before': before_name, 'after': after_name,
                         'tokens': before_tokens | after_tokens,
                         'score': round(score, 3)})
    role_before: dict[str, set[str]] = {}
    role_after: dict[str, set[str]] = {}
    for name, meta in metas.items():
        text = ' '.join([name,
                         str(meta.get('meaning') or ''),
                         ' '.join(str(item) for item in
                                  (meta.get('entity_ids') or []))])
        tokens = _symbol_tokens(name, meta)
        if not tokens:
            continue
        if _ROLE_BEFORE_RE.search(text):
            role_before[name] = tokens
        if _ROLE_AFTER_RE.search(text):
            role_after[name] = tokens
    for before_name, before_tokens in role_before.items():
        for after_name, after_tokens in role_after.items():
            if before_name == after_name:
                continue
            shared = before_tokens & after_tokens
            before_entities = {
                str(item).lower() for item in
                (metas.get(before_name, {}).get('entity_ids') or [])}
            after_entities = {
                str(item).lower() for item in
                (metas.get(after_name, {}).get('entity_ids') or [])}
            shared_entities = before_entities & after_entities
            if not shared and not shared_entities:
                continue
            score = len(shared) / len(before_tokens | after_tokens)
            if not shared_entities and score < 0.4:
                continue
            rows.append({
                'before': before_name, 'after': after_name,
                'tokens': before_tokens | after_tokens | shared_entities,
                'score': round(score, 3),
                'synthetic': True,
            })
    return sorted(rows, key=lambda row: (
        -row['score'], bool(row.get('synthetic')),
        row['before'], row['after']))


def _pair_for(symbol: str, pair_rows: list[dict],
              metas: dict[str, dict], allowed: set[str],
              rule: str | None = None) -> dict | None:
    base, _ = _split_suffix(symbol)
    desired = _content_tokens(_HASH_PREFIX_RE.sub('', base))
    desired |= _content_tokens(metas.get(symbol, {}).get('meaning'))
    candidates = [row for row in pair_rows
                  if row['before'] != symbol and row['after'] != symbol
                  if row['before'] in allowed and row['after'] in allowed]
    scored = []
    for row in candidates:
        shared = desired & row['tokens']
        union = desired | row['tokens']
        score = len(shared) / len(union) if union else 0.0
        if shared:
            scored.append((round(score, 3), row))
    if not scored:
        if rule == 'drained':
            numeric = [row for row in candidates
                       if all((_sort(metas.get(row[key], {}))
                               in _NUMERIC_SORTS)
                               for key in ('before', 'after'))
                       and row['tokens'] & _AMOUNT_TOKENS]
            if len(numeric) == 1:
                return numeric[0]
        return None
    best_score = max(score for score, _ in scored)
    best = [row for score, row in scored if score == best_score]
    return best[0] if len(best) == 1 else None


def _rule_for(symbol: str, meta: dict) -> tuple[str | None, str]:
    _, suffix = _split_suffix(symbol)
    if suffix in _STATE_RULES | _OUTCOME_RULES | {'authorized'}:
        normalized = {'fails': 'succeeds', 'reverts': 'succeeds',
                      'blocked': 'succeeds', 'completes': 'succeeds'}.get(
                          suffix, suffix)
        return normalized, suffix
    text = ' '.join([symbol] + [str(meta.get(key) or '')
                              for key in ('meaning', 'checkpoint')])
    if _AUTHORIZED_WORDS.search(text) and not _UNAUTHORIZED_WORDS.search(text):
        return 'authorized', 'meaning'
    if _SUCCESS_WORDS.search(text) or _FAILURE_WORDS.search(text):
        return 'succeeds', 'meaning'
    for rule, pattern in _RELATION_CUES:
        if pattern.search(str(meta.get('meaning') or '')):
            return rule, 'meaning'
    return None, 'none'


def _relation_from_meaning(meta: dict) -> str | None:
    meaning = str(meta.get('meaning') or '')
    for rule, pattern in _RELATION_CUES:
        if pattern.search(meaning):
            return rule
    return None


def _relation_expression(rule: str, pair: dict, metas: dict[str, dict],
                         symbol: str) -> tuple[dict | None, str | None]:
    before = pair['before']
    after = pair['after']
    before_meta = metas.get(before, {})
    after_meta = metas.get(after, {})
    if rule not in _STATE_OPS:
        return None, 'unsupported state rule'
    if rule in {'drained', 'increased', 'decreased'}:
        sorts = {_sort(before_meta), _sort(after_meta)}
        if not (sorts & _NUMERIC_SORTS):
            return None, 'numeric transition has non-numeric before/after pair'
    if not pair.get('synthetic') and (
            _checkpoint_layer(before_meta.get('checkpoint')) == 'other' or
            _checkpoint_layer(after_meta.get('checkpoint')) == 'other'):
        return None, 'pair does not have distinct before/after checkpoints'
    first, second = before, after
    if rule == 'increased':
        first, second = after, before
    return {'op': _STATE_OPS[rule], 'args': [
        {'var': first}, {'var': second}]}, None


def _polarities(node, symbol: str) -> set[str]:
    found = set()
    for item in _walk(node):
        if set(item) == {'var'} and item.get('var') == symbol:
            found.add('positive')
        if (item.get('op') == 'not' and len(item.get('args') or []) == 1
                and (item['args'][0] or {}) == {'var': symbol}):
            found.add('negative')
    return found


def _opposite_symbol(symbol: str, rule: str, metas: dict[str, dict],
                     allowed: set[str]) -> str | None:
    base = _content_tokens(_HASH_PREFIX_RE.sub('', symbol))
    if rule == 'succeeds':
        negative = _FAILURE_WORDS
    elif rule == 'fails':
        negative = _SUCCESS_WORDS
    elif rule == 'authorized':
        negative = _UNAUTHORIZED_WORDS
    else:
        return None
    candidates = []
    for name in sorted(allowed):
        if name == symbol:
            continue
        meta = metas.get(name, {})
        if _sort(meta) not in {'bool', ''}:
            continue
        text = ' '.join([name] + [str(meta.get(key) or '')
                                 for key in ('meaning', 'checkpoint')])
        if not negative.search(text):
            continue
        tokens = _symbol_tokens(name, meta)
        overlap = len(base & tokens)
        if not overlap:
            continue
        candidates.append((-overlap, name))
    if not candidates:
        return None
    candidates.sort()
    if len(candidates) > 1 and candidates[0][0] == candidates[1][0]:
        return None
    return candidates[0][1]


def _call_outcome_context(symbol: str, rule: str, i_expr, v_expr,
                          metas: dict[str, dict], allowed: set[str]) -> dict:
    polarities = _polarities(v_expr, symbol)
    independent = bool(_vars(v_expr) - _vars(i_expr))
    witnessed = bool(polarities) and independent
    opposite = _opposite_symbol(symbol, rule, metas, allowed)
    context = {
        'symbol': symbol,
        'rule': rule,
        'expression': {'var': symbol},
        'polarity_in_v': sorted(_polarities(v_expr, symbol)),
        'independent_effect_present': independent,
        'unique_opposite': opposite,
        'witnessed_by_v': witnessed,
    }
    return context


def _node_key(node) -> str:
    return json.dumps(node, sort_keys=True, separators=(',', ':'))


def _numeric_atoms(node) -> list[dict]:
    atoms: list[dict] = []

    def walk(value):
        if not isinstance(value, dict):
            return
        args = value.get('args')
        if (value.get('op') in _NUMERIC_OPS
                and isinstance(args, list) and len(args) == 2
                and all(isinstance(arg, dict) and set(arg) == {'var'}
                        for arg in args)):
            atoms.append(value)
        for child in value.values():
            if isinstance(child, dict):
                walk(child)
            elif isinstance(child, list):
                for item in child:
                    walk(item)

    walk(node)
    return atoms


def _positive_numeric_atoms(node, positive: bool = True) -> list[dict]:
    atoms: list[dict] = []
    if not isinstance(node, dict):
        return atoms
    args = node.get('args') or []
    if node.get('op') == 'not' and len(args) == 1:
        return _positive_numeric_atoms(args[0], not positive)
    if (positive and node.get('op') in _NUMERIC_OPS
            and isinstance(args, list) and len(args) == 2
            and all(isinstance(arg, dict) and set(arg) in ({'var'}, {'const'})
                    for arg in args)):
        atoms.append(node)
    for child in args:
        atoms.extend(_positive_numeric_atoms(child, positive))
    return atoms


def _numeric_operand(arg) -> tuple[str, object] | None:
    if not isinstance(arg, dict):
        return None
    if set(arg) == {'var'}:
        return 'var', str(arg['var'])
    if set(arg) == {'const'}:
        return 'const', arg['const']
    return None


def _opposite_atom(atom: dict) -> dict | None:
    opposite_op = _OPPOSITE_NUMERIC_OP.get(str(atom.get('op')))
    if not opposite_op:
        return None
    return {'op': opposite_op, 'args': copy.deepcopy(atom.get('args') or [])}


def _falsifier_change(falsifier: dict) -> dict:
    return {
        'symbol': '*',
        'rule': falsifier.get('rule', 'v_falsifier'),
        'origin': 'declaration',
        'mode': falsifier.get('mode'),
        'expression': copy.deepcopy(falsifier['expression']),
        'source_symbols': list(falsifier.get('source_symbols') or []),
        'atom': copy.deepcopy(falsifier.get('atom')),
        'witness': falsifier.get('witness'),
        'i_falsifier_hint': copy.deepcopy(falsifier.get('i_falsifier_hint')),
    }


def _numeric_counterexample_restatement(formal: dict, claim_id: str,
                                        declaration: dict | None) -> dict | None:
    """Derive one implication-counterexample from V's numeric violation.

    ``I = (V_atom -> opposite(V_atom))`` stays code/report grounded and gives
    the shared audit an independent polarity witness without copying V or
    merely restating P.  This is the only fallback used for numeric atoms that
    the transition/post-bound rules cannot shape safely.
    """
    claim = _claim(formal, claim_id) or {}
    v_expr = _expression(claim, 'effects')
    p_expr = _expression(claim, 'preconditions')
    p_atoms = {_node_key(atom) for atom in _numeric_atoms(p_expr)}
    symbols = formal.get('symbols') or {}
    metas = {name: _meta(formal, declaration, name) for name in symbols}
    for name in _vars(v_expr):
        metas.setdefault(name, _meta(formal, declaration, name))
    candidates: list[tuple[tuple, dict]] = []
    hint = (declaration or {}).get('i_falsifier_hint') or {}
    for index, atom in enumerate(_positive_numeric_atoms(v_expr)):
        operands = [_numeric_operand(arg) for arg in atom.get('args') or []]
        if any(item is None for item in operands):
            continue
        variables = [value for kind, value in operands if kind == 'var']
        constants = [value for kind, value in operands if kind == 'const']
        if not variables or len(constants) > 1:
            continue
        if not all(_sort(metas.get(name, {})) in _NUMERIC_SORTS
                   for name in variables):
            continue
        opposite = _opposite_atom(atom)
        if opposite is None:
            continue
        if (_node_key(atom) in p_atoms
                or _node_key(opposite) in p_atoms):
            continue
        expression = {'op': 'implies', 'args': [
            copy.deepcopy(atom), opposite]}
        layers = {
            _checkpoint_layer(metas.get(name, {}).get('checkpoint'))
            for name in variables
        }
        bound_names = [
            name for name in variables
            if _is_config_bound(name, metas.get(name, {}))
        ]
        witness = next(
            (name for name in variables if name not in bound_names),
            variables[0])
        if constants:
            mode = 'const_bound'
        elif {'before', 'after'} <= layers:
            mode = 'transition_bound'
        elif layers == {'before', 'other'}:
            mode = 'input_bound'
        else:
            continue
        rank = (-len(bound_names), -len(constants),
                -len(layers), _node_key(expression), index)
        candidates.append((rank, {
            'rule': 'v_counterexample',
            'origin': 'declaration',
            'mode': mode,
            'expression': expression,
            'atom': copy.deepcopy(atom),
            'opposite': opposite,
            'witness': witness,
            'source_symbols': sorted(variables),
            'i_falsifier_hint': copy.deepcopy(hint),
        }))
    if not candidates:
        return None
    candidates.sort(key=lambda row: row[0])
    return candidates[0][1]


def _is_config_bound(name: str, meta: dict) -> bool:
    text = ' '.join([name] + [str(meta.get(key) or '')
                              for key in ('meaning', 'checkpoint')])
    return bool(_CONFIG_BOUND_RE.search(text))


def _v_falsifier_restatement(formal: dict, claim_id: str,
                             declaration: dict | None) -> dict | None:
    """Derive one falsifiable I from V's asserted numeric violation.

    The candidate is not a copy of V: it uses the *opposite* numeric relation
    and keeps the violation witness outside I so the shared audit does not
    collapse the pair.  A before/after transition needs a separate negated
    hazard witness; a post-state bound violation uses the after symbol as the
    witness.  P symbols and report-solved atoms are never reused; ambiguity
    returns ``None``.
    """
    claim = _claim(formal, claim_id) or {}
    p_expr = _expression(claim, 'preconditions')
    i_expr = _expression(claim, 'safety')
    v_expr = _expression(claim, 'effects')
    symbols = formal.get('symbols') or {}
    metas = {name: _meta(formal, declaration, name) for name in symbols}
    for name in _vars(p_expr) | _vars(i_expr) | _vars(v_expr):
        metas.setdefault(name, _meta(formal, declaration, name))
    p_atoms = {_node_key(atom) for atom in _numeric_atoms(p_expr)}
    p_vars = _vars(p_expr)
    candidates: list[dict] = []
    for atom in _positive_numeric_atoms(v_expr):
        key = _node_key(atom)
        if key in p_atoms:
            continue
        if not all(isinstance(arg, dict) and set(arg) == {'var'}
                   for arg in atom.get('args') or []):
            continue
        left, right = (str(arg['var']) for arg in atom['args'])
        atom_vars = {left, right}
        layers = {
            _checkpoint_layer(metas.get(name, {}).get('checkpoint'))
            for name in atom_vars
        }
        if not all(_sort(metas.get(name, {})) in _NUMERIC_SORTS
                   for name in atom_vars):
            continue
        opposite_op = _OPPOSITE_NUMERIC_OP.get(str(atom.get('op')))
        if not opposite_op:
            continue
        opposite = {'op': opposite_op,
                    'args': [copy.deepcopy(arg) for arg in atom['args']]}
        if _node_key(opposite) in p_atoms:
            continue
        witnesses = []
        if {'before', 'after'} <= layers:
            for name in sorted(_vars(v_expr) - atom_vars - p_vars):
                if _sort(metas.get(name, {})) not in {'bool', ''}:
                    continue
                polarities = _polarities(v_expr, name)
                if 'negative' not in polarities:
                    continue
                witnesses.append((0 if name in _vars(i_expr) else 1, name))
            if len(witnesses) != 1:
                continue
            mode = 'transition'
            witness = witnesses[0][1]
            source_symbols = sorted(atom_vars | {witness})
        elif layers == {'after', 'other'}:
            after_names = [
                name for name in atom_vars
                if _checkpoint_layer(metas.get(name, {}).get('checkpoint'))
                == 'after']
            bound_names = [
                name for name in atom_vars
                if _checkpoint_layer(metas.get(name, {}).get('checkpoint'))
                == 'other']
            if len(after_names) != 1 or len(bound_names) != 1:
                continue
            if after_names[0] in p_vars:
                continue
            if not _is_config_bound(
                    bound_names[0], metas.get(bound_names[0], {})):
                continue
            mode = 'post_bound'
            witness = after_names[0]
            source_symbols = sorted(atom_vars)
        else:
            continue
        hint = (declaration or {}).get('i_falsifier_hint') or {}
        candidates.append({
            'rule': 'v_falsifier',
            'origin': 'declaration',
            'mode': mode,
            'expression': opposite,
            'atom': copy.deepcopy(atom),
            'opposite': opposite,
            'witness': witness,
            'source_symbols': source_symbols,
            'i_falsifier_hint': copy.deepcopy(hint),
        })
    unique = {}
    for candidate in candidates:
        unique.setdefault(_node_key(candidate['expression']), candidate)
    return next(iter(unique.values())) if len(unique) == 1 else None


def _replace_invariant(node, replacements: dict[str, dict],
                       protected: set[str]):
    if not isinstance(node, dict):
        return copy.deepcopy(node)
    if node.get('op') == 'implies' and isinstance(node.get('args'), list) \
            and len(node['args']) == 2:
        antecedent, consequent = node['args']
        return {'op': 'implies', 'args': [
            copy.deepcopy(antecedent),
            _replace_invariant(consequent, replacements, protected)]}
    if set(node) == {'var'} and node.get('var') in replacements \
            and node['var'] not in protected:
        return copy.deepcopy(replacements[node['var']])
    result = {}
    for key, value in node.items():
        if isinstance(value, dict):
            result[key] = _replace_invariant(value, replacements, protected)
        elif isinstance(value, list):
            result[key] = [
                _replace_invariant(item, replacements, protected)
                if isinstance(item, dict) else copy.deepcopy(item)
                for item in value]
        else:
            result[key] = copy.deepcopy(value)
    return result


def _codes(contract: dict) -> set[str]:
    result = set()
    for key in ('problems', 'warnings', 'advisories'):
        for row in contract.get(key) or []:
            if isinstance(row, dict) and row.get('code'):
                result.add(str(row['code']))
            elif isinstance(row, str):
                result.add(row)
    return result


def _synthetic_binding(symbols: dict) -> dict:
    return {'bindings': {
        name: {'checkpoint': str(meta.get('checkpoint') or ''),
               'sort': str(meta.get('sort') or '')}
        for name, meta in symbols.items() if isinstance(meta, dict)}}


def _weak_report(formal: dict, claim_id: str, declaration: dict | None) -> dict:
    return weak_invariant.diagnose(
        formal, claim_id, _synthetic_binding(formal.get('symbols') or {}),
        declaration)


def _restated_formal(formal: dict, claim_id: str, safety) -> dict:
    result = copy.deepcopy(formal)
    for claim in result.get('claims') or []:
        if isinstance(claim, dict) and claim.get('id') == claim_id:
            claim.setdefault('properties', {}).setdefault(
                'safety', {})['expression'] = copy.deepcopy(safety)
            break
    return result


def _verify(formal: dict, claim: dict, claim_id: str, candidate_safety,
            declaration: dict | None, observability: dict | None) -> dict:
    rules = _formalization_rules()
    original_audit = rules.audit_claim(
        formal, claim, observability.get(claim_id)
        if isinstance(observability, dict) else None)
    candidate_formal = _restated_formal(formal, claim_id, candidate_safety)
    candidate_claim = _claim(candidate_formal, claim_id) or {}
    candidate_audit = rules.audit_claim(
        candidate_formal, candidate_claim,
        observability.get(claim_id) if isinstance(observability, dict)
        else None)
    original_codes = _codes(original_audit)
    candidate_codes = _codes(candidate_audit)
    original_weak = _weak_report(formal, claim_id, declaration)
    candidate_weak = _weak_report(candidate_formal, claim_id, declaration)
    original_weak_codes = set(original_weak.get('codes') or [])
    candidate_weak_codes = set(candidate_weak.get('codes') or [])
    original_targets = original_codes & _SEMANTIC_CODES
    remaining_targets = candidate_codes & _SEMANTIC_CODES
    new_codes = candidate_codes - original_codes
    weak_blocking = candidate_weak_codes & weak_invariant.BLOCKING_CODES
    original_weak_blocking = original_weak_codes & weak_invariant.BLOCKING_CODES
    reasons = []
    if candidate_codes & _FORBIDDEN_CODES:
        reasons.append('restatement introduces a structural invariant error')
    if new_codes:
        reasons.append('restatement introduces new audit codes: '
                       + ', '.join(sorted(new_codes)))
    if (original_targets or original_weak_blocking) \
            and not remaining_targets < original_targets \
            and not candidate_weak_codes < original_weak_codes:
        reasons.append('restatement does not remove a blocking semantic code')
    if weak_blocking:
        reasons.append('weak-invariant audit still blocks the restated claim')
    return {
        'accepted': not reasons,
        'reasons': reasons,
        'original_codes': sorted(original_codes),
        'restated_codes': sorted(candidate_codes),
        'removed_codes': sorted(original_codes - candidate_codes),
        'new_codes': sorted(new_codes),
        'original_target_codes': sorted(original_targets),
        'remaining_target_codes': sorted(remaining_targets),
        'original_weak_codes': sorted(original_weak_codes),
        'restated_weak_codes': sorted(candidate_weak_codes),
        'audit_rules_version': rules.SCHEMA_VERSION,
        'weak_invariant_rules_version': weak_invariant.SCHEMA_VERSION,
    }


def restate_claim(formal: dict, claim_id: str, *,
                  declaration: dict | None = None,
                  formalization_contract: dict | None = None,
                  observability: dict | None = None) -> dict:
    """Return a verified restatement record for one claim."""
    claim = _claim(formal, claim_id)
    if claim is None:
        return {
            'schema_version': SCHEMA_VERSION,
            'claim_id': claim_id,
            'status': 'claim_missing',
            'original_safety': None,
            'restated_safety': None,
            'original': {'preconditions': None, 'safety': None, 'effects': None},
            'restated': {'preconditions': None, 'safety': None, 'effects': None},
            'changes': [],
            'unresolved': [],
            'requirements': [],
            'before_after_pairs': [],
            'call_outcome': None,
            'authorization_context': None,
            'input_contract': formalization_contract or {},
            'verification': {'accepted': False, 'reasons': ['claim missing']},
        }
    p_expr = _expression(claim, 'preconditions')
    i_expr = _expression(claim, 'safety')
    v_expr = _expression(claim, 'effects')
    symbols = formal.get('symbols') or {}
    metas = {name: _meta(formal, declaration, name) for name in symbols}
    for name in _vars(p_expr) | _vars(i_expr) | _vars(v_expr):
        metas.setdefault(name, _meta(formal, declaration, name))
    allowed = _vars(p_expr) | _vars(i_expr) | _vars(v_expr)
    protected = _vars(p_expr)
    pairs = _pair_index(symbols, metas)
    replacements: dict[str, dict] = {}
    changes = []
    unresolved = []
    call_outcome = None
    authorization_context = None
    falsifier = None

    for symbol in sorted(_vars(i_expr) - protected):
        meta = metas.get(symbol, {})
        rule, origin = _rule_for(symbol, meta)
        pair = _pair_for(symbol, pairs, metas, allowed, rule)
        if rule in _STATE_RULES and pair:
            expression, reason = _relation_expression(
                rule, pair, metas, symbol)
            if expression is None:
                unresolved.append({
                    'symbol': symbol, 'rule': rule, 'origin': origin,
                    'reason': reason, 'route': 'binding_recipe',
                    'required_recipe': _RECIPE_BY_RULE[rule]})
                continue
            replacements[symbol] = expression
            changes.append({
                'symbol': symbol, 'rule': rule, 'origin': origin,
                'expression': copy.deepcopy(expression),
                'before': pair['before'], 'after': pair['after'],
                'source_symbols': sorted(_vars(expression))})
            continue
        if rule in _STATE_RULES:
            unresolved.append({
                'symbol': symbol, 'rule': rule, 'origin': origin,
                'reason': 'no unique before/after symbol pair',
                'route': 'binding_recipe',
                'required_recipe': _RECIPE_BY_RULE[rule]})
            continue
        if rule in _OUTCOME_RULES:
            outcome_role = (
                'succeeds' if origin in {'succeeds', 'completes'}
                else 'fails')
            opposite = _opposite_symbol(symbol, outcome_role, metas, allowed)
            if opposite:
                expression = {'op': 'not', 'args': [{'var': opposite}]}
                replacements[symbol] = expression
                changes.append({
                    'symbol': symbol, 'rule': outcome_role, 'origin': origin,
                    'expression': expression,
                    'source_symbols': sorted(_vars(expression))})
                continue
            context = _call_outcome_context(
                symbol, outcome_role, i_expr, v_expr, metas, allowed)
            call_outcome = call_outcome or context
            if not context['witnessed_by_v']:
                unresolved.append({
                    'symbol': symbol, 'rule': outcome_role, 'origin': origin,
                    'reason': 'no unique call outcome or V witness',
                    'route': 'binding_recipe',
                    'required_recipe': 'call_outcome'})
            continue
        if rule == 'authorized':
            opposite = _opposite_symbol(symbol, 'authorized', metas, allowed)
            if opposite:
                expression = {'op': 'not', 'args': [{'var': opposite}]}
                replacements[symbol] = expression
                changes.append({
                    'symbol': symbol, 'rule': 'authorized', 'origin': origin,
                    'expression': expression,
                    'source_symbols': sorted(_vars(expression))})
                continue
            context = _call_outcome_context(
                symbol, 'authorized', i_expr, v_expr, metas, allowed)
            authorization_context = context
            if not context['witnessed_by_v']:
                unresolved.append({
                    'symbol': symbol, 'rule': 'authorized', 'origin': origin,
                    'reason': ('authorization requires a unique opposite '
                               'authorization observable or a V witness'),
                    'route': 'binding_recipe',
                    'required_recipe': 'authorization_context'})
            continue
        snapshot_rule = _relation_from_meaning(meta)
        if pair and snapshot_rule:
            expression, reason = _relation_expression(
                snapshot_rule, pair, metas, symbol)
            if expression is not None:
                replacements[symbol] = expression
                changes.append({
                    'symbol': symbol, 'rule': snapshot_rule,
                    'origin': 'snapshot', 'expression': expression,
                    'before': pair['before'], 'after': pair['after'],
                    'source_symbols': sorted(_vars(expression))})
                continue
            unresolved.append({
                'symbol': symbol, 'rule': snapshot_rule,
                'origin': 'snapshot', 'reason': reason,
                'route': 'binding_recipe',
                'required_recipe': _RECIPE_BY_RULE[snapshot_rule]})
            continue
        if formalization_contract:
            codes = _codes(formalization_contract)
            if codes & {'I_LAYER_MISMATCH'}:
                unresolved.append({
                    'symbol': symbol, 'rule': 'layer', 'origin': 'contract',
                    'reason': 'no report-grounded numeric pair for I/V layer',
                    'route': 'binding_recipe',
                    'required_recipe': 'state_before_after'})

    weak_original = _weak_report(formal, claim_id, declaration)
    weak_codes = set(weak_original.get('codes') or [])
    contract_codes = _codes(formalization_contract or {})
    needs_falsifier = bool(
        weak_codes & {'I_LAYER_MISMATCH', 'I_CHECKPOINT_COLLAPSED'}
        or contract_codes & {'I_LAYER_MISMATCH'})
    falsifier_candidates: list[dict] = []
    if needs_falsifier:
        primary = _v_falsifier_restatement(formal, claim_id, declaration)
        if primary:
            falsifier_candidates.append(primary)
        fallback = _numeric_counterexample_restatement(
            formal, claim_id, declaration)
        if fallback and all(
                _node_key(fallback['expression']) != _node_key(row['expression'])
                for row in falsifier_candidates):
            falsifier_candidates.append(fallback)
        falsifier = falsifier_candidates[0] if falsifier_candidates else None
        if falsifier:
            changes.append(_falsifier_change(falsifier))
    if falsifier:
        candidate_safety = copy.deepcopy(falsifier['expression'])
    elif replacements:
        candidate_safety = _replace_invariant(
            i_expr, replacements, protected)
    else:
        candidate_safety = copy.deepcopy(i_expr)
    verification = _verify(
        formal, claim, claim_id, candidate_safety, declaration, observability)
    if not verification['accepted'] and len(falsifier_candidates) > 1:
        for alternative in falsifier_candidates[1:]:
            alternative_safety = copy.deepcopy(alternative['expression'])
            alternative_verification = _verify(
                formal, claim, claim_id, alternative_safety, declaration,
                observability)
            if not alternative_verification['accepted']:
                continue
            falsifier = alternative
            candidate_safety = alternative_safety
            verification = alternative_verification
            changes = [
                row for row in changes
                if row.get('rule') not in {'v_falsifier', 'v_counterexample'}]
            changes.append(_falsifier_change(falsifier))
            break
    status = 'unchanged'
    if changes:
        status = ('restated' if verification['accepted'] else 'rejected')
        if not verification['accepted']:
            unresolved.append({
                'symbol': '*', 'rule': 'verification', 'origin': 'audit',
                'reason': '; '.join(verification['reasons']),
                'route': 'stage2_restate',
                'required_recipe': None})
            changes = []
            candidate_safety = i_expr
    return {
        'schema_version': SCHEMA_VERSION,
        'claim_id': claim_id,
        'status': status,
        'original_safety': copy.deepcopy(i_expr),
        'restated_safety': copy.deepcopy(candidate_safety),
        'original': {'preconditions': copy.deepcopy(p_expr),
                     'safety': copy.deepcopy(i_expr),
                     'effects': copy.deepcopy(v_expr)},
        'restated': {'preconditions': copy.deepcopy(p_expr),
                     'safety': copy.deepcopy(candidate_safety),
                     'effects': copy.deepcopy(v_expr)},
        'changes': changes,
        'unresolved': unresolved,
        'requirements': [
            {'symbol': row['symbol'], 'rule': row['rule'],
             'route': row.get('route'),
             'required_recipe': row.get('required_recipe'),
             'required_observables': [row['symbol']]
             if row['symbol'] != '*' else []}
            for row in unresolved],
        'before_after_pairs': [
            {'before': row['before'], 'after': row['after'],
             'score': row['score']}
            for row in pairs],
        'v_falsifier': copy.deepcopy(falsifier),
        'call_outcome': call_outcome,
        'authorization_context': authorization_context,
        'input_contract': copy.deepcopy(formalization_contract or {}),
        'verification': verification,
    }


def apply(formal: dict, restatement: dict) -> dict:
    """Return a copy of ``formal`` with a verified I restatement applied."""
    if restatement.get('status') not in {'restated', 'partial'}:
        return copy.deepcopy(formal)
    result = copy.deepcopy(formal)
    claim_id = restatement.get('claim_id')
    for claim in result.get('claims') or []:
        if isinstance(claim, dict) and claim.get('id') == claim_id:
            safety = claim.setdefault('properties', {}).setdefault(
                'safety', {})
            safety['expression'] = copy.deepcopy(
                restatement.get('restated_safety'))
            safety['deterministic_restatement'] = {
                'schema_version': SCHEMA_VERSION,
                'changes': copy.deepcopy(restatement.get('changes') or []),
                'unresolved': copy.deepcopy(restatement.get('unresolved') or []),
                'verification': copy.deepcopy(
                    restatement.get('verification') or {}),
            }
            break
    return result


def build_final_contract(formal: dict, restatement: dict, *,
                         original_contract: dict | None = None,
                         observability: dict | None = None,
                         declaration: dict | None = None,
                         trusted_label: dict | None = None,
                         binding_feedback: dict | None = None) -> dict:
    """Return the post-restatement claim contract consumed by Stage 3."""
    rules = _formalization_rules()
    claim_id = restatement.get('claim_id')
    claim = _claim(formal, claim_id) or {}
    claim_observability = None
    if isinstance(observability, dict):
        claim_observability = observability.get(claim_id)
    contract = copy.deepcopy(
        rules.audit_claim(formal, claim, claim_observability))
    contract['invariant_restatement'] = {
        'schema_version': SCHEMA_VERSION,
        'status': restatement.get('status'),
        'accepted': bool((restatement.get('verification') or {}).get('accepted')),
        'changes': copy.deepcopy(restatement.get('changes') or []),
        'unresolved': copy.deepcopy(restatement.get('unresolved') or []),
        'verification': copy.deepcopy(restatement.get('verification') or {}),
        'source_contract_claim_id': claim_id,
    }
    contract['contract_source'] = (
        'stage3_restated' if restatement.get('status') == 'restated'
        else 'stage2_original')
    if original_contract:
        original_codes = _codes(original_contract)
        original_route = str(original_contract.get('route') or 'auto_assert')
        original_can_auto = bool(original_contract.get(
            'can_auto_assert',
            original_contract.get('status') == 'ready'
            and original_route == 'auto_assert'))
        accepted = bool((restatement.get('verification') or {}).get('accepted'))
        if not accepted or original_route != 'auto_assert' or not original_can_auto:
            if not accepted or not original_codes <= _SEMANTIC_CODES:
                for key in ('status', 'route', 'can_auto_assert',
                            'auto_assert_allowed', 'checkpoint_missing',
                            'observable_missing'):
                    if key in original_contract:
                        contract[key] = copy.deepcopy(original_contract[key])
                contract['contract_source'] = 'stage2_preserved'
                contract.setdefault('preserved_reasons', []).append(
                    'original non-restatable Stage-2 route is authoritative')
    accepted = bool((restatement.get('verification') or {}).get('accepted'))
    trusted_reject = execution_gate.trusted_rejection(trusted_label)
    if trusted_reject:
        contract['status'] = 'negative_witness'
        contract['route'] = 'negative_witness'
        contract['can_auto_assert'] = False
        contract['auto_assert_allowed'] = False
        contract.setdefault('problems', []).append({
            'code': 'TRUSTED_NEGATIVE_UNRESOLVED',
            'severity': 'advisory',
            'message': trusted_reject['reason'],
        })
        contract['contract_source'] = 'stage2_trusted_review'
        contract['negative_witness_route'] = {
            'eligible': True,
            'code': trusted_reject['code'],
            'impact_class': trusted_reject.get('impact_class'),
            'reason': trusted_reject['reason'],
            'restatement_accepted': accepted,
        }
        contract['trusted_label_review'] = {
            'code': trusted_reject['code'],
            'impact_class': trusted_reject.get('impact_class'),
            'reason': trusted_reject['reason'],
            'restatement_accepted': accepted,
        }
    if binding_feedback:
        from lib import bindability_feedback

        contract = bindability_feedback.apply_to_contract(
            contract, binding_feedback)
    return contract
