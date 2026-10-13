#!/usr/bin/env python3
"""Single-file new-SC pipeline (deterministic, zero model calls).

One command per case: merge stage-2's compiled claim into the original
stage-1 slice as ONE Solidity file (the new SC), execute it with forge,
adjudicate the pre-registered four-branch verdict, and ingest the result
into stage 3 through the existing stage3-feedback path (on a run COPY --
frozen runs are never touched).

  /root/.local/share/uv/tools/halmos/bin/python new_sc.py <case_key> \
      [--batch prompt_live4_blind_01]
  /root/.local/share/uv/tools/halmos/bin/python new_sc.py --all \
      --batch final_holdout_01
  /root/.local/share/uv/tools/halmos/bin/python new_sc.py --template \
      <case_key>            binding skeleton (symbols pre-filled from
                            formal-plan), the first step for a NEW case
  /root/.local/share/uv/tools/halmos/bin/python new_sc.py <case_key> \
      --batch <batch> --experiment bisection/<dir>
                            differential-replay bisection (the reflux
                            attribution instrument): run the case against an
                            isolated workspace -- <dir>/run is a COPY of the
                            frozen run carrying the variant under test,
                            <dir>/binding.json an optional variant binding
                            (checked-in binding used when absent).  ALL
                            outputs stay inside <dir>; the frozen batch and
                            the checked-in case-named artifacts are never
                            touched.  Evidence lands in
                            adjudication_ledger.json.

Per-case inputs (data only, no per-case code):
  <batch>/runs/<case_key>/            stage-2 frozen run (constraints.json,
                                      formal-plan.json, provenance.json)
  corpus case dir                     stage-1 slice contract.flattened.t.sol
  bindings/<case_key>.json            symbol -> Solidity binding map

Outputs (all under this directory, never overwriting an existing one):
  new_sc__<case_key>/new_sc.t.sol     the new SC: slice bytes verbatim as a
                                      prefix + the appended guard contract
  new_sc__<case_key>/foundry.toml
  new_sc__<case_key>/sc-spec.json     unified stage-1/2/3 interface
  forge__<case_key>.log               forge evidence for this case
  verdict__<case_key>.json            four-branch adjudication record
  stage3_feedback__<case_key>.json    ingest input for this case
  stage3-consistency__<case_key>.json archived ingest evidence (auto-copied;
                                      a differing rerun is refused, not silently
                                      overwritten)
  run_copy__<case_key>/               run copy + stage3-consistency.json
  adjudication_summary__<batch>.json  --all mode: one row per case + counts

Pre-registered adjudication (frozen in README.md before any run):
  p&!i&v -> violation_reproduced    p&i&v -> i_too_weak
  !p     -> precondition_mismatch   p&!v  -> violation_not_observed

Single-sourced with the Z3 backend (2026-10-09): expression traversal and the
op vocabulary come from lib/dsl.py, and the p/i/v -> code-query mapping from
lib/stage3_consistency.queries_from_piv (the same module that adjudicates the
ingested feedback), so the two backends cannot drift apart silently.
"""

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
EVAL = HERE.parent
REPO = HERE.parents[3]
# 语料根可用 STAGE2_CORPUS 环境变量覆盖（换机器/换语料不必改代码）。
CORPUS = Path(os.environ.get(
    'STAGE2_CORPUS',
    '/root/poc_repro_work/verified_flatten_pass_1568_exact_cases'))
MAIN_PY = REPO / 'main.py'
CLAIM_ID = 'core_claim'
CONTRACT_NAME = 'Stage2InvariantGuard'
DEFAULT_BATCH = 'prompt_live4_blind_01'

# --- binding map schema (stage2-newsc-binding/1) ---------------------------
# 绑定映射是整条管线唯一的人工输入；下面的机械门把它变成"被校验的数据"
# 而不是"被信任的散文"。绑定错误必须在写任何文件之前在这里失败，绝不
# 允许流到 forge 再以一个自信但错误的四分支裁决收场。schema 与编写指南
# 见 bindings/README.md（Ekubo/Merkl 两份是规范范例）。
BINDING_SCHEMA_VERSION = 'stage2-newsc-binding/1'
BINDING_TOP_KEYS = {'schema_version', 'case_key', 'binding_provenance',
                    'state', 'setup', 'attack', 'post', 'binding_sanity',
                    'symbols'}
