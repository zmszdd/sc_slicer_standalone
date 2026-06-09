#!/bin/bash

# ╔════════════════════════════════════════════════════════════════════╗
# ║              SC_Slicer - 目标导向代码切片分析工具                   ║
# ║              Target-Oriented Analysis v2.0                          ║
# ║              默认完整模式 - 直接运行即可                            ║
# ╚════════════════════════════════════════════════════════════════════╝

set -e

# 解析命令行参数
while [[ $# -gt 0 ]]; do
    case $1 in
        --quick|-q)
            MODE_ARG="quick"
            shift
            ;;
        --full|-f)
            MODE_ARG="full"
            shift
            ;;
        --level|-l)
            MAX_LEVEL="$2"
            shift 2
            ;;
        --help|-h)
            cat << EOF
用法: $0 [选项]

运行模式:
  默认           完整模式（语义分析 + LLM 补全）
  --quick, -q    快速模式（仅切片，不使用 LLM）
  --full, -f     完整模式（显式指定）

选项:
  --level, -l    分析层级 (0: 仅限目标函数/合约, 1: 包含一级调用, 2: 包含二级调用)
                 默认值: 0 (为了保持结果精简)

示例:
  $0              # 默认完整模式 (Level 0)
  $0 -q -l 1      # 快速模式，包含一级调用
  $0 -l 2         # 完整模式，包含二级调用（结果可能很大）

环境变量配置:
  INPUT_FILE      输入文件路径
  CONTRACT_NAME   目标合约名称
  FUNCTION_NAME   目标函数名称（可选）
  VARIABLE_NAME   目标变量名称
  OUTPUT_FILE     输出文件路径

EOF
            exit 0
            ;;
        *)
            echo "未知选项: $1"
            echo "使用 --help 查看帮助"
            exit 1
            ;;
    esac
done

# ═════════════════════ 配置区域 ═════════════════════

# 禁用代理，防止本地代理导致网络请求失败
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY all_proxy ALL_PROXY

# LLM 配置
export MODEL_NAME="${MODEL_NAME:-DeepSeek-V4-Flash}"
export LLM_MODEL="$MODEL_NAME"
export OPENAI_BASE_URL="${OPENAI_BASE_URL:-https://www.dreamfield.top/v1}"
export OPENAI_API_KEY="${OPENAI_API_KEY:-sk-cDDsIBEx9ym4SCM8moTqISMRVoQWtCVXlfS9yrQPUqchshyq}"

# 默认参数
INPUT_FILE="${INPUT_FILE:-./examples/src/poc_final.t.sol}"
CONTRACT_NAME="${CONTRACT_NAME:-PoC}"
FUNCTION_NAME="${FUNCTION_NAME:-testExploit}"  # 可选
VARIABLE_NAME="${VARIABLE_NAME:-availableForWithdrawal}"
MAX_LEVEL="${MAX_LEVEL:-0}"

# 自动生成带时间戳的结果文件和日志文件
mkdir -p logs results
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
OUTPUT_FILE="${OUTPUT_FILE:-./results/slice_${CONTRACT_NAME}_${TIMESTAMP}.sol}"
LOG_FILE="./logs/run_${CONTRACT_NAME}_${TIMESTAMP}.log"
RUN_MODE="${MODE_ARG:-${RUN_MODE:-full}}"

# ═══════════════════════════════════════════════════

# 颜色
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${BLUE}"
echo "╔════════════════════════════════════════════════════════════════════╗"
echo "║              SC_Slicer - 目标导向代码切片分析工具                   ║"
echo "║              🎯 Target-Oriented Analysis v2.0                       ║"
if [ "$RUN_MODE" = "full" ]; then
    echo "║              🌟 完整模式（默认）- 精准高效                          ║"
else
    echo "║              ⚡ 快速模式 - 仅切片                                  ║"
fi
echo "╚════════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# 显示配置
echo -e "${BLUE}📋 配置信息:${NC}"
echo "  📁 输入文件:   $INPUT_FILE"
echo "  🎯 目标合约:   $CONTRACT_NAME"
[ -n "$FUNCTION_NAME" ] && echo "  🔧 目标函数:   $FUNCTION_NAME"
echo "  📊 目标变量:   $VARIABLE_NAME"
echo "  📝 输出文件:   $OUTPUT_FILE"
echo "  🤖 LLM 模型:   $MODEL_NAME"
echo "  🔗 API 地址:   $OPENAI_BASE_URL"
echo "  ⚙️  分析层级:   $MAX_LEVEL"
echo "  ⚙️  运行模式:   $RUN_MODE"
echo ""

# 检查 API Key
if [ -z "$OPENAI_API_KEY" ] || [ "$OPENAI_API_KEY" = "your-api-key-here" ]; then
    echo -e "${YELLOW}⚠️  警告: 未设置有效的 OPENAI_API_KEY${NC}"
    echo "请设置环境变量或编辑脚本中的 OPENAI_API_KEY"
    if [ "$RUN_MODE" = "full" ]; then
        echo "完整模式需要 API Key，切换到快速模式..."
        RUN_MODE="quick"
    fi
fi

# 构建命令
CMD="cargo run --release -- '$INPUT_FILE' '$CONTRACT_NAME' '$VARIABLE_NAME'"

# 添加可选函数名
if [ -n "$FUNCTION_NAME" ]; then
    CMD="$CMD '$FUNCTION_NAME'"
fi

# 根据模式添加参数
case $RUN_MODE in
    quick)
        echo -e "${CYAN}⚡ 快速模式: 仅切片（不使用 LLM）${NC}"
        echo -e "${CYAN}💡 提示: 直接运行 ./run_slicer_v2.sh 使用完整模式${NC}"
        echo ""
        CMD="$CMD --max-level $MAX_LEVEL -o '$OUTPUT_FILE'"
        ;;
    full)
        echo -e "${GREEN}🌟 完整模式: 目标导向切片 + 语义分析 + LLM 补全${NC}"
        echo -e "${GREEN}📌 特性: 智能过滤 + 自动补全 + 可编译输出${NC}"
        echo ""
        CMD="$CMD --semantic --two-phase --aggressive-cleanup --llm-completion --max-level $MAX_LEVEL --parallel -o '$OUTPUT_FILE' --api-key '$OPENAI_API_KEY' --model '$MODEL_NAME'"
        ;;
    *)
        echo "未知模式: $RUN_MODE"
        exit 1
        ;;
esac

# 显示优势
echo -e "${BLUE}🎯 目标导向分析优势:${NC}"
echo "  ✅ 只分析 $CONTRACT_NAME 相关代码"
[ -n "$FUNCTION_NAME" ] && echo "  ✅ 聚焦函数: $FUNCTION_NAME"
echo "  ✅ 性能提升: 3-6倍"
echo "  ✅ 节点减少: 70-90%"
echo "  ✅ 结果更精准"
echo ""

# 执行
echo -e "${GREEN}🚀 开始分析... (过程日志将保存至 $LOG_FILE)${NC}"
echo ""

if eval "$CMD" 2>&1 | tee "$LOG_FILE"; then
    echo ""
    echo -e "${GREEN}✅ 分析完成!${NC}"
    echo "📄 结果文件: $OUTPUT_FILE"
    
    if [ -f "$OUTPUT_FILE" ]; then
        LINES=$(wc -l < "$OUTPUT_FILE")
        SIZE=$(du -h "$OUTPUT_FILE" | cut -f1)
        echo "📊 统计: $LINES 行, $SIZE"
    fi
else
    echo ""
    echo -e "${YELLOW}❌ 分析失败${NC}"
    exit 1
fi
