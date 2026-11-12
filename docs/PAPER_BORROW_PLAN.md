# KASC 论文借鉴落地计划（主线，阶段一不动）

更新时间：2026-10-31
范围：只改阶段二（`tools/report_constraints_v2/`）与阶段三（`tools/stage3/`），
阶段一（`src/`、`run.sh`）完全不动。

## 定位

KASC 做"报告 → 正向 exploit 生成"，本项做"报告不变量 → 原始/补丁差分一致性
验证"。借鉴其 oracle 纪律、失败分级与双层闭环，但判据保持差分方向。

## 四个落地阶段

| 阶段 | 借鉴点 | 改动 | 状态 |
| --- | --- | --- | --- |
| A | missing evidence 一等化 | 两处 impact-inventory 崩溃降级为 `needs_impact_review` | 完成 |
| B | oracle `require(φ)` / 验证目标行为 | `P_and_T_and_not_I` 成为裁决主判据 | 完成 |
| C | 双层循环外层 | 非复现裁决附带 `replan_diagnostic` + `stage3 replan` 入口 | 完成 |
| D | 同协议回归 + 判定分布 | 负样本案例 + 批量判定分布 + 配对复测 | 部分完成 |

## Phase A（完成）

- `cli/semantic_pipeline.py` 新增 `_degrade_impact_inventory()`：把
  `impact_inventory_verbatim` 与 `impact_inventory_duplicate_id` 两类确定性
  缺陷降级为空 inventory + 三要素诊断（expected/observed/violated_gate），
  不再顶层 `rejected`。
- 复测两个原崩溃案例：均变为 `acceptance_status=needs_impact_review`，
  并落盘 `impact-inventory-failure.json`。

## Phase B（完成）

- `lib/stage3_consistency.py::consistency_verdict` 改为：
  `P_and_T_and_not_I == sat` 主判 `violation_reproduced`；
  `P_and_T_and_not_I == unsat` 且 `P_and_T_and_V == sat` 判
  `effect_observed_invariant_holds`（结果不一致）；
  V 仅在 not_I 未知时作佐证。
- 阶段二裁决测试 +3，阶段三差分测试不变，全部通过。

## Phase C（完成）

- `ingest_feedback` 落盘时附带 `replan_diagnostic`，按裁决给出
  `accept / replan_rule / rebind / rebind_or_restate_i /
  collect_missing_evidence` 五类下一动作。
- 新入口 `python main.py stage3 replan --consistency <stage3-consistency.json>`。

## Phase D（部分完成，剩余见下）

- 新增负样本案例 `tools/stage3/cases/smoke_vault_fixed_src`：
  源码已满足不变量，预期 `violation_not_reproduced`，已跑通并回填诊断。
- 批量 6 案例：`violation_reproduced` x5、`violation_not_reproduced` x1。
- 完成：
  1. 同盐 30 份配对复测（`evaluation/live26_fix_confirm30_rerun/`）：
     `rejected` 崩溃 2 → 0；规则化率 63.0% → 56.1% 属模型非确定性波动。
  2. 绑定错误样本 `tools/stage3/cases/smoke_vault_bad_binding`：
     `preconditions_infeasible_on_code`，已跑通。
  3. 内置案例批量 7/7，判定分布 {reproduced:5, not_reproduced:1,
     preconditions_infeasible:1}。
- 剩余：真实负样本 5-10 个（需逐个人工绑定的真实 Code4rena finding）。

## direct_relation_infeasible 归因修复（本轮新增）

- 根因：`direct_relation_infeasible` 的主导形态是 `P_and_V=unsat` +
  `P_and_V_and_not_I=unsat`，即合成出的 V 自相矛盾。
- 具体机制：当 `impact_outcome` 与 `pattern.condition` 用同一个布尔符号、
  取值相反时（如 condition=`underflow_occurred=false`、
  outcome=`underflow_occurred=true`），`direct_witness_effects` 把两者都
  conjoin 进 V，产生 `x AND NOT x`。
