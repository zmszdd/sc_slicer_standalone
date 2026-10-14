"""semantic-live-5 structural additions: gates, advisory reviews, stage-3 contract.

No model calls.  Covers the four post-closure features and the stage-3
binding/feedback loop; every fixture is local JSON or a literal dict.
"""
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from lib.plan_synthesizer import (check_distinct_p_predicates, intent_scope_review,
                              placeholder_predicate_review,
                              relax_unsupported_relation, requirement_source_review)
from lib.stage3_consistency import (binding_contract, ingest_feedback)
from tests.test_evidence_ids import id_inputs

HERE = Path(__file__).resolve().parents[1]


def live_plan():
    """A minimal report-formal-plan/4 shaped fixture (not schema-validated)."""
    return {
        'schema_version': 'report-formal-plan/4',
        'relation_class': 'value_relation',
        'precondition_ids': ['pre_a', 'pre_b'],
        'intent_id': 'intent_guard',
        'impact_ids': ['impact_bad'],
        'symbols': {
            'flag_a': {'sort': 'bool', 'unit': None, 'meaning': 'first fact',
                       'checkpoint': 'before', 'entity_ids': ['caller'],
                       'source_ids': ['pre_a']},
            'flag_b': {'sort': 'bool', 'unit': None, 'meaning': 'second fact',
                       'checkpoint': 'before', 'entity_ids': ['caller'],
                       'source_ids': ['pre_b']},
            'held': {'sort': 'bool', 'unit': None, 'meaning': 'guard holds',
                     'checkpoint': 'after', 'entity_ids': ['caller'],
                     'source_ids': ['intent_guard']},
            'bad': {'sort': 'bool', 'unit': None, 'meaning': 'bad result',
                    'checkpoint': 'after', 'entity_ids': ['caller'],
                    'source_ids': ['impact_bad']},
        },
        'precondition_terms': [
            {'source_id': 'pre_a', 'predicate': {'kind': 'truth', 'symbol': 'flag_a',
                                                 'value': True}},
            {'source_id': 'pre_b', 'predicate': {'kind': 'truth', 'symbol': 'flag_b',
                                                 'value': True}},
        ],
        'derived_definitions': [],
        'pattern': {'kind': 'relation_obligation',
                    'condition': {'kind': 'truth', 'symbol': 'flag_a', 'value': True},
                    'relation': {'kind': 'truth', 'symbol': 'held', 'value': True}},
        'assumptions': [], 'unresolved': [], 'limitations': [],
    }


def statement(statement_id, kind, text):
    return {'id': statement_id, 'kind': kind, 'text': text, 'modality': 'asserted',
            'entity_ids': ['caller'], 'evidence_ids': []}


def fixture_elements(intent_text='The guard must hold for any unauthorized caller.'):
    return {'schema_version': 'report-elements/2',
            'scope': {'flow': 'f', 'environment': 'e', 'evidence_ids': []},
            'entities': [{'id': 'caller', 'name': 'caller', 'role': 'attacker',
                          'evidence_ids': []}],
            'statements': [
                statement('pre_a', 'precondition', 'The pool is initialized before the call.'),
                statement('pre_b', 'precondition', 'The caller is not the owner of the pool.'),
                statement('intent_guard', 'security_intent', intent_text),
                statement('impact_bad', 'impact', 'An unauthorized caller drains the pool.'),
            ],
            'attack_steps': [], 'ambiguities': []}


