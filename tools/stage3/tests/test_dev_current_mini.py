import json
import sys
import tempfile
import unittest
from pathlib import Path

STAGE3 = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(STAGE3))
sys.path.insert(0, str(STAGE3 / 'evaluation' / 'metrics'))

from build_dev_current_mini import build  # noqa: E402
from dev_current_metrics import build as build_metrics  # noqa: E402


class DevCurrentMiniTest(unittest.TestCase):
    def test_manifest_is_stratified_and_excludes_dev24(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            frozen = root / 'frozen'
            metrics = root / 'metrics'
            cases_root = root / 'tools' / 'stage3' / 'cases'
            frozen.mkdir(parents=True)
            metrics.mkdir(parents=True)

            def add_case(case_id):
                case_dir = cases_root / case_id
                (case_dir / 'stage2_run').mkdir(parents=True)
                (case_dir / 'bindings').mkdir()

            positives = [
                f'ProjA__p{i}__x' for i in range(4)
            ] + [f'ProjB__p{i}__x' for i in range(4)]
            for case_id in positives:
                add_case(case_id)
            dev252 = frozen / 'dev252.json'
            dev252.write_text(json.dumps({'case_list': {'cases': [
                {'case_id': case_id, 'label': 'tp'} for case_id in positives]}}))
            dev24 = frozen / 'dev24.json'
            dev24.write_text(json.dumps({'cases': [
                {'case_id': positives[0]}]}))

            negatives = [f'ProjC__n{i}__x' for i in range(4)]
            for case_id in negatives:
                add_case(case_id)
            negative_file = metrics / 'negative.json'
            negative_file.write_text(json.dumps({'cases': [
                {'case': case_id, 'status': 'done'} for case_id in negatives]}))

            manifest = build(dev252_path=dev252, dev24_path=dev24,
                             negative_paths=(negative_file,), root=root,
                             positives=4, negatives=2, seed=7)
            ids = [row['case_id'] for row in manifest['cases']]
            self.assertNotIn(positives[0], ids)
            self.assertEqual(sum(row['label'] == 'positive'
                                 for row in manifest['cases']), 4)
            self.assertEqual(sum(row['label'] == 'negative'
                                 for row in manifest['cases']), 2)

    def test_metrics_use_resolved_only_matrix(self):
        results = {'results': [
            {'label': 'positive', 'classification': {'outcome': 'tp'}},
            {'label': 'positive', 'classification': {'outcome': 'fn'}},
            {'label': 'positive', 'classification': {'outcome': 'fn_unresolved'}},
            {'label': 'negative', 'classification': {'outcome': 'tn'}},
            {'label': 'negative', 'classification': {'outcome': 'fp'}},
            {'label': 'negative', 'classification': {'outcome': 'unresolved'}},
        ]}
        report = build_metrics(results)
        self.assertEqual(report['confusion_matrix']['tp'], 1)
        self.assertEqual(report['confusion_matrix']['fn'], 1)
        self.assertEqual(report['metrics']['recall'], 0.5)
        self.assertEqual(report['metrics']['precision_vuln'], 0.5)
        self.assertFalse(report['reportable'])

    def test_full_sample_counts_unevaluated_positives_as_fn(self):
        results = {'results': [
            {'label': 'positive', 'classification': {'outcome': 'tp'}},
            {'label': 'positive', 'classification': {'outcome': 'tp'}},
            {'label': 'positive', 'classification': {'outcome': 'fn'}},
            {'label': 'positive', 'classification': {'outcome': 'fn_unresolved'}},
            {'label': 'negative', 'classification': {'outcome': 'tn'}},
            {'label': 'negative', 'classification': {'outcome': 'fp'}},
            {'label': 'negative', 'classification': {'outcome': 'unresolved'}},
        ]}
        report = build_metrics(results, resolved_only=False)
        self.assertEqual(report['metric_mode'], 'full_sample')
        self.assertEqual(report['confusion_matrix']['fn'], 2)
        self.assertEqual(report['confusion_matrix']['fn_resolved'], 1)
        self.assertEqual(report['confusion_matrix']['fn_unresolved'], 1)
        self.assertEqual(report['metrics']['recall'], 0.5)
        self.assertEqual(report['metrics']['precision_vuln'], round(2 / 3, 4))
        self.assertEqual(report['metrics']['accuracy'], round(3 / 7, 4))
        self.assertEqual(report['coverage']['completion_rate'], round(5 / 7, 4))
        self.assertFalse(report['reportable'])


if __name__ == '__main__':
    unittest.main()
