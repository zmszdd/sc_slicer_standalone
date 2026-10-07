#!/usr/bin/env bash
# One-shot launcher for the live-3 and live-4 same-model dual reviews
# (10 + 10 deepseek-flash calls, heterogeneous auditor prompt).
# Invoked via: bash run_dual_review.sh   (from anywhere; absolute paths)
set -euo pipefail
PY=/root/.local/share/uv/tools/halmos/bin/python
BASE=/root/sc_slicer_standalone/tools/report_constraints_v2/evaluation
cd "$BASE/prompt_live3_blind_01"
"$PY" dual_review.py > dual_review.log 2>&1
echo "live3 dual exit: $?"
cd "$BASE/prompt_live4_blind_01"
"$PY" dual_review.py > dual_review.log 2>&1
echo "live4 dual exit: $?"
