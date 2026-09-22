# Invariant-mining baselines

This directory records reproducible baseline runs used to connect dynamic
invariant mining with SC_Slicer.

## Layout

- `invcon/result-summary.json`: summary of the verified InvCon cached example.
- `invcon/output/`: local InvCon artifacts (ignored by Git).
- `trace2inv/output/`: local Trace2Inv artifacts (ignored by Git).

Run the InvCon cached example from the repository root:

```bash
scripts/baselines/reproduce_invcon.sh
```

Normalize the generated Daikon output:

```bash
python3 scripts/baselines/normalize_invcon.py \
  baselines/invcon/output/official_cached_case/TokenERC20.inv \
  -o baselines/invcon/output/official_cached_case/normalized-invariants.json
```

The script intentionally runs against the cache embedded in the official
image. Mounting an empty host directory as InvCon's `--workspace` hides that
cache and forces the legacy Etherscan crawler to run.

The next integration step is to normalize each tool's output into records
containing the contract, function, referenced state variables, predicate, and
training evidence. Those records can then become multi-seed inputs to
SC_Slicer.

Parse the result files packaged with the Trace2Inv artifact:

```bash
scripts/baselines/reproduce_trace2inv_precomputed.sh
```

Normalize the packaged Trace2Inv evidence logs:

```bash
python3 scripts/baselines/normalize_trace2inv.py \
  baselines/trace2inv/output/precomputed/raw \
  -o baselines/trace2inv/output/precomputed/normalized-evidence.json
```

This is an artifact-integrity check, not a live re-execution of blockchain
trace analysis. Live `main.py AC` still requires working Etherscan/RPC
configuration from the original artifact.
