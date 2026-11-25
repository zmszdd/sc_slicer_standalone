import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from lib.manifest import ManifestError
from lib.runner import (ROOT, _build_stage1_cmd, _build_stage2_cmd,
                        _overlap, _resolve_stage3_config, _reuse_stage2,
                        _write_verdicts)


import json
import tempfile


class RunnerPureTest(unittest.TestCase):
    def test_overlap(self):
        a = {'start': 't0', 'end': 't2'}
        b = {'start': 't1', 'end': 't3'}
        self.assertTrue(_overlap(a, b))
        self.assertTrue(_overlap(b, a))

    def test_no_overlap(self):
        a = {'start': 't0', 'end': 't1'}
        b = {'start': 't2', 'end': 't3'}
        self.assertFalse(_overlap(a, b))

    def test_stage1_command(self):
        manifest = {
            'stage1': {
                'input': 'poc.sol', 'contract': 'PoC', 'variable': 'x',
                'function': 'test_x', 'level': 2, 'compile_guarantee': True,
            },
        }
        cmd = _build_stage1_cmd(manifest, '/tmp/slice.sol')
        self.assertIn('/tmp/slice.sol', cmd)
        self.assertIn('--no-rerun-test', cmd)
        self.assertIn('--compile-guarantee', cmd)
        self.assertIn('--level', cmd)
        self.assertIn('--fn', cmd)

    def test_stage2_command(self):
        manifest = {'stage2': {'report': 'r.json', 'output': 'out', 'args': ['--extract']}}
        cmd = _build_stage2_cmd(manifest, Path('.'))
        self.assertEqual(cmd[0], sys.executable)
        self.assertEqual(cmd[1], str(ROOT / 'main.py'))
        self.assertEqual(cmd[2], 'run')
        self.assertIn('--extract', cmd)

    def test_stage3_config_preserves_binding_rounds(self):
        manifest = {'stage3': {
            'case_dir': 'case',
            'binding': None,
            'binding_rounds': 1,
            'test': None,
            'run_id': None,
        }}
        config = _resolve_stage3_config(manifest, Path('/repo/manifest.json').parent)
        self.assertEqual(config['binding_rounds'], 1)
        self.assertEqual(config['case_dir'], '/repo/case')

    def test_write_verdicts_reproduced_wins(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            _write_verdicts(run_dir, mode='multi', verdicts=[
                {'claim_id': 'a', 'verdict': 'inconclusive'},
                {'claim_id': 'b', 'verdict': 'violation_reproduced'},
            ])
            data = json.loads((run_dir / 'stage3-verdicts.json').read_text())
            self.assertEqual(data['case_verdict'], 'violation_reproduced')
            self.assertEqual(data['reproduced'], 1)

    def test_write_verdicts_not_reproduced_when_no_repro(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            _write_verdicts(run_dir, mode='multi', verdicts=[
                {'claim_id': 'a', 'verdict': 'violation_not_reproduced'},
            ])
            data = json.loads((run_dir / 'stage3-verdicts.json').read_text())
            self.assertEqual(data['case_verdict'], 'violation_not_reproduced')

    def test_write_verdicts_inconclusive_when_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            _write_verdicts(run_dir, mode='bind_failed', verdicts=[])
            data = json.loads((run_dir / 'stage3-verdicts.json').read_text())
            self.assertEqual(data['case_verdict'], 'inconclusive')

    def test_stage2_reuse_fails_closed_on_verify_failure(self):
        with tempfile.TemporaryDirectory() as tmp, patch(
                'lib.runner.subprocess.call', return_value=1):
            root = Path(tmp)
            with self.assertRaises(ManifestError):
                _reuse_stage2(root, root / 'source')

    def test_stage2_reuse_legacy_opt_out_is_recorded(self):
        with tempfile.TemporaryDirectory() as tmp, patch(
                'lib.runner.subprocess.call', return_value=1) as call:
            root = Path(tmp)
            source = root / 'source'
            source.mkdir()
            for name in ('stage3-spec.json', 'constraints.json',
                         'formalization.json'):
                (source / name).write_text('{}')
            self.assertEqual(_reuse_stage2(root, root / 'source',
                                           verify=False), 0)
            call.assert_not_called()
            self.assertIn('explicitly disabled',
                          (root / 'stage2-verify.log').read_text())


if __name__ == '__main__':
    unittest.main()
