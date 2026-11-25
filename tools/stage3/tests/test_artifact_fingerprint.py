import json
import tempfile
import unittest
from pathlib import Path

from lib import artifact_fingerprint, mainline_protocol


class ArtifactFingerprintTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.stage2 = self.root / 'stage2'
        self.stage2.mkdir()
        for name in ('stage3-spec.json', 'constraints.json',
                     'formalization.json'):
            (self.stage2 / name).write_text('{}')
        self.binding = self.root / 'binding.json'
        self.binding.write_text('{}')

    def test_build_records_current_protocol(self):
        fingerprint = artifact_fingerprint.build(self.stage2, self.binding)
        self.assertEqual(fingerprint['mainline_protocol'],
                         mainline_protocol.current())

    def test_run_manifest_carries_provenance(self):
        path = self.root / 'run-manifest.json'
        record = artifact_fingerprint.write_run_manifest(
            path,
            run_id='run-1',
            created_at='2026-11-20T00:00:00+00:00',
            stage2_dir=self.stage2,
            binding_path=self.binding,
            claim_id='claim-1')
        self.assertEqual(json.loads(path.read_text()), record)
        self.assertEqual(record['claim_id'], 'claim-1')
        self.assertEqual(record['created_at'], '2026-11-20T00:00:00+00:00')
        self.assertEqual(record['mainline_protocol'],
                         mainline_protocol.current())
        self.assertIn('stage3-spec.json', record['stage2'])
        self.assertEqual(len(record['binding_sha256']), 64)


if __name__ == '__main__':
    unittest.main()
