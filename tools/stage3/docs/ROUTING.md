# 主线路由与评测汇总

主线：阶段一 flatten → 阶段二 PIV → 阶段三 绑定+差分+裁决。阶段二产出的是
报告级语义抽象，阶段三此前把所有 claim 都塞进同一条单点 `assert(I)` 注入路径，
导致 `multi_contract`（65% claim）与 should-be 语义大量弃权（`inconclusive`），
拉低了单一的全流程召回，且无法归因。

## 路由层

`lib/routing.py::classify_route` 把 `lib/anchor_resolver.resolve_anchors` 的
bindability 归并为四条主线路由：

| route | bindability | 验证方式 | auto_verifiable |
| --- | --- | --- | --- |
| `auto_assert` | single_anchor / file_level | `assert(I)` 注入 + Foundry 差分 | 是 |
| `reference_patch_cross_contract` | multi_contract | M1 参考补丁 `case/patched/` | 否 |
| `reference_patch_should_be` | no_anchor | 仅参考补丁，代码不计算该值 | 否 |
| `unbound_feedback` | 预留 | 回写阶段二细化 | 否 |

`cli/stage3_pipeline.py` 在进入 Foundry 前先算路由并落盘 `routing.json`。

**路由是提示，不是硬门**：`routing.json` 记录的是锚点保守上界；真正决定能否
`assert(I)` 注入的是**实际 binding 的可表达性**（`lib/expressibility` 的 lint）。
很多 `multi_contract` claim 的符号虽跨合约，但 binding 仍落到单合约注入点并能复现，
若用上界直接挡路会把这些复现误杀。

- 实际 binding `expressible`：走 `auto_assert` 注入（无论锚点上界为何）。
- 实际 binding `cross_contract_reference` 且无 `case/patched/`：终态
  `reference_patch_required`；有 `case/patched/` 则按 M1 路径跑差分。
- 该终态已加入 `lib/verdict_loop.NON_FIXABLE_VERDICTS`（skip，不重试）。

## 评测汇总

`cli/eval_report.py` 把运行产物聚合成“按主线路由分桶”的指标，区分
`recall(全分母)` 与 `recall(auto_assert)`：

```bash
# 按 runs 目录（每个 run 有 stage3-summary.json + routing.json）
python -m cli.eval_report --runs-dir runs --out /tmp/metrics.json

# 按 stage3-eval-run 汇总
python -m cli.eval_report --eval-run /tmp/eval_run.json --out /tmp/metrics.json
```

输出 `metrics.json` 含 `verdict_histogram`、`loss_buckets`、
`route_verdict_histogram` 与分层召回。判定口径不变：只有
`violation_reproduced` 上升才算召回改善，`reference_patch_required` 是
可归因的终态，不再混入 `inconclusive`。

## B 路径端到端验证

`cases/refpatch_cross_contract/` 是自包含的跨合约参考补丁夹具：`Registry` 持有
`whitelisted` 映射，`Gate.enter()` 在原始版不校验白名单，补丁版注入跨合约
`assert(registry.whitelisted(msg.sender))`。`resolve_anchors` 将其归为
`multi_contract`（锚点分别属于 `Registry` / `Gate`），路由为
`reference_patch_cross_contract`。

实测（`runs/refpatch_cross_contract_002`）：

- `consistency_verdict = violation_reproduced`
- `P_and_T = sat`、`P_and_T_and_not_I = sat`、`P_and_T_and_V = sat`

证明多合约 claim 不再弃权为 `inconclusive`：有参考补丁时走 M1 差分并能真实复现，
无参考补丁时落 `reference_patch_required` 终态。
