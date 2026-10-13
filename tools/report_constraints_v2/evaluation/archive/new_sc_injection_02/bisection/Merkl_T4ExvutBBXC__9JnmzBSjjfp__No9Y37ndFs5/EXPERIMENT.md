# 差异重放归因实验：Merkl（scenario-pinned-preconditions 缺陷族）

预注册于 2026-10-12，运行前冻结。本实验是判读回流的归因仪器（差异重放，
differential replay）：控制变量换件重跑，把"判读结果不对"归因到唯一的肇事
组件。零模型调用。

## 背景（要归因的判读）

冻结判读（`verdict__Merkl….json`，final_holdout_01）：
`{"p":false,"i":true,"v":false}` → **precondition_mismatch**。
阶段二 P/I/V 把报告叙事的示例算术（990/1000/1990/2000）钉成常量等式，
而 PoC 实例化的是两笔 FoT 存款（990/0/1980/2000）。

三个候选肇事者：①报告叙事 vs PoC 现实 ②阶段二翻译失真 ③阶段二表示选择
（翻译忠实但表示过脆）④绑定错。本实验区分之。

## 换件设计（一次只换阶段二的表示，其余全部不变）

| 组件 | 本实验用的 | 与冻结判读的差异 |
| --- | --- | --- |
| 报告 | 同一份 report.json | **不变** |
| 切片 | 同一份 contract.flattened.t.sol | **不变** |
| PoC 场景/观测 | 同一 attack/post 代码 | **不变**（sanity 断言原样保留） |
| 阶段二 P/I/V | **constraints_v2**（见下） | 换件：从同一报告重新形式化 |
| 绑定 | binding_v2 | 仅删不再被引用的 `standard_deposit_received` 符号（覆盖兼容，无观测变化） |

binding 换件单独实验**被跳过**，理由是机械的：冻结判读里 4 项 binding_sanity
断言全部通过，把每个观测钉在 PoC 实际值上（fot=990、liab=2000、bal=1980、
1980<2000）——不存在任何绑定改动能让钉死的 P 为真，绑定侧被排除。

## constraints_v2（同一报告的场景一般化形式化）

- P：`fot_deposit_received > 0`（"发生了一笔扣过手续费的 FoT 存款"——
  报告主张的适用前提，一般化后不含叙事示例数字）
- I：`fot > 0 → total_liabilities ≤ physical_balance`（应然不变量：
  有 FoT 存款时资可抵债）
- V：`fot > 0 ∧ total_liabilities > physical_balance`（PoC 观察到的资不
  抵债，即报告主张的违规）

## 预注册预期（运行前冻结）

| 项 | 预期 |
| --- | --- |
| p | **true**（fot = 990 > 0） |
| i | **false**（implies(true, 2000 ≤ 1980) = false，I 被违反——预期的好消息） |
| v | **true**（990 > 0 ∧ 2000 > 1980） |
| 四分支裁决 | **violation_reproduced** |
| binding_sanity | 4 项全过（与冻结判读相同：观测未变） |
| PoC 测试 | PASS（切片完整性） |
| ingest | consistency_verdict = violation_reproduced |

## 预注册的归因判读

若逐项符合上表：**同一报告、同一切片、同一 PoC 观测，仅换阶段二的表示，
判读从 precondition_mismatch 翻转为 violation_reproduced** → 肇事者 =
**阶段二表示选择**（缺陷族 scenario-pinned-preconditions），回流成立；
报告叙事的示例算术记为诱因（contributing factor），不是肇事者。
若不符合：记录实际结果，归因悬置（attribution: inconclusive）。

结果见 `verdict__Merkl….json`（本目录内）；登记于
`../adjudication_ledger.json`。
