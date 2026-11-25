import unittest

from lib import binding_projection


def _ir(candidates, *, kind='boolean_predicate'):
    return {'symbols': {'effect': {
        'expected_kind': kind,
        'sort': 'bool',
        'candidates': candidates,
    }}}


def _candidate(expression, **overrides):
    row = {
        'candidate_id': expression,
        'expression': expression,
        'visible_at_injection': True,
        'ready_eligible': True,
        'match_score': 5,
        'solidity_type': 'bool',
        'evidence': ['source fact'],
    }
    row.update(overrides)
    return row


def _binding(expr='UNBOUND'):
    return {'bindings': {'effect': {
        'kind': 'boolean_predicate',
        'solidity_expr': expr,
        'checkpoint': 'after',
        'source': 'Contract.sol:deposit',
    }}}


class BindingProjectionTest(unittest.TestCase):
    def test_unique_visible_candidate_is_projected(self):
        projected, changes = binding_projection.project_binding(
            _binding(), _ir([_candidate('amount > 0')]))
        self.assertEqual(
            projected['bindings']['effect']['solidity_expr'], 'amount > 0')
        self.assertEqual(changes[0]['symbol'], 'effect')
        self.assertEqual(
            projected['bindings']['effect']['binding_projection']['candidate_id'],
            'amount > 0')

    def test_validation_can_reject_first_candidate(self):
        ir = _ir([
            _candidate('bad()', candidate_id='bad', match_score=9),
            _candidate('good()', candidate_id='good', match_score=4),
        ])
        projected, changes = binding_projection.project_binding(
            _binding(), ir,
            validate=lambda trial: ([] if trial['bindings']['effect'][
                'solidity_expr'] == 'good()' else ['bad identifier']))
        self.assertEqual(
            projected['bindings']['effect']['solidity_expr'], 'good()')
        self.assertEqual(changes[0]['options_considered'], 2)

    def test_invisible_candidate_is_not_projected(self):
        ir = _ir([_candidate('privateVar', visible_at_injection=False)])
        projected, changes = binding_projection.project_binding(_binding(), ir)
        self.assertEqual(
            projected['bindings']['effect']['solidity_expr'], 'UNBOUND')
        self.assertEqual(changes, [])

    def test_type_incompatible_candidate_is_not_projected(self):
        ir = _ir([_candidate('uintValue', solidity_type='uint256')])
        projected, _ = binding_projection.project_binding(_binding(), ir)
        self.assertEqual(
            projected['bindings']['effect']['solidity_expr'], 'UNBOUND')

    def test_bound_expression_is_untouched(self):
        projected, changes = binding_projection.project_binding(
            _binding('amount > 1'), _ir([_candidate('amount > 0')]))
        self.assertEqual(
            projected['bindings']['effect']['solidity_expr'], 'amount > 1')
        self.assertEqual(changes, [])


if __name__ == '__main__':
    unittest.main()
