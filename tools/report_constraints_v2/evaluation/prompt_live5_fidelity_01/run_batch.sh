#!/usr/bin/env bash
# One-shot launcher for the current semantic-live fidelity batch (prompt_live5_fidelity_01).
# Five cases in one manifest (the batch runner caps a manifest at five
# cases).
# Invoked via: bash run_batch.sh   (from anywhere; all paths are absolute)
set -euo pipefail
PY=/root/.local/share/uv/tools/halmos/bin/python
HERE=/root/sc_slicer_standalone/tools/report_constraints_v2/evaluation/prompt_live5_fidelity_01
cd /root/sc_slicer_standalone
for MANIFEST in manifest_a.json; do
  "$PY" main.py batch \
    --manifest "$HERE/$MANIFEST" \
    --output "$HERE/runs" \
    --allow-report-upload \
    --prompt-version semantic-live \
    --readiness-retries 1 --element-retries 1 --formal-retries 1 \
    --lean-formal-input --continue-on-review --resume
done
