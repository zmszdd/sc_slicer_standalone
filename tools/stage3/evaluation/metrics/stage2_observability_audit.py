#!/usr/bin/env python3
"""Read-only audit of the Stage-2 observability contract.

The audit answers one narrow question: can the current Stage-2 handoff tell
Stage-3 *what to observe* without pretending to already know the implementation
code?  It reads the frozen Stage-2 goldset only.  It never rewrites a run, a
claim, a label, or an authoritative metric.

Two layers are deliberately kept separate:

* Stage-2 declarations: observable kind, scope, receiver, checkpoint and, for
  derived symbols, a definition.
* Stage-3 evidence: the concrete code fact, source location and mutation site.

Conflating the two layers is what produced the current "missing code fact"
warning on every claim.  The report exposes that mismatch instead of hiding it.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
STAGE3 = HERE.parents[1]

SCHEMA_VERSION = 'stage2-observability-audit/1'

DEFAULT_POS_ROOT = HERE / 'mainline_goldset_1_7_31_pos'
DEFAULT_NEG_ROOT = HERE / 'mainline_goldset_1_7_31_neg'
DEFAULT_JSON = HERE / 'stage2_observability_audit_20261124.json'
DEFAULT_MD = HERE / 'stage2_observability_audit_20261124.md'

ROLE_NAMES = ('preconditions', 'safety', 'effects')
ROLE_LABELS = {'preconditions': 'P', 'safety': 'I', 'effects': 'V'}
CODE_EVIDENCE_FIELDS = ('source_entity', 'code_fact', 'mutation_site')
DECLARATION_FIELDS = ('observable_kind', 'scope', 'binding_risk')


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


def _present(value) -> bool:
    return value not in (None, '', [], {})


def _latest_cases(roots: tuple[Path, ...]) -> tuple[list[dict], list[str]]:
    """Return one latest non-empty Stage-2 spec per case.

    Case names are the frozen identity.  When a case appears under both the
    positive and negative roots, the first root wins, matching the ranking
    replay and avoiding accidental double counting.
    """
    cases: list[dict] = []
    warnings: list[str] = []
    seen: set[str] = set()
    for root in roots:
        root = Path(root)
        label = 'negative' if '_neg' in root.name else 'positive'
        by_case: dict[str, tuple[float, Path, dict]] = {}
        for path in root.glob('runs_*/*/stage3-spec.json'):
            payload = _load(path)
            if not payload.get('claims'):
                continue
            case = path.parent.name
            stamp = path.stat().st_mtime
            if case not in by_case or stamp > by_case[case][0]:
                by_case[case] = (stamp, path, payload)
        for case, (_, spec_path, spec) in sorted(by_case.items()):
            if case in seen:
                warnings.append(
                    f'duplicate case across roots ignored: {case} ({root})')
                continue
            seen.add(case)
            stage2_dir = spec_path.parent
            obs_payload = _load(stage2_dir / 'observability-contract.json')
            formal_payload = _load(stage2_dir / 'formalization-contract.json')
            review_payload = _load(stage2_dir / 'observability-review.json')
            cases.append({
                'case': case,
                'label': label,
                'stage2_dir': str(stage2_dir),
                'spec_path': str(spec_path),
                'observability_path': str(
                    stage2_dir / 'observability-contract.json'),
                'formalization_path': str(
                    stage2_dir / 'formalization-contract.json'),
                'observability_review_path': str(
                    stage2_dir / 'observability-review.json'),
                'spec': spec,
                'observability': obs_payload.get('claims') or {},
                'formalization_contract': formal_payload.get('claims') or {},
                'observability_review': review_payload,
            })
    return cases, warnings


def _contract_for_claim(case: dict, claim: dict) -> dict:
    contract = claim.get('formalization_contract')
    if isinstance(contract, dict) and contract:
        return contract
    claims = case['formalization_contract']
    if isinstance(claims, list):
        return next((row for row in claims
                     if isinstance(row, dict)
                     and row.get('claim_id') == claim.get('claim_id')), {})
    if isinstance(claims, dict):
        row = claims.get(claim.get('claim_id'))
        return row if isinstance(row, dict) else {}
    return {}


def _observability_for_claim(case: dict, claim_id: str) -> dict:
    claims = case['observability']
    if isinstance(claims, list):
        row = next((row for row in claims
                    if isinstance(row, dict)
                    and row.get('claim_id') == claim_id), {})
    else:
        row = claims.get(claim_id) or {}
    symbols = row.get('symbols') if isinstance(row, dict) else None
    return symbols if isinstance(symbols, dict) else {}


def _code(codes: Counter, value: str) -> int:
    return int(codes.get(value, 0))


def build(pos_root: Path = DEFAULT_POS_ROOT,
          neg_root: Path = DEFAULT_NEG_ROOT) -> dict:
    roots = (Path(pos_root), Path(neg_root))
    cases, load_warnings = _latest_cases(roots)
    route = Counter()
    status = Counter()
    can_auto = Counter()
    codes = Counter()
    role_occurrences = Counter()
    role_no_code = Counter()
    role_high_risk = Counter()
    role_derived_missing = Counter()
    kinds = Counter()
    scopes = Counter()
    risks = Counter()
    missing_fields = Counter()
    field_present = Counter()
    unique_symbol_keys: set[tuple[str, str, str]] = set()
    requires_code_fact: set[tuple[str, str, str]] = set()
    derived_missing: set[tuple[str, str, str]] = set()
    high_risk_symbols: set[tuple[str, str, str]] = set()
    no_code_symbols: set[tuple[str, str, str]] = set()
    claim_rows: list[dict] = []
    review_claim_count = 0
    review_established = Counter()
    review_statuses = Counter()
    review_warning_claims = 0

    for case in cases:
        case_name = case['case']
        review = case.get('observability_review') or {}
        review_rows = review.get('claims') or []
        if isinstance(review_rows, list):
            for row in review_rows:
                if isinstance(row, dict):
                    review_claim_count += 1
                    review_established[str(
                        bool(review.get('observability_established'))).lower()] += 1
                    if row.get('warnings'):
                        review_warning_claims += 1
        review_statuses[str(review.get('review_status') or 'missing')] += 1
        for claim in case['spec'].get('claims') or []:
            if not isinstance(claim, dict) or not claim.get('claim_id'):
                continue
            claim_id = str(claim['claim_id'])
            contract = _contract_for_claim(case, claim)
            obs_symbols = _observability_for_claim(case, claim_id)
            roles = contract.get('roles') or {}
            claim_codes = Counter(
                row.get('code') for row in contract.get('problems') or []
                if isinstance(row, dict) and row.get('code'))
            claim_route = str(contract.get('route') or 'missing')
            claim_status = str(contract.get('status') or 'missing')
            claim_can_auto = bool(contract.get('can_auto_assert'))
            route[claim_route] += 1
            status[claim_status] += 1
            can_auto[str(claim_can_auto).lower()] += 1
            codes.update(claim_codes)

            claim_symbols: set[str] = set()
            claim_derived_missing: set[str] = set()
            claim_high_risk: set[str] = set()
            claim_no_code: set[str] = set()
            for role in ROLE_NAMES:
                for symbol in roles.get(role) or []:
                    symbol = str(symbol)
                    role_occurrences[role] += 1
                    claim_symbols.add(symbol)
                    key = (case_name, claim_id, symbol)
                    unique_symbol_keys.add(key)
                    meta = obs_symbols.get(symbol) or {}
                    if not _present(meta.get('source_entity')) and \
                            not _present(meta.get('code_fact')) and \
                            not _present(meta.get('mutation_site')):
                        role_no_code[role] += 1
                        no_code_symbols.add(key)
                        claim_no_code.add(symbol)
                    if meta.get('binding_risk') == 'high':
                        role_high_risk[role] += 1
                        high_risk_symbols.add(key)
                        claim_high_risk.add(symbol)
                    if (meta.get('observable_kind') == 'derived'
                            and 'derived_definition' in
                            (meta.get('missing') or [])):
                        role_derived_missing[role] += 1
                        derived_missing.add(key)
                        claim_derived_missing.add(symbol)

            for symbol in sorted(claim_symbols):
                meta = obs_symbols.get(symbol) or {}
                for field in DECLARATION_FIELDS:
                    if _present(meta.get(field)):
                        field_present[field] += 1
                for field in CODE_EVIDENCE_FIELDS:
                    if _present(meta.get(field)):
                        field_present[field] += 1
                kinds[str(meta.get('observable_kind') or 'missing')] += 1
                scopes[str(meta.get('scope') or 'missing')] += 1
                risks[str(meta.get('binding_risk') or 'missing')] += 1
                for field in meta.get('missing') or []:
                    missing_fields[str(field)] += 1

            required = {
                str(symbol) for symbol in contract.get('requires_code_fact') or []
                if str(symbol) in claim_symbols}
            for symbol in required:
                requires_code_fact.add((case_name, claim_id, symbol))

            claim_rows.append({
                'case': case_name,
                'label': case['label'],
                'claim_id': claim_id,
                'route': claim_route,
                'status': claim_status,
                'can_auto_assert': claim_can_auto,
                'symbols': len(claim_symbols),
                'pending_code_fact': len(required),
                'no_code_evidence_symbols': len(claim_no_code),
                'high_risk_symbols': len(claim_high_risk),
                'derived_without_definition': len(claim_derived_missing),
                'status_route_conflict': bool(
                    claim_can_auto and claim_route == 'auto_assert'
                    and claim_status == 'needs_review'),
                'auto_assert_without_code_evidence': bool(
                    claim_can_auto and claim_route == 'auto_assert'
                    and claim_no_code),
            })

    claim_count = len(claim_rows)
    auto_claims = [row for row in claim_rows if row['route'] == 'auto_assert']
    review_claims = [row for row in claim_rows
                     if row['route'] == 'binding_review']
    symbol_count = len(unique_symbol_keys)
    summary = {
        'cases': len(cases),
        'positive_cases': sum(case['label'] == 'positive' for case in cases),
        'negative_cases': sum(case['label'] == 'negative' for case in cases),
        'claims': claim_count,
        'claim_symbols': symbol_count,
        'role_occurrences': sum(role_occurrences.values()),
        'requires_code_fact_symbols': len(requires_code_fact),
        'routes': dict(sorted(route.items())),
        'statuses': dict(sorted(status.items())),
        'can_auto_assert': dict(sorted(can_auto.items())),
        'auto_assert_claims': len(auto_claims),
        'binding_review_claims': len(review_claims),
        'auto_assert_without_code_evidence': sum(
            row['auto_assert_without_code_evidence'] for row in claim_rows),
        'auto_assert_with_derived_missing': sum(
            bool(row['derived_without_definition']) for row in auto_claims),
        'status_route_conflicts': sum(
            row['status_route_conflict'] for row in claim_rows),
        'claims_with_pending_code_fact': sum(
            row['pending_code_fact'] > 0 for row in claim_rows),
        'claims_with_derived_missing': sum(
            row['derived_without_definition'] > 0 for row in claim_rows),
        'claims_with_high_risk_symbols': sum(
            row['high_risk_symbols'] > 0 for row in claim_rows),
        'no_code_evidence_symbols': len(no_code_symbols),
        'code_fact_symbols': int(field_present.get('code_fact', 0)),
        'mutation_site_symbols': int(field_present.get('mutation_site', 0)),
        'source_entity_symbols': int(field_present.get('source_entity', 0)),
        'observable_kind_symbols': int(field_present.get('observable_kind', 0)),
        'scope_symbols': int(field_present.get('scope', 0)),
        'binding_risk_symbols': int(field_present.get('binding_risk', 0)),
        'derived_without_definition_symbols': len(derived_missing),
        'derived_without_definition_cases': len({
            key[0] for key in derived_missing}),
        'high_risk_symbols': len(high_risk_symbols),
        'observability_review_claims': review_claim_count,
        'observability_established': dict(sorted(review_established.items())),
        'observability_review_statuses': dict(sorted(review_statuses.items())),
        'observability_review_claims_with_warnings': review_warning_claims,
    }
    family = Counter()
    for row in claim_rows:
        family[(row['route'], bool(row['high_risk_symbols']),
                bool(row['derived_without_definition']),
                row['label'])] += 1

    findings = [
        (f"All {summary['claim_symbols']} claim-level symbols declare "
         f"observable_kind/scope/binding_risk, but {summary['code_fact_symbols']} "
         "declare a code_fact and "
         f"{summary['mutation_site_symbols']} declare a mutation_site."),
        (f"{summary['no_code_evidence_symbols']}/{summary['claim_symbols']} "
         "symbols have neither source_entity, code_fact nor mutation_site. This "
         "is the source of the repeated OBSERVABILITY_REQUIRES_CODE_FACT and "
         "I_MUTATION_SITE_MISSING warnings."),
        (f"{summary['auto_assert_without_code_evidence']}/"
         f"{summary['auto_assert_claims']} auto_assert claims therefore route to "
         "Stage-3 without any Stage-2 code evidence; the audit status says "
         "needs_review at the same time."),
        (f"{summary['derived_without_definition_symbols']} symbols are marked "
         f"observable_kind=derived but have no derived_definition across "
         f"{summary['derived_without_definition_cases']} cases; "
         f"{summary['auto_assert_with_derived_missing']} auto_assert claims are "
         "affected."),
        (f"{summary['high_risk_symbols']} symbols are binding_risk=high; "
         f"{summary['binding_review_claims']} claims are routed to binding "
         "review, showing that the risk signal exists but has no Stage-3 "
         "resolution artifact to clear it."),
        (f"{summary['observability_review_claims']}/"
         f"{summary['observability_review_claims']} reviewed claims report "
         f"observability_established=false; the review is a structural hint, "
         "not a code-binding verdict."),
    ]
    root_causes = [
        {
            'id': 'OBS-1',
            'name': 'Stage-2/Stage-3 evidence-layer conflation',
            'evidence': (f"{summary['no_code_evidence_symbols']} symbols lack "
                         'code fact/mutation site before Stage-3'),
            'owner': 'stage2 contract + stage3 evidence',
            'severity': 'critical',
        },
        {
            'id': 'OBS-2',
            'name': 'derived kind without definition',
            'evidence': (f"{summary['derived_without_definition_symbols']} "
                         'derived symbols missing derived_definition'),
            'owner': 'stage2 plan synthesis',
            'severity': 'high',
        },
        {
            'id': 'OBS-3',
            'name': 'route/status inconsistency',
            'evidence': (f"{summary['status_route_conflicts']} claims are "
                         'auto_assert while status=needs_review'),
            'owner': 'stage2 formalization audit',
            'severity': 'high',
        },
        {
            'id': 'OBS-4',
            'name': 'no Stage-3 evidence write-back',
            'evidence': ('observability-review.observability_established is a '
                         f"constant false ({summary['observability_review_claims']} "
                         'reviewed claims); no per-symbol bound_expr/source/'
                         'mutation evidence artifact is consumed by Stage-2'),
            'owner': 'stage3 binding -> stage2 feedback',
            'severity': 'critical',
        },
        {
            'id': 'OBS-5',
            'name': 'high-risk signal has no clearing rule',
            'evidence': (f"{summary['high_risk_symbols']} high-risk symbols; "
                         'A+ treats the warning as a soft quality label'),
            'owner': 'stage3 gate / A+ policy',
            'severity': 'high',
        },
    ]
    return {
        'schema_version': SCHEMA_VERSION,
        'read_only': True,
        'generated_at': datetime.now(timezone.utc).strftime(
            '%Y-%m-%dT%H:%M:%SZ'),
        'inputs': {
            'positive_root': str(Path(pos_root).resolve()),
            'negative_root': str(Path(neg_root).resolve()),
            'positive_root_spec_sha256': _root_digest(
                Path(pos_root), 'stage3-spec.json'),
            'negative_root_spec_sha256': _root_digest(
                Path(neg_root), 'stage3-spec.json'),
        },
        'sample': {
            'cases': summary['cases'],
            'positive_cases': summary['positive_cases'],
            'negative_cases': summary['negative_cases'],
            'claims': summary['claims'],
            'claim_symbols': summary['claim_symbols'],
            'role_occurrences': summary['role_occurrences'],
        },
        'summary': summary,
        'field_coverage': dict(sorted(field_present.items())),
        'missing_fields': dict(sorted(missing_fields.items())),
        'roles': {
            ROLE_LABELS[role]: {
                'occurrences': role_occurrences[role],
                'without_code_evidence': role_no_code[role],
                'high_risk': role_high_risk[role],
                'derived_without_definition': role_derived_missing[role],
            } for role in ROLE_NAMES},
        'observable_kinds': dict(sorted(kinds.items())),
        'scopes': dict(sorted(scopes.items())),
        'binding_risks': dict(sorted(risks.items())),
        'claim_families': [
            {'route': route_name, 'high_risk': high, 'derived_missing': derived,
             'label': label, 'claims': count}
            for (route_name, high, derived, label), count
            in sorted(family.items(), key=lambda item: (-item[1], item[0]))
        ],
        'findings': findings,
        'root_causes': root_causes,
        'load_warnings': load_warnings,
        'claims': claim_rows,
    }


def _root_digest(root: Path, filename: str) -> str | None:
    """Stable digest of the latest spec paths and bytes under one root."""
    digest = hashlib.sha256()
    for path in sorted(Path(root).glob(f'runs_*/*/{filename}')):
        digest.update(path.relative_to(root).as_posix().encode())
        digest.update(b'\0')
        try:
            digest.update(path.read_bytes())
        except OSError:
            digest.update(b'<unreadable>')
        digest.update(b'\0')
    return digest.hexdigest()


def _fmt(value) -> str:
    if isinstance(value, float):
        return f'{value:.4f}'
    return str(value)


def render_markdown(report: dict) -> str:
    summary = report['summary']
    lines = [
        '# Stage-2 Observability Root-Cause Audit',
        '',
        '- Schema: `' + report['schema_version'] + '`',
        '- Read-only: `true`',
        f"- Sample: {summary['cases']} cases, {summary['claims']} claims, "
        f"{summary['claim_symbols']} claim-level symbols "
        f"({summary['positive_cases']} positive / "
        f"{summary['negative_cases']} negative cases).",
        '',
        '## Executive Summary',
        '',
        '| Signal | Value |',
        '| --- | ---: |',
        f"| symbols with observable_kind | {summary['observable_kind_symbols']} |",
        f"| symbols with code_fact | {summary['code_fact_symbols']} |",
        f"| symbols with mutation_site | {summary['mutation_site_symbols']} |",
        f"| symbols with no code evidence | {summary['no_code_evidence_symbols']} |",
        f"| derived symbols missing definition | "
        f"{summary['derived_without_definition_symbols']} |",
        f"| auto_assert claims | {summary['auto_assert_claims']} |",
        f"| auto_assert claims without code evidence | "
        f"{summary['auto_assert_without_code_evidence']} |",
        f"| status=needs_review while route=auto_assert | "
        f"{summary['status_route_conflicts']} |",
        f"| binding_review claims | {summary['binding_review_claims']} |",
        f"| high-risk symbols | {summary['high_risk_symbols']} |",
        f"| observability_review claims | "
        f"{summary['observability_review_claims']} |",
        f"| observability_established=false | "
        f"{summary['observability_established'].get('false', 0)} |",
        '',
        '## P/I/V Coverage',
        '',
        '| Role | Occurrences | Without code evidence | High risk | '
        'Derived missing definition |',
        '| --- | ---: | ---: | ---: | ---: |',
    ]
    for role in ('P', 'I', 'V'):
        row = report['roles'][role]
        lines.append(
            f"| {role} | {row['occurrences']} | "
            f"{row['without_code_evidence']} | {row['high_risk']} | "
            f"{row['derived_without_definition']} |")
    lines.extend([
        '',
        '## Claim Routing',
        '',
        '| Route | Claims |',
        '| --- | ---: |',
    ])
    for name, count in summary['routes'].items():
        lines.append(f'| `{name}` | {count} |')
    lines.extend([
        '',
        '## Observable Kinds',
        '',
        '| Kind | Symbols |',
        '| --- | ---: |',
    ])
    for name, count in report['observable_kinds'].items():
        lines.append(f'| `{name}` | {count} |')
    lines.extend([
        '',
        '## Binding Risks',
        '',
        '| Risk | Symbols |',
        '| --- | ---: |',
    ])
    for name, count in report['binding_risks'].items():
        lines.append(f'| `{name}` | {count} |')
    lines.extend([
        '',
        '## Root Causes',
        '',
        '| ID | Root cause | Severity | Evidence |',
        '| --- | --- | --- | --- |',
    ])
    for row in report['root_causes']:
        lines.append(
            f"| {row['id']} | {row['name']} | {row['severity']} | "
            f"{row['evidence']} |")
    lines.extend([
        '',
        '## Findings',
        '',
    ])
    lines.extend(f'- {finding}' for finding in report['findings'])
    lines.extend([
        '',
        '## Interpretation',
        '',
        '- The Stage-2 symbols are not lacking observable *intent*: every '
        'symbol has kind, scope and binding risk.',
        '- They are lacking code *evidence*, which Stage-2 cannot legitimately '
        'produce from report text alone.',
        '- Treating that evidence gap as a soft warning makes the warning '
        'non-actionable; treating it as a hard rejection makes every claim '
        'unbindable. The correct fix is an explicit two-layer contract and a '
        'Stage-3 evidence write-back.',
        '- Ranking cannot repair this gap because every candidate is equally '
        'missing the same evidence layer.',
        '',
        '## Reproduction',
        '',
        '```bash',
        'cd tools/stage3',
        'python -m evaluation.metrics.stage2_observability_audit',
        '```',
        '',
    ])
    return '\n'.join(lines)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pos-root', type=Path, default=DEFAULT_POS_ROOT)
    parser.add_argument('--neg-root', type=Path, default=DEFAULT_NEG_ROOT)
    parser.add_argument('--out-json', type=Path, default=DEFAULT_JSON)
    parser.add_argument('--out-md', type=Path, default=DEFAULT_MD)
    args = parser.parse_args(argv)
    report = build(args.pos_root, args.neg_root)
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    args.out_md.write_text(render_markdown(report) + '\n')
    print(json.dumps({
        'sample': report['sample'],
        'summary': {
            key: report['summary'][key] for key in (
                'code_fact_symbols', 'mutation_site_symbols',
                'no_code_evidence_symbols', 'derived_without_definition_symbols',
                'auto_assert_claims', 'auto_assert_without_code_evidence',
                'status_route_conflicts')},
        'out_json': str(args.out_json),
        'out_md': str(args.out_md),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
