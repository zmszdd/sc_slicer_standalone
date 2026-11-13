# 盲测阶段三结果与根因

盲测 stage2 通过的 4 案例共 **10** claim，动态复现 **0**，端到端召回 **0%**。

| 案例 | claims | 复现 | 主要 verdict |
| --- | ---: | ---: | --- |
| Lambo.win_LVoZUeMUNkB__105 | 2 | 0 | binding_failed, compile_blocked |
| Sequence_jEtbuty6H23__144 | 1 | 0 | compile_blocked |
| Sequence_jEtbuty6H23__18 | 6 | 0 | binding_error, compile_blocked, partial_binding |
| Silo_Finance_yjrYyfyTzWc__444 | 1 | 0 | partial_binding |

## 修复前后 verdict 分布

| verdict | 修复前 | 修复后 |
| --- | ---: | ---: |
| binding_error | 1 | 1 |
| binding_failed | 0 | 1 |
| compile_blocked | 1 | 3 |
| not_dynamically_expressible | 5 | 0 |
| partial_binding | 3 | 5 |

## 根因（按影响排序）

- **无 test 入口（硬阻塞）**：盲测 audit `stage_ready=0`，PoC 动作分布 {'no_poc_code': 33, 'snippet_only': 4, 'fork_rpc': 3}（`no_poc_code` 33 / `snippet_only` 4 / `fork_rpc` 3 / `self_contained` 0）。所有案例 `Resurrected.t.sol` 都没有 `test_*` 函数；`forge test` 报 `No tests found`，差分无法运行。合约级 flatten 只含 `src` 不含 PoC 测试。实测 Sequence__144：submission 的 PoC 代码块可 `forge flatten` 成含 `testCrossWalletReplayAttack` 的 harness，但该 PoC 依赖 `vm.envUint`/`vm.rpc` fork 本地 RPC，不是自包含测试；sol_resurrect 产出为空壳 stub。
- **`no_anchor` 过度路由（已修）**：确定性模糊匹配把 「zero shares」映射不到 `_mint`/`balanceOf`，硬路由成 `not_dynamically_expressible`（修复前 5/10）。现在只有 `low` 可观测性才硬路由，其余交给 binding LLM。
- **library/contract 定位（已修）**：patch 注入只匹配 `contract`，`library SessionSig` 触发 `binding_error`；已扩展到 `abstract contract`/`library`。
- **UNBOUND 符号**：`partial_binding` 5 例，binding LLM 未完成 I/V 绑定，走 fn_work_queue 的 rebind。
- **stage2 实体类型误判**：`contract` vs `library` 的语义提取错位。

## 结论

盲测跨项目 e2e 目前无法测出真实召回，因为测试 harness 未就绪；在 harness 补齐前不应据此调 dev 指标。两个 pipeline 级根因已修复，剩余为数据就绪与绑定质量。
