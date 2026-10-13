#!/bin/bash
# Run the injected new-SC guard test, adjudicate the four-branch verdict, and
# ingest it through the existing stage3-feedback loop (on a run COPY -- frozen
# runs are never touched). Zero model calls.
set -euo pipefail

PY=/root/.local/share/uv/tools/halmos/bin/python
HERE="$(cd "$(dirname "$0")" && pwd)"
REPO="$HERE/../../../.."
CASE_KEY=Ekubo_3FTodhsvBkM__9MpUh5dZn3f__nFbsAHPP4jP
NEW_SC="$HERE/new_sc__$CASE_KEY"
RUN_COPY="$HERE/run_copy__$CASE_KEY"
LIVE_RUN="$HERE/../prompt_live4_blind_01/runs/$CASE_KEY"

cd "$NEW_SC"
forge test --match-contract Stage2InvariantGuard -vv > "$HERE/forge.log" 2>&1
cd "$HERE"

"$PY" - "$HERE" "$CASE_KEY" "$LIVE_RUN" "$RUN_COPY" <<'EOF'
import json, re, shutil, subprocess, sys
from pathlib import Path

here = Path(sys.argv[1])
case_key = sys.argv[2]
live_run = Path(sys.argv[3])
run_copy = Path(sys.argv[4])
new_sc = here / f'new_sc__{case_key}'

log = (here / 'forge.log').read_text()
match = re.search(r'STAGE2_VERDICT (\{.*\})', log)
if not match:
    sys.exit('no STAGE2_VERDICT line in forge output')
piv = json.loads(match.group(1))
p, i, v = piv['p'], piv['i'], piv['v']

if not p:
    verdict = 'precondition_mismatch'
elif v and not i:
    verdict = 'violation_reproduced'
elif v and i:
    verdict = 'i_too_weak'
else:
    verdict = 'violation_not_observed'

record = {
    'schema_version': 'stage2-newsc-verdict/1',
    'case_key': case_key,
    'piv': piv,
    'verdict': verdict,
    'verdict_table': 'pre-registered in evaluation/new_sc_injection_01/README.md',
    'forge_log': 'forge.log',
    'guard_test_passed': 'PASS' in log,
    'model_calls': 0,
}
(here / 'verdict.json').write_text(
    json.dumps(record, ensure_ascii=False, indent=2) + '\n')
print('verdict:', verdict, piv)

# --- map to the existing stage3-consistency feedback and ingest (on a copy) ---
if run_copy.exists():
    sys.exit(f'refusing to overwrite existing run copy: {run_copy}')
shutil.copytree(live_run, run_copy)

binding = json.loads((here / 'bindings' / 'ekubo.json').read_text())
feedback = {
    'schema_version': 'stage3-consistency-feedback/1',
    'claim_id': 'core_claim',
    'symbol_bindings': {
        name: {'status': 'bound', 'binding': row['binding_description']}
        for name, row in binding['symbols'].items()},
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
feedback_path = here / 'stage3_feedback.json'
feedback_path.write_text(
    json.dumps(feedback, ensure_ascii=False, indent=2) + '\n')

result = subprocess.run(
    [sys.executable, str(Path(here).parents[3] / 'main.py'),
     'stage3-feedback', str(run_copy), '--feedback', str(feedback_path)],
    cwd=str(here.parents[3]), capture_output=True, text=True)
print(result.stdout[-800:] or result.stderr[-800:])
consistency = run_copy / 'stage3-consistency.json'
if consistency.is_file():
    got = json.loads(consistency.read_text())['consistency_verdict']
    print('stage3 consistency_verdict:', got)
    if got != verdict and verdict in ('violation_reproduced',
                                      'violation_not_reproduced'):
        sys.exit(f'verdict mismatch: newsc={verdict} ingest={got}')
EOF
