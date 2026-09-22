# SC_Slicer 阶段二工作交接

更新时间：2026-09-21  
项目目录：`/root/sc_slicer_standalone`  
当前工作范围：`tools/report_constraints_v2/`  
目标接手环境：DeepSeek V4 for Copilot Chat 新对话

> 新对话首先完整阅读本文件，再阅读
> `tools/report_constraints_v2/docs/STAGE2_CURRENT_STATUS.md` 和
> `tools/report_constraints_v2/evaluation/prompt_v317_development_03/REPORT.md`。
> 不要根据旧聊天记忆猜测状态，也不要从头重做已经完成的实验。

## 1. 当前正在做什么

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
- `preview.py screen` 目前只做本地文件/输入检查；真正的语义充分性门在主流程中。

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

### 3.4 semantic-v3.15 至 v3.17

- v3.15：加入安全关系分类、关系对齐检查和更多通用算术表达。
- v3.16：关系类别唯一映射到固定模板；加入 `derived_definitions` 和字段级局部修复。
- v3.17：使用 `report-formal-plan/5`，增加：
  - 权限、边界、比例、状态对应、时序、进度等专用模板；
  - `impact_context_terms`，保留时间、阈值和状态限定；
  - P 中每个符号必须由对应 P 来源自己支撑；
  - 不同 P 来源不能重复使用完全相同的谓词；
  - ERC/EIP/BIP 等协议编号不再被误当成数值约束；
  - 类型/单位冲突时允许有界关系类别重规划。

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
- 2/5 可带警告继续，均仍为 `needs_review`；
- 2/2 候选通过零调用离线重放；
- 11 次调用；
- 65,925 输入 tokens、12,961 输出 tokens，共 78,886 tokens；
- 模型响应耗时合计 95.778 秒；
- 清理退役切片绑定分支后，当前主线全量本地测试 336/336 通过。

保守语义初评：

- Olas：核心 P/I/V 基本合理，但关系类别标为权限关系并不理想；
- Monetrix：部分正确，P 混入漏洞返回值，并暴露派生定义空真问题；
- Intuition：比例方向合理，但 impact 来源联动修复失败；
- GTE Spot：dust 条件方向合理，但派生定义链和来源不符合当前规则；
- GTE Perps：选中的是 LP 价值差，模型却生成单 reserve 守恒式，拒绝合理。

这是开发集缺陷定位，不是总体准确率或泛化率。

### 3.6 阶段二工程结构整理

- Prompt 已迁到 `tools/report_constraints_v2/prompts/versions/`，统一由
  `prompts/registry.py` 注册和管理版本能力；冻结 Prompt 文本的 SHA-256 未变。
- P/I/V 规范已集中到 `prompts/definitions.py`，生产流程经 `prompts/active.py`
  显式解析最终 Prompt；可用 `python main.py preview-prompt --part
  definitions|element|formal` 查看，不调用模型。v3.5–v3.17 冻结文件未修改。
- 自动测试已迁到 `tools/report_constraints_v2/tests/`；删除退役分支的 22 项专用测试后，当前主线 336 项通过。
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

### 4.6 Z3 不承担自然语言语义判断

Z3 只判断提供给它的公式。错误公式也可能得到完美的 SAT/UNSAT 结果。因此任何文档都不能
把“Z3 通过”写成“报告语义正确”或“PoC 一致”。

### 4.7 历史版本不可原地改写

历史运行依赖 Prompt、schema、确定性合成和文件哈希重放。发现 v3.17 缺陷后必须新建
v3.18/schema v6，不能静默修改 v3.17 语义，否则已有实验无法重放。

### 4.8 当前稳定入口仍是 v3.16

v3.17 已完成开发回归，但仅 2/5 候选，并发现派生定义空真风险。因此 README 仍推荐
v3.16；v3.17 是实验版，不应直接替换默认路径。

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
- `tools/report_constraints_v2/evaluation/prompt_v317_development_03/REPORT.md`：最新五例结果。

### 5.2 核心实现

- `tools/report_constraints_v2/cli/semantic_pipeline.py`：主流程、模型调用、重试、路由和输出。
- `tools/report_constraints_v2/prompts/definitions.py`：P/I/V 唯一的人类可读规范。
- `tools/report_constraints_v2/prompts/active.py`：生产 Prompt 解析、契约检查和最终文本哈希。
- `tools/report_constraints_v2/prompts/registry.py`：Prompt 统一注册和功能矩阵。
- `tools/report_constraints_v2/prompts/versions/semantic_prompts_v317.py`：v3.17 Prompt。
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

