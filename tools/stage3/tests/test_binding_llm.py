import json
import tempfile
import unittest
from pathlib import Path

from lib import binding_llm
from lib.binding_llm import (_analyze, _migrate_patch_contract,
                             _symbols_payload, propose_binding)

CLAIM = 'impact_claim_swap_denial_of_service_afd43cf9_41b015b2'
REQUIRED = {
    'ce8278392_rewards_pool_total_shares',
    'ce8278392_fee_distribution_triggered',
    'ce8278392_distribution_call_reverts',
    'ce8278392_swap_denied',
}


FIXTURE = Path(__file__).resolve().parents[0] / 'fixtures' / 'gte_swap_dos'


def _proposal(unbound=(), placeholder=()):
    bindings = {}
    for sym in REQUIRED:
        expr = 'UNBOUND' if sym in unbound else ('true' if sym not in placeholder else sym)
        bindings[sym] = {
            'kind': 'boolean_predicate',
            'solidity_expr': expr,
            'checkpoint': 'before',
            'source': 'Contract.sol:test_submissionValidity',
        }
    return {
        'schema_version': 'stage3-binding/1',
        'claim_id': CLAIM,
        'bindings': bindings,
        'patch': {'file': 'Contract.sol', 'contract': 'C4PoC',
                  'functions': [{'name': 'test_submissionValidity'}]},
        'probe': {'contract': 'C4PoC', 'exploit_test': 'test_submissionValidity',
                  'safety_test': None},
    }


class AnalyzeTest(unittest.TestCase):
    def test_complete(self):
        hard, unbound = _analyze(_proposal(), CLAIM, REQUIRED)
        self.assertEqual(hard, [])
        self.assertEqual(unbound, [])

    def test_partial_unbound(self):
        hard, unbound = _analyze(_proposal(unbound={'ce8278392_swap_denied'}),
                                 CLAIM, REQUIRED)
        self.assertEqual(hard, [])
        self.assertEqual(unbound, ['ce8278392_swap_denied'])

    def test_placeholder_symbol_name_is_hard(self):
        hard, unbound = _analyze(_proposal(placeholder={'ce8278392_swap_denied'}),
                                 CLAIM, REQUIRED)
        self.assertIn('placeholder solidity_expr for ce8278392_swap_denied', hard)

    def test_missing_symbol_is_hard(self):
        p = _proposal()
        del p['bindings']['ce8278392_swap_denied']
        hard, _ = _analyze(p, CLAIM, REQUIRED)
        self.assertTrue(any('do not cover symbols' in h for h in hard))


class SymbolsPayloadTest(unittest.TestCase):
    def test_observability_included_when_provided(self):
        contract = {'symbols': [{'symbol': 'a', 'appears_in': 'f'},
                                {'symbol': 'b', 'appears_in': 'f'}]}
        payload = _symbols_payload(contract, {'a': ['alpha']},
                                   {'a': 'high', 'b': 'low'})
        self.assertEqual(payload[0]['observability'], 'high')
        self.assertEqual(payload[0]['candidate_identifiers'], ['alpha'])
        self.assertEqual(payload[1]['observability'], 'low')
        self.assertNotIn('candidate_identifiers', payload[1])

    def test_medium_executable_recipe_is_not_ready_payload(self):
        contract = {'symbols': [{'symbol': 'a', 'appears_in': 'f'}]}
        recipes = {'a': [
            {'recipe_id': 'a:direct:0', 'kind': 'state_snapshot',
             'expression': 'value', 'executable': True,
             'confidence': 'medium'},
        ]}
        payload = _symbols_payload(contract, recipes=recipes)
        self.assertNotIn('ready_observable_recipes', payload[0])
        self.assertEqual(len(payload[0]['planned_observable_recipes']), 1)


