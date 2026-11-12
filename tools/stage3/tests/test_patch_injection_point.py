import unittest

from lib.spec_loader import SpecError
from lib.patch import _inject_into_source


class InjectionPointTest(unittest.TestCase):
    def _spec(self):
        return {'claims': []}

    def _formal(self):
        return {'claims': [{
            'id': 'core',
            'properties': {
                'preconditions': {'expression': {'var': 'p'}},
                'safety': {'expression': {'var': 'i'}},
            },
        }]}

    def _entries(self):
        return {
            'p': {'kind': 'boolean_predicate', 'solidity_expr': 'true',
                  'checkpoint': 'before'},
            'i': {'kind': 'boolean_predicate', 'solidity_expr': 'flag',
                  'checkpoint': 'after'},
        }

    def test_snapshot_before_executable_statement(self):
        # A PoC that declares a variable after the exploit must not push the
        # "before" snapshot past the exploit.
        src = (
            'contract C {\n'
            '  function f() public {\n'
            '    state.change();\n'
            '    uint256 x = 1;\n'
            '  }\n'
            '}\n'
        )
        out = _inject_into_source(src, self._spec(), self._formal(), 'core',
                                  self._entries(), [('f', None)])
        self.assertLess(out.find('stage3_p'), out.find('state.change()'))
        self.assertIn('assert(!(stage3_p) || (flag));', out)

    def test_snapshot_before_parameterless_exploit(self):
        src = (
            'contract C {\n'
            '  function f() public {\n'
            '    exploit();\n'
            '  }\n'
            '}\n'
        )
        out = _inject_into_source(src, self._spec(), self._formal(), 'core',
                                  self._entries(), [('f', None)])
        self.assertLess(out.find('stage3_p'), out.find('exploit()'))

    def test_snapshot_after_statement_anchor(self):
        # A mid-function checkpoint must be sampled after its anchor statement,
        # not at the function entry. The snapshot variable is declared at the
        # head (so the tail assertion can see it) and assigned at the anchor.
        entries = {
            'p': {'kind': 'boolean_predicate', 'solidity_expr': 'wallet.admin() == owner',
                  'checkpoint': 'before', 'snapshot_after': 'wallet.init(owner);'},
            'i': {'kind': 'boolean_predicate', 'solidity_expr': 'flag',
                  'checkpoint': 'after'},
        }
        src = (
            'contract C {\n'
            '  function f() public {\n'
            '    wallet.init(owner);\n'
            '    wallet.init(attacker);\n'
            '  }\n'
            '}\n'
        )
        out = _inject_into_source(src, self._spec(), self._formal(), 'core',
                                  entries, [('f', None)])
        anchor = out.find('wallet.init(owner);')
        head_decl = out.find('bool stage3_p;')
        assign = out.find('stage3_p = wallet.admin() == owner;')
        attacker = out.find('wallet.init(attacker);')
        self.assertLess(head_decl, anchor)
        self.assertGreater(assign, anchor)
        self.assertLess(assign, attacker)
        self.assertIn('assert(!(stage3_p) || (flag));', out)

    def test_tuple_destructure_prelude(self):
        # A tuple-returning getter must be destructured into local names before
        # the snapshot expression can reference them.
        entries = {
            'p': {'kind': 'numeric_value', 'solidity_expr': 'r0 * r1',
                  'solidity_stmts': ['(uint256 r0, uint256 r1,) = pair.getReserves();'],
                  'checkpoint': 'before'},
            'i': {'kind': 'boolean_predicate', 'solidity_expr': 'flag',
                  'checkpoint': 'after'},
        }
        src = (
            'contract C {\n'
            '  function f() public {\n'
            '    exploit();\n'
            '  }\n'
            '}\n'
        )
        out = _inject_into_source(src, self._spec(), self._formal(), 'core',
                                  entries, [('f', None)])
        self.assertIn('(uint256 r0, uint256 r1,) = pair.getReserves();', out)
        self.assertIn('uint256 stage3_p = r0 * r1;', out)
        self.assertLess(out.find('stage3_p'), out.find('exploit()'))

    def test_snapshot_after_nested_anchor_is_function_scoped(self):
        # An anchor inside a loop body must still produce a snapshot variable
        # that the tail assertion can reference.
        entries = {
            'p': {'kind': 'boolean_predicate', 'solidity_expr': 'firstProblem != 0',
                  'checkpoint': 'before', 'snapshot_after': 'firstProblem = exponents[i];'},
            'i': {'kind': 'boolean_predicate', 'solidity_expr': 'flag',
                  'checkpoint': 'after'},
        }
        src = (
            'contract C {\n'
            '  function f() public {\n'
            '    int firstProblem = 0;\n'
            '    for (uint i = 0; i < 3; i++) {\n'
            '      firstProblem = exponents[i];\n'
            '    }\n'
            '  }\n'
            '}\n'
        )
        out = _inject_into_source(src, self._spec(), self._formal(), 'core',
                                  entries, [('f', None)])
        self.assertIn('bool stage3_p;', out)
        self.assertIn('stage3_p = firstProblem != 0;', out)
        # tail assertion still references the function-scoped snapshot
        self.assertIn('assert(!(stage3_p) || (flag));', out)

    def test_snapshot_after_missing_anchor_raises(self):
        entries = {
            'p': {'kind': 'boolean_predicate', 'solidity_expr': 'true',
                  'checkpoint': 'before', 'snapshot_after': 'no.such.statement;'},
            'i': {'kind': 'boolean_predicate', 'solidity_expr': 'flag',
                  'checkpoint': 'after'},
        }
        src = (
            'contract C {\n'
            '  function f() public {\n'
            '    exploit();\n'
            '  }\n'
            '}\n'
        )
        with self.assertRaises(SpecError):
            _inject_into_source(src, self._spec(), self._formal(), 'core',
                                entries, [('f', None)])


if __name__ == '__main__':
    unittest.main()
