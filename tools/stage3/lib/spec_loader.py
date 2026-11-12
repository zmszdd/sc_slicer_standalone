"""Load and minimally validate a stage-2 run directory."""
from __future__ import annotations

import json
from pathlib import Path


class SpecError(ValueError):
    pass


def _read_json(path: Path) -> dict:
    if not path.is_file():
        raise SpecError(f'missing file: {path}')
    try:
        value = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise SpecError(f'invalid JSON in {path}: {exc}') from exc
    if not isinstance(value, dict):
        raise SpecError(f'expected a JSON object in {path}')
    return value


def load_stage2_run(stage2_dir: Path) -> dict:
    stage2_dir = Path(stage2_dir)
    spec = _read_json(stage2_dir / 'stage3-spec.json')
    constraints = _read_json(stage2_dir / 'constraints.json')
    formal = _read_json(stage2_dir / 'formalization.json')

    spec_claims = spec.get('claims')
    if not isinstance(spec_claims, list) or not spec_claims:
        raise SpecError('stage3-spec.json has no claims')
    formal_claims = formal.get('claims')
    if not isinstance(formal_claims, list) or not formal_claims:
        raise SpecError('formalization.json has no claims')
    formal_ids = {row.get('id') for row in formal_claims if isinstance(row, dict)}
    for row in spec_claims:
        if not isinstance(row, dict) or 'claim_id' not in row:
            raise SpecError('stage3-spec claim is missing claim_id')
        if row['claim_id'] not in formal_ids:
            raise SpecError(f"claim {row['claim_id']} not found in formalization.json")

    eligible_claims = [row for row in spec_claims
                       if row.get('formalization_status') == 'formalized_candidate']
    rejected_claims = [row['claim_id'] for row in spec_claims
                       if row.get('formalization_status') != 'formalized_candidate']
    if not eligible_claims:
        raise SpecError(
            'stage2 quality gate blocked stage3: no claim is formalized_candidate')
    spec = {**spec, 'claims': eligible_claims,
            'rejected_claims': rejected_claims}
    return {'spec': spec, 'constraints': constraints, 'formal': formal}


def claim_binding_contract(spec: dict, claim_id: str) -> dict:
    for row in spec.get('claims', []):
        if row.get('claim_id') == claim_id:
            contract = row.get('binding_contract')
            if not isinstance(contract, dict):
                raise SpecError(f'claim {claim_id} has no binding_contract')
            return contract
    raise SpecError(f'claim {claim_id} not found in stage3-spec.json')


def required_symbols(spec: dict, claim_id: str) -> set[str]:
    contract = claim_binding_contract(spec, claim_id)
    return {
        row['symbol'] for row in contract.get('symbols', [])
        if row.get('appears_in')
    }


def _expression_vars(node) -> set[str]:
    """Symbols referenced by a stage-2 P/I/V expression AST."""
    if not isinstance(node, dict):
        return set()
    if 'var' in node:
        return {node['var']}
    found: set[str] = set()
    for value in node.values():
        if isinstance(value, dict):
            found |= _expression_vars(value)
        elif isinstance(value, list):
            for item in value:
                found |= _expression_vars(item)
    return found


def safety_symbols_for_claim(formal: dict, claim_id: str) -> set[str]:
    """Symbols appearing in the claim's safety (I) expression.

    A trivially-constant boolean binding is only vacuous when it waters down
    I itself; a constant P-side boolean (for example ``direct_call_occurred``
    bound to ``true`` in a PoC that calls the function directly) is a faithful
    precondition and must not fail the binding lint.
    """
    for row in formal.get('claims', []):
        if not isinstance(row, dict) or row.get('id') != claim_id:
            continue
        properties = row.get('properties', {})
        safety = properties.get('safety', {})
        preconditions = properties.get('preconditions', {})
        # The safety expression is stored as ``P -> I``; only the symbols in
        # the consequent are the invariant's dynamic content.  A P-side symbol
        # that also appears in the antecedent must not count as I-only.
        return (_expression_vars(safety.get('expression')) -
                _expression_vars(preconditions.get('expression')))
    return set()


def precondition_symbols_for_claim(formal: dict, claim_id: str) -> set[str]:
    """Symbols appearing in the claim's precondition (P) expression."""
    for row in formal.get('claims', []):
        if not isinstance(row, dict) or row.get('id') != claim_id:
            continue
        properties = row.get('properties', {})
        preconditions = properties.get('preconditions', {})
        return _expression_vars(preconditions.get('expression'))
    return set()
