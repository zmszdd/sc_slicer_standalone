import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from evaluation.metrics import stage2_observability_preflight as preflight


class Stage2ObservabilityPreflightTest(unittest.TestCase):
    def test_selects_only_claims_with_visible_symbols(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            stage2 = root / 'stage2'
            flatten = root / 'flatten' / 'case_a'
            stage2 = root / 'stage2' / 'case_a'
            stage2.mkdir(parents=True)
            flatten.mkdir(parents=True)
            (flatten / 'contract.flattened.t.sol').write_text('contract T {}')
            claims = []
            for claim_id in ('observable', 'semantic_only'):
                claims.append({
                    'claim_id': claim_id,
                    'formalization_status': 'formalized_candidate',
                    'binding_contract': {'symbols': [
                        {'symbol': claim_id + '_symbol', 'appears_in': ['P']},
                    ]},
                })
            (stage2 / 'stage3-spec.json').write_text(json.dumps({
                'claims': claims,
            }))
            (stage2 / 'constraints.json').write_text('{}')
            (stage2 / 'formalization.json').write_text(json.dumps({
                'claims': [{'id': row['claim_id']} for row in claims],
            }))
            (stage2 / 'provenance.json').write_text(json.dumps({
                'continue_on_review': True,
            }))

            def fake_build_contract(_stage2_dir, claim_id, _src):
                route = 'visible' if claim_id == 'observable' else 'unobservable'
                return {'symbols': {claim_id + '_symbol': {
                    'roles': ['P'],
                    'candidates': [{
                        'visible_at_injection': route == 'visible',
                        'source_grounded': False,
                    }] if route == 'visible' else [],
                }}}

            with patch.object(preflight.observable_ir, 'build_contract',
                              side_effect=fake_build_contract):
                report = preflight.build(stage2.parents[0], flatten.parent,
                                         root / 'out', cases=['case_a'])
            selected = report['cases'][0]['selected_claim_ids']
            self.assertEqual(selected, ['observable'])
            out_spec = json.loads((root / 'out' / 'case_a'
                                   / 'stage3-spec.json').read_text())
            self.assertEqual([row['claim_id'] for row in out_spec['claims']],
                             selected)


if __name__ == '__main__':
    unittest.main()
