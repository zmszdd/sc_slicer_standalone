"""Batch guard tests use mocks only, never external models."""
from contextlib import redirect_stderr, redirect_stdout
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from cli import batch_verify as batch
from prompts.registry import DEFAULT_VERSION


class BatchGuards(unittest.TestCase):
    def reject(self, manifest, consent=True):
        with tempfile.TemporaryDirectory() as work:
            root = Path(work)
            source = root / 'manifest.json'
            source.write_text(json.dumps(manifest))
            output = root / 'output'
            argv = ['batch', '--manifest', str(source), '--output', str(output)]
            if consent:
                argv.append('--allow-report-upload')
            with patch('sys.argv', argv), patch.object(batch.subprocess, 'run') as call:
                with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                    batch.main()
                call.assert_not_called()
                self.assertFalse(output.exists())

    def test_no_consent_no_calls(self):
        self.reject({'data_root': '.', 'cases': []}, consent=False)

    def test_over_five_no_calls(self):
        self.reject({'data_root': '.', 'cases': [
            {'id': str(n), 'case_directory': str(n)} for n in range(6)]})

    def test_references_disallowed(self):
        self.reject({'data_root': '.', 'cases': [
            {'id': 'x', 'case_directory': 'x', 'reference': 'answer'}]})

    def test_path_escape_disallowed(self):
        self.reject({'data_root': '.', 'cases': [
            {'id': '../escape', 'case_directory': 'x'}]})

    def test_batch_runs_once_per_case_and_preserves_failure(self):
        with tempfile.TemporaryDirectory() as work:
            root = Path(work)
            (root / 'case').mkdir()
            (root / 'case' / 'report.json').write_text('{}')
            manifest = root / 'manifest.json'
            manifest.write_text(json.dumps({'data_root': str(root), 'cases': [
                {'id': 'x', 'case_directory': 'case'}]}))
            output = root / 'out'

            def fake(command, **kwargs):
                target = Path(command[command.index('--output') + 1])
                target.mkdir()
                status = {'acceptance_status': 'rejected', 'external_model_invocations': 1}
                (target / 'status.json').write_text(json.dumps(status))
                return batch.subprocess.CompletedProcess(command, 2, json.dumps(status), '')

            argv = ['batch', '--manifest', str(manifest), '--output', str(output),
                    '--allow-report-upload']
            with patch('sys.argv', argv), patch.object(batch.subprocess, 'run', side_effect=fake) as call:
                with redirect_stdout(io.StringIO()):
                    batch.main()
                self.assertEqual(call.call_count, 1)
                self.assertNotIn('--elements', call.call_args.args[0])
                self.assertNotIn('--formalization', call.call_args.args[0])
                self.assertIn('--prompt-version', call.call_args.args[0])
                self.assertIn(DEFAULT_VERSION, call.call_args.args[0])
            saved = json.loads((output / 'batch-summary.json').read_text())
            # Current live adds one audit-guided local formula repair to the
            # extraction, applicability and formalization retry budgets.
            self.assertEqual(saved['retry_count'], 4)
            self.assertEqual(saved['prompt_version'], DEFAULT_VERSION)
            self.assertEqual(saved['results'][0]['exit_code'], 2)

    def test_relative_output_is_resolved_before_child_changes_cwd(self):
        with tempfile.TemporaryDirectory() as work:
            root = Path(work)
            (root / 'case').mkdir()
            (root / 'case' / 'report.json').write_text('{}')
            manifest = root / 'manifest.json'
            manifest.write_text(json.dumps({'data_root': str(root), 'cases': [
                {'id': 'x', 'case_directory': 'case'}]}))

            seen = []

            def fake(command, **kwargs):
                target = Path(command[command.index('--output') + 1])
                seen.append(target)
                target.mkdir(parents=True)
                status = {'acceptance_status': 'needs_review'}
                (target / 'status.json').write_text(json.dumps(status))
                return batch.subprocess.CompletedProcess(command, 0, json.dumps(status), '')

            previous = Path.cwd()
            try:
                os.chdir(root)
                argv = ['batch', '--manifest', str(manifest), '--output', 'relative-out',
                        '--allow-report-upload']
                with patch('sys.argv', argv), \
                        patch.object(batch.subprocess, 'run', side_effect=fake):
                    with redirect_stdout(io.StringIO()):
                        batch.main()
            finally:
                os.chdir(previous)

            self.assertEqual(seen, [root / 'relative-out' / 'x'])
            self.assertTrue((root / 'relative-out' / 'batch-summary.json').is_file())



