"""Resolve the frozen claim population for the locked mainline sample.

Stage-3 run directories accumulate artifacts from earlier Stage-2 revisions.
Counting a stale summary for a claim that is no longer in the frozen spec makes
a current case look unresolved forever.  This module defines the canonical
population as the claim ids present in the frozen goldset specs for the
sampled cases.  It is deterministic, uses no model, and does not inspect any
Stage-3 verdict.
"""
from __future__ import annotations

import json
from pathlib import Path

from lib import invariant_ranking

SCHEMA_VERSION = 'mainline-claim-population/1'

STAGE3 = Path(__file__).resolve().parents[1]
METRICS = STAGE3 / 'evaluation' / 'metrics'
GOLDSET_ROOTS = (
    METRICS / 'mainline_goldset_1_7_31_pos',
    METRICS / 'mainline_goldset_1_7_31_neg',
)
CLAIM_TOP_K = 3


def _load(path: Path) -> dict:
    try:
        payload = json.loads(path.read_text())
    except (OSError, ValueError):
        return {}
    return payload if isinstance(payload, dict) else {}


def current_claim_ids(sample_path: Path) -> dict[str, frozenset[str]]:
    """Return case -> frozen claim ids for cases that have a Stage-2 spec."""
    sample = _load(Path(sample_path))
    wanted = {str(case) for case in sample.get('positive_cases') or []}
    wanted |= {str(case) for case in sample.get('negative_cases') or []}
    population: dict[str, frozenset[str]] = {}
    for root in GOLDSET_ROOTS:
        if not root.is_dir():
            continue
        for run_dir in sorted(root.glob('runs_*')):
            for case_dir in sorted(run_dir.iterdir()):
                if not case_dir.is_dir() or case_dir.name not in wanted:
                    continue
                spec_path = case_dir / 'stage3-spec.json'
                if not spec_path.is_file():
                    continue
                payload = _load(spec_path)
                claims = payload.get('claims') or []
                ranking = invariant_ranking.rank_claims(
                    Path(spec_path).parent, payload, limit=CLAIM_TOP_K)
                population[case_dir.name] = frozenset(
                    str(claim_id)
                    for claim_id in ranking['selected_claim_ids'])
    return population


def describe() -> dict:
    return {
        'schema_version': SCHEMA_VERSION,
        'goldset_roots': [str(path) for path in GOLDSET_ROOTS],
        'claim_top_k': CLAIM_TOP_K,
    }
