# SC_Slicer 阶段二工作交接

更新时间：2026-10-20

项目目录：`/root/sc_slicer_standalone`  
当前工作范围：`tools/report_constraints_v2/`  
目标接手环境：DeepSeek V4 for Copilot Chat 新对话

> **当前状态入口**：先读
> [`STAGE2_CURRENT_STATUS.md`](tools/report_constraints_v2/docs/STAGE2_CURRENT_STATUS.md)。
> 本交接文件保留了历史实施细节；其中旧版本号、测试计数和计划不得覆盖当前状态文档。
> 当前工作树含未提交 S19 变更，开始操作前先看 `git status` 和对应 diff。

## 1. 当前正在做什么

阶段二当前唯一主线是把报告声称的安全性质转成**可追溯、可审计、可重放并可交给阶段三的规格**。阶段二不判断报告真假，也不证明 PoC 与报告一致。完成定义、现状和有限收口任务以 `STAGE2_CURRENT_STATUS.md` 为准。

下列项目背景与 P/I/V 定义仍有效：

项目总目标是判断智能合约漏洞报告中的 PoC 是否与报告声称的漏洞效果一致：

1. 阶段一对 PoC/合约代码切片，提取与目标效果相关的执行路径；
2. **阶段二从漏洞报告自然语言推导报告声称的性质，并将其规则化；**
3. 阶段三把阶段一的代码行为与阶段二的形式化性质绑定，通过符号执行检查一致性。

目前只处理阶段二。阶段二的两个直接目标是：

- 从报告描述和影响中提取：
  - `P`：漏洞成立前的场景前提；
  - `I`：报告声称在 P 下应满足的安全性质；
  - `V`：报告声称实际发生、且直接否定 I 的坏效果。
- 把 P/I/V 转换成有证据来源、变量类型、单位和作用域的 AST、SMT 与
  `stage3-spec.json`，供后续阶段消费。

阶段二不负责执行 PoC，也不负责最终判断报告真假。`src/llm_completion.rs`、Rust slicer、
`run.sh` 和阶段一切片逻辑不在当前修改范围内。

## 2. 当前阶段二工作流

```text
report.json
  ↓
提取前信息充分性筛选
  ├─ 缺少受影响对象、触发/行为、直接效果或安全关系依据
  │    → excluded_before_extraction / needs_input_review，停止
  └─ 信息充分
       ↓
标题、描述、影响片段编号
       ↓
DeepSeek 提取实体、P、动作、根因、I、V
       ↓
程序检查证据编号、角色、模态和 schema
       ↓
DeepSeek 选择关系类别、观测变量和形式计划
       ↓
程序按固定模板确定性合成 P/I/V AST
       ↓
来源、类型、单位、数值、地址、影响限定检查
       ├─ 可修复局部错误 → 最多两次受限修复
       └─ 关键错误 → 拒绝并保存原始响应
       ↓
SMT + Z3 查询
       ↓
constraints.json / status.json / stage3-spec.json
```

逻辑门主要检查：

- `P ∧ V` 是否可满足；
- `P ∧ V ∧ I` 是否不可满足，即 V 是否直接违反 I；
- 证据编号、来源、变量、单位和模板是否一致。

这些检查只证明**生成公式内部一致**，不证明模型忠于原报告，更不证明 PoC 与报告一致。

## 3. 已经完成的工作

### 3.1 基础链路

- 阶段二输入已统一为 `report.json` 的标题、漏洞描述和影响片段。
- 代码、PoC、修复 diff 不作为当前 P/I/V 提取输入；`metadata.json` 只用于身份核对。
- 程序先给原文片段编号，模型只返回证据 ID，程序再取回原文。
- 未知证据 ID、错误来源角色和非法 schema 会被拒绝。
- 已能生成 P/I/V AST、SMT、Z3 查询、状态文件及阶段三接口文件。
- 每次模型响应、重试、Token、错误和原始输出都会保留，支持离线审计。

### 3.2 提取前筛选

- 已把筛选放到 P/I/V 提取之前。
- 信息明确不足的报告不再进入后续流程，避免浪费调用和制造低质量公式。
- 旧的“生成后自动筛选”已退出活动工作流，不要重新接回主流程。
- 本地文件/输入身份核对并入主流程的 `load_report` / `build_catalog`；
  真正的语义充分性门在主流程中。

### 3.3 神经符号规则化

- 模型负责理解报告、选择证据和提出形式计划。
- 程序负责固定模板、类型、单位、来源、结构与 Z3 检查。
- 已建立 12 类通用安全关系：
  - `access_control`
  - `value_relation`
  - `bounded_value`
  - `monotonicity`
  - `conservation`
  - `proportional_fairness`
  - `state_correspondence`
  - `temporal_validity`
  - `sequence_preservation`
  - `data_structure_integrity`
  - `progress_or_liveness`
  - `range_capacity`

### 3.4 semantic-v3.15 至 v3.20

- v3.15：加入安全关系分类、关系对齐检查和更多通用算术表达。
- v3.16：关系类别唯一映射到固定模板；加入 `derived_definitions` 和字段级局部修复。
- v3.17：使用 `report-formal-plan/5`，增加：
  - 权限、边界、比例、状态对应、时序、进度等专用模板；
  - `impact_context_terms`，保留时间、阈值和状态限定；
  - P 中每个符号必须由对应 P 来源自己支撑；
  - 不同 P 来源不能重复使用完全相同的谓词；
  - ERC/EIP/BIP 等协议编号不再被误当成数值约束；
  - 类型/单位冲突时允许有界关系类别重规划。