class AutoDiscovery(unittest.TestCase):
    """--reports-root discovery and --resume, still without model calls."""

    def make_root(self, work, names, extra_dirs=()):
        root = Path(work) / 'reports'
        for name in names:
            (root / name).mkdir(parents=True)
            (root / name / 'report.json').write_text('{}')
        for name in extra_dirs:
            (root / name).mkdir(parents=True)
        return root

    def fake_run(self, command, **kwargs):
        target = Path(command[command.index('--output') + 1])
        target.mkdir(parents=True, exist_ok=True)
        status = {'acceptance_status': 'needs_review'}
        (target / 'status.json').write_text(json.dumps(status))
        return batch.subprocess.CompletedProcess(command, 0, json.dumps(status), '')

    def run_batch(self, argv):
        with patch('sys.argv', argv), patch.object(batch.subprocess, 'run',
                                                  side_effect=self.fake_run) as call:
            with redirect_stdout(io.StringIO()):
                batch.main()
        return call

    def test_reports_root_discovers_only_case_folders(self):
        with tempfile.TemporaryDirectory() as work:
            root = self.make_root(work, ['case_a', 'case_b'], extra_dirs=['notes'])
            output = Path(work) / 'out'
            self.run_batch(['batch', '--reports-root', str(root), '--output', str(output),
                            '--allow-report-upload'])
            summary = json.loads((output / 'batch-summary.json').read_text())
            self.assertEqual([row['case_id'] for row in summary['results']],
                             ['case_a', 'case_b'])
            self.assertTrue((output / 'batch-summary.md').is_file())

    def test_requires_exactly_one_case_source(self):
        with tempfile.TemporaryDirectory() as work:
            root = self.make_root(work, ['case_a'])
            output = Path(work) / 'out'
            for argv in (['batch', '--output', str(output)],
                         ['batch', '--manifest', 'm.json', '--reports-root', str(root),
                          '--output', str(output)]):
                with self.subTest(argv=argv), \
                        patch('sys.argv', argv + ['--allow-report-upload']), \
                        patch.object(batch.subprocess, 'run') as call:
                    with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                        batch.main()
                    call.assert_not_called()

    def test_max_cases_caps_discovery(self):
        with tempfile.TemporaryDirectory() as work:
            root = self.make_root(work, [f'case_{n}' for n in range(7)])
            output = Path(work) / 'out'
            call = self.run_batch(['batch', '--reports-root', str(root), '--max-cases', '2',
                                   '--output', str(output), '--allow-report-upload'])
            self.assertEqual(call.call_count, 2)

    def test_resume_skips_completed_cases(self):
        with tempfile.TemporaryDirectory() as work:
            root = self.make_root(work, ['case_a', 'case_b'])
            output = Path(work) / 'out'
            (output / 'case_a').mkdir(parents=True)
            (output / 'case_a' / 'status.json').write_text(
                json.dumps({'acceptance_status': 'needs_review'}))
            call = self.run_batch(['batch', '--reports-root', str(root), '--output', str(output),
                                   '--allow-report-upload', '--resume'])
            self.assertEqual(call.call_count, 1)
            summary = json.loads((output / 'batch-summary.json').read_text())
            self.assertEqual([row['case_id'] for row in summary['results'] if row.get('resumed')],
                             ['case_a'])

    def test_resume_parks_an_incomplete_directory(self):
        with tempfile.TemporaryDirectory() as work:
            root = self.make_root(work, ['case_a'])
            output = Path(work) / 'out'
            (output / 'case_a').mkdir(parents=True)
            (output / 'case_a' / 'leftover.txt').write_text('partial')
            self.run_batch(['batch', '--reports-root', str(root), '--output', str(output),
                            '--allow-report-upload', '--resume'])
            parked = list(output.glob('case_a.incomplete-*'))
            self.assertEqual(len(parked), 1)
            self.assertTrue((parked[0] / 'leftover.txt').is_file())

if __name__ == '__main__':
    unittest.main()
