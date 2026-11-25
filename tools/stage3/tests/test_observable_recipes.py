import unittest

from lib.observable_recipes import audit, build, is_compile_ready


SYMBOLS = {
    'tree_size_before': {
        'checkpoint': 'before', 'observability': 'high', 'meaning': 'tree size',
        'sort': 'uint256'},
    'tree_size_after': {
        'checkpoint': 'after', 'observability': 'high', 'meaning': 'tree size',
        'sort': 'uint256'},
    'tree_size_changed': {
        'checkpoint': 'after', 'observability': 'high',
        'meaning': 'tree size changed', 'sort': 'bool'},
    'caller_authorized': {
        'checkpoint': 'before', 'observability': 'medium',
        'meaning': 'caller is authorized', 'sort': 'bool'},
    'get_fee_succeeds': {
        'checkpoint': 'after', 'observability': 'low',
        'meaning': 'getFee completes successfully', 'sort': 'bool'},
}


def candidates():
    high = {'expression': 'treeSize', 'kind': 'state_var',
            'scope': 'single_contract', 'entity_hit': True, 'match_score': 6,
            'solidity_type': 'uint256', 'evidence': 'state variable treeSize'}
    medium = {'expression': 'price', 'kind': 'state_var',
              'scope': 'single_contract', 'entity_hit': False,
              'match_score': 1, 'solidity_type': 'uint256',
              'evidence': 'state variable price'}
    return {
        'tree_size_before': [high],
        'tree_size_after': [high],
        'tree_size_changed': [medium],
        'caller_authorized': [medium],
        'get_fee_succeeds': [medium],
    }


SOURCE = '''
contract Vault {
    uint256 public treeSize;
    uint256 public price;
    address public owner;
    function getFee(uint256 amount) external returns (uint256) { return amount; }
}
'''


SIGNATURES = {
    'functions': {
        'getFee': [{'arity': 1, 'param_types': ['uint256'],
                    'returns': ['uint256']}],
        'owner': [{'arity': 0, 'param_types': [], 'returns': ['address']}],
    },
    'state_vars': {'treeSize': 'uint256', 'price': 'uint256',
                   'owner': 'address'},
    'mapping_getters': {},
    'struct_getters': {},
    'structs': {},
}