SYMBOL_KEYS = {'phase', 'type', 'expr', 'unit', 'binding_description'}
BINDING_PHASES = ('pre', 'post')
BINDING_TYPES = ('address', 'bool', 'uint256', 'int256')
#: formal-plan 声明的 sort 允许映射到哪些 Solidity 类型。
SORT_TO_TYPES = {'bool': ('bool',), 'address': ('address',),
                 'int': ('uint256', 'int256')}

# lib/ 单源共享（2026-10-09 语义单源化）：表达式遍历与算子词汇表来自
# lib/dsl.py，p/i/v -> code-query 映射来自 lib/stage3_consistency.py。
# 本脚本从自身目录直接运行，先把阶段二根目录补进 sys.path（与
# tests/__init__.py 同法）。
_STAGE2_ROOT = HERE.parents[1]
if str(_STAGE2_ROOT) not in sys.path:
    sys.path.insert(0, str(_STAGE2_ROOT))
from lib import dsl, stage3_consistency  # noqa: E402

BINARY_OPS = {'and': '&&', 'or': '||', 'ne': '!=', 'eq': '==',
              'lt': '<', 'le': '<=', 'gt': '>', 'ge': '>=',
              'add': '+', 'sub': '-', 'mul': '*'}
# translate 的算子面必须精确等于 lib/dsl.py 的 SOLIDITY_OPS：dsl 是两个
# 编译后端（Z3 侧 lib/report_only.py）共享的词汇表单源，这里在启动时
# 机械核对，任何一侧加减算子而漏掉另一侧都会 fail-fast。'mod' 有意不在
# Solidity 侧（Z3 欧几里得取余 vs Solidity 截断取余，负被除数下数值不同，
# 盲补会制造静默语义分歧），详见 lib/dsl.py 模块 docstring。
assert set(BINARY_OPS) | {'not', 'implies'} == set(dsl.SOLIDITY_OPS), \
    'translator op set drifted from lib/dsl.SOLIDITY_OPS'

FOUNDARY_TOML = '''[profile.default]
src = "."
test = "."
out = "out"
libs = ["lib"]
via_ir = true
optimizer = true
optimizer_runs = 200
'''


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


class CaseError(Exception):
    """Per-case failure (missing inputs, binding gaps, verdict mismatch).
    Raised so batch mode can record the failure and keep going."""


def fail(msg):
    raise CaseError(msg)


def check_provenance(run, case_key, case_dir, slice_bytes):
    """Mechanical source alignment: the stage-2 run and the corpus case must
    be the same report + slice (the mistake this replaces was manual)."""
    prov = json.loads((run / 'provenance.json').read_text())
    if prov.get('case_id') != case_key:
        fail(f'provenance case_id {prov.get("case_id")!r} != {case_key!r}')
    report_path = Path(prov['report_path'])
    if report_path.parent.resolve() != case_dir.resolve():
        fail(f'provenance report_path points at {report_path.parent}, '
             f'not the corpus case dir {case_dir}')
    report_bytes = (case_dir / 'report.json').read_bytes()
    if sha256_bytes(report_bytes) != prov['report_sha256']:
        fail('corpus report.json sha256 != provenance report_sha256')
    declared = prov.get('declared_code_sha256')
    if declared and sha256_bytes(slice_bytes) != declared:
        fail('slice contract.flattened.t.sol sha256 != declared_code_sha256')
    return prov


def translate(node, symbols):
    """op-args/var expression (the compiled Z3 source) -> a Solidity bool."""
    if isinstance(node, bool):
        return 'true' if node else 'false'
    if isinstance(node, int):
        node = {'const': node}
    if isinstance(node, dict) and 'const' in node:
        # Constants may arrive as bare ints or {"const": N} nodes; both get
        # the same cast. Negative literals cannot be cast to uint256; int256
        # keeps the compile error at fail-fast level for mixed-sign exprs.
        node_val = node['const']
        return f'int256({node_val})' if node_val < 0 else f'uint256({node_val})'
    if isinstance(node, dict) and 'var' in node:
        row = symbols[node['var']]
        return f'({row["expr"]})'
    op, args = node['op'], node['args']
    if op == 'not':
        return f'(!{translate(args[0], symbols)})'
    if op == 'implies':
        return f'((!{translate(args[0], symbols)}) || {translate(args[1], symbols)})'
    if op in BINARY_OPS:
        # QEXPR ops may be n-ary (e.g. a 4-ary and); fold left to right, which
        # is identical to the binary form for 2-ary nodes.
        rendered = [translate(a, symbols) for a in args]
        expr = rendered[0]
        for piece in rendered[1:]:
            expr = f'({expr} {BINARY_OPS[op]} {piece})'
        return expr
    raise ValueError(f'unsupported expression node: {node!r}')


