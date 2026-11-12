#!/usr/bin/env python3
"""Build a negative sample from a positive one by applying a code fix.

The negative case keeps the same report/stage-2 claim and binding, but its
source carries the fix, so original and patched both pass on the (corrected)
PoC -> expected verdict ``violation_not_reproduced``.

Fixes are explicit line-level replacements, never guessed. Run with
cwd = tools/stage3:
    python -m cli.stage3_make_negative --positive cases/forte_float128_pos \
        --out cases/forte_float128_neg \
        --fix '{"retVal := lt(aMan, bMan)":"retVal := iszero(gt(aMan, bMan))"}'
        --fix-poc '{"assertEq(isEqual, false);":"assertEq(isEqual, true);"}'
"""
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path


def _apply_replacements(text: str, replacements: dict) -> str:
    for old, new in replacements.items():
        if old not in text:
            raise SystemExit(f'fix target not found: {old[:80]}')
        text = text.replace(old, new, 1)
    return text


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--positive', required=True)
    parser.add_argument('--out', required=True)
    parser.add_argument('--fix', required=True, help='JSON {old:new} code fix on src')
    parser.add_argument('--fix-poc', default='{}',
                        help='JSON {old:new} PoC expectation correction')
    parser.add_argument('--src-name', default='Contract.sol')
    parser.add_argument('--binding', default=None,
                        help='defaults to <positive>/binding.json')
    args = parser.parse_args(argv)

    pos = Path(args.positive).resolve()
    out = Path(args.out).resolve()
    if out.exists():
        raise SystemExit(f'output already exists: {out}')

    src = (pos / 'src' / args.src_name).read_text()
    src = _apply_replacements(src, json.loads(args.fix))
    poc = json.loads(args.fix_poc)
    if poc:
        src = _apply_replacements(src, poc)

    (out / 'src').mkdir(parents=True)
    (out / 'test').mkdir(parents=True)
    (out / 'stage2_run').mkdir(parents=True)
    (out / 'src' / args.src_name).write_text(src)
    for a in ('stage3-spec.json', 'constraints.json', 'formalization.json'):
        shutil.copy2(pos / 'stage2_run' / a, out / 'stage2_run' / a)
    binding_path = Path(args.binding).resolve() if args.binding else pos / 'binding.json'
    binding = json.loads(binding_path.read_text())
    if binding.get('patch'):
        binding['patch']['file'] = args.src_name
    for entry in binding.get('bindings', {}).values():
        entry['source'] = args.src_name + ':' + entry.get('source', '').split(':', 1)[-1]
    (out / 'binding.json').write_text(json.dumps(binding, ensure_ascii=False, indent=2) + '\n')
    (out / 'foundry.toml').write_text(
        '[profile.default]\nsrc = "src"\ntest = "test"\nout = "out"\n'
        'via_ir = true\noptimizer = true\noptimizer_runs = 200\n')
    print(f'built negative case: {out}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
