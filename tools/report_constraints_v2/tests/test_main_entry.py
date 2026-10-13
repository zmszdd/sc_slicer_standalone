"""Regressions for the single repository entry point ``main.py``.

No model calls and no writes: the entry point must stay a pure dispatcher, so
these tests only exercise its command tables, exit codes and documentation.
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


class CommandTableTest(unittest.TestCase):
    def test_every_command_points_at_an_existing_script(self):
        for command, (script, description) in entry.STAGE2_COMMANDS.items():
            with self.subTest(command=command):
                self.assertTrue(entry._script_path(script) is not None,
                                f'{command} -> missing {script}')
                self.assertTrue(description.strip(), command)

    def test_no_command_reuses_the_same_script_and_arguments(self):
        # preview-report / preview-plan share preview.py but differ by prefix.
        keys = [(script, entry.STAGE2_ARG_PREFIX.get(command, ()))
                for command, (script, _) in entry.STAGE2_COMMANDS.items()]
        self.assertEqual(len(keys), len(set(keys)))

    def test_library_modules_exist_and_are_not_commands(self):
        commands = {script for script, _ in entry.STAGE2_COMMANDS.values()}
        for name in entry.LIBRARY_MODULES:
            with self.subTest(module=name):
                self.assertTrue(entry._script_path(name) is not None)
        self.assertEqual(commands & set(entry.LIBRARY_MODULES), set())

    def test_meta_and_stage2_tables_do_not_overlap(self):
        meta = {name for name, _ in entry.META_COMMANDS}
        self.assertEqual(meta & set(entry.STAGE2_COMMANDS), set())

    def test_primary_and_advanced_commands_partition_stage2(self):
        primary = set(entry.PRIMARY_STAGE2_COMMANDS)
        advanced = set(entry.ADVANCED_STAGE2_COMMANDS)
        self.assertFalse(primary & advanced)
        self.assertEqual(primary | advanced, set(entry.STAGE2_COMMANDS))

    def test_stage2_layout_is_where_the_entry_point_expects_it(self):
        self.assertTrue(entry._script_path('semantic_pipeline.py').is_file())
        self.assertTrue((STAGE2 / 'prompts' / 'registry.py').is_file())
        self.assertTrue((STAGE2 / 'tests').is_dir())


class DispatchTest(unittest.TestCase):
    def test_usage_lists_every_command(self):
        code, out, _ = run([])
        self.assertEqual(code, 0)
        for command in entry.STAGE2_COMMANDS:
            self.assertIn(command, out)
        for command, _ in entry.META_COMMANDS:
            self.assertIn(command, out)

    def test_unknown_command_is_rejected(self):
        code, _, err = run(['definitely-not-a-command'])
        self.assertEqual(code, 2)
        self.assertIn('unknown', err)

    def test_child_exit_code_is_preserved(self):
        # argparse rejects the missing required argument, so the child exits 2.
        code, _, _ = run(['screen'])
        self.assertEqual(code, 2)

    def test_child_help_is_forwarded(self):
        code, out, _ = run(['preview-report', '--help'])
        self.assertEqual(code, 0)
        self.assertIn('usage', out.lower())

    def test_prompt_preview_is_exposed_without_model_defaults(self):
        code, out, err = run(['preview-prompt', '--part', 'definitions'])
        self.assertEqual(code, 0)
        self.assertIn('P — Preconditions', out)
        self.assertIn('V — Direct violation witness', out)
        self.assertIn('"external_model_called": false', err)

    def test_stage2_shorthand_matches_the_explicit_prefix(self):
        direct, out, _ = run(['versions'])
        nested, out2, _ = run(['stage2', 'versions'])
        self.assertEqual((direct, nested), (0, 0))
        self.assertEqual(out, out2)

    def test_meta_commands_reject_extra_arguments(self):
        # 'test' forwards its arguments to unittest on purpose, and 'frozen'
        # accepts --write, so both validate their arguments their own way.
        for command, _ in entry.META_COMMANDS:
            if command == 'test':
                continue
            with self.subTest(command=command):
                code, _, err = run([command, 'unexpected'])
                self.assertEqual(code, 2)
                self.assertIn('argument', err)

    def test_versions_reports_recommended_and_experimental(self):
        registry = entry._registry()
        code, out, _ = run(['versions'])
        self.assertEqual(code, 0)
        self.assertIn(registry.RECOMMENDED_VERSION, out)
        self.assertIn(registry.EXPERIMENTAL_VERSION, out)
        for version in registry.VERSIONS:
            self.assertIn(version, out)

    def test_recommended_version_is_a_frozen_version(self):
        registry = entry._registry()
        self.assertIn(registry.RECOMMENDED_VERSION, registry.VERSIONS)
        self.assertIn(registry.EXPERIMENTAL_VERSION, registry.VERSIONS)

    def test_status_points_at_the_authoritative_documents(self):
        code, out, _ = run(['status'])
        self.assertEqual(code, 0)
        self.assertIn('not_evaluated', out)
        self.assertIn('HANDOFF.md', out)
        self.assertIn('STRUCTURE.md', out)


class SafetyTest(unittest.TestCase):
    def test_entry_point_is_the_only_main_module(self):
        self.assertTrue((ROOT / 'main.py').is_file())
        self.assertFalse((STAGE2 / 'main.py').exists(),
                         'stage-2 must not grow a second entry point')

    def test_secret_file_is_only_statted_never_read(self):
        source = (ROOT / 'main.py').read_text(encoding='utf-8')
        for line in source.splitlines():
            if 'STAGE2_ENV' in line:
                self.assertNotIn('read', line, line)
                self.assertNotIn('open', line, line)
        for forbidden in ('os.environ', 'getenv', 'os.system'):
            self.assertNotIn(forbidden, source,
                             f'{forbidden} must not appear in the entry point')

    def test_doctor_runs_without_raising_or_leaking(self):
        code, out, err = run(['doctor'])
        self.assertIn(code, (0, 1))
        text = out + err
        self.assertNotIn('API_KEY', text)
        self.assertNotIn('sk-', text)



class Stage2OnlyTest(unittest.TestCase):
    """The entry point covers stage 2 only and defaults the whole flow to DeepSeek."""

    def test_stage_one_is_not_part_of_this_entry_point(self):
        code, _, err = run(['stage1'])
        self.assertEqual(code, 2)
        self.assertIn('unknown', err)

    def test_entry_point_carries_no_stage_one_wiring(self):
        source = (ROOT / 'main.py').read_text(encoding='utf-8')
        # './run.sh' may still be *mentioned* as guidance; the wiring must be gone.
        for forbidden in ('STAGE1_ENTRY', '_stage1', 'os.access', "'stage1'"):
            self.assertNotIn(forbidden, source,
                             f'{forbidden} should have moved out of the stage-2 entry point')

    def test_run_injects_deepseek_for_the_neural_flow(self):
        self.assertEqual(
            entry._with_arg_defaults('run', ['--extract', '--case-dir', 'x']),
            ['--provider', 'deepseek', '--extract', '--case-dir', 'x',
             '--deepseek-proxy', 'direct', '--claim-verdict', 'signals',
             '--formal-retries', '1', '--element-retries', '1'])

    def test_formalize_only_run_gets_no_element_retry_budget(self):
        # --element-retries is guarded by the target parser as
        # "requires --extract"; injecting it into a formalize-only run
        # would make the child exit 2 before any model call.
        result = entry._with_arg_defaults(
            'run', ['--formalize-only', '--case-dir', 'x'])
        self.assertIn('--formal-retries', result)
        self.assertNotIn('--element-retries', result)

    def test_offline_run_is_not_pinned_to_the_deepseek_transport(self):
        """An offline run replays saved candidates and makes no model call.

        The DeepSeek transport rejects non-neural invocations outright
        (`--provider deepseek requires neural extraction or formalization`), so
        injecting it made EVERY offline `main.py run` fail with exit 2.
        """
        offline = (['--case-dir', 'x', '--elements', 'e',
                    '--formalization', 'f'],
                   ['--report', 'r', '--elements-only', 'e'])
        for argv in offline:
            with self.subTest(argv=argv):
                result = entry._with_arg_defaults('run', argv)
                self.assertNotIn('--provider', result)
                # proxy/verdict defaults still apply (transport-agnostic);
                # retry budgets do not (the parser requires neural flags).
                self.assertEqual(result[-4:], ['--deepseek-proxy', 'direct',
                                               '--claim-verdict', 'signals'])
                self.assertNotIn('--formal-retries', result)
                self.assertNotIn('--element-retries', result)

    def test_batch_also_pins_the_official_model_id(self):
        args = entry._with_arg_defaults('batch', ['--reports-root', 'r'])
        self.assertEqual(args[:4],
                         ['--provider', 'deepseek', '--model', 'deepseek-flash'])

    def test_explicit_provider_is_never_overridden(self):
        argv = ['--provider', 'opencode', '--extract', '--case-dir', 'x']
        self.assertEqual(entry._with_arg_defaults('run', argv),
                         [*argv, '--deepseek-proxy', 'direct',
                          '--claim-verdict', 'signals',
                          '--formal-retries', '1', '--element-retries', '1'])
        argv = ['--provider', 'opencode', '--formalize-only', '--case-dir', 'x']
        self.assertEqual(entry._with_arg_defaults('run', argv),
                         [*argv, '--deepseek-proxy', 'direct',
                          '--claim-verdict', 'signals',
                          '--formal-retries', '1'])

    def test_explicit_retry_budget_is_never_overridden(self):
        argv = ['--extract', '--case-dir', 'x', '--formal-retries', '2']
        self.assertEqual(entry._with_arg_defaults('run', argv),
                         ['--provider', 'deepseek', *argv,
                          '--deepseek-proxy', 'direct',
                          '--claim-verdict', 'signals',
                          '--element-retries', '1'])

    def test_offline_commands_get_no_model_defaults(self):
        for command in ('verify', 'screen', 'status'):
            with self.subTest(command=command):
                self.assertEqual(entry._with_arg_defaults(command, ['d']), ['d'])


class CommandSmokeTest(unittest.TestCase):
    """Every advertised command must at least answer --help (no model calls)."""

    def test_every_command_answers_help(self):
        import subprocess
        for command in sorted(entry.STAGE2_COMMANDS):
            with self.subTest(command=command):
                proc = subprocess.run(
                    [sys.executable, str(ROOT / 'main.py'), command, '--help'],
                    cwd=str(ROOT), capture_output=True, text=True, timeout=60)
                self.assertEqual(proc.returncode, 0,
                                 f'{command} --help failed:\n{proc.stderr[-1500:]}')
                self.assertIn('usage', (proc.stdout + proc.stderr).lower())

    def test_every_injected_flag_is_declared_by_its_target_script(self):
        """A flag `main.py` injects must appear in the target script's parser.

        Static check on purpose. Both dynamic alternatives provably fail to
        catch a violation, each verified against the real
        `main.py batch` / `--claim-verdict` regression:

        1. `cmd --help` exits 0 -- argparse handles --help before it reports
           unrecognised arguments.
        2. Omitting required args to avoid running the pipeline backfires --
           argparse reports "the following arguments are required" BEFORE
           "unrecognized arguments", so the bogus flag is never mentioned.

        So the invariant is asserted where it is verifiable: the target
        script's own source must declare each injected flag.
        """
        tables = {command: (*prepend,
                            *(flag for flags, _conflict, _requires in appends
                              for flag in flags))
                  for command, (prepend, appends, _neural) in
                  entry.STAGE2_ARG_DEFAULTS.items()}
        for command, defaults in sorted(tables.items()):
            script = entry._script_path(entry.STAGE2_COMMANDS[command][0])
            source = script.read_text(encoding='utf-8')
            for flag in (item for item in defaults if item.startswith('--')):
                    with self.subTest(command=command, flag=flag):
                        self.assertIn(
                            f"add_argument('{flag}'", source,
                            f'`main.py {command}` injects {flag} but '
                            f'{script.name} never declares it')


class BatchVerdictForwardingTest(unittest.TestCase):
    """`batch` must hand its verdict policy down to every run subprocess.

    The child writes ``provenance.claim_verdict_policy`` and ``verify`` replays
    from that value, so dropping the flag would silently pin every batch run
    back to the legacy verdict while the run summary still advertised signals.
    ``subprocess.run`` is patched, so no model is ever contacted.
    """

    def test_verdict_policy_reaches_the_run_subprocess(self):
        import tempfile
        from unittest.mock import patch

        from cli import batch_verify

        captured = []

        class FakeProc:
            returncode = 0
            stdout = ''
            stderr = ''

        def fake_run(command, **_kwargs):
            captured.append(list(command))
            # The real child creates its own --output directory.
            Path(command[command.index('--output') + 1]).mkdir(
                parents=True, exist_ok=True)
            return FakeProc()

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / 'reports'
            (root / 'case_a').mkdir(parents=True)
            (root / 'case_a' / 'report.json').write_text(
                '{"title": "t", "body": "b"}', encoding='utf-8')
            previous = sys.argv
            try:
                sys.argv = ['batch_verify.py', '--reports-root', str(root),
                            '--output', str(Path(tmp) / 'out'),
                            '--allow-report-upload', '--provider', 'opencode',
                            '--concurrency', '1',
                            '--claim-verdict', 'signals']
                with patch.object(batch_verify.subprocess, 'run', fake_run):
                    batch_verify.main()
            finally:
                sys.argv = previous

        self.assertEqual(len(captured), 1, 'one case must spawn one subprocess')
        command = captured[0]
        self.assertIn('--claim-verdict', command,
                      'batch dropped --claim-verdict on the way to the child')
        self.assertEqual(command[command.index('--claim-verdict') + 1], 'signals')
        self.assertIn('cli.semantic_pipeline', command)


if __name__ == '__main__':
    unittest.main()
