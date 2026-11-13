import unittest

from lib.forge_runner import first_failure_reason, test_result, _no_tests_found


class NoTestsDetectionTest(unittest.TestCase):
    def test_no_tests_found_message(self):
        self.assertTrue(_no_tests_found(
            'No tests found in project! Forge looks for functions that '
            'start with `test`'))
        self.assertTrue(_no_tests_found('No tests found'))
        self.assertFalse(_no_tests_found(''))
        self.assertFalse(_no_tests_found('{"test_results": {}}'))


class ForgeRunnerTest(unittest.TestCase):
    def test_first_failure_reason_reports_setup(self):
        parsed = {
            'src/Contract.sol:C4PoC': {
                'test_results': {
                    'setUp()': {'status': 'Failure',
                                'reason': 'vm.readFile: path not allowed'},
                },
            },
        }
        self.assertEqual(
            first_failure_reason(parsed),
            'setUp(): vm.readFile: path not allowed',
        )

    def test_first_failure_reason_none_when_all_pass(self):
        parsed = {'s': {'test_results': {'t()': {'status': 'Success'}}}}
        self.assertIsNone(first_failure_reason(parsed))

    def test_test_result_not_found_returns_none(self):
        parsed = {'s': {'test_results': {'setUp()': {'status': 'Failure'}}}}
        self.assertIsNone(test_result(parsed, 'test_exploit'))


if __name__ == '__main__':
    unittest.main()
