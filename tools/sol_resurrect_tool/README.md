# 🔧 Solidity Resurrector

Solidity Resurrector 是一个基于 AST + LLM 混合架构的智能工具，专门用于将残缺或无法编译的 Solidity 代码片段，快速重建为完整、可测试的 Foundry 代码。

---

## ✨ 核心特性

- **🚀 高精度重构**: 结合 Tree-sitter 的 AST 解析能力与 LLM 语义推理，精准识别悬空函数、缺失的依赖库，并将其智能归位。
- **🔌 易于使用**: 配置简单，直接读取 `.sol` 切片文件，一键生成完整可执行的 `.t.sol` 测试文件。
- **🤖 广泛的 LLM 支持**: 开箱支持兼容 OpenAI 接口规范的各类模型服务（如 GPT-4, DeepSeek 等）。

---

## 🚀 快速开始

### 1. 环境准备

确保已安装 Python 3.8+，然后安装所需依赖：

```bash
pip install -r requirements.txt
```

### 2. 配置 API

运行时配置统一放在 SC_Slicer 项目根目录 `config/llm.env`。第一次使用时可以从示例复制：

```bash
cd /root/sc_slicer_standalone
cp config/llm.env.example config/llm.env
```

配置文件格式：

```bash
LLM_PROVIDER=opencode
MODEL_NAME=opencode-go/deepseek-v4-flash

# 仅在 LLM_PROVIDER=openai 时需要：
# GEMINI_API_KEY=你的 Gemini Key
# OPENAI_API_KEY=你的 OpenAI-compatible Key
# API_BASE_URL=https://api.openai.com/v1
```

默认 `opencode` 模式会调用本机 `opencode run --model ...`，使用 opencode 已登录的凭据，不需要 `API_BASE_URL`。切到 `LLM_PROVIDER=openai` 时，工具会优先读取 `GEMINI_API_KEY`，没有时读取 `OPENAI_API_KEY`；`API_BASE_URL` 必须是 OpenAI 兼容接口，实际请求路径是 `${API_BASE_URL}/chat/completions`。

子工具目录下的 `.env` 仍然兼容，但 SC_Slicer 根目录 `config/llm.env` 会覆盖同名配置。也可以用 `--config` 临时切换：

```bash
cd /root/sc_slicer_standalone
./run_sol_resurrect.sh tools/sol_resurrect_tool/examples/raw.sol --config config/llm.env
```

### 3. 运行重构

准备残缺的 Solidity 代码（如 `examples/raw.sol`），运行以下命令：

```bash
# 基础运行模式，默认将输出写入 runs/sol_resurrect/latest/Resurrected.t.sol
cd /root/sc_slicer_standalone
./run_sol_resurrect.sh tools/sol_resurrect_tool/examples/raw.sol
```

也可以指定输出目录：

```bash
./run_sol_resurrect.sh tools/sol_resurrect_tool/examples/raw.sol --output runs/sol_resurrect/my_case/Resurrected.t.sol
```

### 4. 测试验证

使用 Foundry 验证生成的完整测试代码：

```bash
cd /root/sc_slicer_standalone/runs/sol_resurrect/latest
forge test --match-path test/Resurrected.t.sol --via-ir
```

快速执行一个不调用 LLM 的本地 smoke test：

```bash
cd /root/sc_slicer_standalone
./run_sol_resurrect.sh --smoke
```

如需对 `examples/raw.sol` 跑完整 LLM 重构流程：

```bash
cd /root/sc_slicer_standalone/tools/sol_resurrect_tool
./quicktest.sh --full
```

---

## 📂 目录结构

为保持工作区整洁直观，核心目录结构如下：
- `main.py`: 主程序入口。
- `quicktest.sh`: 快速测试验证脚本。
- `src/`: 核心逻辑源码（AST 解析、LLM 大脑推理、代码组装）。
- `examples/`: 示例输入，当前包含 `raw.sol`。
- `scripts/`: 辅助脚本和本地 smoke test。
- `/root/sc_slicer_standalone/runs/sol_resurrect/`: 运行产物目录，包含输出、Foundry 验证工程和构建日志。
- `/root/sc_slicer_standalone/logs/sol_resurrect/`: 主程序执行日志。

默认运行产物：

```text
runs/sol_resurrect/latest/Resurrected.t.sol       重构后的 Solidity/Foundry 测试文件
runs/sol_resurrect/latest/test/Resurrected.t.sol  Foundry 验证用测试文件副本
runs/sol_resurrect/latest/build.log               forge clean/test 完整日志
runs/sol_resurrect/latest/slice_result.json       v2/effective-slice 结果元数据
logs/sol_resurrect/*.log                          主程序执行日志
```

---

> 💡 **提示**: 生成的 `.t.sol` 文件默认已经补全标准测试框架的 pragma 声明和依赖库 Mock，可直接无缝接入你的智能合约测试工作流。