class DuplicatePredicateGateTests(unittest.TestCase):
    def test_identical_predicates_are_rejected(self):
        # final_holdout_01 GTE_Perps shape: two sources, one truth predicate.
        plan = live_plan()
        plan['precondition_terms'][1]['predicate'] = \
            plan['precondition_terms'][0]['predicate']
        with self.assertRaisesRegex(ValueError,
                                    'distinct P sources reuse identical predicate'):
            check_distinct_p_predicates(plan)

    def test_distinct_predicates_pass(self):
        check_distinct_p_predicates(live_plan())

    def test_gate_matches_the_v5_rejection_message(self):
        # The gate reuses the v5 schema's exact message so the repair channel
        # and the boundary table keep routing it identically.
        from lib.plan_synthesizer import identical_p_predicates
        plan = live_plan()
        self.assertEqual(identical_p_predicates(plan), [])
        plan['precondition_terms'][1]['predicate'] = \
            plan['precondition_terms'][0]['predicate']
        self.assertEqual(identical_p_predicates(plan), ['pre_b'])

    def test_mirrored_comparisons_are_one_predicate(self):
        # blind-batch_03 GTE_Perps: the two salt facts lowered to
        # real ne derived and derived ne real (one side spelled as a bare
        # symbol, the other as {"symbol": ...}), so the JSON-exact check
        # passed a fact collapse.
        from lib.plan_synthesizer import identical_p_predicates
        plan = live_plan()
        plan['precondition_terms'] = [
            {'source_id': 'pre_a',
             'predicate': {'kind': 'comparison', 'left': 'real_pair',
                           'operator': 'ne',
                           'right': {'symbol': 'derived_pair'}}},
            {'source_id': 'pre_b',
             'predicate': {'kind': 'comparison', 'left': 'derived_pair',
                           'operator': 'ne', 'right': 'real_pair'}},
        ]
        self.assertEqual(identical_p_predicates(plan), ['pre_b'])

    def test_same_symbol_zero_bound_family_is_one_predicate(self):
        # blind-batch_03 Monetrix: borrow_value > 0 and borrow_value != 0
        # from two sources -- not logically equivalent, but at most one
        # report fact can live in a same-observable zero bound.
        from lib.plan_synthesizer import identical_p_predicates
        plan = live_plan()
        plan['precondition_terms'] = [
            {'source_id': 'pre_a',
             'predicate': {'kind': 'comparison', 'left': 'borrow_value',
                           'operator': 'gt', 'right': {'const': 0}}},
            {'source_id': 'pre_b',
             'predicate': {'kind': 'comparison', 'left': 'borrow_value',
                           'operator': 'ne', 'right': {'const': 0}}},
        ]
        self.assertEqual(identical_p_predicates(plan), ['pre_b'])
        with self.assertRaisesRegex(ValueError,
                                    'distinct P sources reuse identical predicate'):
            check_distinct_p_predicates(plan)

    def test_distinct_zero_bounds_on_distinct_symbols_stay_clean(self):
        from lib.plan_synthesizer import identical_p_predicates
        plan = live_plan()
        plan['precondition_terms'] = [
            {'source_id': 'pre_a',
             'predicate': {'kind': 'comparison', 'left': 'x',
                           'operator': 'gt', 'right': {'const': 0}}},
            {'source_id': 'pre_b',
             'predicate': {'kind': 'comparison', 'left': 'y',
                           'operator': 'ne', 'right': {'const': 0}}},
        ]
        self.assertEqual(identical_p_predicates(plan), [])
        check_distinct_p_predicates(plan)


class CompoundTermBudgetTests(unittest.TestCase):
    """blind-batch_04: a faithful 5-fact all_of died on the 4-term cap.
    The report, not the schema, sets the fact count (S16); the cap only
    guards against degenerate compounds."""

    @staticmethod
    def _symbols(count):
        return {f'flag_{i}': {'sort': 'bool'} for i in range(count)}

    @staticmethod
    def _compound(count):
        return {'kind': 'all_of', 'terms': [
            {'kind': 'truth', 'symbol': f'flag_{i}', 'value': True}
            for i in range(count)]}

    def test_five_report_facts_fit_the_budget(self):
        from lib.plan_synthesizer import _predicate
        _predicate(self._compound(5), self._symbols(5))

    def test_eight_terms_still_fit(self):
        from lib.plan_synthesizer import _predicate
        _predicate(self._compound(8), self._symbols(8))

    def test_nine_terms_stay_malformed(self):
        from lib.plan_synthesizer import _predicate
        with self.assertRaisesRegex(ValueError, 'invalid compound predicate'):
            _predicate(self._compound(9), self._symbols(9))


