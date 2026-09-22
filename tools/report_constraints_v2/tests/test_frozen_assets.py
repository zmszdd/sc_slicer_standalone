"""The frozen-asset manifest must keep detecting real tampering.

Stage-1 and the archived v1 artifact are immutable: frozen evaluation reports and the
commands in HANDOFF depend on them replaying byte-for-byte.  ``main.py frozen``
verifies the manifest, so these tests keep that command honest.
"""

import io
import sys
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

HERE = Path(__file__).resolve().parent
STAGE2 = HERE.parent
ROOT = STAGE2.parent.parent

sys.path.insert(0, str(ROOT))
try:
    import main as entry
finally:
    sys.path.remove(str(ROOT))


def run(argv):
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = entry.main(argv)
    return code, out.getvalue(), err.getvalue()


class FrozenAssetTest(unittest.TestCase):
    def test_manifest_records_the_expected_enumerated_entries(self):
        paths = entry._frozen_paths()
        self.assertTrue(paths)
        self.assertIn('run.sh', paths)
        self.assertIn('src/main.rs', paths)
        self.assertIn('archives/report_constraints_v1_20260912.zip', paths)
        self.assertFalse(any(name.startswith('tools/report_constraints/')
                             for name in paths))
        self.assertFalse(any('__pycache__' in name for name in paths))
        self.assertEqual(len(paths), len(set(paths)))

    def test_scopes_cover_stage_one_and_v1_only(self):
        self.assertEqual(list(entry.FROZEN_SCOPES), [
            'src/**/*.rs',
            'run.sh',
            'archives/report_constraints_v1_*.zip',
        ])

    def test_mutable_runtime_cache_is_not_frozen(self):
        self.assertNotIn('.slicer_cache.json', entry._frozen_paths())

    def test_manifest_lives_at_the_repository_root(self):
        self.assertEqual(entry.FROZEN_MANIFEST, ROOT / 'PROTECTED_HASHES.json')
        self.assertTrue(entry.FROZEN_MANIFEST.is_file())

    def test_verification_passes_on_a_clean_tree(self):
        code, out, _ = run(['frozen'])
        self.assertEqual(code, 0, out)
        self.assertIn('一致', out)

    def test_verification_detects_tampering_and_recovers(self):
        target = ROOT / 'run.sh'
        original = target.read_bytes()
        try:
            target.write_bytes(original + b'\n')
            code, out, _ = run(['frozen'])
            self.assertEqual(code, 1)
            self.assertIn('[CHANGED] run.sh', out)
        finally:
            target.write_bytes(original)
        code, out, _ = run(['frozen'])
        self.assertEqual(code, 0, out)

    def test_unknown_argument_is_rejected(self):
        code, _, err = run(['frozen', '--nonsense'])
        self.assertEqual(code, 2)
        self.assertIn('unknown argument', err)


if __name__ == '__main__':
    unittest.main()
