#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

MODE_ARG=""

usage() {
    cat <<'EOF'
用法:
  ./run.sh [选项]

默认会复现当前 PoC 的 v2 切片和测试:
  cargo run --release -- ./examples/src/poc_final.t.sol PoC availableForWithdrawal \
    --target-test test_submissionValidity --aggressive-cleanup --resurrect-v2 \
    --max-level 0 -o ./results/slice_<目标信息>_<时间戳>.sol

常用:
  ./run.sh                         # 生成 v2 切片，并复跑 forge test
  ./run.sh --no-rerun-test          # 只运行 slicer，不额外复跑 forge test
  ./run.sh --manual-project ./x     # 把输出复制到指定 forge 工程再测试

选项:
  -i, --input FILE          输入 Solidity 文件，默认 ./examples/src/poc_final.t.sol
  -c, --contract NAME       目标合约，默认 PoC
  -v, --variable NAME       目标变量，默认 availableForWithdrawal
      --fn NAME             目标测试/函数，默认 test_submissionValidity
      --function NAME       同 --fn
  -l, --level N             --max-level，默认 0
  -o, --output FILE         输出文件；不指定时自动生成唯一文件名

运行模式:
      --v2                  使用 --resurrect-v2，默认
  -q, --quick               与 v2 同一引擎（保留别名兼容）
  -f, --full                完整模式，等同默认 v2
      --compile-guarantee   给 v2 添加 --compile-guarantee
      --include-types       添加 --include-types
      --semantic            已弃用：切片恒为 v2，该选项不再生效

验证:
      --no-rerun-test       不额外复跑 forge test
      --manual-project DIR  使用 DIR 作为手动验证 forge root；默认 ./foundry_runs/<run-id>

其他:
      --debug               使用 cargo run，不加 --release
  -h, --help                显示帮助

输出相关文件:
  合约源码:   ./results/<run-id>.sol
  v2 元数据:  ./results/<run-id>.sol.v2.json
  slicer日志: ./logs/<run-id>.log
  测试日志:   ./logs/<run-id>.forge-test.log
  Forge工程:  ./foundry_runs/<run-id>/
EOF
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --quick|-q)
            MODE_ARG="quick"
            shift
            ;;
        --full|-f|--v2)
            MODE_ARG="v2"
            shift
            ;;
        --level|-l)
            MAX_LEVEL="$2"
            shift 2
            ;;
        --contract|-c)
            CONTRACT_NAME="$2"
            shift 2
            ;;
        --function|--fn)
            FUNCTION_NAME="$2"
            shift 2
            ;;
        --variable|-v)
            VARIABLE_NAME="$2"
            shift 2
            ;;
        --input|-i)
            INPUT_FILE="$2"
            shift 2
            ;;
        --output|-o)
            OUTPUT_FILE="$2"
            shift 2
            ;;
        --include-types)
            INCLUDE_TYPES=1
            shift
            ;;
        --semantic)
            USE_SEMANTIC=1
            shift
            ;;
        --compile-guarantee)
            COMPILE_GUARANTEE=1
            shift
            ;;
        --no-rerun-test|--no-verify)
            RERUN_FORGE_TEST=0
            shift
            ;;
        --manual-project)
            MANUAL_PROJECT="$2"
            shift 2
            ;;
        --debug)
            CARGO_PROFILE="debug"
            shift
            ;;
        --help|-h)
            usage
            exit 0
            ;;
        *)
            echo "未知选项: $1" >&2
            echo "使用 --help 查看帮助" >&2
            exit 1
            ;;
    esac
done

unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY all_proxy ALL_PROXY 2>/dev/null || true

INPUT_FILE="${INPUT_FILE:-./examples/src/poc_final.t.sol}"
CONTRACT_NAME="${CONTRACT_NAME:-PoC}"
FUNCTION_NAME="${FUNCTION_NAME:-test_submissionValidity}"
VARIABLE_NAME="${VARIABLE_NAME:-availableForWithdrawal}"
MAX_LEVEL="${MAX_LEVEL:-0}"
RUN_MODE="${MODE_ARG:-${RUN_MODE:-v2}}"
INCLUDE_TYPES="${INCLUDE_TYPES:-0}"
USE_SEMANTIC="${USE_SEMANTIC:-0}"
COMPILE_GUARANTEE="${COMPILE_GUARANTEE:-0}"
RERUN_FORGE_TEST="${RERUN_FORGE_TEST:-1}"
CARGO_PROFILE="${CARGO_PROFILE:-release}"
MANUAL_PROJECT="${MANUAL_PROJECT:-}"

mkdir -p logs results foundry_runs

