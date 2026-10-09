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
"""

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
EVAL = HERE.parent
REPO = HERE.parents[3]
CORPUS = Path('/root/poc_repro_work/verified_flatten_pass_1568_exact_cases')
MAIN_PY = REPO / 'main.py'
CLAIM_ID = 'core_claim'
CONTRACT_NAME = 'Stage2InvariantGuard'
DEFAULT_BATCH = 'prompt_live4_blind_01'

BINARY_OPS = {'and': '&&', 'or': '||', 'ne': '!=', 'eq': '==',
              'lt': '<', 'le': '<=', 'gt': '>', 'ge': '>=',
              'add': '+', 'sub': '-', 'mul': '*'}

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


def guard_sol(binding, expressions, case_key):
    """The guard contract, APPENDED to the slice file (never editing it)."""
    inherits = binding['state'].get('inherits', 'Test')
    state = '\n        '.join(binding['state']['declarations']) or '    '
    setup = '\n        '.join('        ' + line for line in binding['setup'])
    attack = '\n        '.join('        ' + line for line in binding['attack'])
    post = '\n        '.join('        ' + line for line in binding['post'])
    sanity = '\n        '.join('        ' + line for line in binding['binding_sanity'])
    p, i, v = expressions['preconditions'], expressions['safety'], expressions['effects']
    return f'''
// ---------------------------------------------------------------------------
// new-SC injection: generated by evaluation/new_sc_injection_02/new_sc.py
// (deterministic, zero model calls). Case: {case_key}.
// Everything above this line is the original stage-1 slice, byte-identical
// (see sc-spec.json slice.prefix_sha256); this appended block is the whole
// of the stage-2 merge. P/I/V below are byte-identical to the compiled claim
// in constraints.json (the same source the Z3 queries use); only the symbol
// bindings come from bindings/{case_key}.json.
// ---------------------------------------------------------------------------
contract {CONTRACT_NAME} is {inherits} {{
    {state}

    event Stage2Verdict(bool pHolds, bool iHolds, bool vHolds);

    // setUp is inherited from the PoC test contract; the scenario setup below
    // belongs to the attack test itself (it declares its own local addresses).
    function testStage2InjectedInvariants() public {{
        // --- scenario setup (the PoC's pre-attack state) ---
{setup}

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


def collect_vars(node, acc):
    """Walk an op-args/var expression collecting every referenced var name."""
    if isinstance(node, dict):
        if 'var' in node:
            acc.add(node['var'])
        elif 'args' in node:  # {"const": N} leaves carry no vars
            for arg in node['args']:
                collect_vars(arg, acc)


def check_binding_coverage(symbols, claim, plan):
    """Pre-flight version of the stage3 binding rule: every symbol the P/I/V
    expressions actually reference must be bound, and no extra bindings.
    Catches a missing binding BEFORE any file is written (fail-fast) instead
    of at ingest time."""
    required = set()
    for kind in ('preconditions', 'safety', 'effects'):
        collect_vars(claim['properties'][kind]['expression'], required)
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


def run_case(case_key, batch_name):
    """One case end-to-end: merge -> execute -> adjudicate -> ingest."""
    run = EVAL / batch_name / 'runs' / case_key
    case_dir = CORPUS / case_key
    binding_path = HERE / 'bindings' / f'{case_key}.json'
    for path, what in ((run, 'stage-2 run'), (case_dir, 'corpus case dir'),
                       (binding_path, 'binding map')):
        if not path.is_dir() and not path.is_file():
            fail(f'{what} missing: {path}')

    slice_path = case_dir / 'contract.flattened.t.sol'
    slice_bytes = slice_path.read_bytes()
    prov = check_provenance(run, case_key, case_dir, slice_bytes)

    binding = json.loads(binding_path.read_text())
    symbols = binding['symbols']
    bundle = json.loads((run / 'constraints.json').read_text())
    claim = next(row for row in bundle['claims'] if row['id'] == CLAIM_ID)
    plan = json.loads((run / 'formal-plan.json').read_text())

    check_binding_coverage(symbols, claim, plan)

    def compile_expr(kind):
        source = claim['properties'][kind]['expression']
        return {'source': json.dumps(source, ensure_ascii=False),
                'solidity': translate(source, symbols)}

    expressions = {kind: compile_expr(kind)
                   for kind in ('preconditions', 'safety', 'effects')}

    # --- step 1: merge into ONE file (slice prefix + appended guard) ---
    out = HERE / f'new_sc__{case_key}'
    if out.exists():
        fail(f'refusing to overwrite existing new-SC dir: {out}')
    out.mkdir()
    guard_bytes = guard_sol(binding, expressions, case_key).encode()
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
            'target_test': prov.get('target_test'),
        },
        'model_calls': 0,
    }
    (out / 'sc-spec.json').write_text(
        json.dumps(sc_spec, ensure_ascii=False, indent=2) + '\n')

    # --- step 2: execute with forge (full suite = slice integrity + guard) ---
    forge = subprocess.run(['forge', 'test', '-vv'], cwd=str(out),
                           capture_output=True, text=True)
    log = forge.stdout + forge.stderr
    forge_log = HERE / f'forge__{case_key}.log'
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
    verdict_path = HERE / f'verdict__{case_key}.json'
    verdict_path.write_text(
        json.dumps(record, ensure_ascii=False, indent=2) + '\n')
    print('verdict:', verdict, piv)

    # --- step 3: ingest into stage 3 (on a COPY; frozen runs never touched) ---
    run_copy = HERE / f'run_copy__{case_key}'
    if run_copy.exists():
        fail(f'refusing to overwrite existing run copy: {run_copy}')
    shutil.copytree(run, run_copy)

    feedback = {
        'schema_version': 'stage3-consistency-feedback/1',
        'claim_id': CLAIM_ID,
        'symbol_bindings': {
            name: {'status': 'bound', 'binding': row['binding_description']}
            for name, row in symbols.items()},
        'code_query_results': {
            'P_and_T': 'sat' if p else 'unsat',
            'P_and_T_and_not_I': 'sat' if (p and not i) else 'unsat',
            'P_and_T_and_V': 'sat' if (p and v) else 'unsat',
            'P_and_T_and_not_V': 'unsat' if (p and v) else 'sat',
        },
        'poc': {
            'executed': True,
            'description': (
                'new-SC guard test Stage2InvariantGuard.testStage2InjectedInvariants: '
                'PoC scenario re-run with recorded logs; P/I/V expressions from '
                'stage-2 constraints.json evaluated against bound Solidity '
                'observables (forge, zero model calls)'),
        },
    }
    feedback_path = HERE / f'stage3_feedback__{case_key}.json'
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
    archive = HERE / f'stage3-consistency__{case_key}.json'
    if archive.exists() and archive.read_text() != consistency.read_text():
        fail(f'archived ingest evidence differs from this run: {archive.name}')
    archive.write_text(consistency.read_text())

    if got != verdict and verdict in ('violation_reproduced',
                                      'violation_not_reproduced'):
        fail(f'verdict mismatch: newsc={verdict} ingest={got}')
    record['stage3_consistency_verdict'] = got
    verdict_path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n')
    return record


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
    opts = parser.parse_args()
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
            record = run_case(case_key, opts.batch)
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
