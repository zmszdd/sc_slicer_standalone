"""Load and validate the three-stage parallel pipeline manifest."""
from __future__ import annotations

import json
from pathlib import Path

SCHEMA = 'pipeline-manifest/1'

STAGE2_ARTIFACTS = ('stage3-spec.json', 'constraints.json', 'formalization.json')


class ManifestError(ValueError):
    pass


def _require(condition, message):
    if not condition:
        raise ManifestError(message)


def load_manifest(path: Path) -> dict:
    path = Path(path)
    if not path.is_file():
        raise ManifestError(f'manifest not found: {path}')
    try:
        value = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise ManifestError(f'invalid manifest JSON: {exc}') from exc
    if not isinstance(value, dict):
        raise ManifestError('manifest must be a JSON object')
    return validate_manifest(value, path.parent)


def validate_manifest(value: dict, base_dir: Path | None = None) -> dict:
    _require(value.get('schema_version') == SCHEMA, 'unknown manifest schema')
    case_id = value.get('case_id')
    _require(isinstance(case_id, str) and case_id.strip(), 'case_id is required')

    stage1 = value.get('stage1')
    _require(isinstance(stage1, dict), 'stage1 must be an object')
    for key in ('input', 'contract', 'variable', 'output_slice'):
        _require(isinstance(stage1.get(key), str) and stage1[key].strip(),
                 f'stage1.{key} is required')
    _require(isinstance(stage1.get('level', 0), int), 'stage1.level must be an int')

    stage2 = value.get('stage2')
    _require(isinstance(stage2, dict), 'stage2 must be an object')
    has_report = isinstance(stage2.get('report'), str) and stage2['report'].strip()
    has_run_dir = isinstance(stage2.get('run_dir'), str) and stage2['run_dir'].strip()
    _require(has_report or has_run_dir,
             'stage2 must set either report or run_dir')
    if has_report:
        _require(isinstance(stage2.get('output'), str) and stage2['output'].strip(),
                 'stage2.output is required when stage2.report is set')
    extra_args = stage2.get('args', [])
    _require(isinstance(extra_args, list) and all(isinstance(a, str) for a in extra_args),
             'stage2.args must be a list of strings')
    reuse_verify = stage2.get('reuse_verify', True)
    _require(isinstance(reuse_verify, bool),
             'stage2.reuse_verify must be a bool')

    stage3 = value.get('stage3')
    _require(isinstance(stage3, dict), 'stage3 must be an object')
    _require(isinstance(stage3.get('case_dir'), str)
             and stage3['case_dir'].strip(), 'stage3.case_dir is required')
    if stage3.get('test') is not None:
        _require(isinstance(stage3['test'], str) and stage3['test'].strip(),
                 'stage3.test must be a string when set')
    if stage3.get('binding') is not None:
        _require(isinstance(stage3['binding'], str) and stage3['binding'].strip(),
                 'stage3.binding must be a string when set')
    if stage3.get('binding_rounds') is not None:
        _require(isinstance(stage3['binding_rounds'], int)
                 and stage3['binding_rounds'] >= 0,
                 'stage3.binding_rounds must be a non-negative int')

    normalized = {
        'case_id': case_id,
        'stage1': {
            'input': stage1['input'],
            'contract': stage1['contract'],
            'variable': stage1['variable'],
            'function': stage1.get('function'),
            'level': stage1.get('level', 0),
            'compile_guarantee': bool(stage1.get('compile_guarantee', False)),
            'output_slice': stage1['output_slice'],
        },
        'stage2': {
            'report': stage2.get('report'),
            'run_dir': stage2.get('run_dir'),
            'output': stage2.get('output'),
            'args': extra_args,
            'reuse_verify': reuse_verify,
        },
        'stage3': {
            'binding': stage3.get('binding'),
            'binding_rounds': int(stage3.get('binding_rounds') or 3),
            'test': stage3.get('test'),
            'case_dir': stage3['case_dir'],
            'run_id': stage3.get('run_id'),
        },
    }
    if base_dir is not None:
        _check_paths(normalized, base_dir)
    return normalized


def _resolve(base_dir: Path, value: str | None) -> Path | None:
    if value is None:
        return None
    path = Path(value)
    return path if path.is_absolute() else (base_dir / path)




def build_manifest_from_case(*, case_id: str, src: Path, test: Path | None = None,
                             out_dir: Path,
                             report: Path | None = None,
                             stage2_run_dir: Path | None = None,
                             stage2_output: Path | None = None,
                             contract: str | None = None,
                             variable: str | None = None,
                             function: str | None = None,
                             binding: Path | None = None,
                             binding_rounds: int = 3,
                             case_dir: Path | None = None,
                             stage2_reuse_verify: bool = True) -> dict:
    """Build a pipeline manifest for one flattened, self-contained case.

    The flattened PoC (``contract.flattened.t.sol``) is treated as the
    stage-1 slice source: when ``run_pipeline(skip_stage1=True)`` is used,
    ``src`` is passed straight through to stage-3, so a brand-new case only
    needs a report and a compilable flatten to run end-to-end. The flatten is
    self-contained (it includes the PoC test harness), so ``test`` defaults to
    ``None`` and the harness lives in ``src/`` only, matching the eval path.
    Slicing targets (contract/variable) are optional here and only matter when
    stage-1 slicing is re-enabled.

    ``stage3.binding`` is intentionally omitted unless provided: the runner
    auto-binds via ``stage3_bind`` (see ``runner._run_stage3``).
    """
    stage2 = {}
    if report is not None:
        stage2 = {'report': str(report), 'output': str(stage2_output or
                                                       (out_dir / 'stage2'))}
    elif stage2_run_dir is not None:
        stage2 = {'run_dir': str(stage2_run_dir)}
    else:
        raise ManifestError('either report or stage2_run_dir is required')
    stage2['reuse_verify'] = bool(stage2_reuse_verify)

    stage3 = {'case_dir': str(case_dir or (out_dir / 'case'))}
    if test is not None:
        stage3['test'] = str(test)
    if binding is not None:
        stage3['binding'] = str(binding)
    else:
        stage3['binding_rounds'] = int(binding_rounds)

    return {
        'schema_version': SCHEMA,
        'case_id': case_id,
        'stage1': {
            'input': str(src),
            'contract': contract or 'TODO_contract',
            'variable': variable or 'TODO_variable',
            'function': function,
            'level': 2,
            'compile_guarantee': True,
            'output_slice': str(src),
        },
        'stage2': stage2,
        'stage3': stage3,
    }

def _check_paths(manifest: dict, base_dir: Path):
    stage1 = manifest['stage1']
    _require(_resolve(base_dir, stage1['input']).is_file(),
             f"stage1.input not found: {stage1['input']}")
    stage2 = manifest['stage2']
    if stage2['report'] is None:
        run_dir = _resolve(base_dir, stage2['run_dir'])
        for artifact in STAGE2_ARTIFACTS:
            _require((run_dir / artifact).is_file(),
                     f'stage2.run_dir missing {artifact}: {run_dir}')
    stage3 = manifest['stage3']
    if stage3['binding'] is not None:
        _require(_resolve(base_dir, stage3['binding']).is_file(),
                 f"stage3.binding not found: {stage3['binding']}")
    if stage3['test'] is not None:
        _require(_resolve(base_dir, stage3['test']).exists(),
                 f"stage3.test not found: {stage3['test']}")


def resolve_path(base_dir: Path, value: str | None) -> Path | None:
    if value is None:
        return None
    path = Path(value)
    return (path if path.is_absolute() else (base_dir / path)).resolve()
