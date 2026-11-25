import tempfile
import unittest
from pathlib import Path

from lib.binding_validate import lint_binding
from lib.patch import inject_patched_sources
from lib.test_monitor import build_monitor_binding


SRC = (
    'contract Registry { bool public paused; }\n'
    'contract Gate { function enter() external {} }\n'
)

TEST = (
    'import "forge-std/Test.sol";\n'
    'contract Harness is Test {\n'
    '  Registry registry;\n'
    '  Gate gate;\n'
    '  function test_poc() public { gate.enter(); assertTrue(!registry.paused()); }\n'
    '}\n'
)


def _binding():
    return {
        'claim_id': 'c1',
        'probe': {'contract': 'Harness', 'exploit_test': 'test_poc'},
        'patch': {'file': 'Contract.sol', 'contract': 'Gate',
                  'functions': [{'name': 'enter'}]},
        'bindings': {
            'p': {'solidity_expr': 'true', 'kind': 'boolean_predicate',
                  'checkpoint': 'before'},
            'i': {'solidity_expr': '!registry.paused()',
                  'kind': 'boolean_predicate', 'checkpoint': 'after'},
        },
    }


class TestMonitorTest(unittest.TestCase):
    def _case(self, root: Path):
        case = root / 'case'
        (case / 'src').mkdir(parents=True)
        (case / 'test').mkdir(parents=True)
        (case / 'src' / 'Contract.sol').write_text(SRC)
        test = case / 'test' / 'PoC.t.sol'
        test.write_text(TEST)
        return case, test

    def test_relocates_cross_contract_observable_to_test_frame(self):
        with tempfile.TemporaryDirectory() as tmp:
            case, _ = self._case(Path(tmp))
            binding = _binding()
            candidate, record = build_monitor_binding(binding, case)
        self.assertIsNotNone(candidate)
        self.assertEqual(record['status'], 'candidate')
        self.assertEqual(candidate['patch']['file'], '../test/PoC.t.sol')
        self.assertEqual(candidate['patch']['functions'][0]['name'], 'test_poc')

    def test_monitor_binding_lints_with_test_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            case, _ = self._case(Path(tmp))
            candidate, _ = build_monitor_binding(_binding(), case)
            lint = lint_binding(candidate, case / 'src', test_dir=case / 'test',
                                strict=True, safety_symbols={'i'})
        self.assertTrue(lint['ok'], lint)

    def test_injection_uses_copied_test_tree(self):
        with tempfile.TemporaryDirectory() as tmp:
            case, _ = self._case(Path(tmp))
            candidate, _ = build_monitor_binding(_binding(), case)
            patched = Path(tmp) / 'patched' / 'src'
            (patched.parent / 'test').mkdir(parents=True)
            (patched.parent / 'test' / 'PoC.t.sol').write_text(TEST)
            patched.mkdir(parents=True)
            spec = {'claims': [{'claim_id': 'c1', 'properties': {}}]}
            formal = {'claims': [{'id': 'c1', 'properties': {
                'preconditions': {'expression': {'var': 'p'}},
                'safety': {'expression': {'var': 'i'}},
            }}]}
            inject_patched_sources(case, patched, candidate, spec, formal)
            injected = (patched.parent / 'test' / 'PoC.t.sol').read_text()
        self.assertIn('stage3:I', injected)


if __name__ == '__main__':
    unittest.main()
