"""binding.json loading and validation against a stage-2 spec."""
from __future__ import annotations

import json
from pathlib import Path

from lib.spec_loader import SpecError, claim_binding_contract, required_symbols

BINDING_SCHEMA = 'stage3-binding/1'
KINDS = {'boolean_predicate', 'address_value', 'numeric_value'}
CHECKPOINTS = {'before', 'after', 'input'}


def load_binding(path: Path) -> dict:
    path = Path(path)
    if not path.is_file():
        raise SpecError(f'missing binding file: {path}')
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise SpecError('binding.json must be a JSON object')
    return value


def validate_binding(binding: dict, spec: dict) -> tuple[str, dict]:
    if binding.get('schema_version') != BINDING_SCHEMA:
        raise SpecError('unsupported binding schema')
    claim_id = binding.get('claim_id')
    if not isinstance(claim_id, str) or not claim_id:
        raise SpecError('binding.json is missing claim_id')
    contract = claim_binding_contract(spec, claim_id)
    required = {row['symbol'] for row in contract.get('symbols', [])
                if row.get('appears_in')}
    entries = binding.get('bindings')
    if not isinstance(entries, dict) or set(entries) != required:
        raise SpecError(
            f'bindings must cover exactly the P/I/V symbols: '
            f'{", ".join(sorted(required))}')
    for name, entry in entries.items():
        if not isinstance(entry, dict):
            raise SpecError(f'bad binding entry for {name}')
        if entry.get('kind') not in KINDS:
            raise SpecError(f'bad binding kind for {name}')
        if not isinstance(entry.get('solidity_expr'), str) or not entry['solidity_expr'].strip():
            raise SpecError(f'bad solidity_expr for {name}')
        if entry.get('checkpoint') not in CHECKPOINTS:
            raise SpecError(f'bad checkpoint for {name}')
        if not isinstance(entry.get('source'), str) or not entry['source'].strip():
            raise SpecError(f'bad source for {name}')
    return claim_id, entries


def build_feedback(claim_id: str, entries: dict, code_query_results: dict,
                   poc: dict | None = None) -> dict:
    symbol_bindings = {
        name: {
            'status': 'bound',
            'binding': f"{entry['solidity_expr']} ({entry['checkpoint']} @ {entry['source']})",
        }
        for name, entry in entries.items()
    }
    feedback = {
        'schema_version': 'stage3-consistency-feedback/1',
        'claim_id': claim_id,
        'symbol_bindings': symbol_bindings,
        'code_query_results': dict(code_query_results),
    }
    if poc is not None:
        feedback['poc'] = poc
    return feedback
