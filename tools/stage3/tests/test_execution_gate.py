import json
import tempfile
import unittest
from pathlib import Path

from lib.execution_gate import (adjudicate, inspect, is_trusted_negative,
                                load_trusted_label, negative_witness, preflight,
                                trusted_rejection)


def formal(*, i_expr=None, v_expr=None, scope='A user can steal deposited funds.'):
    return {
        'symbols': {
            'p': {'sort': 'bool'}, 'i': {'sort': 'bool'},
            'v': {'sort': 'bool'}, 'lost': {'sort': 'bool'}},
        'claims': [{
            'id': 'c',
            'scope': scope,
            'impact_ids': ['fund_loss'],
            'properties': {
                'preconditions': {'text': 'Attacker starts a call.',
                                  'expression': {'var': 'p'}},
                'safety': {'text': 'Caller must be authorized.',
                           'expression': i_expr or {'var': 'i'}},
                'effects': {'text': 'Funds are stolen.',
                            'expression': v_expr or {
                                'op': 'and', 'args': [
                                    {'op': 'not', 'args': [{'var': 'i'}]},
                                    {'var': 'lost'}]}},
            },
        }],
    }


def binding(**expressions):
    values = {'p': 'msg.sender == attacker', 'i': 'authorized',
              'v': '!authorized && lost', 'lost': 'balanceOf(victim) == 0'}
    values.update(expressions)
    return {'bindings': {
        name: {'solidity_expr': expr, 'checkpoint': 'before'}
        for name, expr in values.items()
    }}


