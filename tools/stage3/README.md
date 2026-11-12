# 阶段三：把报告不变量做成补丁，用 Foundry 动态验证一致性

本目录只负责阶段三：把阶段二 `stage3-spec.json` 中每条 claim 的 P/I/V 不变量绑定到
真实 Solidity 代码的可观测点，生成“打补丁合约”，用 Foundry 跑原始版本与补丁版本的
同一套测试，比较执行差异，最后把结果回填成 `stage3-consistency.json`。

阶段三不做静态证明，也不判断报告真假。动态测试只能产出“复现/未复现”的有界见证，
`unsat` 一律解释为“给定测试范围内未复现”。

## 与阶段二的关系

- 输入来自阶段二 run 目录：`stage3-spec.json`、`constraints.json`、`formalization.json`。
- 输出是 `stage3-consistency-feedback.json`，并调用阶段二的
  `lib/stage3_consistency.py::ingest_feedback()` 落盘权威的
  `stage3-consistency.json`。
- 阶段三不修改阶段二、阶段一或原始合约源码。

## 命令

```bash
# 单案例
python main.py stage3 --case-dir cases/panoptic_builder_init

# 从阶段一/二产物组装案例（三阶段通道）
python main.py pipeline --name N --src slice.sol --stage2-run <dir> \
  --binding binding.json --test poc.t.sol --run --run-id N_001

# 批量
python main.py stage3 batch --cases-root cases --output /tmp/summary.json

# 全自动评测：组装 + LLM 提绑定（带 hint 的多轮修复） + 差分运行
python -m cli.stage3_eval_run --goldset-root <goldset> --flatten-root <flatten> \
  --cases-root cases --out /tmp/eval_run.json --max-binding-rounds 3

# 一站式全流程自动化：组装 -> 多轮绑定 -> 差分 -> 裁决闭环 -> 验收门
python main.py stage3 autorun --goldset-root <goldset> --flatten-root <flatten> \
  --cases-root cases --out /tmp/autorun.json --repair-loop \
  --min-reproduction-rate 0.5 --min-terminal-rate 0.8

# 裁决闭环：对可修复裁决（partial_binding / preconditions_infeasible /
# compile_error / inconclusive）按 replan 诊断重提绑定并重跑
python main.py stage3 verdict-loop --case-dir cases/<case> --max-rounds 2

# 验收门：汇总复现率 / 终态率，可按阈值 gating
python main.py stage3 acceptance --summary /tmp/eval_run.json \
  --min-reproduction-rate 0.5 --min-terminal-rate 0.8

# 四指标 + 判例锚定一条命令（按需负样本用 --negative，或 --negative-results 复用）
python main.py stage3 full-flow --goldset-root <goldset> \
  --flatten-root <flatten> --cases-root cases --out-dir /tmp/fullflow
```

`--run-id` 可省略，自动按案例名 + UTC 时间戳生成。运行产物写入
`runs/<run-id>/`，包含 `original/`、`patched/` 两个 Foundry 工程、
`stage2/` 里的阶段二产物副本，以及权威的 `stage3-consistency.json`。

## 补丁两条路径

- 参考补丁：`case/patched/` 存在时原样使用（M1 手工路径）。
- AST 自动注入：无 `patched/` 时，按 `binding.json` 的 `patch` 说明把 P/I
  断言注入 `src/` 指定函数（M4 路径）。注入语义为“在 P 成立的路径上断言 I”，
  不会把 P 当成无条件 `require`。

## 自动化的故障隔离

- 注入点定位到函数体最后一个顶层声明之后，避免把快照插在未声明符号之前。
- 绑定 lint 增加了合约作用域校验：`solidity_expr` 的根标识符若引用其他合约
  的状态变量（同文件内可见性不一致）会在 strict 下拦下，避免 forge 编译失败。
- 补丁工程编译失败时，自动从 forge 报错提取肇事标识符，并优先做确定性
  snapshot 重定位；不再以类型安全常量中性化绑定。重定位仍失败时保留
  `compile_error`，交给裁决闭环补绑修复，避免常量绑定造成的假阴性。
- `stage3_eval_run --max-binding-rounds N` 会在提案/ lint 失败时带 repair hint
  重提绑定，最多 N 轮。
- 无法在代码观测的符号由 LLM 标成 `UNBOUND`：pipeline 在注入/编译前 fail
  closed，直接产出 `partial_binding` 并列出 `unbound_symbols`，不再伪造
  常量绑定。

## 已内置案例

- `smoke_vault`：数值 `before/after` + 手工参考补丁。
- `access_control`：地址/布尔权限不变量 + 自动注入 + 安全路径。
- `mint_supply`：数值供应量不变量 + 自动注入。
- `panoptic_builder_init`：真实 code4rena `2025-12-panoptic` finding 17，
  `BuilderWallet.init` 无访问控制导致 admin 可被任意调用者覆盖。
- `panoptic_builder_init_stage1`：同一漏洞，`src/` 来自阶段一 slicer 产物，
  用于验证 阶段一 → 阶段二 → 阶段三 完整串行链路。

`smoke_vault_fixed_src` 预期 `violation_not_reproduced`（负样本），
`smoke_vault_bad_binding` 预期 `preconditions_infeasible_on_code`（绑定错误样本）；
七个案例均已端到端跑通。

## 回归

```bash
cd "$(git rev-parse --show-toplevel)/tools/stage3"
python3 -m unittest discover -s tests
```

依赖：`forge`（可用 `FORGE` 环境变量覆盖）、`solc`（Foundry 自带），
以及 `z3-solver`（`pip install -r requirements.txt`）。

完整三阶段流水线报告见仓库根目录 `docs/THREE_STAGE_PIPELINE.md`。
