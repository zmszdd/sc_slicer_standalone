#!/bin/bash

# ╔════════════════════════════════════════════════════════════════════╗
# ║              SC_Slicer - 目标导向代码切片分析工具                   ║
# ║              Target-Oriented Analysis v2.0 (简化版)                ║
# ╚════════════════════════════════════════════════════════════════════╝

# ═════════════════════ 配置区域 ═════════════════════

# 1. 设置 LLM 模型名称
export MODEL_NAME="${MODEL_NAME:-deepseek-chat}"

# 2. 设置 API Base URL (接口地址)
export OPENAI_BASE_URL="${OPENAI_BASE_URL:-https://api.deepseek.com}"

# 3. 设置 API KEY
export OPENAI_API_KEY="${OPENAI_API_KEY:-sk-4d65d403d3a14e10b027c1cd65f3da77}"

# 4. 目标配置
INPUT_FILE="${INPUT_FILE:-./examples/src/poc_final.t.sol}"
CONTRACT_NAME="${CONTRACT_NAME:-PoC}"           # 🎯 目标合约
FUNCTION_NAME="${FUNCTION_NAME:-}"              # 🎯 目标函数（可选）
VARIABLE_NAME="${VARIABLE_NAME:-availableForWithdrawal}"  # 🎯 目标变量
OUTPUT_FILE="${OUTPUT_FILE:-./result_clean.txt}"

# ===========================================

echo "╔════════════════════════════════════════════╗"
echo "║   SC_Slicer - 目标导向分析 v2.0           ║"
echo "╚════════════════════════════════════════════╝"
echo ""
echo "🎯 目标合约: $CONTRACT_NAME"
[ -n "$FUNCTION_NAME" ] && echo "🔧 目标函数: $FUNCTION_NAME"
echo "📊 目标变量: $VARIABLE_NAME"
echo "🤖 使用模型: $MODEL_NAME"
echo ""

# 检查是否填写了 Key
if [ -z "$OPENAI_API_KEY" ] || [ "$OPENAI_API_KEY" = "your-api-key-here" ]; then
    echo "❌ 错误: 未设置有效的 OPENAI_API_KEY"
    echo "请编辑本脚本 (run_slicer.sh)，填入你的 API Key。"
    exit 1
fi

echo "🚀 启动目标导向分析..."
echo "  ✅ 只分析与 $CONTRACT_NAME 相关的代码"
echo "  ⚡ 性能提升: 3-6倍"
echo "  🎯 节点减少: 70-90%"
echo ""

# 运行 Cargo 命令（目标导向分析自动启用）
cargo run --release -- \
    "$INPUT_FILE" \
    "$CONTRACT_NAME" \
    "${FUNCTION_NAME}" \
    "$VARIABLE_NAME" \
    --semantic \
    --two-phase \
    --aggressive-cleanup \
    --llm-completion \
    --max-level 2 \
    --parallel \
    --api-key "$OPENAI_API_KEY" \
    --model "$MODEL_NAME" \
    -o "$OUTPUT_FILE"

echo ""
echo "✅ 运行结束，结果已保存至 $OUTPUT_FILE"
