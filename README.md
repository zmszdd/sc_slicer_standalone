# SC_Slicer

SC_Slicer 是一个面向 Solidity 合约的目标导向代码切片工具。当前推荐使用 `run.sh` 入口运行，它会按指定的输入文件、目标合约、目标测试函数和目标变量生成切片合约，并可自动用 Foundry 复跑目标测试。

## 统一入口

仓库根目录的 `main.py` 是**阶段二 / 阶段三 / 三阶段 pipeline** 的统一命令行入口；
阶段一（Rust 切片器，唯一引擎 `resurrect-v2`）请直接用 `./run.sh`：

## 环境准备（可移植）

依赖：Python 3.10+、`z3-solver`、Foundry(`forge`)、Rust(`cargo`/`rustc`)。

```bash
./scripts/doctor.sh              # 只读自检，列出缺失项
./scripts/bootstrap.sh install   # 一键补齐依赖
# 或等价：make doctor / make install
```

若使用自定义解释器或 forge，可用环境变量覆盖：

```bash
PYTHON=/path/to/python ./scripts/doctor.sh
FORGE=/path/to/forge make test-stage3
```

阶段二入口（需要已安装 `z3-solver`）：

```bash
python main.py --help          # 列出全部命令
python main.py doctor          # 环境与配置自检
python main.py run --case-dir ...   # 阶段二：报告 → P/I/V 规则化
python main.py verify <目录>   # 阶段二：零模型调用重放
python main.py test            # 阶段二回归
python main.py frozen          # 校验阶段一/v1 冻结资产未被改写
python main.py stage3 ...      # 阶段三：单案例差分验证
python main.py pipeline ...    # 三阶段串联：组装 + 运行
```

`main.py` 只做分发，不实现阶段逻辑；阶段实现仍在 `run.sh`、`src/` 和 `tools/report_constraints_v2/`。下面的 `./run.sh` 写法继续有效。详见 [tools/report_constraints_v2/STRUCTURE.md](tools/report_constraints_v2/STRUCTURE.md)。

## 工程门禁

```bash
make doctor        # 只读自检
make test          # cargo test + 阶段二/三/pipeline 回归
make e2e           # 阶段一切片 + forge test 端到端闭环
```

CI（`.github/workflows/ci.yml`）包含 `stage1-rust`、`stage1-e2e`、`stage2-offline`、
`stage3-unit` 和 `pipeline-e2e` 五个 job。

## 快速运行

在项目根目录执行：

```bash
cd "$(git rev-parse --show-toplevel)"
./run.sh
```

默认目标是当前 PoC：

```text
输入文件: ./examples/src/poc_final.t.sol
目标合约: PoC
目标测试: test_submissionValidity
目标变量: availableForWithdrawal
模式:     resurrect-v2
层级:     0
```

等价核心命令是：

```bash
cargo run --release -- ./examples/src/poc_final.t.sol PoC availableForWithdrawal \
  --target-test test_submissionValidity \
  --aggressive-cleanup \
  --resurrect-v2 \
  --max-level 0 \
  -o ./results/<run-id>.sol
```

## 输出文件

不指定 `-o/--output` 时，脚本会自动生成唯一文件名，避免覆盖历史结果。

一次运行会生成类似下面的文件：

```text
results/slice_PoC_test_submissionValidity_availableForWithdrawal_v2_20260616_151234_12345.sol
results/slice_PoC_test_submissionValidity_availableForWithdrawal_v2_20260616_151234_12345.sol.v2.json
logs/slice_PoC_test_submissionValidity_availableForWithdrawal_v2_20260616_151234_12345.log
logs/slice_PoC_test_submissionValidity_availableForWithdrawal_v2_20260616_151234_12345.forge-test.log
foundry_runs/slice_PoC_test_submissionValidity_availableForWithdrawal_v2_20260616_151234_12345/
```

含义：

```text
.sol                 切片后的合约源码
.sol.v2.json         v2 切片元数据，包括 compile_success、last_command 等
.log                 slicer 运行日志
.forge-test.log      目标 forge test 日志
foundry_runs/.../    本地 Foundry 验证工程
```

## 目录布局

根目录只保留主入口和 Rust 工程文件。辅助数据和批处理脚本放在下面这些目录：

```text
data/code4rena/          Code4rena 项目清单 CSV
scripts/code4rena/       Code4rena 报告抓取、批量 flatten、fallback flatten 脚本
tools/sol_resurrect_tool/ Python 版 Solidity Resurrector 子工具
config/llm.env           统一 LLM 运行配置，本地真实 key，不提交
logs/code4rena/          历史 Code4rena 抓取日志
code4rena_reports/       已抓取的报告、coverage manifest 和 repo queue
c4_pipeline_output/      flatten pipeline 的批量输出和 GitHub 仓库缓存
```