- v3.18：**仅提示词**的窄修复，schema 仍是 `report-formal-plan/4`。
  删除正式提示词里继承自 v3.15 的三处 legacy 形状说明
  （`condition_forbids_effect` / `condition_requires_effect`），它们与编译器固定
  模板自相矛盾 —— `FIXED_RELATION_CLASS_PATTERN` 只允许 `monotonicity` /
  `conservation` / `relation_obligation`，而其中一段明确指示模型把"合法操作本应
  完成却 revert"编码成 legacy 形状，这个场景正是 `progress_or_liveness`（固定
  模板要求它用 `relation_obligation`）。`lib/plan_synthesizer.py` 未改动；只新增
  `prompts/versions/semantic_prompts_v318.py` 与 `prompts/registry.py` 的一行注册。

- v3.19：**仅提示词**的窄修复，schema 仍是 `report-formal-plan/4`。
  修正 `access_control` 类内容规则与 grounding 规则的冲突：类规则原先说
  `relation` 就是"required authorization"，而 grounding 规则要求每个被选中的
  `impact_id` 都由出现在 `relation` 里的符号引用（condition-only 触发量明令不计）。
  授权谓词只能由 precondition 支撑，两条规则无法同时成立，而提示词从未说明优先级。
  改为 condition 承载受保护动作**加上缺失或被绕过的 guard**，`relation` 在 impact
  是后果时取其自身可观察量的**否定**。`lib/plan_synthesizer.py` 未改动。

- v3.20：**仅提示词**的窄修复，schema 仍是 `report-formal-plan/4`。给
  `sequence_domain_fork` 残留的两个真缺陷各一条可执行配方：审核第 3 条补上"值被固定／
  缓存／只读一次"事实的两种忠实形态（禁止自反比较的规则本身未动）；审核第 4 条补上
  "只有 `state_correspondence` 的等式不够，`relation` 必须同时包含带 impact 的可观察量"。
  两条配方都先在该真实样本上离线验证过能通过校验。

### 3.5 当前测试结果

v3.16 冻结留出集：

- 5/5 生成合法要素；
- 3/5 生成最终候选；
- 严格公式初评 1/3 完整正确。

v3.17 五例开发回归：

- 案例：Monetrix、Intuition、GTE Spot、GTE Perps、Olas；
- 只向 DeepSeek `deepseek-flash` 发送已保存的阶段二结构化要素；
- 未发送合约代码；
- 2/5 生成最终候选：Monetrix、Olas；
- 2/5 可带警告继续，均仍为 `needs_review`（该批 run 的 provenance 未记录策略，按 `legacy` 重放；
  `signals` 策略下同一批会变成 `candidate_checks_passed`，见 §4.9）；
- 2/2 候选通过零调用离线重放；
- 11 次调用；
- 65,925 输入 tokens、12,961 输出 tokens，共 78,886 tokens；
- 模型响应耗时合计 95.778 秒；
- 清理退役切片绑定分支后，当前主线全量本地测试 266/266 通过。

保守语义初评：

- Olas：核心 P/I/V 基本合理，但关系类别标为权限关系并不理想；
- Monetrix：部分正确，P 混入漏洞返回值，并暴露派生定义空真问题；
- Intuition：比例方向合理，但 impact 来源联动修复失败；
- GTE Spot：dust 条件方向合理，但派生定义链和来源不符合当前规则；
- GTE Perps：选中的是 LP 价值差，模型却生成单 reserve 守恒式，拒绝合理。

这是开发集缺陷定位，不是总体准确率或泛化率。

v3.18 提示词修正的对照实测（5 例 × 10 次 = 50 次调用，输入与命令和基线逐字节一致）：

- 关系类别服从固定模板：**36/50 -> 50/50**；
- `gte_fok_dust`、`intuition_pause_escrow`（均为 `progress_or_liveness`）：
  **3/10 -> 10/10**，其 `fixed relation template mismatch` 由 14 次降到 **0 次**；
- `panoptic_builder_init`（`access_control`）：校验通过 0/10 -> 7/10，grounding
  失败由 10/10 降到 3/10；
- `sequence_domain_fork`（`state_correspondence`）：仍 0/10，原因仍是 truth
  binding，与本次改动无关；
- `olas_permissionless_sweep`：仍 0/10，原因仍是 grounding；
- **没有任何新的失败类别出现**，说明问题被消除而不是转移。

这是开发集上的机制验证，不是总体准确率。

v3.19 提示词修正的对照实测（同样 5 例 × 10 次 = 50 次调用，输入与命令与基线逐字节一致）：

- 校验通过 **27/50 -> 40/50（80%）**；kind 合规保持 50/50，无回归；
- `olas_permissionless_sweep`：**0/10 -> 10/10**；
- `panoptic_builder_init`：7/10 -> **10/10**；
- `core relation observables lack intent/impact grounding`：**13 次 -> 0 次**；
- `sequence_domain_fork` 仍 0/10（truth binding，与本次改动无关）；
- **没有出现任何新的失败类别**；
- 副作用需记明：`intuition_pause_escrow` 的 `relation_class` 变为
  access_control 5 / progress_or_liveness 5。两类的 `relation` 谓词形态一致，
  且都映射到 `relation_obligation`，发出的公式相同，10/10 全部通过 ——
  **只是标签不稳定**，会影响人工评审读法，不影响产物公式。

