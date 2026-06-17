# Changelog

## 0.2.0

- Removed the legacy v1 resurrection path and its `--resurrect` / `--v1` entry points.
- Promoted source-backed Resurrection V2 as the only resurrection pipeline.
- Moved the preflight source normalizer into `src/source_normalizer.rs`.
- Improved target-oriented analysis so functions are included only when their AST references the focus variable, with conservative fallbacks for complex statements.
- Kept quick slicing mode available for non-resurrection output.

## 0.1.0

- Initial standalone SC_Slicer CLI.
