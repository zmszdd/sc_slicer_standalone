#!/usr/bin/env python3
"""Repo-native replication of the standalone-PoC + flatten-pass pipeline.

The dev set (``/root/poc_repro_work/verified_flatten_pass_1568_exact_cases``)
was produced by an external pipeline that, per code4rena submission:

  1. authored/collected a ``Standalone_<submission>_<finding>.t.sol`` entry
     whose target test passes in the project's Foundry root (``entry_pass``);
  2. ran ``forge flatten`` on that entry;
  3. ran the flattened file's target test and required it to ``[PASS]``
     (``flatten_pass``).

This script reproduces that deterministic orchestration inside the repo and
emits the same ``result.json`` / status-CSV schema so the blind set gets the
same treatment as the dev set.

PoC authoring has two tiers:

  * deterministic wrapper: when the submission PoC is a bare ``function
    test_*()`` body without a ``contract ... is Test`` harness, this script
    borrows the repo's closest existing Foundry test contract (imports, state
    variables, ``setUp``) and embeds the PoC body into a renamed
    ``Standalone_<submission>_<finding>`` contract;

  * LLM authoring (``--author``): for diff/snippet submissions the submission
    text, the target source file and the repo's closest existing test are sent
    to DeepSeek (same key as stage-2/3) which returns a self-contained
    ``Standalone_*`` contract.

Usage:
    python standalone_poc_pipeline.py --case <case-id> [--dry-run] [--author]
    python standalone_poc_pipeline.py --all --dry-run
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass, asdict
from pathlib import Path

from findings_lookup import matching_finding

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parents[1]
BLIND = ROOT / 'tools' / 'stage3' / 'evaluation' / 'metrics' / 'blind_set.json'
REPORTS = ROOT / 'code4rena_reports'
DEFAULT_OUT = ROOT / 'c4_pipeline_output' / 'standalone_poc_batch'

_CODE_BLOCK_RE = re.compile(r'```(?:solidity|sol|js)?\s*\n(.*?)```', re.S | re.I)
_RPC_RE = re.compile(r'(?:_?vm)\.(?:rpc|createSelectFork|createFork|rollFork|'
                     r'rollForkId|makePersistent|selectFork)\s*\(')
_ENV_RE = re.compile(r'(?:_?vm)\.env(?:Uint|Int|String|Bytes32?|Address|Bool|'
                     r'Uint256)\s*\(')
_TEST_FN_RE = re.compile(r'\bfunction\s+(test[A-Za-z0-9_]*)\s*\(')
_TEST_CONTRACT_RE = re.compile(
    r'\b(?:abstract\s+)?contract\s+([A-Za-z0-9_]+)\s+is\s+[A-Za-z0-9_,\s]*'
    r'(?:DSTest|Test)\b')
_HARNESS_RE = re.compile(r'(?:forge-std/Test\.sol|\bis\s+(?:DSTest|Test)\b)')
_SRC_IMPORT_RE = re.compile(r'from\s+"src/|import\s+"src/')
_TEST_IMPORT_RE = re.compile(r'from\s+"test/|import\s+"test/|'
                             r'from\s+"\.\./|import\s+"\.\./')
_IDENT_RE = re.compile(r'\b[a-zA-Z_][a-zA-Z0-9_]{2,}\b')

STATUS_PASS = 'flatten_pass'
STATUS_ENTRY_ONLY = 'entry_pass_only'
STATUS_FAILED = 'failed'
STATUS_BLOCKED = 'blocked'

AUTHOR_TIMEOUT = 300

FORGE_STD_SRC = ROOT / 'c4_pipeline_output' / '_github_repos_light' / 'code-423n4__2025-06-panoptic__72836c0d5fc8a46052a5dce27cd09c299b7f6edb' / 'lib' / 'forge-std'


def _ensure_forge_std(repo: Path) -> bool:
    if (repo / 'lib' / 'forge-std' / 'src' / 'Test.sol').is_file():
        return True
    src = FORGE_STD_SRC
    if not (src / 'src' / 'Test.sol').is_file():
        return False
    import shutil
    dst = repo / 'lib' / 'forge-std'
    try:
        shutil.copytree(src, dst, dirs_exist_ok=True)
    except (OSError, shutil.Error):
        return False
    return (dst / 'src' / 'Test.sol').is_file()


@dataclass
class CaseOutcome:
    key: str
    project: str
    submission_uid: str
    finding_uid: str
    status: str
    error: str = ''


def _load_blind() -> dict:
    return json.loads(BLIND.read_text())


def _finding(case: dict) -> dict | None:
    return matching_finding(case)


def _poc_blocks(finding: dict) -> list[str]:
    for field in ('proof_of_concept', 'proofOfConcept', 'body'):
        text = finding.get(field) or ''
        blocks = [m.group(1).strip() for m in _CODE_BLOCK_RE.finditer(text)]
        runnable = [b for b in blocks if _TEST_FN_RE.search(b)]
        if runnable:
            return runnable
    text = ((finding.get('proof_of_concept') or '') + '\n'
            + (finding.get('proofOfConcept') or '') + '\n'
            + (finding.get('body') or ''))
    return [m.group(1).strip() for m in _CODE_BLOCK_RE.finditer(text)]


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


def _is_foundry(repo: Path | None) -> bool:
    return bool(repo and (repo / 'foundry.toml').is_file())


def _repo_test_forks(repo: Path | None) -> bool:
    if repo is None or not (repo / 'test').is_dir():
        return False
    for sol in (repo / 'test').rglob('*.sol'):
        try:
            if _RPC_RE.search(sol.read_text()):
                return True
        except OSError:
            continue
    return False


def _classify(case: dict, blocks: list[str]) -> dict:
    if not blocks:
        return {'action': 'no_poc_code', 'deps': [], 'has_test': False,
                'is_harness': False, 'blocks': 0}
    merged = '\n'.join(blocks)
    deps: list[str] = []
    if _RPC_RE.search(merged):
        deps.append('fork_rpc')
    if _ENV_RE.search(merged):
        deps.append('env_dep')
    if _TEST_IMPORT_RE.search(merged):
        deps.append('repo_test_deps')
    if _SRC_IMPORT_RE.search(merged):
        deps.append('repo_src_deps')
    has_test = bool(_TEST_FN_RE.search(merged))
    is_harness = bool(_HARNESS_RE.search(merged))
    if not has_test:
        action = 'snippet_only'
    elif 'fork_rpc' in deps:
        action = 'fork_rpc'
    elif not is_harness:
        action = 'bare_test_fn'
    elif 'repo_test_deps' in deps:
        if _repo_test_forks(_repo_root(case)):
            deps.append('fork_rpc')
            action = 'fork_rpc'
        else:
            action = 'complete_test'
    else:
        action = 'complete_test'
    return {'action': action, 'deps': deps, 'has_test': has_test,
            'is_harness': is_harness, 'blocks': len(blocks)}


def _extract_names(block: str) -> tuple[str | None, str | None]:
    fn = None
    m = _TEST_FN_RE.search(block)
    if m:
        fn = m.group(1)
    contract = None
    m = _TEST_CONTRACT_RE.search(block)
    if m:
        contract = m.group(1)
    return contract, fn


def _write_standalone(repo: Path, sub_uid: str, finding_uid: str,
                      block: str) -> Path:
    entry = repo / 'test' / f'Standalone_{sub_uid}_{finding_uid}.t.sol'
    entry.parent.mkdir(parents=True, exist_ok=True)
    entry.write_text(block, encoding='utf-8')
    return entry


def _run(cmd: list[str], cwd: Path, timeout: int = 600) -> tuple[int, str]:
    proc = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True,
                          timeout=timeout)
    return proc.returncode, (proc.stdout or '') + (proc.stderr or '')


def _test_passes(output: str, test_name: str) -> bool:
    if '[PASS]' not in output:
        return False
    return re.search(r'\[PASS\]\s+' + re.escape(test_name) + r'\s*\(', output) is not None


def _repo_test_sources(repo: Path | None) -> list[Path]:
    if repo is None or not (repo / 'test').is_dir():
        return []
    try:
        return sorted((repo / 'test').rglob('*.sol'))
    except OSError:
        return []


def _identifiers(text: str) -> set[str]:
    return set(_IDENT_RE.findall(text))


def _find_best_test_source(repo: Path | None, block: str) -> Path | None:
    sources = _repo_test_sources(repo)
    if not sources:
        return None
    block_ids = _identifiers(block)
    best: Path | None = None
    best_score = -1
    for src in sources:
        if re.match(r'Standalone_[A-Za-z0-9_]+\.t\.sol$', src.name):
            continue
        try:
            text = src.read_text(encoding='utf-8')
        except OSError:
            continue
        if not _HARNESS_RE.search(text):
            continue
        score = len(block_ids & _identifiers(text))
        if score > best_score:
            best = src
            best_score = score
    return best


def _rename_contract(text: str, new_name: str) -> str:
    pattern = re.compile(
        r'\bcontract\s+[A-Za-z0-9_]+'
        r'((?:\s+is\s+[A-Za-z0-9_,\s]*(?:DSTest|Test)\b)?)')
    changed, n = pattern.subn(lambda m: f'contract {new_name}{m.group(1)}',
                              text, count=1)
    if n == 0:
        changed = re.sub(r'\bcontract\s+[A-Za-z0-9_]+',
                         f'contract {new_name}', text, count=1)
    return changed


def _contract_open_brace(text: str) -> int:
    m = re.search(r'\bcontract\s+[A-Za-z0-9_]+\s+is\s+[A-Za-z0-9_,\s]*'
                  r'(?:DSTest|Test)\b[^{]*\{', text)
    if not m:
        m = re.search(r'\bcontract\s+[A-Za-z0-9_]+[^{]*\{', text)
    if not m:
        return -1
    return m.end() - 1


def _matching_close_brace(text: str, open_pos: int) -> int:
    depth = 0
    i = open_pos
    in_string = False
    in_line_comment = False
    in_block_comment = False
    quote = ''
    while i < len(text):
        c = text[i]
        nxt = text[i + 1] if i + 1 < len(text) else ''
        if in_line_comment:
            if c == '\n':
                in_line_comment = False
            i += 1
            continue
        if in_block_comment:
            if c == '*' and nxt == '/':
                in_block_comment = False
                i += 2
                continue
            i += 1
            continue
        if in_string:
            if c == '\\':
                i += 2
                continue
            if c == quote:
                in_string = False
            i += 1
            continue
        if c == '/' and nxt == '/':
            in_line_comment = True
            i += 2
            continue
        if c == '/' and nxt == '*':
            in_block_comment = True
            i += 2
            continue
        if c in ('"', "'"):
            in_string = True
            quote = c
            i += 1
            continue
        if c == '{':
            depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return -1


def _embed_into_contract(harness: str, new_name: str, block: str) -> str:
    text = _rename_contract(harness, new_name)
    open_pos = _contract_open_brace(text)
    if open_pos < 0:
        return f'{text.rstrip()}\n\n{block}\n'
    close_pos = _matching_close_brace(text, open_pos)
    if close_pos < 0:
        return f'{text.rstrip()}\n\n{block}\n'
    snippet = '\n' + block.strip('\n') + '\n'
    return text[:close_pos] + snippet + text[close_pos:]


def _rename_test_fn(block: str, new_name: str) -> str:
    return _TEST_FN_RE.sub(lambda m: f'function {new_name}(', block, count=1)


def _safe_slug(value: str) -> str:
    return re.sub(r'[^A-Za-z0-9_]', '_', str(value))


def _author_wrapper_from_source(best_source: Path, sub_uid: str,
                                finding_uid: str, block: str) -> str:
    harness = best_source.read_text(encoding='utf-8')
    contract_name = f'Standalone_{_safe_slug(sub_uid)}_{_safe_slug(finding_uid)}'
    block = _rename_test_fn(block, f'test_audit_poc_{_safe_slug(finding_uid)}')
    return _embed_into_contract(harness, contract_name, block)


def _author_via_llm(case: dict, finding: dict, block: str,
                    repo: Path | None, error_hint: str = '') -> str | None:
    """Ask DeepSeek for a self-contained Foundry test contract."""
    try:
        sys.path.insert(0, str(ROOT / 'tools' / 'stage3'))
        from lib import llm
    except Exception:
        return None

    source_path = case.get('source_path')
    target_src = ''
    if source_path and Path(source_path).is_file():
        try:
            target_src = Path(source_path).read_text(encoding='utf-8')[:20000]
        except OSError:
            target_src = ''

    best = _find_best_test_source(repo, block) if repo else None
    test_src = ''
    if best:
        try:
            test_src = best.read_text(encoding='utf-8')[:20000]
        except OSError:
            test_src = ''

    system = (
        'You author a Foundry test that PASSES against the CURRENT (vulnerable) '
        'code exactly as supplied. Reproduce the bug as a passing assertion: '
        '- if the bug makes a call revert that should not, use '
        '`vm.expectRevert(...)` or a low-level `.call` and assert the failure; '
        '- if the bug allows an unauthorized action, perform it and assert it '
        'succeeds; '
        '- if the bug leaks or miscalculates a value, assert that wrong value. '
        'The test must fail after the vulnerability is fixed. '
        'Produce ONLY a JSON object with one key "solidity" whose value is a '
        'complete, self-contained Foundry test file: SPDX, pragma, imports, a '
        '`contract ... is Test`, a setUp, and the test function. No markdown.')
    user = (
        f'Project: {case.get("project")}\n'
        f'Finding title: {finding.get("title")}\n'
        f'Target source file:\n```solidity\n{target_src}\n```\n\n'
        f'Closest existing repo test:\n```solidity\n{test_src}\n```\n\n'
        f'Repo foundry.toml:\n```toml\n{_foundry_toml(repo)}\n```\n\n'
        f'PoC snippet to turn into a passing test:\n```solidity\n{block}\n```\n'
        f'Previous attempt failure (fix it):\n```\n{error_hint[-6000:]}\n```\n')
    try:
        resp = llm.chat_json(system, user, max_tokens=8000)
    except Exception:
        return None
    solidity = resp.get('solidity')
    if isinstance(solidity, str) and solidity.strip():
        return solidity.strip()
    return None


def _foundry_toml(repo: Path | None) -> str:
    if repo is None:
        return ''
    ft = repo / 'foundry.toml'
    if not ft.is_file():
        return ''
    try:
        return ft.read_text(encoding='utf-8')[:4000]
    except OSError:
        return ''


def _run_entry(repo: Path, sub_uid: str, finding_uid: str,
               block: str, test_name: str | None = None) -> tuple[str, str, str]:
    """Write the entry, run forge test, flatten, rerun.

    Returns (status, error, forge_output).
    """
    if not test_name:
        _, test_name = _extract_names(block)
    if not test_name:
        return STATUS_FAILED, 'no_test_function', ''
    if not _ensure_forge_std(repo):
        return STATUS_BLOCKED, 'forge_std_unavailable', ''
    entry = _write_standalone(repo, sub_uid, finding_uid, block)
    code, out_txt = _run(['forge', 'test', '--match-test', test_name], repo)
    entry_ok = code == 0 and _test_passes(out_txt, test_name)
    if not entry_ok:
        return STATUS_ENTRY_ONLY, 'entry_test_failed', out_txt
    flat_dir = repo / '.poc_flattened'
    flat_dir.mkdir(parents=True, exist_ok=True)
    flat = flat_dir / f'Standalone_{sub_uid}_{finding_uid}.flattened.t.sol'
    code, out_txt = _run(['forge', 'flatten', str(entry)], repo)
    if code != 0:
        return STATUS_ENTRY_ONLY, 'flatten_failed', out_txt
    flat.write_text(out_txt, encoding='utf-8')
    code, out_txt = _run(['forge', 'test', '--match-test', test_name], repo)
    if code == 0 and _test_passes(out_txt, test_name):
        return STATUS_PASS, '', out_txt
    return STATUS_ENTRY_ONLY, 'flattened_test_failed', out_txt


def _process_case(case: dict, args) -> CaseOutcome:
    finding = _finding(case)
    sub_uid = str((finding or {}).get('uid') or case.get('finding_uid')
                  or case.get('finding_key') or 'unknown')
    finding_uid = str((finding or {}).get('number') or case.get('finding_key')
                      or 'unknown')
    key = f"{case['project']}__{finding_uid}__{sub_uid}"
    repo = _repo_root(case)

    if finding is None:
        return CaseOutcome(key, case['project'], sub_uid, finding_uid,
                           STATUS_BLOCKED, 'finding_not_found')

    blocks = _poc_blocks(finding)
    cls = _classify(case, blocks)

    if cls['action'] == 'no_poc_code':
        return CaseOutcome(key, case['project'], sub_uid, finding_uid,
                           STATUS_BLOCKED, 'no_poc_code_block')
    if cls['action'] == 'fork_rpc':
        return CaseOutcome(key, case['project'], sub_uid, finding_uid,
                           STATUS_BLOCKED, 'poc_forks_live_rpc')
    if repo is None:
        return CaseOutcome(key, case['project'], sub_uid, finding_uid,
                           STATUS_BLOCKED, 'repo_not_found')
    if not _is_foundry(repo):
        return CaseOutcome(key, case['project'], sub_uid, finding_uid,
                           STATUS_BLOCKED, 'hardhat_root_no_forge')
    if args.dry_run:
        return CaseOutcome(key, case['project'], sub_uid, finding_uid,
                           'dry_run', '')

    block = blocks[0]
    test_name: str | None = None

    if cls['action'] == 'bare_test_fn':
        best = _find_best_test_source(repo, block)
        if best is not None:
            test_name = f'test_audit_poc_{_safe_slug(finding_uid)}'
            block = _author_wrapper_from_source(best, sub_uid, finding_uid, block)
        elif not args.author:
            return CaseOutcome(key, case['project'], sub_uid, finding_uid,
                               STATUS_BLOCKED, 'no_test_harness_to_borrow')
        else:
            authored = _author_via_llm(case, finding, block, repo)
            if authored is None:
                return CaseOutcome(key, case['project'], sub_uid, finding_uid,
                                   STATUS_FAILED, 'authoring_failed')
            block = authored

    if cls['action'] == 'snippet_only':
        if not args.author:
            return CaseOutcome(key, case['project'], sub_uid, finding_uid,
                               STATUS_BLOCKED, 'needs_authoring')
        author_block = '\n\n'.join(blocks)
        authored = _author_via_llm(case, finding, author_block, repo)
        if authored is None:
            return CaseOutcome(key, case['project'], sub_uid, finding_uid,
                               STATUS_FAILED, 'authoring_failed')
        block = authored

    status, error, out_txt = _run_entry(repo, sub_uid, finding_uid, block, test_name)
    if args.author and cls['action'] in ('snippet_only', 'bare_test_fn'):
        current = block
        for _ in range(3):
            if status == STATUS_PASS:
                break
            repaired = _author_via_llm(case, finding, current, repo,
                                       error_hint=out_txt)
            if repaired is None or repaired.strip() == current.strip():
                break
            current = repaired
            status, error, out_txt = _run_entry(repo, sub_uid, finding_uid, repaired)
    return CaseOutcome(key, case['project'], sub_uid, finding_uid,
                       status, error)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case', default=None, help='single blind-set case id')
    parser.add_argument('--all', action='store_true', help='process every case')
    parser.add_argument('--out-dir', default=str(DEFAULT_OUT))
    parser.add_argument('--dry-run', action='store_true',
                        help='classify only; do not run forge or LLM')
    parser.add_argument('--author', action='store_true',
                        help='author standalone PoC via LLM for snippet cases')
    args = parser.parse_args()

    blind = _load_blind()
    cases = blind['cases']
    if args.case:
        cases = [c for c in cases if c['case'] == args.case]
        if not cases:
            raise SystemExit(f'case not found: {args.case}')
    elif not args.all:
        raise SystemExit('pass --case <id> or --all')

    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    rows: list[CaseOutcome] = []

    for idx, case in enumerate(cases, 1):
        row = _process_case(case, args)
        rows.append(row)
        print(f'[{idx}/{len(cases)}] {row.key}: {row.status} {row.error}',
              flush=True)

    summary = {
        'total_rows': len(rows),
        'flatten_pass': sum(1 for r in rows if r.status == STATUS_PASS),
        'entry_pass_only': sum(1 for r in rows if r.status == STATUS_ENTRY_ONLY),
        'failed': sum(1 for r in rows if r.status == STATUS_FAILED),
        'blocked': sum(1 for r in rows if r.status == STATUS_BLOCKED),
        'dry_run': sum(1 for r in rows if r.status == 'dry_run'),
    }
    (out / 'full_poc_batch_summary.json').write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + '\n')
    csv_lines = ['key,project,submission_uid,finding_uid,status,error']
    csv_lines += [f'{r.key},{r.project},{r.submission_uid},{r.finding_uid},'
                  f'{r.status},{r.error}' for r in rows]
    (out / 'full_poc_batch_status.csv').write_text('\n'.join(csv_lines) + '\n')
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
