# SC_Slicer v2.0 - 目标导向分析 快速使用指南

> **SC_Slicer** 是一款专为复杂智能合约设计的、具备语义理解能力的代码切片工具。v2.0 版本显著增强了对大型 PoC 的处理能力。

## ⚠️ 安全提示

**切勿将包含真实 API Key 的脚本提交到公共仓库！**

推荐的安全做法：
1. **使用环境变量**: 在终端执行 `export OPENAI_API_KEY="sk-..."` 而非修改脚本。
2. **设置 .gitignore**: 确保包含 `run_slicer*.sh` 如果你决定在其中硬编码 Key。

## 🎯 核心改进

SC_Slicer v2.0 引入了**目标导向增量式分析**与**智能化生命周期管理**：
- ⚡ **性能大幅提升**: 3-6倍，实现秒级响应
- 🎯 **精准切片**: 自动提取 70-90% 的关键节点，忽略无关逻辑
- ✅ **智能补全**: LLM 驱动的三阶段代码补全，确保输出代码的可编译性
- 🔍 **语义增强**: 深入理解变量流向与合约状态
- 💾 **极低开销**: 减少 85% 以上的内存占用

## 📝 使用方法

### 方法 1: 使用脚本（推荐）

#### 简化版（run_slicer.sh）
```bash
# 直接运行（使用默认配置）
./run_slicer.sh

# 自定义配置
CONTRACT_NAME="MyContract" \
VARIABLE_NAME="myVariable" \
./run_slicer.sh
```

#### 增强版（run_slicer_v2.sh）
```bash
# 完整模式（默认，包含 LLM 补全）
./run_slicer_v2.sh

# 使用命令行参数切换模式
# 快速模式（仅切片，不使用 LLM）
./run_slicer_v2.sh --quick
# 或者使用简写
./run_slicer_v2.sh -q

# 显式指定完整模式
./run_slicer_v2.sh --full

# 查看帮助信息
./run_slicer_v2.sh --help

# 指定目标函数（通过环境变量）
FUNCTION_NAME="testExploit" ./run_slicer_v2.sh
```

### 方法 2: 直接使用 Cargo

```bash
# 基础用法（必须提供 4 个参数）
cargo run --release -- \
    <输入文件> \
    <目标合约> \
    <目标函数> \
    <目标变量>

# 示例 1: 分析特定函数和变量
cargo run --release -- \
    ./examples/src/poc_final.t.sol \
    PoC \
    testExploit \
    availableForWithdrawal \
    --semantic \
    --two-phase \
    --aggressive-cleanup \
    --llm-completion \
    --max-level 2 \
    --parallel \
    --api-key "sk-xxx" \
    -o result.txt

# 示例 2: 不指定函数（分析所有访问变量的函数）
cargo run --release -- \
    ./contract.sol \
    MyContract \
    "" \
    myVariable \
    -o result.txt
```

## 🎯 参数说明

### 位置参数（必需）
1. **输入文件**: Solidity 源文件路径
2. **目标合约**: 要分析的合约名称
3. **目标函数**: 要分析的函数名称（可选，传空字符串 `""` 表示所有函数）
4. **目标变量**: 要分析的变量名称

### 可选参数
- `--semantic`: 启用语义分析
- `--two-phase`: 两阶段处理（静态切片 + 语义分析）
- `--aggressive-cleanup`: 激进式代码清理
- `--llm-completion`: LLM 三阶段补全
- `--max-level N`: 最大调用层级（默认 3）
- `--parallel`: 并行 LLM 调用
- `--api-key KEY`: API 密钥
- `--model MODEL`: LLM 模型名称
- `-o FILE`: 输出文件

## 📊 运行效果对比

### 全局分析（v1.0）
```
分析时间: 8-15s
节点数量: 2700+
边失败: 500+
内存占用: ~2MB
```

### 目标导向分析（v2.0）
```
分析时间: 2-4s ⚡
节点数量: ~300 🎯
边失败: <10 ✅
内存占用: ~300KB 💾
```

## 🔍 实际案例

### 案例 1: 分析 PoC 合约的 availableForWithdrawal 变量

```bash
./run_slicer.sh
```

**输出示例**:
```
🎯 Target-oriented analysis: contract=PoC, function=, variable=availableForWithdrawal
✅ Found target contract: PoC
📍 Finding functions that access variable: availableForWithdrawal
  ↳ Analyzing function 'setUp' (accesses availableForWithdrawal)
  ↳ Analyzing function '_setupDefaultOracles' (accesses availableForWithdrawal)
✅ Analyzed 2 relevant functions in contract PoC
```

