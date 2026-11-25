import json
import hashlib
import sys
import tempfile
import unittest
from unittest import mock
from unittest import mock
from pathlib import Path

METRICS = Path(__file__).resolve().parents[1] / 'evaluation' / 'metrics'
STAGE3 = METRICS.parents[1]
sys.path.insert(0, str(METRICS))
from sample_mainline import _alloc_capped, frozen_dev_case_ids  # noqa: E402
from sample_mainline import main as sample_main  # noqa: E402
from build_official_negative_pool import build as build_pool  # noqa: E402
from build_official_negative_pool import latest_validity  # noqa: E402
import mainline_metrics  # noqa: E402
sys.path.insert(0, str(STAGE3))
from lib import artifact_fingerprint  # noqa: E402


class MainlineSampleTest(unittest.TestCase):
    def test_negative_allocation_respects_project_cap_and_reports_shortfall(self):
        alloc, shortfall = _alloc_capped(
            {'ProjA': 40, 'ProjB': 20, 'ProjC': 10}, 60)
        self.assertEqual(sum(alloc.values()) + shortfall, 60)
        self.assertLessEqual(max(alloc.values()), 15)

    def test_sample_size_and_negative_enumeration(self):
        sample = json.loads((METRICS / 'mainline_sample.json').read_text())
        self.assertEqual(sample['selected_positives'], 350)
        self.assertEqual(len(sample['positive_cases']), 350)
        self.assertEqual(len(set(sample['positive_cases'])), 350)
        self.assertEqual(sample['negative_count'],
                         len(sample['negative_cases']))
        self.assertEqual(len(sample['negative_cases']),
                         len(set(sample['negative_cases'])))

    def test_sample_cases_are_all_judge_ground_truth_rows(self):
        gt = json.loads((METRICS / 'judge_ground_truth.json').read_text())
        known = {c['case'] for c in gt['cases']}
        pool = json.loads((METRICS / 'official_negative_pool_20261121.json').read_text())
        negatives = set(pool['selected_cases'])
        sample = json.loads((METRICS / 'mainline_sample.json').read_text())
        self.assertTrue(set(sample['positive_cases']) <= known)
        self.assertEqual(set(sample['negative_cases']), negatives)
        self.assertFalse(set(sample['negative_cases']) & known)

    def test_official_pool_provenance_is_recorded(self):
        pool_path = METRICS / 'official_negative_pool_20261121.json'
        sample = json.loads((METRICS / 'mainline_sample.json').read_text())
        self.assertTrue(sample['negative_source'].endswith(pool_path.name))
        self.assertEqual(
            sample['negative_source_sha256'],
            hashlib.sha256(pool_path.read_bytes()).hexdigest())
        self.assertEqual(sample['selected_negatives'], 60)
        self.assertEqual(sample['negative_shortfall'], 0)
        self.assertEqual(sample['negative_population'], 165)
        self.assertEqual(len(set(sample['negative_cases'])), 60)

    def test_latest_official_validity_evaluation_wins(self):
        row = {'raw': {'evaluations': [
            {'type': 'validity', 'value': 'valid', 'findingUid': 'f1',
             'createdAt': '2025-12-01T00:00:00.000Z'},
            {'type': 'quality', 'value': 'sufficient', 'findingUid': 'f1',
             'createdAt': '2025-12-02T00:00:00.000Z'},
            {'type': 'validity', 'value': 'invalid', 'findingUid': 'f1',
             'createdAt': '2025-12-03T00:00:00.000Z'},
        ]}}
        self.assertEqual(latest_validity(row), 'invalid')

    def test_official_pool_excludes_ground_truth_and_dev_cases(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            findings = root / 'findings' / 'ProjA_abc' / '20260101_000000'
            findings.mkdir(parents=True)
            rows = []
            for index, (finding, final) in enumerate((
                    ('f1', 'invalid'), ('f2', 'invalid'), ('f3', 'invalid')), 1):
                rows.append({
                    'uid': f's{index}', 'submission_index': str(index),
                    'title': f'finding {index}', 'severity': 'high',
                    'raw': {'evaluations': [
                        {'type': 'validity', 'findingUid': finding,
                         'value': final, 'createdAt': '2026-01-01T00:00:00.000Z'},
                    ]},
                })
            (findings / 'findings.json').write_text(json.dumps(rows))
            (findings / 'reports').mkdir()
            (findings / 'flatten_sorted').mkdir()
            ground_truth = root / 'gt.json'
            ground_truth.write_text(json.dumps({'cases': [
                {'case': 'ProjA_abc__f1__s1', 'project': 'ProjA_abc',
                 'validity': 'invalid'}]}))
            dev_case = 'ProjA_abc__f2__s2'
            with mock.patch('sample_mainline.frozen_dev_case_ids',
                            return_value={dev_case}):
                pool = build_pool(target=2, max_share=1.0, seed=7,
                             findings_root=root / 'findings',
                             ground_truth=ground_truth)
            self.assertEqual(pool['label_agreement'],
                             {'matched_ground_truth_rows': 1, 'agreements': 1})
            self.assertEqual(pool['counts']['candidates_outside_dev'], 1)
            self.assertEqual(pool['selected_cases'], ['ProjA_abc__f3__s3'])

    def test_sampler_consumes_official_negative_pool(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ground_truth = root / 'gt.json'
            ground_truth.write_text(json.dumps({'cases': [
                {'case': f'Proj{i}__p{i}__s{i}', 'project': f'Proj{i}',
                 'validity': 'valid'} for i in range(5)]}))
            selected = [
                {'case': f'Neg{i}__f{i}__s{i}', 'project': f'Neg{i}',
                 'validity': 'invalid', 'submission_number': str(i)}
                for i in range(3)]
            pool_path = root / 'pool.json'
            pool_path.write_text(json.dumps({
                'schema_version': 'official-negative-pool/1',
                'selected_cases': [row['case'] for row in selected],
                'selected': selected, 'candidates': selected,
                'label_rule': 'latest validity evaluation for the same finding uid',
                'policy': 'test pool',
                'label_agreement': {'matched_ground_truth_rows': 1,
                                    'agreements': 1},
            }))
            output = root / 'sample.json'
            markdown = root / 'sample.md'
            sample_main([
                '--ground-truth', str(ground_truth),
                '--exclude-dev', str(root / 'missing.json'),
                '--target-positives', '5', '--target-negatives', '3',
                '--official-negative-pool', str(pool_path),
                '--output', str(output), '--markdown', str(markdown),
            ])
            sample = json.loads(output.read_text())
            self.assertEqual(set(sample['negative_cases']),
                             {row['case'] for row in selected})
            self.assertEqual(sample['negative_label_rule'],
                             'latest validity evaluation for the same finding uid')
            self.assertEqual(
                sample['negative_source_sha256'],
                hashlib.sha256(pool_path.read_bytes()).hexdigest())

    def test_sample_covers_every_project_with_positives_outside_dev(self):
        gt = json.loads((METRICS / 'judge_ground_truth.json').read_text())
        dev_cases = frozen_dev_case_ids()
        positives = {c['case']: c['project'] for c in gt['cases']
                     if c.get('validity') in {'valid', 'fixed', 'wontfix'}
                     and c['case'] not in dev_cases}
        sample = json.loads((METRICS / 'mainline_sample.json').read_text())
        projects = {positives[c] for c in sample['positive_cases']}
        self.assertEqual(projects, {p for p in positives.values()})
        self.assertFalse(set(sample['positive_cases']) & dev_cases)

    def test_sample_is_disjoint_from_all_frozen_dev_cases(self):
        sample = json.loads((METRICS / 'mainline_sample.json').read_text())
        dev_cases = frozen_dev_case_ids()
        self.assertFalse(set(sample['positive_cases']) & dev_cases)
        self.assertFalse(set(sample['negative_cases']) & dev_cases)

    def test_mainline_metrics_confusion_matrix_is_consistent(self):
        data = json.loads((METRICS / 'mainline_metrics.json').read_text())
        cm = data['confusion_matrix']
        cov = data['coverage']
        self.assertEqual(cm['tp'] + cm['fn'], cm['positives_evaluated'])
        self.assertEqual(cm['tp_consistency'] + cm['fn_consistency'],
                         cm['positives_evaluated'])
        self.assertEqual(cm['tp'] + cm['fn'] + cm['unevaluated_positives'],
                         data['sample']['positives'])
        self.assertLessEqual(cm['fp_raw'] + cm['tn'], cm['negatives_evaluated'])
        self.assertTrue(data['metrics']['recall'] is None
                        or 0 <= data['metrics']['recall'] <= 1)
        self.assertTrue(0 <= data['metrics']['recall_sample_wide'] <= 1)
        headline = data['headline_metrics']
        self.assertEqual(headline['recall_conservative'],
                         data['metrics']['recall_sample_wide'])
        self.assertEqual(headline['recall_evaluated'], data['metrics']['recall'])
        self.assertEqual(headline['precision_vuln'],
                         data['metrics']['precision_vuln'])
        for key in ('accuracy', 'accuracy_consistency', 'recall_consistency'):
            value = data['metrics'][key]
            self.assertTrue(value is None or 0 <= value <= 1, key)
        for key in ('recall_cluster_bootstrap',
                    'precision_vuln_cluster_bootstrap'):
            ci = data['confidence_intervals'][key]
            if ci['low'] is None or ci['high'] is None:
                self.assertEqual(ci['low'], ci['high'])
            else:
                self.assertLessEqual(ci['low'], ci['high'])
        self.assertIn('refresh_gate', data)
        consistency_gate = data['consistency_gate']
        self.assertEqual(consistency_gate['negative_floor'], 24)
        self.assertFalse(consistency_gate['publishable'])
        self.assertGreater(
            mainline_metrics.consistency_fpr_upper_95(1, 8),
            consistency_gate['publication_max_fpr_upper95'])
        self.assertLess(
            mainline_metrics.consistency_fpr_upper_95(1, 24),
            consistency_gate['publication_max_fpr_upper95'])
        self.assertEqual(
            cov['positives_evaluated'] + cov['positives_explicit_failure']
            + cov['positives_not_attributable'], data['sample']['positives'])
        denominator = (cov['positives_evaluated']
                       + cov['positives_explicit_failure'])
        expected_completion = (cov['positives_evaluated'] / denominator
                               if denominator else None)
        if expected_completion is None:
            self.assertIsNone(data['metrics']['completion_rate'])
        else:
            self.assertAlmostEqual(data['metrics']['completion_rate'],
                                   expected_completion, places=4)
        expected_wide = (cov['positives_evaluated'] / data['sample']['positives']
                         if data['sample']['positives'] else None)
        if expected_wide is None:
            self.assertIsNone(data['metrics']['completion_sample_wide'])
        else:
            self.assertAlmostEqual(data['metrics']['completion_sample_wide'],
                                   expected_wide, places=4)

    def test_consistency_tp_uses_independent_effect_witness_not_invariant(self):
        summary = {
            'consistency_verdict': 'effect_observed_invariant_holds',
            'code_query_results': {
                'P_and_T': 'sat', 'P_and_T_and_not_I': 'unsat',
                'P_and_T_and_V': 'sat', 'P_and_T_and_not_V': 'unknown',
            },
            'forge': {'effect': {'status': 'Success'}},
        }
        self.assertTrue(mainline_metrics.consistency_effect_confirmed(summary))
        data = json.loads((METRICS / 'mainline_metrics.json').read_text())
        cm = data['confusion_matrix']
        self.assertGreaterEqual(cm['tp_consistency'], cm['tp'])


class MainlineEligibilityTest(unittest.TestCase):
    def test_unresolved_and_stale_runs_are_not_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            stage2 = Path(tmp)
            for name in ('stage3-spec.json', 'constraints.json',
                         'formalization.json'):
                (stage2 / name).write_text('{}')
            fingerprint = artifact_fingerprint.build(stage2)

        unresolved = {
            'claim_id': 'claim-1',
            'consistency_verdict': 'binding_error',
            'artifact_fingerprint': fingerprint,
        }
        stale = {
            'claim_id': 'claim-2',
            'consistency_verdict': 'violation_reproduced',
        }
        eligible = {
            'claim_id': 'claim-3',
            'consistency_verdict': 'violation_reproduced',
            'artifact_fingerprint': fingerprint,
            'forge': {'exploit': {
                'original': {'status': 'Success'},
                'patched': {'status': 'Failure'},
            }},
            'execution_gate': {'metric_eligibility': {
                'consistency': True, 'vulnerability': True,
            }},
        }

        class Index:
            def __init__(self, rows):
                self.rows = rows

            def iter_auto(self, case, claim_id=None):
                return self.rows

            def iter_refpatch(self, case):
                return []

        self.assertEqual(mainline_metrics._case_evidence(
            Index([unresolved, stale]), 'case', [], 'negative'), [])
        rows = mainline_metrics._case_evidence(
            Index([eligible]), 'case', [], 'negative')
        self.assertEqual(len(rows), 1)
        self.assertTrue(rows[0]['reproduced'])

        revert = {
            'claim_id': 'claim-4',
            'consistency_verdict': 'effect_not_witnessed',
            'artifact_fingerprint': fingerprint,
            'execution_gate': {'metric_eligibility': {
                'consistency': True, 'vulnerability': False,
            }},
        }
        with mock.patch.object(
                mainline_metrics.revert_witness, 'evaluate',
                return_value={'eligible': True, 'reason': 'test'}):
            rows = mainline_metrics._case_evidence(
                Index([revert]), 'case', [], 'positive')
        self.assertEqual(len(rows), 1)
        self.assertFalse(rows[0]['reproduced'])
        self.assertIsNone(rows[0]['reproduction_basis'])


if __name__ == '__main__':
    unittest.main()
