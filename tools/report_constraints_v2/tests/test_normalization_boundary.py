"""The normalization boundary must be explicit, complete and honest.

No model calls, no network, nothing written: this file only re-derives the
rejection surface from source and checks it against the declared boundary.
"""
import ast
import unittest
from pathlib import Path

from lib.normalization import (BOUNDARY, NORMALIZE, REJECT, WARN, classify,
                               entry_for, exact_entry_for, normalize_readiness)

HERE = Path(__file__).resolve().parent
STAGE2 = HERE.parent
LIB_MODULES = ('lib/ingest.py', 'lib/semantic_core.py', 'lib/plan_synthesizer.py',
               'lib/report_only.py')
RAISED = ('ValueError', 'RuntimeError')


def _literal(node):
    """The statically visible message text, including an f-string's literal parts."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.JoinedStr):
        return ''.join(part.value for part in node.values
                       if isinstance(part, ast.Constant)
                       and isinstance(part.value, str))
    if isinstance(node, ast.BinOp):
        return _literal(node.left) or _literal(node.right)
    return None


def rejection_messages():
    """Every message the lib layer can use to abort a run, derived from source."""
    found = {}
    for relative in LIB_MODULES:
        tree = ast.parse((STAGE2 / relative).read_text(encoding='utf-8'))
        for node in ast.walk(tree):
            message = None
            if isinstance(node, ast.Call):
                name = (getattr(node.func, 'id', None)
                        or getattr(node.func, 'attr', None))
                if name == 'require' and len(node.args) >= 2:
                    message = _literal(node.args[1])
            elif isinstance(node, ast.Raise) and isinstance(node.exc, ast.Call):
                if getattr(node.exc.func, 'id', None) in RAISED and node.exc.args:
                    message = _literal(node.exc.args[0])
            if message:
                found.setdefault(message, f'{relative}:{node.lineno}')
    return found


class BoundaryCoverageTest(unittest.TestCase):
    """The boundary is only real if nothing can bypass it."""

    def test_every_rejection_message_is_classified(self):
        """A new ``require(...)`` must declare its mode or this test fails."""
        # exact_entry_for, not entry_for: a truncated entry must NOT count as
        # declared, otherwise the boundary can lose a point without failing here.
        unlisted = sorted(message for message in rejection_messages()
                          if exact_entry_for(message) is None)
        self.assertEqual(
            unlisted, [],
            f'{len(unlisted)} rejection message(s) absent from BOUNDARY: '
            + '; '.join(repr(m) for m in unlisted[:5]))

    def test_entries_are_unique_and_use_known_modes(self):
        messages = [entry[0] for entry in BOUNDARY]
        self.assertEqual(len(messages), len(set(messages)),
                         'duplicate BOUNDARY entry')
        for entry in BOUNDARY:
            with self.subTest(message=entry[0]):
                self.assertIn(entry[1], (NORMALIZE, WARN, REJECT))

    def test_warn_is_empty_by_design(self):
        """Declared-uncertainty semantics live in compile_bundle (S12), not here."""
        self.assertEqual([e for e in BOUNDARY if e[1] == WARN], [])

    def test_unlisted_messages_default_to_reject(self):
        """The default is the historical behaviour, so nothing normalizes by accident."""
        self.assertEqual(classify('a rejection nobody wrote down'), REJECT)


class ReadinessNormalizationTest(unittest.TestCase):
    """The one proven in-boundary fix: pure position, no semantic change."""

    @staticmethod
    def _nested():
        return {'schema_version': 'report-readiness/1', 'decision': 'ready',
                'dimensions': {'affected_subject': {'status': 'present'},
                               'missing_dimensions': [], 'summary': 'ok'}}

    def test_hoists_nested_telemetry(self):
        normalized, changes = normalize_readiness(self._nested())
        self.assertEqual(sorted(normalized), ['decision', 'dimensions',
                                              'missing_dimensions',
                                              'schema_version', 'summary'])
        self.assertEqual(sorted(normalized['dimensions']), ['affected_subject'])
        self.assertEqual(changes, ['hoisted missing_dimensions out of dimensions',
                                   'hoisted summary out of dimensions'])

    def test_a_well_formed_response_is_untouched(self):
        candidate = {'schema_version': 'report-readiness/1', 'decision': 'ready',
                     'dimensions': {'affected_subject': {'status': 'present'}},
                     'missing_dimensions': [], 'summary': 'ok'}
        self.assertEqual(normalize_readiness(candidate), (candidate, []))

    def test_top_level_values_are_never_overwritten(self):
        candidate = self._nested()
        candidate['summary'] = 'authoritative'
        normalized, changes = normalize_readiness(candidate)
        self.assertEqual(normalized['summary'], 'authoritative')
        self.assertEqual(changes, ['hoisted missing_dimensions out of dimensions'])

    def test_the_input_is_never_mutated(self):
        """Purity is what keeps the raw response auditable after a correction."""
        import copy
        candidate = self._nested()
        snapshot = copy.deepcopy(candidate)
        normalize_readiness(candidate)
        self.assertEqual(candidate, snapshot)

    def test_malformed_shapes_are_left_for_the_validator(self):
        for candidate in (None, 'text', {'dimensions': 'not-a-dict'},
                          {'decision': 'ready'}):
            with self.subTest(candidate=candidate):
                self.assertEqual(normalize_readiness(candidate), (candidate, []))


class ScreeningNormalizationWiringTest(unittest.TestCase):
    """Wiring guard: without this, deleting the call keeps every test green.

    The fixer's own tests above would still pass if ``cli/semantic_pipeline.py``
    stopped calling it, which is exactly the gap this class closes.
    """

    def test_a_nested_screening_response_does_not_abort_the_run(self):
        import io
        import json
        import sys
        import tempfile
        from unittest.mock import patch

        import semantic_pipeline as pipeline

        reached = {}

        def fake(payload, output, _model, _prompt, **_kwargs):
            if output.name == 'neural-input-screen':
                ids = [row['id'] for row in json.loads(payload)['fragments']]
                names = ('affected_subject', 'trigger_or_action',
                         'direct_effect', 'safety_relation_basis')
                # The exact slip observed on the gold-v1 blind run: the two
                # telemetry keys arrive one level too deep.
                return {'schema_version': 'report-readiness/1',
                        'decision': 'ready',
                        'dimensions': {name: {'status': 'present',
                                              'evidence_ids': [ids[0]],
                                              'reason': 'supported'}
                                       for name in names}
                        | {'missing_dimensions': [], 'summary': 'sufficient'}}
            reached['elements'] = True
            raise RuntimeError('stop after screening')

        with tempfile.TemporaryDirectory() as dirname:
            root = Path(dirname)
            source = root / 'report.md'
            source.write_text('# Finding description\n\nA body.\n')
            out = root / 'run'
            argv = ['semantic_pipeline.py', '--report', str(source), '--extract',
                    '--elements-only', '--provider', 'deepseek',
                    '--allow-report-upload', '--output', str(out)]
            previous = sys.argv
            try:
                sys.argv = argv
                with patch.object(pipeline.r, 'load_deepseek_key',
                                  return_value='test-key'), \
                        patch.object(pipeline.r, 'extract_deepseek',
                                     side_effect=fake), \
                        patch('sys.stdout', io.StringIO()):
                    pipeline.main()
            finally:
                sys.argv = previous

            self.assertTrue(reached.get('elements'),
                            'screening was rejected instead of normalized')
            log = json.loads(
                (out / 'neural-input-screen' / 'normalization-log.json').read_text())
            self.assertEqual(log['mode'], NORMALIZE)
            self.assertEqual(log['changes'],
                             ['hoisted missing_dimensions out of dimensions',
                              'hoisted summary out of dimensions'])
            provenance = json.loads((out / 'provenance.json').read_text())
            self.assertEqual(provenance['input_screening_normalizations'],
                             log['changes'])


if __name__ == '__main__':
    unittest.main()
