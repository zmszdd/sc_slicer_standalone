# 阶段二两份新报告完整流程小测

日期：2026-09-16。样本与 SHA-256 在运行前冻结于 [manifest.json](manifest.json)。
两份具体 submission 未见于现有阶段二评测/提示文件；项目类型分别为数值边界与 epoch 时长。
使用 `semantic-v3.7`、同一外部模型、顺序运行，最多一次第二步重试。
仅 `report.json` 标题及描述/影响送入模型；合约、PoC、修复建议未送入模型。

## 工程结果

| 案例 | 要素提取 | 形式计划 | SMT/Z3 | 调用 | 自动分流 |
| --- | --- | --- | --- | ---: | --- |
| Forte `sqrt(0)` | 完成 | 初次因 `missing plan quantity unit` 拒绝，重试完成 | 完成 | 3 | `review` |
| Merkl duration | 完成 | 一次完成 | 完成，但 `P∧V=UNSAT` | 2 | `abstain`（离线新分流重放） |

5 次完成调用共记录 52,538 tokens、293.913 秒模型耗时、估算成本 0.022306176。
这是两份小样本的记录值，不是稳定吞吐或账单费用。Forte 实际证明了一次 schema/单位错误
可被受控重试恢复；Merkl 未触发重试。两份 `status.json` 均为 `needs_review`，
表示程序生成了形式文件但未通过验收；`auto-triage.json` 是额外的路由层。

## 语义抽查：没有可信准确率

- **Forte：P 含未获报告支持的角色假设。** `c_true_any_caller` 声称“任何人（包括未授权者）
  都能调用 sqrt”；它引用的片段仅说零输入和 `stop()`，没有调用权限事实。
  编号合法不等于语义蕴含。核心 I/V 的零输入与不返回方向相符，但形式计划用
  `returns_valid_zero` 布尔量概括了 packedFloat 的具体零表示，仍需后续绑定或更精细约束。
- **Merkl：P/I/V 自相矛盾。** 模型把“文档要求 duration 是 epoch 整数倍”选为实际 P，
  同时 V 表达创建了非整数倍 duration 的活动，故 `P∧V=UNSAT`。
  这不是合理反例，也不是报告支持的触发前提。现有谓词语法不能表达 `%`；模型把
  `duration_is_multiple_of_epoch` 作为布尔观察量并列为非阻塞 unresolved，不能据此宣称
  数值不变量已忠实形式化。

上述为助手依报告原文的**问题定位**，不是独立专家金标准，不据此计算总体 P/I/V 准确率。
两例均不能称“自动语义确认”。Z3 SAT/UNSAT 只检查生成公式，不检查报告真实性或 PoC。

## 分流修正与结果位置

Merkl 初次运行的 `auto-triage.json` 为 `review`，但内部关系已显示 `P∧V=UNSAT`。
现已把这类数学上不可行的核心约束通用地改为 `abstain`，并在
`results/semantic/generalization_probe_01/merkl_epoch_duration_replay/` 对冻结模型输出
离线重放验证；旧运行文件保持原样。Forte 原始输出在
`results/semantic/generalization_probe_01/forte_sqrt_zero/`，Merkl 原始输出在
`results/semantic/generalization_probe_01/merkl_epoch_duration/`。

下一步应优先解决“证据编号合法但陈述不被证据支持”和“取模关系无法表达”两类问题，
在固定可访问环境下继续跨项目抽样；不要因为工程链 2/2 完成就发布准确率。
