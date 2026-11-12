# 准确率 / 召回率主线研究方案

更新时间：2026-11-04
目标：围绕主线（阶段一 flatten → 阶段二 PIV → 阶段三 绑定+差分+裁决）提升
一致性检测的准确率与召回率，重点是阶段二提取质量与阶段三复现能力。

## 1. 指标定义

- 阶段二召回率（提取覆盖）：`impact_formalization_rate`（规则化 impact / 证据完整 impact）
  与 `report_level.complete`（完整报告占比）。当前 goldset_v2_pos91(88)：78.4% / 51.1%。
- 阶段二准确率（忠实度）：P/I/V 六维评级 `faithful` 占比。当前 ~70%（无 unfaithful 口径）。
- 阶段三端到端召回率（主线）：正样本 `violation_reproduced` 的 claim 级占比。
  当前真实 50 案例：0%（claim 8.47% / 案例 20% 为旧口径）。

## 2. 缺陷清单

### 阶段二（准确率/召回率主战场）
- 召回类：
  - `zero_output`：88 案例中 20 例零输出（22.7%），整份报告无候选。
  - `direct_relation_infeasible`：关系类无法形式化（30 案例口径 7-10/轮）。
  - `generator_defect`：schema/template/quantity/fidelity 确定性失败（12-17/轮）。
  - 候选率方差大（57%-77%），模型不稳定。
- 准确类：
  - I 维度 unfaithful（集中在 required_property）。
  - `weakened` 大量出现（单主张压缩，设计取舍但影响严格口径）。
  - vacuous safety（I 空洞为真）；formula I 循环编码。

### 阶段三（主线端到端）
- 真实正样本复现率 0%（50 案例）。
- 单合约注入天花板 6.8%（P1.7 实测：177 claim 中仅 12 个 single-contract）。
- 跨合约函数引用 → `compile_error`（lint 只查状态变量、不查函数）。
- `ambiguous` 锚点 25.4%（通用符号名匹配多合约）。
- 退化绑定 `true`/`false` 未拦截。
- `partial_binding` 高占比（旧 50 案例 58.8%）。

### 三阶段配合
- 阶段二只证明公式内部一致，不产出「代码可绑定性」标记。
- 缺阶段二→阶段三的 bindability 反馈通道。

## 3. 执行顺序（先低成本高杠杆）

1. P2.0 阶段二 zero_output 归因：20/88 零输出逐例归因（输入筛查/关系不可行/
   模型失败），针对最大桶做确定性修复。→ 直接提召回。
2. P2.1 generator_defect 确定性修复：延续 P1 风格（schema/type 归一化）。→ 提召回。
3. P1.9 可绑定性反馈通道：阶段二产出 bindability 标记，把 ambiguous 在阶段二
   就筛掉/细化。→ 同时提准确率（减少错绑）与召回率（阶段二知道要细化）。
4. P1.8 注入点迁移：解耦 patch/probe，允许跨合约函数引用，把 6.8% 天花板做实。→ 提端到端召回。
5. P2.2 忠实度 I 维度与 vacuity：针对 required_property 失真与空安全性做审计前
   确定性门。→ 提准确率。

## 4. 判定标准

- 召回：`impact_formalization_rate`、`report_level.complete`、claim 级复现率上升。
- 准确：六维 `faithful` 占比上升、`unfaithful` 下降。
- 只有主线指标（复现/忠实）上升才算有效；只降 partial/compile 不算。

## 5. 执行记录（2026-11-04）

### P2.0 zero_output 归因（已完成）
- 20/88 零输出案例归因：
  - `needs_impact_review`（0 impact）：9 例（45%），根因是 `impact_inventory_status:
    no_marked_impact_section`——报告没有显式 `Impact` 标题，impact 写在
    `Summary`/`Description` 里，确定性 `explicit_impact_ranges` 因此返回空。
  - `needs_review`（有 impact 但 0 规则化）：11 例，主因 `direct_relation_infeasible`
    （7 例）与 `formula_construction`/`schema_or_validation`（各 4-5 例）。

### P2.0 修复（已实现，待盲测验证）
- `lib/ingest.py`：`explicit_impact_ranges` 新增回退——仅当报告完全没有任何显式
  `Impact` 区时，才把 `Summary`/`Description`/`Detailed Description`/
  `Vulnerability Details` 当作 impact 证据区；`Root Cause` 刻意排除（纯机制，
  纳入会污染 impact 证据、伤忠实度）。有显式 Impact 区的报告保持原严格边界。
- 效果：5 个 `no_marked_impact_section` 案例中 3 个恢复 impact 范围
  （Ekubo/Merkl/SukukFi）；Olas/Panoptic 无任何标题，仍需单独的 prose 推断
  （fidelity 风险，另行立项）。
