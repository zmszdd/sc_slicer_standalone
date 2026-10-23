"""Explicit Impact-area parsing and evidence boundary tests."""

import unittest

from cli.semantic_pipeline import validate_core_element_candidate
from lib.ingest import (build_catalog, explicit_impact_evidence_ids,
                        explicit_impact_ranges, validate_impact_evidence)
from lib.impact_inventory import (merge_impact_inventory,
                                  validate_impact_inventory)
from tests.test_evidence_ids import TEXT, id_inputs


class ExplicitImpactScopeTests(unittest.TestCase):
    def test_supported_explicit_formats(self):
        cases = {
            'markdown heading': (
                '## Description\nCause only.\n## Impact\nFunds are stuck.\n'
                '## Mitigation\nAdd a check.\n', 'Funds are stuck.',
                'Cause only.', 'Add a check.'),
            'bold heading': (
                '** Description **\nCause.\n** Impact **\nUsers lose funds.\n'
                '**Recommended Mitigation:**\nAdd validation.\n',
                'Users lose funds.', 'Cause.', 'Add validation.'),
            'inline label': (
                'Description: cause.\n- **Impact:** swaps execute at stale prices.\n'
                'Mitigation: add deadline.\n', 'swaps execute at stale prices.',
                'Description: cause.', 'Mitigation: add deadline.'),
            'combined heading': (
                '## Intro\nGeneral cause.\n'
                '## Finding description and impact\nCause details.\nDeposits fail.\n'
                '## Affected code\ncontract C {}\n', 'Deposits fail.',
                'General cause.', 'contract C {}'),
            'direct and multi-user labels': (
                '** Impact **\n-> Direct Impact\nRedemptions fail.\n'
                '-> Multi-User Impact\nAll users are affected.\n'
                '**Recommended Mitigation:**\nFix accounting.\n',
                'Redemptions fail.', 'Cause.', 'Fix accounting.'),
            'nested impact headings': (
                '## Impact\nSummary.\n### Direct Impact\nWithdrawals fail.\n'
                '### Multi-User Impact\nAll users are affected.\n'
                '## Mitigation\nChange accounting.\n',
                'Withdrawals fail.', 'Cause.', 'Change accounting.'),
        }
        for name, (text, included, excluded_a, excluded_b) in cases.items():
            with self.subTest(format=name):
                ranges = explicit_impact_ranges(text)
                extracted = '\n'.join(text[start:end] for start, end in ranges)
                self.assertIn(included, extracted)
                self.assertNotIn(excluded_a, extracted)
                self.assertNotIn(excluded_b, extracted)

    def test_unmarked_description_has_no_impact_source(self):
        text = 'Description\nCause leads to a loss.\nRecommended fix\n'
        self.assertEqual(explicit_impact_ranges(text), [])
        self.assertEqual(explicit_impact_evidence_ids(build_catalog(text), text), [])

    def test_impact_evidence_ids_are_a_hard_boundary(self):
        text = ('## Description\nThe function has a bug.\n'
                '## Impact\nUsers cannot withdraw.\n')
        catalog = build_catalog(text)
        allowed = explicit_impact_evidence_ids(catalog, text)
        by_text = {row['text']: row['id'] for row in catalog['fragments']}
        impact_id = next(ident for fragment, ident in by_text.items()
                         if 'Users cannot withdraw.' in fragment)
        description_id = next(ident for fragment, ident in by_text.items()
                              if 'The function has a bug.' in fragment)
        candidate = {'statements': [
            {'id': 'withdrawals_blocked', 'kind': 'impact',
             'evidence_ids': [impact_id]},
        ]}
        validate_impact_evidence(candidate, allowed)
        candidate['statements'][0]['evidence_ids'] = [description_id]
        with self.assertRaisesRegex(ValueError, 'outside marked Impact areas'):
            validate_impact_evidence(candidate, allowed)

    def test_empty_impact_scope_allows_zero_impact_candidate(self):
        elements, _ = id_inputs()
        elements['statements'] = [row for row in elements['statements']
                                  if row['kind'] != 'impact']
        catalog = build_catalog(TEXT)
        validate_core_element_candidate(
            elements, catalog, TEXT, require_core_counts=True,
            normalize_steps=True, normalize_ids=True,
            max_core_impacts=4, max_core_intents=4, impact_source_ids=[])

    def test_impact_inventory_rejects_out_of_scope_evidence(self):
        text = '## Impact\nUsers lose funds.\n## Details\nThe cause is a stale quote.\n'
        catalog = build_catalog(text)
        allowed = explicit_impact_evidence_ids(catalog, text)
        outside = next(row['id'] for row in catalog['fragments']
                       if 'stale quote' in row['text'])
        candidate = {
            'schema_version': 'report-impact-inventory/1',
            'impacts': [{'id': 'fund_loss', 'text': 'Users lose funds.',
                         'modality': 'asserted', 'evidence_ids': [outside]}],
            'ambiguities': [],
        }
        with self.assertRaisesRegex(ValueError, 'outside marked Impact areas'):
            validate_impact_inventory(candidate, allowed)

    def test_v2_inventory_requires_verbatim_impact_evidence(self):
        text = '## Impact\nUsers may lose funds if the oracle is stale.\n'
        catalog = build_catalog(text)
        allowed = explicit_impact_evidence_ids(catalog, text)
        evidence_id = allowed[0]
        candidate = {
            'schema_version': 'report-impact-inventory/2',
            'impacts': [{'id': 'fund_loss',
                         'text': 'Users may lose funds if the oracle is stale.',
                         'modality': 'potential',
                         'evidence_ids': [evidence_id]}],
            'ambiguities': [],
        }
        self.assertEqual(validate_impact_inventory(
            candidate, allowed, catalog), candidate)
        changed_word = {**candidate, 'impacts': [{
            **candidate['impacts'][0],
            'text': 'Fund Lock: The campaign is created, and funds moved to the Distributor contract.'}]}
        with self.assertRaisesRegex(ValueError, 'verbatim'):
            validate_impact_inventory(changed_word, allowed, catalog)

        paraphrase = {**candidate, 'impacts': [{
            **candidate['impacts'][0], 'text': 'Users lose funds.'}]}
        with self.assertRaisesRegex(ValueError, 'verbatim'):
            validate_impact_inventory(paraphrase, allowed, catalog)

        inferred = {**candidate, 'impacts': [{
            **candidate['impacts'][0], 'modality': 'inferred'}]}
        with self.assertRaisesRegex(ValueError, 'modality'):
            validate_impact_inventory(inferred, allowed, catalog)

    def test_v2_quote_check_ignores_only_common_markdown_presentation(self):
        text = ('## Impact\n1.  **Fund Lock:** The campaign is created, and '
                'funds move to the `Distributor` contract.\n')
        catalog = build_catalog(text)
        allowed = explicit_impact_evidence_ids(catalog, text)
        candidate = {
            'schema_version': 'report-impact-inventory/2',
            'impacts': [{'id': 'fund_lock',
                         'text': 'Fund Lock: The campaign is created, and funds move to the Distributor contract.',
                         'modality': 'asserted', 'evidence_ids': allowed}],
            'ambiguities': [],
        }
        self.assertEqual(validate_impact_inventory(
            candidate, allowed, catalog), candidate)

    def test_inventory_allows_more_than_four_explicit_impacts(self):
        text = ('## Impact\n- First: funds are locked.\n- Second: swaps fail.\n'
                '- Third: users pay a fee.\n- Fourth: orders are cancelled.\n'
                '- Fifth: the market collapses.\n')
        catalog = build_catalog(text)
        allowed = explicit_impact_evidence_ids(catalog, text)
        candidates = []
        for index, outcome in enumerate((
                'funds are locked', 'swaps fail', 'users pay a fee',
                'orders are cancelled', 'the market collapses'), 1):
            evidence_id = next(row['id'] for row in catalog['fragments']
                               if outcome in row['text'])
            candidates.append({
                'id': f'explicit_harm_{index}',
                'text': f'{index}. {outcome}.',
                'modality': 'asserted',
                'evidence_ids': [evidence_id],
            })
        candidate = {'schema_version': 'report-impact-inventory/2',
                     'impacts': candidates, 'ambiguities': []}
        self.assertEqual(len(validate_impact_inventory(
            candidate, allowed, catalog)['impacts']), 5)

    def test_v1_inventory_remains_replay_compatible(self):
        candidate = {
            'schema_version': 'report-impact-inventory/1',
            'impacts': [{'id': 'fund_loss', 'text': 'Users may lose funds.',
                         'modality': 'inferred', 'evidence_ids': ['impact_evidence']}],
            'ambiguities': [],
        }
        self.assertEqual(validate_impact_inventory(
            candidate, ['impact_evidence']), candidate)

    def test_merge_uses_only_separately_validated_impacts(self):
        elements, _ = id_inputs()
        original_impact_ids = {row['id'] for row in elements['statements']
                               if row['kind'] == 'impact'}
        allowed = ['impact_evidence']
        inventory = {
            'schema_version': 'report-impact-inventory/1',
            'impacts': [{'id': 'explicit_loss', 'text': 'Users lose funds.',
                         'modality': 'potential', 'evidence_ids': allowed}],
            'ambiguities': [],
        }
        merged = merge_impact_inventory(elements, inventory)
        impacts = [row for row in merged['statements'] if row['kind'] == 'impact']
        self.assertEqual([row['id'] for row in impacts], ['explicit_loss'])
        self.assertEqual(impacts[0]['evidence_ids'], allowed)
        self.assertEqual(original_impact_ids - {row['id'] for row in impacts},
                         original_impact_ids)


if __name__ == '__main__':
    unittest.main()
