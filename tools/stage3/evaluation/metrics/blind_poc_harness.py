#!/usr/bin/env python3
"""Blind-set PoC harness classification.

Turns the opaque "no test entrypoint" blocker into a per-case, actionable
classification. A case can reach ``forge test`` only when its PoC is a runnable
test harness that is self-contained or whose dependencies (repo src/test +
forge-std) can be flattened; PoCs that fork a live RPC via ``vm.rpc`` or that
are only code snippets/diffs are recorded as honest ceilings, not as pipeline
failures.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'scripts' / 'code4rena'))
from findings_lookup import matching_finding

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
BLIND = HERE / 'blind_set.json'
REPORTS = ROOT / 'code4rena_reports'
OUT_JSON = HERE / 'blind_poc_harness_status.json'
OUT_MD = HERE / 'blind_poc_harness_status.md'

_CODE_BLOCK_RE = re.compile(r'```(?:solidity|sol|js)?\s*\n(.*?)```', re.S | re.I)
_RPC_RE = re.compile(r'(?:_?vm)\.(?:rpc|createSelectFork|createFork|rollFork|'
                     r'rollForkId|makePersistent|selectFork)\s*\(')
_ENV_RE = re.compile(r'(?:_?vm)\.env(?:Uint|Int|String|Bytes32?|Address|Bool|'
                     r'Uint256)\s*\(')
_TEST_RE = re.compile(r'\bfunction\s+test[A-Za-z0-9_]*\s*\(')
_TEST_HARNESS_RE = re.compile(
    r'(?:forge-std/Test\.sol|\bis\s+(?:DSTest|Test)\b|import\s+\{[^}]*Test'
    r'[^}]*\}\s+from\s+"forge-std/Test\.sol")')
_SRC_IMPORT_RE = re.compile(r'from\s+"src/|import\s+"src/')
_TEST_IMPORT_RE = re.compile(r'from\s+"test/|import\s+"test/|'
                             r'from\s+"\.\./|import\s+"\.\./')

ACTIONS = {
    'missing_submission': 'fetch code4rena submission dump first',
    'no_poc_code': 'no runnable PoC code block in submission',
    'snippet_only': 'PoC is a diff/snippet, not a forge test; needs manual harness',
    'fork_rpc': 'PoC forks live RPC (vm.rpc/fork); not self-contained',
    'repo_test_deps': 'PoC imports repo test/ helpers; flatten required',
    'repo_src_deps': 'PoC imports repo src/; flatten required',
    'bare_test_fn': 'bare test function without a contract is Test harness; needs wrapper',
    'self_contained': 'PoC is a full contract is Test harness',
}


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


def _repo_test_forks(repo: Path) -> bool:
    if repo is None or not (repo / 'test').is_dir():
        return False
    for sol in (repo / 'test').rglob('*.sol'):
        try:
            text = sol.read_text()
        except OSError:
            continue
        if _RPC_RE.search(text):
            return True
    return False


def _submission_for(case: dict) -> dict | None:
    return matching_finding(case)


def _poc_blocks(finding: dict) -> list[str]:
    """Prefer the full-test proof over report-body snippets."""
    for field in ('proof_of_concept', 'proofOfConcept', 'body'):
        text = finding.get(field) or ''
        blocks = [m.group(1).strip() for m in _CODE_BLOCK_RE.finditer(text)]
        runnable = [b for b in blocks if _TEST_RE.search(b)]
        if runnable:
            return runnable
    text = ((finding.get('proof_of_concept') or '') + '\n'
            + (finding.get('proofOfConcept') or '') + '\n'
            + (finding.get('body') or ''))
    return [m.group(1).strip() for m in _CODE_BLOCK_RE.finditer(text)]


def _classify(case: dict, blocks: list[str]) -> dict:
    if not blocks:
        return {'action': 'no_poc_code', 'deps': [], 'has_test': False,
                'is_harness': False, 'blocks': 0}
    merged = '\n'.join(blocks)
    deps: list[str] = []
    has_test = bool(_TEST_RE.search(merged))
    is_harness = bool(_TEST_HARNESS_RE.search(merged))
    if _RPC_RE.search(merged):
        deps.append('fork_rpc')
    if _ENV_RE.search(merged):
        deps.append('env_dep')
    if _TEST_IMPORT_RE.search(merged):
        deps.append('repo_test_deps')
    if _SRC_IMPORT_RE.search(merged):
        deps.append('repo_src_deps')
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
            action = 'repo_test_deps'
    elif 'repo_src_deps' in deps:
        action = 'repo_src_deps'
    else:
        action = 'self_contained'
    return {'action': action, 'deps': deps, 'has_test': has_test,
            'is_harness': is_harness, 'blocks': len(blocks)}


def main() -> int:
    blind = json.loads(BLIND.read_text())
    rows = []
    for case in blind['cases']:
        finding = _submission_for(case)
        blocks = _poc_blocks(finding) if finding else []
        cls = _classify(case, blocks)
        repo = _repo_root(case)
        tooling = ('foundry' if repo and (repo / 'foundry.toml').is_file()
                   else 'hardhat' if repo else 'none')
        rows.append({
            'case': case['case'],
            'project': case['project'],
            'submission_present': finding is not None,
            'poc_blocks': len(blocks),
            'action': cls['action'],
            'action_hint': ACTIONS.get(cls['action'], ''),
            'deps': cls['deps'],
            'has_test': cls['has_test'],
            'is_harness': cls['is_harness'],
            'repo_tooling': tooling,
        })

    counts: dict[str, int] = {}
    for r in rows:
        counts[r['action']] = counts.get(r['action'], 0) + 1
    report = {
        'schema_version': 'blind-poc-harness-status/1',
        'generated': '2026-11-13',
        'total': len(rows),
        'by_action': counts,
        'self_contained': counts.get('self_contained', 0),
        'rows': rows,
    }
    OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')

    lines = [
        '# 盲测 PoC harness 就绪分类',
        '',
        f"样本 **{report['total']}**；动作分布："
        + '、'.join(f"{k} {v}" for k, v in sorted(counts.items())) + '。',
        '',
        '| case | project | 工具 | PoC 块 | 动作 | deps |',
        '| --- | --- | --- | ---: | --- | --- |',
    ]
    for r in rows:
        lines.append(
            f"| {r['case']} | {r['project']} | {r['repo_tooling']} | "
            f"{r['poc_blocks']} | {r['action']} | "
            f"{', '.join(r['deps']) or '-'} |")
    lines += [
        '',
        '## 动作含义',
    ]
    for action, hint in ACTIONS.items():
        lines.append(f"- `{action}`：{hint}")
    OUT_MD.write_text('\n'.join(lines) + '\n')
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
