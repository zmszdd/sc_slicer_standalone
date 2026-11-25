"""Deterministic semantic UNBOUND classifier tests; no LLM calls."""
import unittest

from lib.unbound_semantics import resolve_unbound


def binding(entries):
    return {'schema_version': 'stage3-binding/1', 'claim_id': 'c',
            'bindings': entries}


def entry(kind='boolean_predicate', expr='UNBOUND'):
    return {'kind': kind, 'solidity_expr': expr, 'checkpoint': 'before',
            'source': 'C.sol:f'}


def contract(rows):
    return {'schema_version': 'stage3-binding-contract/1',
            'claim_id': 'c', 'symbols': rows}


def row(symbol, meaning, kind='boolean_predicate', appears=None, **extra):
    value = {'symbol': symbol, 'sort': 'bool' if kind == 'boolean_predicate' else 'int',
             'unit': None if kind == 'boolean_predicate' else 'wei',
             'meaning': meaning, 'checkpoint': 'before',
             'entity_ids': [], 'appears_in': appears or ['I'],
             'binding_kind': kind}
    value.update(extra)
    return value


class UnboundSemanticsTest(unittest.TestCase):
    def test_effect_only_does_not_block(self):
        result, changes, report = resolve_unbound(
            binding({'v': entry(expr='UNBOUND')}),
            contract([row('v', 'event emitted', appears=['V'])]), 'contract C {}')
        self.assertEqual(report['items']['v']['bucket'], 'semantic_effect_only')
        self.assertEqual(report['items']['v']['route'], 'effect_probe_optional')
        self.assertEqual(changes, [])
        self.assertEqual(result['bindings']['v']['solidity_expr'], 'UNBOUND')

    def test_time_window_repairs_from_start_and_duration(self):
        source = ('contract Vault {\n'
                  '  uint256 public start;\n'
                  '  uint256 public duration;\n'
                  '}\n')
        result, changes, report = resolve_unbound(
            binding({'within_window': entry()}),
            contract([row('within_window',
                          'call occurs within the vesting window after start duration',
                          checkpoint='call_entry')]),
            source, injection_contract='Vault')
        self.assertEqual(report['items']['within_window']['bucket'],
                         'semantic_time_window')
        self.assertEqual(result['bindings']['within_window']['solidity_expr'],
                         'block.timestamp < (start + duration)')
        self.assertTrue(changes)

    def test_cross_contract_symbol_is_receiver_qualified(self):
        source = ('contract Oracle {\n'
                  '  uint256 public price;\n'
                  '}\n'
                  'contract Harness {\n'
                  '  Oracle oracle;\n'
                  '}\n')
        result, changes, report = resolve_unbound(
            binding({'oracle_price': entry(kind='numeric_value')}),
            contract([row('oracle_price', 'price reported by oracle',
                          kind='numeric_value', scope='cross_contract',
                          receiver='oracle', contract_type='Oracle')]),
            source, injection_contract='Harness')
        self.assertEqual(report['items']['oracle_price']['bucket'],
                         'semantic_cross_contract')
        self.assertEqual(result['bindings']['oracle_price']['solidity_expr'],
                         'oracle.price')

    def test_derived_boolean_uses_complementary_meaning(self):
        result, changes, report = resolve_unbound(
            binding({'fee_charged': entry(),
                     'fee_waived': entry(expr='true')}),
            contract([row('fee_charged', 'fee is charged'),
                      row('fee_waived', 'fee is not charged', appears=['V'])]),
            'contract C { bool feeWaived; }')
        self.assertEqual(report['items']['fee_charged']['bucket'],
                         'semantic_derived_boolean')
        self.assertEqual(result['bindings']['fee_charged']['solidity_expr'],
                         '!(true)')

    def test_mapping_getter_stays_unresolved_without_key(self):
        source = ('struct S { uint256 a; }\n'
                  'contract C { mapping(uint256 => S) public states; }\n')
        result, changes, report = resolve_unbound(
            binding({'epoch_state': entry(kind='numeric_value')}),
            contract([row('epoch_state', 'state for the epoch',
                          kind='numeric_value', observable_kind='mapping')]),
            source, injection_contract='C')
        self.assertEqual(report['items']['epoch_state']['bucket'],
                         'semantic_mapping_or_struct_getter')
        self.assertIn('epoch_state', report['unresolved'])
        self.assertEqual(result['bindings']['epoch_state']['solidity_expr'],
                         'UNBOUND')

    def test_genuinely_unobservable_routes_away_from_rebinding(self):
        _result, _changes, report = resolve_unbound(
            binding({'secret': entry()}),
            contract([row('secret', 'internal value with no reader')]),
            'contract C {}', injection_contract='C')
        self.assertEqual(report['items']['secret']['bucket'],
                         'genuinely_unobservable')
        self.assertEqual(report['route_suggestion'],
                         'stage2_restate_or_reference_patch')
        self.assertTrue(report['terminal_unresolved'])

    def test_input_binding_is_not_mutated(self):
        original = binding({'v': entry(expr='UNBOUND')})
        resolve_unbound(original, contract([row('v', 'event')]), 'contract C {}')
        self.assertEqual(original['bindings']['v']['solidity_expr'], 'UNBOUND')


if __name__ == '__main__':
    unittest.main()
