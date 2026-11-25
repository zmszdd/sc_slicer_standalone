import json
import tempfile
import unittest
from pathlib import Path

from evaluation.metrics.provision_reference_patches import provision_record


class ReferencePatchProvisionTest(unittest.TestCase):
    def _case(self, root: Path) -> Path:
        case = root / 'case'
        (case / 'src').mkdir(parents=True)
        (case / 'src' / 'Contract.sol').write_text('contract A {}\n')
        return case

    def test_repo_reachability_alone_is_not_provisioned(self):
        with tempfile.TemporaryDirectory() as tmp:
            case = self._case(Path(tmp))
            row = provision_record(
                case='C', project='P', repo='https://example.invalid/r',
                lines=[], case_dir=case)
            self.assertFalse(row['provisioned'])
            self.assertFalse(row['ready_to_materialize'])
            self.assertIn('missing_reference_sources', row['reasons'])

    def test_local_diff_is_ready_to_materialize(self):
        with tempfile.TemporaryDirectory() as tmp:
            case = self._case(Path(tmp))
            (case / 'patched.diff').write_text('diff --git a/A b/A\n')
            row = provision_record(
                case='C', project='P', repo=None, lines=[], case_dir=case)
            self.assertTrue(row['provisioned'])
            self.assertTrue(row['ready_to_materialize'])
            self.assertEqual(row['source_kind'], 'local_diff')
            self.assertFalse(row['materialized'])

    def test_missing_patched_src_is_not_provisioned(self):
        with tempfile.TemporaryDirectory() as tmp:
            case = self._case(Path(tmp))
            (case / 'reference_sources.json').write_text(json.dumps({
                'patched_src': str(Path(tmp) / 'missing')}))
            row = provision_record(
                case='C', project='P', repo=None, lines=[], case_dir=case)
            self.assertFalse(row['provisioned'])
            self.assertIn('patched_src_not_found', row['reasons'])

    def test_local_git_refs_require_a_local_repo(self):
        with tempfile.TemporaryDirectory() as tmp:
            case = self._case(Path(tmp))
            (case / 'reference_sources.json').write_text(json.dumps({
                'repo': 'https://example.invalid/r', 'base': 'a', 'fix': 'b'}))
            row = provision_record(
                case='C', project='P', repo='https://example.invalid/r',
                lines=[], case_dir=case)
            self.assertFalse(row['provisioned'])
            self.assertIn('repo_not_local_or_missing', row['reasons'])


if __name__ == '__main__':
    unittest.main()
