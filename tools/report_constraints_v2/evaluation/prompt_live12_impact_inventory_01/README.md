# semantic-live-12 staged Impact inventory blind evaluation

Ten fresh reports are frozen before calls. The selector excludes historical case IDs, report hashes, and normalized input hashes; it does not inspect Impact section presence or content when selecting.

Configuration: DeepSeek `deepseek-flash`, `semantic-live`, concurrency 2, one readiness/element/formalization retry, lean formal input, continue on review, claim verdict `signals`. The pipeline extracts Impact statements from a restricted Impact-only catalog, extracts core elements separately, merges the validated inventory, then formalizes each impact independently. Inputs are public submission reports from the frozen source corpus.

`run_batches.py` writes outputs under `runs/`; `replay_all.py` verifies artifacts with zero model calls. Do not rerun the selector after model execution.