v3.20 提示词修正的对照实测（5 例 × 10 次 = 50 次调用）：

- 校验通过 **40/50 -> 43/50（86%）**；kind 合规保持 50/50，无回归；
- `sequence_domain_fork`：**0/10 -> 3/10**（首次通过）；
- 该案例 grounding 失败 **3 -> 0**、自反比较 **6 -> 3**；
- 其余四例保持 10/10；**没有出现任何新的失败类别**；
- 残余 7 次：4 次整数当标志位、3 次自反比较 —— 均为模型能力边界。

### 3.6 阶段二工程结构整理

- Prompt 已迁到 `tools/report_constraints_v2/prompts/versions/`，统一由
  `prompts/registry.py` 注册和管理版本能力；冻结 Prompt 文本的 SHA-256 未变。
- P/I/V 规范已集中到 `prompts/definitions.py`，生产流程经 `prompts/active.py`
  显式解析最终 Prompt（`resolve_prompt_set()`，不调用模型）。
  v3.5–v3.20 冻结文件未修改。
- 自动测试已迁到 `tools/report_constraints_v2/tests/`；删除退役分支的 22 项专用测试后，当前主线 268 项通过。
- 阶段二根目录现在**没有任何 `.py`**：入口在 `cli/`，共享模块在 `lib/`。
  重构前的 14 个旧模块名（`fidelity`、`evidence_catalog`、`verify_semantic` 等）
  由 `lib/compat.py` 的 `sys.meta_path` finder 惰性解析，并保持模块同一性；
  详见 `STRUCTURE.md` 的"历史模块名兼容层"。
- 断言策略在 S12 变为可切换（`--claim-verdict legacy|signals`）。默认 `legacy`
  与重构前输出逐字节一致；`main.py run` / `batch` 自动使用 `signals`。详见 §4.9。
- 设计、状态和历史报告已迁到 `tools/report_constraints_v2/docs/`。
- `evaluation/` 和 `results/` 各有索引，明确开发集、留出集和运行产物的边界。
- 已删除与当前主线脱节的早期切片绑定/旧阶段三接口分支，包括其专用代码、
  22 项测试、Panoptic 样例和失败切片产物；删除清单见 `tools/report_constraints_v2/MIGRATION.md`。
- 旧到新路径及导入方式见 `tools/report_constraints_v2/MIGRATION.md`；文件职责见
  `tools/report_constraints_v2/STRUCTURE.md`。后续不要再把 Prompt、测试或单次报告堆到根目录。

## 4. 关键设计决策及理由

### 4.1 阶段二以报告为输入，不依赖阶段一

阶段二要恢复的是“报告声称什么”，不能让代码行为反向污染报告解释。阶段一与阶段二可
并行执行，到阶段三才通过变量、检查点和行为进行绑定。

### 4.2 使用 `report.json`，不把 `contract.flattened.t.sol` 当作提取输入

`report.json` 适合恢复标题、描述和影响；flattened 合约适合代码定位，不适合回答报告作者
声称的性质。代码可以在后续绑定时作为事实来源，但不能替代报告语义。

### 4.3 模型提出候选，程序确定性合成

让模型直接输出自由 SMT 容易产生未定义变量、极性反转、来源伪造和不可重放问题。当前让
模型选择关系和变量，程序生成 AST/SMT，从而保留自然语言理解能力并提高可审计性。

### 4.4 核心 claim 每次只选择一个直接 impact

多个下游影响经常需要不同前提、变量和逻辑关系。核心 claim 只形式化一个直接 V，其余影响
记录为 deferred/warning，避免把“局部异常”错误升级为“全部资产损失”等更强结论。

### 4.5 次要问题允许带警告继续，关键问题仍拒绝

`--continue-on-review` 只放行公式完整、V 能直接否定 I、无阻塞未决项的候选。次级影响未
覆盖、报告歧义等作为警告；未知证据、缺失变量、公式矛盾和关键限定遗漏仍拒绝。

**分档缺口已补（本次）**：上面这句原先只是**意图** —— `compile_bundle` 里没有任何
产生硬拒绝的路径，一切非干净结果都是 `needs_review`，而 `--continue-on-review` 可以
越过它。现在：

- `lib/semantic_core.py` 定义 `CONTRADICTION_CHECKS = {precondition_feasibility,
  safety_feasibility}`；任一项 `unsat` ⇒ `acceptance_status = 'rejected'`，并把命中的
  检查名写进 `contradiction_checks`；
- `lib/solving.py::attach_review` **只升不降** —— 否则评审告警会把拒绝覆写回
  `needs_review`，正是要逃出的那一档；
- `lib/solving.py::from_bundle` 把 `rejected` 路由为 `abstain`
  （`stage2_can_continue: false`），不再当作 `review`。

为什么只有这两项：`precondition_feasibility` unsat 是 P 自相矛盾（I、V 与一切查询都
无信息）；`safety_feasibility` unsat 使 V 在每个 P 模型里都为真（V 空真）。
`effects_feasibility` / `safety_negation_feasibility` unsat 描述的是**编码强度**而非
空真，且有 3 个已跟踪运行带它们 —— 升级会改写已记录的产物，故维持 review 并在此记明。

