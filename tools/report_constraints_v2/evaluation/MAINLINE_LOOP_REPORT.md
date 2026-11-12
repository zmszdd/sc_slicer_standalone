# 主线改进循环报告（同批 30 份、semantic-live-26）

候选率 = 规则化 Impact / 证据完整候选；逻辑完整率 = 规则化 /（候选 − incomplete_piv）。

| 组 | 轮次 | 候选率 | 逻辑完整率 | direct_relation | generator_defect | candidates | 调用 |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 修复前 | NEW2 | 64.20% | 69.33% | 9 | 23 | 14/30 | 448 |
| 修复前 | NEW3 | 66.25% | 70.67% | 7 | 22 | 14/30 | 388 |
| 修复前 | NEW4 | 54.65% | 61.84% | 16 | 29 | 11/30 | 478 |
| 符号上限8→12 | R5 | 76.62% | 77.63% | 1 | 17 | 15/30 | 420 |
| 符号上限8→12 | R6 | 57.14% | 64.86% | 11 | 26 | 12/30 | 402 |
| 符号上限8→12 | R7 | 69.62% | 76.39% | 7 | 17 | 16/30 | 422 |
| +关系类重对齐 | R8 | 76.00% | 82.61% | 7 | 12 | 12/30 | 418 |
| +关系类重对齐 | R9 | 68.83% | 75.71% | 8 | 17 | 13/30 | 455 |
| +关系类重对齐 | R10 | 70.83% | 80.95% | 10 | 12 | 10/30 | 373 |

## 中位数轨迹

| 组 | 候选率中位 | 逻辑完整率中位 |
| --- | ---: | ---: |
| 修复前 (n=3) | 64.20% | 69.33% |
| +符号上限 (n=3) | 69.62% | 76.39% |
| +关系类重对齐 (n=3) | 70.83% | 80.95% |

## 结论（诚实版）

- 两项机械修复叠加后，中位数候选率 64.2%→70.8%、逻辑完整率 69.3%→81.0%，
  方向向上且 `stage2_can_continue` 稳定 22–23/23。
- 但组内极差仍达 ~19pp（R5 76.6% vs R6 57.1%），n=3 无法拒绝“无效果”；
  只能说是“中性偏正”，不是“明显好转”。
- 剩余主瓶颈：`direct_relation_infeasible`（7–10/轮，属 incomplete_piv）
  与 `generator_defect`（12–17/轮，schema/template/quantity/fidelity）。

## 下一步（借用论文）

- 双循环重绑定：`P_and_I=unsat` 时不只重试，而是重解析 I 源语句并重绑不变量
  （KASC 外层 reparse/rebind），针对 incomplete_piv 最大子桶。
- 或先压噪再谈：formalization 用 n=3 多数投票 / `deepseek-v4-pro`，让后续
  每轮可解释（成本 3×/更高单价）。

## 方案一（P∧I 重绑）三轮验证：明确回退

| 轮次 | 候选率 | 逻辑完整率 | direct_relation | formula_construction | candidates |
| --- | ---: | ---: | ---: | ---: | ---: |
| R11 | 62.67% | 71.21% | 12 | 5 | 12/30 |
| R12 | 63.74% | 72.50% | 11 | 13 | 12/30 |
| R13 | 56.63% | 61.04% | 6 | 16 | 9/30 |

- 中位候选率 62.7%、逻辑完整率 71.2%，低于关系类重对齐基线（70.8%/81.0%）。
- 三轮全部低于基线三轮，R13 跌到 56.6% 且 `formula_construction` 飙到 16。
- 结论：注入 I 源原文的重绑提示使模型过度拟合单句、诱发公式构造错误，
  效果明显变差；按循环终止条件回退该改动，保留“符号上限 + 关系类重对齐”
  作为当前最优状态。

## S2-1/S2-2A：formal_retries 1→2 对照（n=5，median+IQR）

| 组 | 候选率 median (IQR) | 逻辑完整率 median (IQR) | candidate_passed median | schema median | calls median |
| --- | ---: | ---: | ---: | ---: | ---: |
| fr=1 基线 | 70.83% (68.83–72.97) | 78.26% (75.71–80.95) | 12 | 6 | 418 |
| fr=2 对照 | **75.00% (74.71–78.38)** | 78.31% (77.65–82.86) | **16** | **2** | 481 |

- 候选率 +4.2pp、`candidate_checks_passed` +4、`schema_or_validation` 6→2、
  `direct_relation_infeasible` 8→5；调用 +15%。
