#!/bin/bash

# ================= 配置区域 =================

# 1. 设置 LLM 模型名称
# DeepSeek 官方 API 模型名为: deepseek-chat (通用) 或 deepseek-coder (代码专用)
# 硅基流动的模型名为: deepseek-ai/DeepSeek-V3.2
# OpenAI 模型名为: gpt-4o
export MODEL_NAME="deepseek-chat"

# 2. 设置 API Base URL (接口地址)
# 注意：https://api.siliconflow.cn 仅限中国大陆访问，当前环境位于海外，无法连接。
# 请使用全球可访问的 DeepSeek 官方接口 或 OpenAI 官方接口。
export OPENAI_BASE_URL="https://api.deepseek.com"

# 3. 设置 API KEY
# 必填！请将下方引号内的内容替换为你真实可用的 DeepSeek 官方 API Key (sk-...)
export OPENAI_API_KEY="sk-4d65d403d3a14e10b027c1cd65f3da77"

# ===========================================

echo "正在运行 sc_slicer..."
echo "使用模型: $MODEL_NAME"
echo "API 地址: $OPENAI_BASE_URL"

# 检查是否填写了 Key
if [ -z "$OPENAI_API_KEY" ]; then
    echo "❌ 错误: 未设置 OPENAI_API_KEY"
    echo "请编辑本脚本 (run_slicer.sh)，填入你的 DeepSeek 官方 API Key。"
    exit 1
fi

# 运行 Cargo 命令
cargo run --release -- \
    ./examples/src/poc_final.t.sol \
    PoC \
    availableForWithdrawal \
    --semantic \
    --two-phase \
    --aggressive-cleanup \
    --max-level 2 \
    --parallel \
    --model "$MODEL_NAME" \
    -o ./result_clean.txt

echo "运行结束，结果已保存至 result_clean.txt"