def pre_symbol_name(name):
    """Solidity identifier of the pre-attack snapshot of a phase:'pre' symbol."""
    return f'{name}__pre'


def pre_capture_sol(symbols):
    """Snapshot lines for phase:'pre' symbols, emitted BEFORE the attack.

    'phase' is enforced semantics, not metadata: the binding expr of a 'pre'
    symbol is evaluated pre-attack and captured into <name>__pre.  An expr
    that only compiles after the attack (it needs attack/post locals) fails
    right here at compile time -- fail-fast, never a silently wrong P."""
    lines = []
    for name, row in sorted(symbols.items()):
        if row['phase'] != 'pre':
            continue
        if not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', name):
            fail(f'phase "pre" symbol {name!r} is not a valid Solidity '
                 'identifier (its snapshot variable name must be)')
        lines.append(f'{row["type"]} {pre_symbol_name(name)} = {row["expr"]};')
    return lines


def build_translate_symbols(symbols):
    """The var-resolution table translate() compiles against: phase 'pre'
    symbols resolve to their pre-attack snapshots; everything else resolves
    to the binding expr verbatim."""
    return {name: {'expr': pre_symbol_name(name) if row['phase'] == 'pre'
                   else row['expr']}
            for name, row in symbols.items()}


def guard_sol(binding, expressions, case_key, pre_lines):
    """The guard contract, APPENDED to the slice file (never editing it)."""
    inherits = binding['state'].get('inherits', 'Test')
    state = '\n        '.join(binding['state']['declarations']) or '    '
    setup = '\n        '.join('        ' + line for line in binding['setup'])
    attack = '\n        '.join('        ' + line for line in binding['attack'])
    post = '\n        '.join('        ' + line for line in binding['post'])
    sanity = '\n        '.join('        ' + line for line in binding['binding_sanity'])
    pre = ''
    if pre_lines:
        pre = ('\n        // --- pre-capture: phase \'pre\' observables, '
               'snapshotted BEFORE the attack ---\n'
               + '\n'.join('        ' + line for line in pre_lines) + '\n')
    p, i, v = expressions['preconditions'], expressions['safety'], expressions['effects']
    return f'''
// ---------------------------------------------------------------------------
// new-SC injection: generated by evaluation/new_sc_injection_02/new_sc.py
// (deterministic, zero model calls). Case: {case_key}.
// Everything above this line is the original stage-1 slice, byte-identical
// (see sc-spec.json slice.prefix_sha256); this appended block is the whole
// of the stage-2 merge. P/I/V below are byte-identical to the compiled claim
// in constraints.json (the same source the Z3 queries use); only the symbol
// bindings come from bindings/{case_key}.json.  phase 'pre' symbols are
// snapshotted BEFORE the attack; the P/I/V booleans are evaluated after
// the post-state observables.
// ---------------------------------------------------------------------------
contract {CONTRACT_NAME} is {inherits} {{
    {state}

    event Stage2Verdict(bool pHolds, bool iHolds, bool vHolds);

    // setUp is inherited from the PoC test contract; the scenario setup below
    // belongs to the attack test itself (it declares its own local addresses).
    function testStage2InjectedInvariants() public {{
        // --- scenario setup (the PoC's pre-attack state) ---
{setup}
{pre}
        // --- attack action (the PoC scenario's T transition) ---
{attack}

        // --- post-state observables ---
{post}

        // --- stage-2 claim, translated against the bindings ---
        // P (preconditions):   {p['source']}
        bool pHolds = {p['solidity']};
        // I (safety):          {i['source']}
        bool iHolds = {i['solidity']};
        // V (effects):         {v['source']}
        bool vHolds = {v['solidity']};

        emit Stage2Verdict(pHolds, iHolds, vHolds);
        console.log("STAGE2_VERDICT", string(abi.encodePacked(
            '{{\\"p\\":', pHolds ? "true" : "false",
            ',\\"i\\":', iHolds ? "true" : "false",
            ',\\"v\\":', vHolds ? "true" : "false", '}}')));

        // The test hard-fails ONLY on binding impossibilities; a violated I
        // is the expected finding on vulnerable code, not a test failure.
{sanity}
    }}
}}
'''


