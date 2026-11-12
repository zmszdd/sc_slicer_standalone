"""End-to-end serial-chain test: stage-1 slice -> stage-2 run -> stage-3 verdict.

Two levels:

* ``TestSerialChainReusingArtifacts`` -- fast, deterministic, CI-safe. Reuses the
  committed stage-1 slice and the frozen stage-2 run, then drives the real
  stage-3 assemble + forge differential through ``lib.runner.run_pipeline`` and
  asserts ``violation_reproduced``.
* ``TestSerialChainFromStage1Input`` -- slow, opt-in. Regenerates the slice from
  ``stage1_input/BuilderWalletInitPoC.sol`` with ``run.sh`` (cargo build), then
  runs the same stage-3 chain. Guarded by ``RUN_STAGE1_E2E=1``.
"""
import json
import os
import shutil
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

from lib.runner import ROOT, STAGE3_DIR, run_pipeline


def _unique_run_id(prefix: str) -> str:
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')
    return f'{prefix}_{stamp}'


def _build_manifest(tmp: Path, *, output_slice: Path) -> Path:
    manifest = {
        'schema_version': 'pipeline-manifest/1',
        'case_id': 'panoptic_builder_init_e2e',
        'stage1': {
            'input': str(ROOT / 'stage1_input' / 'BuilderWalletInitPoC.sol'),
            'contract': 'BuilderWalletInitPoC',
            'function': 'test_builderWalletInitCanBeOverwritten',
            'variable': 'stolen',
            'level': 2,
            'compile_guarantee': True,
            'output_slice': str(output_slice),
        },
        'stage2': {
            'run_dir': str(ROOT / 'tools' / 'stage3' / 'cases'
                           / 'panoptic_builder_init' / 'stage2_run'),
        },
        'stage3': {
            'binding': str(ROOT / 'stage1_input' / 'stage3_handoff' / 'binding.json'),
            'test': str(ROOT / 'stage1_input' / 'stage3_handoff' / 'test'),
            'case_dir': str(tmp / 'case'),
        },
    }
    path = tmp / 'manifest.pipeline.json'
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    return path


def _assert_reproduced(run_dir: Path):
    evidence_path = run_dir / 'pipeline-summary.json'
    if not evidence_path.is_file():
        raise AssertionError(f'pipeline summary missing: {evidence_path}')
    evidence = json.loads(evidence_path.read_text())
    verdict = (evidence.get('stage3') or {}).get('consistency_verdict')
    if verdict != 'violation_reproduced':
        raise AssertionError(
            f'expected violation_reproduced, got {verdict!r}; '
            f'see {run_dir}')


class TestSerialChainReusingArtifacts(unittest.TestCase):
    def setUp(self):
        import tempfile
        self._tmp = Path(tempfile.mkdtemp(prefix='e2e_pipeline_'))
        self._run_id = _unique_run_id('e2e_pipeline_reuse')

    def tearDown(self):
        run_dir = STAGE3_DIR / 'runs' / self._run_id
        shutil.rmtree(run_dir, ignore_errors=True)
        shutil.rmtree(self._tmp, ignore_errors=True)

    def test_reused_slice_and_stage2_reproduces(self):
        slice_path = ROOT / 'stage1_input' / 'BuilderWalletSlice.sol'
        manifest = _build_manifest(self._tmp, output_slice=slice_path)
        run_dir = self._tmp / 'run'
        rc, run_dir = run_pipeline(manifest, run_dir=run_dir,
                                   skip_stage1=True, skip_stage2=True, serial=True,
                                   run_id=self._run_id)
        self.assertEqual(rc, 0, f'pipeline failed; see {run_dir}')
        _assert_reproduced(run_dir)


@unittest.skipUnless(os.environ.get('RUN_STAGE1_E2E') == '1',
                     'set RUN_STAGE1_E2E=1 to regenerate the slice via run.sh')
class TestSerialChainFromStage1Input(unittest.TestCase):
    def setUp(self):
        import tempfile
        self._tmp = Path(tempfile.mkdtemp(prefix='e2e_pipeline_stage1_'))
        self._run_id = _unique_run_id('e2e_pipeline_stage1')

    def tearDown(self):
        run_dir = STAGE3_DIR / 'runs' / self._run_id
        shutil.rmtree(run_dir, ignore_errors=True)
        shutil.rmtree(self._tmp, ignore_errors=True)

    def test_regenerate_slice_then_reproduce(self):
        slice_path = self._tmp / 'slice' / 'BuilderWalletSlice.sol'
        manifest = _build_manifest(self._tmp, output_slice=slice_path)
        run_dir = self._tmp / 'run'
        rc, run_dir = run_pipeline(manifest, run_dir=run_dir,
                                   skip_stage1=False, skip_stage2=True, serial=True,
                                   run_id=self._run_id)
        self.assertEqual(rc, 0, f'pipeline failed; see {run_dir}')
        _assert_reproduced(run_dir)


if __name__ == '__main__':
    sys.exit(unittest.main())
