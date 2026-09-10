#!/usr/bin/env bash
set -Eeuo pipefail

# Batch runner for run_code4rena_flatten_pipeline.sh.
#
# Reads Code4rena audit rows from a CSV and runs the flatten pipeline for each
# project_id. Each completed project is stored as:
#   c4_pipeline_output/[sanitized_project_title]_[project_id]/<timestamp>/

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"

CSV_PATH="${CSV_PATH:-${ROOT_DIR}/data/code4rena/code4rena_audits_solidity_ended.csv}"
PIPELINE_SH="${PIPELINE_SH:-${SCRIPT_DIR}/run_code4rena_flatten_pipeline.sh}"
OUTPUT_DIR="${OUTPUT_DIR:-${ROOT_DIR}/c4_pipeline_output}"
BATCH_LOG_DIR="${BATCH_LOG_DIR:-${OUTPUT_DIR}/_batch_logs}"
if [[ -z "${FIX_SCRIPT:-}" ]]; then
  if [[ -f "${SCRIPT_DIR}/fix_flatten_order.py" ]]; then
    FIX_SCRIPT="${SCRIPT_DIR}/fix_flatten_order.py"
  else
    FIX_SCRIPT="${OUTPUT_DIR}/_tools/identity_fix_flatten_order.py"
  fi
fi

# Optional controls for long runs.
LIMIT="${LIMIT:-}"
START_AT="${START_AT:-1}"
FORCE_RERUN="${FORCE_RERUN:-false}"
JOBS="${JOBS:-1}"

# Pipeline defaults for batch use. Callers can override them in the environment.
AUTO_DOWNLOAD_GITHUB="${AUTO_DOWNLOAD_GITHUB:-true}"
if [[ -z "${GITHUB_CACHE_DIR:-}" ]]; then
  GITHUB_CACHE_DIR="${OUTPUT_DIR}/_github_repos"
  GITHUB_CACHE_DIR_WAS_SET="false"
else
  GITHUB_CACHE_DIR_WAS_SET="true"
fi
GITHUB_SUBMODULES="${GITHUB_SUBMODULES:-none}"
COMMAND_TIMEOUT="${COMMAND_TIMEOUT:-300}"
SLEEP_SECONDS="${SLEEP_SECONDS:-0.2}"
API_WORKERS="${API_WORKERS:-1}"
INCLUDE_INVALID="${INCLUDE_INVALID:-false}"
SEVERITIES="${SEVERITIES:-}"
SKIP_FLATTEN="${SKIP_FLATTEN:-false}"
DRY_RUN="${DRY_RUN:-false}"

is_true() {
  case "${1,,}" in
    1|true|yes|y|on) return 0 ;;
    *) return 1 ;;
  esac
}

die() {
  echo "ERROR: $*" >&2
  exit 1
}

[[ -r "${CSV_PATH}" ]] || die "CSV not readable: ${CSV_PATH}"
[[ -x "${PIPELINE_SH}" || -f "${PIPELINE_SH}" ]] || die "Pipeline script not found: ${PIPELINE_SH}"

mkdir -p "${OUTPUT_DIR}" "${BATCH_LOG_DIR}"

status_csv="${BATCH_LOG_DIR}/batch_status.csv"
status_lock="${BATCH_LOG_DIR}/batch_status.lock"
if [[ ! -f "${status_csv}" ]]; then
  printf 'row,project_id,title,slug,status,output_dir,log_path,message\n' > "${status_csv}"
fi

quote_csv() {
  local value="${1//$'\r'/ }"
  value="${value//$'\n'/ }"
  value="${value//\"/\"\"}"
  printf '"%s"' "${value}"
}

append_status() {
  local row="$1" project_id="$2" title="$3" slug="$4" status="$5" output="$6" log="$7" message="$8"
  (
    flock -x 9
    {
      printf '%s,%s,' "${row}" "${project_id}"
      quote_csv "${title}"
      printf ','
      quote_csv "${slug}"
      printf ',%s,' "${status}"
      quote_csv "${output}"
      printf ','
      quote_csv "${log}"
      printf ','
      quote_csv "${message}"
      printf '\n'
    } >> "${status_csv}"
  ) 9>> "${status_lock}"
}

tmp_rows="$(mktemp)"
trap 'rm -f "${tmp_rows}"' EXIT

python3 - "${CSV_PATH}" > "${tmp_rows}" <<'PY'
import csv
import re
import sys

def sanitize_title(value: str) -> str:
    value = (value or "").strip()
    value = re.sub(r"[^A-Za-z0-9._-]+", "_", value)
    value = re.sub(r"_+", "_", value).strip("._-")
    return value[:120] or "untitled"

