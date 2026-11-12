import json
import tempfile
import unittest
from pathlib import Path

from cli.full_metrics import analyze


class FullMetricsTest(unittest.TestCase):
    def test_analyze_computes_four_metrics(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            s2 = root / 'summary.json'
            s2.write_text(json.dumps({
                'n_reports': 100, 'at_least_one_candidate': 80,
                'complete_reports': 50,
            }))
            pos = root / 'eval.json'
            pos.write_text(json.dumps({
                'cases': [
                    {'status': 'done', 'claims': 10, 'reproduced': 5,
                     'verdicts': ['violation_reproduced'] * 5
                     + ['violation_not_reproduced'] * 2
                     + ['inconclusive'] * 3},
                    {'status': 'done', 'claims': 10, 'reproduced': 0,
                     'verdicts': ['partial_binding'] * 10},
                ],
            }))
            neg = root / 'neg.json'
            neg.write_text(json.dumps([
                {'verdict': 'violation_not_reproduced'},
                {'verdict': 'violation_reproduced'},
            ]))
            metrics = analyze(s2, pos, neg)
            # completion
            self.assertAlmostEqual(metrics['completion']['stage2_candidate_rate'], 0.8)
            self.assertAlmostEqual(metrics['completion']['stage2_complete_rate'], 0.5)
            # recall: tp=5, total=20, verifiable=5+2+3=10
            self.assertAlmostEqual(metrics['recall']['full'], 0.25)
            self.assertAlmostEqual(metrics['recall']['verifiable'], 0.5)
            # precision: tp=5, fp=1
            self.assertAlmostEqual(metrics['precision']['precision'], 5 / 6)
            # f1 full = 2*P*R/(P+R)
            p, r = 5 / 6, 0.25
            self.assertAlmostEqual(metrics['f1']['full'], 2 * p * r / (p + r))


if __name__ == '__main__':
    unittest.main()
