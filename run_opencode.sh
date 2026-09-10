#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="${SCRIPT_DIR}/config/llm.env"

if [[ -f "${CONFIG_FILE}" ]]; then
  set -a
  source "${CONFIG_FILE}"
  set +a
fi

exec opencode "$@"
