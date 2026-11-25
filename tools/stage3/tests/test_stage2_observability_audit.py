import json
import sys
import tempfile
import unittest
from pathlib import Path

STAGE3 = Path(__file__).resolve().parents[1]
METRICS = STAGE3 / 'evaluation' / 'metrics'
sys.path.insert(0, str(STAGE3))
sys.path.insert(0, str(METRICS))

import stage2_observability_audit as audit  # noqa: E402


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n')


def _case(root: Path, case: str, *, route: str = 'auto_assert',
          can_auto: bool = True, high_risk: bool = False,
          derived_missing: bool = True) -> None:
    run = root / 'runs_01' / case
    symbols = {
        'c1_safe_after': {
            'observable_kind': 'state',
            'scope': 'business',
            'receiver': None,
            'contract_type': None,
            'binding_risk': 'low',
            'missing': [],
        },
        'c1_expected_after': {
            'observable_kind': 'derived' if derived_missing else 'getter',
            'scope': 'cross_contract',
            'receiver': 'token',
            'contract_type': 'Token',
            'binding_risk': 'high' if high_risk else 'medium',
            'missing': ['derived_definition'] if derived_missing else [],
        },
    }
    claim_id = 'impact_claim_' + case.lower()
    contract = {
        'claim_id': claim_id,
        'status': 'needs_review' if can_auto else 'ready',
        'route': route,
        'can_auto_assert': can_auto,
        'roles': {
            'preconditions': ['c1_expected_after'],
            'safety': ['c1_safe_after', 'c1_expected_after'],
            'effects': ['c1_safe_after', 'c1_expected_after'],
        },
        'requires_code_fact': ['c1_safe_after', 'c1_expected_after'],
        'problems': [],
    }
    spec = {
        'schema_version': 'stage3-semantic-spec/1',
        'claims': [{'claim_id': claim_id,
                    'formalization_status': 'formalized_candidate',
                    'formalization_contract': contract}],
    }
    _write_json(run / 'stage3-spec.json', spec)
    _write_json(run / 'observability-contract.json', {
        'schema_version': 'observability-contract/1',
        'claims': {claim_id: {
            'schema_version': 'observability-contract/1',
            'contract_present': True,
            'symbols': symbols,
            'high_risk': ['c1_expected_after'] if high_risk else [],
        }},
    })
    _write_json(run / 'observability-review.json', {
        'schema_version': 'observability-review/1',
        'review_status': 'needs_review',
        'observability_established': False,
        'claims': [{'claim_id': claim_id, 'warnings': ['structural hint']}],
    })
    _write_json(run / 'formalization-contract.json', {
        'schema_version': 'stage2-formalization-contract/2',
        'claims': {claim_id: contract},
    })


class Stage2ObservabilityAuditTest(unittest.TestCase):
    def test_counts_missing_code_evidence_and_derived_definitions(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pos, neg = root / 'pos', root / 'neg'
            _case(pos, 'CaseA')
            _case(neg, 'CaseB', route='binding_review', can_auto=False,
                  high_risk=True, derived_missing=False)
            report = audit.build(pos, neg)

        summary = report['summary']
        self.assertEqual(report['sample']['cases'], 2)
        self.assertEqual(report['sample']['claims'], 2)
        self.assertEqual(report['sample']['claim_symbols'], 4)
        self.assertEqual(report['sample']['role_occurrences'], 10)
        self.assertEqual(summary['code_fact_symbols'], 0)
        self.assertEqual(summary['mutation_site_symbols'], 0)
        self.assertEqual(summary['no_code_evidence_symbols'], 4)
        self.assertEqual(summary['derived_without_definition_symbols'], 1)
        self.assertEqual(summary['auto_assert_claims'], 1)
        self.assertEqual(summary['auto_assert_without_code_evidence'], 1)
        self.assertEqual(summary['status_route_conflicts'], 1)
        self.assertEqual(summary['binding_review_claims'], 1)
        self.assertEqual(summary['high_risk_symbols'], 1)
        self.assertEqual(summary['observability_review_claims'], 2)
        self.assertEqual(summary['observability_established'], {'false': 2})
        self.assertEqual(summary['observability_review_claims_with_warnings'], 2)

    def test_duplicate_case_is_counted_once(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pos, neg = root / 'pos', root / 'neg'
            _case(pos, 'SameCase')
            _case(neg, 'SameCase', route='binding_review', can_auto=False)
            report = audit.build(pos, neg)

        self.assertEqual(report['sample']['cases'], 1)
        self.assertEqual(report['sample']['claims'], 1)
        self.assertTrue(report['load_warnings'])

    def test_markdown_exposes_root_causes_and_reproduction(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pos, neg = root / 'pos', root / 'neg'
            _case(pos, 'CaseA')
            text = audit.render_markdown(audit.build(pos, neg))

        self.assertIn('Stage-2 Observability Root-Cause Audit', text)
        self.assertIn('OBS-1', text)
        self.assertIn('auto_assert claims without code evidence', text)
        self.assertIn('stage2_observability_audit', text)


if __name__ == '__main__':
    unittest.main()
