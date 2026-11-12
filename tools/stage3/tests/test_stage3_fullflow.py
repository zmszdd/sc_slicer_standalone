import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from cli.stage3_fullflow import (BLIND_INVALID_EVALS, METRICS_DIR,
                                 compose_report, select_negative_targets,
                                 _judge_anchor_args, _run_script)


class SelectNegativeTargetsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.cases = Path(self.tmp.name) / 'cases'
        self.cases.mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def _positive(self, case, verdicts, bound_ids):
        return {'cases': [{
            'case': case,
            'status': 'done',
            'reproduced': int(verdicts.count('violation_reproduced') > 0),
            'verdicts': verdicts,
            'bound_claim_ids': bound_ids,
        }]}

    def test_picks_reproduced_claim_with_binding(self):
        case = 'Demo__a__b'
        claim = 'impact_claim_x'
        (self.cases / case / 'bindings').mkdir(parents=True)
        (self.cases / case / 'bindings' / f'{claim}.json').write_text('{}')
        positive = self._positive(case, ['violation_reproduced'], [claim])
        targets = select_negative_targets(positive, self.cases)
        self.assertEqual(len(targets), 1)
        self.assertEqual(targets[0]['case'], case)
        self.assertEqual(targets[0]['claim_id'], claim)

    def test_skips_not_reproduced(self):
        positive = self._positive('Demo__a__b', ['violation_not_reproduced'],
                                  ['impact_claim_x'])
        self.assertEqual(select_negative_targets(positive, self.cases), [])

    def test_skips_missing_binding(self):
        positive = self._positive('Demo__a__b', ['violation_reproduced'],
                                  ['impact_claim_x'])
        self.assertEqual(select_negative_targets(positive, self.cases), [])

    def test_max_negatives(self):
        rows = []
        for i in range(3):
            case = f'Demo__a__b{i}'
            claim = f'impact_claim_{i}'
            (self.cases / case / 'bindings').mkdir(parents=True)
            (self.cases / case / 'bindings' / f'{claim}.json').write_text('{}')
            rows.append({'case': case, 'status': 'done', 'reproduced': 1,
                         'verdicts': ['violation_reproduced'],
                         'bound_claim_ids': [claim]})
        targets = select_negative_targets({'cases': rows}, self.cases,
                                          max_negatives=2)
        self.assertEqual(len(targets), 2)


class ComposeReportTest(unittest.TestCase):
    def test_merges_layers(self):
        positive = {'cases': []}
        negative = []
        report = compose_report(positive, negative,
                                {'precision': 0.9}, {'targets': 1})
        self.assertEqual(report['schema_version'], 'stage3-fullflow-report/1')
        self.assertEqual(report['judge_anchored'], {'precision': 0.9})
        self.assertEqual(report['negative_build'], {'targets': 1})
        self.assertIn('metrics', report)


class RunScriptTest(unittest.TestCase):
    def test_run_script_invokes_file_directly_not_as_module(self):
        captured = {}
        original = subprocess.run

        class _Proc:
            returncode = 0

        def fake_run(cmd, **kwargs):
            captured['cmd'] = cmd
            captured['kwargs'] = kwargs
            return _Proc()

        subprocess.run = fake_run
        try:
            self.assertEqual(
                _run_script(Path('/x/metrics/judge_anchor.py'),
                            ['--out', '/tmp/o']),
                0)
        finally:
            subprocess.run = original
        self.assertEqual(captured['cmd'][:2],
                         [sys.executable, '/x/metrics/judge_anchor.py'])
        self.assertEqual(captured['kwargs']['cwd'], '/x/metrics')

    def test_judge_anchor_args_include_blind_invalid_evals(self):
        args = _judge_anchor_args(Path('/x/gt.json'), Path('/y/pe.json'),
                                  Path('/z/out.json'))
        self.assertIn('--judge-ground-truth', args)
        self.assertIn('--positive-eval', args)
        self.assertIn('--out', args)
        for name in BLIND_INVALID_EVALS:
            blind = METRICS_DIR / name
            if blind.is_file():
                self.assertIn('--blind-invalid-eval', args)
                self.assertIn(str(blind), args)


if __name__ == '__main__':
    unittest.main()
