import unittest
from pathlib import Path

from lib.anchor_resolver import resolve_anchors
from lib.solidity_scan import scan_src

CASES = Path(__file__).resolve().parents[1] / 'cases'


class AnchorResolverRealCaseTest(unittest.TestCase):
    def test_panoptic_is_single_anchor_builder_wallet(self):
        case = CASES / 'panoptic_builder_init'
        result = resolve_anchors(case / 'stage2_run', 'core_claim', case / 'src')
        self.assertEqual(result['bindability'], 'single_anchor')
        self.assertEqual(result['suggested_patch_contract'], 'BuilderWallet')
        self.assertTrue(result['dynamically_expressible'])
        for row in result['symbols']:
            self.assertIsNotNone(row['anchor'], row['symbol'])

    def test_intuition_cross_contract_is_multi_contract(self):
        case = CASES / ('Intuition_2VUsxVJwReb__6YNDfbQYkTa__KcTHtNrsMFs')
        result = resolve_anchors(
            case / 'stage2_run',
            'impact_claim_dos_via_expired_window_8ceee315_ddfa6e3d',
            case / 'src')
        self.assertEqual(result['bindability'], 'multi_contract')
        self.assertIsNone(result['suggested_patch_contract'])
        self.assertFalse(result['dynamically_expressible'])


if __name__ == '__main__':
    unittest.main()
