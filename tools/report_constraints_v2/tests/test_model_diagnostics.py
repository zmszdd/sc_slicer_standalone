"""Model-runtime diagnostics must not persist prompts, reports, or credentials."""
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import report_only


class ModelDiagnosticTests(unittest.TestCase):
    def test_error_event_category_without_raw_output(self):
        secret = 'SECRET_REPORT_AND_KEY'
        stdout = json.dumps({'type': 'error', 'error': {
            'message': f'401 Unauthorized: {secret}'}})
        proc = subprocess.CompletedProcess(args=[], returncode=1,
                                           stdout=stdout, stderr='')
        with tempfile.TemporaryDirectory() as work:
            output = Path(work)
            with patch('report_only.subprocess.run', return_value=proc):
                with self.assertRaisesRegex(RuntimeError, 'category=authentication') as error:
                    report_only.extract(secret, output, 'test-model', 'PROMPT')
            diagnostic = (output / 'model-runtime-diagnostic.json').read_text()
            self.assertEqual(json.loads(diagnostic)['category'], 'authentication')
            self.assertNotIn(secret, diagnostic)
            self.assertNotIn(secret, str(error.exception))

    def test_unknown_failure_stays_unknown(self):
        self.assertEqual(report_only.model_failure_category('', 'unexpected exit'),
                         'unknown_runtime_error')

    def test_local_permission_is_not_called_model_error(self):
        self.assertEqual(report_only.model_failure_category('', 'EACCES: permission denied'),
                         'local_permission')


if __name__ == '__main__':
    unittest.main()
