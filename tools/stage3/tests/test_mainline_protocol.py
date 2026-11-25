import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from lib import mainline_protocol


class MainlineProtocolTest(unittest.TestCase):
    def test_compute_has_all_declared_files(self):
        record = mainline_protocol.compute()
        self.assertEqual(record['version'], mainline_protocol.PROTOCOL_VERSION)
        self.assertEqual(record['stage2_prompt_version'],
                         mainline_protocol.STAGE2_PROMPT_VERSION)
        self.assertEqual(record['stage2_provider'],
                         mainline_protocol.STAGE2_PROVIDER)
        self.assertEqual(record['stage2_model'],
                         mainline_protocol.STAGE2_MODEL)
        self.assertTrue(record['files'])
        for name in ('main.py', 'run.sh', 'src/main.rs',
                     'tools/stage3/lib/mainline_protocol.py',
                     'tools/report_constraints_v2/prompts/live26_snapshot.py'):
            self.assertIn(name, record['files'])
        self.assertNotIn('config/llm.env', record['files'])

    def test_execution_and_report_hashes_are_separated(self):
        record = mainline_protocol.compute()
        self.assertEqual(record['sha256'], record['execution_sha256'])
        self.assertTrue(record['report_sha256'])
        metric = ('tools/stage3/evaluation/metrics/mainline_metrics.py')
        self.assertIn(metric, record['files'])
        self.assertIn(metric, record['report_files'])
        self.assertNotIn(metric, record['execution_files'])
        self.assertIn('main.py', record['execution_files'])

    def test_current_run_and_legacy_hash_are_accepted(self):
        self.assertTrue(
            mainline_protocol.is_current_run(mainline_protocol.current()))
        legacy = next(iter(
            mainline_protocol.LEGACY_RUN_HASHES[
                mainline_protocol.PROTOCOL_VERSION]))
        self.assertTrue(mainline_protocol.is_current_run({
            'version': mainline_protocol.PROTOCOL_VERSION,
            'sha256': legacy,
        }))
        self.assertFalse(mainline_protocol.is_current_run({
            'version': 'mainline/0.0.0',
            'sha256': legacy,
        }))
        self.assertFalse(mainline_protocol.is_current_run({
            'version': mainline_protocol.PROTOCOL_VERSION,
            'sha256': '0' * 64,
        }))

    def test_report_only_predecessor_runs_are_accepted(self):
        predecessor = next(iter(
            mainline_protocol.REPORT_ONLY_VERSION_PREDECESSORS[
                mainline_protocol.PROTOCOL_VERSION]))
        legacy = next(iter(
            mainline_protocol.LEGACY_RUN_HASHES[predecessor]))
        self.assertTrue(mainline_protocol.is_current_run({
            'version': predecessor,
            'sha256': legacy,
        }))
        self.assertFalse(mainline_protocol.is_current_run({
            'version': 'mainline/0.0.0',
            'sha256': legacy,
        }))

    def test_verify_detects_hash_and_version_drift(self):
        record = mainline_protocol.compute()
        with tempfile.TemporaryDirectory() as tmp:
            baseline = Path(tmp) / 'baseline.json'
            baseline.write_text(json.dumps(record) + '\n')
            with patch.object(mainline_protocol, 'compute', return_value=record):
                result = mainline_protocol.verify(baseline_path=baseline)
            self.assertTrue(result['ok'])

            drifted = {**record, 'sha256': '1' * 64}
            with patch.object(mainline_protocol, 'compute', return_value=drifted):
                result = mainline_protocol.verify(baseline_path=baseline)
            self.assertFalse(result['ok'])
            self.assertTrue(any('hash drift' in p for p in result['problems']))

            versioned = {**record, 'version': 'mainline/9.9.9'}
            with patch.object(mainline_protocol, 'compute', return_value=versioned):
                result = mainline_protocol.verify(baseline_path=baseline)
            self.assertFalse(result['ok'])
            self.assertTrue(any('version drift' in p for p in result['problems']))

    def test_write_baseline_is_deterministic(self):
        with tempfile.TemporaryDirectory() as tmp:
            first = mainline_protocol.write_baseline(Path(tmp) / 'a.json')
            second = mainline_protocol.write_baseline(Path(tmp) / 'b.json')
            self.assertEqual(first, second)


if __name__ == '__main__':
    unittest.main()