- 验证：既有 6 组 impact 格式测试全部通过；新增 4 个回退测试通过。
- 注意：阶段二全量回归当前因 `results/report_only/brix_fee_assistant_final/
  extraction-input.txt` 等 fixture 被 git 删除而报 13 个 ImportError（先于本次
  改动已存在），需先恢复 fixture 或确认删除决策后才能跑全量。

### 下一步（待执行）
- 盲测 P2.0 修复：同批 30 份，对比修复前后 `impact_formalization_rate` 与
  `fidelity_failed`，确认「召回升、忠实度不降」才保留。
- P2.1：`direct_relation_infeasible` 归因与确定性修复（7/11 零输出、7-10/轮）。

### P2.0 盲测验证（2026-11-04 已完成）
- 目标 5 例（此前 `no_marked_impact_section`）：
  - SukukFi：0 → `candidate_checks_passed`，2/2 impact 规则化，rate 1.0。
  - Ekubo：0 → 3 impact 提取（1 规则化，2 direct_relation_infeasible）。
  - Merkl：0 → 1 impact 提取（0 规则化，1 generator_defect）。
  - Olas / Panoptic：仍 0（报告无任何标题，需 prose 推断，另行立项）。
- 对照 3 例（此前有显式 Impact 区）：
  - 均 `impact_source_status: marked_section_present`，回退逻辑未触发；
    Brix 3/3 完整、Covenant/Ekubo 波动属模型噪声，非本修复引入。
- 结论：召回提升（3/5 零输出恢复 impact），忠实度边界保持（显式 Impact 区不受影响）。
- 回归：阶段二 484/484 通过（恢复被删的 results fixture 后）。
- 判定：P2.0 修复保留。

### 下一步
- P2.1：`direct_relation_infeasible` 归因（本轮 Ekubo 2 例、此前 7/20 零输出主因）。
- Olas/Panoptic 类「无标题报告」的 prose 推断（fidelity 风险，需谨慎立项）。

## 6. 阶段三主线完整方案（针对复现率 0 的问题）

### 问题定级
- 真实正样本复现率 0；单合约注入天花板 6.8%；60.5% claim 被 ambiguous 锚点卡住。
- 新发现语义天花板：阶段三自动 `assert(I)` 只能验证「代码已计算的可观察状态
  不变量」（如 panoptic 访问控制），无法验证 should-be 语义（如 Intuition
  「窗口应签进 hash」——代码根本不计算该值）。should-be 类必须走 M1 参考补丁。

### 执行顺序
1. P1.8a 解耦 patch/probe（已完成）：probe 锚定 PoC，patch 允许指向业务合约。
2. P1.8b 确定性注入点迁移：用 `function_owner`/`state_var_owner` + 完整表达式
   扫描（含嵌套调用）把 patch 迁到持有符号的合约；歧义时用继承闭包消解。
3. P1.8c 可观测性分类路由：每个 claim 分类为
   - `observable_assertable`：自动 assert 可覆盖（保留现有路径）；
   - `should_be_reference`：需 M1 参考补丁，自动路径跳过并标注。
4. P1.9 阶段二可绑定性反馈：阶段二产出 bindability 标记，阶段三据此路由。
5. 评测：按 `violation_reproduced` 的 claim/案例级复现率判定，对照修复前 0。

### 本轮已完成
- P1.8a 解耦 + prompt 更新 + 归属查询辅助（function_owner/state_var_owner）。
- 回归：阶段三 65 项全绿。
- 发现：Intuition 为 should-be 语义，自动 assert 无法复现，需参考补丁路径。

### P1.9 确定性锚点解析 + 可绑定性通道（2026-11-04 已完成）
- 根因：阶段二只读报告不读代码，符号是报告语义抽象；阶段三把「抽象符号→
  代码锚点+注入合约」的映射交给 LLM 自由猜测，是 ambiguous(25.4%)/
  cross-contract/unbound 三类失败（端到端复现率 0%）的共同根因。
- 实现：`tools/stage3/lib/anchor_resolver.py` 确定性解析（候选→仅函数/状态变量
  → `function_owner`/`state_var_owner` 归属→`single_anchor/multi_contract/
  file_level/no_anchor`+`suggested_patch_contract`）；接入
  `binding_llm.propose_binding`（SUGGESTED_PATCH_CONTRACT 约束）与
  `stage3_eval_run`（bindability 分布统计）。
- 实测：panoptic→single_anchor(BuilderWallet)，Intuition→multi_contract；
  阶段三 74/74 全绿。
- 下一步：`multi_contract` 走 M1 参考补丁；`single_anchor` 把
  `suggested_patch_contract` 用作确定性 patch 迁移目标。
