import contextlib
import io
import json
import shutil
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import cli.stage3_bind as stage3_bind  # noqa: E402

STAGE2_RUN = (ROOT / 'cases' / 'panoptic_builder_init' / 'stage2_run')


class _FakeProc:
    def __init__(self, stdout='', stderr='', returncode=2):
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode


class Stage3BindFailurePathTest(unittest.TestCase):
    def test_transport_failure_emits_summary_and_fails(self):
        case_dir = ROOT / 'cases' / '__stage3_bind_fixture__'
        case_dir.mkdir(exist_ok=True)
        (case_dir / 'src').mkdir(exist_ok=True)

        original = stage3_bind.subprocess.run
        stage3_bind.subprocess.run = (
            lambda *a, **k: _FakeProc(stderr='transport down'))
        buf = io.StringIO()
        try:
            with contextlib.redirect_stdout(buf):
                rc = stage3_bind.main([
                    '--case-dir', str(case_dir),
                    '--stage2-run', str(STAGE2_RUN),
                    '--max-rounds', '2',
                ])
        finally:
            stage3_bind.subprocess.run = original
            shutil.rmtree(case_dir, ignore_errors=True)

        self.assertEqual(rc, 1)
        summary = json.loads(buf.getvalue())
        self.assertEqual(summary['schema_version'], 'stage3-bind-summary/1')
        self.assertEqual(summary['total_claims'], 1)
        self.assertEqual(summary['bound'], 0)
        self.assertEqual(summary['failed'], 1)
        self.assertEqual(summary['claims'][0]['status'], 'failed')
        self.assertIn('rounds_used', summary['claims'][0])


class Stage3BindReuseTest(unittest.TestCase):
    def test_reuse_skips_existing_binding(self):
        case_dir = ROOT / 'cases' / '__stage3_bind_reuse__'
        case_dir.mkdir(exist_ok=True)
        (case_dir / 'src').mkdir(exist_ok=True)
        (case_dir / 'bindings').mkdir(exist_ok=True)
        (case_dir / 'bindings' / 'core_claim.json').write_text('{}')

        def _boom(*a, **k):
            raise AssertionError('LLM subprocess must not run with --reuse')

        original = stage3_bind.subprocess.run
        stage3_bind.subprocess.run = _boom
        buf = io.StringIO()
        try:
            with contextlib.redirect_stdout(buf):
                rc = stage3_bind.main([
                    '--case-dir', str(case_dir),
                    '--stage2-run', str(STAGE2_RUN),
                    '--reuse',
                ])
        finally:
            stage3_bind.subprocess.run = original
            shutil.rmtree(case_dir, ignore_errors=True)

        self.assertEqual(rc, 0)
        summary = json.loads(buf.getvalue())
        self.assertEqual(summary['total_claims'], 1)
        self.assertEqual(summary['reused'], 1)
        self.assertEqual(summary['bound'], 0)
        self.assertEqual(summary['failed'], 0)
        self.assertEqual(summary['claims'][0]['status'], 'reused')


if __name__ == '__main__':
    unittest.main()
