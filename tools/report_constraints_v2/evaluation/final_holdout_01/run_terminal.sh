#!/usr/bin/env bash
# One-shot terminal launcher for the final_holdout_01 holdout measurement.
# Frozen 2026-10-06 BEFORE any live-3/live-4 iteration; never inspected since.
# Runs ONCE with the final configuration: semantic-live-4 prompt text plus the
# pre-registered hex gate fix. Ten cases across two manifests (the batch runner
# caps a manifest at five cases), both into runs/ with identical flags matching
# the live batches exactly (incl. --formal-retries 1, whose reachability caveat
# is disclosed in the terminal report).
# Invoked via: bash run_terminal.sh   (from anywhere; all paths are absolute)
set -euo pipefail
PY=/root/.local/share/uv/tools/halmos/bin/python
HERE=/root/sc_slicer_standalone/tools/report_constraints_v2/evaluation/final_holdout_01
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
