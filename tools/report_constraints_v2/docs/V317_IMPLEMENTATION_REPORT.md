# semantic-v3.17 实现与开发回归报告

## 目标

v3.17 针对 v3.16 留出测试暴露的三类通用问题：大多数关系被压缩为同一个模板、报告限定
没有进入公式作用域、不同 P 来源复用同一谓词，以及协议编号被误识别为数值约束。v3.16
及其冻结结果保持可重放，v3.17 使用新的 `report-formal-plan/5`。

## 实现

关系类别现在确定性映射到专用模板：

| 关系类别 | 程序模板 |
| --- | --- |
| `access_control` | `authorization_guard` |
| `bounded_value` / `range_capacity` | `bounded_relation` |
| `monotonicity` | `monotonicity` |
| `conservation` | `conservation` |
| `proportional_fairness` | `proportional_relation` |
| `state_correspondence` | `correspondence` |
| `temporal_validity` | `temporal_order` |
| `sequence_preservation` / `progress_or_liveness` | `required_effect` |
| `value_relation` / `data_structure_integrity` | `relation_obligation` |

新增三项程序检查：

1. `impact_context_terms`：检测到强时间、阈值或状态限定时，必须通过
   `qualifier_types` 分类并提供由该 impact 自身支撑的谓词；程序检查检测类型是否被覆盖，
   再将谓词同时加入 I 的适用范围和 V。
2. P 来源独立绑定：P 谓词中的每个符号必须由该条 P 自身支撑，不同 P 不能复用完全相同
   的谓词。
3. 数值扫描在 v3.17 排除 ERC/EIP/BIP/BEP/CAIP/SIP/SLIP/TIP 等协议编号；旧版本仍按旧
   逻辑回放。

## 验证状态

- 全量本地回归 **322/322**；v3.16 留出集的 3 个历史完整候选均通过零调用离线重放。
- 经用户明确授权，已将五份案例的已保存阶段二结构化要素发送至 DeepSeek
  `deepseek-flash`，未发送合约源码。
- 五例开发回归得到 2/5 最终候选和 2/5 带警告继续；两个候选均通过零调用离线重放。
- 11 次调用共使用 78,886 tokens，模型响应耗时合计 95.778 秒。

语义初评中 Olas 的核心 P/I/V 较完整，Monetrix 部分正确；其余三例分别暴露关系错配、
派生定义结构和来源联动修复问题。该批案例已参与开发，结果不是泛化准确率。详见
[五例开发回归报告](../evaluation/archive/prompt_v317_development_03/REPORT.md)。

因此 v3.17 仍是**实验版**：工程链可用且可审计，但尚不适合无人工复核投入使用。下一步
应以新 schema 修复派生定义空真和局部来源修复，再冻结规则并运行全新留出集。
