# Stage 2 frozen 50-report rerun

This run reuses the exact frozen manifests from `../prompt_live11_stage2_n50/` and writes outputs into this directory. It does not modify baseline outputs.

Configuration: DeepSeek `deepseek-flash`, `semantic-live`, concurrency 2, one element retry, one formalization retry, lean formal input, continue on review, claim verdict `signals`.

`RUN_METADATA.json` records the current source hashes and frozen selection hash.
