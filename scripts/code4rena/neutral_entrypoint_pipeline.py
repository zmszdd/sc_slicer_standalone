#!/usr/bin/env python3
"""Build neutral executable entrypoints for the frozen negative cases.

The official Code4rena negative submissions were written to demonstrate an
alleged vulnerability.  That makes the original PoC a poor Foundry
entrypoint: it frequently fails against the current code or depends on a live
RPC fork.  This script does not rewrite the finding and does not reproduce the
alleged bug.  It imports the target source and adds one always-passing
``test_entrypoint`` so stage-2/3 receive a self-contained, locally runnable
slice.  The finding text and labels remain unchanged.

Usage:
    python neutral_entrypoint_pipeline.py [--cases-file CASES] [--out-dir DIR]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from contextlib import contextmanager
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parents[1]
STAGE3 = ROOT / 'tools' / 'stage3'
if str(STAGE3) not in sys.path:
    sys.path.insert(0, str(STAGE3))
from lib import path_config

C4_OUTPUT = path_config.c4_output_root()
REPO_CACHE = C4_OUTPUT / '_github_repos_by_project'
CASES_DEFAULT = (ROOT / 'tools' / 'stage3' / 'evaluation' / 'metrics'
                 / 'official_negative_stage1_cases_20261121.json')
OUT_DEFAULT = C4_OUTPUT / 'official_negative_neutral_entrypoints_20261121'

IMPORT_RE = re.compile(r'''(?:from\s+)?["']([^"']+\.sol)["']''')
PRAGMA_RE = re.compile(r'^\s*pragma\s+solidity\s+([^;]+);', re.M)
VERSION_RE = re.compile(r'\d+\.\d+\.\d+')
MISSING_RE = re.compile(r'error="([^"]+)": No such file or directory')
SOURCE_NOT_FOUND_RE = re.compile(r'Source\s+"([^"]+)"\s+not found')
TEST_NAME = 'test_entrypoint'


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _safe(value: str) -> str:
    return re.sub(r'[^A-Za-z0-9_]', '_', str(value))


def _repo_root(case: dict) -> Path | None:
    source = case.get('source_path')
    if not source:
        return None
    path = Path(source)
    for parent in path.parents:
        if ((parent / 'foundry.toml').is_file()
                or (parent / 'hardhat.config.js').is_file()
                or (parent / 'hardhat.config.ts').is_file()):
            return parent
    return None


def _extract_pragma(text: str) -> str:
    match = PRAGMA_RE.search(text)
    return match.group(1).strip() if match else '^0.8.0'


def _import_paths(text: str) -> list[str]:
    return IMPORT_RE.findall(text)


def _min_version(constraint: str) -> tuple[int, int, int] | None:
    values = [tuple(int(part) for part in match.split('.'))
              for match in VERSION_RE.findall(constraint)]
    return min(values) if values else None


def _read_remappings(path: Path) -> list[tuple[str, str]]:
    rows = []
    if not path.is_file():
        return rows
    for line in path.read_text().splitlines():
        text = line.strip()
        if not text or text.startswith('#') or '=' not in text:
            continue
        prefix, target = text.split('=', 1)
        rows.append((prefix.strip(), target.strip().rstrip('/')))
    return rows


def _remapping_for(rows: list[tuple[str, str]], path: str) -> tuple[str, str] | None:
    candidates = [row for row in rows
                  if path.startswith(row[0].rstrip('/'))]
    return max(candidates, key=lambda row: len(row[0])) if candidates else None


def _donor_remappings() -> list[tuple[str, str, Path]]:
    rows = []
    for path in REPO_CACHE.glob('*/*/remappings.txt'):
        repo = path.parent
        for prefix, target in _read_remappings(path):
            if (repo / target).is_dir():
                rows.append((prefix, target, repo))
    return rows


def _external_imports(source: Path, repo: Path) -> set[str]:
    found: set[str] = set()
    seen: set[Path] = set()
    repo_root = repo.resolve()

    def visit(path: Path) -> None:
        resolved = path.resolve()
        if resolved in seen or not resolved.is_file():
            return
        seen.add(resolved)
        text = resolved.read_text(encoding='utf-8', errors='replace')
        for imported in _import_paths(text):
            if imported.startswith('.'):
                visit((resolved.parent / imported).resolve())
            elif (repo_root / imported).is_file():
                visit((repo_root / imported).resolve())
            else:
                found.add(imported)

    visit(source)
    return found


def _ensure_dependencies(repo: Path, source: Path) -> list[str]:
    local = _read_remappings(repo / 'remappings.txt')
    donors = _donor_remappings()
    unresolved = []
    copied = []
    for imported in sorted(_external_imports(source, repo)):
        matched = _remapping_for(local, imported)
        if matched and (repo / matched[1]).is_dir():
            continue
        candidates = [(prefix, target, donor)
                      for prefix, target, donor in donors
                      if imported.startswith(prefix.rstrip('/'))
                      and repo != donor]
        if not candidates:
            unresolved.append(imported)
            continue
        candidates.sort(key=lambda row: (
            0 if row[2].parent.name == repo.parent.name else 1,
            _min_version(_extract_pragma(
                (row[2] / row[1] / 'IERC20.sol').read_text(
                    encoding='utf-8', errors='replace'))
                if (row[2] / row[1] / 'IERC20.sol').is_file() else '^0.8.0')
            or (99, 99, 99),
            str(row[2])))
        prefix, target, donor = candidates[0]
        dst = repo / target
        if not dst.is_dir() or not any(dst.iterdir()):
            dst.mkdir(parents=True, exist_ok=True)
            shutil.copytree(donor / target, dst, dirs_exist_ok=True,
                            ignore=shutil.ignore_patterns('.git'))
        if not matched:
            remappings = repo / 'remappings.txt'
            with remappings.open('a', encoding='utf-8') as handle:
                handle.write(f'{prefix}={target}\n')
            local.append((prefix, target))
        copied.append(target)
    return unresolved or []


def _ensure_foundry(repo: Path, source: Path) -> None:
    (repo / 'test').mkdir(parents=True, exist_ok=True)
    if (repo / 'foundry.toml').is_file():
        return
    relative = source.resolve().relative_to(repo.resolve())
    src_dir = relative.parts[0] if len(relative.parts) > 1 else 'src'
    (repo / 'foundry.toml').write_text(
        '[profile.default]\n'
        f'src = "{src_dir}"\n'
        'test = "test"\n'
        'libs = ["lib"]\n', encoding='utf-8')


def _local_source_graph(root: Path, repo: Path) -> list[Path]:
    repo_root = repo.resolve()
    found: set[Path] = set()

    def visit(path: Path) -> None:
        resolved = path.resolve()
        if resolved in found or not resolved.is_file():
            return
        if repo_root not in resolved.parents:
            return
        found.add(resolved)
        text = resolved.read_text(encoding='utf-8', errors='replace')
        for imported in _import_paths(text):
            if imported.startswith('.'):
                visit((resolved.parent / imported).resolve())

    visit(root)
    return sorted(found, key=lambda path: path.relative_to(repo_root).as_posix())


def _base_harness(case: dict, repo: Path) -> Path | None:
    name = ('Standalone_' + _safe(case['submission_uid']) + '_'
            + _safe(case['finding_key']) + '.t.sol')
    path = repo / 'test' / name
    return path if path.is_file() else None


def _wrapper_text(case: dict, pragma: str, import_path: str,
                  inheritance: str) -> tuple[str, str]:
    name = 'Neutral_' + _safe(case['submission_uid']) + '_' + _safe(case['finding_uid'])
    text = (
        '// SPDX-License-Identifier: MIT\n'
        f'pragma solidity {pragma};\n\n'
        f'import "{import_path}";\n\n'
        f'contract {name}{inheritance} {{\n'
        f'    function {TEST_NAME}() public {{\n'
        '        require(true, "neutral stage1 entrypoint");\n'
        '    }\n'
        '}\n')
    return name, text


def _materialize_project(case: dict, repo: Path, source: Path,
                         out: Path, use_base: bool = True
                         ) -> tuple[Path, Path, str, list[Path]]:
    project = out / str(case['case']) / 'foundry_project'
    if project.exists():
        shutil.rmtree(project)
    (project / 'src').mkdir(parents=True)
    (project / 'test').mkdir(parents=True)
    (project / 'foundry.toml').write_text(
        '[profile.default]\n'
        'src = "src"\n'
        'test = "test"\n'
        'libs = ["lib"]\n'
        'optimizer = true\n'
        'optimizer_runs = 200\n',
        encoding='utf-8')
    for name in ('lib', 'node_modules'):
        donor = repo / name
        if donor.is_dir():
            (project / name).symlink_to(donor.resolve(), target_is_directory=True)
    remappings = repo / 'remappings.txt'
    if remappings.is_file():
        shutil.copyfile(remappings, project / 'remappings.txt')

    base = _base_harness(case, repo) if use_base else None
    root = base or source
    graph = _local_source_graph(root, repo)
    for path in graph:
        relative = path.resolve().relative_to(repo.resolve())
        if relative.parts and relative.parts[0] in ('lib', 'node_modules'):
            continue
        destination = project / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, destination)

    if base is not None:
        base_text = base.read_text(encoding='utf-8', errors='replace')
        pragma = _extract_pragma(base_text)
        match = re.search(r'\bcontract\s+([A-Za-z0-9_]+)', base_text)
        import_path = './' + base.name
        inheritance = ' is ' + match.group(1) if match else ''
    else:
        pragma = _extract_pragma(
            source.read_text(encoding='utf-8', errors='replace'))
        relative = source.resolve().relative_to(repo.resolve()).as_posix()
        import_path = '../' + relative
        inheritance = ''
    return project, root, pragma, graph


def _run(cmd: list[str], cwd: Path, timeout: int) -> tuple[int, str]:
    env = os.environ.copy()
    env['FOUNDRY_OFFLINE'] = 'true'
    env.setdefault('GIT_TERMINAL_PROMPT', '0')
    env.setdefault('GIT_CONFIG_COUNT', '1')
    env.setdefault('GIT_CONFIG_KEY_0', 'protocol.allow')
    env.setdefault('GIT_CONFIG_VALUE_0', 'never')
    try:
        proc = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True,
                              timeout=timeout, env=env)
        return proc.returncode, (proc.stdout or '') + (proc.stderr or '')
    except subprocess.TimeoutExpired as exc:
        output = (exc.stdout or '') + (exc.stderr or '')
        if isinstance(output, bytes):
            output = output.decode('utf-8', 'replace')
        return 124, str(output)


@contextmanager
def _without_gitmodules(repo: Path):
    marker = repo / '.gitmodules'
    disabled = repo / '.gitmodules.neutral-disabled'
    moved = False
    if marker.is_file():
        if disabled.exists():
            disabled.unlink()
        marker.rename(disabled)
        moved = True
    try:
        yield
    finally:
        if moved:
            disabled.rename(marker)


def _passes(output: str) -> bool:
    return '[PASS]' in output and TEST_NAME in output


def _compatible(target_constraint: str, donor_text: str) -> bool:
    target_min = _min_version(target_constraint)
    donor_min = _min_version(_extract_pragma(donor_text))
    if target_min is None or donor_min is None:
        return True
    return donor_min <= target_min


def _fill_submodules(repo: Path) -> list[str]:
    gitmodules = repo / '.gitmodules'
    if not gitmodules.is_file():
        return []
    filled = []
    for line in gitmodules.read_text().splitlines():
        match = re.match(r'\s*path\s*=\s*(.+?)\s*$', line)
        if not match:
            continue
        target = repo / match.group(1)
        name = target.name
        sources = sorted(
            path for path in REPO_CACHE.glob(f'*/*/lib/{name}')
            if path.is_dir() and any(path.iterdir())
            and repo.resolve() not in path.resolve().parents)
        if not sources:
            continue
        if target.is_dir() and any(target.iterdir()):
            donor = sources[0]
            filled_count = 0
            for source_file in donor.rglob('*'):
                if not source_file.is_file():
                    continue
                relative = source_file.relative_to(donor)
                destination = target / relative
                if destination.is_file():
                    continue
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source_file, destination)
                filled_count += 1
            if filled_count:
                filled.append(str(target.relative_to(repo)) + f' (+{filled_count})')
            continue
        target.mkdir(parents=True, exist_ok=True)
        shutil.copytree(sources[0], target, dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns('.git'))
        filled.append(str(target.relative_to(repo)))
    return filled


def _missing_paths(output: str, root: Path) -> list[Path]:
    root = root.resolve()
    paths = []
    values = MISSING_RE.findall(output) + SOURCE_NOT_FOUND_RE.findall(output)
    for text in values:
        path = Path(text)
        if not path.is_absolute():
            path = root / path
        else:
            try:
                path.resolve().relative_to(root)
            except ValueError:
                try:
                    parts = path.resolve().relative_to(
                        REPO_CACHE.resolve()).parts
                except ValueError:
                    continue
                if len(parts) <= 2:
                    continue
                path = root / Path(*parts[2:])
        if root not in path.parents:
            continue
        if not path.is_file() and path not in paths:
            paths.append(path)
    return paths


def _donor_for(root: Path, missing: Path,
               target_constraint: str, repo: Path) -> Path | None:
    root = root.resolve()
    try:
        relative = missing.resolve().relative_to(root)
    except ValueError:
        parts = missing.resolve().relative_to(REPO_CACHE.resolve()).parts
        if len(parts) <= 2:
            return None
        relative = Path(*parts[2:])
    exact = [path for path in REPO_CACHE.glob(f'*/**/{relative.as_posix()}')
             if path.is_file() and root.resolve() not in path.parents
             and _compatible(target_constraint,
                             path.read_text(encoding='utf-8',
                                            errors='replace')[:5000])]
    if exact:
        return sorted(exact, key=lambda path: (
            0 if path.parent == repo else (
                1 if path.parent.parent.name == repo.parent.name else 2),
            _min_version(_extract_pragma(
                path.read_text(encoding='utf-8', errors='replace')[:5000]))
            or (99, 99, 99),
            str(path)))[0]
    by_name = [path for path in REPO_CACHE.glob(f'*/**/{missing.name}')
               if path.is_file() and root.resolve() not in path.parents]
    by_name = [path for path in by_name
               if _compatible(target_constraint,
                              path.read_text(encoding='utf-8',
                                             errors='replace')[:5000])]
    if not by_name:
        return None
    return sorted(by_name, key=lambda path: (
        0 if path.parent == repo else (
            1 if path.parent.parent.name == repo.parent.name else 2),
        len(path.parts), str(path)))[0]


def _repair_missing(root: Path, output: str,
                    target_constraint: str, repo: Path) -> list[str]:
    root = root.resolve()
    repaired = []
    for missing in _missing_paths(output, root):
        try:
            missing.resolve().relative_to(root)
        except ValueError:
            parts = missing.resolve().relative_to(REPO_CACHE.resolve()).parts
            if len(parts) <= 2:
                continue
            missing = root / Path(*parts[2:])
        donor = _donor_for(root, missing, target_constraint, repo)
        if donor is None:
            continue
        missing.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(donor, missing)
        repaired.append(str(missing.relative_to(root.resolve())))
    return repaired


def _attempt_case(case: dict, repo: Path, source: Path, out: Path,
                  timeout: int, use_base: bool, via_ir: bool = False) -> dict:
    row = {'case': str(case['case']), 'status': 'blocked', 'error': '',
           'artifact': None, 'route': 'base' if use_base else 'direct',
           'via_ir': via_ir}
    _ensure_foundry(repo, source)
    _fill_submodules(repo)
    unresolved = _ensure_dependencies(repo, source)
    project, root, pragma, graph = _materialize_project(
        case, repo, source, out, use_base=use_base)
    if root.name.startswith('Standalone_'):
        match = re.search(r'\bcontract\s+([A-Za-z0-9_]+)',
                          root.read_text(encoding='utf-8', errors='replace'))
        import_path = './' + root.name
        inheritance = ' is ' + match.group(1) if match else ''
    else:
        import_path = '../' + root.resolve().relative_to(
            repo.resolve()).as_posix()
        inheritance = ''
    name, harness = _wrapper_text(case, pragma, import_path, inheritance)
    harness_path = project / 'test' / f'{name}.t.sol'
    harness_path.write_text(harness, encoding='utf-8')
    compiler_flags = ['--via-ir'] if via_ir else []

    repaired = []
    for _ in range(5):
        code, output = _run(['forge', 'test', '--offline'] + compiler_flags + [
                             '--match-path', f'test/{harness_path.name}',
                             '--match-test', TEST_NAME],
                            project, timeout)
        fixed = _repair_missing(project, output, pragma, repo)
        if not fixed:
            break
        repaired.extend(fixed)
    row['repaired_sources'] = repaired
    row['source_files'] = [path.relative_to(repo.resolve()).as_posix()
                           for path in graph]
    row['entry_code'] = code
    row['entry_output'] = output[-6000:]
    if code != 0 or not _passes(output):
        row['error'] = 'unresolved_imports' if unresolved else 'entry_test_failed'
        if unresolved:
            row['unresolved'] = unresolved
        return row

    code, output = _run(['forge', 'flatten', f'test/{harness_path.name}'],
                        project, timeout)
    if code != 0:
        row['error'] = 'flatten_failed'
        row['flatten_output'] = output[-2000:]
        return row
    flat_path = project / 'test' / f'{name}.flattened.t.sol'
    flat_path.write_text(output, encoding='utf-8')

    code, output = _run(['forge', 'test', '--offline'] + compiler_flags + [
                         '--match-path', f'test/{flat_path.name}',
                         '--match-test', TEST_NAME],
                        project, timeout)
    if code != 0 or not _passes(output):
        row['error'] = 'flattened_test_failed'
        row['flattened_output'] = output[-2000:]
        return row

    case_out = out / str(case['case'])
    case_out.mkdir(parents=True, exist_ok=True)
    artifact = case_out / 'contract.flattened.t.sol'
    shutil.copyfile(flat_path, artifact)
    shutil.copyfile(harness_path, case_out / 'entrypoint.t.sol')
    row.update({
        'status': 'flatten_pass',
        'error': '',
        'artifact': str(artifact.resolve()),
        'artifact_sha256': _sha256(artifact),
        'harness_sha256': _sha256(harness_path),
    })
    return row


def process_case(case: dict, out: Path, timeout: int) -> dict:
    repo = _repo_root(case)
    source = Path(case['source_path'])
    if repo is None or not source.is_file():
        return {'case': str(case['case']), 'status': 'blocked',
                'error': 'source_or_repo_missing', 'artifact': None}
    row = _attempt_case(case, repo, source, out, timeout, use_base=True)
    if row['status'] == 'flatten_pass':
        return row
    fallback = _attempt_case(case, repo, source, out, timeout, use_base=False)
    if fallback['status'] == 'flatten_pass':
        return fallback
    row['fallback_error'] = fallback.get('error')
    outputs = ' '.join((row.get('entry_output') or '',
                        fallback.get('entry_output') or '',
                        row.get('flattened_output') or '',
                        fallback.get('flattened_output') or ''))
    if 'Stack too deep' in outputs:
        via_base = _attempt_case(case, repo, source, out, timeout,
                                 use_base=True, via_ir=True)
        if via_base['status'] == 'flatten_pass':
            return via_base
        via_fallback = _attempt_case(case, repo, source, out, timeout,
                                     use_base=False, via_ir=True)
        if via_fallback['status'] == 'flatten_pass':
            return via_fallback
        row['via_ir_error'] = via_base.get('error')
        row['via_ir_fallback_error'] = via_fallback.get('error')
    return row


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cases-file', type=Path, default=CASES_DEFAULT)
    parser.add_argument('--out-dir', type=Path, default=OUT_DEFAULT)
    parser.add_argument('--case', default=None,
                        help='optional comma-separated case ids for debugging')
    parser.add_argument('--timeout', type=int, default=600)
    args = parser.parse_args(argv)

    cases = json.loads(args.cases_file.read_text())['cases']
    if args.case:
        wanted = set(args.case.split(','))
        cases = [row for row in cases if str(row['case']) in wanted]
    out = args.out_dir
    out.mkdir(parents=True, exist_ok=True)

    rows = []
    for index, case in enumerate(cases, 1):
        row = process_case(case, out, args.timeout)
        rows.append(row)
        print(f'[{index}/{len(cases)}] {row["case"]}: '
              f'{row["status"]} {row["error"]}', flush=True)

    summary = {'total': len(rows)}
    for row in rows:
        summary[row['status']] = summary.get(row['status'], 0) + 1
    (out / 'neutral_entrypoint_summary.json').write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + '\n')
    (out / 'neutral_entrypoint_status.json').write_text(
        json.dumps({'schema_version': 'neutral-entrypoint/1',
                    'cases_file': str(args.cases_file.resolve()),
                    'rows': rows}, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