class ObservableRecipesTest(unittest.TestCase):
    def test_order_book_getters_are_side_aware_and_compile_ready(self):
        source = '''
struct Limit { uint64 numOrders; }
contract CLOB {
    function getNumBids() external view returns (uint256) { return 0; }
    function getNumAsks() external view returns (uint256) { return 0; }
    function getTOB() external view returns (uint256, uint256) { return (0, 0); }
    function getLimit(uint256 price, Side side) external view returns (Limit memory) {}
    function postLimitOrder(PostArgs memory args) external {
        if (args.side == Side.BUY) { uint256 x = args.price; }
    }
}
'''
        signatures = {'functions': {
            'getNumBids': [{'arity': 0, 'returns': ['uint256']}],
            'getNumAsks': [{'arity': 0, 'returns': ['uint256']}],
            'getTOB': [{'arity': 0, 'returns': ['uint256', 'uint256']}],
            'getLimit': [{'arity': 2, 'returns': ['Limit']}],
        }}
        all_candidates = [
            {'expression': 'clob.getNumBids()'},
            {'expression': 'clob.getNumAsks()'},
            {'expression': 'clob.getTOB()'},
            {'expression': 'clob.getLimit(1, Side.BUY)'},
        ]
        symbols = {
            'tree_size': {'meaning': 'number of price levels in the order tree',
                          'sort': 'uint256', 'checkpoint': 'before'},
            'lowest_price': {'meaning': 'lowest price in the tree',
                             'sort': 'uint256', 'checkpoint': 'before'},
            'orders_at_price': {
                'meaning': 'number of orders at the same price level',
                'sort': 'uint256', 'checkpoint': 'before'},
        }
        plans = build(symbols, {}, source=source, signatures=signatures,
                      all_candidates=all_candidates)
        tree = next(row for row in plans['tree_size']['recipes']
                    if row['kind'] == 'order_book_aggregate')
        self.assertIn('clob.getNumBids()', tree['expression'])
        self.assertIn('clob.getNumAsks()', tree['expression'])
        self.assertTrue(is_compile_ready(tree, 'numeric_value', 'before'))

        top = next(row for row in plans['lowest_price']['recipes']
                   if row['kind'] == 'order_book_aggregate')
        self.assertIn('getTOB()', top['solidity_stmts'][0])
        self.assertTrue(is_compile_ready(top, 'numeric_value', 'before'))

        orders = next(row for row in plans['orders_at_price']['recipes']
                      if row['kind'] == 'order_book_aggregate')
        self.assertEqual(orders['expression'],
                         'clob.getLimit(args.price, args.side).numOrders')
        self.assertTrue(is_compile_ready(orders, 'numeric_value', 'before'))

    def test_transition_uses_before_snapshot(self):
        plan = build(SYMBOLS, candidates(), source=SOURCE,
                     signatures=SIGNATURES)['tree_size_changed']
        transition = next(row for row in plan['recipes']
                          if row['kind'] == 'state_before_after')
        self.assertEqual(transition['expression'],
                         'stage3_tree_size_before != (treeSize)')
        self.assertTrue(transition['executable'])

    def test_medium_candidate_is_planned_not_ready(self):
        plan = build(SYMBOLS, candidates(), source=SOURCE,
                     signatures=SIGNATURES)['caller_authorized']
        self.assertEqual(plan['status'], 'planned')
        self.assertTrue(any(row['kind'] == 'authorization_context'
                            for row in plan['recipes']))

    def test_call_outcome_is_a_plan_not_an_expression(self):
        plan = build(SYMBOLS, candidates(), source=SOURCE,
                     signatures=SIGNATURES)['get_fee_succeeds']
        outcome = next(row for row in plan['recipes']
                       if row['kind'] == 'call_outcome')
        self.assertFalse(outcome['executable'])
        self.assertIn('call_arguments', outcome['required_inputs'])

    def test_call_outcome_with_unique_receiver_emits_monitor(self):
        receiver = {'expression': 'burner.getFee()', 'kind': 'getter',
                    'scope': 'cross_contract', 'entity_hit': False,
                    'match_score': 1, 'solidity_type': 'uint256',
                    'source_grounded': True, 'receiver_known': True,
                    'evidence': 'getter on burner'}
        rows = candidates()
        rows['get_fee_succeeds'] = [receiver]
        signatures = {'functions': {'getFee': [
            {'arity': 0, 'param_types': [], 'returns': ['uint256']}]},
            'state_vars': {}, 'mapping_getters': {}, 'struct_getters': {},
            'structs': {}}
        plan = build(SYMBOLS, rows, source=SOURCE,
                     signatures=signatures)['get_fee_succeeds']
        outcome = next(row for row in plan['recipes']
                       if row['kind'] == 'call_outcome')
        self.assertTrue(outcome['executable'])
        self.assertEqual(outcome['expression'],
                         'stage3_get_fee_succeeds_succeeds')
        self.assertTrue(any('try burner.getFee()' in line
                            for line in outcome['solidity_stmts']))
        self.assertEqual(plan['status'], 'ready')

    def test_authorization_uses_already_grounded_getter_candidate(self):
        owner = {'expression': 'vault.owner()', 'kind': 'getter',
                 'scope': 'cross_contract', 'entity_hit': False,
                 'match_score': 1, 'solidity_type': 'address',
                 'source_grounded': True, 'receiver_known': True,
                 'evidence': 'owner getter'}
        rows = candidates()
        rows['caller_authorized'] = [owner]
        plan = build(SYMBOLS, rows, source=SOURCE,
                     signatures=SIGNATURES)['caller_authorized']
        authorization = next(row for row in plan['recipes']
                             if row['kind'] == 'authorization_context')
        self.assertEqual(authorization['expression'],
                         'msg.sender == vault.owner()')

    def test_deep_source_chain_can_be_ready(self):
        chain = {'expression': 'ds.askTree.size()', 'kind': 'source_expr',
                 'scope': 'source_grounded', 'entity_hit': False,
                 'match_score': 13, 'structural_hits': 2, 'chain_depth': 2,
                 'receiver_known': False, 'source_grounded': True,
                 'solidity_type': 'uint256',
                 'evidence': 'source chain'}
        rows = candidates()
        rows['tree_size_before'] = [chain]
        symbols = {**SYMBOLS, 'tree_size_before': {
            **SYMBOLS['tree_size_before'], 'binding_kind': 'numeric_value'}}
        plan = build(symbols, rows, source=SOURCE,
                     signatures=SIGNATURES)['tree_size_before']
        self.assertEqual(plan['status'], 'ready')

    def test_ambiguous_candidate_is_never_high_confidence(self):
        first = {'expression': 'treeSize', 'kind': 'state_var',
                 'scope': 'single_contract', 'entity_hit': True,
                 'match_score': 6, 'structural_hits': 2,
                 'solidity_type': 'uint256', 'ambiguous': True,
                 'evidence': 'ambiguous tree size'}
        rows = candidates()
        rows['tree_size_before'] = [first]
        plan = build(SYMBOLS, rows, source=SOURCE,
                     signatures=SIGNATURES)['tree_size_before']
        direct = next(row for row in plan['recipes']
                      if row['kind'] == 'state_snapshot')
        self.assertEqual(direct['confidence'], 'medium')
        self.assertEqual(plan['status'], 'planned')

    def test_known_incompatible_type_is_never_high_confidence(self):
        wrong = {'expression': 'treeSize', 'kind': 'state_var',
                 'scope': 'single_contract', 'entity_hit': True,
                 'match_score': 6, 'structural_hits': 2,
                 'solidity_type': 'bool', 'source_grounded': True,
                 'evidence': 'wrongly typed tree size'}
        rows = candidates()
        rows['tree_size_before'] = [wrong]
        plan = build(SYMBOLS, rows, source=SOURCE,
                     signatures=SIGNATURES)['tree_size_before']
        self.assertEqual(plan['status'], 'planned')

    def test_ir_expected_kind_is_used_for_type_compatibility(self):
        typed = {'expression': 'treeSize', 'kind': 'state_var',
                 'scope': 'single_contract', 'entity_hit': True,
                 'match_score': 6, 'structural_hits': 2,
                 'solidity_type': 'uint256', 'source_grounded': True,
                 'ready_eligible': True, 'evidence': 'typed state variable'}
        rows = candidates()
        rows['tree_size_before'] = [typed]
        symbols = {'tree_size_before': {
            'checkpoint': 'before', 'observability': 'high',
            'meaning': 'tree size', 'sort': 'uint256',
            'expected_kind': 'numeric_value'}}
        plan = build(symbols, rows, source=SOURCE,
                     signatures=SIGNATURES)['tree_size_before']
        self.assertEqual(plan['status'], 'ready')

    def test_contract_handle_is_not_a_numeric_snapshot(self):
        handle = {'expression': 'burner', 'kind': 'function_local',
                  'scope': 'function_scope', 'entity_hit': True,
                  'match_score': 6, 'structural_hits': 1,
                  'solidity_type': 'BuyBackBurnerUniswap',
                  'source_grounded': True, 'receiver_known': True,
                  'ready_eligible': True, 'evidence': 'PoC local handle'}
        rows = candidates()
        rows['tree_size_before'] = [handle]
        plan = build(SYMBOLS, rows, source=SOURCE,
                     signatures=SIGNATURES)['tree_size_before']
        direct = next(row for row in plan['recipes']
                      if row['kind'] == 'state_snapshot')
        self.assertEqual(direct['confidence'], 'medium')
        self.assertEqual(plan['status'], 'planned')

    def test_medium_executable_recipe_is_not_counted_as_ready(self):
        plan = build(SYMBOLS, candidates(), source=SOURCE,
                     signatures=SIGNATURES)['tree_size_changed']
        self.assertEqual(plan['status'], 'ready')
        self.assertEqual(plan['ready_count'], 1)
        self.assertGreater(plan['planned_count'], 0)

    def test_recipe_audit_warns_when_ready_recipe_is_ignored(self):
        plans = build(SYMBOLS, candidates(), source=SOURCE,
                      signatures=SIGNATURES)
        binding = {'bindings': {
            'tree_size_changed': {'solidity_expr': 'price > 0'}}}
        result = audit(binding, plans)
        self.assertTrue(any(row['code'] == 'RECIPE_NOT_SELECTED'
                            for row in result['problems']))


if __name__ == '__main__':
    unittest.main()