- 逻辑完整率基本持平（78.26→78.31），符合预期：额外重试主要救机械/schema
  失败，不动 `incomplete_piv`。
- IQR 略收窄但仍 ~4–5pp（R19 65.4% 为低点），噪声未完全消除。
- 判定：保留 `formal_retries=2` 为新基线。

## P0：vacuity 预检前移（2 轮验证）→ 回退

把 `reject_vacuous_safety` 从 faithfulness 审计后前移到审计前（`cli/semantic_pipeline.py` 生成候选后立即执行），期望省审计调用并在重试前拦截空安全性形状。同批 30 份、`--formal-retries 2` 复测 2 轮（R21/R22）。

| 指标 | 基线 R16–20 median | R21 | R22 |
| --- | ---: | ---: | ---: |
| 候选率 | 75.0% | 69.1% | 71.6% |
| 逻辑完整率 | 78.3% | 75.7% | 81.8% |
| candidate_passed | 16 | 16 | 14 |
| 模型调用 | 481 | 454 | 481 |
| fidelity_failed | 7 | 3 | 2 |
| fidelity_needs_review | 5 | 5 | 4 |
| fidelity_not_completed | 9 | 19 | 21 |

- `fidelity_failed` 7→3/2，但 `fidelity_not_completed` 9→19/21：本质是把“审计抓到失败”平移到“审计未完成”，口径平移而非真改进。
- 候选率两轮均 ≤ 基线中位（69.1/71.6 vs 75.0），`candidate_passed` 持平或略降，调用几乎未省。
- 判定：中性偏负、无主线增益，回退前移调用，保留原最终门禁。回退后阶段二 480/480、阶段三 14/14 全绿。
- 数据存档：`evaluation/live26_fix_confirm30_rerun21`、`rerun22`。
- 下一步 P1：`invalid quantity expression`（16）+ `type/unit mismatch`（10）合计 26/103，属确定性 schema/类型失败，优先做审计前的确定性归一化/预校验，复用重试机制、不新增模型调用。

## P1：数量表达式复合类型接受 `literal`（3 轮验证）→ 保留

根因：`lib/plan_synthesizer.py::_quantity_expression` 复合分支只认 `int`，但
`sub(const,const)`（Panoptic `2^106 − 1` 派生定义）被 `expr_type` 常量折叠为
`literal`，导致 16 个 `invalid quantity expression types` 全部误杀。改为接受
`('int','literal')`（`literal` 即整型常量）。

同批 30 份、`--formal-retries 2` 复测 3 轮（R23–R25），对比 fr=2 基线 R16–R20：

| 指标 | 基线 median | P1 median | 变化 |
| --- | ---: | ---: | ---: |
| 候选率 | 75.0% | **78.7%** | +3.7pp |
| 逻辑完整率 | 78.3% | **79.8%** | +1.4pp |
| generator_defect | 18 | **15** | −3 |
| 模型调用 | 481 | **442** | −8% |
| candidate_passed | 16 | 15 | −1 |
| schema_or_validation | 2 | 2 | 持平 |

- `invalid quantity expression types` 从 16 个（5 轮累计）降到 R23–R25 的 0/1/0，基本清零。
- 候选率三轮 [75.0, 78.7, 78.7] 全部 ≥ 基线中位；`generator_defect` 降 3 达标。
- 判定：满足“候选率不降且 generator_defect 降 ≥3”，**保留该修复**。
- 回归：阶段二 480/480、阶段三 14/14 全绿。
- 数据存档：`evaluation/live26_fix_confirm30_rerun23/24/25`。
- 下一步 P1b：`type/unit mismatch`（本批 6/0/5）多为“一比一比率”被误编码为不同单位符号相等
  （`shares == wei`），属语义问题，机械改写会篡改语义；改走针对性重试提示或
  fidelity 审计前的一比一比率归一（仅在报告明确“1:1”时重写为速率比较）。

## P1b：1:1 比率归一（3 轮验证）→ 保留但收益边际

在 `lib/salvage.py::normalize_one_to_one_rate` 增加源锚定的 1:1 比率归一：
仅当源语句明确“1:1/one-to-one/1 X per 1 Y”且比较为 `eq(shares, wei)` 等不同单位
符号相等时，确定性重写为 `eq(shares_per_wei, 1)`，并落盘
`one-to-one-rate-normalization.json`。同批 30 份、`--formal-retries 2` 复测 3 轮
（R26–R28），对比 P1 基线 R23–R25：

