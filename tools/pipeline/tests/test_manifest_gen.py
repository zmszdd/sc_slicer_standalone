import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools' / 'pipeline'))

from cli import manifest_gen  # noqa: E402
from lib.manifest import validate_manifest  # noqa: E402


class ManifestGenTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.findings = self.root / 'findings.json'
        self.flatten = self.root / 'flatten'
        self.flatten.mkdir()
        self.out = self.root / 'out'

    def tearDown(self):
        self.tmp.cleanup()

    def _write_findings(self, extra=None):
        finding = {
            'uid': 'subAAA',
            'raw': {'finding': {'uid': 'findBBB'}},
            'validity': 'valid',
            'quality': 'sufficient',
            'severity': 'high',
            'title': 'Test finding',
            'body': '## Impact\nattacker drains funds',
        }
        if extra:
            finding.update(extra)
        self.findings.write_text(json.dumps([finding]))

    def _write_index(self):
        case_dir = 'Proj__findBBB__subAAA'
        (self.flatten / case_dir).mkdir(parents=True)
        (self.flatten / case_dir / 'contract.flattened.t.sol').write_text('')
        with (self.flatten / 'index.csv').open('w', newline='') as fh:
            writer = csv.DictWriter(fh, fieldnames=[
                'key', 'case_dir', 'submission_uid', 'finding_uid', 'test_name'])
            writer.writeheader()
            writer.writerow({
                'key': case_dir,
                'case_dir': case_dir,
                'submission_uid': 'subAAA',
                'finding_uid': 'findBBB',
                'test_name': 'test_POC',
            })

    def test_matched_finding_produces_runnable_manifest(self):
        self._write_findings()
        self._write_index()
        rc = manifest_gen.main([
            '--findings', str(self.findings),
            '--out-dir', str(self.out),
            '--flatten-root', str(self.flatten),
        ])
        self.assertEqual(rc, 0)
        summary = json.loads((self.out / 'manifest-gen-summary.json').read_text())
        self.assertEqual(summary['flatten_matched'], 1)
        self.assertEqual(summary['flatten_unmatched'], 0)
        manifest = json.loads((self.out / 'manifests' / 'subAAA.pipeline.json').read_text())
        self.assertEqual(manifest['kind'], 'runnable')
        validated = validate_manifest(manifest, None)
        self.assertIsNone(validated['stage3']['binding'])
        self.assertEqual(validated['stage3']['binding_rounds'], 3)
        self.assertEqual(validated['stage1']['function'], 'test_POC')
        self.assertIn('contract.flattened.t.sol', validated['stage1']['input'])

    def test_unmatched_finding_falls_back_to_needs_input(self):
        self._write_findings()
        rc = manifest_gen.main([
            '--findings', str(self.findings),
            '--out-dir', str(self.out),
        ])
        self.assertEqual(rc, 0)
        summary = json.loads((self.out / 'manifest-gen-summary.json').read_text())
        self.assertEqual(summary['flatten_matched'], 0)
        self.assertEqual(summary['flatten_unmatched'], 1)
        self.assertEqual(summary['needs_input_manifests'], 1)
        self.assertEqual(summary['needs_input_reasons'], {'needs_flatten': 1})
        manifest = json.loads((self.out / 'manifests' / 'needs_input'
                               / 'subAAA.pipeline.json').read_text())
        self.assertEqual(manifest['kind'], 'needs_input')
        self.assertEqual(manifest['blockers'], ['needs_flatten'])
        self.assertEqual(manifest['stage1']['input'], None)
        self.assertEqual(manifest['stage1']['contract'], None)
        self.assertEqual(manifest['stage3']['binding_rounds'], 3)

    def test_matched_finding_infers_test_name_from_flatten(self):
        self._write_findings()
        case_dir = 'Proj__findBBB__subAAA'
        (self.flatten / case_dir).mkdir(parents=True)
        flatten = self.flatten / case_dir / 'contract.flattened.t.sol'
        flatten.write_text('contract C { function test_POC() public {} }')
        with (self.flatten / 'index.csv').open('w', newline='') as fh:
            writer = csv.DictWriter(fh, fieldnames=[
                'key', 'case_dir', 'submission_uid', 'finding_uid', 'test_name'])
            writer.writeheader()
            writer.writerow({
                'key': case_dir,
                'case_dir': case_dir,
                'submission_uid': 'subAAA',
                'finding_uid': 'findBBB',
                'test_name': '',
            })
        rc = manifest_gen.main([
            '--findings', str(self.findings),
            '--out-dir', str(self.out),
            '--flatten-root', str(self.flatten),
        ])
        self.assertEqual(rc, 0)
        manifest = json.loads((self.out / 'manifests' / 'subAAA.pipeline.json').read_text())
        self.assertEqual(manifest['stage1']['function'], 'test_POC')


if __name__ == '__main__':
    unittest.main()
