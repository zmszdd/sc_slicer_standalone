#!/usr/bin/env bash
set -Eeuo pipefail

# ============================================================
# Code4rena finding collector + Foundry flatten post-processor
#
# Fill in the configuration block below, then run:
#   bash scripts/code4rena/run_code4rena_flatten_pipeline.sh
#
# You can also override any variable from the command line:
#   PROJECT_ID=c9MhophgwGP LOCAL_REPO_DIR="/d/work/.../2025-06-panoptic" bash scripts/code4rena/run_code4rena_flatten_pipeline.sh
# ============================================================

# --------------------- Required parameters ---------------------
# Code4rena audit UID, for example: c9MhophgwGP
PROJECT_ID="${PROJECT_ID:-c9MhophgwGP}"

# Local checkout of the audited repository. The script maps Code4rena
# GitHub linesOfCode URLs such as src/HypoVault.sol#L422 into this folder.
# Windows paths like D:\work\...\repo are accepted under WSL if wslpath exists.
LOCAL_REPO_DIR="${LOCAL_REPO_DIR:-${PWD}}"

# --------------------- Optional parameters ---------------------
# If set, use this local JSON instead of calling Code4rena API.
# The JSON should contain detailed submissions with linesOfCode fields.
SUBMISSIONS_JSON="${SUBMISSIONS_JSON:-}"

# Code4rena browser cookie. Prefer exporting CODE4RENA_COOKIE in your shell.
# LOGIN=... and C4AUTH-LOGIN=... are both accepted by the Python component.
#   export CODE4RENA_COOKIE='LOGIN=...'
CODE4RENA_COOKIE="${CODE4RENA_COOKIE:-}"

# Optional proxy, for example: http://127.0.0.1:7890
PROXY="${PROXY:-}"

# Output folder. Each run creates PROJECT_ID/timestamp under this directory.
OUTPUT_DIR="${OUTPUT_DIR:-}"

# Download GitHub owner/repo/ref from each Code4rena linesOfCode URL and
# flatten against that exact checkout. Default: true.
AUTO_DOWNLOAD_GITHUB="${AUTO_DOWNLOAD_GITHUB:-true}"

# Optional cache directory for downloaded GitHub checkouts. If empty, the
# Python pipeline uses OUTPUT_DIR/_github_repos.
GITHUB_CACHE_DIR="${GITHUB_CACHE_DIR:-}"

# Submodule mode for downloaded GitHub checkouts: none, first-level, recursive.
# Keep none by default so large dependency trees do not stall collection.
GITHUB_SUBMODULES="${GITHUB_SUBMODULES:-none}"

# Timeout in seconds for each git/forge/fix subprocess.
COMMAND_TIMEOUT="${COMMAND_TIMEOUT:-300}"

# Include findings judged invalid. Default: false.
INCLUDE_INVALID="${INCLUDE_INVALID:-false}"

# Filter severity. Leave empty for all severities. Example: "high medium"
SEVERITIES="${SEVERITIES:-}"

# Limit API detail requests while testing. Leave empty for full run.
MAX_SUBMISSIONS="${MAX_SUBMISSIONS:-}"

# Set true to only collect/export Code4rena data and skip flatten.
SKIP_FLATTEN="${SKIP_FLATTEN:-false}"

# Set true to print planned forge commands without running them.
DRY_RUN="${DRY_RUN:-false}"

# Delay between Code4rena API detail requests.
SLEEP_SECONDS="${SLEEP_SECONDS:-0.4}"

# Parallel workers for Code4rena submission detail requests.
API_WORKERS="${API_WORKERS:-1}"

# Tool paths. If PYTHON_BIN is not provided, prefer python and fall back to python3.
if [[ -z "${PYTHON_BIN:-}" ]]; then
  if command -v python >/dev/null 2>&1; then
    PYTHON_BIN="python"
  elif command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="python3"
  else
    PYTHON_BIN="python"
  fi
fi
FORGE_BIN="${FORGE_BIN:-forge}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"
OUTPUT_DIR="${OUTPUT_DIR:-${ROOT_DIR}/c4_pipeline_output}"
PIPELINE_PY="${PIPELINE_PY:-${SCRIPT_DIR}/code4rena_flatten_pipeline.py}"
if [[ -z "${FIX_SCRIPT:-}" ]]; then
  if [[ -f "${SCRIPT_DIR}/fix_flatten_order.py" ]]; then
    FIX_SCRIPT="${SCRIPT_DIR}/fix_flatten_order.py"
  else
    FIX_SCRIPT="${OUTPUT_DIR}/_tools/identity_fix_flatten_order.py"
  fi
fi

to_unix_path() {
  local value="$1"
  if [[ -z "${value}" ]]; then
    printf '%s' "${value}"
  elif [[ "${value}" =~ ^[A-Za-z]:\\ ]] && command -v wslpath >/dev/null 2>&1; then
    wslpath -u "${value}"
  elif [[ "${value}" =~ ^[A-Za-z]:\\ ]] && command -v cygpath >/dev/null 2>&1; then
    cygpath -u "${value}"
  else
    printf '%s' "${value}"
  fi
}

