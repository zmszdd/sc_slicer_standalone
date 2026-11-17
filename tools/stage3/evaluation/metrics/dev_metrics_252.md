# dev 集指标（客观 252 例，stage3 已跑完的全部判例 valid 案例）

## 口径

- 判例 ground truth：`judge_ground_truth.json`
  - 总计 1556；valid=959，fixed=441，wontfix=65，invalid=91
  - “相关/有效”= valid+fixed+wontfix = **1465**
- dev252 = 其中已跑完 stage3 的 252 例（未挑拣，全部为 judge-valid）
- 精确率含盲测无效集：14 例 FP 全部来自 blind-invalid，TN=58，pool FP=0

## 四指标（统一分母、客观口径）

| 指标 | 数值 | 分子/分母 | 说明 |
| --- | ---: | --- | --- |
| 端到端召回率 | **68.7%** | 173 / 252 | 95% CI 62.7%–74.1%；未判定、绑定失败、天花板一律计 FN |
| 判例锚定精确率 | **92.5%** | 173 / (173+14) | FP 全部来自 blind-invalid；95% CI 87.8%–95.5% |
| 漏洞级精确率 | **98.3%** | — | 排除 11 例“影响不足”FP 后；剩余 FP=3 |
| 全量完成率 | **17.2%** | 252 / 1465 | dev252 是“已跑完子集”，非全量覆盖 |
| F1（端到端×判例精确率） | **0.788** | — | 2·(0.687·0.925)/(0.687+0.925) |

## 上限与可恢复

- 端到端机制天花板：99.2%（2 例机制硬天花板，250/252 理论上限）
- 可恢复 FN：77 例；当前 FN=79
- 可评测召回（仅参考，非主口径）：89.6%（173/193）

## 当前 FN 分桶（79 例）

| 分桶 | 数量 |
| --- | ---: |
| mixed_non_dynamic | 35 |
| invariant_holds_on_exploit_path | 15 |
| partial_binding | 14 |
| poc_not_witnessed | 7 |
| compile_error | 2 |
| binding_error | 2 |
| reference_patch_required | 1 |
| inconclusive | 1 |
| not_dynamically_expressible | 1 |
| patch_no_effect | 1 |

主要剩余瓶颈是阶段二弱不变量（I 在 exploit 路径上恒成立）与语义型
`UNBOUND`（时间窗、跨合约状态、派生布尔量），不是单纯 stage3 重绑定。

> 2026-11-17 补丁：阶段二强不变量 gate、可观测性合同、stage3 语义
> `UNBOUND` 分类器与弱不变量风险诊断已落地；离线重放见
> `weak_invariant_offline_252.json`（TP 误杀 1.19%，新增 code 误杀 0）。
> 本轮未重跑 LLM campaign，故上表四指标保持不变。

> 主口径说明：recall 分母固定为全部 252 例；完成率分母为全量有效判例 1465，
> 不再是“dev 内全部跑完”。精确率以盲测无效集为准，不再报 100%。
