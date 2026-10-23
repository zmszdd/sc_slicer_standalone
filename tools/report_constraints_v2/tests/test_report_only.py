"""Synthetic compiler controls; NOT evaluation of model extraction accuracy."""
import unittest

import z3

from lib import report_only as r

TEXT = 'The operation should not fail solely because the supplied fee exceeds the quote.'


def fixture():
    def symbol(sort, unit):
        return {'sort': sort, 'unit': unit, 'meaning': 'synthetic test observation',
                'checkpoint': 'input', 'evidence': TEXT}
    def prop(expr):
        return {'text': 'synthetic compiler control', 'expression': expr,
                'evidence': [TEXT], 'derivation': 'test only'}
    fee = {'op': 'gt', 'args': [{'var': 'paid'}, {'var': 'quoted'}]}
    safe = {'op': 'implies', 'args': [fee, {'op': 'not', 'args': [{'var': 'fee_revert'}]}]}
    return {'symbols': {'paid': symbol('int', 'wei'), 'quoted': symbol('int', 'wei'),
                        'fee_revert': symbol('bool', None)},
            'properties': {'preconditions': prop(None), 'safety': prop(safe), 'effects': prop(None)},
            'assumptions': [], 'unresolved': []}


class ReportOnlyTests(unittest.TestCase):
    def test_safety_only_is_complete_candidate(self):
        result, smt = r.compile_spec(fixture(), TEXT)
        self.assertEqual(result['formalization_status'], 'formalized_candidate')
        self.assertEqual(result['code_alignment_status'], 'not_attempted')
        self.assertEqual(result['consistency_verdict'], 'not_evaluated')
        self.assertIn('(define-fun report_safety', smt)
        self.assertNotIn('(assert report_safety)', smt)
        z3.parse_smt2_string(smt)

    def test_missing_safety(self):
        x = fixture(); x['properties']['safety']['expression'] = None
        self.assertEqual(r.compile_spec(x, TEXT)[0]['formalization_status'], 'not_formalized')

    def test_explicit_abstention_without_symbols(self):
        x = fixture(); x['symbols'] = {}
        for prop in x['properties'].values(): prop['expression'] = None
        self.assertEqual(r.compile_spec(x, TEXT)[0]['formalization_status'], 'not_formalized')

    def test_conflicting_premise(self):
        x = fixture(); x['properties']['preconditions']['expression'] = {'const': False}
        self.assertEqual(r.compile_spec(x, TEXT)[0]['formalization_status'], 'needs_review')

    def test_tautological_safety(self):
        x = fixture(); x['properties']['safety']['expression'] = {'const': True}
        self.assertEqual(r.compile_spec(x, TEXT)[0]['formalization_status'], 'needs_review')

    def test_unit_mismatch(self):
        x = fixture(); x['symbols']['quoted']['unit'] = 'token'
        with self.assertRaises(ValueError): r.compile_spec(x, TEXT)

    def test_unsupported_operator(self):
        x = fixture(); x['properties']['safety']['expression']['op'] = 'call'
        with self.assertRaises(ValueError): r.compile_spec(x, TEXT)

    def test_fake_evidence(self):
        x = fixture(); x['symbols']['paid']['evidence'] = 'not in report'
        with self.assertRaises(ValueError): r.compile_spec(x, TEXT)

    def test_no_silent_assumptions(self):
        x = fixture(); x['assumptions'] = ['paid is nonnegative']
        smt = r.compile_spec(x, TEXT)[1]
        self.assertNotIn('(>= paid 0)', smt)

    def test_strip_poc_fix_and_code(self):
        body = '## Description\nkeep\n```solidity\nBUG_CODE\n```\nimpact\n## Recommended mitigation steps\nFIX\n## Proof of Concept\nPOC'
        self.assertEqual(r.prose_only(body), '## Description\nkeep\nimpact')

    def test_report_json_includes_recommendation_as_report_grounded_i_source(self):
        report = {
            'title': 'Unauthorized withdrawal',
            'body': '## Finding description and impact\nAnyone can withdraw.\n'
                    '## Recommended mitigation steps\nSECRET_FIX',
            'proof_of_concept': 'SECRET_POC',
            'source_record': {'raw': 'SECRET_RAW'},
            'pairing': {'note': 'SECRET_PAIRING'},
        }
        text, policy = r.report_json_input(report)
        self.assertIn('Unauthorized withdrawal', text)
        self.assertIn('Anyone can withdraw.', text)
        self.assertIn('SECRET_FIX', text)
        self.assertNotIn('SECRET_POC', text)
        self.assertNotIn('SECRET_RAW', text)
        self.assertNotIn('SECRET_PAIRING', text)
        self.assertEqual(policy['source_format'], 'report.json')
        self.assertEqual(policy['selected_fields'],
                         ['title', 'body.description_impact_and_recommendations'])

    def test_duplicate_json_title_is_removed(self):
        report = {
            'title': '[H-01]Missing Caller Authorization',
            'body': '# Missing Caller Authorization\n\n## Impact\nFunds can be stolen.',
        }
        text, policy = r.report_json_input(report)
        self.assertEqual(text.count('Missing Caller Authorization'), 1)
        self.assertEqual(text, '# Missing Caller Authorization\n\n## Impact\nFunds can be stolen.')
        self.assertTrue(policy['title_deduplicated'])
        self.assertEqual(policy['selected_fields'],
                         ['body.description_impact_and_recommendations'])

    def test_distinct_json_title_is_kept(self):
        text, policy = r.report_json_input({
            'title': 'Unauthorized withdrawal',
            'body': '## Finding description and impact\nAnyone can withdraw.',
        })
        self.assertTrue(text.startswith('Unauthorized withdrawal\n\n'))
        self.assertFalse(policy['title_deduplicated'])

    def test_report_json_requires_body(self):
        with self.assertRaises(ValueError):
            r.report_json_input({'title': 'missing body', 'proof_of_concept': 'code'})

    def test_poc_first(self):
        self.assertEqual(r.prose_only('description\n## Proof of Concept\ncode'), 'description')

    def test_resume_impact_after_poc_without_leaking_poc(self):
        body = ('## Description\nThe guard fails.\n## Proof of Concept steps\n'
                'SECRET_POC\n```solidity\n## Impact\nSECRET_CODE\n```\n'
                '## Impact Assessment\nRewards remain claimable.\n'
                '## Recommended mitigation steps\nSECRET_FIX')
        result = r.prose_only(body)
        self.assertIn('Rewards remain claimable.', result)
        self.assertNotIn('SECRET_', result)

    def test_resume_summary_after_mitigation_placeholder(self):
        body = ('## Finding description and impact\nWrite a description.\n'
                '## Recommended mitigation steps\nSECRET_FIX\n'
                '## Summary\nA relayer can alter validity bounds.\n'
                '## Vulnerability Details\nThe signature suffix is unauthenticated.')
        result = r.prose_only(body)
        self.assertIn('A relayer can alter validity bounds.', result)
        self.assertIn('signature suffix is unauthenticated.', result)
        self.assertNotIn('SECRET_FIX', result)

    def test_nested_impact_in_mitigation_does_not_resume(self):
        body = ('## Description\nAn error.\n## Mitigation\n'
                '### Impact\nSECRET_FIX_DETAIL\n## Impact\nUsers lose funds.')
        result = r.prose_only(body)
        self.assertIn('Users lose funds.', result)
        self.assertNotIn('SECRET_FIX_DETAIL', result)

    def test_v2_report_input_replay_still_stops_at_first_exclusion(self):
        report = {'title': 'A report', 'body': '## Description\nBefore.\n'
                  '## Proof of Concept\nPOC\n## Impact\nAfter.'}
        old_text, old_policy = r.report_json_input(report, input_policy_version=2)
        new_text, new_policy = r.report_json_input(report, input_policy_version=3)
        self.assertEqual(old_policy['policy_version'], 'report-json-input/2')
        self.assertEqual(new_policy['policy_version'], 'report-json-input/3')
        self.assertNotIn('After.', old_text)
        self.assertIn('After.', new_text)
        self.assertNotIn('POC\n', new_text)

    def test_v4_excludes_unheaded_mitigation_and_preserves_v3_replay(self):
        report = {'title': 'Balance decrease',
                  'body': ('## Impact Assessment\nUnderflow blocks rewards.\n\n'
                           'Recommended mitigation steps\nImmediate Fix\n'
                           'Replace the subtraction.\n## Impact\nUsers cannot claim. ')}
        previous, old_policy = r.report_json_input(report, input_policy_version=3)
        current, new_policy = r.report_json_input(report, input_policy_version=4)
        self.assertIn('Replace the subtraction.', previous)
        self.assertNotIn('Replace the subtraction.', current)
        self.assertIn('Users cannot claim.', current)
        self.assertEqual(old_policy['policy_version'], 'report-json-input/3')
        self.assertEqual(new_policy['policy_version'], 'report-json-input/4')

    def test_inline_triple_backticks_not_fence(self):
        body = '## Impact\n```withdraw()```\nUsers receive fewer tokens.\n## Mitigation\nfix'
        self.assertIn('Users receive fewer tokens.', r.prose_only(body))
        self.assertIn('```withdraw()```', r.prose_only(body))

    def test_fence_length_and_type_must_match(self):
        body = 'keep\n````solidity\n```\n~~~\nsecret\n````\nimpact'
        self.assertEqual(r.prose_only(body), 'keep\nimpact')

    def test_address_identity_not_integer(self):
        x = fixture(); x['symbols']['paid']['sort'] = 'address'; x['symbols']['paid']['unit'] = None
        with self.assertRaises(ValueError): r.compile_spec(x, TEXT)

    def test_quantity_not_boolean(self):
        x = fixture(); x['properties']['safety']['expression'] = {'var': 'paid'}
        with self.assertRaises(ValueError): r.compile_spec(x, TEXT)

if __name__ == '__main__': unittest.main()