class ProposePartialTest(unittest.TestCase):
    def test_p_side_unbound_is_not_silently_bound_to_true(self):
        stage2_dir = FIXTURE / 'stage2_run'
        src_dir = FIXTURE / 'src'
        symbol = 'ce8278392_rewards_pool_total_shares'
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)

            class FakeLLM:
                def chat_json(self, system, user, *, model=None):
                    return _proposal(unbound={symbol})

            original = binding_llm.llm.chat_json
            binding_llm.llm.chat_json = FakeLLM().chat_json
            try:
                proposal = propose_binding(stage2_dir, CLAIM, src_dir, out)
            finally:
                binding_llm.llm.chat_json = original
            self.assertTrue(proposal['partial'])
            self.assertIn(symbol, proposal['unbound'])
            written = json.loads((out / 'binding.proposal.json').read_text())
            entry = written['bindings'][symbol]
            self.assertEqual(entry['solidity_expr'], 'UNBOUND')
            self.assertTrue(entry.get('degraded'))
            self.assertIn('not auto-bound to true', entry['degraded_reason'])

    def test_partial_binding_written(self):
        stage2_dir = FIXTURE / 'stage2_run'
        src_dir = FIXTURE / 'src'
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)

            class FakeLLM:
                def chat_json(self, system, user, *, model=None):
                    return _proposal(unbound={'ce8278392_swap_denied'})

            original = binding_llm.llm.chat_json
            binding_llm.llm.chat_json = FakeLLM().chat_json
            try:
                proposal = propose_binding(stage2_dir, CLAIM, src_dir, out)
            finally:
                binding_llm.llm.chat_json = original
            self.assertTrue(proposal['partial'])
            self.assertEqual(proposal['unbound'], ['ce8278392_swap_denied'])
            self.assertTrue((out / 'binding.proposal.json').is_file())
            written = json.loads((out / 'binding.proposal.json').read_text())
            self.assertEqual(
                written['bindings']['ce8278392_swap_denied']['solidity_expr'],
                'UNBOUND')

    def test_injection_point_overridden_from_source(self):
        stage2_dir = FIXTURE / 'stage2_run'
        src_dir = FIXTURE / 'src'
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)

            class FakeLLM:
                def chat_json(self, system, user, *, model=None):
                    p = _proposal()
                    p['patch'] = {'file': 'Wrong.sol', 'contract': 'Wrong',
                                  'functions': [{'name': 'testExploit'}]}
                    p['probe'] = {'contract': 'Wrong',
                                  'exploit_test': 'testExploit', 'safety_test': None}
                    return p

            original = binding_llm.llm.chat_json
            binding_llm.llm.chat_json = FakeLLM().chat_json
            try:
                propose_binding(stage2_dir, CLAIM, src_dir, out)
            finally:
                binding_llm.llm.chat_json = original
            written = json.loads((out / 'binding.proposal.json').read_text())
            self.assertEqual(written['patch']['contract'], 'PoCLaunchpad')
            self.assertEqual(written['patch']['functions'][0]['name'],
                             'test_submissionValidity')
            self.assertEqual(written['probe']['contract'], 'PoCLaunchpad')
            self.assertEqual(written['probe']['exploit_test'],
                             'test_submissionValidity')

    def test_focused_rebind_merges_existing(self):
        stage2_dir = FIXTURE / 'stage2_run'
        src_dir = FIXTURE / 'src'
        existing = _proposal(unbound={'ce8278392_swap_denied'})
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)

            class FakeLLM:
                def chat_json(self, system, user, *, model=None):
                    self.user = user
                    return {
                        'schema_version': 'stage3-binding/1',
                        'claim_id': CLAIM,
                        'bindings': {
                            'ce8278392_swap_denied': {
                                'kind': 'boolean_predicate',
                                'solidity_expr': 'true',
                                'checkpoint': 'before',
                                'source': 'Contract.sol:test_submissionValidity',
                            },
                        },
                        'patch': {'file': 'Contract.sol', 'contract': 'PoCLaunchpad',
                                  'functions': [{'name': 'test_submissionValidity'}]},
                        'probe': {'contract': 'PoCLaunchpad',
                                  'exploit_test': 'test_submissionValidity',
                                  'safety_test': None},
                    }

            fake = FakeLLM()
            original = binding_llm.llm.chat_json
            binding_llm.llm.chat_json = fake.chat_json
            try:
                proposal = propose_binding(stage2_dir, CLAIM, src_dir, out,
                                           existing=existing)
            finally:
                binding_llm.llm.chat_json = original
            self.assertTrue(proposal['ok'])
            self.assertEqual(proposal['unbound'], [])
            self.assertIn('focus_symbols', fake.user)
            merged = proposal['binding']['bindings']
            self.assertEqual(merged['ce8278392_swap_denied']['solidity_expr'],
                             'true')
            self.assertEqual(
                merged['ce8278392_rewards_pool_total_shares']['solidity_expr'],
                'true')


