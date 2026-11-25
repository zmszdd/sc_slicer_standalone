#!/usr/bin/env python3
"""Read-only replay of Stage-3 claim ranking variants.

The replay never executes Stage 3 and never rewrites an evaluation artifact. It
joins the frozen Stage-2 claim population to the existing current-protocol
Stage-3 outcomes, then compares the current ranking with two alternatives:

* observability-first, with an optional one-claim-per-impact diversity pass;
* a deterministic paper-style text-similarity proxy.

The paper-style proxy is deliberately labelled a proxy. PropertyGPT ranks a
generated property against a human reference property. This project has no
isomorphic reference property set, so the proxy uses the report impact text as
the reference and simple token overlap as the similarity function.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
STAGE3 = HERE.parents[1]
if str(STAGE3) not in sys.path:
    sys.path.insert(0, str(STAGE3))

from lib.invariant_ranking import rank_claims  # noqa: E402

SCHEMA_VERSION = 'stage3-ranking-replay/1'
PROTOCOL_VERSION = 'mainline/1.7.33'
PRIMARY_K = 3
TOP_KS = (1, 2, 3, 5)

DEFAULT_POS_ROOT = HERE / 'mainline_goldset_1_7_31_pos'
DEFAULT_NEG_ROOT = HERE / 'mainline_goldset_1_7_31_neg'
DEFAULT_POS_EVAL = HERE / 'mainline_pos_eval_1_7_33.json'
DEFAULT_NEG_EVAL = HERE / 'mainline_neg_eval_1_7_33.json'
DEFAULT_RUNS = STAGE3 / 'runs'
DEFAULT_JSON = HERE / 'ranking_replay_20261124.json'
DEFAULT_MD = HERE / 'ranking_replay_20261124.md'

TERMINAL_VERDICTS = {
    'violation_reproduced',
    'violation_not_reproduced',
    'effect_observed_invariant_holds',
    'invariant_holds_on_exploit_path',
}

HARD_RISK_CODES = {
    'I_MUTATION_SITE_MISSING',
    'OBSERVABILITY_REQUIRES_CODE_FACT',
    'OBSERVABILITY_HIGH_RISK',
    'CHECKPOINT_MISSING',
    'stage2_review_required',
}

SNAPSHOT_RISK_CODES = {
    'CHECKPOINT_SNAPSHOT_ONLY',
    'I_SNAPSHOT_ONLY',
    'I_SNAPSHOT_BARE_VAR',
    'I_NOT_TRANSITION',
    'I_SAME_CHECKPOINT_ONLY',
    'I_CHECKPOINT_COLLAPSED',
    'I_LAYER_MISMATCH',
}

TRANSITION_BUCKETS = {'transition', 'state_before_after'}
STOPWORDS = {
    'a', 'an', 'and', 'are', 'as', 'at', 'be', 'been', 'by', 'can', 'do',
    'does', 'for', 'from', 'has', 'have', 'if', 'in', 'into', 'is', 'it',
    'its', 'may', 'must', 'not', 'of', 'on', 'or', 'that', 'the', 'their',
    'then', 'this', 'to', 'was', 'were', 'when', 'which', 'while', 'with',
    'without', 'will', 'would', 'any', 'all', 'each', 'every', 'user',
    'users', 'attacker', 'attackers', 'contract', 'contracts', 'amount',
    'token', 'tokens', 'function', 'functions', 'call', 'calls', 'after',
    'before', 'during', 'state',
}


def _load(path: Path) -> dict:
    try:
        payload = json.loads(Path(path).read_text())
    except (OSError, ValueError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _sha256(path: Path) -> str | None:
    try:
        return hashlib.sha256(Path(path).read_bytes()).hexdigest()
    except OSError:
        return None


def _codes(contract: dict) -> set[str]:
    out: set[str] = set()
    for field in ('problems', 'warnings', 'advisories'):
        for row in contract.get(field) or []:
            code = row.get('code') if isinstance(row, dict) else row
            if code:
                out.add(str(code))
    return out


def _candidate_index(stage2_dir: Path) -> dict:
    payload = _load(Path(stage2_dir) / 'invariant-candidates.json')
    claims = payload.get('claims') or {}
    return claims if isinstance(claims, dict) else {}


def _selected_candidate(index: dict, claim_id: str) -> dict:
    row = index.get(claim_id) or {}
    selected_id = row.get('selected_candidate_id')
    return next((candidate for candidate in row.get('candidates') or []
                 if isinstance(candidate, dict)
                 and candidate.get('candidate_id') == selected_id), {})


def _impact_map(spec: dict) -> dict[str, dict]:
    mapped: dict[str, dict] = {}
    for item in spec.get('report_impact_coverage') or []:
        if not isinstance(item, dict):
            continue
        impact_id = str(item.get('impact_id') or '')
        evidence = ' '.join(str(value) for value in item.get('evidence') or [])
        text = ' '.join(value for value in (impact_id, evidence) if value)
        for claim_id in item.get('claim_ids') or []:
            mapped[str(claim_id)] = {'impact_id': impact_id, 'text': text,
                                     'evidence': evidence}
    return mapped


def _tokens(text: str | None) -> set[str]:
    words = re.findall(r'[a-z0-9]+', str(text or '').lower())
    return {word for word in words if word not in STOPWORDS and len(word) > 1}


def _jaccard(left: str | None, right: str | None) -> float:
    a, b = _tokens(left), _tokens(right)
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def _transition_level(contract: dict, candidate: dict) -> int:
    profile = contract.get('semantic_profile') or {}
    if profile.get('has_before_after') or profile.get('bucket') in TRANSITION_BUCKETS:
        return 1
    checkpoints = ((candidate.get('checkpoints') or {}).get('normalized') or {})
    values = set(checkpoints.values())
    if 'transition' in values or {'before', 'after'} <= values:
        return 1
    return 0


def _claim_row(*, case: str, label: str, stage2_dir: Path, spec: dict,
               claim: dict, current_row: dict, index: dict,
               impacts: dict[str, dict]) -> dict:
    claim_id = str(claim.get('claim_id'))
    contract = claim.get('formalization_contract') or {}
    candidate = _selected_candidate(index, claim_id)
    codes = _codes(contract)
    labels = set(codes)
    labels.update(str(value) for value in candidate.get('quality_labels') or []
                  if value)
    impact = impacts.get(claim_id) or {}
    reference = impact.get('text') or ''
    candidate_text = candidate.get('text') or claim.get('scope') or ''
    scope = claim.get('scope') or ''
    x_similarity = _jaccard(scope, reference)
    y_similarity = _jaccard(candidate_text, reference)
    paper_score = (0.69 * x_similarity + 0.309 * y_similarity)
    auto_score = (2 if contract.get('route') == 'auto_assert' else 0) + (
        1 if contract.get('can_auto_assert') else 0)
    return {
        'case': case,
        'label': label,
        'stage2_dir': str(stage2_dir),
        'claim_id': claim_id,
        'scope': scope,
        'impact_id': impact.get('impact_id') or claim_id,
        'current_rank_score': round(float(current_row.get('score') or 0.0), 4),
        'current_rank_reasons': list(current_row.get('reasons') or []),
        'quality_labels': sorted(labels),
        'hard_risk_count': len(labels & HARD_RISK_CODES),
        'snapshot_risk_count': len(labels & SNAPSHOT_RISK_CODES),
        'transition_level': _transition_level(contract, candidate),
        'independent': bool((contract.get('i_v') or {}).get('independent', True)),
        'auto_score': auto_score,
        'executable': bool(candidate.get('executable')),
        'evidence_count': len(candidate.get('evidence_ids') or []),
        'candidate_score': round(float(candidate.get('score') or 0.0), 4),
        'candidate_derivation': candidate.get('derivation'),
        'selected_candidate_id': candidate.get('candidate_id'),
        'paper_x_similarity': round(x_similarity, 6),
        'paper_y_similarity': round(y_similarity, 6),
        'paper_score': round(paper_score, 6),
    }


def _observability_key(row: dict):
    return (
        row['hard_risk_count'],
        row['snapshot_risk_count'],
        -row['transition_level'],
        -int(row['independent']),
        -int(row['executable']),
        -row['auto_score'],
        -row['evidence_count'],
        -row['candidate_score'],
        row['claim_id'],
    )


def _diverse_order(rows: list[dict]) -> list[dict]:
    unique: list[dict] = []
    repeated: list[dict] = []
    seen: set[str] = set()
    for row in rows:
        impact_id = row['impact_id']
        if impact_id in seen:
            repeated.append(row)
        else:
            seen.add(impact_id)
            unique.append(row)
    return unique + repeated


def _load_cases(roots: tuple[Path, ...]) -> tuple[list[dict], list[dict]]:
    cases: list[dict] = []
    rows: list[dict] = []
    seen_cases: set[str] = set()
    for root in roots:
        label = 'negative' if '_neg' in Path(root).name else 'positive'
        by_case: dict[str, tuple[float, Path, dict]] = {}
        for path in Path(root).glob('runs_*/*/stage3-spec.json'):
            payload = _load(path)
            if not payload.get('claims'):
                continue
            case = path.parent.name
            stamp = path.stat().st_mtime
            if case not in by_case or stamp > by_case[case][0]:
                by_case[case] = (stamp, path, payload)
        for case, (_, spec_path, spec) in sorted(by_case.items()):
            if case in seen_cases:
                continue
            seen_cases.add(case)
            stage2_dir = spec_path.parent
            ranking = rank_claims(stage2_dir, spec, limit=0)
            current_rows = {str(row['claim_id']): row
                            for row in ranking.get('ranked') or []}
            index = _candidate_index(stage2_dir)
            impacts = _impact_map(spec)
            case_rows = []
            for claim in spec.get('claims') or []:
                if not isinstance(claim, dict) or not claim.get('claim_id'):
                    continue
                claim_id = str(claim['claim_id'])
                case_rows.append(_claim_row(
                    case=case, label=label, stage2_dir=stage2_dir,
                    spec=spec, claim=claim,
                    current_row=current_rows.get(claim_id) or {},
                    index=index, impacts=impacts))
            cases.append({
                'case': case,
                'label': label,
                'spec_path': str(spec_path),
                'claim_count': len(case_rows),
                'current_order': [row['claim_id'] for row in sorted(
                    case_rows, key=lambda item: (
                        -item['current_rank_score'], item['claim_id']))],
            })
            rows.extend(case_rows)
    return cases, rows


def _load_outcomes(eval_paths: tuple[Path, ...], runs_dir: Path,
                   claims: list[dict]) -> dict[str, dict]:
    population = {(row['case'], row['claim_id']) for row in claims}
    outcomes: dict[tuple[str, str], dict] = {}
    for path in eval_paths:
        payload = _load(path)
        for case_row in payload.get('cases') or []:
            if not isinstance(case_row, dict) or 'claim_ids' not in case_row:
                continue
            case = str(case_row.get('case') or '')
            bound = {str(value) for value in case_row.get('bound_claim_ids') or []}
            for claim_id, verdict in zip(case_row.get('claim_ids') or [],
                                         case_row.get('verdicts') or []):
                key = (case, str(claim_id))
                if key not in population:
                    continue
                outcomes[key] = {
                    'verdict': verdict,
                    'bound': str(claim_id) in bound,
                    'source': str(path),
                }
    for path in Path(runs_dir).glob('*/stage3-summary.json'):
        summary = _load(path)
        case = Path(str(summary.get('case') or '')).name
        claim_id = str(summary.get('claim_id') or '')
        key = (case, claim_id)
        if key not in population or key in outcomes:
            continue
        protocol = ((summary.get('artifact_fingerprint') or {}).get(
            'mainline_protocol') or {})
        if protocol.get('version') != PROTOCOL_VERSION:
            continue
        contract = summary.get('execution_contract') or {}
        requirements = contract.get('requirements') or {}
        outcomes[key] = {
            'verdict': summary.get('consistency_verdict'),
            'bound': bool(requirements.get('required_symbols_bound')),
            'source': str(path),
        }
    return outcomes


def _order_rows(rows: list[dict], variant: str) -> list[dict]:
    if variant == 'current':
        return sorted(rows, key=lambda row: (
            -row['current_rank_score'], row['claim_id']))
    if variant == 'observability':
        return sorted(rows, key=_observability_key)
    if variant == 'observability_diverse':
        return _diverse_order(sorted(rows, key=_observability_key))
    if variant == 'paper_proxy':
        return sorted(rows, key=lambda row: (-row['paper_score'], row['claim_id']))
    raise ValueError(f'unknown ranking variant: {variant}')


def _select(cases: list[dict], rows: list[dict], variant: str,
            limit: int) -> list[dict]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        grouped[row['case']].append(row)
    selected = []
    for case in cases:
        ordered = _order_rows(grouped[case['case']], variant)
        selected.extend(ordered[:limit] if limit > 0 else ordered)
    return selected


def _summarize(selected: list[dict], outcomes: dict[tuple[str, str], dict],
               reproduced_total: int, reproduced_cases: set[str]) -> dict:
    known = [row for row in selected
             if (row['case'], row['claim_id']) in outcomes]
    verdicts = [outcomes[(row['case'], row['claim_id'])]['verdict']
                for row in known]
    bound = [outcomes[(row['case'], row['claim_id'])]['bound'] for row in known]
    terminal = [verdict in TERMINAL_VERDICTS for verdict in verdicts]
    reproduced = [verdict == 'violation_reproduced' for verdict in verdicts]
    impact_counts: dict[tuple[str, str], Counter] = defaultdict(Counter)
    for row in selected:
        impact_counts[row['case']][row['impact_id']] += 1
    duplicate_cases = sum(
        1 for counts in impact_counts.values()
        if sum(count - 1 for count in counts.values() if count > 1) > 0)
    reproduced_case_hits = {
        row['case'] for row, hit in zip(known, reproduced) if hit
    }
    return {
        'selected': len(selected),
        'known_outcomes': len(known),
        'unknown_outcomes': len(selected) - len(known),
        'stage3_completion_known_rate': _rate(len(known), len(selected)),
        'bound_known': sum(bound),
        'binding_success_known_rate': _rate(sum(bound), len(known)),
        'metric_eligible_known': sum(terminal),
        'metric_eligible_known_rate': _rate(sum(terminal), len(known)),
        'reproduced_known': sum(reproduced),
        'known_reproduced_capture_rate': _rate(sum(reproduced),
                                               reproduced_total),
        'known_reproduced_per_selected': _rate(sum(reproduced), len(selected)),
        'known_reproduced_cases_captured': len(reproduced_case_hits),
        'known_reproduced_cases_total': len(reproduced_cases),
        'known_reproduced_case_capture_rate': _rate(
            len(reproduced_case_hits), len(reproduced_cases)),
        'cases_selected': len({row['case'] for row in selected}),
        'cases_with_duplicate_impact': duplicate_cases,
        'unique_impacts': len({(row['case'], row['impact_id'])
                               for row in selected}),
        'transition_claims': sum(row['transition_level'] > 0 for row in selected),
        'transition_rate': _rate(sum(row['transition_level'] > 0
                                     for row in selected), len(selected)),
        'executable_claims': sum(row['executable'] for row in selected),
        'hard_risk_claims': sum(row['hard_risk_count'] > 0 for row in selected),
        'hard_risk_count_total': sum(row['hard_risk_count'] for row in selected),
        'snapshot_risk_claims': sum(row['snapshot_risk_count'] > 0
                                    for row in selected),
        'snapshot_risk_count_total': sum(row['snapshot_risk_count']
                                         for row in selected),
        'known_verdict_counts': dict(sorted(Counter(verdicts).items())),
        'selected_claims': [row['claim_id'] for row in selected],
        'unknown_selected_claims': [
            row['claim_id'] for row in selected
            if (row['case'], row['claim_id']) not in outcomes
        ],
    }


def _rate(numerator: int, denominator: int) -> float:
    return round(numerator / denominator, 6) if denominator else 0.0


def _variant_report(cases: list[dict], rows: list[dict],
                    outcomes: dict[tuple[str, str], dict], variant: str) -> dict:
    totals = Counter(outcome['verdict'] for outcome in outcomes.values())
    reproduced_total = totals.get('violation_reproduced', 0)
    reproduced_cases = {
        case for (case, _), outcome in outcomes.items()
        if outcome.get('verdict') == 'violation_reproduced'
    }
    curves = {}
    for limit in TOP_KS:
        selected = _select(cases, rows, variant, limit)
        curves[str(limit)] = _summarize(
            selected, outcomes, reproduced_total, reproduced_cases)
    selected = _select(cases, rows, variant, PRIMARY_K)
    return {
        'variant': variant,
        'top_k': curves,
        'primary': _summarize(selected, outcomes, reproduced_total,
                              reproduced_cases),
        'per_case': {
            case['case']: {
                'selected_claim_ids': [
                    row['claim_id'] for row in selected
                    if row['case'] == case['case']
                ],
                'selected_impact_ids': [
                    row['impact_id'] for row in selected
                    if row['case'] == case['case']
                ],
            }
            for case in cases
        },
    }


def build(*, pos_root: Path, neg_root: Path, pos_eval: Path, neg_eval: Path,
          runs_dir: Path) -> dict:
    cases, rows = _load_cases((Path(pos_root), Path(neg_root)))
    outcomes = _load_outcomes((Path(pos_eval), Path(neg_eval)),
                              Path(runs_dir), rows)
    variants = ('current', 'observability', 'observability_diverse',
                'paper_proxy')
    reports = {variant: _variant_report(cases, rows, outcomes, variant)
               for variant in variants}
    current = reports['current']['top_k'][str(PRIMARY_K)]
    obs_diverse = reports['observability_diverse']['top_k'][str(PRIMARY_K)]
    return {
        'schema_version': SCHEMA_VERSION,
        'read_only': True,
        'protocol_version': PROTOCOL_VERSION,
        'generated_at': datetime.now(timezone.utc).strftime(
            '%Y-%m-%dT%H:%M:%SZ'),
        'inputs': {
            'positive_spec_root': str(pos_root),
            'negative_spec_root': str(neg_root),
            'positive_eval': {
                'path': str(pos_eval), 'sha256': _sha256(pos_eval)},
            'negative_eval': {
                'path': str(neg_eval), 'sha256': _sha256(neg_eval)},
            'runs_dir': str(runs_dir),
        },
        'sample': {
            'cases': len(cases),
            'positive_cases': sum(case['label'] == 'positive' for case in cases),
            'negative_cases': sum(case['label'] == 'negative' for case in cases),
            'claims': len(rows),
            'known_outcomes': len(outcomes),
            'unknown_outcomes': len(rows) - len(outcomes),
            'known_verdicts': dict(sorted(Counter(
                outcome['verdict'] for outcome in outcomes.values()).items())),
        },
        'ranking_definitions': {
            'current': 'Stage-3 invariant_ranking.py',
            'observability': (
                'Lexicographic preference: fewer hard observability risks, '
                'fewer snapshot risks, transition, independent I/V, '
                'executable candidate, auto-assert route, evidence, candidate '
                'score, claim_id.'),
            'observability_diverse': (
                'observability order with first occurrence of each impact_id '
                'promoted ahead of repeated impact variants.'),
            'paper_proxy': (
                'PropertyGPT-style coefficients applied to deterministic token '
                'overlap: Xraw=Xsummary=scope-vs-report-impact; '
                'Yraw=Ysummary=candidate-text-vs-report-impact. '
                'This is not a reproduction of the paper (no reference property '
                'set and no LLM summaries).'),
        },
        'variants': reports,
        'comparison': {
            'current_to_observability_diverse': {
                'selected_overlap': len(set(current['selected_claims']) &
                                        set(obs_diverse['selected_claims'])),
                'reproduced_known_delta': (
                    obs_diverse['reproduced_known'] -
                    current['reproduced_known']),
                'known_outcomes_delta': (
                    obs_diverse['known_outcomes'] - current['known_outcomes']),
                'duplicate_impact_cases_delta': (
                    obs_diverse['cases_with_duplicate_impact'] -
                    current['cases_with_duplicate_impact']),
                'snapshot_risk_claims_delta': (
                    obs_diverse['snapshot_risk_claims'] -
                    current['snapshot_risk_claims']),
            },
        },
        'policy': (
            'No frozen sample, label, denominator, execution gate, metric '
            'eligibility rule, or authoritative metric file is modified. '
            'Unknown claims remain unknown and are never counted as success.'),
    }


def _fmt(value) -> str:
    if isinstance(value, float):
        return f'{value:.4f}'
    return str(value)


def render_markdown(report: dict) -> str:
    sample = report['sample']
    lines = [
        '# Stage-3 Claim Ranking Offline Replay',
        '',
        f"- Protocol: `{report['protocol_version']}`",
        f"- Read-only: `{str(report['read_only']).lower()}`",
        f"- Sample: {sample['cases']} non-zero-claim cases, "
        f"{sample['claims']} claims "
        f"({sample['positive_cases']} positive / {sample['negative_cases']} negative)",
        f"- Known current-protocol outcomes: {sample['known_outcomes']} / "
        f"{sample['claims']}; unknown claims are never counted as success.",
        '',
        'The paper-style variant is a deterministic proxy, not a reproduction: '
        'this project has no human reference-property corpus and the proxy uses '
        'report impact text instead.',
        '',
        '## Top-3 Comparison',
        '',
        '| variant | selected | known | completion(known) | binding(known) | '
        'eligible(known) | reproduced | known capture | cases captured | '
        'snapshot risk | duplicate-impact cases |',
        '| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | '
        '---: | ---: |',
    ]
    for name, variant in report['variants'].items():
        row = variant['top_k'][str(PRIMARY_K)]
        lines.append(
            f"| `{name}` | {row['selected']} | {row['known_outcomes']} | "
            f"{_fmt(row['stage3_completion_known_rate'])} | "
            f"{_fmt(row['binding_success_known_rate'])} | "
            f"{_fmt(row['metric_eligible_known_rate'])} | "
            f"{row['reproduced_known']} | "
            f"{_fmt(row['known_reproduced_capture_rate'])} | "
            f"{row['known_reproduced_cases_captured']}/"
            f"{row['known_reproduced_cases_total']} | "
            f"{row['snapshot_risk_claims']} | "
            f"{row['cases_with_duplicate_impact']} |")
    lines.extend([
        '',
        '`completion(known)` is coverage of claims that already have a current '
        'Stage-3 result, not a success rate. `known capture` is reproduced '
        'claims selected divided by all known reproduced claims in the frozen '
        'population.',
        '',
        '## Top-K Curve',
        '',
        '| variant | k | selected | known | reproduced | known capture | '
        'snapshot risk | duplicate-impact cases |',
        '| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |',
    ])
    for name, variant in report['variants'].items():
        for k, row in variant['top_k'].items():
            lines.append(
                f"| `{name}` | {k} | {row['selected']} | "
                f"{row['known_outcomes']} | {row['reproduced_known']} | "
                f"{_fmt(row['known_reproduced_capture_rate'])} | "
                f"{row['snapshot_risk_claims']} | "
                f"{row['cases_with_duplicate_impact']} |")
    comp = report['comparison']['current_to_observability_diverse']
    lines.extend([
        '',
        '## Findings',
        '',
        f"- Current Top-3 selects {report['variants']['current']['primary']['selected']} "
        f"claims; {report['variants']['current']['primary']['snapshot_risk_claims']} "
        f"carry snapshot/transition risk and "
        f"{report['variants']['current']['primary']['cases_with_duplicate_impact']} "
        f"cases contain repeated impact variants.",
        f"- Observability-first with impact diversity overlaps the current "
        f"selection on {comp['selected_overlap']} claims; known reproduced "
        f"delta is {comp['reproduced_known_delta']}, snapshot-risk delta is "
        f"{comp['snapshot_risk_claims_delta']}, duplicate-impact-case delta is "
        f"{comp['duplicate_impact_cases_delta']}.",
        '- The replay cannot establish a metric lift because most newly selected '
        'claims have no current-protocol execution result. Any claim of recall '
        'improvement requires a protocol bump and a full rerun.',
        '- All 211 claims carry `I_MUTATION_SITE_MISSING` and '
        '`OBSERVABILITY_REQUIRES_CODE_FACT`. This is a Stage-2 observability '
        'defect, not a ranking-weight defect; no ranker can manufacture a '
        'missing mutation site or code fact.',
        '',
        '## Recommendation',
        '',
        '1. Do not replace the authoritative Top-3 ranking from this replay alone.',
        '2. Fix the upstream mutation-site/observable evidence gap first; the '
        'ranker can only choose among equally unobservable claims today.',
        '3. If a protocol bump is approved, use observability-first plus one '
        'claim per impact as the candidate ranking, then rerun and compare '
        'coverage-aware metrics against this baseline.',
        '',
    ])
    return '\n'.join(lines)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pos-root', type=Path, default=DEFAULT_POS_ROOT)
    parser.add_argument('--neg-root', type=Path, default=DEFAULT_NEG_ROOT)
    parser.add_argument('--pos-eval', type=Path, default=DEFAULT_POS_EVAL)
    parser.add_argument('--neg-eval', type=Path, default=DEFAULT_NEG_EVAL)
    parser.add_argument('--runs-dir', type=Path, default=DEFAULT_RUNS)
    parser.add_argument('--out-json', type=Path, default=DEFAULT_JSON)
    parser.add_argument('--out-md', type=Path, default=DEFAULT_MD)
    args = parser.parse_args(argv)
    report = build(pos_root=args.pos_root, neg_root=args.neg_root,
                   pos_eval=args.pos_eval, neg_eval=args.neg_eval,
                   runs_dir=args.runs_dir)
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    args.out_md.write_text(render_markdown(report) + '\n')
    primary = {name: value['top_k'][str(PRIMARY_K)] for name, value in
               report['variants'].items()}
    print(json.dumps({
        'sample': report['sample'],
        'top3': {name: {key: row[key] for key in (
            'selected', 'known_outcomes', 'reproduced_known',
            'known_reproduced_capture_rate', 'snapshot_risk_claims',
            'cases_with_duplicate_impact')} for name, row in primary.items()},
        'out_json': str(args.out_json),
        'out_md': str(args.out_md),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
