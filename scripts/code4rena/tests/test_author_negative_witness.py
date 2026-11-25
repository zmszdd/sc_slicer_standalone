"""Regression tests for the frozen negative-witness harness generator."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import author_negative_witness as witness


class NegativeWitnessWrapperTest(unittest.TestCase):
    def test_inherited_base_is_emitted_once(self):
        name, text = witness._wrapper(
            {'submission_uid': 'abc123'}, '^0.8.20', './Standalone.t.sol',
            ' is SimpleToken', True, '', 'assertTrue(true);')
        self.assertEqual(name, 'NegWitness_abc123')
        self.assertIn(
            'contract NegWitness_abc123 is SimpleToken {', text)
        self.assertNotIn('is is', text)
        self.assertIn('function test_negative_witness() public {', text)

    def test_direct_source_contract_is_emitted_once(self):
        _, text = witness._wrapper(
            {'submission_uid': 'abc123'}, '^0.8.20', '../src/A.sol',
            '', False, 'contract A { function f() external {} }',
            'assertTrue(true);')
        self.assertIn('contract NegWitness_abc123 is Test, A {', text)
        self.assertNotIn('is is', text)


class NegativeWitnessHelpersTest(unittest.TestCase):
    def test_passes_only_for_the_witness_test(self):
        self.assertTrue(witness._passes(
            '[PASS] test_negative_witness() (gas: 1)'))
        self.assertFalse(witness._passes('[PASS] test_entrypoint() (gas: 1)'))

    def test_test_contract_prefers_the_contract_with_setup_and_test(self):
        source = (
            'contract SimpleToken { function mint() external {} }\n'
            'contract PoCTest is Test { function setUp() public {} '
            'function test_poc() public {} }\n')
        self.assertEqual(witness._test_contract(source), 'PoCTest')

    def test_relative_import_is_redirected_to_project_copy(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            (project / 'mocks').mkdir()
            (project / 'mocks' / 'Mock.sol').write_text('contract Mock {}')
            harness = project / 'test' / 'Standalone.t.sol'
            harness.parent.mkdir()
            source = 'import {Mock} from "../../mocks/Mock.sol";\n'
            repaired = witness._repair_relative_imports(
                source, harness, project)
            self.assertIn('../mocks/Mock.sol', repaired)
            self.assertNotIn('../../mocks/Mock.sol', repaired)

    def test_compiler_errors_drop_warnings(self):
        output = ('Warning (2018): utility warning\n'
                  'Error (7576): Undeclared identifier\n'
                  '  --> test/A.t.sol:1:1\n'
                  'Error: Compilation failed\n')
        errors = witness._compiler_errors(output)
        self.assertNotIn('Warning', errors)
        self.assertIn('Undeclared identifier', errors)

    def test_first_test_body_uses_existing_poc_statements(self):
        source = (
            'contract PoCTest { function setUp() public {} '
            'function test_poc() public { target.call(); assertTrue(true); } '
            'function test_other() public { x(); } }')
        body = witness._first_test_body(source, 'PoCTest')
        self.assertIn('target.call()', body)
        self.assertNotIn('x();', body)

    def test_flat_witness_rejects_pure_arithmetic_models(self):
        source = ('library Helpers { function f() internal pure returns (uint) '
                  '{ return 1; } }\n'
                  'contract Vault { function sweep() external {} }')
        modeled = 'uint256 bonus = 100 / 10; assertTrue(true);'
        library_only = 'uint256 value = Helpers.f(); assertTrue(true);'
        real = ('Vault vault = new Vault(); vault.sweep(); '
                'assertTrue(true);')
        self.assertFalse(witness._uses_target_contract(modeled, source))
        self.assertFalse(witness._uses_target_contract(library_only, source))
        self.assertTrue(witness._uses_target_contract(real, source))


if __name__ == '__main__':
    unittest.main()
