import unittest

from lib.witness_router import route


class WitnessRouterTest(unittest.TestCase):
    def test_stage2_semantic_route(self):
        result = route({'consistency_verdict':
                        'invariant_holds_on_exploit_path'})
        self.assertEqual(result['primary_reason'], 'stage2_semantic')
        self.assertEqual(result['next_action'], 'restate_stage2_invariant')

    def test_compile_failed_route(self):
        result = route({'consistency_verdict': 'compile_error',
                        'compile_error': 'undeclared identifier'})
        self.assertEqual(result['primary_reason'], 'compile_failed')
        self.assertIn('undeclared identifier',
                      result['secondary_reasons'][0])

    def test_unknown_route_fails_closed(self):
        result = route({})
        self.assertEqual(result['primary_reason'], 'unresolved')


if __name__ == '__main__':
    unittest.main()
