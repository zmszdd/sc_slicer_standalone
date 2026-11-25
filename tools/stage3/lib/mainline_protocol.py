"""Version and fingerprint the single mainline protocol.

A run is only comparable with other runs when the code that produced it is
identical.  This module hashes the files that define the mainline contract and
stores the result in every run.  A committed baseline catches accidental code
drift; intentional changes require an explicit ``PROTOCOL_VERSION`` bump and a
regenerated baseline.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

STAGE3_DIR = Path(__file__).resolve().parents[1]
ROOT = STAGE3_DIR.parents[1]
BASELINE_FILE = STAGE3_DIR / 'mainline-protocol.json'

PROTOCOL_VERSION = 'mainline/1.7.36'
SCHEMA_VERSION = 'mainline-protocol/1'

# semantic-live-27 adds observability metadata.  Its symbol namespace must be
# aligned with the namespaced formalization for stage-2 audit and stage-3
# binding to consume the same contract.
STAGE2_PROMPT_VERSION = 'semantic-live-27'
STAGE2_PROVIDER = 'opencode_api'
STAGE2_MODEL = 'opencode-go/deepseek-v4.1-flash'

# Explicitly enumerate the mainline.  Experimental or historical scripts must
# not silently change the meaning of an evaluation result.
MAINLINE_FILES = (
    'config/llm.env.example',
    'requirements.txt',
    'Cargo.toml',
    'Cargo.lock',
    'run.sh',
    'main.py',
    'src/**/*.rs',
    'tools/pipeline/cli/case_run.py',
    'tools/pipeline/cli/manifest_gen.py',
    'tools/pipeline/cli/pipeline_batch.py',
    'tools/pipeline/cli/pipeline_run.py',
    'tools/pipeline/lib/manifest.py',
    'tools/pipeline/lib/runner.py',
    'tools/report_constraints_v2/cli/batch_verify.py',
    'tools/report_constraints_v2/cli/semantic_pipeline.py',
    'tools/report_constraints_v2/lib/formalization_audit.py',
    'tools/report_constraints_v2/lib/invariant_candidates.py',
    'tools/report_constraints_v2/lib/multi_impact.py',
    'tools/report_constraints_v2/lib/plan_synthesizer.py',
    'tools/report_constraints_v2/lib/report_only.py',
    'tools/report_constraints_v2/lib/semantic_core.py',
    'tools/report_constraints_v2/prompts/active.py',
    'tools/report_constraints_v2/prompts/current.py',
    'tools/report_constraints_v2/prompts/definitions.py',
    'tools/report_constraints_v2/prompts/live26_snapshot.py',
    'tools/report_constraints_v2/prompts/registry.py',
    'scripts/code4rena/author_negative_witness.py',
    'scripts/code4rena/build_negative_witness_inputs.py',
    'scripts/code4rena/neutral_entrypoint_pipeline.py',
    'tools/stage3/cli/stage3_bind.py',
    'tools/stage3/cli/stage3_eval_run.py',
    'tools/stage3/cli/stage3_metrics_sync.py',
    'tools/stage3/cli/stage3_multi.py',
    'tools/stage3/cli/stage3_pipeline.py',
    'tools/stage3/evaluation/metrics/current_denominator.py',
    'tools/stage3/evaluation/metrics/case_readiness.py',
    'tools/stage3/evaluation/metrics/consolidate_mainline_stage2.py',
    'tools/stage3/evaluation/metrics/effect_witness_reaudit.py',
    'tools/stage3/evaluation/metrics/freeze_mainline_subset.py',
    'tools/stage3/evaluation/metrics/build_dev_current_mini.py',
    'tools/stage3/evaluation/metrics/build_official_negative_pool.py',
    'tools/stage3/evaluation/metrics/dev_current_metrics.py',
    'tools/stage3/evaluation/metrics/mainline_metrics.py',
    'tools/stage3/evaluation/metrics/provenance_gate.py',
    'tools/stage3/evaluation/metrics/refresh_negative_slice_readiness.py',
    'tools/stage3/evaluation/metrics/run_mainline.py',
    'tools/stage3/evaluation/metrics/sample_mainline.py',
    'tools/stage3/evaluation/metrics/run_dev_24.py',
    'tools/stage3/lib/artifact_fingerprint.py',
    'tools/stage3/lib/bindability_feedback.py',
    'tools/stage3/lib/binding.py',
    'tools/stage3/lib/binding_llm.py',
    'tools/stage3/lib/binding_projection.py',
    'tools/stage3/lib/binding_normalize.py',
    'tools/stage3/lib/binding_scope.py',
    'tools/stage3/lib/binding_validate.py',
    'tools/stage3/lib/case_runner.py',
    'tools/stage3/lib/claim_population.py',
    'tools/stage3/lib/execution_contract.py',
    'tools/stage3/lib/execution_gate.py',
    'tools/stage3/lib/forge_runner.py',
    'tools/stage3/lib/harness_manifest.py',
    'tools/stage3/lib/invariant_ranking.py',
    'tools/stage3/lib/mainline_protocol.py',
    'tools/stage3/lib/path_config.py',
    'tools/stage3/lib/metrics_sync.py',
    'tools/stage3/lib/observable_ir.py',
    'tools/stage3/lib/observable_recipes.py',
    'tools/stage3/lib/patch.py',
    'tools/stage3/lib/recipe_compiler.py',
    'tools/stage3/lib/reference_patch.py',
    'tools/stage3/lib/revert_witness.py',
    'tools/stage3/lib/spec_loader.py',
    'tools/stage3/lib/stage2_contract.py',
    'tools/stage3/lib/stage2_restate.py',
    'tools/stage3/lib/strong_invariant.py',
    'tools/stage3/lib/locked_eval.py',
    'tools/stage3/lib/source_ir.py',
    'tools/stage3/lib/witness_router.py',
    'tools/stage3/cli/stage3_locked_eval.py',
    'tools/pipeline/lib/harness_qualification.py',
    'tools/stage3/lib/witness_protocol.py',
)


# These files determine how results are reported, not what Stage-3 executes.
# Editing them must not invalidate already-produced run envelopes.
REPORT_ONLY_FILES = {
    'tools/stage3/cli/stage3_metrics_sync.py',
    'tools/stage3/evaluation/metrics/build_dev_current_mini.py',
    'tools/stage3/evaluation/metrics/build_official_negative_pool.py',
    'tools/stage3/evaluation/metrics/current_denominator.py',
    'tools/stage3/evaluation/metrics/case_readiness.py',
    'tools/stage3/evaluation/metrics/dev_current_metrics.py',
    'tools/stage3/evaluation/metrics/effect_witness_reaudit.py',
    'tools/stage3/evaluation/metrics/freeze_mainline_subset.py',
    'tools/stage3/evaluation/metrics/mainline_metrics.py',
    'tools/stage3/evaluation/metrics/provenance_gate.py',
    'tools/stage3/evaluation/metrics/sample_mainline.py',
    'tools/stage3/lib/locked_eval.py',
    'tools/stage3/lib/mainline_protocol.py',
    'tools/stage3/lib/metrics_sync.py',
    'tools/stage3/lib/revert_witness.py',
}

# Runs produced before report-only files were split still carry the legacy
# all-file hash.  Only accept them for the same frozen protocol version; any
# execution change still requires an explicit PROTOCOL_VERSION bump.
LEGACY_RUN_HASHES = {
    'mainline/1.7.36': frozenset({
        # Report-only successor of 1.7.35; execution semantics are unchanged.
        'd2b0965b868b228ea599d1ec96381753fb6592c5a7fc544d678c6ff1bc6eaac3',
        'fbd309d19ce2aa393d39b89e3a6f28fc9da6777d02ab100b5d38db0124833fcb',
        'd04fe32f98c4e3436a9908e1fe1157c827279913843502a796666d4994102006',
        'ea1fa14ffcf6196a67643da23c16e9e8f2047cbbe5cee45258e3a0df7c9d546c',
        '3c40a7cb3519b44de20e9becb948a5c10375d038e0398585cd2ea7af5759b2bd',
    }),
    'mainline/1.7.35': frozenset({
        # Report-only successor of 1.7.34; execution semantics are unchanged.
        'fbd309d19ce2aa393d39b89e3a6f28fc9da6777d02ab100b5d38db0124833fcb',
        'd04fe32f98c4e3436a9908e1fe1157c827279913843502a796666d4994102006',
        'ea1fa14ffcf6196a67643da23c16e9e8f2047cbbe5cee45258e3a0df7c9d546c',
        '3c40a7cb3519b44de20e9becb948a5c10375d038e0398585cd2ea7af5759b2bd',
    }),
    'mainline/1.7.33': frozenset({
        # Execution digest before the orchestration-only negative lane entry.
        # run_mainline controls which cases are submitted; it does not change
        # Stage-3 binding, compilation, execution or verdict semantics.
        'ea1fa14ffcf6196a67643da23c16e9e8f2047cbbe5cee45258e3a0df7c9d546c',
        '3c40a7cb3519b44de20e9becb948a5c10375d038e0398585cd2ea7af5759b2bd',
    }),
    'mainline/1.7.34': frozenset({
        'd04fe32f98c4e3436a9908e1fe1157c827279913843502a796666d4994102006',
        'ea1fa14ffcf6196a67643da23c16e9e8f2047cbbe5cee45258e3a0df7c9d546c',
        '3c40a7cb3519b44de20e9becb948a5c10375d038e0398585cd2ea7af5759b2bd',
    }),
}

REPORT_ONLY_VERSION_PREDECESSORS = {
    'mainline/1.7.36': frozenset({
        'mainline/1.7.35', 'mainline/1.7.34', 'mainline/1.7.33'}),
    'mainline/1.7.35': frozenset({'mainline/1.7.34', 'mainline/1.7.33'}),
    'mainline/1.7.34': frozenset({'mainline/1.7.33'}),
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _paths(root: Path) -> list[Path]:
    found: set[Path] = set()
    for pattern in MAINLINE_FILES:
        if '**' in pattern or '*' in pattern:
            found.update(path for path in root.glob(pattern) if path.is_file())
            continue
        path = root / pattern
        if not path.is_file():
            raise FileNotFoundError('mainline file missing: ' + str(path))
        found.add(path)
    return sorted(found, key=lambda path: path.relative_to(root).as_posix())


def compute(root: Path | None = None) -> dict:
    """Compute the current protocol record without reading private config."""
    root = Path(root) if root is not None else ROOT
    files = {
        path.relative_to(root).as_posix(): _sha256(path)
        for path in _paths(root)
    }
    execution_files = {
        name: digest for name, digest in files.items()
        if name not in REPORT_ONLY_FILES
    }
    report_files = {
        name: digest for name, digest in files.items()
        if name in REPORT_ONLY_FILES
    }

    def _digest(payload: dict) -> str:
        canonical = json.dumps(
            payload, ensure_ascii=False, sort_keys=True,
            separators=(',', ':'),
        ).encode('utf-8')
        return hashlib.sha256(canonical).hexdigest()

    identity = {
        'version': PROTOCOL_VERSION,
        'stage2_prompt_version': STAGE2_PROMPT_VERSION,
        'stage2_provider': STAGE2_PROVIDER,
        'stage2_model': STAGE2_MODEL,
    }
    return {
        'schema_version': SCHEMA_VERSION,
        **identity,
        'sha256': _digest({**identity, 'files': execution_files}),
        'execution_sha256': _digest({**identity, 'files': execution_files}),
        'report_sha256': _digest({'files': report_files}),
        'files': files,
        'execution_files': execution_files,
        'report_files': report_files,
    }


def current() -> dict:
    record = compute()
    return {
        'version': record['version'],
        'stage2_prompt_version': record['stage2_prompt_version'],
        'stage2_provider': record['stage2_provider'],
        'stage2_model': record['stage2_model'],
        'sha256': record['execution_sha256'],
        'report_sha256': record['report_sha256'],
    }


def is_current_run(record: dict | None) -> bool:
    """Return true when a run envelope belongs to the current execution.

    Report-only edits change ``report_sha256`` but not ``sha256``.  Runs made
    before the split carry the version's legacy all-file hash; they remain valid
    only for the same frozen protocol version.
    """
    record = record or {}
    version = str(record.get('version') or '')
    if version != PROTOCOL_VERSION:
        if version not in REPORT_ONLY_VERSION_PREDECESSORS.get(
                PROTOCOL_VERSION, frozenset()):
            return False
    current_record = current()
    digest = str(record.get('sha256') or '')
    if digest == current_record['sha256']:
        return True
    return (digest in LEGACY_RUN_HASHES.get(PROTOCOL_VERSION, frozenset())
            or digest in LEGACY_RUN_HASHES.get(version, frozenset()))


def load_baseline(path: Path | None = None) -> dict:
    path = Path(path) if path is not None else BASELINE_FILE
    try:
        payload = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return {}
    return payload if isinstance(payload, dict) else {}


def verify(root: Path | None = None, baseline_path: Path | None = None) -> dict:
    actual = compute(root)
    baseline = load_baseline(baseline_path)
    problems = []
    if not baseline:
        problems.append('mainline protocol baseline missing or unreadable')
    else:
        if baseline.get('version') != actual['version']:
            problems.append(
                f"protocol version drift: baseline={baseline.get('version')} "
                f"current={actual['version']}")
        for key in ('stage2_prompt_version', 'stage2_provider', 'stage2_model'):
            if baseline.get(key) != actual[key]:
                problems.append(
                    f'{key} drift: baseline={baseline.get(key)!r} '
                    f'current={actual[key]!r}')
        if baseline.get('sha256') != actual['sha256']:
            problems.append('protocol hash drift: regenerate baseline after '
                            'an intentional protocol version bump')
            baseline_files = baseline.get('files') or {}
            changed = sorted(
                name for name in set(actual['files']) | set(baseline_files)
                if actual['files'].get(name) != baseline_files.get(name))
            problems.append('changed files: ' + ', '.join(changed[:40]))
        elif baseline.get('report_sha256') != actual['report_sha256']:
            problems.append('report-only hash drift: regenerate baseline after '
                            'changing metric or report generation code')
    return {
        'ok': not problems,
        'problems': problems,
        'version': actual['version'],
        'sha256': actual['sha256'],
    }


def write_baseline(path: Path | None = None) -> dict:
    path = Path(path) if path is not None else BASELINE_FILE
    record = compute()
    path.write_text(
        json.dumps(record, ensure_ascii=False, indent=2, sort_keys=True) + '\n',
        encoding='utf-8')
    return record


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--check', action='store_true',
                       help='verify the committed baseline (default)')
    group.add_argument('--write', action='store_true',
                       help='regenerate the committed baseline')
    args = parser.parse_args(argv)
    if args.write:
        record = write_baseline()
        print(json.dumps({'version': record['version'],
                          'sha256': record['sha256']}, indent=2))
        return 0
    result = verify()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result['ok'] else 1


if __name__ == '__main__':
    sys.exit(main())
