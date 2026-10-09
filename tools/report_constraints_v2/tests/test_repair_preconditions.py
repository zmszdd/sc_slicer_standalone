"""Offline controls for audit-guided P-only repair."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from lib.ingest import build_catalog, hydrate_elements
from cli import preconditions as repair
from lib.semantic_core import validate_elements
from tests.test_evidence_ids import TEXT, id_inputs


class PreconditionRepairTests(unittest.TestCase):
    def setUp(self):
        self.elements, _ = id_inputs()
        self.catalog = build_catalog(TEXT)
        self.assumption = next(row for row in self.elements['statements']
                               if row['kind'] == 'assumption')
        self.pids = [row['id'] for row in self.elements['statements']
                     if row['kind'] in ('precondition', 'assumption')]
        self.audit = {'schema_version': 'precondition-support-review/5',
                      'source_sha256': self.catalog['source_sha256'],
                      'items': [{'statement_id': ident,
                                 'evidence_verdict': 'supported',
                                 'role_verdict': ('contains_action_or_result'
                                                  if ident == self.assumption['id']
                                                  else 'before_condition')}
                                for ident in self.pids],
                      'needs_review_ids': [self.assumption['id']]}

    def test_audit_must_cover_all_p_inputs_and_source(self):
        self.assertEqual(repair.check_audit(self.audit, self.elements, self.catalog),
                         [self.assumption['id']])
        with self.assertRaises(ValueError):
            repair.check_audit({**self.audit, 'items': self.audit['items'][:1]},
                               self.elements, self.catalog)
        with self.assertRaises(ValueError):
            repair.check_audit({**self.audit, 'source_sha256': 'bad'},
                               self.elements, self.catalog)

    def test_only_flagged_p_can_be_removed(self):
        result = repair.apply_repairs(self.elements, {
            'schema_version': 'precondition-repair/1',
            'repairs': [{'statement_id': self.assumption['id'], 'operation': 'remove',
                         'reason': 'Not a before-condition.'}]}, [self.assumption['id']])
        self.assertEqual(result['scope'], self.elements['scope'])
        self.assertEqual(result['entities'], self.elements['entities'])
        self.assertEqual(result['attack_steps'], self.elements['attack_steps'])
        self.assertEqual(result['ambiguities'], self.elements['ambiguities'])
        self.assertEqual([row for row in result['statements'] if row['id'] != self.assumption['id']],
                         [row for row in self.elements['statements']
                          if row['id'] != self.assumption['id']])
        validate_elements(hydrate_elements(result, self.catalog, TEXT), TEXT)

    def test_replacement_identity_and_all_p_removed_rejected(self):
        bad = copy.deepcopy(self.assumption)
        bad['kind'] = 'impact'
        with self.assertRaisesRegex(ValueError, 'identity or kind'):
            repair.apply_repairs(self.elements, {
                'schema_version': 'precondition-repair/1',
                'repairs': [{'statement_id': self.assumption['id'],
                             'operation': 'replace', 'reason': 'bad',
                             'replacement': bad}]}, [self.assumption['id']])
        with self.assertRaisesRegex(ValueError, 'every P input'):
            repair.apply_repairs(self.elements, {
                'schema_version': 'precondition-repair/1',
                'repairs': [{'statement_id': ident, 'operation': 'remove', 'reason': 'bad'}
                            for ident in self.pids]}, self.pids)

    def test_main_produces_reauditable_candidate_without_model_network(self):
        with tempfile.TemporaryDirectory() as root:
            run_dir = Path(root) / 'run'; run_dir.mkdir()
            audit_dir = Path(root) / 'audit'; audit_dir.mkdir()
            output = Path(root) / 'repair'
            (run_dir / 'elements-ids.json').write_text(json.dumps(self.elements))
            (run_dir / 'evidence-catalog.json').write_text(json.dumps(self.catalog))
            (run_dir / 'extraction-input.txt').write_text(TEXT)
            (audit_dir / 'support-audit.json').write_text(json.dumps(self.audit))
            response = {'schema_version': 'precondition-repair/1',
                        'repairs': [{'statement_id': self.assumption['id'],
                                     'operation': 'remove', 'reason': 'not a prior condition'}]}
            argv = ['preconditions.py', '--run-dir', str(run_dir),
                    '--audit-dir', str(audit_dir), '--output', str(output),
                    '--allow-report-upload', '--model', 'synthetic_control']
            with patch('sys.argv', argv), patch.object(repair.r, 'extract', return_value=response):
                repair.repair_main()
            candidate = json.loads((output / 'elements-ids.json').read_text())
            self.assertEqual(len(candidate['statements']), len(self.elements['statements']) - 1)
            review = json.loads((output / 'repair-review.json').read_text())
            self.assertTrue(review['needs_reaudit'])
            self.assertTrue(review['coverage_requires_review'])
            self.assertFalse(review['is_independent_gold'])


if __name__ == '__main__':
    unittest.main()
