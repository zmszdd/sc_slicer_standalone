#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
cd "${SCRIPT_DIR}"

echo "🔧 Solidity Resurrector - 快速测试脚本"
echo "========================================"
echo ""

echo "[1/4] 检查 Python 环境..."
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未安装 Python3"
    exit 1
fi
echo "✅ Python3 已安装: $(python3 --version)"
echo ""

echo "[2/4] 检查并安装依赖..."
pip install -q -r requirements.txt
echo "✅ 依赖已就绪"
echo ""

echo "[3/4] 检查 smoke test..."
if [ ! -f "scripts/smoke_test.py" ]; then
    echo "❌ 错误: 找不到 smoke test 脚本 scripts/smoke_test.py"
    exit 1
fi
echo "✅ 准备就绪"
echo ""

echo "[4/4] 运行本地 smoke test..."
python3 scripts/smoke_test.py

echo ""
echo "========================================"
echo "✅ smoke test 完成"

if [ "${1:-}" = "--full" ]; then
    echo ""
    echo "[FULL] 开始运行 examples/raw.sol，需要 ${WORKSPACE_ROOT}/config/llm.env 中配置 API。"
    if [ ! -f "${WORKSPACE_ROOT}/config/llm.env" ]; then
        echo "⚠️  警告: 未找到 ${WORKSPACE_ROOT}/config/llm.env，请先从 config/llm.env.example 复制并配置 API 信息"
        exit 1
    fi
    if [ ! -f "examples/raw.sol" ]; then
        echo "❌ 错误: 找不到输入文件 examples/raw.sol"
        exit 1
    fi
    python3 main.py examples/raw.sol --config "${WORKSPACE_ROOT}/config/llm.env"
    echo "✅ full run 输出: ${WORKSPACE_ROOT}/runs/sol_resurrect/latest/Resurrected.t.sol"
fi
