# 阶段二通用安全关系分类（semantic-v3.15）

## 目的

v3.14 只有四种顶层逻辑模式，容易把不同安全性质都压缩为“条件禁止/要求某个结果”。
v3.15 在不改变历史版本的前提下，引入 `report-formal-plan/3`：模型先选择通用安全关系
类别，程序再检查类别与逻辑模板是否兼容，并确定性生成 I、V、AST、SMT 和 Z3 查询。

分类不是漏洞名称，也不预置某个案例答案。它描述报告声称的**安全关系形状**。

## 关系类别

| `relation_class` | 典型安全含义 | 示例关系 |
| --- | --- | --- |
| `access_control` | 效果必须得到某种授权 | `transfer -> owner_or_approved` |
| `value_relation` | 两个观测值应满足直接关系 | `event_token == state_token` |
| `bounded_value` | 数值必须处于报告给出的边界内 | `price_deviation <= max_slippage` |
| `monotonicity` | 状态随触发只增不减或只减不增 | `assets_after >= assets_before` |
| `conservation` | 同单位数量在前后或各方之间守恒 | `assets_after + paid == assets_before` |
| `proportional_fairness` | 份额、价格或分配满足报告给出的比例 | `shares * assets_before == deposit * supply_before` |
| `state_correspondence` | 事件、缓存、计数器和真实状态相符 | `event_recipient == state_recipient` |
| `temporal_validity` | 操作只能在报告给出的时间关系下生效 | `execution_time <= deadline` |
| `sequence_preservation` | 嵌套/批量操作不能破坏外层上下文 | `outer_context_after_inner == true` |
| `data_structure_integrity` | 链表、队列或索引关系在更新后保持 | `next.prev == current` |
| `progress_or_liveness` | 合法操作应完成，或不应因目标原因回退 | `valid_call -> !target_revert` |
| `range_capacity` | 值必须处于存储位宽或支持范围内 | `stored_value == computed_value` |

## 确定性逻辑模板

v3.15 保留四个历史模板，并新增三个模板：

- `relation_obligation`：`condition -> relation`，V 为 `condition ∧ ¬relation`；用于边界、
  对应、比例、时间、序列、数据结构和范围关系。
- `monotonicity`：生成 `after >= before` 或 `after <= before`，V 自动取反。
- `conservation`：生成 `after_expression == before_expression`，V 自动生成为不等。

程序拒绝类别与模板不匹配。例如 `monotonicity` 不能配
`condition_forbids_effect`，从而减少模型虽然选对类别却输出无关公式的空间。

v3.15 还会从模板中机械提取定义 I/V 的核心观测量。它们的 `source_ids` 合并后必须同时
覆盖所选 `intent_id` 和每个 `impact_id`；trigger/condition 中仅用于描述场景的变量不计入。
成功时保存 `relation-alignment.json`，缺少覆盖时在 SMT 生成前拒绝。V 由程序对同一关系
直接取反，因此 I/V 在结构上共享核心观测量。

定量表达现支持报告明确提供的 `add`、`sub`、`mul`，并继续检查类型和单位。没有原文关系
时不得从领域知识补公式。

## 多影响处理

要素层可保留 1–4 个直接影响，解决旧版“最多两个影响”对报告抽取的机械误拦截；但
`report-formal-plan/3` 的单个计划必须只选择一个影响。不同关系应延期或在后续多 claim
版本中拆分，不能为了覆盖率强行合成一条公式。

## 当前边界

- 分类仍由模型选择；程序只能检查类别与模板兼容，不能单独证明分类忠于报告。
- 尚无一般除法、单位消去、量词、数组/映射聚合、无界时序逻辑。
- I 与 V 已由同一模板共享核心观测量，但来源覆盖仍依赖模型提供的 statement ID，不能
  单独证明其语义绑定正确。
- 一个计划仍只生成一个核心 claim；多个不同关系尚需分别规划。
- v3.15 已通过本地编译、端到端模拟与离线重放，并完成五份冻结新报告测试；分类初评
  4/4，但严格 P/I/V 公式全通过 0/4，说明类别选择尚不能保证公式忠实。

因此 v3.15 仍是实验版本，不覆盖 v3.14 冻结留出集；真实结果见
[留出报告](../evaluation/prompt_v315_holdout_01/REPORT.md)，不能据此回写历史准确率。

## v3.16 固定模板补充

v3.16 保留上述 12 类，但不再让模型在兼容模板集合中自由选择：`monotonicity` 固定为
单调模板，`conservation` 固定为守恒模板，其余类别固定为 `relation_obligation`。模型只填
条件、关系、符号和来源。派生量通过 `derived_definitions` 显式定义，程序将定义同时加入
I 与其构造性反例 V。字段级局部修复禁止改变未获准的分类、意图和来源选择。

这减少了类别正确但模板形状错误的工程失败，仍不能证明 condition/relation 与选中 impact
同义。v3.16 留出集的严格公式仅 1/3，表明下一步应集中解决作用域和攻击限定保真，而不是
继续扩充关系类别。

## v3.17 专用模板与通用检查

v3.17 不增加漏洞名称，而将已有类别映射为更具体的确定性公式模板：权限、边界、比例、
状态对应、时序和进度分别使用 `authorization_guard`、`bounded_relation`、
`proportional_relation`、`correspondence`、`temporal_order` 和 `required_effect`；单调与
守恒保留原模板，只有通用值关系和数据结构关系使用 `relation_obligation` 兜底。

`report-formal-plan/5` 还要求强时间/阈值/状态限定先通过 `qualifier_types` 分类，再由
`impact_context_terms` 进入 I/V，
要求每条 P 的变量由其自身来源支撑且不同 P 不复用同一谓词，并在数值保真检查中排除
ERC-4337、EIP-191 等协议标识符。实现和验证边界见
[v3.17 实现报告](V317_IMPLEMENTATION_REPORT.md)。该版本已完成五例开发回归，但尚未完成全新
留出测试，因此不能用本地单元测试推断准确率。
