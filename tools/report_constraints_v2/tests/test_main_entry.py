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
                self.assertTrue((entry.STAGE2_DIR / script).is_file(),
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
                self.assertTrue((entry.STAGE2_DIR / name).is_file())
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
        self.assertTrue((STAGE2 / 'semantic_pipeline.py').is_file())
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

    def test_run_injects_deepseek_when_the_caller_omits_it(self):
        self.assertEqual(entry._with_deepseek_defaults('run', ['--case-dir', 'x']),
                         ['--provider', 'deepseek', '--case-dir', 'x'])

    def test_batch_also_pins_the_official_model_id(self):
        args = entry._with_deepseek_defaults('batch', ['--reports-root', 'r'])
        self.assertEqual(args[:4],
                         ['--provider', 'deepseek', '--model', 'deepseek-flash'])

    def test_explicit_provider_is_never_overridden(self):
        argv = ['--provider', 'opencode', '--case-dir', 'x']
        self.assertEqual(entry._with_deepseek_defaults('run', argv), argv)

    def test_offline_commands_get_no_model_defaults(self):
        for command in ('verify', 'screen', 'status'):
            with self.subTest(command=command):
                self.assertEqual(entry._with_deepseek_defaults(command, ['d']), ['d'])


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

if __name__ == '__main__':
    unittest.main()