### 4.6 Z3 不承担自然语言语义判断

Z3 只判断提供给它的公式。错误公式也可能得到完美的 SAT/UNSAT 结果。因此任何文档都不能
把“Z3 通过”写成“报告语义正确”或“PoC 一致”。

### 4.7 历史版本不可原地改写

历史运行依赖 Prompt、schema、确定性合成和文件哈希重放。发现 v3.17 缺陷后必须新建冻结版本，不能静默修改 v3.17 语义，否则已有实验无法重放。

已经这样落地的三次：**v3.18、v3.19 与 v3.20 都是仅提示词的窄修复，schema 仍是 `report-formal-plan/4`**，
只删除自相矛盾/无法同时满足的提示词文字，未动验证器。仍待做的是 `report-formal-plan/6`
（`semantic_axioms` / I 空真 / 有向无环定义）那一套，顺延为 v3.21，见 §8 第二步。

**边界归一化与重放的契约（v3.20 补记）**：`cli/batch_verify.py` 要求落盘的
`formal-plan.json` 等于原始模型响应，所以任何"落盘前修正模型输出"的归一化都会破坏
重放。正确做法沿用元素层的先例（`element-format-normalization.json`）：原始响应留在
`neural-formalization/model-claim.json`，修正后的 plan 落盘，变更写入同目录的
`normalization-log.json`，`verify` **重新施加**该变换并**审计变更记录**后才做严格相等。
`lib/salvage.py` 的机械重放路径施加同一变换，以免重放与所重放的运行结论不同。

### 4.8 当前稳定入口仍是 v3.16

v3.17 已完成开发回归，但仅 2/5 候选，并发现派生定义空真风险；v3.18 与 v3.19 都只在
提示词层解决矛盾（关系类别 vs 固定模板；类内容规则 vs grounding 规则），也都只跑过
5 例开发集。因此 README 仍推荐
v3.16，`RECOMMENDED_VERSION` 与 `DEFAULT_VERSION` 都未变；v3.20 是实验版
（`EXPERIMENTAL_VERSION`），不应直接替换默认路径。

### 4.9 断言策略可切换：`legacy` 与 `signals`（S12）

原先 `acceptance_status` 把两类东西混在一起否决：真正的结构失败（公式不可满足、
I/V 倒置），和模型自报的歧义/局限/未决项。在 72 个可重算 run 上实测，前者只占
4 个，后者却把通过率压在 0/72 —— 等于"越诚实越不通过"。

`lib/semantic_core.py` 的 `compile_bundle()` 现在有 `verdict_v2` 形参，对应两套策略：

| 策略 | 触发 | 判断依据 |
| --- | --- | --- |
| `legacy` | 默认；直接跑 `cli/semantic_pipeline.py` | 结构原因 **或** 任何模型自报的不确定性 |
| `signals` | `--claim-verdict signals`；`main.py run` / `batch` 自动注入 | 仅结构原因 |

`signals` 下模型自报的不确定性全部降级为信息性字段：`report_ambiguities_declared`、
`formalization_limitations_declared`、claim 自带的 `unresolved` / `modality`，
以及新增的 `coverage_status`（`complete` / `partial`）与 `coverage_gaps`
（`impacts_not_assigned` / `preconditions_not_used` / `effect_coverage_partial`）。

两条必须记住的约束：

1. **`legacy` 逐字节不变。**`cli/batch_verify.py` 用
   `require(bundle == saved, 'bundle replay mismatch')` 做严格相等重放，78 份冻结
   产物和 8 个测试文件依赖旧输出，所以新行为一律在 `verdict_v2` 之后。
2. **策略写进 `provenance.claim_verdict_policy`，`verify` 按它重放，不猜测。**
   旧 run 没有该字段时回落 `legacy`，历史产物仍可逐字节复现。

实测（72 个可重算 run，零模型调用）：`candidate_checks_passed` 由 0/72 升至
68/72（94.4%）；剩余 4 个 `needs_review` 全是真实问题 —— 3 个
`effects_feasibility` / `safety_negation_feasibility` unsat，1 个 I/V 倒置。

`coverage_status` 描述报告覆盖完整度，与 `acceptance_status` 正交，不能互相替代。

## 5. 重要文件索引

### 5.1 当前状态与汇报

- `HANDOFF.md`：本交接文件。
- `tools/report_constraints_v2/docs/STAGE2_CURRENT_STATUS.md`：完整历史和当前进度。
- `tools/report_constraints_v2/docs/STAGE2_PRESENTATION_REPORT.md`：可向导师展示的简洁汇报。
- `tools/report_constraints_v2/docs/SECOND_STAGE_DESIGN.md`：阶段二方法和设计依据。
- `tools/report_constraints_v2/docs/SAFETY_RELATION_TAXONOMY.md`：安全关系分类。
- `tools/report_constraints_v2/README.md`：操作说明和使用边界。
- `tools/report_constraints_v2/STRUCTURE.md`：目录结构与入口/库分工。
- `main.py`（仓库根目录）：唯一命令行入口，分发表在文件顶部。
- `PROTECTED_HASHES.json`（仓库根目录）：冻结资产哈希清单，用 `python main.py frozen` 校验。
- `archives/report_constraints_v1_20260912.zip`：已验证的完整 v1 归档；活动树中的
  `tools/report_constraints/` 已删除，不要恢复为第二套实现。
