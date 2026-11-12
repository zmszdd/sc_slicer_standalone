import unittest

from lib.differential import compute_queries


class DifferentialTest(unittest.TestCase):
    def test_violation_reproduced(self):
        queries = compute_queries(
            {'exploit_test': 'test_double_withdraw'},
            {'status': 'Success', 'reason': None},
            {'status': 'Failure', 'reason': 'panic: assertion failed (0x01)'},
        )
        self.assertEqual(queries['P_and_T'], 'sat')
        self.assertEqual(queries['P_and_T_and_not_I'], 'sat')
        self.assertEqual(queries['P_and_T_and_V'], 'sat')

    def test_preconditions_infeasible(self):
        queries = compute_queries(
            {'exploit_test': 't'},
            {'status': 'Success', 'reason': None},
            {'status': 'Failure', 'reason': 'revert: stage3:P failed'},
        )
        self.assertEqual(queries['P_and_T'], 'unsat')

    def test_precondition_unwitnessed_routes_to_unsat(self):
        queries = compute_queries(
            {'exploit_test': 't'},
            {'status': 'Success', 'reason': None},
            {'status': 'Failure',
             'reason': 'revert: stage3:precondition_unwitnessed'},
        )
        self.assertEqual(queries['P_and_T'], 'unsat')
        self.assertEqual(queries['P_and_T_and_not_I'], 'unknown')

    def test_reference_patch_business_revert_counts_as_violation(self):
        queries = compute_queries(
            {'exploit_test': 't'},
            {'status': 'Success', 'reason': None},
            {'status': 'Failure', 'reason': 'already initialized'},
            reference_patch=True,
        )
        self.assertEqual(queries['P_and_T'], 'sat')
        self.assertEqual(queries['P_and_T_and_not_I'], 'sat')
        self.assertEqual(queries['P_and_T_and_V'], 'sat')

    def test_business_revert_without_reference_patch_stays_unknown(self):
        queries = compute_queries(
            {'exploit_test': 't'},
            {'status': 'Success', 'reason': None},
            {'status': 'Failure', 'reason': 'already initialized'},
        )
        self.assertEqual(queries['P_and_T'], 'unknown')

    def test_not_reproduced(self):
        queries = compute_queries(
            {'exploit_test': 't'},
            {'status': 'Success', 'reason': None},
            {'status': 'Success', 'reason': None},
        )
        self.assertEqual(queries['P_and_T'], 'sat')
        self.assertEqual(queries['P_and_T_and_V'], 'unsat')

    def test_original_fails_patched_passes_is_preconditions_infeasible(self):
        queries = compute_queries(
            {'exploit_test': 't'},
            {'status': 'Failure', 'reason': 'revert: fee tier out of bounds'},
            {'status': 'Success', 'reason': None},
        )
        self.assertEqual(queries['P_and_T'], 'unsat')
        self.assertEqual(queries['P_and_T_and_not_I'], 'unknown')

    def test_panic_only_reason_counts_as_invariant_failure(self):
        queries = compute_queries(
            {'exploit_test': 't'},
            {'status': 'Success', 'reason': None},
            {'status': 'Failure', 'reason': 'Panic(0x01)'},
        )
        self.assertEqual(queries['P_and_T_and_not_I'], 'sat')

    def test_halt_rewrite_counts_as_violation(self):
        queries = compute_queries(
            {'exploit_test': 't'},
            {'status': 'Success', 'reason': None},
            {'status': 'Failure', 'reason': 'revert: stage3:halt'},
        )
        self.assertEqual(queries['P_and_T'], 'sat')
        self.assertEqual(queries['P_and_T_and_not_I'], 'sat')
        self.assertEqual(queries['P_and_T_and_V'], 'sat')


if __name__ == '__main__':
    unittest.main()
