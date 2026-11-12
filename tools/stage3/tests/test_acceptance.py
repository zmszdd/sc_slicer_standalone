import unittest

from cli.stage3_acceptance import evaluate


class AcceptanceTest(unittest.TestCase):
    def test_evaluate_flattens_verdicts(self):
        summary = {
            'cases': [
                {'status': 'done', 'claims': 2,
                 'verdicts': ['violation_reproduced', 'violation_not_reproduced']},
                {'status': 'done', 'claims': 1,
                 'verdicts': ['partial_binding']},
                {'status': 'no_stage2_run', 'claims': 5, 'verdicts': []},
            ],
        }
        metrics = evaluate(summary)
        self.assertEqual(metrics['total_cases'], 2)
        self.assertEqual(metrics['total_claims'], 3)
        self.assertEqual(metrics['reproduced'], 1)
        self.assertEqual(metrics['reproduction_rate'], 1 / 3)
        self.assertEqual(metrics['terminal_rate'], 2 / 3)
        self.assertEqual(metrics['binding_blocked'], 0)

    def test_binding_blocked_counts_missing_verdicts(self):
        summary = {
            'cases': [
                {'status': 'done', 'claims': 4,
                 'verdicts': ['violation_reproduced']},
            ],
        }
        metrics = evaluate(summary)
        self.assertEqual(metrics['verdicts'], 1)
        self.assertEqual(metrics['binding_blocked'], 3)


if __name__ == '__main__':
    unittest.main()
