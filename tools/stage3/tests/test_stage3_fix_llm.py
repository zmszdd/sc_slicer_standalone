import unittest

from cli import stage3_fix_llm
from cli.stage3_fix_llm import validate_fix, _report_focus, _focus_contract_body


class FixLLMTest(unittest.TestCase):
    def test_validate_fix_verbatim(self):
        src = ('function mint(address to, uint256 amount) external {\n'
               '    _mint(to, amount);\n}\n'
               'assertEq(balance, 1 ether);\n')
        fix = {'    _mint(to, amount);': '    require(whitelisted(to));\n    _mint(to, amount);'}
        fix_poc = {'assertEq(balance, 1 ether);': 'assertEq(balance, 0);'}
        proposal = validate_fix(fix, fix_poc, src)
        self.assertTrue(proposal['applicable'])
        self.assertEqual(proposal['missing_old'], [])

    def test_validate_fix_rejects_non_verbatim(self):
        src = 'function mint() external {}\n'
        proposal = validate_fix({'mint(address,uint256)': 'x'}, {}, src)
        self.assertFalse(proposal['applicable'])
        self.assertEqual(proposal['missing_old'], ['mint(address,uint256)'])

    def test_report_focus_keeps_mitigation(self):
        body = '## Summary\nnoise\n## Recommended mitigation steps\nPrimary Fix\n```\nfix code\n```'
        focus = _report_focus(body)
        self.assertIn('Recommended mitigation', focus)

    def test_focus_contract_body_extracts_full_contract(self):
        src = ('contract A { function x() external {} }\n'
               'contract Vault { function computeNAV() external returns (uint) '
               '{ return 1; } }\n')
        body = _focus_contract_body(src, 'Vault')
        self.assertIn('computeNAV', body)
        self.assertNotIn('contract A', body)

    def test_focus_contract_body_missing_returns_empty(self):
        self.assertEqual(_focus_contract_body('contract A {}', 'Vault'), '')

    def test_propose_fix_includes_focus_contract_in_prompt(self):
        src = ('contract Vault {\n'
               '    function computeNAV() external returns (uint) {\n'
               '        return 1;\n'
               '    }\n'
               '}\n'
               'contract PoC { function test_exploit() public { } }\n')

        class FakeLLM:
            def __init__(self):
                self.user = None

            def chat_json(self, system, user, *, model=None, max_tokens=None):
                self.user = user
                return {'fix': {'        return 1;': '        return 2;'},
                        'fix_poc': {}, 'reason': 'fixed'}

        fake = FakeLLM()
        original = stage3_fix_llm.llm.chat_json
        stage3_fix_llm.llm.chat_json = fake.chat_json
        try:
            proposal = stage3_fix_llm.propose_fix(
                '## Impact\ncomputeNAV is wrong', src, focus_contract='Vault')
        finally:
            stage3_fix_llm.llm.chat_json = original
        self.assertIn('FOCUS CONTRACT', fake.user)
        self.assertIn('computeNAV', fake.user)
        self.assertTrue(proposal['applicable'])


if __name__ == '__main__':
    unittest.main()