def check_binding_schema(binding, case_key, plan):
    """Mechanical gate on the ONE human input: structure, self-consistency,
    and type/unit alignment against formal-plan.json.  A mis-typed or
    mis-united binding would otherwise compile fine and produce a confidently
    wrong four-branch verdict; it fails HERE, before any file is written."""
    def bad(msg):
        fail(f'binding map {msg}')

    if set(binding) != BINDING_TOP_KEYS:
        bad(f'top-level keys must be exactly {sorted(BINDING_TOP_KEYS)}')
    if binding['schema_version'] != BINDING_SCHEMA_VERSION:
        bad(f'unsupported schema_version {binding["schema_version"]!r}')
    if binding['case_key'] != case_key:
        bad(f'case_key {binding["case_key"]!r} != {case_key!r} '
            f'(a binding authored for another case)')
    if not (isinstance(binding['binding_provenance'], str)
            and binding['binding_provenance'].strip()):
        bad('binding_provenance must be a nonempty string (disclose the '
            'binding authorship and any unit scaling here)')
    state = binding['state']
    if not isinstance(state, dict) or set(state) != {'inherits', 'declarations'}:
        bad("state must have exactly keys 'inherits' and 'declarations'")
    if not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', state['inherits'] or ''):
        bad(f'state.inherits {state["inherits"]!r} is not a contract identifier')
    if not (isinstance(state['declarations'], list)
            and all(isinstance(x, str) and x.strip()
                    for x in state['declarations'])):
        bad('state.declarations must be a list of nonempty Solidity lines')
    for key in ('setup', 'attack', 'post', 'binding_sanity'):
        rows = binding[key]
        if not (isinstance(rows, list)
                and all(isinstance(x, str) and x.strip() for x in rows)):
            bad(f'{key} must be a list of nonempty Solidity lines')

    symbols = binding['symbols']
    if not (isinstance(symbols, dict) and symbols):
        bad('symbols must be a nonempty object')
    for name, row in sorted(symbols.items()):
        where = f'symbol {name!r}'
        if not isinstance(row, dict) or set(row) != SYMBOL_KEYS:
            bad(f'{where} keys must be exactly {sorted(SYMBOL_KEYS)}')
        if row['phase'] not in BINDING_PHASES:
            bad(f'{where} phase {row["phase"]!r} not in {list(BINDING_PHASES)}')
        if row['type'] not in BINDING_TYPES:
            bad(f'{where} type {row["type"]!r} not in {list(BINDING_TYPES)}')
        if not (isinstance(row['expr'], str) and row['expr'].strip()):
            bad(f'{where} expr must be a nonempty Solidity expression')
        if not (isinstance(row['binding_description'], str)
                and row['binding_description'].strip()):
            bad(f'{where} binding_description must be a nonempty string')
        item = plan.get('symbols', {}).get(name)
        if item is None:
            bad(f'{where} is absent from formal-plan symbols')
            continue
        allowed = SORT_TO_TYPES.get(item['sort'])
        if allowed is None:
            bad(f'{where}: formal-plan declares unknown sort {item["sort"]!r}')
        elif row['type'] not in allowed:
            bad(f'{where}: formal-plan sort {item["sort"]!r} requires type '
                f'in {list(allowed)}, got {row["type"]!r}')
        if item['sort'] == 'int':
            if row['unit'] != item.get('unit'):
                bad(f'{where}: unit {row["unit"]!r} != formal-plan unit '
                    f'{item.get("unit")!r} -- numeric bindings must bind the '
                    f'plan-declared unit, with any wei->token scaling written '
                    f'explicitly inside expr, never silently')
        elif row['unit'] is not None:
            bad(f'{where}: unit must be null for non-numeric bindings')


def check_binding_coverage(symbols, claim, plan):
    """Pre-flight version of the stage3 binding rule: every symbol the P/I/V
    expressions actually reference must be bound, and no extra bindings.
    Catches a missing binding BEFORE any file is written (fail-fast) instead
    of at ingest time.  Variable collection is the shared lib/dsl.py
    traversal (same skeleton the Z3 side uses), not a local re-derivation."""
    required = set()
    for kind in ('preconditions', 'safety', 'effects'):
        required |= dsl.variables(claim['properties'][kind]['expression'])
    plan_symbols = set(plan['symbols'])
    unknown = sorted(required - plan_symbols)
    if unknown:
        fail(f'P/I/V reference symbols absent from formal-plan: {unknown}')
    bound = set(symbols)
    missing = sorted(required - bound)
    extra = sorted(bound - required)
    if missing:
        fail(f'binding map missing symbols referenced by P/I/V: {missing}')
    if extra:
        fail(f'binding map has symbols not referenced by P/I/V: {extra}')


