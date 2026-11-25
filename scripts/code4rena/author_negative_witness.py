#!/usr/bin/env python3
"""Author locally passing negative-witness harnesses for frozen negative cases.

A judge-invalid report can still exercise a real code path.  Stage 3 needs a
locally runnable test that witnesses that path and asserts the actual safe
outcome; the neutral compile-only entrypoint cannot supply those queries.
This script keeps the frozen case list and labels unchanged and only authors a
passing test on the current source.  Cases that cannot be authored remain
unresolved and are never relabelled or dropped.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parents[1]
sys.path.insert(0, str(ROOT / 'tools' / 'stage3'))

import neutral_entrypoint_pipeline as base
from lib import llm, path_config
from lib.solidity_scan import (_contract_spans, clean_source,
                               poc_test_function)

SUBMISSIONS = (ROOT / 'tools' / 'stage3' / 'evaluation' / 'metrics'
               / 'official_negative_submissions_20261121.json')
CASES_DEFAULT = (ROOT / 'tools' / 'stage3' / 'evaluation' / 'metrics'
                 / 'official_negative_stage1_cases_20261121.json')
OUT_DEFAULT = (ROOT / 'c4_pipeline_output'
               / 'official_negative_witness_20261121')
OUT_DEFAULT = path_config.c4_output_root() / 'official_negative_witness_20261121'
TEST_NAME = 'test_negative_witness'
FORGE_STD_CANDIDATES = path_config.forge_std_candidates()


def _reports() -> dict[str, dict]:
    return {str(row.get('uid')): row
            for row in json.loads(SUBMISSIONS.read_text())}


def _body_from_model(case: dict, report: dict, source: str, base_test: str,
                     base_contract: str, error_hint: str,
                     flat_mode: bool = False) -> str | None:
    system = (
        'You write the body of a Foundry test function for an official '
        'Code4rena finding that the judges marked INVALID. The test must PASS '
        'against the supplied current source. The generated function will be '
        'placed inside a subclass of the supplied base test contract. Prefer '
        'reusing that contract\'s inherited state variables, setUp state and '
        'internal helpers. Declare any additional local variables yourself. '
        'Every identifier you reference must be declared in the base test '
        'contract, imported by it, declared locally, or a Solidity/forge-std '
        'builtin. Execute the alleged setup and transition faithfully, then '
        'end with assertTrue(true) to record that the path completed. Do not '
        'guess quantitative safe outcomes: stage 3 injects its own invariant '
        'and effect probes and decides safety from those probes. Never assert '
        'that the reported bug occurs and never use vm.expectRevert. Use '
        'forge-std cheatcodes only when they are available through the base '
        'contract. Return ONLY a JSON object with one key "body" whose value '
        'is Solidity statements for the test function body. No markdown, no '
        'function signature, no contract wrapper.')
    if flat_mode:
        system += (
            ' The supplied source is one self-contained flattened Solidity '
            'file. If base_contract is "Test", instantiate the target '
            'contracts declared in that file directly; do not import other '
            'files or assume an external library path. Do not replace the '
            'alleged path with a pure arithmetic model or placeholder '
            'computation; the body must deploy at least one concrete contract '
            'declared in the flattened source with `new Contract(...)`, then '
            'call that instance.')
    text = str(report.get('body') or '')[:12000]
    user = json.dumps({
        'case': str(case.get('case') or ''),
        'title': str(report.get('title') or case.get('title') or ''),
        'finding_report': text,
        'target_source': source[:24000],
        'base_contract': base_contract,
        'base_test_contract_source': base_test[:30000],
        'previous_failure': error_hint[-6000:],
        'test_function_name': TEST_NAME,
    }, ensure_ascii=False)
    try:
        result = llm.chat_json(system, user, max_tokens=8000)
    except Exception:
        return None
    body = result.get('body')
    if not isinstance(body, str) or not body.strip():
        return None
    return body.strip()


def _compiler_errors(output: str) -> str:
    lines = (output or '').splitlines()
    selected: list[str] = []
    for index, line in enumerate(lines):
        if 'Error (' in line or line.startswith('Error:'):
            selected.extend(lines[index:index + 7])
    return '\n'.join(selected[-120:])


def _uses_target_contract(body: str, flat_source: str) -> bool:
    """Require a real contract deployment when no base PoC contract exists."""
    ignored = {'Test', 'Vm', 'StdAssertions', 'StdChains', 'StdCheats',
               'StdInvariant', 'StdUtils', 'TestBase', 'console2'}
    names = set(re.findall(r'\bcontract\s+([A-Za-z_]\w*)', flat_source))
    names -= ignored
    for name in names:
        if re.search(rf'\bnew\s+{re.escape(name)}\s*\(', body):
            return True
    return False


def _passes(output: str) -> bool:
    return '[PASS]' in output and TEST_NAME in output


def _repair_dependencies(project: Path, output: str, pragma: str, repo: Path,
                        protected: dict[Path, str],
                        harness_copy: Path | None = None) -> list[str]:
    repaired = base._repair_missing(project, output, pragma, repo)
    if harness_copy is not None:
        refreshed = _expose_state(_repair_relative_imports(
            harness_copy.read_text(encoding='utf-8', errors='replace'),
            harness_copy, project))
        harness_copy.write_text(refreshed, encoding='utf-8')
        protected[harness_copy] = refreshed
    for path, text in protected.items():
        path.write_text(text, encoding='utf-8')
    return repaired


def _first_contract(source: str) -> str | None:
    match = re.search(r'\bcontract\s+([A-Za-z_$][A-Za-z0-9_$]*)', source)
    return match.group(1) if match else None


def _test_contract(source: str) -> str | None:
    """Pick the harness contract that actually carries the PoC setUp/test."""
    clean = clean_source(source)
    spans = _contract_spans(clean)
    candidates = []
    for contract, (open_idx, close_idx) in spans.items():
        body = clean[open_idx + 1:close_idx]
        has_setup = bool(re.search(r'\bfunction\s+setUp\s*\(', body))
        has_test = bool(re.search(r'\bfunction\s+test[A-Za-z0-9_]*\s*\(', body))
        if has_setup or has_test:
            candidates.append((has_setup and has_test, contract))
    if candidates:
        return max(candidates)[1]
    return _first_contract(source)


def _first_test_body(source: str, contract: str | None) -> str | None:
    clean = clean_source(source)
    span = _contract_spans(clean).get(contract) if contract else None
    if span is None:
        return None
    body = clean[span[0] + 1:span[1]]
    match = re.search(
        r'\bfunction\s+test[A-Za-z0-9_]*\s*\([^)]*\)[^{]*\{', body)
    if match is None:
        return None
    open_idx = match.end() - 1
    depth = 1
    index = open_idx + 1
    while index < len(body) and depth:
        if body[index] == '{':
            depth += 1
        elif body[index] == '}':
            depth -= 1
        index += 1
    return body[open_idx + 1:index - 1].strip()


def _expose_state(source: str) -> str:
    return re.sub(r'\bprivate\b', 'internal', source)


def _repair_relative_imports(source: str, harness_path: Path,
                             project: Path) -> str:
    pattern = re.compile(r'(?P<prefix>\bfrom\s+|\bimport\s+)["\']'
                         r'(?P<path>\.[^"\']+)["\']')

    def replace(match: re.Match) -> str:
        raw = match.group('path')
        if (harness_path.parent / raw).resolve().is_file():
            return match.group(0)
        parts = Path(raw).parts
        while parts and parts[0] == '..':
            parts = parts[1:]
            candidate = project.joinpath(*parts)
            if candidate.is_file():
                repaired = os.path.relpath(candidate.resolve(),
                                           harness_path.parent.resolve())
                return (match.group('prefix') + '"'
                        + Path(repaired).as_posix() + '"')
        return match.group(0)

    return pattern.sub(replace, source)


def _wrapper(case: dict, pragma: str, import_path: str, inheritance: str,
             base_contract: bool, source: str, body: str) -> tuple[str, str]:
    name = 'NegWitness_' + base._safe(case['submission_uid'])
    if base_contract:
        bases = re.sub(r'^\s*is\s+', '', inheritance).strip()
        imports = f'import "{import_path}";\n'
    else:
        source_contract = (re.sub(r'^\s*is\s+', '', inheritance).strip()
                           if inheritance else _first_contract(source))
        if not source_contract:
            raise ValueError('target contract not found')
        bases = 'Test, ' + source_contract
        imports = ('import "forge-std/Test.sol";\n'
                   f'import "{import_path}";\n')
    text = (
        '// SPDX-License-Identifier: MIT\n'
        f'pragma solidity {pragma};\n\n'
        + imports + '\n'
        f'contract {name} is {bases} {{\n'
        f'    function {TEST_NAME}() public {{\n'
        + '\n'.join('        ' + line for line in body.splitlines()) + '\n'
        '    }\n'
        '}\n')
    return name, text


def _foundry_project(path: Path, case: dict | None = None) -> Path:
    if path.exists():
        shutil.rmtree(path)
    (path / 'test').mkdir(parents=True)
    (path / 'foundry.toml').write_text(
        '[profile.default]\n'
        'src = "src"\n'
        'test = "test"\n'
        'libs = ["lib"]\n'
        'optimizer = true\n'
        'optimizer_runs = 200\n',
        encoding='utf-8')
    forge_std = None
    if case is not None:
        repo = base._repo_root(case)
        if repo is not None and (repo / 'lib' / 'forge-std' / 'src' / 'Test.sol').is_file():
            forge_std = repo / 'lib' / 'forge-std'
    if forge_std is None:
        forge_std = next((candidate for candidate in FORGE_STD_CANDIDATES
                          if (candidate / 'src' / 'Test.sol').is_file()), None)
    if forge_std is not None:
        lib = path / 'lib'
        lib.mkdir(exist_ok=True)
        (lib / 'forge-std').symlink_to(forge_std.resolve(),
                                      target_is_directory=True)
    return path


def _author_from_flat_base(case: dict, report: dict, flat_base_root: Path,
                           out: Path, timeout: int, via_ir: bool = False,
                           allow_via_ir_fallback: bool = True) -> dict | None:
    """Author a witness from a stage-1 verified flattened slice.

    The repository PoC harness can fail to compile for reasons unrelated to
    the finding (wrong pragma, missing submodule, stale enum member).  A
    neutral flatten slice has already passed forge test/flatten/retest, so it
    is a safer base for the witness wrapper.  Nothing about the frozen case,
    label or stage-2 contract changes here.
    """
    case_id = str(case['case'])
    flat_path = Path(flat_base_root) / case_id / 'contract.flattened.t.sol'
    if not flat_path.is_file():
        return None
    flat_source = flat_path.read_text(encoding='utf-8', errors='replace')
    pragma_match = re.search(r'pragma\s+solidity\s+([^;]+);', flat_source)
    if pragma_match is None:
        return None
    pragma = pragma_match.group(1).strip()
    picked = poc_test_function(flat_source, ignore_neutral=True)
    base_contract = (picked[0] if picked
                     and not picked[0].startswith('Neutral_') else None)
    deterministic_body = (_first_test_body(flat_source, base_contract)
                          if base_contract else None)

    case_out = out / case_id
    project = _foundry_project(case_out / 'flat_witness_project', case)
    (project / 'test' / 'Base.sol').write_text(flat_source, encoding='utf-8')
    name = 'NegWitness_' + base._safe(case['submission_uid'])
    compiler_flags = ['--via-ir'] if via_ir else []
    error_hint = ''
    harness_path = project / 'test' / f'{name}.t.sol'
    body = None
    output = ''
    code = 1
    last_rejection = ''
    for attempt in range(4):
        if attempt == 0 and deterministic_body:
            body = deterministic_body
        else:
            body = _body_from_model(
                case, report, flat_source, flat_source,
                base_contract or 'Test', error_hint, flat_mode=True)
        if body is None:
            return {'case': case_id, 'status': 'blocked',
                    'error': 'flat_authoring_failed',
                    'route': 'negative_witness', 'via_ir': via_ir}
        if (base_contract in (None, 'Test')
                and not _uses_target_contract(body, flat_source)):
            error_hint = (
                'The previous body did not deploy a concrete contract. Use '
                '`new Contract(...)` for a contract declared in the flattened '
                'source and call that instance; no placeholders or pure '
                'arithmetic models.')
            last_rejection = error_hint
            continue
        bases = base_contract or 'Test'
        forge_std_import = ''
        if not re.search(r'\b(?:abstract\s+)?contract\s+Test\b', flat_source):
            forge_std_import = 'import "forge-std/Test.sol";\n'
        harness = (
            '// SPDX-License-Identifier: MIT\n'
            f'pragma solidity {pragma};\n\n'
            + forge_std_import + 'import "./Base.sol";\n\n'
            f'contract {name} is {bases} {{\n'
            f'    function {TEST_NAME}() public {{\n'
            + '\n'.join('        ' + line for line in body.splitlines()) + '\n'
            '    }\n'
            '}\n')
        harness_path.write_text(harness, encoding='utf-8')
        code, output = base._run(
            ['forge', 'test', '--offline'] + compiler_flags + [
                '--match-path', f'test/{harness_path.name}',
                '--match-test', TEST_NAME], project, timeout)
        if code == 0 and _passes(output):
            break
        error_hint = _compiler_errors(output)
    if code != 0 or not _passes(output):
        row = {'case': case_id, 'status': 'blocked',
               'error': ('flat_no_contract_call' if last_rejection and not output
                         else 'flat_entry_test_failed'),
               'route': 'negative_witness', 'via_ir': via_ir,
               'entry_output': (last_rejection if not output
                                else output[-6000:])}
        if (allow_via_ir_fallback and not via_ir
                and 'stack too deep' in output.lower()):
            return _author_from_flat_base(case, report, flat_base_root,
                                          out, timeout, True, False)
        return row

    code, flatten_output = base._run(
        ['forge', 'flatten', f'test/{harness_path.name}'], project, timeout)
    if code != 0:
        return {'case': case_id, 'status': 'blocked',
                'error': 'flat_flatten_failed',
                'route': 'negative_witness', 'via_ir': via_ir,
                'flatten_output': flatten_output[-2000:]}
    verify = _foundry_project(case_out / 'flat_witness_verify')
    flattened_path = verify / 'test' / f'{name}.flattened.t.sol'
    flattened_path.write_text(flatten_output, encoding='utf-8')
    code, output = base._run(
        ['forge', 'test', '--offline'] + compiler_flags + [
            '--match-path', f'test/{flattened_path.name}',
            '--match-test', TEST_NAME], verify, timeout)
    if code != 0 or not _passes(output):
        return {'case': case_id, 'status': 'blocked',
                'error': 'flat_flattened_test_failed',
                'route': 'negative_witness', 'via_ir': via_ir,
                'flattened_output': output[-6000:]}

    case_out.mkdir(parents=True, exist_ok=True)
    artifact = case_out / 'contract.flattened.t.sol'
    artifact.write_text(flatten_output, encoding='utf-8')
    shutil.copyfile(harness_path, case_out / 'entrypoint.t.sol')
    (case_out / 'harness-manifest.json').write_text(json.dumps({
        'schema_version': 'stage1-harness-manifest/1',
        'case': case_id,
        'route': 'negative_witness',
        'test_entrypoint': False,
        'exploit_test': TEST_NAME,
        'forge_command': f'forge test --match-test {TEST_NAME}',
        'compile_status': 'verified',
        'compile_hash': base._sha256(artifact),
        'source_files': [str(flat_path)],
        'fixed_block': False,
        'fork_block': None,
        'external_imports': [],
        'dependencies_vendored': True,
        'local_runnable': True,
        'blockers': [],
    }, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return {'case': case_id, 'status': 'flatten_pass',
            'artifact': str(artifact.resolve()),
            'route': 'negative_witness', 'via_ir': via_ir,
            'author_route': 'verified_flatten_base',
            'flat_base': str(flat_path.resolve()),
            'base_contract': base_contract or 'Test',
            'artifact_sha256': base._sha256(artifact),
            'harness_sha256': base._sha256(harness_path)}


def process_case(case: dict, report: dict, out: Path, timeout: int,
                 via_ir: bool = False,
                 allow_via_ir_fallback: bool = True,
                 flat_base_root: Path | None = None) -> dict:
    row = {'case': str(case['case']), 'status': 'blocked', 'error': '',
           'artifact': None, 'route': 'negative_witness', 'via_ir': via_ir}
    repo = base._repo_root(case)
    source_path = Path(case['source_path'])
    if repo is None or not source_path.is_file() or report is None:
        row['error'] = 'missing_repo_or_report'
        return row
    base._ensure_foundry(repo, source_path)
    base._fill_submodules(repo)
    unresolved = base._ensure_dependencies(repo, source_path)
    if unresolved:
        row['error'] = 'unresolved_imports'
        row['unresolved'] = unresolved
        return row
    project, root, pragma, graph = base._materialize_project(
        case, repo, source_path, out)
    if root.name.startswith('Standalone_'):
        harness_copy = project / 'test' / root.name
        harness_text = _expose_state(_repair_relative_imports(
            harness_copy.read_text(encoding='utf-8', errors='replace'),
            harness_copy, project))
        harness_copy.write_text(harness_text, encoding='utf-8')
        base_contract = _test_contract(harness_text)
        row['base_contract'] = base_contract
        row['relative_import_repaired'] = '../../mocks/' not in harness_text
        import_path = './' + root.name
        inheritance = ' is ' + base_contract if base_contract else ''
        base_contract = True
    else:
        base_contract = None
        import_path = '../' + root.resolve().relative_to(repo.resolve()).as_posix()
        inheritance = ''
        base_contract = False
    source = '\n'.join(path.read_text(encoding='utf-8', errors='replace')
                       for path in graph if path.is_file())
    base_test = root.read_text(encoding='utf-8', errors='replace') if root.is_file() else ''
    if root.name.startswith('Standalone_'):
        base_test = (project / 'test' / root.name).read_text(
            encoding='utf-8', errors='replace')
    deterministic_body = _first_test_body(
        base_test, inheritance.replace(' is ', '', 1).strip()
        if inheritance else None)
    compiler_flags = ['--via-ir'] if via_ir else []
    error_hint = ''
    harness_path = None
    harness_name = None
    code = 1
    output = ''
    for attempt in range(4):
        if attempt == 0 and deterministic_body:
            body = deterministic_body
        else:
            body = _body_from_model(
                case, report, source, base_test,
                inheritance.replace(' is ', '', 1).strip()
                if inheritance else 'Test', error_hint)
        if body is None:
            row['error'] = 'authoring_failed'
            return row
        try:
            harness_name, harness = _wrapper(
                case, pragma, import_path, inheritance, base_contract,
                source, body)
        except ValueError as exc:
            row['error'] = 'target_contract_not_found'
            row['detail'] = str(exc)
            return row
        harness_path = project / 'test' / f'{harness_name}.t.sol'
        harness_path.write_text(harness, encoding='utf-8')
        protected = {harness_path: harness}
        if root.name.startswith('Standalone_'):
            protected[project / 'test' / root.name] = harness_text
        for _ in range(3):
            code, output = base._run(
                ['forge', 'test', '--offline'] + compiler_flags + [
                    '--match-path', f'test/{harness_path.name}',
                    '--match-test', TEST_NAME], project, timeout)
            repaired = _repair_dependencies(
                project, output, pragma, repo, protected,
                harness_copy if root.name.startswith('Standalone_') else None)
            if not repaired:
                break
        row['author_attempts'] = attempt + 1
        if code == 0 and _passes(output):
            break
        error_hint = _compiler_errors(output)
    if code != 0 or not _passes(output) or harness_path is None:
        row['error'] = 'entry_test_failed'
        row['entry_output'] = output[-6000:]
        if (allow_via_ir_fallback and not via_ir
                and 'stack too deep' in output.lower()):
            return process_case(case, report, out, timeout, True, False,
                                flat_base_root)
        if flat_base_root is not None:
            flat_row = _author_from_flat_base(
                case, report, flat_base_root, out, timeout, via_ir,
                allow_via_ir_fallback)
            if flat_row is not None and flat_row.get('status') == 'flatten_pass':
                return flat_row
            row['flat_fallback_error'] = (
                (flat_row or {}).get('error') or 'unavailable')
        return row

    if root.name.startswith('Standalone_'):
        harness_copy = project / 'test' / root.name
        harness_text = _expose_state(_repair_relative_imports(
            harness_copy.read_text(encoding='utf-8', errors='replace'),
            harness_copy, project))
        harness_copy.write_text(harness_text, encoding='utf-8')
        row['relative_import_repaired'] = '../../mocks/' not in harness_text
    code, output = base._run(
        ['forge', 'flatten', f'test/{harness_path.name}'], project, timeout)
    if code != 0:
        row['error'] = 'flatten_failed'
        row['flatten_output'] = output[-2000:]
        return row
    flat_path = project / 'test' / f'{harness_name}.flattened.t.sol'
    flat_path.write_text(output, encoding='utf-8')
    code, output = base._run(
        ['forge', 'test', '--offline'] + compiler_flags + [
            '--match-path', f'test/{flat_path.name}',
            '--match-test', TEST_NAME], project, timeout)
    if code != 0 or not _passes(output):
        row['error'] = 'flattened_test_failed'
        row['flattened_output'] = output[-6000:]
        return row

    case_out = out / str(case['case'])
    case_out.mkdir(parents=True, exist_ok=True)
    artifact = case_out / 'contract.flattened.t.sol'
    shutil.copyfile(flat_path, artifact)
    shutil.copyfile(harness_path, case_out / 'entrypoint.t.sol')
    (case_out / 'harness-manifest.json').write_text(json.dumps({
        'schema_version': 'stage1-harness-manifest/1',
        'case': str(case['case']),
        'route': 'negative_witness',
        'test_entrypoint': False,
        'exploit_test': TEST_NAME,
        'forge_command': f'forge test --match-test {TEST_NAME}',
        'compile_status': 'verified',
        'compile_hash': base._sha256(artifact),
        'source_files': [path.relative_to(repo.resolve()).as_posix()
                         for path in graph],
        'fixed_block': False,
        'fork_block': None,
        'external_imports': [],
        'dependencies_vendored': True,
        'local_runnable': True,
        'blockers': [],
    }, ensure_ascii=False, indent=2) + '\n')
    row.update({'status': 'flatten_pass', 'artifact': str(artifact.resolve()),
                'artifact_sha256': base._sha256(artifact),
                'harness_sha256': base._sha256(harness_path)})
    return row


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cases-file', type=Path, default=CASES_DEFAULT)
    parser.add_argument('--out', type=Path, default=OUT_DEFAULT)
    parser.add_argument('--timeout', type=int, default=600)
    parser.add_argument('--via-ir', action='store_true')
    parser.add_argument('--case', action='append', default=[],
                        help='case id to author; repeatable')
    parser.add_argument('--resume', action='store_true',
                        help='reuse cases already recorded with a final status')
    parser.add_argument('--flat-base-root', type=Path, default=None,
                        help='fallback to verified neutral flatten artifacts')
    parser.add_argument('--retry-blocked', action='store_true',
                        help='re-attempt blocked cases with --flat-base-root')
    parser.add_argument('--flat-only', action='store_true',
                        help='only run the verified-flatten witness fallback')
    args = parser.parse_args(argv)

    payload = json.loads(args.cases_file.read_text())
    cases = payload['cases']
    if args.case:
        wanted = set(args.case)
        cases = [row for row in cases if str(row['case']) in wanted]
    reports = _reports()
    args.out.mkdir(parents=True, exist_ok=True)
    status_path = args.out / 'status.json'
    existing = {}
    if args.resume and status_path.is_file():
        try:
            previous = json.loads(status_path.read_text(encoding='utf-8'))
            existing = {str(row.get('case')): row for row in
                        previous.get('rows', [])
                        if row.get('status') in {'flatten_pass', 'blocked'}}
        except (OSError, ValueError):
            existing = {}
    rows = []
    for case in cases:
        case_id = str(case['case'])
        report = reports.get(str(case.get('submission_uid')))
        if args.flat_only:
            if args.flat_base_root is None:
                raise SystemExit('--flat-only requires --flat-base-root')
            row = _author_from_flat_base(
                case, report, args.flat_base_root, args.out, args.timeout,
                args.via_ir)
            if row is not None:
                rows.append(row)
                print(json.dumps(row, ensure_ascii=False), flush=True)
                status_path.write_text(json.dumps({
                    'schema_version': 'negative-witness-status/1',
                    'rows': rows,
                }, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
            continue
        if case_id in existing:
            previous = existing[case_id]
            if (args.flat_base_root and args.retry_blocked
                    and previous.get('status') == 'blocked'):
                flat_row = _author_from_flat_base(
                    case, report, args.flat_base_root, args.out, args.timeout,
                    args.via_ir)
                if flat_row is not None and flat_row.get('status') == \
                        'flatten_pass':
                    rows.append(flat_row)
                    print(json.dumps(flat_row, ensure_ascii=False), flush=True)
                else:
                    rows.append(previous)
            else:
                rows.append(existing[case_id])
            continue
        row = process_case(case, report, args.out, args.timeout, args.via_ir,
                           flat_base_root=args.flat_base_root)
        rows.append(row)
        print(json.dumps(row, ensure_ascii=False), flush=True)
        status_path.write_text(json.dumps({
            'schema_version': 'negative-witness-status/1',
            'rows': rows,
        }, ensure_ascii=False, indent=2) + '\n')
    summary = {
        'requested': len(rows),
        'flatten_pass': sum(1 for row in rows if row['status'] == 'flatten_pass'),
        'blocked': sum(1 for row in rows if row['status'] != 'flatten_pass'),
    }
    (args.out / 'summary.json').write_text(
        json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary, indent=2), flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
