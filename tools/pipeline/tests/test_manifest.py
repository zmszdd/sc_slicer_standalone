import json
import tempfile
import unittest
from pathlib import Path

from lib.manifest import (ManifestError, build_manifest_from_case,
                          load_manifest, validate_manifest)

VALID = {
    'schema_version': 'pipeline-manifest/1',
    'case_id': 'demo',
    'stage1': {
        'input': 'poc.sol', 'contract': 'PoC', 'variable': 'x',
        'output_slice': 'slice.sol', 'level': 2,
    },
    'stage2': {'run_dir': 'stage2'},
    'stage3': {
        'binding': 'binding.json', 'test': 'test', 'case_dir': 'case',
    },
}


class ManifestTest(unittest.TestCase):
    def test_valid_reuse_mode(self):
        manifest = validate_manifest(VALID, None)
        self.assertEqual(manifest['case_id'], 'demo')
        self.assertIsNone(manifest['stage2']['report'])

    def test_report_mode_requires_output(self):
        value = json.loads(json.dumps(VALID))
        value['stage2'] = {'report': 'report.json'}
        with self.assertRaises(ManifestError):
            validate_manifest(value, None)

    def test_missing_schema(self):
        value = json.loads(json.dumps(VALID))
        value.pop('schema_version')
        with self.assertRaises(ManifestError):
            validate_manifest(value, None)

    def test_missing_input_path_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'm.json'
            path.write_text(json.dumps(VALID))
            with self.assertRaises(ManifestError):
                load_manifest(path)

    def test_binding_optional_and_defaults(self):
        value = json.loads(json.dumps(VALID))
        value['stage3'].pop('binding')
        manifest = validate_manifest(value, None)
        self.assertIsNone(manifest['stage3']['binding'])
        self.assertEqual(manifest['stage3']['binding_rounds'], 3)

    def test_binding_rounds_override(self):
        value = json.loads(json.dumps(VALID))
        value['stage3'].pop('binding')
        value['stage3']['binding_rounds'] = 5
        manifest = validate_manifest(value, None)
        self.assertEqual(manifest['stage3']['binding_rounds'], 5)

    def test_binding_rounds_must_be_int(self):
        value = json.loads(json.dumps(VALID))
        value['stage3']['binding_rounds'] = 'x'
        with self.assertRaises(ManifestError):
            validate_manifest(value, None)

    def test_test_optional_without_binding(self):
        value = json.loads(json.dumps(VALID))
        value['stage3'].pop('binding')
        value['stage3'].pop('test')
        manifest = validate_manifest(value, None)
        self.assertIsNone(manifest['stage3']['test'])

    def test_load_valid_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'poc.sol').write_text('')
            (root / 'binding.json').write_text('')
            (root / 'test').mkdir()
            stage2 = root / 'stage2'
            stage2.mkdir()
            for name in ('stage3-spec.json', 'constraints.json', 'formalization.json'):
                (stage2 / name).write_text('{}')
            path = root / 'm.json'
            path.write_text(json.dumps(VALID))
            manifest = load_manifest(path)
            self.assertEqual(manifest['case_id'], 'demo')

    def test_build_manifest_from_case_report_mode(self):
        manifest = build_manifest_from_case(
            case_id='c', src=Path('flat.t.sol'), test=Path('flat.t.sol'),
            out_dir=Path('out'), report=Path('report.json'),
        )
        self.assertEqual(manifest['schema_version'], 'pipeline-manifest/1')
        self.assertIsNone(manifest['stage3'].get('binding'))
        self.assertEqual(manifest['stage3']['binding_rounds'], 3)
        self.assertEqual(manifest['stage2']['report'], 'report.json')
        self.assertEqual(manifest['stage1']['output_slice'], 'flat.t.sol')

    def test_build_manifest_from_case_reuse_mode(self):
        manifest = build_manifest_from_case(
            case_id='c', src=Path('flat.t.sol'), test=Path('flat.t.sol'),
            out_dir=Path('out'), stage2_run_dir=Path('run'),
        )
        self.assertEqual(manifest['stage2']['run_dir'], 'run')
        self.assertNotIn('report', manifest['stage2'])

    def test_build_manifest_from_case_with_binding(self):
        manifest = build_manifest_from_case(
            case_id='c', src=Path('flat.t.sol'), test=Path('flat.t.sol'),
            out_dir=Path('out'), report=Path('report.json'),
            binding=Path('b.json'), binding_rounds=5,
        )
        self.assertEqual(manifest['stage3']['binding'], 'b.json')
        self.assertNotIn('binding_rounds', manifest['stage3'])

    def test_build_manifest_from_case_self_contained_defaults_no_test(self):
        manifest = build_manifest_from_case(
            case_id='c', src=Path('flat.t.sol'),
            out_dir=Path('out'), report=Path('report.json'),
        )
        self.assertNotIn('test', manifest['stage3'])


if __name__ == '__main__':
    unittest.main()
