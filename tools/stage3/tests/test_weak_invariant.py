import unittest

from lib.weak_invariant import diagnose, gate


class WeakInvariantDiagnosticTest(unittest.TestCase):
    def formal(self):
        return {
            'symbols': {
                'p': {'sort': 'bool'}, 'i_before': {'sort': 'int'},
                'i_after': {'sort': 'int'}, 'v_before': {'sort': 'int'},
                'v_after': {'sort': 'int'}},
            'claims': [{
                'id': 'c',
                'properties': {
                    'preconditions': {'expression': {'var': 'p'}},
                    'safety': {'expression': {
                        'op': 'le', 'args': [{'var': 'i_before'},
                                             {'var': 'i_after'}]}},
                    'effects': {'expression': {
                        'op': 'lt', 'args': [{'var': 'v_before'},
                                             {'var': 'v_after'}]}},
                },
            }],
        }

    def binding(self):
        return {'bindings': {
            'p': {'checkpoint': 'input'},
            'i_before': {'checkpoint': 'state_after'},
            'i_after': {'checkpoint': 'state_after'},
            'v_before': {'checkpoint': 'before'},
            'v_after': {'checkpoint': 'after'},
        }}

    def test_checkpoint_collapse_is_high_risk(self):
        report = diagnose(self.formal(), 'c', self.binding())
        self.assertIn('I_CHECKPOINT_COLLAPSED', report['codes'])
        self.assertEqual(report['risk'], 'high')

    def test_stage2_falsifier_hint_is_carried(self):
        declaration = {'i_falsifier_hint': {'status': 'sat', 'witness': {}}}
        report = diagnose(self.formal(), 'c', self.binding(), declaration)
        self.assertEqual(report['i_falsifier_hint'], declaration['i_falsifier_hint'])

    def test_high_risk_stage2_code_alone_raises_risk(self):
        declaration = {'weak_invariant_diagnostics': [
            {'code': 'I_HOLDS_ON_EXPLOIT_PATH', 'severity': 'blocking'}]}
        report = diagnose(self.formal(), 'c', {'bindings': {}}, declaration)
        self.assertEqual(report['risk'], 'high')

    def test_checkpoint_collapse_is_review_but_not_hard_block(self):
        report = diagnose(self.formal(), 'c', self.binding())
        decision = gate(report)
        self.assertFalse(decision['blocking'])
        self.assertIn('I_CHECKPOINT_COLLAPSED', decision['review_codes'])

    def test_stage2_blocking_diagnostic_blocks_before_forge(self):
        declaration = {'weak_invariant_diagnostics': [
            {'code': 'I_HOLDS_ON_EXPLOIT_PATH', 'severity': 'blocking'}]}
        report = diagnose(self.formal(), 'c', {'bindings': {}}, declaration)
        decision = gate(report)
        self.assertTrue(decision['blocking'])
        self.assertIn('I_HOLDS_ON_EXPLOIT_PATH', decision['codes'])

    def test_low_risk_does_not_block(self):
        report = {'claim_id': 'c', 'risk': 'low', 'codes': []}
        self.assertFalse(gate(report)['blocking'])


if __name__ == '__main__':
    unittest.main()