class PlaceholderPredicateReviewTests(unittest.TestCase):
    """blind-batch_03: structural facts became truth symbols and trivial
    zero bounds.  Advisory only -- the cues are lexical, so the review
    surfaces the suspicion instead of enforcing it."""

    @staticmethod
    def _plan(terms):
        return {'precondition_terms': terms}

    def test_truth_placeholder_for_a_structural_fact_is_flagged(self):
        elements = fixture_elements()
        elements['statements'][0]['text'] = (
            'The factory deploys pairs with CREATE2 salt '
            'keccak(token0, token1, launchpadLp, launchpadFeeDistributor).')
        plan = self._plan([{'source_id': 'pre_a',
                            'predicate': {'kind': 'truth',
                                          'symbol': 'real_pair', 'value': True}}])
        result = placeholder_predicate_review(elements, plan)
        self.assertEqual(result['flagged_count'], 1)
        self.assertEqual(result['flagged'][0]['flag'], 'truth_placeholder')
        self.assertFalse(result['blocks_candidate_acceptance'])

    def test_truth_symbol_for_a_plain_state_fact_is_not_flagged(self):
        result = placeholder_predicate_review(
            fixture_elements(),
            self._plan([{'source_id': 'pre_a',
                         'predicate': {'kind': 'truth', 'symbol': 'flag_a',
                                       'value': True}}]))
        self.assertEqual(result['flagged_count'], 0)
        self.assertEqual(result['schema_version'],
                         'placeholder-predicate-review/1')

    def test_trivial_zero_bound_without_textual_zero_is_flagged(self):
        # blind-batch_03 Monetrix: "0x811 contains both borrow and supply"
        # stood on borrow_value >= 0 -- a bound satisfied by default.
        elements = fixture_elements()
        elements['statements'][0]['text'] = (
            'Slot 0x811 contains both borrow and supply values.')
        plan = self._plan([{'source_id': 'pre_a',
                            'predicate': {'kind': 'comparison',
                                          'left': 'borrow_value',
                                          'operator': 'ge',
                                          'right': {'const': 0}}}])
        result = placeholder_predicate_review(elements, plan)
        self.assertEqual(result['flagged_count'], 1)
        self.assertEqual(result['flagged'][0]['flag'], 'trivial_zero_bound')

    def test_stated_zero_bound_is_not_flagged(self):
        # "greater than or equal to zero" grounds const 0 (final_holdout_02
        # GTE_Perps): the bound is textual, not a placeholder.
        elements = fixture_elements()
        elements['statements'][0]['text'] = (
            'Accrued fees are greater than or equal to zero.')
        plan = self._plan([{'source_id': 'pre_a',
                            'predicate': {'kind': 'comparison',
                                          'left': 'fees', 'operator': 'ge',
                                          'right': {'const': 0}}}])
        self.assertEqual(placeholder_predicate_review(elements, plan)['flagged_count'], 0)


class RequirementSourceReviewTests(unittest.TestCase):
    def test_documentation_citation_is_flagged(self):
        # final_holdout_01 SukukFi shape: a P source stating what documentation
        # requires, not what the incident established.
        elements = fixture_elements()
        elements['statements'][0]['text'] = (
            'The documentation states the decimals must equal the underlying '
            'asset decimals plus the offset.')
        result = requirement_source_review(elements, live_plan())
        self.assertEqual(result['flagged_count'], 1)
        self.assertEqual(result['flagged'][0]['statement_id'], 'pre_a')
        self.assertFalse(result['blocks_candidate_acceptance'])

    def test_incident_fact_is_not_flagged(self):
        result = requirement_source_review(fixture_elements(), live_plan())
        self.assertEqual(result['flagged_count'], 0)
        self.assertEqual(result['schema_version'], 'requirement-source-review/1')


class IntentScopeReviewTests(unittest.TestCase):
    def test_impact_only_condition_symbols_flag_narrowing(self):
        # Dual-review partial shape: the intent claims a general scope but
        # every condition symbol is grounded only by the impact subcase.
        plan = live_plan()
        plan['symbols']['flag_a']['source_ids'] = ['impact_bad']
        result = intent_scope_review(plan, fixture_elements())
        self.assertTrue(result['scope_narrowing_risk'])
        self.assertEqual(result['condition_symbols_grounded_only_by_impacts'],
                         ['flag_a'])
        self.assertFalse(result['blocks_candidate_acceptance'])

    def test_precondition_grounded_condition_is_not_flagged(self):
        result = intent_scope_review(live_plan(), fixture_elements())
        self.assertFalse(result['scope_narrowing_risk'])
        self.assertEqual(set(result['intent_scope_cues']), {'for any', 'unauthorized'})

    def test_no_scope_cues_is_not_flagged(self):
        elements = fixture_elements(intent_text='The guard holds for this flow.')
        result = intent_scope_review(live_plan(), elements)
        self.assertEqual(result['intent_scope_cues'], [])
        self.assertFalse(result['scope_narrowing_risk'])


