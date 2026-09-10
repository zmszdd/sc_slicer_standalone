#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TOOL_DIR="${SCRIPT_DIR}/tools/sol_resurrect_tool"

if [[ "${1:-}" == "--smoke" ]]; then
  exec "${TOOL_DIR}/quicktest.sh"
fi

exec python3 "${TOOL_DIR}/main.py" "$@"
