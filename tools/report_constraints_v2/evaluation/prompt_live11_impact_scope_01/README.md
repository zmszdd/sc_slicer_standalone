# Stage 2 explicit Impact scope blind evaluation

Fresh ten report holdout frozen before model calls. The selector excludes prior case IDs, report hashes, and normalized input hashes; it does not inspect Impact section presence or content when choosing cases.

Configuration: DeepSeek `deepseek-flash`, `semantic-live`, concurrency 2, one element retry, one formalization retry, lean formal input, continue on review, claim verdict `signals`. The reports are public submissions from the frozen source corpus. Calls require the explicit `--allow-report-upload` flag.

Run `python select.py --source-root /root/poc_repro_work/verified_flatten_pass_1568_exact_cases --count 10` only before freezing; do not rerun after model execution. `run_batches.py` writes outputs under `runs/`.
