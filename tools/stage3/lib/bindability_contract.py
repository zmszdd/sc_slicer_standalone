"""Deterministic bindability contract for the stage-2 -> stage-3 handoff.

Stage 2 reads the report only, so it cannot emit a code anchor; the contract is
therefore computed stage-3 side *before* any LLM binding is proposed, from the
stage-2 spec plus the assembled Solidity source.  It is persisted per case so
the verdict loop / metrics path can route deterministically instead of letting
the binding LLM free-guess the injection target.

Schema::

    {
      "schema_version": "stage3-bindability-contract/1",
      "case": "<case>",
      "claims": {
        "<claim_id>": {
          "bindability": "single_anchor|file_level|multi_contract|no_anchor",
          "dynamically_expressible": true|false,
          "suggested_patch_contract": "<Contract>|null",
          "anchor_roles": ["I", "V"],
          "anchor_observability": "low|medium|high"
        }
      }
    }
"""
from __future__ import annotations

import json
from pathlib import Path

SCHEMA = 'stage3-bindability-contract/1'


def build_contract(stage2_dir: Path, claims: list[str], src: Path) -> dict:
    from lib.anchor_resolver import resolve_anchors

    rows = {}
    for claim_id in claims:
        try:
            anchor = resolve_anchors(stage2_dir, claim_id, src)
        except Exception:
            rows[claim_id] = {
                'bindability': 'unknown',
                'dynamically_expressible': False,
                'suggested_patch_contract': None,
                'anchor_roles': [],
                'anchor_observability': 'low',
            }
            continue
        rows[claim_id] = {
            'bindability': anchor.get('bindability'),
            'dynamically_expressible': anchor.get('dynamically_expressible'),
            'suggested_patch_contract': anchor.get('suggested_patch_contract'),
            'anchor_roles': list(anchor.get('anchor_roles') or []),
            'anchor_observability': _min_anchor_observability(anchor),
        }
    return rows


_OBS_RANK = {'low': 0, 'medium': 1, 'high': 2}


def _min_anchor_observability(anchor: dict) -> str:
    """Worst observability across a claim's anchoring (I/V) symbols.

    ``low`` means at least one anchoring symbol has zero fuzzy-token overlap
    with any declared identifier and is genuinely unobservable by the
    deterministic matcher. ``medium``/``high`` mean the matcher still saw
    semantic signal even though it could not reduce it to a single strong
    anchor, which is a false negative to be handed to the binding LLM.
    """
    symbols = anchor.get('symbols') or []
    ranks = []
    for sym in symbols:
        appears_in = sym.get('appears_in') or []
        if not any(role in appears_in for role in ('I', 'V')):
            continue
        ranks.append(_OBS_RANK.get(sym.get('observability'), 0))
    if not ranks:
        return 'low'
    return ['low', 'medium', 'high'][min(ranks)]


def is_hard_ceiling(claim_row: dict) -> bool:
    """True only for a genuinely unobservable ``no_anchor`` claim.

    ``no_anchor`` is a deterministic upper bound from fuzzy token overlap; it
    has false negatives whenever the report wording (e.g. "zero shares") does
    not token-overlap the code identifier (e.g. ``_mint``/``balanceOf``). Only
    a ``no_anchor`` whose anchoring symbols are all ``low`` observability is a
    hard ceiling that must skip the binding LLM.
    """
    if claim_row.get('bindability') != 'no_anchor':
        return False
    return claim_row.get('anchor_observability') == 'low'


def write_contract(case_dir: Path, stage2_dir: Path, claims: list[str]) -> Path:
    rows = build_contract(stage2_dir, claims, case_dir / 'src')
    payload = {
        'schema_version': SCHEMA,
        'case': case_dir.name,
        'claims': rows,
    }
    out = case_dir / 'stage3-bindability.json'
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n')
    return out


def load_contract(case_dir: Path) -> dict:
    path = case_dir / 'stage3-bindability.json'
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError:
        return {}
    if data.get('schema_version') == SCHEMA:
        return data.get('claims', {})
    # Backward-compatible read of the earlier stage3-bindability-feedback/1
    # file that only stored the bindability class per claim.
    if isinstance(data.get('bindabilities'), dict):
        return {
            claim_id: {
                'bindability': bindability,
                'dynamically_expressible': bindability in
                    ('single_anchor', 'file_level'),
                'suggested_patch_contract': None,
                'anchor_roles': ['I', 'V'],
            }
            for claim_id, bindability in data['bindabilities'].items()
        }
    return {}
