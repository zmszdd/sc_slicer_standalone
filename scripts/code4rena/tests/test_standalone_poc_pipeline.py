"""Deterministic unit tests for the standalone PoC pipeline pure logic.

These are the "real tests" for the blind-set authoring path: they pin the two
regressions found during blind flatten work (test-name extraction picking the
borrowed harness's first test, and parameterized test matching), plus the
classification and wrapper-embedding mechanics. No forge, no LLM, no network.
"""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import standalone_poc_pipeline as p


HARNESS = """// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import {Test, console} from "forge-std/Test.sol";
import {LiquidRon} from "../src/LiquidRon.sol";

contract LiquidRonTest is Test {
    LiquidRon public liquidRon;

    function setUp() public {
        liquidRon = new LiquidRon(address(0), address(0), 250, address(this), "T", "T");
    }

    function test_admin_pause() public {
        assertTrue(true);
    }

    receive() external payable {}
}
"""

BARE_FN = """function test_issue_poc(uint88 _amount) public {
    vm.assume(_amount >= 1 ether);
    liquidRon.deposit{value: _amount}();
}
"""


class TestPassesTest(unittest.TestCase):
    def test_parameterized_pass(self):
        out = "[PASS] test_audit_poc_1036(uint88) (runs: 256)"
        self.assertTrue(p._test_passes(out, "test_audit_poc_1036"))

    def test_plain_pass(self):
        out = "[PASS] test_admin_pause() (gas: 14686)"
        self.assertTrue(p._test_passes(out, "test_admin_pause"))

    def test_fail_not_pass(self):
        out = "[FAIL: ErrInvalidOperator()] test_audit_poc_104()"
        self.assertFalse(p._test_passes(out, "test_audit_poc_104"))

    def test_other_test_pass_does_not_contaminate(self):
        out = "[PASS] test_admin_pause()\n[FAIL] test_audit_poc_104()"
        self.assertFalse(p._test_passes(out, "test_audit_poc_104"))


class ClassifyTest(unittest.TestCase):
    def test_no_poc_code(self):
        self.assertEqual(p._classify({}, [])['action'], 'no_poc_code')

    def test_bare_test_fn(self):
        cls = p._classify({}, [BARE_FN])
        self.assertEqual(cls['action'], 'bare_test_fn')
        self.assertTrue(cls['has_test'])
        self.assertFalse(cls['is_harness'])

    def test_snippet_only(self):
        cls = p._classify({}, ["require(a == b, 'x');"])
        self.assertEqual(cls['action'], 'snippet_only')
        self.assertFalse(cls['has_test'])

    def test_fork_rpc(self):
        block = "function test_x() public { vm.createSelectFork('rpc'); }"
        self.assertEqual(p._classify({}, [block])['action'], 'fork_rpc')


class ExtractNamesTest(unittest.TestCase):
    def test_extracts_contract_and_first_test(self):
        full = (HARNESS + "\n" + "function test_issue_poc(uint88 a) public {}")
        contract, fn = p._extract_names(full)
        self.assertEqual(contract, 'LiquidRonTest')
        # _extract_names returns the first test fn; the bare_test_fn wrapper path
        # must therefore pass an explicit test name to _run_entry (pinned below).
        self.assertEqual(fn, 'test_admin_pause')

    def test_wrapper_path_uses_explicit_poc_test_name(self):
        wrapped = p._author_wrapper_from_source(
            _HarnessFile(HARNESS), "saSt2BUFmQ3", "104", BARE_FN)
        # The PoC body is renamed, so the target test is deterministic and
        # does NOT collide with the borrowed harness's own test functions.
        self.assertIn('function test_audit_poc_104(uint88 _amount) public {', wrapped)
        self.assertNotIn('function test_issue_poc', wrapped)


class WrapperEmbedTest(unittest.TestCase):
    def test_rename_contract_and_embed(self):
        wrapped = p._author_wrapper_from_source(
            _HarnessFile(HARNESS), "DRwbqkrQPik", "1036", BARE_FN)
        self.assertIn('contract Standalone_DRwbqkrQPik_1036 is Test', wrapped)
        # PoC fn is renamed so it cannot collide with a borrowed harness's tests
        self.assertIn('function test_audit_poc_1036(uint88 _amount) public {', wrapped)
        self.assertNotIn('function test_issue_poc', wrapped)
        # borrows setUp + state
        self.assertIn('liquidRon = new LiquidRon', wrapped)

    def test_matching_close_brace(self):
        src = "contract C is Test { function a() { if (true) { x(); } } function b() {} }"
        open_pos = p._contract_open_brace(src)
        self.assertGreater(open_pos, 0)
        close_pos = p._matching_close_brace(src, open_pos)
        self.assertEqual(close_pos, len(src) - 1)

    def test_best_source_excludes_standalone(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / 'test').mkdir(parents=True)
            (repo / 'test' / 'LiquidRon.t.sol').write_text(HARNESS)
            (repo / 'test' / 'Standalone_stale_1036.t.sol').write_text(
                HARNESS + '\n' + BARE_FN)
            best = p._find_best_test_source(repo, BARE_FN)
            self.assertIsNotNone(best)
            self.assertEqual(best.name, 'LiquidRon.t.sol')


class _HarnessFile:
    def __init__(self, text):
        self._text = text

    def read_text(self, encoding='utf-8'):
        return self._text


if __name__ == '__main__':
    unittest.main()
