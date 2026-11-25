import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from evaluation.metrics import stage2_restatement_binding_candidate as candidate


class Stage2RestatementCandidateBindingTest(unittest.TestCase):
    def test_selects_first_fully_bound_candidate(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            stage2_root = root / 'stage2'
            stage2 = stage2_root / 'case_a'
            flatten = root / 'flatten' / 'case_a'
            stage2.mkdir(parents=True)
            flatten.mkdir(parents=True)
            (flatten / 'contract.flattened.t.sol').write_text('contract T {}')
            claim_id = 'claim_a'
            spec = {
                'claims': [{
                    'claim_id': claim_id,
                    'formalization_status': 'formalized_candidate',
                    'binding_contract': {'symbols': [
                        {'symbol': 'p_symbol', 'appears_in': ['P']},
                        {'symbol': 'i_symbol', 'appears_in': ['I']},
                        {'symbol': 'v_symbol', 'appears_in': ['V']},
                    ]},
                }],
            }
            formal = {'claims': [{
                'id': claim_id,
                'properties': {
                    'preconditions': {'expression': {'var': 'p_symbol'}},
                    'safety': {'expression': {'var': 'i_symbol'}},
                    'effects': {'expression': {'var': 'v_symbol'}},
                },
            }]}
            for name, payload in (
                    ('stage3-spec.json', spec),
                    ('constraints.json', {}),
                    ('formalization.json', formal),
                    ('provenance.json', {'continue_on_review': True})):
                (stage2 / name).write_text(json.dumps(payload))

            def fake_assemble_case(**kwargs):
                out = Path(kwargs['out'])
                (out / 'src').mkdir(parents=True, exist_ok=True)
                (out / 'test').mkdir(parents=True, exist_ok=True)
                (out / 'src' / 'Contract.sol').write_text('contract T {}')
                return out

            hints = []

            def fake_run(command, **kwargs):
                out = Path(command[command.index('--out') + 1])
                hint = command[command.index('--hint') + 1]
                hints.append(hint)
                index = int(out.name.split('_')[1])
                expr = 'UNBOUND' if index == 1 else 'amount > 0'
                binding = {
                    'schema_version': 'stage3-binding/1',
                    'claim_id': claim_id,
                    'bindings': {
                        'p_symbol': {'kind': 'boolean_predicate',
                                     'solidity_expr': 'true',
                                     'checkpoint': 'before',
                                     'source': 'Contract.sol:T'},
                        'i_symbol': {'kind': 'boolean_predicate',
                                     'solidity_expr': expr,
                                     'checkpoint': 'after',
                                     'source': 'Contract.sol:T'},
                        'v_symbol': {'kind': 'boolean_predicate',
                                     'solidity_expr': 'true',
                                     'checkpoint': 'after',
                                     'source': 'Contract.sol:T'},
                    },
                    'patch': {'file': 'Contract.sol', 'contract': 'T',
                              'functions': [{'name': 'run'}]},
                    'probe': {'contract': 'TTest', 'exploit_test': 'testRun'},
                }
                (out / 'binding.proposal.json').write_text(
                    json.dumps(binding))
                return type('Proc', (), {
                    'stdout': json.dumps({'ok': index == 2,
                                          'partial': index == 1,
                                          'unbound': ['i_symbol']
                                          if index == 1 else []}),
                    'stderr': '',
                })()

            restatement = {'status': 'unresolved',
                           'unresolved': [{'reason': 'no unique outcome'}],
                           'changes': []}
            with patch.object(candidate.case_builder, 'assemble_case',
                              side_effect=fake_assemble_case), \
                    patch.object(candidate.stage2_contract, 'load',
                                 return_value={}), \
                    patch.object(candidate.stage2_restate, 'restate_claim',
                                 return_value=restatement), \
                    patch.object(candidate, 'lint_binding',
                                 return_value={'summary': {'errors': 0},
                                               'problems': []}):
                report = candidate.build(
                    stage2_root, flatten.parent, root / 'out',
                    cases=['case_a'], candidates=2, run_fn=fake_run)

            claim_row = report['cases'][0]['claims'][0]
            self.assertEqual(claim_row['selected'], 2)
            binding = json.loads((root / 'out' / 'cases' / 'case_a'
                                  / 'bindings' / f'{claim_id}.json').read_text())
            self.assertEqual(
                binding['bindings']['i_symbol']['solidity_expr'], 'amount > 0')
            self.assertIn('stage2_restatement_status=unresolved', hints[0])
            self.assertIn('reject_unbound=i_symbol', hints[1])


if __name__ == '__main__':
    unittest.main()
