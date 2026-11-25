import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from lib import forge_runner
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

    def test_test_result_matches_fuzzed_name(self):
        parsed = {
            'src/Contract.sol:Standalone': {
                'test_results': {
                    'test_audit_poc_1036(uint88)': {
                        'status': 'Success', 'reason': None},
                },
            },
        }
        result = test_result(parsed, 'test_audit_poc_1036')
        self.assertEqual(result['name'], 'test_audit_poc_1036')
        self.assertEqual(result['status'], 'Success')

    def test_run_forge_safe_reports_timeout(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(
                forge_runner.subprocess, 'run',
                side_effect=subprocess.TimeoutExpired(['forge'], 5)):
            result = forge_runner.run_forge_safe(Path(tmp))
        self.assertFalse(result['ok'])
        self.assertIn('timed out', result['compile_error'])
        self.assertIn('timeout_seconds', result)


if __name__ == '__main__':
    unittest.main()
