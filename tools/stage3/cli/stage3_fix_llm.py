#!/usr/bin/env python3
"""Propose a code-fix negative via DeepSeek from one audit report.

给定一个已复现的正样本报告 + 扁平化源码，让模型提出“真实修复补丁”的
``{old: new}`` 行级替换，并可选给出 ``--fix-poc`` 的 PoC 期望修正。

产出 ``fix.json``（schema ``stage3-fix-proposal/1``），其中：
  * ``fix``      : {old: new}，old 必须是源文件里的 verbatim 子串
  * ``fix_poc``  : {old: new}，PoC 断言极性修正，可为空
  * ``applicable``: 每个 old 都逐字命中时为 true，否则 false（交给人类/重试）

用法（cwd = tools/stage3）：
    python -m cli.stage3_fix_llm \
        --report <case>/report.json --src cases/<case>/src/Contract.sol \
        --out /tmp/fix.json
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from lib import llm
from lib.binding_llm import slice_flatten

PROPOSAL_SCHEMA = 'stage3-fix-proposal/1'
MAX_SOURCE_CHARS = 160000
TEST_TAIL_CHARS = 24000

_SYSTEM = (
    'You extract a concrete code fix from an audit report and map it onto '
    'flattened Solidity source. Reply with JSON only.\n'
    'JSON schema:\n'
    '{"fix": {"<old line(s)>": "<new line(s)>", ...}, '
    '"fix_poc": {"<old PoC assertion>": "<new PoC assertion>", ...}, '
    '"reason": "<one sentence>"}\n'
    'Rules:\n'
    '- Each "old" value must be a VERBATIM substring of the provided source. '
    'Copy it exactly, including indentation and punctuation.\n'
    '- "fix" applies the vulnerability fix recommended by the report. Use the '
    'minimal, exact source lines that actually change.\n'
    '- "fix_poc" is optional: only correct the PoC expectation if the fix '
    'flips the asserted outcome (e.g. vm.expectRevert -> assertEq success). '
    'Otherwise leave it empty ({}).\n'
    '- If the report does not contain enough detail to produce an exact '
    'replacement, return "fix": {} with a reason.\n'
)


def _report_focus(body: str, limit: int = 12000) -> str:
    """Keep root-cause + mitigation parts, drop irrelevant prose."""
    lines = body.splitlines()
    keep = []
    capturing = False
    for line in lines:
        if re.search(r'(?i)(root cause|finding description|impact|recommended '
                     r'mitigation|primary fix|suggested fix|fix)', line):
            capturing = True
        if capturing:
            keep.append(line)
    text = '\n'.join(keep) if keep else body
    return text[:limit]


def _focus_contract_body(source: str, contract: str | None) -> str:
    """Return the full verbatim body of the contract to fix, or '' if unknown."""
    if not contract:
        return ''
    try:
        from lib.patch import _contract_region
        start, end = _contract_region(source, contract)
        return source[start:end]
    except Exception:
        return ''


def validate_fix(fix: dict, fix_poc: dict, source: str) -> dict:
    """Deterministic verbatim gate on the model's {old:new} proposal."""
    missing = [old for old in fix if old not in source]
    missing_poc = [old for old in fix_poc if old not in source]
    applicable = (len(fix) > 0 and not missing and not missing_poc)
    return {
        'schema_version': PROPOSAL_SCHEMA,
        'fix': fix,
        'fix_poc': fix_poc,
        'applicable': applicable,
        'missing_old': missing,
        'missing_poc_old': missing_poc,
    }


def propose_fix(report_body: str, source: str, hint: str | None = None,
                focus_contract: str | None = None) -> dict:
    focus = _report_focus(report_body)
    sliced = slice_flatten(source)
    body = _focus_contract_body(source, focus_contract)
    if body:
        head = ('FOCUS CONTRACT (full verbatim source of the contract to fix; '
                'prefer replacing lines inside it):\n' + body + '\n\n')
        budget = max(MAX_SOURCE_CHARS - len(head) - 100, 0)
        user = ('REPORT (root cause + recommended mitigation):\n' + focus +
                '\n\n' + head +
                'FLATTENED SOLIDITY SOURCE (business sources plus PoC test tail):\n'
                + sliced[:budget])
    else:
        user = (
            'REPORT (root cause + recommended mitigation):\n' + focus +
            '\n\nFLATTENED SOLIDITY SOURCE (business sources plus PoC test tail):\n'
            + sliced[:MAX_SOURCE_CHARS])
    if hint:
        user += ('\n\nADDITIONAL CONSTRAINT (previous attempt was rejected '
                 'because it did not remove the vulnerability):\n' + hint +
                 '\nProduce a different, complete fix that actually removes '
                 'the vulnerability.')
    raw = llm.chat_json(_SYSTEM, user)
    fix = raw.get('fix') or {}
    fix_poc = raw.get('fix_poc') or {}
    if not isinstance(fix, dict) or not isinstance(fix_poc, dict):
        raise llm.LLMError('model returned non-object fix/fix_poc')
    proposal = validate_fix(fix, fix_poc, source)
    proposal['reason'] = raw.get('reason')
    return proposal


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--src', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--binding', type=Path, default=None,
                        help='positive binding.json; its patch.contract is '
                             'kept fully in the prompt to avoid truncation')
    parser.add_argument('--hint', default=None,
                        help='feedback from a previous rejected attempt')
    args = parser.parse_args(argv)

    report = json.loads(Path(args.report).read_text())
    body = report.get('body') or ''
    source = Path(args.src).read_text()
    focus_contract = None
    if args.binding:
        try:
            binding = json.loads(Path(args.binding).read_text())
            focus_contract = (binding.get('patch') or {}).get('contract')
        except (json.JSONDecodeError, OSError):
            focus_contract = None
    proposal = propose_fix(body, source, hint=args.hint,
                           focus_contract=focus_contract)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(proposal, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(proposal, ensure_ascii=False, indent=2))
    return 0 if proposal['applicable'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
