"""Unit coverage for isolated impact claim IDs, symbol namespaces and abstentions."""
import unittest
import json
import tempfile
from pathlib import Path

from lib.multi_impact import (claim_id_for_impact, merge_claim_formalizations,
                              namespace_formalization)
from lib.ingest import build_catalog, hydrate_elements, hydrate_formalization
from lib.plan_synthesizer import synthesize_id_formalization
from lib.semantic_core import compile_bundle, symbols_for_claim
from lib.solving import solve_queries
from cli.batch_verify import verify_multi_impact_plans
from tests.test_evidence_ids import id_inputs, TEXT
from tests.test_plan_synthesizer import plan


class MultiImpactClaimTests(unittest.TestCase):
    def test_claim_ids_are_stable_valid_and_distinct(self):
        first = claim_id_for_impact('impact_revert')
        self.assertEqual(first, claim_id_for_impact('impact_revert'))
        self.assertNotEqual(first, claim_id_for_impact('impact_no_dispatch'))
        self.assertLessEqual(len(first), 64)
        self.assertTrue(first.startswith('impact_claim_'))

    def test_namespace_rewrites_only_formula_variables(self):
        elements, _ = id_inputs()
        formal = synthesize_id_formalization(plan(), elements)
        renamed = namespace_formalization(formal, claim_id_for_impact('impact_revert'))
        self.assertNotIn('paid_fee', renamed['symbols'])
        claim = renamed['claims'][0]
        self.assertEqual(claim['id'], claim_id_for_impact('impact_revert'))
        used = symbols_for_claim(claim, renamed['symbols'])
        self.assertTrue(used)
        self.assertTrue(all(name.startswith('c') for name in used))

    def test_every_impact_gets_one_formal_or_explicit_unformalized_claim(self):
        elements, _ = id_inputs()
        per_impact = synthesize_id_formalization(plan(), elements)
        impact_ids = [row['id'] for row in elements['statements']
                      if row['kind'] == 'impact']
        failed = [(impact_id, 'No faithful formula after bounded retries.')
                  for impact_id in impact_ids if impact_id != 'impact_revert']
        merged = merge_claim_formalizations(
            [('impact_revert', per_impact)], elements, failed)
        self.assertEqual(len(merged['claims']), len(impact_ids))
        self.assertEqual({claim['impact_ids'][0] for claim in merged['claims']},
                         set(impact_ids))
        self.assertEqual(sum(row['status'] == 'unformalized'
                             for claim in merged['claims']
                             for row in claim['effect_coverage']), len(failed))
        self.assertEqual(len(merged['symbols']), len(per_impact['symbols']))
        self.assertTrue(any('No faithful formula after bounded retries.' in item
                            for item in merged['limitations']))

    def test_duplicate_or_missing_impact_disposition_is_rejected(self):
        elements, _ = id_inputs()
        per_impact = synthesize_id_formalization(plan(), elements)
        with self.assertRaisesRegex(ValueError, 'exactly one claim disposition'):
            merge_claim_formalizations([('impact_revert', per_impact)], elements)

    def test_partial_multi_claim_bundle_compiles_and_keeps_reasons(self):
        elements_raw, _ = id_inputs()
        impact_ids = [row['id'] for row in elements_raw['statements']
                      if row['kind'] == 'impact']
        one = synthesize_id_formalization(
            plan(), elements_raw, claim_id=claim_id_for_impact('impact_revert'),
            include_unselected_limitations=False)
        failures = [(impact_id, 'No faithful relation could be built.')
                    for impact_id in impact_ids if impact_id != 'impact_revert']
        formal_raw = merge_claim_formalizations(
            [('impact_revert', one)], elements_raw, failures)
        catalog = build_catalog(TEXT)
        elements = hydrate_elements(elements_raw, catalog, TEXT)
        formal = hydrate_formalization(formal_raw, catalog, TEXT)
        bundle = compile_bundle(elements, formal, TEXT, strict_piv=True,
                                verdict_v2=True, require_complete_piv=True)
        self.assertEqual(len(bundle['claims']), len(impact_ids))
        self.assertEqual(bundle['coverage_status'], 'partial')
        coverage = {row['impact_id']: row for row in bundle['report_impact_coverage']}
        self.assertEqual(coverage['impact_revert']['status'], 'formalized')
        self.assertEqual(coverage['impact_ux']['status'], 'unformalized')
        self.assertIn('No faithful relation could be built.',
                      coverage['impact_ux']['reason'])
        for claim in formal['claims']:
            props = claim['properties']
            base = {'symbols': {name: {key: value for key, value in item.items()
                                       if key != 'entity_ids'}
                                for name, item in symbols_for_claim(
                                    claim, formal['symbols']).items()},
                    'properties': {name: {key: value for key, value in prop.items()
                                          if key != 'source_ids'}
                                   for name, prop in props.items()},
                    'assumptions': claim['assumptions'],
                    'unresolved': claim['unresolved']}
            queries = solve_queries(base, TEXT)
            expected = ({'P', 'P_and_I', 'P_and_not_I', 'P_and_V',
                         'P_and_V_and_not_I', 'P_and_V_and_I'}
                        if all(prop['expression'] is not None
                               for prop in props.values()) else set())
            self.assertEqual(set(queries), expected)

    def test_multi_impact_plan_set_replays_without_model_calls(self):
        elements, _ = id_inputs()
        impacts = [row['id'] for row in elements['statements']
                   if row['kind'] == 'impact']
        candidate = plan()
        successful = synthesize_id_formalization(
            candidate, elements, claim_id=claim_id_for_impact('impact_revert'),
            include_unselected_limitations=False)
        failures = [(impact_id, 'No faithful formula after bounded retries.')
                    for impact_id in impacts if impact_id != 'impact_revert']
        formal = merge_claim_formalizations([('impact_revert', successful)],
                                            elements, failures)
        with tempfile.TemporaryDirectory() as work:
            root = Path(work)
            entries = []
            for impact_id in impacts:
                target = root / 'impact-formalizations' / impact_id
                target.mkdir(parents=True)
                entry = {'impact_id': impact_id,
                         'claim_id': claim_id_for_impact(impact_id)}
                if impact_id == 'impact_revert':
                    entry.update({'status': 'formalized_candidate',
                                  'formal_plan_path': f'impact-formalizations/{impact_id}/formal-plan.json'})
                    (target / 'formal-plan.json').write_text(json.dumps(candidate))
                    (target / 'formalization-ids.json').write_text(json.dumps(
                        synthesize_id_formalization(
                            candidate, elements,
                            claim_id=claim_id_for_impact(impact_id),
                            include_unselected_limitations=False)))
                    neural = target / 'neural-formalization'
                    neural.mkdir()
                    (neural / 'model-claim.json').write_text(json.dumps(candidate))
                    (target / 'formalization-attempts.json').write_text(json.dumps([
                        {'outcome': 'accepted_for_validation',
                         'artifact_dir': 'neural-formalization'}]))
                else:
                    reason = 'No faithful formula after bounded retries.'
                    entry.update({'status': 'unformalized', 'reason': reason})
                    (target / 'status.json').write_text(json.dumps(
                        {'status': 'unformalized', 'reason': reason}))
                entries.append(entry)
            (root / 'formal-plan.json').write_text(json.dumps({
                'schema_version': 'report-formal-plan-set/1', 'claims': entries}))
            no_reviews = {name: False for name in (
                'numeric_guard', 'address_guard', 'duplicate_predicate_gate',
                'semantic_faithfulness_audit', 'structured_unresolved',
                'relation_alignment', 'requirement_source_review',
                'intent_scope_review', 'placeholder_predicate_review',
                'mixed_unit_scaling_review', 'symbol_table_review',
                'example_pinning_review')}
            self.assertEqual(verify_multi_impact_plans(
                root, elements, formal, no_reviews), [])
            current_formal = merge_claim_formalizations(
                [('impact_revert', successful)], elements, failures,
                include_failed_claims=False)
            self.assertEqual(verify_multi_impact_plans(
                root, elements, current_formal, no_reviews,
                acceptance_policy_version='complete-piv-v1'), [])


if __name__ == '__main__':
    unittest.main()