TIMESTAMP="$(date +"%Y%m%d_%H%M%S")_$$"
SAFE_CONTRACT="${CONTRACT_NAME//[^a-zA-Z0-9_]/_}"
SAFE_FUNCTION="${FUNCTION_NAME:-all}"
SAFE_FUNCTION="${SAFE_FUNCTION//[^a-zA-Z0-9_]/_}"
SAFE_VARIABLE="${VARIABLE_NAME//[^a-zA-Z0-9_]/_}"
RUN_ID="slice_${SAFE_CONTRACT}_${SAFE_FUNCTION}_${SAFE_VARIABLE}_${RUN_MODE}_${TIMESTAMP}"
OUTPUT_FILE="${OUTPUT_FILE:-./results/${RUN_ID}.sol}"
OUTPUT_STEM="$(basename "$OUTPUT_FILE" .sol)"
LOG_FILE="${LOG_FILE:-./logs/${OUTPUT_STEM}.log}"
FORGE_LOG_FILE="${FORGE_LOG_FILE:-./logs/${OUTPUT_STEM}.forge-test.log}"
BUILD_LOG_FILE="${BUILD_LOG_FILE:-./logs/${OUTPUT_STEM}.build.log}"
META_FILE="${OUTPUT_FILE}.v2.json"
DEFAULT_FOUNDRY_ROOT="./foundry_runs/${OUTPUT_STEM}"
FOUNDRY_ROOT="${MANUAL_PROJECT:-$DEFAULT_FOUNDRY_ROOT}"

export SC_SLICER_LOG_FILE="$LOG_FILE"
export SC_SLICER_BUILD_LOG_FILE="$BUILD_LOG_FILE"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

print_cmd() {
    printf '  '
    printf '%q ' "$@"
    printf '\n'
}

die() {
    echo -e "${RED}错误: $*${NC}" >&2
    exit 1
}

extract_json_string() {
    local key="$1"
    local file="$2"
    sed -n "s/^[[:space:]]*\"${key}\":[[:space:]]*\"\\(.*\\)\"[,]*/\\1/p" "$file" | tail -n 1
}

extract_json_bool() {
    local key="$1"
    local file="$2"
    sed -n "s/^[[:space:]]*\"${key}\":[[:space:]]*\\(true\\|false\\)[,]*/\\1/p" "$file" | tail -n 1
}

extract_tmp_root_from_meta() {
    local file="$1"
    local last_command root
    [ -f "$file" ] || return 1
    last_command="$(extract_json_string "last_command" "$file")"
    root="$(printf '%s\n' "$last_command" | sed -n 's/.*--root \([^ ]*\).*/\1/p')"
    [ -n "$root" ] || return 1
    printf '%s\n' "$root"
}

echo -e "${BLUE}${BOLD}SC_Slicer 手动运行脚本${NC}"
echo "  工作目录:   $SCRIPT_DIR"
echo "  输入文件:   $INPUT_FILE"
echo "  目标合约:   $CONTRACT_NAME"
echo "  目标测试:   $FUNCTION_NAME"
echo "  目标变量:   $VARIABLE_NAME"
echo "  max-level:  $MAX_LEVEL"
echo "  模式:       $RUN_MODE"
echo "  输出文件:   $OUTPUT_FILE"
echo "  元数据:     $META_FILE"
echo "  slicer日志: $LOG_FILE"
echo "  测试日志:   $FORGE_LOG_FILE"
echo "  Forge工程:  $FOUNDRY_ROOT"
echo ""

[ -f "$INPUT_FILE" ] || die "输入文件不存在: $INPUT_FILE"

CMD=(cargo run)
if [ "$CARGO_PROFILE" = "release" ]; then
    CMD+=(--release)
elif [ "$CARGO_PROFILE" != "debug" ]; then
    die "未知 CARGO_PROFILE: $CARGO_PROFILE"
fi
CMD+=(-- "$INPUT_FILE" "$CONTRACT_NAME" "$VARIABLE_NAME")

if [ -n "$FUNCTION_NAME" ]; then
    CMD+=(--target-test "$FUNCTION_NAME")
fi

case "$RUN_MODE" in
    quick)
        CMD+=(--aggressive-cleanup --resurrect-v2 --max-level "$MAX_LEVEL" -o "$OUTPUT_FILE")
        ;;
    v2|full)
        CMD+=(--aggressive-cleanup --resurrect-v2 --max-level "$MAX_LEVEL" -o "$OUTPUT_FILE")
        ;;
    *)
        die "未知模式: $RUN_MODE"
        ;;
esac

