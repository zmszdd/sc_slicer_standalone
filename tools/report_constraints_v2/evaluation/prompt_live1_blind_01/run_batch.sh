#!/usr/bin/env bash
# One-shot launcher for the semantic-live-1 blind batch (prompt_live1_blind_01).
# Invoked via: bash run_batch.sh   (from anywhere; all paths are absolute)
set -euo pipefail
PY=/root/.local/share/uv/tools/halmos/bin/python
HERE=/root/sc_slicer_standalone/tools/report_constraints_v2/evaluation/prompt_live1_blind_01
cd /root/sc_slicer_standalone
exec "$PY" main.py batch \
  --manifest "$HERE/manifest.json" \
  --output "$HERE/runs" \
  --allow-report-upload \
  --prompt-version semantic-live \
  --readiness-retries 1 --element-retries 1 --formal-retries 1 \
  --lean-formal-input --continue-on-review
