import json
import tempfile
import unittest
from unittest import mock
from pathlib import Path

from lib.reference_patch import (ReferencePatchError, build_reference_patch,
                                 has_reference_patch,
                                 materialize_reference_patch)

_SRC = 'contract A { function f() public pure returns (uint256) { return 1; } }\n'
_DIFF = (
    '--- a/Contract.sol\n'
    '+++ b/Contract.sol\n'
    '@@ -1 +1 @@\n'
    '-contract A { function f() public pure returns (uint256) { return 1; } }\n'
    '+contract A { function f() public pure returns (uint256) { return 2; } }\n'
)


def _case(root: Path) -> Path:
    case = root / 'case'
    (case / 'src').mkdir(parents=True)
    (case / 'src' / 'Contract.sol').write_text(_SRC)
    return case


class ReferencePatchTest(unittest.TestCase):
    def test_has_reference_patch_none(self):
        with tempfile.TemporaryDirectory() as tmp:
            case = _case(Path(tmp))
            self.assertFalse(has_reference_patch(case))

    def test_has_reference_patch_tree(self):
        with tempfile.TemporaryDirectory() as tmp:
            case = _case(Path(tmp))
            (case / 'patched').mkdir()
            self.assertTrue(has_reference_patch(case))

    def test_has_reference_patch_diff(self):
        with tempfile.TemporaryDirectory() as tmp:
            case = _case(Path(tmp))
            (case / 'patched.diff').write_text(_DIFF)
            self.assertTrue(has_reference_patch(case))

    def test_materialize_from_diff(self):
        with tempfile.TemporaryDirectory() as tmp:
            case = _case(Path(tmp))
            (case / 'patched.diff').write_text(_DIFF)
            patched = materialize_reference_patch(case)
            self.assertEqual(patched, case / 'patched')
            self.assertTrue((case / 'patched' / 'Contract.sol').is_file())
            text = (case / 'patched' / 'Contract.sol').read_text()
            self.assertIn('return 2', text)
            self.assertNotIn('return 1', text)

    def test_materialize_is_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            case = _case(Path(tmp))
            (case / 'patched.diff').write_text(_DIFF)
            first = materialize_reference_patch(case)
            second = materialize_reference_patch(case)
            self.assertEqual(first, second)
            self.assertEqual((case / 'patched' / 'Contract.sol').read_text(),
                             (case / 'patched' / 'Contract.sol').read_text())

    def test_materialize_missing_sources_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            case = Path(tmp) / 'case'
            case.mkdir()
            (case / 'patched.diff').write_text(_DIFF)
            with self.assertRaises(ReferencePatchError):
                materialize_reference_patch(case)

    def test_materialize_bad_diff_raises_and_cleans(self):
        with tempfile.TemporaryDirectory() as tmp:
            case = _case(Path(tmp))
            (case / 'patched.diff').write_text(
                '--- a/Missing.sol\n+++ b/Missing.sol\n@@ -1 +1 @@\n-x\n+y\n')
            with self.assertRaises(ReferencePatchError):
                materialize_reference_patch(case)
            self.assertFalse((case / 'patched').exists())


if __name__ == '__main__':
    unittest.main()


class ReferenceSourcesManifestTest(unittest.TestCase):
    def test_materialize_from_patched_src(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            case = _case(root)
            fixed = root / 'fixed'
            fixed.mkdir()
            (fixed / 'Contract.sol').write_text(
                'contract A { function f() public pure returns (uint256) { return 9; } }\n')
            (case / 'reference_sources.json').write_text(
                f'{{"patched_src": "{fixed}"}}')
            self.assertTrue(has_reference_patch(case))
            patched = materialize_reference_patch(case)
            self.assertIn('return 9', (patched / 'Contract.sol').read_text())

    def test_materialize_from_manifest_diff(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            case = _case(root)
            diff = root / 'fix.diff'
            diff.write_text(_DIFF)
            (case / 'reference_sources.json').write_text(
                f'{{"diff": "{diff}"}}')
            self.assertTrue(has_reference_patch(case))
            patched = materialize_reference_patch(case)
            self.assertIn('return 2', (patched / 'Contract.sol').read_text())

    def test_missing_patched_src_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            case = _case(Path(tmp))
            (case / 'reference_sources.json').write_text(
                '{"patched_src": "/nonexistent/fixed"}')
            with self.assertRaises(ReferencePatchError):
                materialize_reference_patch(case)

    def test_dry_run_does_not_materialize(self):
        with tempfile.TemporaryDirectory() as tmp:
            case = _case(Path(tmp))
            (case / 'patched.diff').write_text(_DIFF)
            record = build_reference_patch(case, dry_run=True)
            self.assertTrue(record['accepted'])
            self.assertEqual(record['source_kind'], 'local_diff')
            self.assertEqual(len(record['source_sha256']), 64)
            self.assertFalse((case / 'patched').exists())

    def test_file_override_and_target_function_validation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            case = _case(root)
            override = root / 'Patched.sol'
            override.write_text(
                'contract A { function fixed() public pure returns (uint256) '
                '{ return 2; } }\n')
            (case / 'reference_sources.json').write_text(json.dumps({
                'files': {'src/Contract.sol': str(override)},
            }))
            with mock.patch('lib.reference_patch._validate_compile',
                            return_value={'ok': True}):
                record = build_reference_patch(
                    case, target_function='fixed', validate_compile=True)
            self.assertTrue(record['accepted'])
            self.assertEqual(record['overrides_applied'],
                             ['src/Contract.sol'])
            self.assertIn('return 2',
                          (case / 'patched' / 'src' / 'Contract.sol').read_text())
            stored = json.loads(
                (case / 'reference-patch-manifest.json').read_text())
            self.assertTrue(stored['target_function_present'])
            self.assertTrue(stored['compile_validation']['ok'])

    def test_missing_target_function_blocks_patch(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            case = _case(root)
            fixed = root / 'fixed'
            fixed.mkdir()
            (fixed / 'Contract.sol').write_text(_SRC)
            (case / 'reference_sources.json').write_text(
                f'{{"patched_src": "{fixed}"}}')
            record = build_reference_patch(case, target_function='missing')
            self.assertFalse(record['accepted'])
            self.assertIn('target_function_not_in_patch', record['blockers'])
