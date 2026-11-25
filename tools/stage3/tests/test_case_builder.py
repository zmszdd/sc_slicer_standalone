import json
import tempfile
import unittest
from pathlib import Path

from lib.case_builder import assemble_case, refresh_stage2_run
from lib.spec_loader import SpecError

CASE = Path(__file__).resolve().parents[1] / 'cases' / 'panoptic_builder_init'


class CaseBuilderTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_assemble_copies_and_validates(self):
        out = assemble_case(
            name='built',
            src=CASE / 'src',
            stage2_run=CASE / 'stage2_run',
            binding=CASE / 'binding.json',
            test=CASE / 'test',
            out=self.root / 'cases' / 'built',
        )
        self.assertTrue((out / 'src' / 'BuilderWallet.sol').is_file())
        self.assertTrue((out / 'test' / 'BuilderWalletPoC.t.sol').is_file())
        for name in ('stage3-spec.json', 'constraints.json', 'formalization.json'):
            self.assertTrue((out / 'stage2_run' / name).is_file())
        self.assertTrue((out / 'binding.json').is_file())
        manifest = json.loads((out / 'case.json').read_text())
        self.assertEqual(manifest['claim_id'], 'core_claim')
        harness = json.loads((out / 'harness-manifest.json').read_text())
        self.assertEqual(harness['schema_version'], 'stage1-harness-manifest/1')
        self.assertTrue(harness['test_entrypoint'])
        self.assertIn('compile_hash', harness)

    def test_assemble_flat_default_toml_and_src_name(self):
        out = assemble_case(
            name='built_flat',
            src=CASE / 'stage2_run' / 'stage3-spec.json',
            stage2_run=CASE / 'stage2_run',
            test=None,
            out=self.root / 'cases' / 'built_flat',
            default_foundry_toml=True,
            src_name='Contract.sol',
        )
        self.assertTrue((out / 'src' / 'Contract.sol').is_file())
        self.assertTrue((out / 'test').is_dir())
        toml = (out / 'foundry.toml').read_text()
        self.assertIn('via_ir = true', toml)
        self.assertFalse((out / 'binding.json').exists())

    def test_assemble_without_binding(self):
        out = assemble_case(
            name='built_nobind',
            src=CASE / 'src',
            stage2_run=CASE / 'stage2_run',
            test=CASE / 'test',
            out=self.root / 'cases' / 'built_nobind',
        )
        for name in ('stage3-spec.json', 'constraints.json', 'formalization.json'):
            self.assertTrue((out / 'stage2_run' / name).is_file())
        self.assertFalse((out / 'binding.json').exists())
        manifest = json.loads((out / 'case.json').read_text())
        self.assertIsNone(manifest['claim_id'])
        self.assertIsNone(manifest['binding'])

    def test_refresh_stage2_run_syncs_drifted_spec(self):
        out = assemble_case(
            name='built_refresh',
            src=CASE / 'src',
            stage2_run=CASE / 'stage2_run',
            test=CASE / 'test',
            out=self.root / 'cases' / 'built_refresh',
        )
        spec = out / 'stage2_run' / 'stage3-spec.json'
        data = json.loads(spec.read_text())
        for claim in data.get('claims', []):
            claim['claim_id'] = 'drifted_claim'
        spec.write_text(json.dumps(data))

        refresh_stage2_run(CASE / 'stage2_run', out)

        refreshed = json.loads(spec.read_text())
        self.assertNotIn('drifted_claim',
                         [c.get('claim_id') for c in refreshed.get('claims', [])])
        for name in ('stage3-spec.json', 'constraints.json', 'formalization.json'):
            self.assertTrue((out / 'stage2_run' / name).is_file())

    def test_assemble_rejects_bad_binding(self):
        with self.assertRaises(SpecError):
            assemble_case(
                name='bad',
                src=CASE / 'src',
                stage2_run=CASE / 'stage2_run',
                binding=CASE / 'expected' / 'expected.json',
                test=CASE / 'test',
                out=self.root / 'cases' / 'bad',
            )


if __name__ == '__main__':
    unittest.main()
