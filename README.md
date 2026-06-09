# SC_Slicer

**SC_Slicer** 是一款专为智能合约设计的目标导向代码切片工具。它基于程序依赖图（PDG），具备语义理解能力，能够快速且精准地从复杂的 Solidity 项目中提取关键代码路径，极大提升代码审计和分析效率。

## 🚀 核心特性

- **🎯 目标导向分析**: 精确锁定指定的合约、函数和变量，自动过滤无关逻辑。
- **⚡ 高性能**: 实现秒级响应，相较于全局分析性能提升 3-6 倍。
- **💡 智能补全**: 集成 LLM 支持三阶段代码智能补全，保障切片代码的独立编译。
- **📉 低开销**: 优化内存占用结构，减少 80% 以上的资源消耗。

## 📦 快速开始

### 1. 编译项目
确保已安装 Rust 并在项目根目录运行：
```bash
cargo build --release
```

### 2. 运行工具
使用提供的快捷脚本 `run.sh` 运行切片分析。

```bash
# 执行完整流程（包含代码切片 + LLM 语义补全）
./run.sh

# 执行快速模式（仅运行静态切片，跳过 LLM 补全）
./run.sh --quick
```

### 3. 配置分析参数

通过直接修改 `run.sh` 中的变量或在命令行设置环境变量来自定义分析目标：

```bash
export INPUT_FILE="./examples/src/poc_final.t.sol"     # 输入源文件
export CONTRACT_NAME="PoC"                             # 目标合约名
export FUNCTION_NAME="testExploit"                     # 目标函数名（可选）
export VARIABLE_NAME="availableForWithdrawal"          # 目标变量名
export OPENAI_API_KEY="sk-..."                         # 完整模式所需的 LLM API Key

./run.sh
```

## 🛠️ 进阶参数

支持通过 `-l` 或 `--level` 参数指定调用的分析层级：
```bash
# 指定包含一层函数调用深度的切片
./run.sh --level 1
```

*(运行 `./run.sh --help` 可查看完整的帮助说明和运行模式)*