class ExecutionGateTest(unittest.TestCase):
    def test_constant_invariant_is_rejected(self):
        gate = inspect(formal(), binding(i='false'), 'c')
        self.assertEqual(gate['status'], 'reject')
        self.assertEqual(gate['category'], 'binding_error')
        self.assertIn('CONSTANT_INVARIANT', gate['codes'])

    def test_constant_effect_is_rejected(self):
        gate = inspect(formal(), binding(lost='false'), 'c')
        self.assertEqual(gate['status'], 'reject')
        self.assertIn('CONSTANT_EFFECT', gate['codes'])

    def test_administrative_dust_griefing_is_impact_insufficient(self):
        claim = formal(
            scope=('An attacker front-runs unregisterVault with a dust '
                   'donation and blocks vault management.'),
            i_expr={'var': 'i'}, v_expr={'var': 'lost'})
        claim['claims'][0]['properties']['effects']['text'] = (
            'Vault management is blocked by a dust donation.')
        claim['claims'][0]['impact_ids'] = ['owner_cannot_unregister_vault']
        gate = inspect(claim, binding(), 'c')
        self.assertEqual(gate['status'], 'reject')
        self.assertEqual(gate['category'], 'impact_insufficient')
        self.assertIn('IMPACT_ADMIN_GRIEFING_ONLY', gate['codes'])

    def test_effect_with_independent_symbol_passes(self):
        gate = inspect(formal(), binding(), 'c')
        self.assertEqual(gate['status'], 'pass')
        self.assertTrue(gate['effect_independent'])

    def test_same_symbols_without_negation_is_not_independent(self):
        claim = formal(i_expr={'var': 'i'}, v_expr={'var': 'i'})
        gate = inspect(claim, binding(), 'c')
        self.assertFalse(gate['effect_independent'])
        self.assertIn('EFFECT_NOT_INDEPENDENT', gate['codes'])

    def test_expanded_implication_complement_is_independent(self):
        amount = {'var': 'amount'}
        minted = {'var': 'minted'}
        entitled = {'var': 'entitled'}
        claim = formal(
            i_expr={'op': 'implies', 'args': [
                {'op': 'gt', 'args': [amount, {'const': 0}]},
                {'op': 'ge', 'args': [minted, entitled]}]},
            v_expr={'op': 'and', 'args': [
                {'op': 'gt', 'args': [amount, {'const': 0}]},
                {'op': 'not', 'args': [
                    {'op': 'ge', 'args': [minted, entitled]}]},
                {'op': 'lt', 'args': [minted, entitled]}]})
        gate = inspect(claim, binding(), 'c')
        self.assertTrue(gate['effect_independent'])
        self.assertNotIn('EFFECT_NOT_INDEPENDENT', gate['codes'])

    def test_permanent_lock_and_unauthorized_transfer_are_strong(self):
        locked = formal(scope='Funds are permanently locked after the call.')
        gate = inspect(locked, binding(), 'c')
        self.assertEqual(gate['status'], 'pass')
        self.assertEqual(gate['impact_class'], 'permanent_lock')
        stolen = formal(scope='The attacker performs an unauthorized transfer.')
        gate = inspect(stolen, binding(), 'c')
        self.assertEqual(gate['status'], 'pass')
        self.assertEqual(gate['impact_class'], 'unauthorized_transfer')

    def test_governance_and_dust_griefing_are_insufficient(self):
        governance = formal(
            scope='An attacker blocks a governance proposal from reaching quorum.')
        governance['claims'][0]['properties']['effects']['text'] = (
            'The governance proposal is blocked.')
        governance['claims'][0]['impact_ids'] = ['governance_blocked']
        gate = inspect(governance, binding(), 'c')
        self.assertEqual(gate['status'], 'reject')
        self.assertEqual(gate['impact_class'], 'governance_griefing')
        self.assertIn('IMPACT_GOVERNANCE_GRIEFING', gate['codes'])
        dust = formal(scope='A donation causes a denial-of-service for swaps.')
        dust['claims'][0]['properties']['effects']['text'] = (
            'Swaps are blocked by the donation.')
        dust['claims'][0]['impact_ids'] = ['swap_dos']
        gate = inspect(dust, binding(), 'c')
        self.assertEqual(gate['status'], 'reject')
        self.assertEqual(gate['impact_class'], 'dust_or_donation_dos')
        self.assertIn('IMPACT_DUST_OR_DONATION_DOS', gate['codes'])

    def test_trusted_judge_invalid_overrides_strong_prose(self):
        gate = inspect(formal(), binding(), 'c',
                       trusted_label={'claim_id': 'c', 'validity': 'invalid'})
        self.assertEqual(gate['status'], 'reject')
        self.assertEqual(gate['category'], 'impact_insufficient')
        self.assertIn('TRUSTED_JUDGE_INVALID', gate['codes'])

    def test_trusted_impact_insufficient_is_not_text_inferred(self):
        gate = inspect(
            formal(), binding(), 'c',
            trusted_label={'claim_id': 'c',
                           'impact_sufficiency': 'insufficient'})
        self.assertEqual(gate['status'], 'reject')
        self.assertEqual(gate['impact_class'], 'trusted_insufficient')

    def test_trusted_rejection_reports_negative_label_without_verdict(self):
        rejection = trusted_rejection(
            {'claim_id': 'c', 'impact_sufficiency': 'insufficient'})
        self.assertEqual(rejection['code'], 'TRUSTED_IMPACT_INSUFFICIENT')
        self.assertNotIn('consistency_verdict', rejection)
        self.assertIsNone(trusted_rejection({'claim_id': 'c',
                                             'validity': 'valid'}))

    def test_preflight_never_consults_trusted_label(self):
        gate = preflight(formal(), binding(), 'c')
        self.assertEqual(gate['status'], 'pass')
        self.assertEqual(gate['decision_phase'], 'pre_execution')
        self.assertEqual(gate['impact_sufficiency'], 'not_evaluated')

    def test_adjudication_preserves_reproduced_negative_as_fp(self):
        label = {'claim_id': 'c', 'validity': 'invalid',
                 'label_scope': 'case'}
        structural = preflight(formal(), binding(), 'c')
        gate = adjudicate(
            formal(), binding(), 'c', trusted_label=label,
            preflight_result=structural,
            execution={'consistency_verdict': 'violation_reproduced'})
        self.assertEqual(gate['status'], 'reject')
        self.assertEqual(gate['category'], 'impact_insufficient')
        self.assertEqual(gate['consistency_verdict'], 'violation_reproduced')
        self.assertTrue(gate['metric_eligibility']['consistency'])
        self.assertEqual(gate['report_impact_sufficiency'], 'strong')
        self.assertIsNone(gate['metric_eligibility'][
            'consistency_exclusion_reason'])
        self.assertFalse(gate['metric_eligibility']['vulnerability'])
        self.assertEqual(gate['decision_phase'], 'post_execution')

    def test_report_impact_insufficient_blocks_consistency(self):
        claim = formal(
            scope=('An attacker front-runs unregisterVault with a dust '
                   'donation and blocks vault management.'),
            i_expr={'var': 'i'}, v_expr={'var': 'lost'})
        claim['claims'][0]['properties']['effects']['text'] = (
            'Vault management is blocked by a dust donation.')
        claim['claims'][0]['impact_ids'] = ['owner_cannot_unregister_vault']
        gate = adjudicate(
            claim, binding(), 'c',
            execution={'consistency_verdict': 'violation_reproduced'})
        self.assertEqual(gate['report_impact_sufficiency'], 'insufficient')
        self.assertEqual(gate['report_impact_class'],
                         'administrative_griefing')
        self.assertFalse(gate['metric_eligibility']['consistency'])
        self.assertEqual(gate['metric_eligibility'][
            'consistency_exclusion_reason'], 'IMPACT_ADMIN_GRIEFING_ONLY')
        self.assertFalse(gate['metric_eligibility']['vulnerability'])

    def test_trusted_label_never_enters_consistency_gate(self):
        gate = adjudicate(
            formal(), binding(), 'c',
            trusted_label={'claim_id': 'c', 'validity': 'invalid'},
            execution={'consistency_verdict': 'violation_reproduced'})
        self.assertTrue(gate['metric_eligibility']['consistency'])
        self.assertEqual(gate['report_impact_sufficiency'], 'strong')
        self.assertFalse(gate['metric_eligibility']['vulnerability'])

    def test_load_trusted_label_from_case_ledger(self):
        with tempfile.TemporaryDirectory() as tmp:
            case_dir = Path(tmp) / 'case'
            case_dir.mkdir()
            (case_dir / 'judge_ground_truth.json').write_text(json.dumps({
                'rows': [{'claim_id': 'c', 'validity': 'invalid',
                          'reason': 'judge rejected'}]}))
            label = load_trusted_label(case_dir, 'c')
        self.assertEqual(label['validity'], 'invalid')
        self.assertEqual(label['label_scope'], 'claim')

    def test_case_level_trusted_label_is_marked_as_case_scope(self):
        with tempfile.TemporaryDirectory() as tmp:
            case_dir = Path(tmp) / 'case'
            case_dir.mkdir()
            (case_dir / 'judge_ground_truth.json').write_text(json.dumps({
                'cases': [{'case': 'case', 'validity': 'invalid',
                           'reason': 'judge rejected'}]}))
            label = load_trusted_label(case_dir, 'anything')
        self.assertEqual(label['label_scope'], 'case')

    def test_negative_witness_requires_all_three_queries(self):
        queries = {'P_and_T': 'sat', 'P_and_T_and_not_V': 'sat',
                   'P_and_T_and_not_I': 'unsat'}
        self.assertTrue(negative_witness({'code_query_results': queries})[
            'eligible'])
        partial = dict(queries, P_and_T_and_not_V='unknown')
        record = negative_witness({'code_query_results': partial})
        self.assertFalse(record['eligible'])
        self.assertEqual(record['missing'], ['effect_absent'])

    def test_trusted_negative_is_only_a_probe_route_hint(self):
        self.assertTrue(is_trusted_negative({
            'impact_sufficiency': 'insufficient'}))
        self.assertTrue(is_trusted_negative({'validity': 'invalid'}))
        self.assertFalse(is_trusted_negative({}))

    def test_adjudication_records_negative_eligibility_without_rewrite(self):
        gate = adjudicate(
            formal(), binding(), 'c',
            execution={
                'consistency_verdict': 'violation_not_reproduced',
                'code_query_results': {
                    'P_and_T': 'sat', 'P_and_T_and_not_V': 'sat',
                    'P_and_T_and_not_I': 'unsat'}})
        self.assertTrue(gate['metric_eligibility']['negative'])
        self.assertEqual(gate['consistency_verdict'],
                         'violation_not_reproduced')


if __name__ == '__main__':
    unittest.main()
