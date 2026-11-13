import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from lib.bindability_contract import build_contract, load_contract, \
    write_contract


class BindabilityContractTest(unittest.TestCase):
    def test_build_contract_maps_anchor_fields(self):
        with patch('lib.anchor_resolver.resolve_anchors') as resolve:
            resolve.return_value = {
                'bindability': 'multi_contract',
                'dynamically_expressible': False,
                'suggested_patch_contract': None,
                'anchor_roles': ['I', 'V'],
            }
            rows = build_contract(Path('/tmp'), ['c1'], Path('/tmp/src'))
        self.assertEqual(rows['c1']['bindability'], 'multi_contract')
        self.assertFalse(rows['c1']['dynamically_expressible'])
        self.assertEqual(rows['c1']['anchor_roles'], ['I', 'V'])

    def test_build_contract_falls_back_to_unknown_on_error(self):
        with patch('lib.anchor_resolver.resolve_anchors',
                   side_effect=RuntimeError('boom')):
            rows = build_contract(Path('/tmp'), ['c1'], Path('/tmp/src'))
        self.assertEqual(rows['c1']['bindability'], 'unknown')
        self.assertFalse(rows['c1']['dynamically_expressible'])

    def test_write_and_load_roundtrip(self):
        tmp = Path(tempfile.mkdtemp())
        (tmp / 'src').mkdir()
        with patch('lib.anchor_resolver.resolve_anchors') as resolve:
            resolve.return_value = {
                'bindability': 'single_anchor',
                'dynamically_expressible': True,
                'suggested_patch_contract': 'Vault',
                'anchor_roles': ['I'],
            }
            out = write_contract(tmp, tmp, ['c1'])
        self.assertTrue(out.is_file())
        loaded = load_contract(tmp)
        self.assertEqual(loaded['c1']['suggested_patch_contract'], 'Vault')
        self.assertTrue(loaded['c1']['dynamically_expressible'])


if __name__ == '__main__':
    unittest.main()