- `tools/report_constraints_v2/docs/V317_IMPLEMENTATION_REPORT.md`：v3.17 实现说明。
- `tools/report_constraints_v2/evaluation/archive/prompt_v317_development_03/REPORT.md`：最新五例结果。

### 5.2 核心实现

- `tools/report_constraints_v2/cli/semantic_pipeline.py`：主流程、模型调用、重试、路由和输出。
- `tools/report_constraints_v2/prompts/definitions.py`：P/I/V 唯一的人类可读规范。
- `tools/report_constraints_v2/prompts/active.py`：生产 Prompt 解析、契约检查和最终文本哈希。
- `tools/report_constraints_v2/prompts/registry.py`：Prompt 统一注册和功能矩阵。
- `tools/report_constraints_v2/prompts/versions/semantic_prompts_v317.py`：v3.17 Prompt。
- `tools/report_constraints_v2/prompts/versions/semantic_prompts_v318.py`：v3.18
  Prompt（仅提示词，派生于 v3.16，schema 仍为 `report-formal-plan/4`）。
- `tools/report_constraints_v2/prompts/versions/semantic_prompts_v319.py`：v3.19
  Prompt（仅提示词，派生于 v3.18，schema 仍为 `report-formal-plan/4`）。
- `tools/report_constraints_v2/prompts/versions/semantic_prompts_v320.py`：v3.20
  Prompt（仅提示词，派生于 v3.19，schema 仍为 `report-formal-plan/4`）。
- `tools/report_constraints_v2/prompts/versions/semantic_prompts_v316.py`：稳定版本 Prompt。
- `tools/report_constraints_v2/lib/plan_synthesizer.py`：形式计划校验与确定性 P/I/V 合成。
- `tools/report_constraints_v2/lib/ingest.py`：证据编号与原文回填、提取前信息充分性判断。
- `tools/report_constraints_v2/lib/report_only.py`：报告输入、DeepSeek 调用和本地配置。
- `tools/report_constraints_v2/lib/salvage.py`：数值保真（含协议编号排除）、地址性质保真与机械规范化。
- `tools/report_constraints_v2/lib/solving.py`：SMT/Z3 查询与 witness、可观察性审查与自动分流。
- `tools/report_constraints_v2/lib/semantic_core.py`：P/I/V schema、类型、编译与基础校验。
- `tools/report_constraints_v2/cli/batch_verify.py`：批量运行与零调用离线重放验证。
- `tools/report_constraints_v2/lib/compat.py`：历史模块名兼容注册（重构前的 14 个名字）。
- `tools/report_constraints_v2/tests/test_main_entry.py`：统一入口的命令表、退出码和保密回归。

### 5.3 关键测试

- `tools/report_constraints_v2/tests/test_prompt_v315.py`
- `tools/report_constraints_v2/tests/test_prompt_v316.py`
- `tools/report_constraints_v2/tests/test_prompt_v317.py`
- `tools/report_constraints_v2/tests/test_plan_synthesizer.py`
- `tools/report_constraints_v2/tests/test_automatic_triage.py`
- `tools/report_constraints_v2/tests/test_main_entry.py`
- `tools/report_constraints_v2/tests/test_frozen_assets.py`
- 其余 `tools/report_constraints_v2/tests/test_*.py`。

### 5.4 DeepSeek 配置

- 私密配置：`config/stage2_deepseek.local.env`
- 示例配置：`config/stage2_deepseek.local.env.example`
- 说明：`tools/report_constraints_v2/docs/DIRECT_DEEPSEEK_SETUP.md`

绝对不要读取并输出 API Key，不要将密钥写入日志、报告、命令参数或聊天。真实配置文件已由
`.gitignore` 忽略，权限应保持 `600`。

## 6. 已知限制（以当前状态文档为准）

本节下方原有问题清单和计划对应 2026-09 的 v3.17 时期，现已过时；不要按其中的 v3.21/schema v6 方案直接开工。当前主要质量限制是多影响报告在单 core-claim 表示中会部分表达，以及少量案例仍会出现公式范围、符号或语义对应偏差。阶段二已具备独立盲测和分层审查记录；不存在可信的“总体准确率”单一数字。详细证据与当前判断见 `STAGE2_CURRENT_STATUS.md`。

阶段三变量绑定、PoC 执行分析与一致性判定不属于阶段二未完成工作。

<!-- 2026-09 historical backlog retained below for audit context. -->

### 6.1 派生定义可能让 I 空真

v3.17 当前把派生定义组合为：

```text
definition ⇒ I_core
```

当派生符号被赋成不满足 definition 的值时，I 会空真。Monetrix 的 `P ∧ I` witness 已暴露
这一风险。这是当前最优先的逻辑缺陷。

不要直接把 v3.17 改成 `definition ∧ I` 并覆盖旧结果。正确做法是新建 v3.18/schema v6，
最好将定义建模为所有查询都必须满足的显式 semantic axioms；若采用其他方案，必须分析
`P∧I`、`P∧¬I`、`P∧V` 和阶段三接口的语义。

### 6.2 局部修复不能联动相关字段

模型常只修改报错字段，没有同步修改：

- `symbols[*].source_ids`；
- `impact_context_terms`；
- `derived_definitions`；
- `pattern` 与 `relation_class`。

