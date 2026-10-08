#!/usr/bin/env bash
# One-shot terminal launcher for the final_holdout_02 holdout measurement.
# Frozen 2026-10-08 BEFORE any blind-batch measurement of the semantic-live-5
# structural changes. Never inspected since.
# Runs ONCE with the then-current semantic-live prompt (the run records its
# own prompt snapshot and prompt_features). Ten cases across two manifests
# (the batch runner caps a manifest at five cases), both into runs/ with flags
# matching the live batches exactly (incl. --formal-retries 1, whose
# reachability caveat is disclosed in the README).
# Invoked via: bash run_terminal.sh   (from anywhere; all paths are absolute)
set -euo pipefail
PY=/root/.local/share/uv/tools/halmos/bin/python
HERE=/root/sc_slicer_standalone/tools/report_constraints_v2/evaluation/final_holdout_02
cd /root/sc_slicer_standalone
for MANIFEST in manifest_a.json manifest_b.json; do
  "$PY" main.py batch \
    --manifest "$HERE/$MANIFEST" \
    --output "$HERE/runs" \
    --allow-report-upload \
    --prompt-version semantic-live \
    --readiness-retries 1 --element-retries 1 --formal-retries 1 \
    --lean-formal-input --continue-on-review --resume
done