if __name__ == '__main__':
    unittest.main()


class MigratePatchContractTest(unittest.TestCase):
    SRC = (
        'contract Business {\n'
        '  function invariantFn() public pure returns (bool) { return true; }\n'
        '}\n'
        'contract PoC {\n'
        '  function test_POC() public {}\n'
        '}\n'
    )

    def _binding(self):
        return {
            'bindings': {'s': {'solidity_expr': 'invariantFn()'}},
            'patch': {'file': 'Contract.sol', 'contract': 'PoC',
                      'functions': [{'name': 'test_POC'}]},
            'probe': {'contract': 'PoC', 'exploit_test': 'test_POC'},
        }

    def test_migrates_single_owner_function(self):
        anchor = {'bindability': 'single_anchor',
                  'suggested_patch_contract': 'Business'}
        migration = _migrate_patch_contract(self.SRC, self._binding(), anchor,
                                            'PoC', 'Contract.sol')
        self.assertEqual(migration['migrated_to'], 'Business')
        self.assertEqual(migration['function'], 'invariantFn')
        self.assertEqual(self._binding()['patch']['contract'], 'PoC')  # copy untouched
        binding = self._binding()
        _migrate_patch_contract(self.SRC, binding, anchor, 'PoC', 'Contract.sol')
        self.assertEqual(binding['patch']['contract'], 'Business')
        self.assertEqual(binding['patch']['functions'][0]['name'], 'invariantFn')

    def test_skips_when_no_owner_function(self):
        anchor = {'bindability': 'single_anchor',
                  'suggested_patch_contract': 'Business'}
        binding = self._binding()
        binding['bindings']['s']['solidity_expr'] = 'true'
        migration = _migrate_patch_contract(self.SRC, binding, anchor,
                                            'PoC', 'Contract.sol')
        self.assertTrue(migration['skipped'])
        self.assertEqual(binding['patch']['contract'], 'PoC')

    def test_skips_when_multi_contract(self):
        anchor = {'bindability': 'multi_contract', 'suggested_patch_contract': None}
        binding = self._binding()
        migration = _migrate_patch_contract(self.SRC, binding, anchor,
                                            'PoC', 'Contract.sol')
        self.assertIsNone(migration)
        self.assertEqual(binding['patch']['contract'], 'PoC')

    def test_migrates_from_poc_call_when_binding_has_no_function(self):
        source = (
            'contract Business {\n'
            '  function doThing() public {}\n'
            '}\n'
            'contract PoC {\n'
            '  function test_POC() public {\n'
            '    Business biz;\n'
            '    biz.doThing();\n'
            '  }\n'
            '}\n'
        )
        anchor = {'bindability': 'single_anchor',
                  'suggested_patch_contract': 'Business'}
        binding = {
            'bindings': {'s': {'solidity_expr': 'true'}},
            'patch': {'file': 'Contract.sol', 'contract': 'PoC',
                      'functions': [{'name': 'test_POC'}]},
            'probe': {'contract': 'PoC', 'exploit_test': 'test_POC'},
        }
        migration = _migrate_patch_contract(source, binding, anchor, 'PoC',
                                            'Contract.sol', 'test_POC')
        self.assertEqual(migration['migrated_to'], 'Business')
        self.assertEqual(migration['function'], 'doThing')
        self.assertEqual(binding['patch']['functions'][0]['name'], 'doThing')
