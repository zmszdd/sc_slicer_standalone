import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools' / 'pipeline'))

from lib.harness_qualification import qualify  # noqa: E402


class HarnessQualificationTest(unittest.TestCase):
    def test_runnable_harness(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'Contract.t.sol'
            path.write_text('''
pragma solidity ^0.8.20;
contract Harness {
    function test_exploit() public { require(true); }
}
''')
            result = qualify(path)
            self.assertEqual(result['status'], 'runnable')

    def test_live_fork_is_needs_input(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'Contract.t.sol'
            path.write_text('''
pragma solidity ^0.8.20;
contract Harness {
    function test_exploit() public { vm.createFork("https://rpc"); }
}
''')
            result = qualify(path, test_name='test_exploit')
            self.assertEqual(result['status'], 'needs_input')
            self.assertIn('harness forks live RPC', result['blockers'])


if __name__ == '__main__':
    unittest.main()
