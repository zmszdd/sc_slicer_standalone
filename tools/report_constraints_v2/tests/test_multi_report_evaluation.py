"""Regression of saved pilot artifacts/ratings; not independent semantic scoring."""
import importlib.util
from pathlib import Path
import unittest

PATH = Path(__file__).resolve().parents[1] / 'evaluation/multi_report_01/evaluate.py'
spec = importlib.util.spec_from_file_location('multi_report_eval', PATH)
evaluation = importlib.util.module_from_spec(spec)
spec.loader.exec_module(evaluation)


class PilotReplay(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.value = evaluation.evaluate()
        cls.rows = {row['id']: row for row in cls.value['results']}

    def test_denominator_and_no_evaluation_calls(self):
        self.assertEqual(self.value['distinct_reports'], 5)
        self.assertEqual(self.value['actual_model_invocations'], 10)
        self.assertEqual(self.value['evaluation_model_invocations'], 0)

    def test_partial_not_counted_as_full_I_pass(self):
        self.assertEqual(self.value['metric_counts']['formal_I'],
                         {'pass': 2, 'partial': 1, 'fail': 2, 'not_evaluable': 0})
        self.assertEqual(self.value['preliminary_formal_I_pass_percentage'], 40)

    def test_general_accuracy_not_inferred(self):
        self.assertIsNone(self.value['general_accuracy_percentage'])
        self.assertIn('not_user_confirmed', self.value['reference_status'])

    def test_formal_completion_is_separate(self):
        self.assertEqual(self.value['formal_pipeline_completed_count'], 2)
        self.assertEqual(self.value['candidate_checks_passed_count'], 0)
        self.assertEqual(self.value['complete_semantic_pass_count'], 0)

    def test_narrow_I_queries(self):
        for case in ('kinetiq_pause', 'merkl_callback'):
            self.assertEqual(self.rows[case]['narrow_I_diagnostic']['status'], 'unsat')
        for case in ('sukuk_authority', 'gte_zero_cost'):
            self.assertEqual(self.rows[case]['narrow_I_diagnostic']['status'], 'sat')

    def test_Hybra_types_not_silently_ignored(self):
        row = self.rows['hybra_maturity']
        self.assertEqual(row['narrow_I_diagnostic']['status'], 'type_error')
        self.assertTrue(row['additional_formula_type_errors'])
        self.assertIsNone(row['full_pipeline_replay'])

    def test_rejections_and_grounding_replay(self):
        self.assertTrue(all(row['elements_grounding_replayed'] for row in self.rows.values()))
        self.assertEqual(self.rows['sukuk_authority']['formal_validation_error_replayed'],
                         'invalid subformula sources')
        self.assertEqual(self.rows['merkl_callback']['additional_invalid_symbol_names'],
                         ['transferred_toSend'])


if __name__ == '__main__':
    unittest.main()