Intuition 和 GTE Spot 均在三次尝试后因这类问题失败。

### 6.3 派生定义规则与 Prompt 不完全一致

程序只允许派生量引用基础符号，不能形成派生量链；Prompt 没有把这一限制说得足够明确。
同时 action/root-cause 是否允许作为派生定义证据尚未统一：GTE Spot 的定义引用真实 action
证据，却被当前 selected-source 白名单拒绝。

### 6.4 P 仍可能混入漏洞结果

Monetrix 将错误返回值 `decimals() = 6` 当作 P。证据 ID 合法不代表它属于动作前条件。
需要增加 P 的时序/角色检查，区分配置事实、触发条件、漏洞机制和坏结果。

### 6.5 安全关系类别可能错位

Olas 的价格验证性质被标为 `access_control`。本例公式仍能表达核心关系，但类别错误会影响
可解释性，也可能在其他案例选错模板。

### 6.6 复杂关系表达能力仍有限

跨交易、长期时序、复杂经济价值、量词、映射全局性质和多主体比较尚不能稳定表达。GTE
Perps 的 LP fork/reference 价值比较就是代表性失败。

### 6.7 尚无可信总体准确率

当前样本少，且许多案例已经参与规则修改。现有数字只能描述工程完成率或开发集缺陷，不能
声称通用准确率。没有经过独立专家确认、覆盖多类漏洞的统一金标准。

### 6.8 阶段三一致性尚未执行

`consistency_verdict` 仍是 `not_evaluated`。阶段二输出没有证明 PoC 执行逻辑与报告一致。

## 7. 历史待办（2026-09，已被后续演进取代）

- 尚未实现 `report-formal-plan/6`（`semantic_axioms` 那一套，顺延为 v3.21）；
  P 谓词重复的**强制**拒绝也留在那里（现在只在 `verify` 输出里报告）。
- 尚未修复派生定义空真。
- 尚未实现来源、谓词和定义的联动局部修复。
- 尚未统一 action/root-cause 对派生定义的证据资格。
- 尚未加入可靠的 P 时序角色检查。
- 尚未加入 impact 与关系模板的语义一致性门。
- v3.17 修正后尚未运行新的独立留出集。
- 尚未获得可信的 P/I/V 总体准确率、误放行率和误拒绝率。
- 尚未与阶段一切片结果进行变量绑定；这属于后续阶段，不要在当前任务中擅自实现。
- 尚未执行阶段三 PoC/报告一致性判断。

## 8. 当前收口记录（2026-10-20）

- S19 代码审阅和验证已完成。全量本地回归 **435/435** 通过，`git diff --check` 通过；新增调用预算测试覆盖 `semantic-live` 忠实度审查的两次最大调用。
- 随后的首项语义质量修正解决了 Covenant 报告 `2^noCapLimit` / `noCapLimit = 60` 被数值门误拒的问题；当前保存的模型计划通过数值门，回归增至 **437/437**。这是单例、零模型调用的机制验证，不代表准确率或泛化提升；细节见 `tools/report_constraints_v2/evaluation/semantic_quality_symbolic_bound_01/REPORT.md`。
- `prompt_live5_fidelity_01` 已补充核心 claim P/I/V 与报告影响覆盖的分层回溯评分：4 个候选中 1 个核心 claim 三维全过；12 项候选报告影响为 2 full、2 partial、6 deferred、2 not extracted。评审复用同模型且属事后重编码，不能当独立金标准；详见该评测目录的 `SCOPE_ADJUSTED_REVIEW.json`。
- 零模型调用重放通过：v3.17 Monetrix/Olas 两个指定历史候选，以及 `prompt_live5_fidelity_01` 的四个候选。
- 另外扫描 130 个归档/结果候选目录，94 个当前可重放，36 个因旧 Prompt/校验契约或历史产物不完整而失败。具体类别和兼容边界见 `tools/report_constraints_v2/docs/STAGE2_CURRENT_STATUS.md`；不承诺所有旧归档都可由当前 verifier 重放。
- 阶段二工程主线已达到交接条件。下一步由阶段三消费 `stage3-spec.json` 并完成代码变量绑定和执行一致性检查；语义忠实度、多影响覆盖及关系表达精度作为独立质量迭代，不作为阶段二无限期收口条件。

接手时仍先查看 `git status` 和 diff；不要覆盖工作树中已有改动。

以下原计划保留作历史记录，不作为当前行动顺序：

严格按以下顺序推进，不要一开始就继续扩大测试规模。

### 第一步：冻结 v3.17（已完成）

- 不修改 v3.17 Prompt、schema 和既有产物语义。**已遵守**：v3.18 是新文件，
  v3.5–v3.17 冻结文件一字未改。
- 确认当前主线测试继续通过：**331/331**（v3.17 时代为 286）。
- 保留 `evaluation/archive/prompt_v317_development_03/` 原始结果。

### 第二步：设计 v3.21/schema v6

目标只解决已确认的通用缺陷，不为单个案例硬编码：

