import json
import tempfile
import unittest
from pathlib import Path

from evaluation.metrics.refresh_negative_slice_readiness import refresh


class RefreshNegativeSliceReadinessTest(unittest.TestCase):
    def test_only_metadata_changes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sample = {
                'schema_version': 'mainline-sample/1',
                'seed': 20261115,
                'positive_cases': ['pos1'],
                'negative_cases': ['neg1', 'neg2'],
                'negative_slice_ready': 0,
            }
            artifact = root / 'neg1.sol'
            artifact.write_text('contract A {}')
            neutral = root / 'neg2.sol'
            neutral.write_text('contract B {}')
            status = root / 'status.json'
            status.write_text(json.dumps({'rows': [
                {'case': 'neg1', 'status': 'flatten_pass',
                 'route': 'negative_witness', 'artifact': str(artifact),
                 'artifact_sha256': 'abc'},
                {'case': 'neg2', 'status': 'blocked',
                 'route': 'negative_witness', 'artifact': ''},
                {'case': 'neg2', 'status': 'flatten_pass',
                 'route': 'neutral_entrypoint', 'artifact': str(neutral),
                 'artifact_sha256': 'def'},
                {'case': 'other', 'status': 'flatten_pass',
                 'route': 'negative_witness', 'artifact': str(artifact)},
            ]}))
            out = root / 'sample.json'
            out.write_text(json.dumps(sample))
            result = refresh(out, status, root / 'refreshed.json')
            refreshed = json.loads((root / 'refreshed.json').read_text())
            self.assertEqual(result['negative_slice_ready'], 2)
            self.assertEqual(refreshed['negative_slice_ready'], 2)
            self.assertEqual(refreshed['positive_cases'], ['pos1'])
            self.assertEqual(refreshed['negative_cases'], ['neg1', 'neg2'])


if __name__ == '__main__':
    unittest.main()
