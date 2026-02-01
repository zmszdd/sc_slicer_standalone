#!/bin/bash
# 一键运行：切片 + LLM修复

set -e

# 清除可能存在的失效环境变量，使用脚本中的默认密钥
unset OPENAI_API_KEY

# 切片目标变量（默认为availableForWithdrawal）
SLICE_TARGET="${1:-availableForWithdrawal}"

echo "🚀 SC_Slicer 完整流程（切片 + LLM智能补全）"
echo "🎯 切片目标变量: $SLICE_TARGET"
echo "💡 LLM补全已集成到切片流程（通用于任何合约/变量）"
echo "================================"
echo ""

# 1. 运行切片器（已启用 --llm-completion）
echo "📍 运行完整切片流程（含LLM三阶段补全）..."
./run_slicer.sh -f examples/src/poc_final.t.sol --mode full --no-compile << EOF
y
EOF

echo ""
echo "================================"
echo ""

# 注意：LLM 补全已集成到 run_slicer.sh 中（通过 --llm-completion 参数）
# 以下 Python 脚本为备用方案（仅在 Rust 侧失败时使用）

if [ ! -f "result_clean.txt" ]; then
    echo "❌ 切片失败，未生成 result_clean.txt"
    exit 1
fi

# 检查是否已经通过 Rust 侧补全（检查文件开头是否有补全标记）
if head -5 result_clean.txt | grep -q "添加缺失的函数实现\|LLM补全"; then
    echo "✅ LLM补全已由 Rust 侧完成（集成在切片流程中）"
    echo "   输出文件: result_clean.txt"
else
    echo "📍 备用方案: 使用 Python 脚本进行 LLM 补全..."
    if [ -f "llm_smart_fix.py" ]; then
        python3 llm_smart_fix.py result_clean.txt "$SLICE_TARGET"
        echo "   输出文件: result_clean_fixed.sol"
    else
        python3 llm_fix.py result_clean.txt
        echo "   输出文件: result_clean_fixed.sol"
    fi
fi

echo ""
echo "================================"
echo "✅ 全部完成！"
echo ""
echo "🔍 验证编译: forge build --contracts result_clean.txt"
