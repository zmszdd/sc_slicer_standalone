#!/usr/bin/env bash
# 列出/移出已跟踪的可再生评测产物（runs/ 目录）。
# 默认 dry-run；加 --apply 才执行 `git rm -r --cached`（只改 index，不动工作区文件）。
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

APPLY=0
if [[ "${1:-}" == "--apply" ]]; then
    APPLY=1
elif [[ -n "${1:-}" ]]; then
    echo "用法: $0 [--apply]" >&2
    exit 2
fi

# 只针对可再生的逐案例 runs/ 产物；保留 evaluation 下的 .py/.md 与 schema JSON。
PATTERNS=(
    'tools/report_constraints_v2/evaluation/**/runs/**'
    'tools/stage3/evaluation/**/runs/**'
    'tools/report_constraints_v2/evaluation/**/runs'
    'tools/stage3/evaluation/**/runs'
)

mapfile -t FILES < <(git ls-files "${PATTERNS[@]}" | sort -u)

echo "将处理的可再生评测产物（runs/）文件数: ${#FILES[@]}"
if [[ "$APPLY" -ne 1 ]]; then
    echo "dry-run：不会修改 index。执行 --apply 才会移出跟踪。"
    if [[ "${#FILES[@]}" -gt 0 ]]; then
        echo "示例（前 10 个）:"
        printf '%s\n' "${FILES[@]:0:10}"
    fi
    exit 0
fi

if [[ "${#FILES[@]}" -eq 0 ]]; then
    echo "没有需要处理的文件。"
    exit 0
fi

# git rm --cached 需要逐批，避免命令行过长。
BATCH=2000
for ((i=0; i<${#FILES[@]}; i+=BATCH)); do
    git rm -r --cached --quiet -- "${FILES[@]:i:BATCH}"
done
echo "已移出 ${#FILES[@]} 个文件（仅 index，工作区保留）。"
echo "请 review 后单独提交；不要把这些产物再 add 回来。"
