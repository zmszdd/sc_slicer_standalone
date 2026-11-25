import unittest

from lib.execution_contract import build


FORMAL = {
    'claims': [{
        'id': 'c1',
        'properties': {
            'preconditions': {'expression': {'var': 'p'}},
            'safety': {'expression': {'var': 'i'}},
            'effects': {'expression': {'var': 'v'}},
        },
    }],
}


class ExecutionContractTest(unittest.TestCase):
    def test_roles_and_missing_invariant_symbol(self):
        binding = {
            'probe': {'contract': 'Harness', 'exploit_test': 'test_poc'},
            'patch': {'file': 'Contract.sol', 'contract': 'Harness',
                      'functions': [{'name': 'test_poc'}]},
            'bindings': {
                'p': {'solidity_expr': 'true', 'kind': 'boolean_predicate',
                      'checkpoint': 'before'},
                'i': {'solidity_expr': 'UNBOUND', 'kind': 'boolean_predicate',
                      'checkpoint': 'after'},
                'v': {'solidity_expr': 'value != 0', 'checkpoint': 'after'},
            },
        }
        record = build(FORMAL, binding, 'c1')
        self.assertEqual(record['status'], 'incomplete')
        self.assertEqual(record['symbols']['i']['roles'], ['I'])
        self.assertFalse(record['symbols']['i']['binding']['bound'])
        self.assertTrue(record['patch_target']['test_level'])
        self.assertEqual(record['requirements']['unbound_required_symbols'], ['i'])


if __name__ == '__main__':
    unittest.main()