def adjudicate(p, i, v):
    if not p:
        return 'precondition_mismatch'
    if v and not i:
        return 'violation_reproduced'
    if v and i:
        return 'i_too_weak'
    return 'violation_not_observed'


def _exp_label(out_root):
    """Label of an experiment workspace in verdict/sc-spec records: relative
    to this directory when inside it, else the absolute path."""
    try:
        return str(out_root.relative_to(HERE))
    except ValueError:
        return str(out_root)


def resolve_io(case_key, batch_name, experiment=None):
    """Path resolution for one case.

    Default: the frozen batch run + the checked-in binding map, outputs to
    this directory.  --experiment: an isolated bisection workspace -- a COPY
    of the frozen run under <experiment>/run/ (carrying the variant under
    test: e.g. a re-formalized constraints.json) plus an optional variant
    binding <experiment>/binding.json (the checked-in binding is used when
    absent).  Experiment outputs never touch the checked-in case-named
    artifacts, and a frozen batch run is never pointed at directly."""
    if experiment is None:
        return (EVAL / batch_name / 'runs' / case_key,
                HERE / 'bindings' / f'{case_key}.json',
                HERE)
    exp = Path(experiment)
    if not exp.is_absolute():
        exp = HERE / exp
    binding_path = exp / 'binding.json'
    if not binding_path.is_file():
        binding_path = HERE / 'bindings' / f'{case_key}.json'
    return exp / 'run', binding_path, exp


