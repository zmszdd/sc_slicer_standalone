"""Run-directory prompt snapshots: replay never re-resolves the live prompt."""
import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from cli import semantic_pipeline as p
from cli import batch_verify as verify_semantic
from prompts import current

HERE = Path(__file__).resolve().parents[1]
TEXT = (HERE / 'results/report_only/brix_fee_assistant_final/extraction-input.txt').read_text()
# A frozen external-model run predating the snapshot policy; replay of such
# directories keeps resolving the time-invariant frozen module.
FROZEN_RUN = (HERE / 'evaluation/archive/prompt_v320_blind_03/runs/'
              'Olas_j3PRAMM3fVq__9eKVuFn3L2m__h3XmvpYNrWz')


def id_inputs():
    """brix_fee elements plus the report-formal-plan/4 candidate the live
    prompt's fixed-template mandate expects (mirrors test_evidence_ids)."""
    elements = json.loads((HERE / 'samples/brix_fee/ids/elements.json').read_text())
    formal = {
        'schema_version': 'report-formal-plan/4',
        'relation_class': 'progress_or_liveness',
        'precondition_ids': ['pre_overpay'],
        'intent_id': 'intent_accept_buffer',
        'impact_ids': ['impact_revert'],
        'symbols': {
            'paid_fee': {'sort': 'int', 'unit': 'native_wei',
                         'meaning': 'Native fee supplied by the caller',
                         'checkpoint': 'call_entry',
                         'entity_ids': ['caller', 'native_fee'],
                         'source_ids': ['pre_overpay']},
            'required_fee': {'sort': 'int', 'unit': 'native_wei',
                             'meaning': 'Required native fee',
                             'checkpoint': 'call_entry',
                             'entity_ids': ['messenger', 'native_fee'],
                             'source_ids': ['pre_overpay']},
            'fee_revert': {'sort': 'bool', 'unit': None,
                           'meaning': 'Fee mismatch revert',
                           'checkpoint': 'call_exit',
                           'entity_ids': ['caller', 'messenger'],
                           'source_ids': ['impact_revert']},
        },
        'precondition_terms': [{
            'source_id': 'pre_overpay',
            'predicate': {'kind': 'comparison', 'left': 'paid_fee',
                          'operator': 'gt', 'right': {'symbol': 'required_fee'}},
        }],
        'derived_definitions': [],
        'pattern': {
            'kind': 'relation_obligation',
            'condition': {'kind': 'comparison', 'left': 'paid_fee',
                          'operator': 'gt', 'right': {'symbol': 'required_fee'}},
            'relation': {'kind': 'truth', 'symbol': 'fee_revert', 'value': False},
        },
        'assumptions': [],
        'unresolved': [],
        'limitations': [],
    }
    return elements, formal


def run_pipeline(root, extra_argv=()):
    """One synthetic neural run (default live prompt); artifacts fully replay."""
    elements, formal = id_inputs()

    def fake(text, output, model, prompt):
        value = elements if output.name == 'neural-elements' else formal
        (output / 'model-claim.json').write_text(json.dumps(value))
        return copy.deepcopy(value)

    output = root / 'out'
    argv = ['semantic_pipeline.py', '--report', str(root / 'report.md'),
            '--extract', '--allow-report-upload', '--model', 'synthetic_control',
            '--output', str(output)] + list(extra_argv)
    with patch('sys.argv', argv), patch.object(p.r, 'extract', side_effect=fake), \
            patch('sys.stdout', io.StringIO()):
        p.main()  # exit code varies with the acceptance verdict; replay is the point
    return output


class PromptSnapshotTests(unittest.TestCase):
    def test_live_run_records_snapshots_and_features(self):
        with tempfile.TemporaryDirectory() as work:
            root = Path(work)
            root.joinpath('report.md').write_text(TEXT)
            output = run_pipeline(root)
            provenance = json.loads((output / 'provenance.json').read_text())
            element = (output / 'prompt-element.txt').read_text()
            formal = (output / 'prompt-formal.txt').read_text()
            self.assertEqual(element, current.ID_ELEMENT_PROMPT)
            self.assertEqual(formal, current.FORMAL_PLAN_PROMPT)
            self.assertEqual(provenance['requested_evidence_mode'], 'ids')
            self.assertEqual(set(provenance['prompt_features']),
                             set(current.FEATURES))
            self.assertTrue(provenance['prompt_features']['strict_piv'])
            self.assertFalse(provenance['prompt_features']
                             ['protocol_identifier_exclusion'])
            # The first element attempt's prompt.txt is prompt + payload, so
            # the cross-check proves the snapshot was the text actually sent.
            sent = (output / 'neural-elements' / 'prompt.txt').read_text()
            self.assertTrue(sent.startswith(element))
            result = verify_semantic.verify(output)
            self.assertTrue(result['offline_verified'])
            self.assertIn('prompt_snapshots', result['checks_performed'])

    def test_tampered_snapshot_fails_verification(self):
        with tempfile.TemporaryDirectory() as work:
            root = Path(work)
            root.joinpath('report.md').write_text(TEXT)
            output = run_pipeline(root)
            path = output / 'prompt-element.txt'
            path.write_text(path.read_text() + ' tampered')
            with self.assertRaisesRegex(ValueError, 'snapshot hash mismatch'):
                verify_semantic.verify(output)

    def test_in_place_prompt_edit_does_not_break_replay(self):
        with tempfile.TemporaryDirectory() as work:
            root = Path(work)
            root.joinpath('report.md').write_text(TEXT)
            output = run_pipeline(root)
            # Simulate the live file being edited in place afterwards.
            with patch.object(current, 'ID_ELEMENT_PROMPT', 'EDITED ELEMENT TEXT'), \
                    patch.object(current, 'FORMAL_PLAN_PROMPT', 'EDITED FORMAL TEXT'):
                result = verify_semantic.verify(output)
                self.assertTrue(result['offline_verified'])
                self.assertIn('prompt_snapshots', result['checks_performed'])
                # Deleting the snapshots forfeits replay: verification falls
                # back to the current (edited) live text and honestly fails.
                (output / 'prompt-element.txt').unlink()
                (output / 'prompt-formal.txt').unlink()
                with self.assertRaises(ValueError):
                    verify_semantic.verify(output)

    def test_frozen_run_without_snapshots_replays_via_registry(self):
        if not FROZEN_RUN.is_dir():
            self.skipTest('frozen blind-03 run not available')
        result = verify_semantic.verify(FROZEN_RUN)
        self.assertTrue(result['offline_verified'])
        self.assertIn('resolved_prompt_hashes', result['checks_performed'])
        self.assertNotIn('prompt_snapshots', result['checks_performed'])


if __name__ == '__main__':
    unittest.main()
