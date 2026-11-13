import unittest

from cli.stage3_eval_run import _ceiling_verdict_for_bindability
from lib.bindability_contract import is_hard_ceiling


class CeilingRoutingTest(unittest.TestCase):
    def test_no_anchor_low_observability_routes_to_not_dynamically_expressible(self):
        # Genuinely unobservable: the deterministic matcher saw no signal for
        # an anchoring symbol, so there is nothing for the binding LLM to bind.
        self.assertEqual(
            _ceiling_verdict_for_bindability('no_anchor', 'low'),
            'not_dynamically_expressible')

    def test_no_anchor_medium_observability_keeps_llm_attempt(self):
        # Fuzzy-token false negative (report wording != code identifier):
        # still hand it to the binding LLM instead of discarding the claim.
        self.assertIsNone(
            _ceiling_verdict_for_bindability('no_anchor', 'medium'))

    def test_no_anchor_high_observability_keeps_llm_attempt(self):
        self.assertIsNone(
            _ceiling_verdict_for_bindability('no_anchor', 'high'))

    def test_no_anchor_missing_observability_keeps_llm_attempt(self):
        # Backward compatibility: without observability we must not discard a
        # claim (the old schema may not have the field).
        self.assertIsNone(_ceiling_verdict_for_bindability('no_anchor'))

    def test_multi_contract_keeps_llm_attempt(self):
        # Regression: the aggressive multi_contract pre-route killed
        # reproducible claims; keep the LLM attempt for this class.
        self.assertIsNone(_ceiling_verdict_for_bindability('multi_contract'))

    def test_dynamic_classes_are_not_routed(self):
        for bindability in ('single_anchor', 'file_level', 'unknown', None):
            self.assertIsNone(_ceiling_verdict_for_bindability(bindability))


class HardCeilingTest(unittest.TestCase):
    def test_only_low_no_anchor_is_hard_ceiling(self):
        self.assertTrue(is_hard_ceiling(
            {'bindability': 'no_anchor', 'anchor_observability': 'low'}))
        self.assertFalse(is_hard_ceiling(
            {'bindability': 'no_anchor', 'anchor_observability': 'medium'}))
        self.assertFalse(is_hard_ceiling(
            {'bindability': 'no_anchor', 'anchor_observability': 'high'}))
        self.assertFalse(is_hard_ceiling({'bindability': 'no_anchor'}))
        self.assertFalse(is_hard_ceiling(
            {'bindability': 'single_anchor', 'anchor_observability': 'low'}))
        self.assertFalse(is_hard_ceiling(
            {'bindability': 'multi_contract', 'anchor_observability': 'medium'}))


if __name__ == '__main__':
    unittest.main()