[ "$INCLUDE_TYPES" -eq 1 ] && CMD+=(--include-types)
[ "$USE_SEMANTIC" -eq 1 ] && CMD+=(--semantic)
[ "$COMPILE_GUARANTEE" -eq 1 ] && CMD+=(--compile-guarantee)

echo -e "${CYAN}${BOLD}运行 slicer:${NC}"
print_cmd "${CMD[@]}"
echo ""

: > "$LOG_FILE"
if ! "${CMD[@]}" 2>&1 | tee -a "$LOG_FILE"; then
    die "slicer 运行失败，日志: $LOG_FILE"
fi

[ -f "$OUTPUT_FILE" ] || die "输出文件不存在: $OUTPUT_FILE"

LINES="$(wc -l < "$OUTPUT_FILE" | tr -d ' ')"
BYTES="$(wc -c < "$OUTPUT_FILE" | tr -d ' ')"
echo ""
echo -e "${GREEN}${BOLD}切片输出:${NC}"
echo "  文件:  $OUTPUT_FILE"
echo "  行数:  $LINES"
echo "  字节:  $BYTES"

if [ -f "$META_FILE" ]; then
    COMPILE_SUCCESS="$(extract_json_bool "compile_success" "$META_FILE" || true)"
    SLICE_EFFECTIVE="$(extract_json_bool "slice_effective" "$META_FILE" || true)"
    LAST_COMMAND="$(extract_json_string "last_command" "$META_FILE" || true)"
    TMP_ROOT="$(extract_tmp_root_from_meta "$META_FILE" || true)"

    echo ""
    echo -e "${GREEN}${BOLD}v2 元数据:${NC}"
    echo "  文件:            $META_FILE"
    echo "  compile_success: ${COMPILE_SUCCESS:-未知}"
    echo "  slice_effective: ${SLICE_EFFECTIVE:-未知}"
    [ -n "${TMP_ROOT:-}" ] && echo "  v2内部临时root:  $TMP_ROOT"
    [ -n "${LAST_COMMAND:-}" ] && echo "  last_command:    $LAST_COMMAND"
else
    LAST_COMMAND=""
    echo ""
    echo -e "${YELLOW}未找到 v2 元数据: $META_FILE${NC}"
fi

if [ "$FOUNDRY_ROOT" = "$DEFAULT_FOUNDRY_ROOT" ]; then
    rm -rf "$FOUNDRY_ROOT"
fi
mkdir -p "$FOUNDRY_ROOT"
cp "$OUTPUT_FILE" "$FOUNDRY_ROOT/ResurrectedV2.t.sol"
cat > "$FOUNDRY_ROOT/foundry.toml" <<'TOML'
[profile.default]
src = "."
out = "out"
libs = []
via_ir = true
optimizer = true
optimizer_runs = 200
TOML

echo ""
echo -e "${GREEN}${BOLD}本地 Foundry 验证工程:${NC}"
echo "  目录:  $FOUNDRY_ROOT"
echo "  合约:  $FOUNDRY_ROOT/ResurrectedV2.t.sol"

if ! command -v forge >/dev/null 2>&1; then
    echo ""
    echo -e "${YELLOW}forge 不存在，跳过 forge 测试。${NC}"
    exit 0
fi

if [ "$RERUN_FORGE_TEST" -eq 1 ]; then
    FORGE_CMD=(forge test --root "$FOUNDRY_ROOT" --match-contract "$CONTRACT_NAME" --match-test "$FUNCTION_NAME" --via-ir)
    echo ""
    echo -e "${CYAN}${BOLD}复跑 forge test:${NC}"
    print_cmd "${FORGE_CMD[@]}"
    echo ""

    : > "$FORGE_LOG_FILE"
    if "${FORGE_CMD[@]}" 2>&1 | tee "$FORGE_LOG_FILE"; then
        echo ""
        echo -e "${GREEN}${BOLD}forge test 通过。${NC}"
    else
        FORGE_EXIT=$?
        echo ""
        echo -e "${RED}${BOLD}forge test 失败，退出码: $FORGE_EXIT${NC}"
        echo "  测试日志: $FORGE_LOG_FILE"
        exit "$FORGE_EXIT"
    fi
fi

echo ""
echo -e "${BLUE}${BOLD}手动验证命令:${NC}"
echo "  重新运行目标测试:"
print_cmd forge test --root "$FOUNDRY_ROOT" --match-contract "$CONTRACT_NAME" --match-test "$FUNCTION_NAME" --via-ir
echo ""
echo "  查看结果文件:"
print_cmd ls -lh "$OUTPUT_FILE" "$META_FILE"
echo ""
echo "  查看 Foundry 工程:"
print_cmd ls -lh "$FOUNDRY_ROOT"
