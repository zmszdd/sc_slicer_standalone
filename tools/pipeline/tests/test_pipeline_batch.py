import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools' / 'pipeline'))

from cli import pipeline_batch  # noqa: E402


class PipelineBatchHelpersTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_find_manifests_skips_skeleton_dir(self):
        (self.root / 'manifests' / 'skeleton').mkdir(parents=True)
        (self.root / 'manifests' / 'a.pipeline.json').write_text('{}')
        (self.root / 'manifests' / 'skeleton' / 'b.pipeline.json').write_text('{}')
        found = pipeline_batch._find_manifests(self.root, None)
        names = [p.name for p in found]
        self.assertIn('a.pipeline.json', names)
        self.assertNotIn('b.pipeline.json', names)

    def test_resume_row_reads_pipeline_summary(self):
        case_dir = self.root / 'runs' / 'case1'
        case_dir.mkdir(parents=True)
        (case_dir / 'pipeline-summary.json').write_text(json.dumps({
            'status': 'ok',
            'overlap': False,
            'stage3': {'consistency_verdict': 'violation_reproduced',
                       'run_id': 'case1_001'},
        }))
        row = pipeline_batch._resume_row(self.root / 'm.pipeline.json', 'case1')
        self.assertEqual(row['status'], 'skipped')
        self.assertEqual(row['verdict'], 'violation_reproduced')

    def test_resume_row_returns_none_when_not_ok(self):
        case_dir = self.root / 'runs' / 'case2'
        case_dir.mkdir(parents=True)
        (case_dir / 'pipeline-summary.json').write_text(json.dumps({
            'status': 'failed',
            'stage3': {},
        }))
        self.assertIsNone(pipeline_batch._resume_row(
            self.root / 'm.pipeline.json', 'case2'))


if __name__ == '__main__':
    unittest.main()
