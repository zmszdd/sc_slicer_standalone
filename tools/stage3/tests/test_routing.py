import unittest
from pathlib import Path

from lib.routing import (AUTO_ASSERT, REFERENCE_PATCH_CROSS_CONTRACT,
                         REFERENCE_PATCH_SHOULD_BE, classify_route)

CASES = Path(__file__).resolve().parents[1] / 'cases'


class RoutingRealCaseTest(unittest.TestCase):
    def test_panoptic_routes_to_auto_assert(self):
        case = CASES / 'panoptic_builder_init'
        route = classify_route(case / 'stage2_run', 'core_claim', case / 'src')
        self.assertEqual(route['route'], AUTO_ASSERT)
        self.assertTrue(route['auto_verifiable'])
        self.assertFalse(route['requires_reference_patch'])
        self.assertEqual(route['suggested_patch_contract'], 'BuilderWallet')

    def test_intuition_cross_contract_routes_to_reference_patch(self):
        case = CASES / ('Intuition_2VUsxVJwReb__6YNDfbQYkTa__KcTHtNrsMFs')
        if not case.is_dir():
            self.skipTest('optional real-case fixture is not present')
        route = classify_route(
            case / 'stage2_run',
            'impact_claim_dos_via_expired_window_8ceee315_ddfa6e3d',
            case / 'src')
        self.assertEqual(route['route'], REFERENCE_PATCH_CROSS_CONTRACT)
        self.assertFalse(route['auto_verifiable'])
        self.assertTrue(route['requires_reference_patch'])

    def test_refpatch_cross_contract_fixture_routes_to_reference_patch(self):
        case = CASES / 'refpatch_cross_contract'
        if not case.is_dir():
            self.skipTest('optional real-case fixture is not present')
        route = classify_route(case / 'stage2_run',
                               'claim_cross_contract_refpatch', case / 'src')
        self.assertEqual(route['route'], REFERENCE_PATCH_CROSS_CONTRACT)
        self.assertEqual(route['bindability'], 'multi_contract')
        self.assertTrue(route['requires_reference_patch'])
        self.assertFalse(route['auto_verifiable'])

    def test_no_anchor_routes_to_should_be(self):
        from lib.routing import _route_for_anchors
        anchors = {
            'bindability': 'no_anchor',
            'suggested_patch_contract': None,
        }
        route, reason, auto_verifiable = _route_for_anchors(anchors)
        self.assertEqual(route, REFERENCE_PATCH_SHOULD_BE)
        self.assertIn('no observable code anchor', reason)
        self.assertFalse(auto_verifiable)


if __name__ == '__main__':
    unittest.main()
