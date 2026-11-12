"""Cross-module contract: patch.py injection shape <-> differential.py verdict.

Locks two facts that must not drift independently:

1. ``lib/patch.py`` emits a single plain ``assert(!P || I)`` with no
   ``stage3:P`` marker.
2. ``lib/differential.py`` maps an original-pass / patched-assertion-failure
   pair to ``P_and_T=sat, P_and_T_and_not_I=sat, P_and_T_and_V=sat``.

No LLM or forge is involved; the test builds an in-memory case and asserts the
emitted source string, then runs ``compute_queries`` on the corresponding
failure reasons.
"""
import tempfile
import unittest
from pathlib import Path

from lib.differential import compute_queries
from lib.patch import inject_patched_sources

SRC = (
    '// SPDX-License-Identifier: MIT\n'
    'pragma solidity ^0.8.20;\n'
    'contract Counter {\n'
    '    uint256 public value;\n'
    '    function bump() external {\n'
    '        value += 1;\n'
    '    }\n'
    '}\n'
)


def _build_case(root: Path) -> tuple[Path, dict, dict, dict]:
    case = root / 'case'
    (case / 'src').mkdir(parents=True)
    (case / 'src' / 'Counter.sol').write_text(SRC)
    spec = {'claims': []}
    formal = {
        'claims': [{
            'id': 'c1',
            'properties': {
                'preconditions': {'expression': {'var': 'p'}},
                'safety': {'expression': {'var': 'i'}},
            },
        }],
    }
    binding = {
        'claim_id': 'c1',
        'bindings': {
            'p': {'solidity_expr': 'value > 0', 'kind': 'boolean_predicate',
                  'checkpoint': 'after'},
            'i': {'solidity_expr': 'value >= 1', 'kind': 'boolean_predicate',
                  'checkpoint': 'after'},
        },
        'patch': {'file': 'Counter.sol', 'functions': [{'name': 'bump'}]},
    }
    return case, spec, formal, binding


class PatchDifferentialContractTest(unittest.TestCase):
    def test_emitted_assertion_matches_differential_mapping(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            case, spec, formal, binding = _build_case(root)
            patched = root / 'patched'
            inject_patched_sources(case, patched, binding, spec, formal)
            source = (patched / 'Counter.sol').read_text()

        self.assertIn('assert(!(value > 0) || (value >= 1));', source)
        self.assertNotIn('stage3:P', source)

        for reason in ('panic: assertion failed (0x01)', 'Panic(0x01)'):
            with self.subTest(reason=reason):
                queries = compute_queries(
                    {'exploit_test': 'test_exploit'},
                    {'status': 'Success', 'reason': None},
                    {'status': 'Failure', 'reason': reason},
                )
                self.assertEqual(queries['P_and_T'], 'sat')
                self.assertEqual(queries['P_and_T_and_not_I'], 'sat')
                self.assertEqual(queries['P_and_T_and_V'], 'sat')


if __name__ == '__main__':
    unittest.main()
