# Changelog

## Unreleased

- Refactored stage 2 (`tools/report_constraints_v2/`) into two layers: `cli/` for
  entrypoints and `lib/` for shared modules. Implementation code no longer lives at
  the stage-2 root; the 14 root-level `.py` files are now 3-4 line compatibility
  shims that alias themselves into `sys.modules` so existing importers keep working
  unchanged.
- Merged same-layer modules: `evidence_catalog.py` + `report_readiness.py` ->
  `lib/ingest.py`; `symbolic_queries.py` + `review.py` -> `lib/solving.py`;
  `fidelity.py` + `mechanical_salvage.py` -> `lib/salvage.py`;
  `run_semantic_batch.py` + `verify_semantic.py` -> `cli/batch_verify.py`.
- `main.py` now resolves command scripts in `cli/` -> `lib/` -> stage-2 root order,
  and no longer lists `solving.py` / `salvage.py` as library-only modules (both are
  also command targets).
- Re-baselined the `code_sha256` fields in the 7 frozen `evaluation/` manifests so
  they resolve to the files that now contain the code. Stage-1 assets in
  `PROTECTED_HASHES.json` are unchanged (`main.py frozen` still passes 21/21).
- Stage 1 and stage 3 untouched.

## 0.2.0

- Removed the legacy v1 resurrection path and its `--resurrect` / `--v1` entry points.
- Promoted source-backed Resurrection V2 as the only resurrection pipeline.
- Moved the preflight source normalizer into `src/source_normalizer.rs`.
- Improved target-oriented analysis so functions are included only when their AST references the focus variable, with conservative fallbacks for complex statements.
- Kept quick slicing mode available for non-resurrection output.

## 0.1.0

- Initial standalone SC_Slicer CLI.