class PartialFormalizationTests(unittest.TestCase):
    def blocking_plan(self):
        plan = live_plan()
        plan['symbols']['rate_relation'] = {
            'sort': 'bool', 'unit': None,
            'meaning': 'the credited rate equals the full rate for the period',
            'checkpoint': 'after', 'entity_ids': ['caller'],
            'source_ids': ['intent_guard', 'impact_bad']}
        plan['pattern']['relation'] = {'kind': 'truth', 'symbol': 'rate_relation',
                                       'value': True}
        plan['unresolved'] = [{
            'category': 'unsupported_relation',
            'description': 'rate quantities cannot be expressed without division',
            'source_ids': ['intent_guard', 'impact_bad'],
            'blocks_formalization': True}]
        return plan

    def test_represented_relation_is_downgraded_with_audit(self):
        plan, changes = relax_unsupported_relation(self.blocking_plan(), fixture_elements())
        self.assertFalse(plan['unresolved'][0]['blocks_formalization'])
        self.assertEqual(changes[0]['kind'], 'relax_unsupported_relation')
        self.assertEqual(changes[0]['representing_symbol'], 'rate_relation')

    def test_unrepresented_relation_stays_blocking(self):
        plan = self.blocking_plan()
        del plan['symbols']['rate_relation']
        plan['pattern']['relation'] = {'kind': 'truth', 'symbol': 'held', 'value': True}
        unchanged, changes = relax_unsupported_relation(plan, fixture_elements())
        self.assertTrue(unchanged['unresolved'][0]['blocks_formalization'])
        self.assertEqual(changes, [])

    def test_partial_source_coverage_does_not_qualify(self):
        plan = self.blocking_plan()
        plan['symbols']['rate_relation']['source_ids'] = ['intent_guard']
        unchanged, changes = relax_unsupported_relation(plan, fixture_elements())
        self.assertTrue(unchanged['unresolved'][0]['blocks_formalization'])
        self.assertEqual(changes, [])


class BindingContractTests(unittest.TestCase):
    def formalization(self):
        elements, formal = id_inputs()
        return formal

    def test_contract_lists_roles_and_binding_kinds(self):
        formal = self.formalization()
        claim = formal['claims'][0]
        contract = binding_contract(formal, claim)
        self.assertEqual(contract['schema_version'], 'stage3-binding-contract/1')
        by_name = {row['symbol']: row for row in contract['symbols']}
        self.assertIn('P', by_name['paid_fee']['appears_in'])
        self.assertEqual(by_name['paid_fee']['binding_kind'], 'numeric_value')
        self.assertEqual(by_name['fee_mismatch_reverted']['binding_kind'], 'boolean_predicate')

    def test_undeclared_symbol_binding_kind_is_not_required(self):
        formal = self.formalization()
        # A declared symbol that no formula references needs no stage-3 binding.
        formal['symbols']['unused_witness'] = dict(
            formal['symbols']['paid_fee'], meaning='never referenced')
        contract = binding_contract(formal, formal['claims'][0])
        by_name = {row['symbol']: row for row in contract['symbols']}
        self.assertEqual(by_name['unused_witness']['appears_in'], [])
        self.assertEqual(by_name['unused_witness']['binding_kind'], 'not_required')


