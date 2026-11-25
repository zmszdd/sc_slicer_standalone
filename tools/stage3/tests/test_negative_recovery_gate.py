#!/usr/bin/env python3
import json
import sys
import tempfile
import unittest
from pathlib import Path

STAGE3 = Path(__file__).resolve().parents[1]
if str(STAGE3) not in sys.path:
    sys.path.insert(0, str(STAGE3))

from evaluation.metrics import negative_recovery_gate as gate  # noqa: E402
from lib import artifact_fingerprint, mainline_protocol  # noqa: E402


class NegativeRecoveryGateTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.sample = self.root / 'sample.json'
        self.goldset = self.root / 'goldset'
        self.negative_goldset = self.goldset / 'mainline_goldset_1_7_31_neg'
        self.negative_goldset.mkdir(parents=True)
        self.runs = self.root / 'runs'
        self.runs.mkdir()
        self.candidate_root = self.root / 'candidate'
        self.candidate_root.mkdir()
        self.case = 'Project__finding__submission'
        self.sample.write_text(json.dumps({
            'schema_version': 'mainline-sample/1',
            'positive_cases': [],
            'negative_cases': [self.case],
        }), encoding='utf-8')

    def tearDown(self):
        self.temp.cleanup()

    def _write_stage2(self, root: Path, claim_id: str, *, fallback: bool):
        case_dir = root / self.case
        case_dir.mkdir(parents=True, exist_ok=True)
        (case_dir / 'stage3-spec.json').write_text(json.dumps({
            'schema_version': 'stage3-semantic-spec/1',
            'claims': [{'claim_id': claim_id}],
        }), encoding='utf-8')
        for name in ('constraints.json', 'formalization.json'):
            (case_dir / name).write_text('{}', encoding='utf-8')
        protocol = mainline_protocol.current()
        (case_dir / 'provenance.json').write_text(json.dumps({
            'prompt_version': protocol['stage2_prompt_version'],
            'model_provider': protocol['stage2_provider'],
            'model_name': protocol['stage2_model'],
            'continue_on_review': fallback,
        }), encoding='utf-8')
        binding = case_dir / 'binding.json'
        binding.write_text('{}', encoding='utf-8')
        return case_dir, binding

    def _write_baseline(self):
        run_dir = self.negative_goldset / 'runs_01' / self.case
        self._write_stage2(run_dir.parent, 'old_claim', fallback=False)
        case_dir = run_dir.parent / self.case
        run_dir = case_dir

    def _write_candidate(self, verdict: str) -> Path:
        return self._write_candidate_with_eligibility(
            verdict, consistency=True)

    def _write_candidate_with_eligibility(
            self, verdict: str, *, consistency: bool,
            negative_witness: bool = True) -> Path:
        case_dir, binding = self._write_stage2(
            self.candidate_root, 'new_claim', fallback=True)
        summary_dir = self.runs / f'{self.case}__new_claim__20261124T000000Z'
        summary_dir.mkdir(parents=True)
        summary = {
            'schema_version': 'stage3-run-summary/1',
            'case': str(case_dir),
            'claim_id': 'new_claim',
            'consistency_verdict': verdict,
            'artifact_fingerprint': artifact_fingerprint.build(case_dir, binding),
            'execution_gate': {'metric_eligibility': {
                'consistency': consistency,
                'vulnerability': False,
            }, 'negative_witness': {'eligible': negative_witness}},
        }
        (summary_dir / 'stage3-summary.json').write_text(
            json.dumps(summary), encoding='utf-8')
        return case_dir

    def test_promotes_only_when_new_eligible_negative_exists(self):
        self._write_baseline()
        self._write_candidate('effect_observed_invariant_holds')

        report = gate.evaluate(self.sample, self.negative_goldset, self.runs,
                               self.candidate_root)

        self.assertTrue(report['promote_allowed'])
        self.assertEqual(report['baseline']['eligible_negative'], 0)
        self.assertEqual(report['candidate']['eligible_negative'], 1)
        self.assertEqual(report['new_eligible_negative'], [self.case])
        self.assertEqual(report['candidates'][0]['claims'], 1)

    def test_rejects_when_stage3_stays_unresolved(self):
        self._write_baseline()
        self._write_candidate('partial_binding')

        report = gate.evaluate(self.sample, self.negative_goldset, self.runs,
                               self.candidate_root)

        self.assertFalse(report['promote_allowed'])
        self.assertEqual(report['new_eligible_negative'], [])

    def test_rejects_claim_level_eligible_without_metric_eligibility(self):
        self._write_baseline()
        self._write_candidate_with_eligibility(
            'effect_observed_invariant_holds', consistency=False,
            negative_witness=False)

        report = gate.evaluate(self.sample, self.negative_goldset, self.runs,
                               self.candidate_root)

        self.assertFalse(report['promote_allowed'])
        self.assertEqual(report['candidate']['eligible_negative'], 0)
        self.assertEqual(report['new_eligible_negative'], [])


if __name__ == '__main__':
    unittest.main()