- 修复：
  - `lib/plan_synthesizer.py` 新增 `_negated_condition_outcome_symbol`，
    在 `reject_vacuous_safety` 中具名该形态。
  - `cli/semantic_pipeline.py` 新增定向重试提示，引导模型把 outcome 改为
    报告陈述的具体可观测效果、把 condition 改为真正的适用性条件。
- 验证：新增 2 个单元测试；阶段二 480/480。
- 注意：单案例复跑未稳定复现同一失败（模型非确定性），故指标级确认需
  同盐多次配对复测，不能靠单轮读数判断。

## 回归结果

- 阶段二：478/478。
- 阶段三：14/14。
- 内置案例批量：6/6 ok，判定分布 {reproduced:5, not_reproduced:1}。

## 验收口径（修正）

Phase A 的验收不是"全部 exit 0"，而是"不再出现 `rejected` 崩溃"：
`needs_impact_review` 属严格退出（exit 2）但为干净降级，属预期。

## 五轮同盐配对复测（最新结论）

同一 30 份报告、同 prompt/参数（`temperature=0`），`direct_relation` 修复前
OLD/NEW1 与修复后 NEW2/NEW3/NEW4 对比：

| 轮次 | direct_relation_infeasible | 规则化率 | candidate_passed | 调用数 |
| --- | ---: | ---: | ---: | ---: |
| OLD(修复前) | 14 | 63.0% | 11/30 | 425 |
| NEW1(修复前) | 14 | 56.1% | 11/30 | 451 |
| NEW2(修复后) | 9 | 64.2% | 14/30 | 448 |
| NEW3(修复后) | 7 | 66.2% | 14/30 | 388 |
| NEW4(修复后) | 16 | 54.7% | 11/30 | 478 |

结论：`direct_relation` 修复在 2/3 修复后轮更低，但 NEW4=16 高于任一修复前轮，
无法拒绝“修复无效果”；规则化率五轮极差约 12pp，属采样噪声，不能宣称改善。
Phase A 的 `rejected=0` 稳定有效。完整报告见
`tools/report_constraints_v2/evaluation/PAIRED_RETEST_5ROUND.md`。

下一步：先修测量协议（每条件 ≥3 轮报 median+IQR，formalization 改
`deepseek-v4-pro` 或 n=3 多数投票），再处理 `schema_or_validation` 与
`formula_construction`，停止读单轮差值做结论。

## 分母口径修正 + 双分母（本轮新增）

- 新增 `cli.semantic_pipeline.piv_failure_bucket`：把 eligible-but-unformalized
  二分 `incomplete_piv`（P∧I/P∧V unsat、自等/自矛盾）与 `generator_defect`
  （schema/unit/symbol/template/fidelity，以及 negated-condition-symbol）。
- `stage2_assessment` 与 `status.json` 新增 `incomplete_piv_count`、
  `generator_defect_count`、`logically_complete_denominator`、
  `logically_complete_formalization_rate`。
- 回算五轮：逻辑完整率 61.8%–75.0%，`generator_defect` 每轮 17–29 是剩余主瓶颈。
  报告：`tools/report_constraints_v2/evaluation/DOUBLE_DENOMINATOR_REPORT.md`。
- 回算工具：`evaluation/compute_double_denominator.py`（零新增模型调用）。

## 机械修复：符号上限 8→12

- `lib/semantic_core.py:442` `MAX_PLAN_SYMBOLS` 8→12；`lib/plan_synthesizer.py`
  与错误消息同步；`prompts/current.py:816` formal prompt “at most 8 symbols”→12。
- 目的：模型已常输出 9 个符号，8 上限导致的机械拒绝改为放行到语义闸门。
- 阶段二回归 480/480。
- 未做：`expanded relation template mismatch` 与 `type/unit mismatch` 已存在
  定向重试提示，剩余失败属模型一次重试修不好，需强模型/多轮投票（第5步）或
  多轮重试验证，不做无依据的自动改写。

## 符号上限修复的三轮验证（rerun5/6/7）

同批 30 份、`semantic-live-26`（prompt 8→12 symbols + `MAX_PLAN_SYMBOLS=12`）：