class IngestFeedbackTests(unittest.TestCase):
    def setUp(self):
        self.workdir = Path(tempfile.mkdtemp())
        self.rundir = self.workdir / 'run'
        self.rundir.mkdir()
        self.formal = self.formalization()
        (self.rundir / 'formalization.json').write_text(
            json.dumps(self.formal))
        contract = binding_contract(self.formal, self.formal['claims'][0])
        spec = {'schema_version': 'stage3-semantic-spec/1',
                'claims': [{'claim_id': 'buffered_unstake',
                            'code_queries_after_binding': [
                                'P_and_T', 'P_and_T_and_not_I', 'P_and_T_and_V',
                                'P_and_T_and_not_V'],
                            'binding_contract': contract}],
                'execution_ready': False}
        (self.rundir / 'stage3-spec.json').write_text(json.dumps(spec))
        (self.rundir / 'constraints.json').write_text('{}')

    def tearDown(self):
        shutil.rmtree(self.workdir)

    def formalization(self):
        elements, formal = id_inputs()
        return formal

    def feedback(self, **overrides):
        symbols = {row['symbol']: {'status': 'bound', 'binding': 'code variable'}
                   for row in binding_contract(self.formal, self.formal['claims'][0])['symbols']
                   if row['appears_in']}
        payload = {'schema_version': 'stage3-consistency-feedback/1',
                   'claim_id': 'buffered_unstake', 'symbol_bindings': symbols,
                   'code_query_results': {'P_and_T': 'sat', 'P_and_T_and_V': 'sat'}}
        payload.update(overrides)
        return payload

    def test_violation_reproduced_verdict(self):
        record = ingest_feedback(self.rundir, self.feedback())
        self.assertEqual(record['consistency_verdict'], 'violation_reproduced')
        self.assertEqual(record['model_calls'], 0)
        self.assertTrue((self.rundir / 'stage3-consistency.json').is_file())

    def test_display_form_query_names_are_normalized(self):
        """Real stage3-spec.json declares "P AND T"; ingest must accept either.

        Regression from the first live smoke run: feedback keyed by the
        spec's display form was rejected outright, and had it passed, the
        verdict logic (underscore keys) would have seen nothing.
        """
        (self.rundir / 'stage3-spec.json').write_text(json.dumps(
            {'schema_version': 'stage3-semantic-spec/1',
             'claims': [{'claim_id': 'buffered_unstake',
                         'code_queries_after_binding': [
                             'P AND T', 'P AND T AND NOT I',
                             'P AND T AND V', 'P AND T AND NOT V'],
                         'binding_contract': binding_contract(
                             self.formal, self.formal['claims'][0])}],
             'execution_ready': False}))
        feedback = self.feedback(code_query_results={
            'P AND T': 'sat', 'P AND T AND V': 'sat'})
        record = ingest_feedback(self.rundir, feedback)
        self.assertEqual(record['consistency_verdict'], 'violation_reproduced')
        self.assertEqual(record['code_query_results'],
                         {'P_and_T': 'sat', 'P_and_T_and_V': 'sat'})

    def test_unbound_symbol_gives_partial_binding(self):
        feedback = self.feedback()
        name = next(iter(feedback['symbol_bindings']))
        feedback['symbol_bindings'][name] = {'status': 'unbound',
                                             'binding': 'no code observable found'}
        record = ingest_feedback(self.rundir, feedback)
        self.assertEqual(record['consistency_verdict'], 'partial_binding')
        self.assertEqual(record['unbound_symbols'], [name])

    def test_infeasible_preconditions_flag_binding(self):
        record = ingest_feedback(self.rundir, self.feedback(
            code_query_results={'P_and_T': 'unsat', 'P_and_T_and_V': 'unknown'}))
        self.assertEqual(record['consistency_verdict'],
                         'preconditions_infeasible_on_code')

    def test_second_ingestion_is_refused(self):
        ingest_feedback(self.rundir, self.feedback())
        with self.assertRaisesRegex(ValueError, 'already adjudicated'):
            ingest_feedback(self.rundir, self.feedback())

    def test_unknown_symbol_binding_is_rejected(self):
        feedback = self.feedback()
        feedback['symbol_bindings']['invented'] = {'status': 'bound',
                                                   'binding': 'x'}
        with self.assertRaisesRegex(ValueError, 'symbol_bindings'):
            ingest_feedback(self.rundir, feedback)

    def test_unknown_query_name_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'code_query_results'):
            ingest_feedback(self.rundir, self.feedback(
                code_query_results={'P_and_V': 'sat'}))


if __name__ == '__main__':
    unittest.main()
