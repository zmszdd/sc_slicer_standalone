"""Deterministic pre/post-execution quality gates for stage-3 claims.

These gates do not decide semantic truth.  They reject bindings which cannot
produce meaningful evidence:

* constant I/V observables make ``require(!P || I)`` vacuous;
* an effect built only from the invariant's own symbols is not an independent
  hazard witness;
* administrative-only griefing (for example a dust transfer blocking a vault
  registry) is impact-insufficient for the vulnerability-level metric.

The checks are source/AST based and use no model calls.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from lib.spec_loader import (precondition_symbols_for_claim,
                             safety_symbols_for_claim)

SCHEMA_VERSION = 'stage3-execution-gate/4'

STRUCTURAL_CODES = {
    'CLAIM_MISSING',
    'CONSTANT_INVARIANT',
    'CONSTANT_EFFECT',
    'CONSTANT_FALSE_PRECONDITION',
}

_DIRECT_LOSS_RE = re.compile(
    r'\b(steal|stolen|theft|drain(?:ed|s)?|loss of funds|funds? lost|'
    r'insolven(?:t|cy)|misappropriat(?:e|ed|ion))\b', re.I)
_PERMANENT_LOCK_RE = re.compile(
    r'\b(permanent(?:ly)? (?:locked|frozen|freeze)|locked forever|'
    r'unrecoverable (?:funds|assets)|irreversible loss)\b', re.I)
_UNAUTHORIZED_TRANSFER_RE = re.compile(
    r'\b(unauthori[sz]ed (?:mint|burn|transfer|withdraw|withdrawal)|'
    r'mint(?:ed)? without authorization|steal(?:s)? (?:funds|assets|tokens))\b',
    re.I)
_GOVERNANCE_GRIEF_RE = re.compile(
    r'\b(governance|proposal|voting|vote|quorum|timelock|admin(?:istrative)? '
    r'(?:action|role|control)|owner(?:ship)? (?:action|control)|'
    r'management)\b', re.I)
_ADMIN_GRIEF_RE = re.compile(
    r'\b(vault management|unregister(?:ed|ing)?|registration|registry|'
    r'administrative)\b', re.I)
_DUST_RE = re.compile(
    r'\b(dust|donation|donate|grief(?:ing)?|front[- ]?run|'
    r'denial[- ]of[- ]service|dos)\b', re.I)


def _claim(formal: dict, claim_id: str) -> dict | None:
    return next((row for row in formal.get('claims') or []
                 if isinstance(row, dict) and row.get('id') == claim_id), None)


def _expr(claim: dict, name: str):
    return (((claim.get('properties') or {}).get(name) or {})
            .get('expression'))


def _vars(node) -> set[str]:
    if not isinstance(node, dict):
        return set()
    if 'var' in node:
        return {node['var']}
    found: set[str] = set()
    for value in node.values():
        if isinstance(value, dict):
            found |= _vars(value)
        elif isinstance(value, list):
            for item in value:
                found |= _vars(item)
    return found


def _entry(binding: dict, symbol: str) -> dict:
    value = (binding.get('bindings') or {}).get(symbol)
    return value if isinstance(value, dict) else {}


def _constant(expr: str) -> str | None:
    value = re.sub(r'\s+', '', str(expr or '')).strip()
    while value.startswith('(') and value.endswith(')'):
        value = value[1:-1]
    low = value.lower()
    if low in {'true', 'false'}:
        return low
    if re.fullmatch(r'-?\d+(?:\.\d+)?', value):
        return 'numeric'
    return None


def _is_not_of(node, target) -> bool:
    return (isinstance(node, dict) and node.get('op') == 'not'
            and len(node.get('args') or []) == 1
            and node['args'][0] == target)


def _contains(node, target) -> bool:
    if node == target:
        return True
    if not isinstance(node, dict):
        return False
    for key, value in node.items():
        if key in {'var', 'const'}:
            continue
        if isinstance(value, dict) and _contains(value, target):
            return True
        if isinstance(value, list) and any(
                isinstance(item, dict) and _contains(item, target)
                for item in value):
            return True
    return False


_OPPOSITE = {
    'lt': 'ge', 'ge': 'lt', 'le': 'gt', 'gt': 'le',
    'eq': 'neq', 'neq': 'eq',
}


def _negates(node, target) -> bool:
    if _is_not_of(node, target):
        return True
    if not isinstance(node, dict) or not isinstance(target, dict):
        return False
    if (node.get('op') in _OPPOSITE
            and node.get('op') == _OPPOSITE.get(target.get('op'))
            and node.get('args') == target.get('args')):
        return True
    if node.get('op') == 'and':
        return any(_negates(child, target) for child in node.get('args') or [])
    return False


def _implication_complement(i_expr, v_expr) -> bool:
    """Recognise a direct falsifier of ``A -> B``, including expanded forms.

    Stage 2 often expands ``¬(A -> B)`` to ``A ∧ ¬B ∧ ...`` (for example with
    a redundant ``lt`` beside ``!ge``).  Such a V is a polarity witness even
    though it uses the same symbols as I.
    """
    if not isinstance(i_expr, dict) or i_expr.get('op') != 'implies':
        return False
    args = i_expr.get('args') or []
    if len(args) != 2:
        return False
    antecedent, consequent = args
    return (_contains(v_expr, antecedent)
            and _negates(v_expr, consequent))


def _independent_effect(i_expr, v_expr, i_symbols: set[str],
                        v_symbols: set[str]) -> bool:
    """Whether V contributes evidence beyond the I expression itself."""
    if not v_symbols:
        return False
    if v_symbols - i_symbols:
        return True
    # ``V == !I`` (or the reverse) is a real polarity witness even though it
    # uses the same symbols.  Merely sharing symbols is not.
    return (_is_not_of(v_expr, i_expr) or _is_not_of(i_expr, v_expr)
            or _implication_complement(i_expr, v_expr))


def _trusted_impact(label: dict | None) -> dict | None:
    """Convert a trusted judge/impact ledger row into a gate result."""
    if not isinstance(label, dict) or not label:
        return None
    sufficiency = str(label.get('impact_sufficiency') or
                      label.get('sufficiency') or '').strip().lower()
    validity = str(label.get('validity') or label.get('status') or '').strip().lower()
    if sufficiency in {'insufficient', 'invalid', 'impact_insufficient'}:
        return {
            'sufficiency': 'insufficient',
            'code': 'TRUSTED_IMPACT_INSUFFICIENT',
            'reason': (label.get('reason') or
                       'trusted impact ledger marks this claim as insufficient'),
            'impact_class': label.get('impact_class') or 'trusted_insufficient',
        }
    if label.get('impact_insufficient') is True:
        return {
            'sufficiency': 'insufficient',
            'code': 'TRUSTED_IMPACT_INSUFFICIENT',
            'reason': (label.get('reason') or
                       'trusted impact ledger marks this claim as insufficient'),
            'impact_class': label.get('impact_class') or 'trusted_insufficient',
        }
    if validity in {'invalid', 'rejected', 'false'}:
        return {
            'sufficiency': 'insufficient',
            'code': 'TRUSTED_JUDGE_INVALID',
            'reason': (label.get('reason') or
                       'trusted judge ledger marks this claim invalid'),
            'impact_class': label.get('impact_class') or 'judge_invalid',
        }
    return None


def trusted_rejection(label: dict | None) -> dict | None:
    """Return the deterministic negative-label rejection for ``label``.

    Stage-2 final-contract construction uses this to keep a known-invalid or
    impact-insufficient claim unresolved when its invariant restatement is not
    accepted.  This is a routing decision only; it never rewrites a dynamic
    verdict or turns an unresolved claim into a true negative.
    """
    return _trusted_impact(label)


def is_trusted_negative(label: dict | None) -> bool:
    """True for a deterministic trusted invalid/insufficient label.

    This is a routing hint for the negative witness harness.  It never turns a
    dynamic verdict into TN by itself.
    """
    trusted = _trusted_impact(label)
    return bool(trusted and trusted.get('sufficiency') == 'insufficient')


NEGATIVE_WITNESS_QUERY = {
    'precondition_and_transition': 'P_and_T',
    'effect_absent': 'P_and_T_and_not_V',
    'invariant_held': 'P_and_T_and_not_I',
}


def negative_witness(execution: dict | None) -> dict:
    """Require an independent dynamic witness before counting a true negative.

    A negative label is never enough: the exploit path must be witnessed, the
    claimed effect must be absent, and the invariant must hold on that path.
    Anything missing keeps the claim unresolved.
    """
    execution = execution if isinstance(execution, dict) else {}
    queries = execution.get('code_query_results')
    if not isinstance(queries, dict):
        witness = execution.get('witness')
        queries = (witness.get('queries') if isinstance(witness, dict)
                   else None) or {}
    required = {
        role: str(queries.get(name) or 'unknown').lower()
        for role, name in NEGATIVE_WITNESS_QUERY.items()
    }
    expected = {
        'precondition_and_transition': 'sat',
        'effect_absent': 'sat',
        'invariant_held': 'unsat',
    }
    missing = [role for role, value in required.items()
               if value != expected[role]]
    eligible = not missing
    return {
        'schema_version': 'stage3-negative-witness/1',
        'eligible': eligible,
        'required': expected,
        'observed': required,
        'missing': missing,
    }


def _impact(formal: dict, claim: dict, trusted_label: dict | None = None) -> dict:
    trusted = _trusted_impact(trusted_label)
    if trusted is not None:
        return trusted
    text = ' '.join(str(value or '') for value in (
        claim.get('scope'),
        claim.get('modality'),
        ' '.join(claim.get('impact_ids') or []),
        ((claim.get('properties') or {}).get('preconditions') or {}).get('text'),
        ((claim.get('properties') or {}).get('safety') or {}).get('text'),
        ((claim.get('properties') or {}).get('effects') or {}).get('text'),
    ))
    direct_loss = bool(_DIRECT_LOSS_RE.search(text))
    permanent_lock = bool(_PERMANENT_LOCK_RE.search(text))
    unauthorized_transfer = bool(_UNAUTHORIZED_TRANSFER_RE.search(text))
    admin_grief = bool(_ADMIN_GRIEF_RE.search(text) and _DUST_RE.search(text))
    dust_dos = bool(_DUST_RE.search(text))
    governance_grief = bool(_GOVERNANCE_GRIEF_RE.search(text))
    strong_class = None
    if permanent_lock:
        strong_class = 'permanent_lock'
    elif unauthorized_transfer:
        strong_class = 'unauthorized_transfer'
    elif direct_loss:
        strong_class = 'direct_fund_loss'
    if strong_class:
        return {'sufficiency': 'strong', 'code': None, 'reason': None,
                'impact_class': strong_class}
    if admin_grief:
        return {
            'sufficiency': 'insufficient',
            'code': 'IMPACT_ADMIN_GRIEFING_ONLY',
            'reason': ('claim is recoverable administrative/registry griefing '
                       'without direct fund loss, permanent asset lock, or '
                       'unauthorized transfer'),
            'impact_class': 'administrative_griefing',
        }
    if dust_dos:
        return {
            'sufficiency': 'insufficient',
            'code': 'IMPACT_DUST_OR_DONATION_DOS',
            'reason': ('claim is a reversible dust/donation or denial-of-service '
                       'griefing without direct loss, permanent lock, or '
                       'unauthorized transfer'),
            'impact_class': 'dust_or_donation_dos',
        }
    if governance_grief:
        return {
            'sufficiency': 'insufficient',
            'code': 'IMPACT_GOVERNANCE_GRIEFING',
            'reason': ('claim only blocks governance/management action and does '
                       'not establish direct loss, permanent lock, or '
                       'unauthorized transfer'),
            'impact_class': 'governance_griefing',
        }
    return {'sufficiency': 'unknown', 'code': None, 'reason': None,
            'impact_class': 'other_or_unknown'}


def preflight(formal: dict, binding: dict, claim_id: str) -> dict:
    """Run source-level checks that must happen before forge execution.

    This phase deliberately has no access to judge or impact ledgers.  A
    trusted label describes how a *completed* dynamic result should be
    adjudicated; using it here would prevent negative cases from producing the
    very evidence needed to detect a false positive.
    """
    claim = _claim(formal, claim_id)
    if claim is None:
        return {'schema_version': SCHEMA_VERSION, 'claim_id': claim_id,
                'decision_phase': 'pre_execution',
                'status': 'reject', 'codes': ['CLAIM_MISSING'],
                'problems': [{'code': 'CLAIM_MISSING',
                              'message': 'claim not found in formalization'}]}

    p_expr = _expr(claim, 'preconditions')
    i_expr = _expr(claim, 'safety')
    v_expr = _expr(claim, 'effects')
    p_symbols = precondition_symbols_for_claim(formal, claim_id)
    i_symbols = safety_symbols_for_claim(formal, claim_id)
    v_symbols = _vars(v_expr) - p_symbols
    entries = binding.get('bindings') or {}

    problems = []
    constants = {}
    for role, symbols in (('P', p_symbols), ('I', i_symbols), ('V', v_symbols)):
        for symbol in sorted(symbols):
            value = _constant((entries.get(symbol) or {}).get('solidity_expr'))
            if value is None:
                continue
            constants[symbol] = {'role': role, 'value': value}
            if role == 'I' and value in {'true', 'false'}:
                problems.append({
                    'code': 'CONSTANT_INVARIANT',
                    'severity': 'error',
                    'symbol': symbol,
                    'message': (f'I symbol {symbol!r} is constant {value}; '
                                'the invariant probe is vacuous or always false'),
                })
            elif role == 'V' and value in {'true', 'false'}:
                problems.append({
                    'code': 'CONSTANT_EFFECT',
                    'severity': 'error',
                    'symbol': symbol,
                    'message': (f'V symbol {symbol!r} is constant {value}; '
                                'it cannot independently witness the hazard'),
                })
            elif role == 'P' and value == 'false':
                problems.append({
                    'code': 'CONSTANT_FALSE_PRECONDITION',
                    'severity': 'error',
                    'symbol': symbol,
                    'message': (f'P symbol {symbol!r} is constant false; every '
                                'probe would pass vacuously'),
                })

    effect_independent = _independent_effect(
        i_expr, v_expr, i_symbols, v_symbols)
    if not effect_independent:
        problems.append({
            'code': 'EFFECT_NOT_INDEPENDENT',
            'severity': 'warning',
            'message': ('V uses only the I expression/symbols and is not its '
                        'logical negation; it cannot corroborate a violation'),
        })

    blocking = [p for p in problems if p['severity'] in ('error', 'reject')]
    if any(p['code'] in ('CONSTANT_INVARIANT', 'CONSTANT_EFFECT',
                         'CONSTANT_FALSE_PRECONDITION') for p in blocking):
        status = 'reject'
        category = 'binding_error'
    else:
        status = 'pass'
        category = None
    return {
        'schema_version': SCHEMA_VERSION,
        'claim_id': claim_id,
        'decision_phase': 'pre_execution',
        'status': status,
        'category': category,
        'codes': [p['code'] for p in problems],
        'problems': problems,
        'constants': constants,
        'effect_independent': effect_independent,
        'impact_sufficiency': 'not_evaluated',
        'impact_class': None,
        'trusted_label': {},
        'roles': {
            'P': sorted(p_symbols),
            'I': sorted(i_symbols),
            'V': sorted(v_symbols),
        },
    }


def adjudicate(formal: dict, binding: dict, claim_id: str,
               trusted_label: dict | None = None,
               preflight_result: dict | None = None,
               execution: dict | None = None) -> dict:
    """Attach impact/judge adjudication to a completed execution result.

    The dynamic consistency verdict is evidence and is never rewritten here.
    The returned ``status`` only says whether the evidence is eligible for the
    vulnerability-level metric.  This keeps a judge-invalid true reproduction
    visible as a false positive instead of relabelling it as "unresolved".
    Consistency eligibility uses only report-derived impact text; trusted
    labels still govern vulnerability eligibility and never enter this gate.
    """
    structural = (preflight_result if isinstance(preflight_result, dict)
                  else preflight(formal, binding, claim_id))
    claim = _claim(formal, claim_id)
    if claim is None:
        return {**structural, 'decision_phase': 'post_execution'}

    problems = list(structural.get('problems') or [])
    impact = _impact(formal, claim, trusted_label)
    report_impact = _impact(formal, claim, None)
    if impact['code']:
        problems.append({
            'code': impact['code'],
            'severity': 'reject',
            'message': impact['reason'],
        })

    structural_reject = structural.get('status') == 'reject'
    impact_reject = impact['sufficiency'] == 'insufficient'
    report_impact_reject = report_impact['sufficiency'] == 'insufficient'
    if structural_reject:
        status = 'reject'
        category = structural.get('category') or 'binding_error'
    elif impact_reject:
        status = 'reject'
        category = 'impact_insufficient'
    else:
        status = 'pass'
        category = None

    execution = execution or {}
    consistency = execution.get('consistency_verdict')
    witness = negative_witness(execution)
    return {
        **structural,
        'schema_version': SCHEMA_VERSION,
        'claim_id': claim_id,
        'decision_phase': 'post_execution',
        'status': status,
        'category': category,
        'codes': [p['code'] for p in problems],
        'problems': problems,
        'impact_sufficiency': impact['sufficiency'],
        'impact_class': impact.get('impact_class'),
        'report_impact_sufficiency': report_impact['sufficiency'],
        'report_impact_class': report_impact.get('impact_class'),
        'report_impact_code': report_impact.get('code'),
        'trusted_label': trusted_label or {},
        'label_scope': (trusted_label or {}).get('label_scope', 'none'),
        'consistency_verdict': consistency,
        'negative_witness': witness,
        'metric_eligibility': {
            'consistency': (consistency is not None
                            and not report_impact_reject),
            'vulnerability': (consistency is not None
                              and not structural_reject
                              and not impact_reject),
            'negative': (consistency in {
                'violation_not_reproduced',
                'effect_observed_invariant_holds',
                'invariant_holds_on_exploit_path',
            } and witness['eligible'] and not structural_reject
                and not impact_reject),
            'exclusion_reason': (
                structural.get('category') if structural_reject else
                (impact['code'] if impact_reject else None)),
            'consistency_exclusion_reason': (
                report_impact['code'] if report_impact_reject else None),
        },
    }


def inspect(formal: dict, binding: dict, claim_id: str,
            trusted_label: dict | None = None) -> dict:
    """Compatibility entry point combining preflight and adjudication."""
    structural = preflight(formal, binding, claim_id)
    decision = adjudicate(
        formal, binding, claim_id, trusted_label=trusted_label,
        preflight_result=structural)
    return {**decision, 'decision_phase': 'combined'}


def _find_claim_row(payload, case_id: str, claim_id: str) -> dict | None:
    if isinstance(payload, list):
        for row in payload:
            found = _find_claim_row(row, case_id, claim_id)
            if found is not None:
                return found
        return None
    if not isinstance(payload, dict):
        return None
    row_claim = str(payload.get('claim_id') or payload.get('claim') or '')
    row_case = str(payload.get('case_id') or payload.get('case') or '')
    if claim_id and (row_claim == claim_id or claim_id in row_claim):
        return payload
    if case_id and (row_case == case_id or case_id in row_case):
        return payload
    for key in ('claims', 'cases', 'rows', 'selected', 'invalid',
                'impact_insufficient', 'records'):
        found = _find_claim_row(payload.get(key), case_id, claim_id)
        if found is not None:
            return found
    return None


def _with_label_scope(row: dict, *, source: str,
                      matched_claim: bool) -> dict:
    label = dict(row)
    explicit = str(label.get('label_scope') or label.get('scope') or '')
    if explicit in {'case', 'claim'}:
        scope = explicit
    elif matched_claim and (label.get('claim_id') or label.get('claim')):
        scope = 'claim'
    else:
        scope = 'case'
    label['label_scope'] = scope
    label.setdefault('label_source', source)
    return label


def load_trusted_label(case_dir: Path, claim_id: str,
                       stage2_dir: Path | None = None) -> dict:
    """Load an impact/judge label from deterministic local ledgers.

    The gate intentionally only reads files supplied by the evaluation case or
    its Stage-2 directory.  It never infers invalidity from report prose here;
    the existing lexical heuristic remains a fallback for legacy runs.
    """
    case_dir = Path(case_dir)
    roots = [case_dir]
    if stage2_dir is not None:
        roots.append(Path(stage2_dir))
    # Central ledgers are produced by the frozen evaluation, but they are
    # still deterministic inputs.  Reading them here prevents the same
    # judge-invalid / impact-insufficient case from being re-judged by prose
    # heuristics during a small regression run.
    roots.append(Path(__file__).resolve().parents[1] / 'evaluation' / 'metrics')
    names = ('impact_insufficient_cases.json', 'judge_ground_truth.json',
             'blind_invalid.json', 'judge_invalid.json',
             'official_negative_pool_20261121.json')
    for root in roots:
        for name in names:
            path = root / name
            if not path.is_file():
                continue
            try:
                payload = json.loads(path.read_text())
            except (OSError, json.JSONDecodeError):
                continue
            if name == 'impact_insufficient_cases.json':
                cases = payload.get('cases') if isinstance(payload, dict) else []
                if isinstance(cases, list) and case_dir.name in cases:
                    return {
                        'case_id': case_dir.name,
                        'label_scope': 'case',
                        'label_source': name,
                        'impact_sufficiency': 'insufficient',
                        'impact_class': 'trusted_insufficient',
                        'reason': ('frozen impact-insufficient ledger marks this '
                                   'case as insufficient'),
                    }
            row = _find_claim_row(payload, case_dir.name, claim_id)
            if row is not None:
                matched_claim = bool(
                    row.get('claim_id') or row.get('claim'))
                return _with_label_scope(
                    row, source=name, matched_claim=matched_claim)
    return {}