1. 增加显式 `semantic_axioms` 或等价的全局定义层；
2. 所有 Z3 查询均应用定义公理，防止 I 空真；
3. 明确 derived definition 只能引用基础量，或正式支持有向无环定义图；
4. 明确 action/root-cause 作为定义证据的允许条件；
5. 局部修复按依赖组同时开放 `symbols`、context、definitions 和 pattern；
6. 增加 P 时序角色检查；
7. 增加 selected impact 与关系模板的一致性检查。
8. 把 `identical_p_predicates()` 接进 `/6` 的校验并随 v3.21 路由：两条不同的 P 来源
   复用同一谓词时合取会塌缩（`(and X X)` 即 `X`），报告的一条事实静默消失。发生率实测
   （限通过校验的计划）：v3.19 12/40、v3.20 4/43。**`/4` 不能原地收紧** —— 已跟踪的
   `deepseek_live_probe_04` 带重复且位于重放电池内 —— 因此现在只在 `main.py verify`
   的输出里报告（`redundant_p_predicates`），强制留到 `/6`。

新版本至少需要新增：

- `prompts/versions/semantic_prompts_v321.py`；
- `report-formal-plan/6` 常量和路由；
- v3.21 专用测试；
- `cli/semantic_pipeline.py`、`cli/batch_verify.py` 的版本路由；
- 文档和新输出目录。

不要删除 v3.17 / v3.18 兼容代码。

### 第三步：本地测试

- 先添加能复现空真、来源联动和派生链问题的单元测试；
- 再实现代码，确保旧版本重放不变；
- 运行全量测试和 `git diff --check`。

### 第四步：五例开发回归

继续使用 Monetrix、Intuition、GTE Spot、GTE Perps、Olas，仅用于验证已知缺陷是否改善。
开发回归不能作为泛化准确率。

### 第五步：冻结规则并运行全新留出集

- 在测试前冻结 Prompt、模板、阈值和程序规则；
- 选择未参与 v3.18 设计的新报告；
- 每次使用新输出目录和独立 API 请求；
- 分开统计：
  - 输入筛选通过率；
  - P/I/V 要素生成率；
  - 形式候选完成率；
  - 核心语义 pass/partial/fail；
  - 误放行率；
  - 误拒绝率；
  - 调用次数、tokens 和耗时。

## 9. 后续不要重复踩的坑

1. **不要把 InvCon/Trace2Inv 当作报告不变量提取器。**它们主要从执行轨迹或已知模板发现
   不变量，只能提供表示和验证思路，不能替代从报告自然语言推导 I。
2. **不要用 flattened 合约代替报告输入。**那会把“代码实际上做什么”混入“报告声称什么”。
3. **不要把 Z3 通过当成语义准确。**SAT/UNSAT 只针对生成公式。
4. **不要为了提高通过率放宽未知 ID、来源、类型或关键限定检查。**应区分正确拒绝和误拒绝。
5. **不要反复修改 Prompt 后继续在同一批案例上报告准确率。**这些案例已经变成开发集。
6. **不要覆盖旧输出目录。**每次实验使用新目录，否则审计和对比失效。
7. **不要让新测试复用旧模型响应。**新运行应发起独立请求；保存输出是为了审计，不是记忆。
8. **不要修改旧 schema 的确定性语义。**新缺陷用新版本解决，保证历史结果可重放。
9. **不要让 P 包含动作后的坏结果。**报告把某事实写成陈述句，不代表它属于前提。
10. **不要把次级影响合并进核心 V。**例如“价格错误”不自动等于“全部资产被盗”。
11. **不要把潜在攻击升级为已发生事件。**保持 asserted/potential/inferred 模态。
12. **不要用未定义布尔量代替可观察数值关系。**例如 `price_is_wrong=true` 不能替代明确阈值。
13. **不要把协议编号当数值。**如 ERC-4337、EIP-191。
14. **不要让局部修复偷换 intent、impact 或整体关系。**只有类型/单位等明确冲突才允许有界
    重分类，并保留完整审计记录。
15. **不要重启旧的生成后案例筛选。**用户要求的是提取前过滤信息不足的报告。
16. **不要把 `needs_review` 或 `--continue-on-review` 描述为通过。**它们只表示可以
    保留候选。同样地，`signals` 策略下的 `candidate_checks_passed` 也不表示"报告与
    实现一致"：它只说明这张断言通过了本地结构自检，阶段三仍未实现，
    `consistency_verdict` 始终是 `not_evaluated`。见 §4.9。
17. **不要泄露 API Key。**不打印、不提交、不复制到聊天或报告。
18. **不要执行破坏性 Git 操作。**当前工作树包含大量用户已有修改和未跟踪文件，不能
    `git reset --hard`、`git clean` 或删除不相关目录。
19. **不要擅自修改阶段一和阶段三。**当前授权范围是阶段二。

## 10. 常用命令

统一入口（阶段二）：`python main.py test`、`python main.py doctor`、`python main.py frozen`、
`python main.py versions`、`python main.py status`。`python main.py versions`、`python main.py verify <dir>`、`python main.py run ...`。
下面的原始命令与它们等价，保留用于历史重放。

### 全流程跑在官方 DeepSeek 上

`main.py` 只为**神经流程**注入 `--provider deepseek`：`run` 需要 `--extract` 或
`--formalize-only`，`batch` 恒为神经流程。`--allow-report-upload` 是上传报告文本
的显式同意门，缺它会在发起任何调用前退出。

