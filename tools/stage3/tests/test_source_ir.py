import tempfile
import unittest
from pathlib import Path

from lib import source_ir


class SourceIRTest(unittest.TestCase):
    def test_build_indexes_declarations_and_annotations(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'Contract.t.sol'
            path.write_text('''
pragma solidity ^0.8.20;
contract Vault {
    uint256 public totalDeposits;
    modifier onlyOwner() { _; }
    function deposit(uint256 amount) external returns (uint256 shares) {
        totalDeposits += amount;
        return amount;
    }
}
''')
            index = source_ir.build(path)
            self.assertEqual(len(index['contracts']), 1)
            self.assertEqual(index['contracts'][0]['name'], 'Vault')
            self.assertIn('totalDeposits', index['state'][0]['name'])
            self.assertEqual(index['functions'][0]['visibility'], 'external')
            self.assertIn('onlyOwner', index['modifiers'][0]['name'])

            observable = {'symbols': {'totalDeposits': {'candidates': [
                {'expression': 'vault.totalDeposits()'},
                {'expression': 'unknownSymbol'},
            ]}}}
            annotated = source_ir.annotate_observable_ir(observable, index)
            self.assertTrue(annotated['symbols']['totalDeposits']
                            ['candidates'][0]['source_ir_grounded'])
            self.assertFalse(annotated['symbols']['totalDeposits']
                             ['candidates'][1]['source_ir_grounded'])


if __name__ == '__main__':
    unittest.main()
