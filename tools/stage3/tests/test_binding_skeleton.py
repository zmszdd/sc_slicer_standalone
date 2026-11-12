import unittest
from pathlib import Path

from lib.binding_skeleton import _candidate_analysis, build_skeleton
from lib.binding import load_binding, validate_binding
from lib.spec_loader import load_stage2_run

CASE = Path(__file__).resolve().parents[1] / 'cases' / 'panoptic_builder_init'


class BindingSkeletonTest(unittest.TestCase):
    def test_skeleton_covers_required_symbols(self):
        stage2 = load_stage2_run(CASE / 'stage2_run')
        skeleton = build_skeleton(CASE / 'stage2_run', 'core_claim')
        claim_id, entries = validate_binding(skeleton, stage2['spec'])
        self.assertEqual(claim_id, 'core_claim')
        self.assertEqual(set(entries), {'init_publicly_callable',
                                        'caller_is_any_eoa',
                                        'builder_admin_overwritten'})
        self.assertEqual(entries['init_publicly_callable']['checkpoint'], 'before')
        self.assertEqual(entries['builder_admin_overwritten']['checkpoint'], 'after')
        self.assertTrue(all('TODO_BIND_' in row['solidity_expr']
                            for row in entries.values()))

    def test_skeleton_annotates_observability(self):
        stage2 = load_stage2_run(CASE / 'stage2_run')
        skeleton = build_skeleton(CASE / 'stage2_run', 'core_claim',
                                  src=CASE / 'src')
        for entry in skeleton['bindings'].values():
            self.assertIn(entry.get('observability'),
                          {'high', 'medium', 'low'})

    def test_candidate_analysis_drops_out_of_scope(self):
        symbol = {'entity_ids': ['gHybr'], 'meaning': 'total supply'}
        declared = {'gHybr', 'hybr', 'totalSupply', 'unrelated'}
        candidates, observability = _candidate_analysis(
            symbol, declared, scope={'hybr', 'totalSupply'},
            state_vars={'gHybr', 'hybr'})
        self.assertNotIn('gHybr', candidates)
        self.assertIn('hybr', candidates)
        self.assertIn('totalSupply', candidates)
        self.assertEqual(observability, 'medium')


if __name__ == '__main__':
    unittest.main()