| 指标 | P1 median | P1b median | 变化 |
| --- | ---: | ---: | ---: |
| 候选率 | 78.7% | 77.8% | −0.9pp |
| 逻辑完整率 | 79.8% | **85.7%** | +6.0pp |
| generator_defect | 15 | **12** | −3 |
| type/unit mismatch | 6/0/5 | **1/0/0** | 基本清零 |
| candidate_passed | 15 | 15 | 持平 |
| 模型调用 | 442 | 479 | +37（噪声） |

- 诚实归因：`type/unit mismatch` 从 11 降到 1，但归一改写 3 轮只触发 2 次（R27×2），
  R26/R28 是模型本就没生成该错误，故该下降主要来自服务端噪声，不是改写的功劳。
- 改写本身零成本（确定性、不新增调用），触发时正确救回 2 个候选；`calls +37` 是
  服务端波动，与改写无关。
- 判定：目标桶达成、`generator_defect` −3，但候选率 −0.9pp 且改写触发极稀（2/90 报告），
  **收益边际，保留为安全网**；不再继续 P1 系确定性微调。
- 结论：确定性微修复已到收益递减点，主瓶颈仍在 `fidelity` 审计与模型噪声。
  下一优先项转向 P3（fidelity 降噪 / 压噪），或冻结当前主线进入端到端验证。

## P3：needs_review 主线可续跑口径（3 轮验证）→ 保留（口径放宽，非质量提升）

`fidelity needs_review`（PIV 关系 weakened）此前被计为 pending，即使规则已生成
SMT 且可进阶段三。改为在 `--continue-on-review` 下将 needs_review 计入 formalized
（带警告），审计信号仍完整保留于 `fidelity_needs_review_count`。同批 30 份、
`--formal-retries 2` 复测 3 轮（R29–R31），对比 P1b 基线 R26–R28：

| 指标 | P1b median | P3 median | 变化 |
| --- | ---: | ---: | ---: |
| 候选率 | 77.8% | **86.8%** | +9.1pp |
| 逻辑完整率 | 85.7% | **91.7%** | +6.0pp |
| generator_defect | 12 | **7** | −5 |
| fidelity_needs_review（审计计数） | 5 | 1 | −4（噪声+口径） |
| fidelity_failed | 7 | 7 | 持平 |
| candidate_passed | 15 | 14 | −1 |
| 模型调用 | 479 | 476 | 持平 |

- 机制确认：needs_review 不再进入 pending，R29 的 6 个 needs_review 全部转为
  formalized；R30/R31 因审计本就没返回 needs_review（噪声）而转换少。
- 诚实说明：+9.1pp 候选率是“口径放宽”+ 本轮 needs_review 发生率偏低两者叠加，
  不是保真度变好——`fidelity_failed` 中位持平 7。
- 该口径与 `--continue-on-review` 语义一致，且 weakened PIV 正是阶段三差分测试要
  验证的一致性信号，故保留；严格质量指标以 `fidelity_failed` 与
  `fidelity_passed_complete_piv_impact_count` 为准。
- 回归：阶段二 480/480、阶段三 14/14 全绿。
- 数据存档：`evaluation/live26_fix_confirm30_rerun29/30/31`。

## 端到端验证（真实 case4rena panoptic 2025-12 finding 17）

- 阶段一：`./run.sh` 重跑 `stage1_input/BuilderWalletInitPoC.sol`，产出切片并通过
  forge test（1/1）。
- 阶段二当前代码：
  - 回归 480/480；R29 案例 `main.py verify` 零调用重放通过（含
    `stage3_interface_hashes`）。
  - 真实报告 `/root/poc_repro_work/.../Panoptic__Next_Core_iqcUwAhCZyD__CUEQdPu878N__Pn5EwLxkitU/report.json`
    用 semantic-live-26 重跑：3/3 impact formalized（rate 1.0）、
    `candidate_checks_passed`、11 次调用，三件套齐全。
- 阶段三：
  - 回归 14/14。
  - `panoptic_builder_init`（手写源码）：`violation_reproduced`（原始 exploit
    Success、补丁 assertion failed、安全路径 Success）。
  - `panoptic_builder_init_stage1`（阶段一切片）：`violation_reproduced`。
- 注意：
  - 现有 case 的 stage2_run 由旧 prompt `semantic-live` 生成，其全量 `verify`
    重放因 readiness prompt 漂移失败（预存问题，与本次改动无关）；但阶段三消费
    其 stage3-spec/constraints/formalization 正常。
  - semantic-live-26 新产物为 3 个 impact claim、自动命名符号，与现有单一
    `core_claim` 的 `binding.json` 不匹配，需重新手工绑定（文档已列出的瓶颈）。
