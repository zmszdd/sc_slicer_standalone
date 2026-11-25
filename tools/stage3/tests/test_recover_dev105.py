import json
import unittest

from evaluation.metrics import recover_dev105 as rd


class FixableClaimsTest(unittest.TestCase):
    def test_uses_bound_claim_ids(self):
        row = {
            'status': 'done',
            'bound_claim_ids': ['c1', 'c2', 'c3'],
            'verdicts': ['partial_binding', 'violation_reproduced', 'compile_error'],
        }
        self.assertEqual(rd._fixable_claims(row),
                         [('c1', 'partial_binding'), ('c3', 'compile_error')])

    def test_falls_back_to_claim_ids(self):
        row = {
            'status': 'done',
            'claim_ids': ['c1'],
            'verdicts': ['binding_error'],
        }
        self.assertEqual(rd._fixable_claims(row), [('c1', 'binding_error')])

    def test_non_fixable_verdicts_are_skipped(self):
        row = {
            'status': 'done',
            'bound_claim_ids': ['c1', 'c2'],
            'verdicts': ['not_dynamically_expressible', 'reference_patch_required'],
        }
        self.assertEqual(rd._fixable_claims(row), [])


class RecountTest(unittest.TestCase):
    def test_recount(self):
        row = {'verdicts': ['violation_reproduced', 'compile_error',
                            'reference_patch_required', 'compile_blocked',
                            'not_dynamically_expressible', 'halt_witness_required']}
        rd._recount(row)
        self.assertEqual(row['reproduced'], 1)
        self.assertEqual(row['compile_error'], 1)
        self.assertEqual(row['reference_patch_required'], 1)
        self.assertEqual(row['compile_blocked'], 1)
        self.assertEqual(row['not_dynamically_expressible'], 1)
        self.assertEqual(row['halt_witness_required'], 1)


class ParsePayloadTest(unittest.TestCase):
    def test_parses_aggregate_from_multiline(self):
        stdout = '\n'.join([
            json.dumps({'claim_id': 'c1', 'status': 'accepted',
                        'verdict': 'violation_reproduced'}),
            json.dumps({'claims': [{'claim_id': 'c1',
                                    'verdict': 'violation_reproduced'}]}),
        ])
        self.assertEqual(rd._parse_payload(stdout)['claims'][0]['claim_id'], 'c1')

    def test_no_payload(self):
        self.assertIsNone(rd._parse_payload('noise'))


if __name__ == '__main__':
    unittest.main()
