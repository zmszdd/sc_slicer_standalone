import json
import shutil
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools' / 'pipeline'))

from cli.case_run import (_find_src, _has_poc_test, _read_test_name,
                          main as case_run_main)  # noqa: E402
from lib.runner import ROOT, STAGE3_DIR  # noqa: E402


def _self_contained_flatten() -> str:
    """Merge the committed slice and PoC test into one self-contained file."""
    slice_text = (ROOT / 'stage1_input' / 'BuilderWalletSlice.sol').read_text()
    test_text = (ROOT / 'stage1_input' / 'stage3_handoff' / 'test'
                 / 'BuilderWalletPoC.t.sol').read_text()
    test_lines = [ln for ln in test_text.splitlines()
                  if not ln.strip().startswith('import')]
    test_lines = [ln for ln in test_lines
                  if not ln.strip().startswith('pragma')
                  and 'SPDX-License-Identifier' not in ln]
    return slice_text.rstrip() + '\n\n' + '\n'.join(test_lines).strip() + '\n'


class CaseRunDiscoveryTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.case = Path(self.tmp.name) / 'case'
        self.case.mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def test_find_src_prefers_flatten(self):
        (self.case / 'contract.flattened.t.sol').write_text('')
        self.assertEqual(_find_src(self.case).name, 'contract.flattened.t.sol')

    def test_find_src_falls_back_to_src_dir(self):
        (self.case / 'src').mkdir()
        (self.case / 'src' / 'A.sol').write_text('')
        self.assertEqual(_find_src(self.case).name, 'A.sol')

    def test_read_test_name(self):
        (self.case / 'metadata.json').write_text(
            json.dumps({'test_name': 'test_POC'}))
        self.assertEqual(_read_test_name(self.case), 'test_POC')

    def test_read_test_name_missing(self):
        self.assertIsNone(_read_test_name(self.case))

    def test_has_poc_test_detects_test_function(self):
        (self.case / 'Contract.sol').write_text(
            'contract C { function test_exploit() public {} }')
        self.assertTrue(_has_poc_test(self.case / 'Contract.sol'))

    def test_has_poc_test_rejects_no_test_function(self):
        (self.case / 'Contract.sol').write_text(
            'contract C { function run() public {} }')
        self.assertFalse(_has_poc_test(self.case / 'Contract.sol'))


class CaseRunOfflineEndToEndTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')
        self.case_name = f'case_run_e2e_{stamp}'
        self.case = Path(self.tmp.name) / self.case_name
        self.case.mkdir()
        self.out = Path(self.tmp.name) / 'out'

    def tearDown(self):
        for run_dir in (STAGE3_DIR / 'runs').glob(f'{self.case_name}*'):
            shutil.rmtree(run_dir, ignore_errors=True)
        self.tmp.cleanup()

    def test_self_contained_case_reproduces(self):
        (self.case / 'contract.flattened.t.sol').write_text(
            _self_contained_flatten())
        binding = json.loads((ROOT / 'stage1_input' / 'stage3_handoff'
                              / 'binding.json').read_text())
        binding['patch']['file'] = 'contract.flattened.t.sol'
        binding_path = self.case / 'binding.json'
        binding_path.write_text(json.dumps(binding, indent=2))
        stage2_run = STAGE3_DIR / 'cases' / 'panoptic_builder_init' / 'stage2_run'

        rc = case_run_main([
            '--case-dir', str(self.case),
            '--out-dir', str(self.out),
            '--binding', str(binding_path),
            '--stage2-run-dir', str(stage2_run),
        ])
        self.assertEqual(rc, 0)
        summary_path = self.out / 'run' / 'pipeline-summary.json'
        self.assertTrue(summary_path.is_file(), summary_path)
        summary = json.loads(summary_path.read_text())
        self.assertEqual((summary.get('stage3') or {}).get('consistency_verdict'),
                         'violation_reproduced')


if __name__ == '__main__':
    unittest.main()