def run_case(case_key, batch_name, experiment=None):
    """One case end-to-end: merge -> execute -> adjudicate -> ingest.

    experiment: a bisection workspace directory (see resolve_io).  None runs
    the frozen batch case with the checked-in binding and writes the
    case-named artifacts to this directory (default path, byte-identical
    across reruns); a workspace runs the variant in isolation."""
    run, binding_path, out_root = resolve_io(case_key, batch_name, experiment)
    case_dir = CORPUS / case_key
    for path, what in ((run, 'stage-2 run'), (case_dir, 'corpus case dir'),
                       (binding_path, 'binding map')):
        if not path.is_dir() and not path.is_file():
            if what == 'binding map':
                fail(f'{what} missing: {path} '
                     f'(generate a skeleton: new_sc.py --template {case_key})')
            if experiment is not None and what == 'stage-2 run':
                fail(f'{what} missing: {path} -- an experiment workspace needs '
                     f'a COPY of the frozen run under <experiment>/run/ '
                     f'(never point --experiment at a frozen batch)')
            fail(f'{what} missing: {path}')

    slice_path = case_dir / 'contract.flattened.t.sol'
    slice_bytes = slice_path.read_bytes()
    prov = check_provenance(run, case_key, case_dir, slice_bytes)

    binding = json.loads(binding_path.read_text())
    symbols = binding['symbols']
    bundle = json.loads((run / 'constraints.json').read_text())
    claim = next(row for row in bundle['claims'] if row['id'] == CLAIM_ID)
    plan = json.loads((run / 'formal-plan.json').read_text())

    check_binding_schema(binding, case_key, plan)
    check_binding_coverage(symbols, claim, plan)

    # Phase 'pre' symbols are snapshotted before the attack and the P/I/V
    # translation resolves them to the snapshots (enforced 'phase' semantics).
    translate_symbols = build_translate_symbols(symbols)
    pre_lines = pre_capture_sol(symbols)

    def compile_expr(kind):
        source = claim['properties'][kind]['expression']
        return {'source': json.dumps(source, ensure_ascii=False),
                'solidity': translate(source, translate_symbols)}

    expressions = {kind: compile_expr(kind)
                   for kind in ('preconditions', 'safety', 'effects')}

    # --- step 1: merge into ONE file (slice prefix + appended guard) ---
    out = out_root / f'new_sc__{case_key}'
    if out.exists():
        fail(f'refusing to overwrite existing new-SC dir: {out}')
    out.mkdir()
    guard_bytes = guard_sol(binding, expressions, case_key, pre_lines).encode()
    new_bytes = slice_bytes + guard_bytes
    (out / 'new_sc.t.sol').write_bytes(new_bytes)
    (out / 'foundry.toml').write_text(FOUNDARY_TOML)

    prefix_ok = sha256_bytes(new_bytes[:len(slice_bytes)]) == sha256_bytes(slice_bytes)
    if not prefix_ok:
        fail('internal error: slice prefix check failed')

    sc_spec = {
        'schema_version': 'stage2-sc-spec/1',
        'case_key': case_key,
        'stage2_run': {
            'batch': batch_name,
            'run_dir': str(run.relative_to(REPO)),
            'claim_id': CLAIM_ID,
        },
        'slice': {
            'source': str(case_dir),
            'file': 'contract.flattened.t.sol',
            'sha256': sha256_bytes(slice_bytes),
            'prefix_sha256': sha256_bytes(new_bytes[:len(slice_bytes)]),
            'slice_length_bytes': len(slice_bytes),
            'merge': 'slice bytes verbatim prefix + appended guard contract '
                     '(the slice text is never edited)',
            'poc_status': 'passing (verified_flatten_pass corpus)',
        },
        'claim': {
            'preconditions': claim['properties']['preconditions']['expression'],
            'safety': claim['properties']['safety']['expression'],
            'effects': claim['properties']['effects']['expression'],
            'source_of_truth': 'constraints.json (same expressions the Z3 '
                               'queries use; never re-derived)',
        },
        'symbol_bindings': {
            name: {'phase': row['phase'], 'type': row['type'],
                   'expr': row['expr'],
                   'binding_description': row['binding_description']}
            for name, row in symbols.items()},
        'code_queries_after_binding': {
            'P_and_T': 'attack executed and bound P holds',
            'P_and_T_and_not_I': 'bound P holds and bound I violated',
            'P_and_T_and_V': 'bound P holds and bound V observed',
            'P_and_T_and_not_V': 'bound P holds and bound V not observed',
        },
        'injected': {
            'guard_contract': CONTRACT_NAME,
            'test': f'{CONTRACT_NAME}.testStage2InjectedInvariants',
            'runner': 'forge test (full suite: PoC + guard)',
            'verdict_line': 'STAGE2_VERDICT',
            'provenance_checks': 'case_id / report_path / report_sha256 / '
                                 'declared_code_sha256 all verified',
            'pre_capture_symbols': sorted(name for name, row in symbols.items()
                                          if row['phase'] == 'pre'),
            'target_test': prov.get('target_test'),
        },
        'model_calls': 0,
    }
    if experiment is not None:
        sc_spec['stage2_run']['experiment'] = _exp_label(out_root)
    (out / 'sc-spec.json').write_text(
        json.dumps(sc_spec, ensure_ascii=False, indent=2) + '\n')

    # --- step 2: execute with forge (full suite = slice integrity + guard) ---
    forge = subprocess.run(['forge', 'test', '-vv'], cwd=str(out),
                           capture_output=True, text=True)
    log = forge.stdout + forge.stderr
    forge_log = out_root / f'forge__{case_key}.log'
    forge_log.write_text(log)

    target_test = prov.get('target_test')
    if target_test:
        passed = re.search(r'\[PASS\][^\n]*' + re.escape(target_test), log)
        if not passed:
            fail(f'slice integrity: PoC test {target_test} not PASS in forge '
                 f'output -- see {forge_log.name}')

    match = re.search(r'STAGE2_VERDICT (\{.*\})', log)
    if not match:
        fail(f'no STAGE2_VERDICT line in forge output -- see {forge_log.name}')
    piv = json.loads(match.group(1))
    p, i, v = piv['p'], piv['i'], piv['v']
    verdict = adjudicate(p, i, v)

    record = {
        'schema_version': 'stage2-newsc-verdict/1',
        'case_key': case_key,
        'piv': piv,
        'verdict': verdict,
        'verdict_table': 'pre-registered in evaluation/new_sc_injection_02/README.md',
        'forge_log': forge_log.name,
        'guard_test_passed': 'PASS' in log,
        'poc_test_passed': bool(target_test),
        'model_calls': 0,
    }
    if experiment is not None:
        record['experiment'] = _exp_label(out_root)
    verdict_path = out_root / f'verdict__{case_key}.json'
    verdict_path.write_text(
        json.dumps(record, ensure_ascii=False, indent=2) + '\n')
    print('verdict:', verdict, piv)

    # --- step 3: ingest into stage 3 (on a COPY; frozen runs never touched) ---
    run_copy = out_root / f'run_copy__{case_key}'
    if run_copy.exists():
        fail(f'refusing to overwrite existing run copy: {run_copy}')
    shutil.copytree(run, run_copy)

    feedback = {
        'schema_version': 'stage3-consistency-feedback/1',
        'claim_id': CLAIM_ID,
        'symbol_bindings': {
            name: {'status': 'bound', 'binding': row['binding_description']}
            for name, row in symbols.items()},
        'code_query_results': stage3_consistency.queries_from_piv(p, i, v),
        'poc': {
            'executed': True,
            'description': (
                'new-SC guard test Stage2InvariantGuard.testStage2InjectedInvariants: '
                'PoC scenario re-run with recorded logs; P/I/V expressions from '
                'stage-2 constraints.json evaluated against bound Solidity '
                'observables (forge, zero model calls)'),
        },
    }
    feedback_path = out_root / f'stage3_feedback__{case_key}.json'
    feedback_path.write_text(json.dumps(feedback, ensure_ascii=False, indent=2) + '\n')

    result = subprocess.run(
        [sys.executable, str(MAIN_PY), 'stage3-feedback', str(run_copy),
         '--feedback', str(feedback_path)],
        cwd=str(REPO), capture_output=True, text=True)
    print(result.stdout[-800:] or result.stderr[-800:])
    consistency = run_copy / 'stage3-consistency.json'
    if not consistency.is_file():
        fail('ingest did not write stage3-consistency.json')
    got = json.loads(consistency.read_text())['consistency_verdict']
    print('stage3 consistency_verdict:', got)

    # Archive the ingest evidence; a rerun that produces a DIFFERENT result is
    # refused (staleness guard), an identical one is a no-op.
    archive = out_root / f'stage3-consistency__{case_key}.json'
    if archive.exists() and archive.read_text() != consistency.read_text():
        fail(f'archived ingest evidence differs from this run: {archive.name}')
    archive.write_text(consistency.read_text())

    if got != verdict and verdict in ('violation_reproduced',
                                      'violation_not_reproduced'):
        fail(f'verdict mismatch: newsc={verdict} ingest={got}')
    record['stage3_consistency_verdict'] = got
    verdict_path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n')
    return record


