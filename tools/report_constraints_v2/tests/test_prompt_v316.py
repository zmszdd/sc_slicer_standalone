"""semantic-v3.16 fixed-template and local-repair regressions; no model calls."""

import copy
import json
from pathlib import Path
import tempfile
import unittest

from prompts.versions import semantic_prompts_v316 as prompts
from lib.plan_synthesizer import synthesize_id_formalization
from cli.semantic_pipeline import request_formalization, validate_local_repair
from tests.test_evidence_ids import id_inputs
from tests.test_plan_synthesizer import plan


def fixed_plan():
    candidate = plan()
    candidate['schema_version'] = 'report-formal-plan/4'
    candidate['relation_class'] = 'progress_or_liveness'
    candidate['derived_definitions'] = []
    candidate['pattern'] = {
        'kind': 'relation_obligation',
        'condition': {
            'kind': 'comparison', 'left': 'paid_fee', 'operator': 'gt',
            'right': {'symbol': 'required_fee'},
        },
        'relation': {'kind': 'truth', 'symbol': 'fee_revert', 'value': False},
    }
    return candidate


class PromptV316Tests(unittest.TestCase):
    def test_prompt_uses_v4_fixed_templates_and_derived_definitions(self):
        text = prompts.formal_prompt('ids', 'core')
        self.assertIn('semantic-v3.16', text)
        self.assertIn('report-formal-plan/4', text)
        self.assertIn('The program fixes the logical template', text)
        self.assertIn('every other class MUST use kind relation_obligation', text)
        self.assertIn('derived_definitions', text)
        self.assertIn('Do not select or encode the vulnerable return value', text)
        self.assertIn('Never duplicate a vulnerable result as a precondition',
                      prompts.ID_ELEMENT_PROMPT)

    def test_fixed_template_is_enforced(self):
        elements, _ = id_inputs()
        candidate = fixed_plan()
        candidate['pattern'] = {
            'kind': 'condition_forbids_effect',
            'condition': candidate['pattern']['condition'],
            'effect': {'kind': 'truth', 'symbol': 'fee_revert', 'value': True},
        }
        with self.assertRaisesRegex(ValueError, 'fixed relation template mismatch'):
            synthesize_id_formalization(candidate, elements)

    def test_v4_observable_needs_impact_while_intent_grounds_property(self):
        elements, _ = id_inputs()
        candidate = fixed_plan()
        formal = synthesize_id_formalization(candidate, elements)
        self.assertEqual(formal['schema_version'], 'report-formalization/2')

    def test_derived_symbol_requires_and_compiles_definition(self):
        elements, _ = id_inputs()
        candidate = fixed_plan()
        candidate['symbols']['expected_fee'] = {
            'sort': 'int', 'unit': 'native_wei',
            'meaning': 'Report-grounded expected fee', 'checkpoint': 'derived',
            'entity_ids': ['messenger', 'native_fee'],
            'source_ids': ['pre_overpay', 'intent_accept_buffer', 'impact_revert'],
        }
        candidate['pattern']['relation'] = {
            'kind': 'comparison', 'left': 'paid_fee', 'operator': 'eq',
            'right': {'symbol': 'expected_fee'},
        }
        with self.assertRaisesRegex(ValueError, 'referenced derived symbol lacks definition'):
            synthesize_id_formalization(candidate, elements)
        candidate['derived_definitions'] = [{
            'symbol': 'expected_fee',
            'expression': {'op': 'add', 'args': [
                {'symbol': 'required_fee'}, {'const': 0}]},
            'source_ids': ['pre_overpay', 'intent_accept_buffer'],
        }]
        formal = synthesize_id_formalization(candidate, elements)
        safety = formal['claims'][0]['properties']['safety']['expression']
        effects = formal['claims'][0]['properties']['effects']['expression']
        self.assertEqual(safety['op'], 'implies')
        self.assertEqual(safety['args'][0]['op'], 'eq')
        self.assertEqual(effects['op'], 'and')

    def test_same_unknown_multiplicative_factor_on_both_sides_is_rejected(self):
        elements, _ = id_inputs()
        candidate = fixed_plan()
        candidate['symbols']['duration'] = {
            'sort': 'int', 'unit': 'seconds', 'meaning': 'duration',
            'checkpoint': 'input', 'entity_ids': ['caller'],
            'source_ids': ['pre_overpay'],
        }
        candidate['symbols']['total_duration'] = {
            'sort': 'int', 'unit': 'seconds', 'meaning': 'total duration',
            'checkpoint': 'input', 'entity_ids': ['caller'],
            'source_ids': ['impact_revert'],
        }
        candidate['pattern']['relation'] = {
            'kind': 'relation',
            'left': {'op': 'mul', 'args': [
                {'symbol': 'paid_fee'}, {'symbol': 'duration'}]},
            'operator': 'le',
            'right': {'op': 'mul', 'args': [
                {'symbol': 'paid_fee'}, {'symbol': 'total_duration'}]},
        }
        with self.assertRaisesRegex(ValueError, 'cancellable observable'):
            synthesize_id_formalization(candidate, elements)

    def test_local_repair_freezes_unrelated_semantic_fields(self):
        previous = fixed_plan()
        repaired = copy.deepcopy(previous)
        repaired['pattern']['relation']['value'] = True
        self.assertEqual(validate_local_repair(previous, repaired, ('pattern',)),
                         ['pattern'])
        repaired['relation_class'] = 'state_correspondence'
        with self.assertRaisesRegex(ValueError, 'changed frozen fields'):
            validate_local_repair(previous, repaired, ('pattern',))

    def test_invalid_template_gets_a_field_scoped_retry(self):
        elements, _ = id_inputs()
        good = fixed_plan()
        bad = copy.deepcopy(good)
        bad['pattern'] = {
            'kind': 'condition_forbids_effect',
            'condition': good['pattern']['condition'],
            'effect': {'kind': 'truth', 'symbol': 'fee_revert', 'value': True},
        }
        calls = []

        def fake_extract(payload, folder, _model, _prompt):
            calls.append(json.loads(payload))
            candidate = bad if len(calls) == 1 else good
            (folder / 'model-claim.json').write_text(json.dumps(candidate))
            return copy.deepcopy(candidate)

        with tempfile.TemporaryDirectory() as work:
            root = Path(work)
            _, formal, _ = request_formalization(
                '{}', 'PROMPT', 'model', root, 1, True, elements,
                structured=True, extract_fn=fake_extract, local_repair=True)
            self.assertEqual(formal['schema_version'], 'report-formalization/2')
            self.assertEqual(calls[1]['task'], 'repair_previous_formal_plan_locally')
            self.assertEqual(calls[1]['mutable_top_level_fields'], ['pattern'])
            attempts = json.loads((root / 'formalization-attempts.json').read_text())
            self.assertEqual(attempts[1]['repair_mode'], 'field_scoped')
            self.assertEqual(attempts[1]['changed_top_level_fields'], ['pattern'])

    def test_null_repair_resubmission_gets_exactly_one_extra_reprompt(self):
        """final_holdout_02 (GTE_Perps): the retry resubmitted the plan
        byte-identically on the FINAL attempt, so the no-change prescription
        could never fire -- no next attempt existed.  A null response now
        grants exactly one reprompt, and only one.  blind-batch_07 escalation:
        repeating the identical repair request cannot produce new content, so
        the granted reprompt runs as a full restatement (frozen decisions
        reopened), not another local repair.
        """
        elements, _ = id_inputs()
        good = fixed_plan()
        bad = copy.deepcopy(good)
        bad['pattern'] = {
            'kind': 'condition_forbids_effect',
            'condition': good['pattern']['condition'],
            'effect': {'kind': 'truth', 'symbol': 'fee_revert', 'value': True},
        }
        calls = []

        def fake_extract(payload, folder, _model, _prompt):
            calls.append(json.loads(payload))
            candidate = bad if len(calls) <= 2 else good
            (folder / 'model-claim.json').write_text(json.dumps(candidate))
            return copy.deepcopy(candidate)

        with tempfile.TemporaryDirectory() as work:
            root = Path(work)
            _, formal, _ = request_formalization(
                '{}', 'PROMPT', 'model', root, 1, True, elements,
                structured=True, extract_fn=fake_extract, local_repair=True)
            self.assertEqual(formal['schema_version'], 'report-formalization/2')
            self.assertEqual(len(calls), 3)
            attempts = json.loads((root / 'formalization-attempts.json').read_text())
            self.assertEqual(len(attempts), 3)
            self.assertTrue(attempts[1]['null_repair_reprompt'])
            self.assertEqual(attempts[1]['error'], 'local repair made no change')
            # The reprompt is a full restatement: no repair payload, no
            # frozen-field record for the third attempt.
            self.assertTrue(attempts[2].get('fresh_restate'))
            self.assertNotIn('repair_mode', attempts[2])
            self.assertNotIn('task', calls[2])

    def test_second_null_repair_still_ends_the_run(self):
        """The null-reprompt grant is one-shot: a model that resubmits
        identically twice must not open an infinite repair loop.  The granted
        restatement is a full replan, so the identical resubmission re-fails
        the deterministic gate itself and the run ends on that defect."""
        elements, _ = id_inputs()
        bad = fixed_plan()
        condition = bad['pattern']['condition']
        bad['pattern'] = {
            'kind': 'condition_forbids_effect',
            'condition': condition,
            'effect': {'kind': 'truth', 'symbol': 'fee_revert', 'value': True},
        }
        calls = []

        def fake_extract(payload, folder, _model, _prompt):
            calls.append(json.loads(payload))
            (folder / 'model-claim.json').write_text(json.dumps(bad))
            return copy.deepcopy(bad)

        with tempfile.TemporaryDirectory() as work:
            root = Path(work)
            with self.assertRaisesRegex(ValueError,
                                        'fixed relation template mismatch'):
                request_formalization(
                    '{}', 'PROMPT', 'model', root, 1, True, elements,
                    structured=True, extract_fn=fake_extract, local_repair=True)
            self.assertEqual(len(calls), 3)

    def test_faithfulness_audit_mismatch_routes_into_the_repair_loop(self):
        """S17: a non-consistent cross-audit verdict is a retryable defect --
        it enters the same bounded repair loop as the deterministic gates,
        the retry feedback names the finding, and only an all-consistent
        verdict writes the run-level audit artifact."""
        elements, _ = id_inputs()
        good = fixed_plan()
        plan_calls, audit_calls, audit_prompts = [], [], []

        def fake_plan(payload, folder, _model, _prompt):
            plan_calls.append(json.loads(payload))
            (folder / 'model-claim.json').write_text(json.dumps(good))
            return copy.deepcopy(good)

        def consistent():
            return {'checks': [{'source_id': term['source_id'],
                                'verdict': 'consistent',
                                'reason': 'statement encoded faithfully'}
                               for term in good['precondition_terms']]}

        def fake_audit(payload, folder, _model, prompt_text):
            audit_calls.append(json.loads(payload))
            audit_prompts.append(prompt_text)
            value = (consistent() if len(audit_calls) > 1 else
                     {'checks': [{'source_id': 'pre_overpay', 'verdict': 'inverted',
                                  'reason': 'statement asserts a fee accrues, '
                                            'predicate asserts equality'}]})
            (folder / 'model-claim.json').write_text(json.dumps(value))
            return copy.deepcopy(value)

        with tempfile.TemporaryDirectory() as work:
            root = Path(work)
            _, formal, _ = request_formalization(
                '{}', 'PROMPT', 'model', root, 1, True, elements,
                structured=True, extract_fn=fake_plan,
                faithfulness_audit=fake_audit, faithfulness_audit_model='model')
            self.assertEqual(formal['schema_version'], 'report-formalization/2')
            self.assertEqual(len(plan_calls), 2)
            self.assertEqual(len(audit_calls), 2)
            # The audit sees the narrow per-source payload only.
            self.assertEqual(audit_calls[0]['schema_version'],
                             'faithfulness-audit-input/1')
            self.assertIn('semantic faithfulness auditor', audit_prompts[0])
            attempts = json.loads((root / 'formalization-attempts.json').read_text())
            self.assertEqual(len(attempts), 2)
            first = attempts[0]['semantic_faithfulness_audit']
            self.assertFalse(first['verdict_consistent'])
            self.assertEqual(first['mismatches'][0]['verdict'], 'inverted')
            self.assertEqual(attempts[0]['error'],
                             'semantic faithfulness mismatch: pre_overpay inverted: '
                             'statement asserts a fee accrues, predicate asserts '
                             'equality')
            # The repair feedback names the audit finding.
            sent = (root / 'neural-formalization-retry-1' / 'prompt.txt').read_text()
            self.assertIn('semantic faithfulness mismatch: pre_overpay inverted',
                          sent)
            # Acceptance writes the run-level replay artifact.
            artifact = json.loads(
                (root / 'semantic-faithfulness-audit.json').read_text())
            self.assertEqual(artifact['mismatch_count'], 0)
            self.assertEqual([row['verdict'] for row in artifact['checks']],
                             ['consistent'])

    def test_null_repair_keeps_the_original_defect_in_the_next_payload(self):
        """blind-batch_02 (Kinetiq): after a byte-identical resubmission the
        repair_error was overwritten by "local repair made no change", so the
        next repair request named NO defect for the model to answer -- only
        the circular instruction to change something.  The substantive
        defect must survive null repairs.  With the blind-batch_07 escalation
        the granted reprompt is a full restatement, so the defect travels in
        the retry feedback appended to the prompt, not in a repair payload."""
        elements, _ = id_inputs()
        bad = fixed_plan()
        condition = bad['pattern']['condition']
        bad['pattern'] = {
            'kind': 'condition_forbids_effect',
            'condition': condition,
            'effect': {'kind': 'truth', 'symbol': 'fee_revert', 'value': True},
        }
        calls = []
        prompts = []

        def fake_extract(payload, folder, _model, prompt_text):
            calls.append(json.loads(payload))
            prompts.append(prompt_text)
            (folder / 'model-claim.json').write_text(json.dumps(bad))
            return copy.deepcopy(bad)

        with tempfile.TemporaryDirectory() as work:
            root = Path(work)
            with self.assertRaisesRegex(ValueError,
                                        'fixed relation template mismatch'):
                request_formalization(
                    '{}', 'PROMPT', 'model', root, 1, True, elements,
                    structured=True, extract_fn=fake_extract, local_repair=True)
            self.assertEqual(len(calls), 3)
            self.assertEqual(calls[1]['repair_error'],
                             'fixed relation template mismatch')
            self.assertNotIn('task', calls[2])
            self.assertIn('fixed relation template mismatch', prompts[2])
            self.assertIn('Restate the complete plan', prompts[2])


if __name__ == '__main__':
    unittest.main()