| 轮次 | 候选率 | 逻辑完整率 | direct_relation | candidates | 调用 |
| --- | ---: | ---: | ---: | ---: | ---: |
| R5 | 76.62% | 77.63% | 1 | 15/30 | 420 |
| R6 | 57.14% | 64.86% | 11 | 12/30 | 402 |
| R7 | 69.62% | 76.39% | 7 | 16/30 | 422 |

结论：中位数候选率 69.6%（修复前 64.2%）、逻辑完整率 76.4%（修复前 69.3%），
但 R6 回落到修复前区间，n=3 无法拒绝“无效果”；仍是中性偏正，不能宣称显著。
`stage2_can_continue` 三轮 23/23、23/24、23/23 稳定。

## 下一改进：扩展关系类确定性重对齐（本轮新增，未验证）

- `lib/plan_synthesizer.py` 新增 `realign_expanded_relation_class`：当
  `pattern.kind` 唯一对应另一个 `relation_class` 时，自动把 label 翻转到匹配
  pattern（KASC “策略失效→重绑定”的零调用版本）。
- 歧义 kind（relation_obligation/bounded_relation/required_effect 对应多类）保持不动。
- `cli/semantic_pipeline.py` 在合成前应用并落盘 `expanded-relation-realignment.json`。
- 回归 480/480；待 rerun8/9/10 三轮验证。

## 关系类重对齐三轮验证（rerun8/9/10）

| 轮次 | 候选率 | 逻辑完整率 | direct_relation | schema | formula |
| --- | ---: | ---: | ---: | ---: | ---: |
| R8 | 76.00% | 82.61% | 7 | 3 | 1 |
| R9 | 68.83% | 75.71% | 8 | 6 | 9 |
| R10 | 70.83% | 80.95% | 10 | 4 | 2 |

中位数：候选率 70.8%、逻辑完整率 81.0%；较“仅符号上限”的 69.6%/76.4%、
修复前的 64.2%/69.3% 继续小幅向上，但仍受单轮噪声制约（n=3，组内极差 ~19pp）。
完整十轮轨迹：`tools/report_constraints_v2/evaluation/MAINLINE_LOOP_REPORT.md`。

## 循环状态

- 已落地并验证：符号上限 8→12、关系类确定性重对齐；均中性偏正，未出现明显回退。
- 下一步二选一（借用论文）：
  1. 双循环重绑定：`P_and_I=unsat` 触发 I 源重解析/重绑（针对 incomplete_piv）。
  2. 先压噪：formalization n=3 多数投票或 `deepseek-v4-pro`（成本 3×/更高单价）。

## 方案一（P∧I 重绑）试验结果：回退

- 实现：`P_and_I=unsat` 时在重试反馈注入 I/P 源原文，要求重编码 I。
- 验证 rerun11/12/13：中位候选率 62.7%（基线 70.8%）、逻辑完整率 71.2%
  （基线 81.0%），三轮全部低于基线，R13 公式构造错误 16。
- 判定：明显变差，已回退；保留“符号上限8→12 + 关系类确定性重对齐”为当前最优。
- 教训：向小模型注入 I 源原文会诱导向单句过度拟合；后续若做重绑需改为
  “只给结构化 I 候选 + 明确禁止改写其他字段”，或换强模型再做。

## S2-1/S2-2A 执行中（基线 n=5 + formal_retries=2 对照）

- 基线（符号上限+关系类重对齐，formal_retries=1）：R8/R9/R10 已有 3 轮，补
  R14/R15 到 n=5。
- 对照（formal_retries=2）：R16–R20 共 5 轮。
- 指标：候选率、逻辑完整率、direct_relation_infeasible、generator_defect、
  model_calls 的 median+IQR；判定 formal_retries 1→2 是否把 IQR 压到可解释。

## S2-2A 结论：formal_retries 2 为新基线

- CLI 放开 `--formal-retries {0,1,2}`（`cli/batch_verify.py`、
  `cli/semantic_pipeline.py`）。
- n=5 对照：候选率 70.8%→75.0%、candidate_passed 12→16、schema 6→2、
  direct_relation 8→5；逻辑完整率持平 78.3%；调用 +15%。
- 结论：保留 fr=2；噪声 IQR 仍 ~4–5pp，后续 S2-3 在稳定读数上修
  `formula_construction`（数量/单位）机械失败。