def emit_template(case_key, batch_name):
    """Write a schema-conformant binding SKELETON for one case.

    Every symbol the core claim references is pre-filled from formal-plan
    (name, type derived from sort, unit from plan), so the author fills in
    exprs and the four code segments and nothing else -- adding a case is
    fill-in-the-blanks, never "write nine fields from a blank page".
    Deterministic, zero model calls, refuses to overwrite."""
    run = EVAL / batch_name / 'runs' / case_key
    if not run.is_dir():
        fail(f'stage-2 run missing: {run}')
    constraints = run / 'constraints.json'
    if not constraints.is_file():
        fail(f'run has no constraints.json: {constraints}')
    bundle = json.loads(constraints.read_text())
    claim = next((row for row in bundle.get('claims', [])
                  if row.get('id') == CLAIM_ID), None)
    if claim is None:
        fail(f'run has no {CLAIM_ID} in constraints.json')
    plan = json.loads((run / 'formal-plan.json').read_text())

    required = set()
    for kind in ('preconditions', 'safety', 'effects'):
        required |= dsl.variables(claim['properties'][kind]['expression'])
    absent = sorted(required - set(plan.get('symbols', {})))
    if absent:
        fail(f'P/I/V reference symbols absent from formal-plan: {absent}')
    symbols = {}
    for name in sorted(required):
        item = plan['symbols'][name]
        allowed = SORT_TO_TYPES.get(item['sort'])
        if not allowed:
            fail(f'symbol {name!r}: formal-plan declares unknown sort '
                 f'{item["sort"]!r}')
        symbols[name] = {
            'phase': 'post',
            'type': allowed[0],
            'expr': 'TODO_observable_expr',
            'unit': item.get('unit'),
            'binding_description': f'TODO: {item.get("meaning", "bind this observable")}',
        }
    binding = {
        'schema_version': BINDING_SCHEMA_VERSION,
        'case_key': case_key,
        'binding_provenance': ('skeleton generated by new_sc.py --template '
                               '(deterministic, zero model calls); '
                               'hand-filled afterwards'),
        'state': {'inherits': 'TODO_PoC_TEST_CONTRACT', 'declarations': []},
        'setup': ['// TODO: scenario setup lines (the PoC pre-attack state)'],
        'attack': ['// TODO: attack action lines (the T transition)'],
        'post': ['// TODO: post-state observable computation lines'],
        'binding_sanity': ['// TODO: binding-impossibility asserts '
                           '(message prefix "STAGE2_BINDING_ERROR: ")'],
        'symbols': symbols,
    }
    path = HERE / 'bindings' / f'{case_key}.json'
    if path.exists():
        fail(f'refusing to overwrite existing binding map: {path.name}')
    path.write_text(json.dumps(binding, ensure_ascii=False, indent=2) + '\n')
    suffix = '' if batch_name == DEFAULT_BATCH else f' --batch {batch_name}'
    print(f'template written: {path.name} ({len(symbols)} symbols)')
    print('fill every TODO field (schema and guide: bindings/README.md), '
          'then run:')
    print(f'  new_sc.py {case_key}{suffix}')
    return path


