#!/usr/bin/env bash
# 差异重放实验的完整执行入口（产物全部落在工作区内，可再生即删）。
set -euo pipefail
cd "$(dirname "$0")/.."
CASE=Merkl_T4ExvutBBXC__9JnmzBSjjfp__No9Y37ndFs5
rm -rf "bisection/$CASE/new_sc__$CASE" "bisection/$CASE/run_copy__$CASE" \
       "bisection/$CASE/forge__$CASE.log" "bisection/$CASE/verdict__$CASE.json" \
       "bisection/$CASE/stage3_feedback__$CASE.json"
exec /root/.local/share/uv/tools/halmos/bin/python new_sc.py "$CASE" \
    --batch final_holdout_01 --experiment "bisection/$CASE"
