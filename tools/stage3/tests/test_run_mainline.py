import json
import subprocess
import tempfile
import unittest
from collections import Counter
from pathlib import Path

from evaluation.metrics import run_mainline as rm


class ParseClaimsPayloadTest(unittest.TestCase):
    def test_stage2_batch_passes_frozen_prompt_version(self):
        with __import__('tempfile').TemporaryDirectory() as tmp:
            captured = {}

            def fake_run(argv, **kwargs):
                captured['argv'] = argv
                return subprocess.CompletedProcess(argv, 0, stdout='', stderr='')

            orig = rm.subprocess.run
            rm.subprocess.run = fake_run
            try:
                rm._run_stage2_batch(['case_a'], Path(tmp), Path(tmp) / 'out',
                                     'opencode_api', 'model-x')
            finally:
                rm.subprocess.run = orig
            self.assertIn('--prompt-version', captured['argv'])
            self.assertEqual(
                captured['argv'][captured['argv'].index('--prompt-version') + 1],
                rm.mainline_protocol.STAGE2_PROMPT_VERSION)

    def test_picks_aggregate_from_multiline_stream(self):
        stdout = '\n'.join([
            json.dumps({'claim_id': 'c1', 'status': 'accepted',
                        'verdict': 'violation_reproduced'}),
            json.dumps({'claim_id': 'c2', 'status': 'accepted',
                        'verdict': 'violation_not_reproduced'}),
            json.dumps({'schema_version': 'stage3-verdict-loop/1',
                        'claims': [
                            {'claim_id': 'c1', 'verdict': 'violation_reproduced'},
                            {'claim_id': 'c2', 'verdict': 'violation_not_reproduced'},
                        ]}),
        ])
        payload = rm._parse_claims_payload(stdout)
        self.assertIsNotNone(payload)
        self.assertEqual([r['claim_id'] for r in payload['claims']],
                         ['c1', 'c2'])

    def test_ignores_noise_and_invalid_lines(self):
        stdout = 'noise line\n' + json.dumps({'claims': [{'claim_id': 'x',
                                                          'verdict': 'compile_error'}]}) + '\n'
        payload = rm._parse_claims_payload(stdout)
        self.assertEqual(payload['claims'][0]['verdict'], 'compile_error')

    def test_no_payload_returns_none(self):
        self.assertIsNone(rm._parse_claims_payload('just text\n'))


class RecountVerdictsTest(unittest.TestCase):
    def test_recounts_all_terminal_buckets(self):
        row = {'verdicts': [
            'violation_reproduced', 'compile_blocked', 'compile_error',
            'not_dynamically_expressible', 'reference_patch_required',
            'halt_witness_required', 'violation_reproduced',
            'violation_reproduced',
        ]}
        rm._recount_verdicts(row)
        self.assertEqual(row['reproduced'], 3)
        self.assertEqual(row['compile_blocked'], 1)
        self.assertEqual(row['compile_error'], 1)
        self.assertEqual(row['not_dynamically_expressible'], 1)
        self.assertEqual(row['reference_patch_required'], 1)
        self.assertEqual(row['halt_witness_required'], 1)
        self.assertEqual(row['automatic_reproduced'], 3)


class RecoverFixableTest(unittest.TestCase):
    def test_recovers_claims_and_recounts(self):
        case = 'case_a'
        with __import__('tempfile').TemporaryDirectory() as tmp:
            cases_root = Path(tmp) / 'cases'
            case_dir = cases_root / case
            (case_dir / 'stage2_run').mkdir(parents=True)
            row = {
                'case': case,
                'status': 'done',
                'claim_ids': ['c1', 'c2', 'c3'],
                'verdicts': ['partial_binding', 'violation_reproduced',
                             'compile_error'],
                'reproduced': 1,
            }

            def fake_run(argv, **kwargs):
                stdout = '\n'.join([
                    json.dumps({'claim_id': 'c1', 'status': 'accepted',
                                'verdict': 'violation_reproduced'}),
                    json.dumps({'claims': [
                        {'claim_id': 'c1', 'verdict': 'violation_reproduced'},
                        {'claim_id': 'c3', 'verdict': 'violation_reproduced'},
                    ]}),
                ])
                return subprocess.CompletedProcess(argv, 0, stdout=stdout, stderr='')

            orig = rm.subprocess.run
            rm.subprocess.run = fake_run
            try:
                updated = rm._recover_fixable(case, row, cases_root)
            finally:
                rm.subprocess.run = orig

            self.assertEqual(updated['verdicts'],
                             ['violation_reproduced', 'violation_reproduced',
                              'violation_reproduced'])
            self.assertEqual(updated['reproduced'], 3)
            self.assertEqual(updated['compile_error'], 0)

    def test_non_done_row_is_untouched(self):
        with __import__('tempfile').TemporaryDirectory() as tmp:
            cases_root = Path(tmp) / 'cases'
            row = {'status': 'error', 'claim_ids': ['c1'],
                   'verdicts': ['partial_binding']}
            result = rm._recover_fixable('case_a', row, cases_root)
            self.assertIs(result, row)


