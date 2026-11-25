import tempfile
import unittest
from pathlib import Path

from lib.patch import inject_patched_sources


def _write(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


class MultiFunctionPatchTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.case = Path(self.tmp.name)
        _write(self.case / 'src' / 'TwoContracts.sol', '''// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.24;

contract Alpha {
    address public admin;
    function init(address a) external { admin = a; }
}

contract Beta {
    address public admin;
    function init(address a) external { admin = a; }
}
''')
        _write(self.case / 'src' / 'Other.sol', '''// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.24;

contract Other {
    bool public configured;
    function configure() external { configured = true; }
}
''')
        self.binding = {
            'schema_version': 'stage3-binding/1',
            'claim_id': 'claim_multi',
            'bindings': {
                'guard_ok': {
                    'kind': 'boolean_predicate', 'solidity_expr': 'true',
                    'checkpoint': 'before', 'source': 'x',
                },
                'bad': {
                    'kind': 'boolean_predicate', 'solidity_expr': 'admin == msg.sender',
                    'checkpoint': 'after', 'source': 'x',
                },
            },
            'patch': {
                'functions': [
                    {'file': 'TwoContracts.sol', 'contract': 'Alpha', 'name': 'init'},
                    {'file': 'TwoContracts.sol', 'contract': 'Beta', 'name': 'init'},
                    {'file': 'Other.sol', 'name': 'configure'},
                ],
            },
        }
        self.spec = {}
        self.formal = {
            'schema_version': 'report-formalization/1',
            'symbols': {},
            'claims': [{
                'id': 'claim_multi',
                'properties': {
                    'preconditions': {'expression': {'var': 'guard_ok'}},
                    'safety': {'expression': {'op': 'implies', 'args': [
                        {'var': 'guard_ok'},
                        {'op': 'not', 'args': [{'var': 'bad'}]},
                    ]}},
                },
            }],
        }

    def tearDown(self):
        self.tmp.cleanup()

    def test_injects_all_files_and_scoped_functions(self):
        out = self.case / 'patched_out'
        inject_patched_sources(self.case, out, self.binding, self.spec, self.formal)
        two = (out / 'TwoContracts.sol').read_text()
        other = (out / 'Other.sol').read_text()
        self.assertEqual(two.count('bool stage3_guard_ok = true;'), 2)
        self.assertEqual(two.count('require('), 2)
        self.assertEqual(other.count('bool stage3_guard_ok = true;'), 1)
        self.assertEqual(other.count('require('), 1)
        # both Alpha and Beta got patched, not just the first match
        self.assertIn('contract Alpha', two)
        self.assertIn('contract Beta', two)

    def test_ambiguous_function_requires_contract_scope(self):
        binding = dict(self.binding)
        binding['patch'] = {'file': 'TwoContracts.sol', 'functions': ['init']}
        out = self.case / 'patched_out_ambiguous'
        from lib.spec_loader import SpecError
        with self.assertRaises(SpecError):
            inject_patched_sources(self.case, out, binding, self.spec, self.formal)


if __name__ == '__main__':
    unittest.main()


class BraceMatchingTest(unittest.TestCase):
    def test_comments_and_strings_do_not_unbalance(self):
        from lib.patch import _matching_brace
        src = (
            'contract C {\n'
            '    // a } comment\n'
            '    /* block { comment } */\n'
            '    string s = "}";\n'
            '    function f() public { uint x = 1; }\n'
            '}\n'
        )
        open_idx = src.find('{', src.find('contract C'))
        close_idx = _matching_brace(src, open_idx)
        self.assertEqual(src[close_idx], '}')
        self.assertIn('function f', src[:close_idx])
