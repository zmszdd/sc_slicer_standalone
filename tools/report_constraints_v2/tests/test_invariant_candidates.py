import unittest

from lib import invariant_candidates as ic


class InvariantCandidateTests(unittest.TestCase):
    def test_normalize_checkpoint(self):
        self.assertEqual(ic.normalize_checkpoint('before withdraw'), 'before')
        self.assertEqual(ic.normalize_checkpoint('after sweep completes'), 'after')
        self.assertEqual(ic.normalize_checkpoint('at all times'), 'snapshot')
        self.assertEqual(ic.normalize_checkpoint(None), 'missing')

    def test_build_ranks_canonical_and_keeps_explicit_alternatives(self):
        elements = {'statements': [
            {'id': 'si_admin', 'kind': 'security_intent',
             'text': 'Only the owner may set the admin.',
             'evidence': ['Only the owner may set the admin.']},
            {'id': 'si_guard', 'kind': 'security_intent',
             'text': 'The admin must never change after deployment.',
             'evidence': ['The admin must never change after deployment.']},
        ]}
        formal = {
            'symbols': {
                'admin_before': {'checkpoint': 'before init call'},
                'admin_after': {'checkpoint': 'after init call'},
            },
            'claims': [{
                'id': 'claim_1', 'impact_ids': ['impact_1'],
                'properties': {'safety': {
                    'text': 'The admin may only be set by the owner.',
                    'expression': {'op': 'eq', 'args': [
                        {'var': 'admin_before'}, {'var': 'admin_after'}]},
                }},
            }],
        }
        weak = {'claims': {'claim_1': {'diagnostics': [
            {'code': 'I_SNAPSHOT_ONLY'}], 'buckets': ['snapshot_only']}}}
        plans = {'claim_1': {'intent_id': 'si_admin'}}
        result = ic.build(elements, formal, weak_triage=weak,
                          applicability={'impacts': [
                              {'impact_id': 'impact_1',
                               'intent_ids': ['si_admin', 'si_guard']}]},
                          plans=plans)
        row = result['claims']['claim_1']
        self.assertEqual(row['selected_candidate_id'], 'claim_1::canonical')
        self.assertEqual(len(row['candidates']), 2)
        canonical = row['candidates'][0]
        self.assertTrue(canonical['executable'])
        self.assertEqual(canonical['checkpoints']['normalized'],
                         {'admin_before': 'before', 'admin_after': 'after'})
        self.assertIn('I_SNAPSHOT_ONLY', canonical['quality_labels'])
        alternate = next(candidate for candidate in row['candidates']
                         if candidate['candidate_id'] == 'claim_1::si_guard')
        self.assertFalse(alternate['executable'])
        self.assertEqual(alternate['derivation'], 'explicit_report_intent')
        self.assertEqual(alternate['evidence_ids'],
                         ['The admin must never change after deployment.'])


if __name__ == '__main__':
    unittest.main()
