import os
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / 'scripts' / 'cleanup_generated.sh'


class CleanupGuardTest(unittest.TestCase):
    def test_dry_run_reports_protected_paths_without_deleting(self):
        result = subprocess.run(
            ['bash', str(SCRIPT)], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('c4_pipeline_output', result.stdout)
        self.assertIn('tools/stage3/runs', result.stdout)
        self.assertIn('dry-run', result.stdout)

    def test_cleanup_script_has_no_external_root_deletion(self):
        text = SCRIPT.read_text()
        self.assertIn('is_protected', text)
        self.assertIn('c4_pipeline_output', text)
        self.assertNotIn('rm -rf -- "$ROOT/c4_pipeline_output"', text)
        self.assertNotIn('find . -type f \\( -name \'*.log\'', text)

    def test_env_override_is_reported_as_protected(self):
        env = {'C4_OUTPUT_ROOT': '/tmp/cleanup-guard-root'}
        result = subprocess.run(
            ['bash', str(SCRIPT)], cwd=ROOT, capture_output=True,
            text=True, env={**os.environ, **env})
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('/tmp/cleanup-guard-root', result.stdout)


if __name__ == '__main__':
    unittest.main()
