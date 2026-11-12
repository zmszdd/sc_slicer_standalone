"""Assemble a stage-3 case directory from stage-1/2 artifacts.

This is the integration channel between the three stages:

    stage1 slice (.sol)  ─┐
    stage2 run dir       ─┼─>  cases/<name>/  ─>  cli.stage3_pipeline
    binding.json         ─┤
    PoC test             ─┘

The builder only copies and validates. It never edits stage-1/2 outputs in place
and never guesses a binding: a malformed handoff fails loudly.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

from lib.spec_loader import SpecError, load_stage2_run
from lib.binding import load_binding, validate_binding

STAGE2_ARTIFACTS = ('stage3-spec.json', 'constraints.json', 'formalization.json')

DEFAULT_FOUNDRY_TOML = (
    '[profile.default]\nsrc = "src"\ntest = "test"\nout = "out"\n'
    'via_ir = true\noptimizer = true\noptimizer_runs = 200\n')


def _copy_file(src: Path, dst: Path):
    if not src.is_file():
        raise SpecError(f'missing file: {src}')
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def _copy_tree(src: Path, dst: Path):
    if not src.is_dir():
        raise SpecError(f'missing directory: {src}')
    shutil.copytree(src, dst, dirs_exist_ok=True)


def _copy_source(src: Path, dst_dir: Path, src_name: str | None = None):
    dst_dir.mkdir(parents=True, exist_ok=True)
    if src.is_dir():
        shutil.copytree(src, dst_dir, dirs_exist_ok=True)
    elif src.is_file():
        _copy_file(src, dst_dir / (src_name or src.name))
    else:
        raise SpecError(f'src must be a Solidity file or a directory: {src}')


def _copy_test(src: Path, dst_dir: Path):
    dst_dir.mkdir(parents=True, exist_ok=True)
    if src.is_dir():
        shutil.copytree(src, dst_dir, dirs_exist_ok=True)
    elif src.is_file():
        _copy_file(src, dst_dir / src.name)
    else:
        raise SpecError(f'test must be a file or a directory: {src}')


def assemble_case(*, name: str, src: Path, stage2_run: Path,
                  binding: Path | None = None, test: Path | None = None,
                  out: Path, foundry_toml: Path | None = None,
                  default_foundry_toml: bool = False, lib: Path | None = None,
                  remappings: Path | None = None, expected: Path | None = None,
                  overwrite: bool = False, src_name: str | None = None) -> Path:
    if not isinstance(name, str) or not name.strip():
        raise SpecError('case name is required')
    out = Path(out)
    if out.exists() and not overwrite:
        raise SpecError(f'output case directory already exists: {out}\n'
                        'pass --overwrite to replace it')
    if out.exists() and overwrite:
        shutil.rmtree(out)

    stage2 = load_stage2_run(Path(stage2_run))
    claim_id = None
    if binding is not None:
        binding_data = load_binding(Path(binding))
        claim_id, _ = validate_binding(binding_data, stage2['spec'])

    out.mkdir(parents=True, exist_ok=False)
    _copy_source(Path(src), out / 'src', src_name=src_name)
    if test is not None:
        _copy_test(Path(test), out / 'test')
    else:
        (out / 'test').mkdir(parents=True, exist_ok=True)
    for artifact in STAGE2_ARTIFACTS:
        _copy_file(Path(stage2_run) / artifact, out / 'stage2_run' / artifact)
    if binding is not None:
        _copy_file(Path(binding), out / 'binding.json')
    if foundry_toml is not None:
        _copy_file(Path(foundry_toml), out / 'foundry.toml')
    elif default_foundry_toml:
        (out / 'foundry.toml').write_text(DEFAULT_FOUNDRY_TOML)
    if lib is not None:
        _copy_tree(Path(lib), out / 'lib')
    if remappings is not None:
        _copy_file(Path(remappings), out / 'remappings.txt')
    if expected is not None:
        _copy_file(Path(expected), out / 'expected' / 'expected.json')

    (out / 'case.json').write_text(json.dumps({
        'schema_version': 'stage3-case-manifest/1',
        'name': name,
        'claim_id': claim_id,
        'src': str(Path(src).resolve()),
        'stage2_run': str(Path(stage2_run).resolve()),
        'binding': str(Path(binding).resolve()) if binding is not None else None,
        'test': str(Path(test).resolve()) if test is not None else None,
    }, indent=2) + '\n')
    return out
