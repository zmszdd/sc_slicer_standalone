import json
import tempfile
import unittest
from pathlib import Path

from evaluation.metrics import label_review_gate
from lib import execution_gate, mainline_protocol, observable_ir
from lib import observable_recipes


class LabelReviewGateTest(unittest.TestCase):
    def _summary(self, *, case: str, verdict: str) -> dict:
        return {
            'case': case,
            'claim_id': 'claim_1',
            'run_id': case + '__run_1',
            'consistency_verdict': verdict,
            'artifact_fingerprint': {
                'schema_version': 'stage3-artifact-fingerprint/1',
                'mainline_protocol': mainline_protocol.current(),
                'protocol_versions': {
                    'execution_gate': execution_gate.SCHEMA_VERSION,
                    'observable_ir': observable_ir.SCHEMA_VERSION,
                    'observable_recipes': observable_recipes.SCHEMA_VERSION,
                },
            },
            'execution_gate': {
                'metric_eligibility': {
                    'consistency': True,
                    'vulnerability': True,
                },
            },
        }

    def test_terminal_violation_on_frozen_negative_is_quarantined(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sample = root / 'sample.json'
            sample.write_text(json.dumps({
                'negative_cases': ['Case__neg', 'Case__ok'],
            }))
            (root / 'Case__neg__run_1').mkdir()
            (root / 'Case__neg__run_1' / 'stage3-summary.json').write_text(
                json.dumps(self._summary(
                    case='Case__neg', verdict='violation_reproduced')))
            (root / 'Case__ok__run_1').mkdir()
            (root / 'Case__ok__run_1' / 'stage3-summary.json').write_text(
                json.dumps(self._summary(
                    case='Case__ok', verdict='partial_binding')))
            report = label_review_gate.build(sample, [root])
            self.assertEqual(report['count'], 1)
            self.assertEqual(report['cases'][0]['case'], 'Case__neg')
            self.assertEqual(report['cases'][0]['status'],
                             'label_review_required')
            self.assertIn('label-review', label_review_gate.markdown(report))


if __name__ == '__main__':
    unittest.main()
