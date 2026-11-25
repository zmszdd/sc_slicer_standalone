import sys
import unittest
from pathlib import Path

STAGE3 = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(STAGE3))
sys.path.insert(0, str(STAGE3 / 'evaluation' / 'metrics'))

from ranking_replay import (_diverse_order, _observability_key,  # noqa: E402
                            _order_rows, _summarize)


def _row(claim_id, impact_id, *, hard=0, snapshot=0, transition=1,
         independent=True, executable=True, auto=3, evidence=1,
         candidate=1.0, current=1.0, paper=0.0):
    return {
        'case': 'case', 'claim_id': claim_id, 'impact_id': impact_id,
        'hard_risk_count': hard, 'snapshot_risk_count': snapshot,
        'transition_level': transition, 'independent': independent,
        'executable': executable, 'auto_score': auto,
        'evidence_count': evidence, 'candidate_score': candidate,
        'current_rank_score': current, 'paper_score': paper,
    }


class RankingReplayTests(unittest.TestCase):
    def test_observability_order_prefers_cleaner_transition(self):
        clean = _row('clean', 'a', hard=0, snapshot=0, transition=1)
        risky = _row('risky', 'b', hard=2, snapshot=2, transition=0)
        self.assertLess(_observability_key(clean), _observability_key(risky))
        ordered = _order_rows([risky, clean], 'observability')
        self.assertEqual([row['claim_id'] for row in ordered],
                         ['clean', 'risky'])

    def test_diversity_promotes_first_occurrence_of_each_impact(self):
        rows = [_row('a1', 'a'), _row('b1', 'b'), _row('a2', 'a')]
        ordered = _diverse_order(rows)
        self.assertEqual([row['claim_id'] for row in ordered],
                         ['a1', 'b1', 'a2'])
        diverse = _order_rows(rows, 'observability_diverse')
        self.assertEqual([row['claim_id'] for row in diverse][:2], ['a1', 'b1'])

    def test_unknown_selection_is_not_counted_as_success(self):
        selected = [
            _row('known', 'a'),
            _row('unknown', 'b'),
        ]
        outcomes = {('case', 'known'): {
            'verdict': 'violation_reproduced', 'bound': True}}
        summary = _summarize(selected, outcomes, 1, {'case'})
        self.assertEqual(summary['known_outcomes'], 1)
        self.assertEqual(summary['unknown_outcomes'], 1)
        self.assertEqual(summary['reproduced_known'], 1)
        self.assertEqual(summary['known_reproduced_capture_rate'], 1.0)
        self.assertEqual(summary['stage3_completion_known_rate'], 0.5)
        self.assertEqual(summary['unknown_selected_claims'], ['unknown'])


if __name__ == '__main__':
    unittest.main()
