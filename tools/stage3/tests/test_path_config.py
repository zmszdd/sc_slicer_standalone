import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from lib import path_config


class PathConfigTest(unittest.TestCase):
    def test_environment_overrides_local_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with patch.dict(os.environ, {
                'C4_OUTPUT_ROOT': str(root / 'c4'),
                'VERIFIED_FLATTEN_ROOT': str(root / 'flatten'),
                'NEGATIVE_FLATTEN_ROOT': str(root / 'negative'),
                'FORGE_STD_CANDIDATES': os.pathsep.join(
                    [str(root / 'forge-a'), str(root / 'forge-b')]),
            }, clear=False):
                self.assertEqual(path_config.c4_output_root(),
                                 root / 'c4')
                self.assertEqual(path_config.verified_flatten_root(),
                                 root / 'flatten')
                self.assertEqual(path_config.negative_flatten_root(),
                                 root / 'negative')
                self.assertEqual(path_config.negative_flatten_summary(),
                                 root / 'negative' / 'input-summary.json')
                self.assertEqual(path_config.forge_std_candidates(), (
                    root / 'forge-a', root / 'forge-b'))

    def test_root_placeholder_is_expanded(self):
        with patch.dict(os.environ, {
            'C4_OUTPUT_ROOT': '${SC_ROOT}/data/c4',
        }, clear=False):
            self.assertEqual(path_config.c4_output_root(),
                             path_config.ROOT / 'data' / 'c4')

    def test_describe_has_all_portable_roots(self):
        with patch.dict(os.environ, {
            'VERIFIED_FLATTEN_ROOT': '/tmp/flatten',
            'NEGATIVE_FLATTEN_ROOT': '/tmp/negative',
            'FORGE_STD_CANDIDATES': '',
        }, clear=False):
            report = path_config.describe()
        self.assertEqual(report['schema_version'], 'mainline-path-config/1')
        self.assertIn('c4_output_root', report)
        self.assertIn('verified_flatten_root', report)
        self.assertIn('negative_flatten_root', report)
        self.assertIn('forge_std_candidates', report)


if __name__ == '__main__':
    unittest.main()
