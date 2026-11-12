import unittest
from pathlib import Path

from lib.binding import load_binding
from lib.binding_validate import lint_binding

CASES = Path(__file__).resolve().parents[1] / 'cases'


class BindingValidateTest(unittest.TestCase):
    def _lint(self, case, binding=None, strict=False):
        binding = binding or load_binding(CASES / case / 'binding.json')
        return lint_binding(binding, CASES / case / 'src',
                            test_dir=CASES / case / 'test', strict=strict)

    def test_real_bindings_lint_clean(self):
        record = self._lint('smoke_vault')
        self.assertTrue(record['ok'], record['problems'])
        self.assertEqual(record['summary']['errors'], 0)

    def test_known_vacuous_fixture_flagged(self):
        # panoptic_builder_init_e2e intentionally ships bare true/false
        # bindings (the TP-2 defect); the lint must now reject them so the
        # verdict loop can force a rebind instead of silently passing.
        record = self._lint('panoptic_builder_init_e2e', strict=True)
        vacuous = [p for p in record['problems']
                   if 'trivially constant binding' in p['message']]
        self.assertTrue(vacuous, record['problems'])
        self.assertTrue(all(p['severity'] == 'error' for p in vacuous))

    def test_placeholder_and_unknown_identifier_flagged(self):
        binding = {
            'schema_version': 'stage3-binding/1',
            'claim_id': 'x',
            'bindings': {
                'a': {'kind': 'boolean_predicate', 'solidity_expr': 'TODO_BIND_a',
                      'checkpoint': 'before', 'source': 'Vault.sol:withdraw'},
                'b': {'kind': 'boolean_predicate',
                      'solidity_expr': 'nonexistent_var == true',
                      'checkpoint': 'after', 'source': 'Vault.sol:withdraw'},
            },
        }
        record = self._lint('smoke_vault', binding=binding)
        self.assertFalse(record['ok'])
        sev = {p['where']: p['severity'] for p in record['problems']}
        self.assertEqual(sev.get('bindings.a.solidity_expr'), 'error')
        self.assertEqual(sev.get('bindings.b.solidity_expr'), 'warning')

    def test_missing_patch_file_is_error(self):
        binding = load_binding(CASES / 'smoke_vault' / 'binding.json')
        binding['patch'] = {'file': 'Nope.sol', 'functions': [{'name': 'withdraw'}]}
        record = self._lint('smoke_vault', binding=binding)
        self.assertFalse(record['ok'])
        self.assertTrue(any(p['severity'] == 'error'
                            for p in record['problems'] if p['where'] == 'patch.file'))

    def test_strict_escalates_warning(self):
        binding = load_binding(CASES / 'smoke_vault' / 'binding.json')
        binding['bindings']['balance_after']['solidity_expr'] = 'ghost_var'
        record = self._lint('smoke_vault', binding=binding, strict=True)
        self.assertFalse(record['ok'])
        self.assertTrue(any(p['severity'] == 'error'
                            for p in record['problems']))

    def test_cross_contract_state_var_reference_flagged(self):
        case = CASES / 'Kinetiq_k8aVPPVguSE__Et2e5TnpUga__wHqL6oK9ToF'
        binding = {
            'schema_version': 'stage3-binding/1',
            'claim_id': 'x',
            'bindings': {
                'a': {'kind': 'boolean_predicate',
                      'solidity_expr': 'stakingManager.getPendingWithdrawalsCount() > 0',
                      'checkpoint': 'before',
                      'source': 'Contract.sol:queueWithdrawal'},
            },
            'patch': {'file': 'Contract.sol', 'contract': 'TestPOC',
                      'functions': [{'name': 'testCancelWithdrawalVulnerability',
                                     'file': 'Contract.sol'}]},
            'probe': {'contract': 'TestPOC',
                      'exploit_test': 'testCancelWithdrawalVulnerability',
                      'safety_test': None},
        }
        record = lint_binding(binding, case / 'src')
        cross = [p for p in record['problems']
                 if 'cross-contract' in p['message']]
        self.assertTrue(cross, 'expected cross-contract warnings')
        self.assertTrue(all(p['severity'] == 'warning' for p in cross))
        strict = lint_binding(binding, case / 'src', strict=True)
        self.assertFalse(strict['ok'])
        self.assertTrue(any('cross-contract' in p['message']
                            and p['severity'] == 'error'
                            for p in strict['problems']))

    def test_solidity_unit_literals_allowed(self):
        binding = {
            'schema_version': 'stage3-binding/1',
            'claim_id': 'x',
            'bindings': {
                'a': {'kind': 'numeric_value',
                      'solidity_expr': 'balances[msg.sender] >= 1 ether',
                      'checkpoint': 'after',
                      'source': 'Vault.sol:withdraw'},
            },
            'patch': {'file': 'Vault.sol', 'contract': 'Vault',
                      'functions': [{'name': 'withdraw', 'file': 'Vault.sol'}]},
            'probe': {'contract': 'Vault', 'exploit_test': 'test_double_withdraw',
                      'safety_test': None},
        }
        record = self._lint('smoke_vault', binding=binding, strict=True)
        self.assertEqual(record['summary']['errors'], 0, record['problems'])

    def test_trivially_constant_binding_flagged(self):
        for literal in ('true', 'false', '  true  ', '(false)', '((true))'):
            binding = {
                'schema_version': 'stage3-binding/1',
                'claim_id': 'x',
                'bindings': {
                    'a': {'kind': 'boolean_predicate',
                          'solidity_expr': literal,
                          'checkpoint': 'before',
                          'source': 'Vault.sol:withdraw'},
                },
            }
            record = self._lint('smoke_vault', binding=binding, strict=True)
            errors = [p for p in record['problems']
                      if p['where'] == 'bindings.a.solidity_expr']
            self.assertTrue(errors, literal)
            self.assertTrue(all(p['severity'] == 'error' for p in errors), literal)
            self.assertTrue(any('trivially constant binding' in p['message']
                                for p in errors), literal)

    def test_boolean_literal_as_subexpression_not_flagged(self):
        binding = {
            'schema_version': 'stage3-binding/1',
            'claim_id': 'x',
            'bindings': {
                'a': {'kind': 'boolean_predicate',
                      'solidity_expr': 'balances[msg.sender] > 0 == true',
                      'checkpoint': 'after',
                      'source': 'Vault.sol:withdraw'},
            },
        }
        record = self._lint('smoke_vault', binding=binding, strict=True)
        self.assertFalse(any('trivially constant binding' in p['message']
                             for p in record['problems']), record['problems'])

    def test_constant_p_bool_not_flagged_when_not_in_safety(self):
        # A PoC that calls the target directly makes a P-side boolean a
        # faithful constant (e.g. direct_call_occurred == true). Only I-side
        # constants vacate the differential witness, so scoping the check to
        # safety symbols must let the P binding pass.
        binding = {
            'schema_version': 'stage3-binding/1',
            'claim_id': 'x',
            'bindings': {
                'direct_call_occurred': {
                    'kind': 'boolean_predicate', 'solidity_expr': 'true',
                    'checkpoint': 'before', 'source': 'Vault.sol:withdraw'},
                'transfer_succeeded': {
                    'kind': 'boolean_predicate',
                    'solidity_expr': 'balances[msg.sender] > 0',
                    'checkpoint': 'after', 'source': 'Vault.sol:withdraw'},
            },
            'patch': {'file': 'Vault.sol', 'contract': 'Vault',
                      'functions': [{'name': 'withdraw', 'file': 'Vault.sol'}]},
            'probe': {'contract': 'Vault', 'exploit_test': 'test_double_withdraw',
                      'safety_test': None},
        }
        record = lint_binding(binding, CASES / 'smoke_vault' / 'src',
                              test_dir=CASES / 'smoke_vault' / 'test',
                              strict=True, safety_symbols={'transfer_succeeded'})
        self.assertFalse(any('trivially constant binding' in p['message']
                             for p in record['problems']), record['problems'])
        # The same constant is still rejected when the symbol IS the safety one.
        record = lint_binding(binding, CASES / 'smoke_vault' / 'src',
                              test_dir=CASES / 'smoke_vault' / 'test',
                              strict=True,
                              safety_symbols={'direct_call_occurred'})
        self.assertTrue(any('trivially constant binding' in p['message']
                            for p in record['problems']), record['problems'])

    def test_invented_patch_function_name_flagged(self):
        binding = {
            'schema_version': 'stage3-binding/1',
            'claim_id': 'x',
            'bindings': {},
            'patch': {'file': 'Vault.sol', 'contract': 'Vault',
                      'functions': [{'name': 'testExploit', 'file': 'Vault.sol'}]},
            'probe': {'contract': 'Vault',
                      'exploit_test': 'test_double_withdraw', 'safety_test': None},
        }
        record = self._lint('smoke_vault', binding=binding)
        self.assertFalse(record['ok'])
        self.assertTrue(any(p['where'] == 'patch.functions[0].name'
                            for p in record['problems']))

    def test_invented_exploit_test_flagged(self):
        binding = {
            'schema_version': 'stage3-binding/1',
            'claim_id': 'x',
            'bindings': {},
            'patch': {'file': 'Vault.sol', 'contract': 'Vault',
                      'functions': [{'name': 'withdraw', 'file': 'Vault.sol'}]},
            'probe': {'contract': 'Vault',
                      'exploit_test': 'test_no_such_test', 'safety_test': None},
        }
        record = self._lint('smoke_vault', binding=binding)
        self.assertFalse(record['ok'])
        self.assertTrue(any(p['where'] == 'probe.exploit_test'
                            for p in record['problems']))


if __name__ == '__main__':
    unittest.main()


class FileLevelVarLintTest(unittest.TestCase):
    def test_file_level_constant_not_cross_contract(self):
        import tempfile
        from pathlib import Path
        from lib.binding_validate import lint_binding
        with tempfile.TemporaryDirectory() as td:
            src_dir = Path(td) / 'src'
            src_dir.mkdir()
            (src_dir / 'Contract.sol').write_text(
                'uint256 constant SIG_OK = 0;\n'
                'contract A { uint256 internal x; function f() external {} }\n')
            binding = {
                'schema_version': 'stage3-binding/1',
                'claim_id': 'x',
                'bindings': {
                    'a': {'kind': 'numeric_value',
                          'solidity_expr': 'SIG_OK == 0',
                          'checkpoint': 'after',
                          'source': 'Contract.sol:f'},
                },
                'patch': {'file': 'Contract.sol', 'contract': 'A',
                          'functions': [{'name': 'f', 'file': 'Contract.sol'}]},
                'probe': {'contract': 'A', 'exploit_test': 'f',
                          'safety_test': None},
            }
            record = lint_binding(binding, src_dir, strict=True)
            self.assertFalse(any('cross-contract' in p['message']
                                 for p in record['problems']), record['problems'])