class NegativeExecutionTest(unittest.TestCase):
    def _write_stage2(self, root: Path, case: str, claims: list[str]) -> Path:
        case_dir = root / case
        case_dir.mkdir(parents=True)
        (case_dir / 'stage3-spec.json').write_text(json.dumps({
            'claims': [
                {'claim_id': claim_id,
                 'formalization_status': 'formalized_candidate'}
                for claim_id in claims
            ],
        }), encoding='utf-8')
        (case_dir / 'constraints.json').write_text('{}', encoding='utf-8')
        (case_dir / 'formalization.json').write_text(json.dumps({
            'claims': [{'id': claim_id} for claim_id in claims],
        }), encoding='utf-8')
        return case_dir

    def test_negative_plan_separates_slice_stage2_and_ready_cases(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            flatten = root / 'flatten'
            goldset = root / 'goldset'
            source = root / 'stage2_source'
            stage2_out = root / 'stage2_out'
            stage2_input = root / 'stage2_input'
            runs = root / 'runs'
            for case in ('ready', 'zero_claim', 'needs_review'):
                case_dir = flatten / case
                case_dir.mkdir(parents=True)
                (case_dir / 'contract.flattened.t.sol').write_text('// x')
            self._write_stage2(goldset / 'runs_01', 'ready', ['c1'])
            zero = self._write_stage2(goldset / 'runs_01', 'zero_claim', [])
            (zero / 'status.json').write_text(json.dumps({
                'impact_source_status': 'marked_section_present',
            }), encoding='utf-8')
            review = source / 'needs_review'
            review.mkdir(parents=True)
            (review / 'status.json').write_text(json.dumps({
                'impact_source_status': 'marked_section_absent',
            }), encoding='utf-8')
            goldset.mkdir(parents=True, exist_ok=True)
            (goldset / 'manifest.json').write_text(json.dumps({
                'source': str(source),
            }), encoding='utf-8')
            for case in ('zero_claim',):
                report = stage2_input / case
                report.mkdir(parents=True)
                (report / 'report.json').write_text('{}')

            rows = rm._negative_plan(
                ['ready', 'zero_claim', 'needs_review', 'no_slice'],
                flatten, goldset, stage2_out, stage2_input, runs)
            reasons = {row['case']: row['reason'] for row in rows}

            self.assertEqual(reasons['ready'], 'stage3_ready')
            self.assertEqual(reasons['zero_claim'], 'zero_claim_stage2')
            self.assertEqual(reasons['needs_review'], 'stage2_needs_impact_review')
            self.assertEqual(reasons['no_slice'], 'no_slice')
            self.assertEqual([row['case'] for row in rows if row['needs_stage2']],
                             ['zero_claim'])

    def test_build_negative_goldset_installs_and_merges_selection(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            goldset = root / 'goldset'
            stage2_out = root / 'stage2_out'
            sample = {'negative_cases': ['new_case', 'old_case']}
            source = self._write_stage2(stage2_out, 'new_case', ['c1'])
            old = self._write_stage2(goldset / 'runs_01', 'old_case', ['c0'])
            (goldset / 'selection.json').write_text(json.dumps({
                'schema_version': 'mainline-goldset/1',
                'cases': [{'case': 'old_case'}],
            }), encoding='utf-8')

            installed = rm._build_negative_goldset(
                sample, ['new_case', 'old_case'], goldset, stage2_out)

            self.assertEqual(installed, ['new_case', 'old_case'])
            self.assertTrue((goldset / 'runs_01' / 'new_case' /
                             'stage3-spec.json').is_file())
            selection = json.loads((goldset / 'selection.json').read_text())
            self.assertEqual([row['case'] for row in selection['cases']],
                             ['new_case', 'old_case'])
            self.assertTrue((old / 'stage3-spec.json').is_file())


if __name__ == '__main__':
    unittest.main()