def discover_cases(batch_name):
    """Every run in the batch whose constraints.json carries the core claim."""
    for run in sorted((EVAL / batch_name / 'runs').iterdir()):
        constraints = run / 'constraints.json'
        if not constraints.is_file():
            continue
        try:
            bundle = json.loads(constraints.read_text())
        except json.JSONDecodeError:
            continue
        if any(row.get('id') == CLAIM_ID for row in bundle.get('claims', [])):
            yield run.name


def summarize(records, batch_name):
    counts = {}
    for record in records:
        key = (record.get('verdict')
               or 'error: ' + record['error'].split(':', 1)[0])
        counts[key] = counts.get(key, 0) + 1
    return {
        'schema_version': 'stage2-newsc-adjudication-summary/1',
        'batch': batch_name,
        'model_calls': 0,
        'cases': records,
        'counts': counts,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('case_key', nargs='*',
                        help='one case key (or omit and use --all)')
    parser.add_argument('--batch', default=DEFAULT_BATCH)
    parser.add_argument('--all', action='store_true',
                        help='adjudicate every case in --batch whose stage-2 '
                             'run compiled a core claim; cases without a '
                             'binding map are reported as errors, never '
                             'silently skipped')
    parser.add_argument('--template', action='store_true',
                        help='write a schema-conformant binding skeleton for '
                             'case_key (symbols pre-filled from formal-plan), '
                             'then exit; refuses to overwrite')
    parser.add_argument('--experiment', default=None, metavar='DIR',
                        help='run the case against an isolated bisection '
                             'workspace (reflux attribution): <DIR>/run = a '
                             'COPY of the frozen run carrying the variant '
                             'under test, <DIR>/binding.json = optional '
                             'variant binding. All outputs stay in DIR')
    opts = parser.parse_args()
    if opts.template:
        if opts.all or opts.experiment or len(opts.case_key) != 1:
            parser.error('--template needs exactly one case_key '
                         '(no --all / --experiment)')
        emit_template(opts.case_key[0], opts.batch)
        return
    if opts.experiment:
        if opts.all:
            parser.error('--experiment and --all are mutually exclusive')
        if len(opts.case_key) != 1:
            parser.error('--experiment needs exactly one case_key')
    if opts.all and opts.case_key:
        parser.error('case_key and --all are mutually exclusive')
    if not opts.all and len(opts.case_key) != 1:
        parser.error('exactly one case_key required (or --all)')
    if opts.all:
        case_keys = list(discover_cases(opts.batch))
        if not case_keys:
            fail(f'no runs with a {CLAIM_ID} in batch {opts.batch!r}')
    else:
        case_keys = [opts.case_key[0]]

    records = []
    for case_key in case_keys:
        try:
            record = run_case(case_key, opts.batch, opts.experiment)
        except CaseError as exc:
            print(f'[{case_key}] ERROR: {exc}')
            record = {'case_key': case_key, 'error': str(exc)}
        records.append(record)

    if len(records) > 1:
        summary = summarize(records, opts.batch)
        summary_path = HERE / f'adjudication_summary__{opts.batch}.json'
        summary_path.write_text(
            json.dumps(summary, ensure_ascii=False, indent=2) + '\n')
        print(f'\n== adjudication summary ({opts.batch}) ==')
        for record in records:
            if 'verdict' in record:
                print(f"  {record['piv']}  {record['verdict']:>22}  "
                      f"{record['case_key']}")
            else:
                print(f"  {'--':>9} {'[error]':>22}  {record['case_key']}"
                      f"  ({record['error'].split(':', 1)[0]})")
        for key, count in sorted(summary['counts'].items()):
            print(f'  {count:2d} x {key}')
        print(f'  written: {summary_path.name}')
    if any('error' in record for record in records):
        sys.exit(1)


if __name__ == '__main__':
    main()
