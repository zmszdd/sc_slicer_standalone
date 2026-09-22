"""Gold-v1 integrity and approval gates; no model calls."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


HERE = Path(__file__).resolve().parents[1]
GOLD = HERE / 'evaluation/gold_v1'


class GoldV1Tests(unittest.TestCase):
    def test_manifest_inputs_and_evidence_are_frozen_and_grounded(self):
        manifest = json.loads((GOLD / 'manifest.json').read_text())
        gold = json.loads((GOLD / 'gold.json').read_text())
        self.assertEqual([x['id'] for x in manifest['cases']], [x['id'] for x in gold['cases']])
        self.assertEqual(len(gold['cases']), 5)
        for source, reference in zip(manifest['cases'], gold['cases']):
            path = GOLD / source['input']
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),
                             source['snapshot_sha256'])
            report = json.loads(path.read_text())
            text = report['title'] + '\n\n' + report['body']
            for values in reference['evidence'].values():
                for quote in values:
                    self.assertIn(quote, text)

    def test_unreviewed_template_cannot_produce_accuracy(self):
        spec = importlib.util.spec_from_file_location('gold_evaluate', GOLD / 'evaluate.py')
        module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        with self.assertRaises((FileNotFoundError, ValueError)):
            module.evaluate(GOLD / 'approved-gold.json', GOLD / 'ratings.template.json')

    def test_blind_runner_requires_explicit_upload_consent(self):
        with tempfile.TemporaryDirectory() as work:
            output = Path(work) / 'result'
            proc = subprocess.run([sys.executable, str(GOLD / 'run_blind.py'),
                                   '--output', str(output)], capture_output=True, text=True)
            self.assertEqual(proc.returncode, 2)
            self.assertIn('explicit upload consent required', proc.stderr)
            self.assertFalse(output.exists())


if __name__ == '__main__':
    unittest.main()