### 案例 2: 精确分析特定函数

```bash
FUNCTION_NAME="testExploit" \
VARIABLE_NAME="availableForWithdrawal" \
./run_slicer.sh
```

**输出示例**:
```
🎯 Target-oriented analysis: contract=PoC, function=testExploit, variable=availableForWithdrawal
✅ Found target contract: PoC
📍 Analyzing target function: testExploit
✅ Analyzed 1 relevant functions in contract PoC
```

## 🛠️ 配置说明

### 环境变量

在脚本中或命令行设置：

```bash
# LLM 配置
export MODEL_NAME="deepseek-chat"
export OPENAI_BASE_URL="https://api.deepseek.com"
export OPENAI_API_KEY="sk-xxx"

# 分析目标
export INPUT_FILE="./contract.sol"
export CONTRACT_NAME="MyContract"
export FUNCTION_NAME="myFunction"  # 可选
export VARIABLE_NAME="myVariable"
export OUTPUT_FILE="./result.txt"

# 运行模式
export RUN_MODE="full"  # quick | full
```

### 编辑脚本

直接修改 `run_slicer.sh` 或 `run_slicer_v2.sh` 中的配置区域：

```bash
# ═════════════════════ 配置区域 ═════════════════════
export MODEL_NAME="${MODEL_NAME:-deepseek-chat}"
export OPENAI_BASE_URL="${OPENAI_BASE_URL:-https://api.deepseek.com}"
export OPENAI_API_KEY="${OPENAI_API_KEY:-sk-xxx}"

INPUT_FILE="${INPUT_FILE:-./examples/src/poc_final.t.sol}"
CONTRACT_NAME="${CONTRACT_NAME:-PoC}"
FUNCTION_NAME="${FUNCTION_NAME:-}"
VARIABLE_NAME="${VARIABLE_NAME:-availableForWithdrawal}"
OUTPUT_FILE="${OUTPUT_FILE:-./result_clean.txt}"
# ═══════════════════════════════════════════════════
```

## 💡 最佳实践

### 1. 先快速后完整
```bash
# 第一步：先用快速模式验证目标和变量是否正确
./run_slicer_v2.sh --quick

# 第二步：确认无误后，用完整模式生成可编译的代码和语义分析结果
./run_slicer_v2.sh --full
```

### 2. 逐步精细化
```bash
# 第一步：分析所有访问变量的函数
FUNCTION_NAME="" VARIABLE_NAME="myVar" ./run_slicer.sh

# 第二步：如果结果太多，聚焦特定函数
FUNCTION_NAME="specificFunc" VARIABLE_NAME="myVar" ./run_slicer.sh
```

### 3. 批量分析
```bash
# 创建批量脚本
for var in "var1" "var2" "var3"; do
    VARIABLE_NAME="$var" \
    OUTPUT_FILE="result_${var}.txt" \
    ./run_slicer.sh
done
```

## 🐛 故障排查

### 问题 1: "Target contract not found"
- 检查合约名是否正确（区分大小写）
- 确认合约在输入文件中存在

### 问题 2: "No functions analyzed"
- 检查变量名是否正确
- 尝试不指定函数名（传空字符串）

### 问题 3: API Key 错误或 LLM 响应缓慢
- 确认 API Key 正确设置（建议在脚本配置区或环境变量中通过 `OPENAI_API_KEY` 设置）
- 检查 `OPENAI_BASE_URL` 是否匹配您的 API 提供商
- 若网络不稳定，可以尝试使用 `--parallel` 参数（v2.0 默认在 `full` 模式开启）加快调用速度
- 快速排查：使用 `--quick` 模式跳过 LLM 步骤，确认切片逻辑是否正常

### 问题 4: 内存不足或编译失败
- 尝试通过 `MAX_LEVEL` 环境变量或 `--max-level` 参数限制递归分析的深度（默认 2-3 层）
- 开启 `--aggressive-cleanup` 进行更彻底的代码精简

## 📚 更多信息

- 详细文档: [TARGET_ORIENTED_ANALYSIS.md](TARGET_ORIENTED_ANALYSIS.md)
- 技术原理: 查看 `src/analyzer.rs` 中的 `analyze_asts_targeted()` 函数
- 问题反馈: 提交 Issue 或查看日志文件

## 🎉 快速开始

```bash
# 1. 克隆项目
cd /root/sc_slicer_standalone

# 2. 编译（首次）
cargo build --release

# 3. 运行默认示例
./run_slicer.sh

# 4. 查看结果
cat result_clean.txt
```

祝您使用愉快！🚀
