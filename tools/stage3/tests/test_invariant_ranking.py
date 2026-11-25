import json
import tempfile
import unittest
from pathlib import Path

from lib.invariant_ranking import rank_claims


class InvariantRankingTests(unittest.TestCase):
    def test_top_k_prefers_transition_contract(self):
        with tempfile.TemporaryDirectory() as tmp:
            stage2 = Path(tmp)
            (stage2 / 'invariant-candidates.json').write_text(json.dumps({
                'schema_version': 'report-invariant-candidates/1',
                'claims': {
                    'strong': {'selected_candidate_id': 'strong::canonical',
                               'candidates': [{'candidate_id': 'strong::canonical',
                                               'score': 3.0,
                                               'quality_labels': [],
                                               'derivation': 'canonical_formalization'}]},
                    'weak': {'selected_candidate_id': 'weak::canonical',
                             'candidates': [{'candidate_id': 'weak::canonical',
                                             'score': 1.0,
                                             'quality_labels': ['I_SNAPSHOT_ONLY'],
                                             'derivation': 'canonical_formalization'}]},
                },
            }))
            spec = {'claims': [
                {'claim_id': 'weak', 'formalization_contract': {
                    'route': 'auto_assert', 'can_auto_assert': True,
                    'semantic_profile': {'bucket': 'snapshot_only'},
                    'problems': [{'code': 'I_SNAPSHOT_ONLY'}]}},
                {'claim_id': 'strong', 'formalization_contract': {
                    'route': 'auto_assert', 'can_auto_assert': True,
                    'semantic_profile': {'bucket': 'transition',
                                         'has_before_after': True},
                    'i_v': {'independent': True}}},
            ]}
            ranking = rank_claims(stage2, spec, limit=1)
            self.assertEqual(ranking['selected_claim_ids'], ['strong'])
            self.assertEqual([row['claim_id'] for row in ranking['ranked']],
                             ['strong', 'weak'])
            self.assertIn('strong::canonical',
                          [row['selected_candidate_id']
                           for row in ranking['selected']])

    def test_zero_limit_keeps_all_claims(self):
        with tempfile.TemporaryDirectory() as tmp:
            spec = {'claims': [{'claim_id': 'only'}, {'claim_id': 'other'}]}
            ranking = rank_claims(Path(tmp), spec, limit=0)
            self.assertEqual(len(ranking['selected_claim_ids']), 2)


if __name__ == '__main__':
    unittest.main()
