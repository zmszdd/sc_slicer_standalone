#!/usr/bin/env bash
# 只读盘点仓库缓存；--apply 时仅删除缓存，绝不触碰外部数据根与评测证据。
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

MODE=dry-run
for arg in "$@"; do
  case "$arg" in
    --apply)
      MODE=apply
      ;;
    --help|-h)
      echo "usage: $0 [--apply]"
      echo "  默认 dry-run；--apply 只删除 Python/tooling 缓存。"
      exit 0
      ;;
    *)
      echo "unknown argument: $arg" >&2
      exit 2
      ;;
  esac
done

PROTECTED=(
  c4_pipeline_output
  code4rena_reports
  tools/stage3/runs
  tools/stage3/cases
  tools/stage3/evaluation/metrics/mainline_goldset
  tools/stage3/evaluation/metrics/mainline_goldset_1_7_31_pos
  tools/stage3/evaluation/metrics/mainline_goldset_1_7_31_neg
  tools/stage3/evaluation/metrics/mainline_stage2_out
  tools/stage3/evaluation/metrics/mainline_negative_p1_rejected_runs
  tools/stage3/evaluation/metrics/mainline_negative_p3_rejected_runs
  tools/stage3/evaluation/metrics/mainline_negative_p4_rejected_runs
  tools/stage3/evaluation/metrics/mainline_metrics.json
  tools/stage3/mainline-protocol.json
  PROTECTED_HASHES.json
  config/llm.env
  config/paths.local.env
)

for name in C4_OUTPUT_ROOT CODE4RENA_REPORTS_ROOT VERIFIED_FLATTEN_ROOT NEGATIVE_FLATTEN_ROOT; do
  override="${!name:-}"
  if [[ -n "$override" ]]; then
    PROTECTED+=("$override")
  fi
done

is_protected() {
  local target="$1" base
  for base in "${PROTECTED[@]}"; do
    base="${base%/}"
    [[ -z "$base" ]] && continue
    if [[ "$target" == "$base" || "$target" == "$base/"* ]]; then
      return 0
    fi
    case "$base" in
      /*) ;;
      *) if [[ "$target" == "./$base" || "$target" == "./$base/"* ]]; then
           return 0
         fi
         ;;
    esac
  done
  return 1
}

echo "== 保护路径（永不删除） =="
missing=0
for path in "${PROTECTED[@]}"; do
  if [[ -e "$path" || -L "$path" ]]; then
    echo "[OK]      $path"
  else
    echo "[MISSING] $path"
    missing=$((missing + 1))
  fi
done
if [[ "$missing" -gt 0 ]]; then
  echo "警告：$missing 个保护路径不存在；先恢复数据根，不要通过删除来‘重建’。"
  echo "恢复方式：从备份恢复，或在 config/paths.local.env 中指向已有数据根。"
fi

PRUNE=( -path './.git' )
for base in "${PROTECTED[@]}"; do
  case "$base" in
    /*) continue ;;
  esac
  base="${base#./}"
  PRUNE+=( -o -path "./$base" )
done

mapfile -t CACHE_DIRS < <(find . \( "${PRUNE[@]}" \) -prune -o -type d \
  \( -name '__pycache__' -o -name '.pytest_cache' -o -name '.mypy_cache' \
     -o -name '.ruff_cache' -o -name 'htmlcov' \) -print | sort)
mapfile -t CACHE_FILES < <(find . \( "${PRUNE[@]}" \) -prune -o -type f \
  \( -name '*.pyc' -o -name '*.pyo' -o -name '.coverage' \) -print | sort)

SAFE_DIRS=()
SAFE_FILES=()
TRACKED_LIST="$(mktemp)"
trap 'rm -f -- "$TRACKED_LIST"' EXIT
git ls-files > "$TRACKED_LIST"
is_tracked() {
  local path="${1#./}"
  grep -qFx -- "$path" "$TRACKED_LIST"
}
for path in "${CACHE_DIRS[@]}"; do
  if is_protected "$path"; then
    echo "跳过保护路径：$path" >&2
    continue
  fi
  if is_tracked "$path"; then
    echo "跳过已跟踪文件：$path" >&2
    continue
  fi
  SAFE_DIRS+=("$path")
done
for path in "${CACHE_FILES[@]}"; do
  if is_protected "$path" || is_tracked "$path"; then
    continue
  fi
  SAFE_FILES+=("$path")
done

echo
echo "== 缓存候选 =="
echo "目录 ${#SAFE_DIRS[@]} 个，文件 ${#SAFE_FILES[@]} 个"
if [[ "$MODE" == dry-run ]]; then
  echo "dry-run：未删除任何内容。执行 $0 --apply 才会删除上述缓存。"
  exit 0
fi

if [[ "${#SAFE_DIRS[@]}" -gt 0 ]]; then
  rm -rf -- "${SAFE_DIRS[@]}"
fi
if [[ "${#SAFE_FILES[@]}" -gt 0 ]]; then
  rm -f -- "${SAFE_FILES[@]}"
fi
echo "已删除 ${#SAFE_DIRS[@]} 个缓存目录、${#SAFE_FILES[@]} 个缓存文件。"
echo "未修改 Git index；未删除任何数据根、run artifact 或 tracked 文件。"
