#!/usr/bin/env python3
import sys
import tempfile
import unittest
from pathlib import Path

STAGE3 = Path(__file__).resolve().parents[1]
ROOT = STAGE3.parents[1]
if str(STAGE3) not in sys.path:
    sys.path.insert(0, str(STAGE3))

from evaluation.metrics import build_official_stage1_cases as builder  # noqa: E402


class ResolveSourceTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.cache = self.root / 'cache'
        self.checkout = self.cache / 'proj' / 'owner__repo__abc'
        (self.checkout / 'contracts/types').mkdir(parents=True)
        self.old_cache = builder.CACHE_ROOT
        builder.CACHE_ROOT = self.cache

    def tearDown(self):
        builder.CACHE_ROOT = self.old_cache
        self.temp.cleanup()

    def _url(self, path):
        return f'https://github.com/owner/repo/blob/abc/{path}'

    def test_prefers_contract_source_when_first_url_is_library_only(self):
        library = self.checkout / 'contracts/types/Library.sol'
        target = self.checkout / 'contracts/Target.sol'
        library.write_text('library TargetLib {}\n')
        target.write_text('contract Target {}\n')
        urls = [self._url('contracts/types/Library.sol'),
                self._url('contracts/Target.sol')]
        finding = {'title': 'Target path can be reached',
                   'body': 'Target is the deployed entrypoint',
                   'proof_of_concept': ''}

        source, source_url, reason = builder._resolve_source(
            'proj', urls, finding)

        self.assertEqual(str(target.resolve()), source)
        self.assertEqual(urls[1], source_url)
        self.assertEqual('contract_source_from_finding_urls', reason)

    def test_keeps_library_only_source_when_no_contract_candidate(self):
        library = self.checkout / 'contracts/types/Library.sol'
        library.write_text('library TargetLib {}\n')
        urls = [self._url('contracts/types/Library.sol')]

        source, source_url, reason = builder._resolve_source('proj', urls, {})

        self.assertEqual(str(library.resolve()), source)
        self.assertEqual(urls[0], source_url)
        self.assertEqual('library_only_available', reason)


if __name__ == '__main__':
    unittest.main()