LOCAL_REPO_DIR="$(to_unix_path "${LOCAL_REPO_DIR}")"
SUBMISSIONS_JSON="$(to_unix_path "${SUBMISSIONS_JSON}")"
OUTPUT_DIR="$(to_unix_path "${OUTPUT_DIR}")"
GITHUB_CACHE_DIR="$(to_unix_path "${GITHUB_CACHE_DIR}")"
PIPELINE_PY="$(to_unix_path "${PIPELINE_PY}")"
FIX_SCRIPT="$(to_unix_path "${FIX_SCRIPT}")"

die() {
  echo "ERROR: $*" >&2
  exit 1
}

is_true() {
  case "${1,,}" in
    1|true|yes|y|on) return 0 ;;
    *) return 1 ;;
  esac
}

echo "== Code4rena flatten pipeline =="
echo "PROJECT_ID      : ${PROJECT_ID}"
echo "LOCAL_REPO_DIR  : ${LOCAL_REPO_DIR}"
echo "OUTPUT_DIR      : ${OUTPUT_DIR}"
echo "AUTO_DOWNLOAD   : ${AUTO_DOWNLOAD_GITHUB}"
echo "GITHUB_CACHE_DIR: ${GITHUB_CACHE_DIR:-<default>}"
echo "GITHUB_SUBMODULES: ${GITHUB_SUBMODULES}"
echo "COMMAND_TIMEOUT : ${COMMAND_TIMEOUT}"
echo "SUBMISSIONS_JSON: ${SUBMISSIONS_JSON:-<api>}"
echo "DRY_RUN         : ${DRY_RUN}"
echo "SKIP_FLATTEN    : ${SKIP_FLATTEN}"
echo

[[ -f "${PIPELINE_PY}" ]] || die "Pipeline script not found: ${PIPELINE_PY}"
command -v "${PYTHON_BIN}" >/dev/null 2>&1 || die "Python not found: ${PYTHON_BIN}"

if ! is_true "${SKIP_FLATTEN}"; then
  if ! is_true "${AUTO_DOWNLOAD_GITHUB}"; then
    [[ -d "${LOCAL_REPO_DIR}" ]] || die "Local repo folder not found: ${LOCAL_REPO_DIR}"
  fi
  if ! is_true "${DRY_RUN}"; then
    [[ -f "${FIX_SCRIPT}" ]] || die "fix_flatten_order.py not found: ${FIX_SCRIPT}"
    command -v "${FORGE_BIN}" >/dev/null 2>&1 || die "forge not found. Install Foundry or set FORGE_BIN."
  fi
fi

args=(
  "${PIPELINE_PY}"
  --project "${PROJECT_ID}"
  --output-dir "${OUTPUT_DIR}"
  --fix-script "${FIX_SCRIPT}"
  --python-bin "${PYTHON_BIN}"
  --forge-bin "${FORGE_BIN}"
  --sleep "${SLEEP_SECONDS}"
  --api-workers "${API_WORKERS}"
  --github-submodules "${GITHUB_SUBMODULES}"
  --command-timeout "${COMMAND_TIMEOUT}"
)

if [[ -n "${GITHUB_CACHE_DIR}" ]]; then
  args+=(--github-cache-dir "${GITHUB_CACHE_DIR}")
fi

if [[ -n "${SUBMISSIONS_JSON}" ]]; then
  [[ -r "${SUBMISSIONS_JSON}" ]] || die "SUBMISSIONS_JSON not readable: ${SUBMISSIONS_JSON}"
  args+=(--submissions-json "${SUBMISSIONS_JSON}")
fi

if [[ -n "${LOCAL_REPO_DIR}" ]]; then
  args+=(--repo "${LOCAL_REPO_DIR}")
fi

if [[ -n "${PROXY}" ]]; then
  args+=(--proxy "${PROXY}")
fi

if [[ -n "${MAX_SUBMISSIONS}" ]]; then
  args+=(--max-submissions "${MAX_SUBMISSIONS}")
fi

if [[ -n "${CODE4RENA_COOKIE}" ]]; then
  export CODE4RENA_COOKIE
fi

if is_true "${INCLUDE_INVALID}"; then
  args+=(--include-invalid)
fi

if is_true "${SKIP_FLATTEN}"; then
  args+=(--skip-flatten)
fi

if is_true "${DRY_RUN}"; then
  args+=(--dry-run)
fi

if ! is_true "${AUTO_DOWNLOAD_GITHUB}"; then
  args+=(--no-download-github)
fi

if [[ -n "${SEVERITIES}" ]]; then
  for severity in ${SEVERITIES}; do
    args+=(--severity "${severity}")
  done
fi

echo "Running:"
printf '  %q' "${PYTHON_BIN}" "${args[@]}"
echo
echo

"${PYTHON_BIN}" "${args[@]}"