```bash
# 单案例全流程：3 次 DeepSeek 调用（输入充分性筛查 + 抽 P/I/V 要素 + 形式化）
cd /root/sc_slicer_standalone
/root/.local/share/uv/tools/halmos/bin/python main.py run \
  --extract --allow-report-upload --case-dir /path/to/case \
  --output results/semantic/<新目录>

# 批量：每案例 3 次调用（--concurrency 1 便于对账）
/root/.local/share/uv/tools/halmos/bin/python main.py batch \
  --reports-root /path/to/reports --output results/semantic/<新目录> \
  --allow-report-upload --concurrency 1
```

**代理**：`main.py` 同时注入 `--deepseek-proxy direct`，即忽略环境里的 `*_proxy`
变量。这是踩过坑的：环境中的 `HTTPS_PROXY` 曾指向一个不响应 HTTP CONNECT 的端口，
urllib 隐式把请求交给它并立刻被掐断，报错却只有
`DeepSeek network failure; details not saved`，完全看不出是代理。若你的网络确实需要
代理，传 `--deepseek-proxy environment`（沿用环境变量）或一个 `http(s)://` URL；
`socks5://` 会被直接拒绝（urllib 不支持 SOCKS）。该标志仅对 `--provider deepseek`
生效。失败时看 `model-runtime-diagnostic.json` 的 `proxy_in_effect` 即可确认用了哪个代理。

走官方 API 需要 `config/stage2_deepseek.local.env`（权限必须 0600）。纯离线重放
`run`（给 `--elements` / `--formalization`）不会被注入，零调用；历史产物统一用
`main.py verify <run-dir>` 重放。

### 全量本地测试

```bash
cd /root/sc_slicer_standalone
/root/.local/share/uv/tools/halmos/bin/python -m unittest discover \
  -s tools/report_constraints_v2/tests \
  -t tools/report_constraints_v2 -p 'test_*.py' -q
```

当前基线应为：`Ran 276 tests ... OK`。

### 检查格式问题

```bash
cd /root/sc_slicer_standalone
git diff --check
```

### 离线重放 v3.17 两个候选

```bash
cd /root/sc_slicer_standalone
for c in Monetrix_L3gNZDymiju__XdnQZTBJovh__ckuTxYrFvYX \
         Olas_j3PRAMM3fVq__9eKVuFn3L2m__fvnHZN9Wssa; do
  /root/.local/share/uv/tools/halmos/bin/python main.py verify \
    "tools/report_constraints_v2/evaluation/archive/prompt_v317_development_03/runs/$c"
done
```

注意：`verify_semantic.py` 已在 S11 删除，上面的旧写法不再可执行。

两者应返回 `offline_verified: true`。`acceptance_status` 取决于该 run 记录的
策略：`legacy` 为 `needs_review`，`signals` 为 `candidate_checks_passed`。

### 自动化批量运行（推荐）

```bash
cd /root/sc_slicer_standalone
python main.py batch --reports-root /path/to/reports --output results/semantic/auto-001 \
  --provider deepseek --model deepseek-flash --prompt-version semantic-v3.16 \
  --lean-formal-input --continue-on-review --allow-report-upload \
  --max-cases 5 --resume
```

`--reports-root` 自动发现 `<dir>/<case>/report.json`，不需要手写 manifest；
`--resume` 复用输出目录并跳过已有 `status.json` 的案例，半成品目录会被改名为
`<case>.incomplete-<UTC>` 保留证据（不删除）。完成后写出 `batch-summary.json` 和
`batch-summary.md`。单批仍限制最多 5 例（`--max-cases` 可调），以控制费用。

### 当前稳定版单案例运行

```bash
cd /root/sc_slicer_standalone
PYTHONDONTWRITEBYTECODE=1 /root/.local/share/uv/tools/halmos/bin/python \
  main.py run \
  --case-dir /absolute/path/to/case \
  --extract --provider deepseek --model deepseek-flash \
  --prompt-version semantic-v3.16 --lean-formal-input \
  --continue-on-review --allow-report-upload \
  --output tools/report_constraints_v2/results/semantic/NEW_UNIQUE_RUN
```

官方 API 模型 ID 必须是 `deepseek-flash`，它对应当前使用的 DeepSeek-V4.1-Flash；不要写成
`deepseek-v4.1-flash`。调用会消耗 DeepSeek 账户额度，不消耗 Codex 模型额度，但当前聊天
代理本身的操作仍会消耗其所在产品额度。

## 11. 当前工作树注意事项

当前 `git status` 显示仓库已有大量修改和未跟踪目录，包括根 README、配置、baselines、
archives 和整个 `tools/report_constraints_v2/`。这些不应被视为可随意清理的临时文件。

- 只编辑与阶段二当前任务直接相关的文件；
- 不删除、重置或覆盖用户已有改动；
- 新实验必须写入新的唯一目录；
- 先读现有文档和测试，再修改代码。

## 12. 给新对话的第一条指令建议

可以在 DeepSeek V4 for Copilot Chat 中发送：

```text
请先完整阅读 /root/sc_slicer_standalone/HANDOFF.md，并核对其中引用的当前状态、
v3.17 开发回归报告和 v3.18 / v3.19 / v3.20 提示词修正的对照实测。继续阶段二工作，只修改
tools/report_constraints_v2，不修改阶段一、阶段三，不覆盖历史实验。先给出你对
当前剩余缺陷（grounding、truth binding）和 v3.21/schema v6 实施顺序的复述，
经确认后再开始修改。
```