with open(sys.argv[1], newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for idx, row in enumerate(reader, 1):
        project_id = (row.get("project_id") or row.get("uid") or "").strip()
        title = (row.get("title") or row.get("slug") or project_id).strip()
        slug = (row.get("slug") or "").strip()
        repo = (row.get("repo") or "").strip()
        if not project_id:
            continue
        folder = f"{sanitize_title(title)}_{project_id}"
        print("\t".join([str(idx), project_id, title, slug, repo, folder]))
PY

total_rows="$(wc -l < "${tmp_rows}" | tr -d ' ')"
echo "== Code4rena flatten batch =="
echo "CSV_PATH        : ${CSV_PATH}"
echo "OUTPUT_DIR      : ${OUTPUT_DIR}"
echo "BATCH_LOG_DIR   : ${BATCH_LOG_DIR}"
echo "FIX_SCRIPT      : ${FIX_SCRIPT}"
echo "total rows      : ${total_rows}"
echo "START_AT        : ${START_AT}"
echo "LIMIT           : ${LIMIT:-<none>}"
echo "FORCE_RERUN     : ${FORCE_RERUN}"
echo "JOBS            : ${JOBS}"
echo "API_WORKERS     : ${API_WORKERS}"
echo

processed=0
successes=0
failures=0
skipped=0

run_project() {
  local row="$1" project_id="$2" title="$3" slug="$4" repo="$5" folder="$6"
  local target_dir="${OUTPUT_DIR}/${folder}"
  local success_marker="${target_dir}/.pipeline_success"
  local log_path="${BATCH_LOG_DIR}/${row}__${folder}.log"

  if [[ -f "${success_marker}" ]] && ! is_true "${FORCE_RERUN}"; then
    echo "[$row/$total_rows] SKIP ${title} (${project_id})"
    append_status "${row}" "${project_id}" "${title}" "${slug}" "skipped" "${target_dir}" "${log_path}" "success marker exists"
    return 0
  fi

  echo "[$row/$total_rows] RUN  ${title} (${project_id})"

  local local_repo_dir="${repo:-${SCRIPT_DIR}}"
  if [[ "${local_repo_dir}" =~ ^https?:// ]]; then
    local_repo_dir=""
  fi

  local project_github_cache_dir="${GITHUB_CACHE_DIR}"
  if (( JOBS > 1 )) && ! is_true "${GITHUB_CACHE_DIR_WAS_SET}"; then
    project_github_cache_dir="${OUTPUT_DIR}/_github_repos_by_project/${project_id}"
  fi

  set +e
  PROJECT_ID="${project_id}" \
  LOCAL_REPO_DIR="${local_repo_dir}" \
  OUTPUT_DIR="${OUTPUT_DIR}" \
  FIX_SCRIPT="${FIX_SCRIPT}" \
  AUTO_DOWNLOAD_GITHUB="${AUTO_DOWNLOAD_GITHUB}" \
  GITHUB_CACHE_DIR="${project_github_cache_dir}" \
  GITHUB_SUBMODULES="${GITHUB_SUBMODULES}" \
  COMMAND_TIMEOUT="${COMMAND_TIMEOUT}" \
  INCLUDE_INVALID="${INCLUDE_INVALID}" \
  SEVERITIES="${SEVERITIES}" \
  SKIP_FLATTEN="${SKIP_FLATTEN}" \
  DRY_RUN="${DRY_RUN}" \
  SLEEP_SECONDS="${SLEEP_SECONDS}" \
  API_WORKERS="${API_WORKERS}" \
    bash "${PIPELINE_SH}" > "${log_path}" 2>&1
  local rc=$?
  set -e

  local source_dir="${OUTPUT_DIR}/${project_id}"
  if [[ -d "${source_dir}" ]]; then
    mkdir -p "${target_dir}"
    shopt -s nullglob dotglob
    for item in "${source_dir}"/*; do
      mv "${item}" "${target_dir}/"
    done
    shopt -u nullglob dotglob
    rmdir "${source_dir}" 2>/dev/null || true
  fi

  if [[ "${rc}" -eq 0 ]]; then
    date -u +"%Y-%m-%dT%H:%M:%SZ" > "${success_marker}"
    append_status "${row}" "${project_id}" "${title}" "${slug}" "success" "${target_dir}" "${log_path}" "pipeline exited 0"
    echo "[$row/$total_rows] OK   ${target_dir}"
    return 0
  fi

  append_status "${row}" "${project_id}" "${title}" "${slug}" "failed" "${target_dir}" "${log_path}" "pipeline exited ${rc}"
  echo "[$row/$total_rows] FAIL rc=${rc}; log=${log_path}" >&2
  return "${rc}"
}

while IFS=$'\t' read -r row project_id title slug repo folder; do
  if (( row < START_AT )); then
    continue
  fi
  if [[ -n "${LIMIT}" ]] && (( processed >= LIMIT )); then
    break
  fi
  processed=$((processed + 1))

  if (( JOBS > 1 )); then
    while (( $(jobs -pr | wc -l) >= JOBS )); do
      wait -n || true
    done
    run_project "${row}" "${project_id}" "${title}" "${slug}" "${repo}" "${folder}" &
  else
    if run_project "${row}" "${project_id}" "${title}" "${slug}" "${repo}" "${folder}"; then
      successes=$((successes + 1))
    else
      failures=$((failures + 1))
    fi
  fi
done < "${tmp_rows}"

if (( JOBS > 1 )); then
  wait || true
fi

echo
echo "== Batch summary =="
echo "processed: ${processed}"
if (( JOBS > 1 )); then
  echo "finished : see status CSV for per-project results"
else
  echo "success  : ${successes}"
  echo "failed   : ${failures}"
  echo "skipped  : ${skipped}"
fi
echo "status   : ${status_csv}"
