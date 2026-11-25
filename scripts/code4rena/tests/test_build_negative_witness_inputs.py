"""Regression tests for witness-to-stage3 input assembly."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import build_negative_witness_inputs as builder


class BuildNegativeWitnessInputsTest(unittest.TestCase):
    def test_only_verified_witnesses_are_copied(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            witness = root / 'witness'
            goldset = root / 'goldset'
            flatten = root / 'flatten'
            ready = witness / 'ready'
            ready.mkdir(parents=True)
            (ready / 'contract.flattened.t.sol').write_text('contract A {}')
            (ready / 'harness-manifest.json').write_text(json.dumps({
                'route': 'negative_witness'}))
            blocked = witness / 'blocked'
            blocked.mkdir(parents=True)
            (blocked / 'contract.flattened.t.sol').write_text('contract B {}')
            (blocked / 'harness-manifest.json').write_text(json.dumps({
                'route': 'negative_witness'}))
            (witness / 'status.json').write_text(json.dumps({'rows': [
                {'case': 'ready', 'status': 'flatten_pass',
                 'route': 'negative_witness',
                 'artifact': str(ready / 'contract.flattened.t.sol')},
                {'case': 'blocked', 'status': 'blocked',
                 'route': 'negative_witness',
                 'artifact': str(blocked / 'contract.flattened.t.sol')},
            ]}))
            goldset.mkdir()
            (goldset / 'selection.json').write_text(json.dumps({'cases': [
                {'case': 'ready'}, {'case': 'blocked'}]}))
            summary = builder.build([witness], goldset, flatten)
            self.assertEqual(summary['witness_ready'], 1)
            self.assertEqual(summary['unresolved'], ['blocked'])
            self.assertTrue(
                (flatten / 'ready' / 'contract.flattened.t.sol').is_file())
            self.assertTrue(
                (flatten / 'ready' / 'harness-manifest.json').is_file())
            self.assertFalse((flatten / 'blocked').exists())

    def test_fallback_root_is_used_in_frozen_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            primary = root / 'primary'
            fallback = root / 'fallback'
            goldset = root / 'goldset'
            flatten = root / 'flatten'
            for base, case, marker in ((primary, 'first', 'primary'),
                                       (fallback, 'second', 'fallback')):
                case_dir = base / case
                case_dir.mkdir(parents=True)
                (case_dir / 'contract.flattened.t.sol').write_text(marker)
                (case_dir / 'harness-manifest.json').write_text(json.dumps({
                    'route': 'negative_witness'}))
                (base / 'status.json').write_text(json.dumps({'rows': [
                    {'case': case, 'status': 'flatten_pass',
                     'route': 'negative_witness',
                     'artifact': str(case_dir / 'contract.flattened.t.sol')},
                ]}))
            goldset.mkdir()
            (goldset / 'selection.json').write_text(json.dumps({'cases': [
                {'case': 'first'}, {'case': 'second'}]}))
            summary = builder.build([primary, fallback], goldset, flatten)
            self.assertEqual(summary['witness_ready'], 2)
            merged = json.loads(
                (flatten / 'merged-status.json').read_text())['rows']
            self.assertEqual([row['case'] for row in merged],
                             ['first', 'second'])
            self.assertEqual((flatten / 'first' /
                              'contract.flattened.t.sol').read_text(),
                             'primary')
            self.assertEqual((flatten / 'second' /
                              'contract.flattened.t.sol').read_text(),
                             'fallback')

    def test_neutral_slices_are_recorded_as_ready_not_stage3_inputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            witness = root / 'witness'
            neutral = root / 'neutral'
            goldset = root / 'goldset'
            flatten = root / 'flatten'
            witness.mkdir()
            (witness / 'status.json').write_text(json.dumps({'rows': [
                {'case': 'neutral_only', 'status': 'blocked',
                 'route': 'negative_witness', 'artifact': ''},
            ]}))
            ready = neutral / 'neutral_only'
            ready.mkdir(parents=True)
            (ready / 'contract.flattened.t.sol').write_text('contract A {}')
            goldset.mkdir()
            (goldset / 'selection.json').write_text(json.dumps({'cases': [
                {'case': 'neutral_only'}]}))
            summary = builder.build([witness], goldset, flatten,
                                    neutral_root=neutral)
            self.assertEqual(summary['neutral_slice_ready'], 1)
            self.assertEqual(summary['witness_ready'], 0)
            self.assertEqual(summary['unresolved'], ['neutral_only'])
            self.assertFalse((flatten / 'neutral_only').exists())
            merged = json.loads(
                (flatten / 'merged-status.json').read_text())['rows']
            self.assertEqual(merged[0]['route'], 'neutral_entrypoint')
            self.assertEqual(merged[0]['status'], 'flatten_pass')


if __name__ == '__main__':
    unittest.main()