## 6. 当前明确存在的问题

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

## 7. 还没有完成的工作

- 尚未实现 `semantic-v3.18` 或 `report-formal-plan/6`。
- 尚未修复派生定义空真。
- 尚未实现来源、谓词和定义的联动局部修复。
- 尚未统一 action/root-cause 对派生定义的证据资格。
- 尚未加入可靠的 P 时序角色检查。
- 尚未加入 impact 与关系模板的语义一致性门。
- v3.17 修正后尚未运行新的独立留出集。
- 尚未获得可信的 P/I/V 总体准确率、误放行率和误拒绝率。
- 尚未与阶段一切片结果进行变量绑定；这属于后续阶段，不要在当前任务中擅自实现。
- 尚未执行阶段三 PoC/报告一致性判断。

## 8. 接下来应该怎么做

严格按以下顺序推进，不要一开始就继续扩大测试规模。

### 第一步：冻结 v3.17

- 不修改 v3.17 Prompt、schema 和既有产物语义。
- 确认当前 336 个主线测试继续通过。
- 保留 `evaluation/prompt_v317_development_03/` 原始结果。

### 第二步：设计 v3.18/schema v6

目标只解决已确认的通用缺陷，不为单个案例硬编码：

1. 增加显式 `semantic_axioms` 或等价的全局定义层；
2. 所有 Z3 查询均应用定义公理，防止 I 空真；
3. 明确 derived definition 只能引用基础量，或正式支持有向无环定义图；
4. 明确 action/root-cause 作为定义证据的允许条件；
5. 局部修复按依赖组同时开放 `symbols`、context、definitions 和 pattern；
6. 增加 P 时序角色检查；
7. 增加 selected impact 与关系模板的一致性检查。

新版本至少需要新增：

- `prompts/versions/semantic_prompts_v318.py`；
- `report-formal-plan/6` 常量和路由；
- v3.18 专用测试；
- `semantic_pipeline.py`、`verify_semantic.py`、`run_semantic_batch.py` 的版本路由；
- 文档和新输出目录。

不要删除 v3.17 兼容代码。

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
16. **不要把 `needs_review` 或 `--continue-on-review` 描述为通过。**它们只表示可以保留候选。
17. **不要泄露 API Key。**不打印、不提交、不复制到聊天或报告。
18. **不要执行破坏性 Git 操作。**当前工作树包含大量用户已有修改和未跟踪文件，不能
    `git reset --hard`、`git clean` 或删除不相关目录。
19. **不要擅自修改阶段一和阶段三。**当前授权范围是阶段二。

## 10. 常用命令

统一入口（阶段二）：`python main.py test`、`python main.py doctor`、`python main.py frozen`、
`python main.py versions`、`python main.py status`。`python main.py versions`、`python main.py verify <dir>`、`python main.py run ...`。
下面的原始命令与它们等价，保留用于历史重放。

### 全量本地测试

```bash
cd /root/sc_slicer_standalone
/root/.local/share/uv/tools/halmos/bin/python -m unittest discover \
  -s tools/report_constraints_v2/tests \
  -t tools/report_constraints_v2 -p 'test_*.py' -q
```

当前基线应为：`Ran 336 tests ... OK`。

### 检查格式问题

```bash
cd /root/sc_slicer_standalone
git diff --check
```

### 离线重放 v3.17 两个候选

```bash
cd /root/sc_slicer_standalone/tools/report_constraints_v2
/root/.local/share/uv/tools/halmos/bin/python verify_semantic.py \
  evaluation/prompt_v317_development_03/runs/Monetrix_L3gNZDymiju__XdnQZTBJovh__ckuTxYrFvYX

/root/.local/share/uv/tools/halmos/bin/python verify_semantic.py \
  evaluation/prompt_v317_development_03/runs/Olas_j3PRAMM3fVq__9eKVuFn3L2m__fvnHZN9Wssa
```

两者应返回 `offline_verified: true`、`acceptance_status: needs_review`。

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

### 预览将发送的报告文本

```bash
cd /root/sc_slicer_standalone
/root/.local/share/uv/tools/halmos/bin/python \
  main.py preview-report --case-dir /absolute/path/to/case
```

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
请先完整阅读 /root/sc_slicer_standalone/HANDOFF.md，并核对其中引用的当前状态和 v3.17
开发回归报告。继续阶段二工作，只修改 tools/report_constraints_v2，不修改阶段一、阶段三，
不覆盖历史实验。先给出你对当前缺陷和 v3.18 实施顺序的复述，经确认后再开始修改。
```
