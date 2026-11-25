import unittest

from lib.witness_protocol import classify


class WitnessProtocolTest(unittest.TestCase):
    def test_compile_failure_is_not_poc_failure(self):
        record = classify(
            'c1', compile_error={'original': 'Error: Undeclared identifier x'},
            original_result=None, patched_result=None)
        self.assertEqual(record['status'], 'unavailable')
        self.assertEqual(record['failure_code'], 'poc_compile_failed')

    def test_missing_test_is_explicit(self):
        record = classify('c1', test_missing=True)
        self.assertEqual(record['failure_code'], 'poc_test_missing')

    def test_unbound_precondition_is_distinct_from_revert(self):
        record = classify(
            'c1', original_result={'status': 'Success'},
            patched_result={'status': 'Success'}, invariant_unbound=['p'])
        self.assertEqual(record['status'], 'unavailable')
        self.assertEqual(record['failure_code'], 'precondition_unobservable')

    def test_original_revert_records_reason(self):
        record = classify(
            'c1', original_result={'status': 'Failure',
                                   'reason': 'EvmError: Revert'},
            patched_result={'status': 'Success'})
        self.assertEqual(record['failure_code'], 'poc_revert_before_effect')
        self.assertEqual(record['revert_reason'], 'EvmError: Revert')

    def test_snapshot_false_is_precondition_false(self):
        record = classify(
            'c1', original_result={'status': 'Success'},
            patched_result={'status': 'Failure',
                            'reason': 'stage3:precondition_unwitnessed'},
            precondition_failure='snapshot_unwitnessed')
        self.assertEqual(record['failure_code'], 'precondition_false')

    def test_witnessed_violation(self):
        record = classify(
            'c1', original_result={'status': 'Success'},
            patched_result={'status': 'Failure', 'reason': 'stage3:I'},
            effect_result={'status': 'Success'},
            queries={'P_and_T_and_not_I': 'sat', 'P_and_T_and_V': 'sat'})
        self.assertEqual(record['status'], 'witnessed')
        self.assertTrue(record['effect_witnessed'])
        self.assertTrue(record['invariant_contradicted'])
        self.assertTrue(record['action_witnessed'])
        self.assertTrue(record['effect_after_action'])
        self.assertEqual(record['evidence_level'], 'complete')

    def test_action_without_effect_is_not_a_complete_witness(self):
        record = classify(
            'c1', original_result={'status': 'Success'},
            patched_result={'status': 'Failure', 'reason': 'stage3:I'},
            effect_result={'status': 'Failure', 'reason': 'assertion failed'},
            queries={'P_and_T_and_not_I': 'sat', 'P_and_T_and_V': 'unsat'})
        self.assertEqual(record['status'], 'failed')
        self.assertEqual(record['failure_code'], 'effect_not_witnessed')
        self.assertTrue(record['action_witnessed'])
        self.assertFalse(record['effect_after_action'])
        self.assertEqual(record['evidence_level'], 'partial')

    def test_checkpoint_evidence_records_injection_and_snapshots(self):
        binding = {
            'probe': {'contract': 'Harness', 'exploit_test': 'test_poc'},
            'patch': {'file': 'C.sol', 'contract': 'Vault',
                      'functions': [{'name': 'withdraw'}]},
            'bindings': {
                'p': {'solidity_expr': 'ready', 'checkpoint': 'before',
                      'snapshot_after': 'setup();'},
                'i': {'solidity_expr': 'totalAssets() == shares',
                      'checkpoint': 'after'},
            },
        }
        record = classify('c1', original_result={'status': 'Success'},
                          patched_result={'status': 'Success'},
                          queries={'P_and_T_and_not_I': 'unsat'},
                          binding=binding)
        evidence = record['checkpoint_evidence']
        self.assertEqual(evidence['injection']['contract'], 'Vault')
        self.assertEqual(evidence['symbols']['p']['snapshot_after'], 'setup();')
        self.assertTrue(evidence['symbols']['i']['bound'])


if __name__ == '__main__':
    unittest.main()