常用 Code4rena 辅助命令：

```bash
python3 scripts/code4rena/fetch_code4rena_reports.py --audit-only
bash scripts/code4rena/run_code4rena_flatten_batch_from_csv.sh
```

## Solidity Resurrector 子工具

Python 版 `sol_resurrect_tool` 已整合到：

```text
tools/sol_resurrect_tool/
```

LLM 配置统一放在项目根目录：

```text
config/llm.env
config/llm.env.example
```

当前配置字段：

```bash
LLM_PROVIDER=opencode
MODEL_NAME=opencode-go/deepseek-v4-flash

# 仅在 LLM_PROVIDER=openai 时需要：
# OPENAI_API_KEY=...
# API_BASE_URL=https://api.openai.com/v1
```

运行 smoke test：

```bash
./run_sol_resurrect.sh --smoke
```

运行完整重构：

```bash
./run_sol_resurrect.sh tools/sol_resurrect_tool/examples/raw.sol
```

默认输出：

```text
runs/sol_resurrect/latest/Resurrected.t.sol
logs/sol_resurrect/*.log
```

## 自定义输入参数

推荐直接通过命令行参数传入，不需要修改脚本。

参数对应关系：

```text
-i, --input FILE       输入 Solidity 文件
-c, --contract NAME    目标合约名
--fn NAME              目标测试/函数名，会传给 --target-test
-v, --variable NAME    目标变量名
-l, --level N          最大依赖层级，对应 --max-level
-o, --output FILE      指定输出文件；不指定则自动生成唯一文件名
```

例如，分析另一个文件、合约、测试函数和变量：

```bash
./run.sh \
  --input ./examples/src/poc_final.t.sol \
  --contract PoC \
  --fn test_submissionValidity \
  --variable availableForWithdrawal \
  --level 0
```

如果希望输出到固定文件：

```bash
./run.sh \
  -i ./examples/src/poc_final.t.sol \
  -c PoC \
  --fn test_submissionValidity \
  -v availableForWithdrawal \
  -o ./results/my_slice.sol
```

注意：指定固定 `-o` 会覆盖同名文件。日常跑实验建议不传 `-o`，让脚本自动命名。

## 常用运行方式

生成 v2 切片并复跑目标测试：

```bash
./run.sh
```

只生成切片，不额外复跑 `forge test`：

```bash
./run.sh --no-rerun-test
```

默认情况下，脚本会把可复跑的 Foundry 工程放在项目内：

```text
./foundry_runs/<run-id>/
```

该目录会包含：

```text
foundry_runs/<run-id>/ResurrectedV2.t.sol
foundry_runs/<run-id>/foundry.toml
```

之后可以手动复跑：

```bash
forge test --root ./foundry_runs/<run-id> \
  --match-contract PoC \
  --match-test test_submissionValidity \
  --via-ir
```

如果想指定自己的 Foundry 工程目录：

```bash
./run.sh --manual-project ./foundry_runs/my_verify_project
```

## 运行模式

默认使用 `--resurrect-v2`：

```bash
./run.sh --v2
```

`--quick` 现在是 v2 引擎的别名，不再走旧切片器：

```bash
./run.sh --quick
```

开启 v2 的更宽松编译保证：

```bash
./run.sh --compile-guarantee
```

## 验证结果

运行完成后，终端会打印实际输出文件、元数据文件、测试日志和可复制的手动验证命令。

成功时应看到类似：

```text
[PASS] test_submissionValidity()
Suite result: ok. 1 passed; 0 failed
```

也可以查看对应的元数据：

```bash
cat results/<run-id>.sol.v2.json
```

其中关键字段：

```text
compile_success: true 表示切片结果编译/测试通过
slice_effective: true 表示没有退化成完整源文件
last_command          记录实际执行的 forge test 命令
```

## 查看帮助

```bash
./run.sh --help
```

## 报告约束实验 v1（第二阶段）

早期“报告自然语言 → 安全性质及效果约束”v1 已停止开发并完整归档到
`archives/report_constraints_v1_20260912.zip`；当前实现统一位于
[tools/report_constraints_v2](tools/report_constraints_v2/README.md)。

第二版的统一接口和只读切片绑定见 [tools/report_constraints_v2](tools/report_constraints_v2/README.md)。该版保留 v1 不变；真实样例因切片依赖缺失被阻断，尚未端到端打通。
