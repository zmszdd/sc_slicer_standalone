# semantic-live-14 真实报告盲测（新增 10 份）

## 方法

- 从冻结的 1,568 份报告集中预先固定 10 份未运行样本，分成两批各 5 份；清单见 [manifest_1.json](manifest_1.json) 和 [manifest_2.json](manifest_2.json)。
- DeepSeek Flash，`semantic-live-14`，串行；每份 readiness、element、formalization 最多各重试 1 次。模型没有收到参考答案（两份 `batch-summary.json` 均记录 `reference_answers_provided_to_model: false`）。
- 这是工程候选检查与离线重放评估，不是带独立金标准的语义准确率测试。

## 结果

| 报告 | 候选门 | Impact 数 | 规则化数 | 未完成数 | 模型调用 |
|---|---|---:|---:|---:|---:|
| SukukFi `…35X8HSswRc6` | `needs_review`：核心 P/I/V 未完整 | 2 | 0 | 2 | 9 |
| SukukFi `…NWyWHUbc8h8` | `candidate_checks_passed` | 4 | 3 | 1 | 14 |
| SukukFi `…4xd9CjGVS2n` | `needs_review`：核心 P/I/V 未完整 | 1 | 0 | 1 | 3 |
| Monetrix `…5yjseW7eSkE` | `needs_review`：核心 P/I/V 未完整 | 6 | 0 | 6 | 3 |
| Hybra Finance `…pG2nZWsvvjH` | `candidate_checks_passed` | 5 | 4 | 1 | 16 |
| SukukFi `…K8iEhnzEysb` | `needs_review`：核心 P/I/V 未完整 | 1 | 0 | 1 | 3 |
| Intuition `…deVmwC5DHi7` | `needs_review`：核心 P/I/V 未完整 | 2 | 0 | 2 | 3 |
| Sequence Transaction Rails `…vuyPaaLuUXu` | `needs_review`：核心 P/I/V 未完整 | 1 | 0 | 1 | 3 |
| SukukFi `…8j5nFX9rNe8` | `candidate_checks_passed` | 1 | 1 | 0 | 6 |
| Monetrix `…jczYF4pgf3U` | `needs_review`：核心 P/I/V 未完整 | 4 | 0 | 4 | 3 |

10 份中 3 份通过工程候选门（30%），7 份没有通过。原始清单共记录 27 条影响项，其中 8 条进入规则化、19 条未完成；这是流水线输出计数，**不是规则化成功率的有效分母**。其中包含缺少明确 P/I/V 来源、相互重叠或非主要的条目；按目标口径应先排除这些条目，再统计主要且 P/I/V 均有原文依据的影响项。该合格项分母尚未逐条完成审定。模型调用共 63 次。`consistency_verdict` 均为 `not_evaluated`，不能将候选门通过解释为端到端一致性验证通过。

## 质量抽查

候选产物中的自动语义审计均报零不一致，但它不是独立盲审。手工查看产物时，Hybra 的 5 个影响项有明显重叠：例如“合并/拆分损失用户奖励”在两条清单中重复表达，多个 gHybr 损失条目又复用同一组 P/I。它有 4/5 项形式化，工程检查通过，但清单去重和影响项边界仍需人工复核。SukukFi `…NWyWHUbc8h8` 也有标题性/概括性影响与具体影响并列的情况；系统标记了一条重复歧义。SukukFi `…8j5nFX9rNe8` 的单项 P/I/V、适用性和影响覆盖完整，且自动审计关系一致；这只是单例证据。

## 零模型调用重放

10/10 个样本均通过 `main.py verify`：`offline_verified: true`、`model_calls: 0`，包括 7 个未通过候选门的部分产物。重放验证产物可复验，不代表内容语义正确。

## 与上一轮 5 份合并观察

上一轮通过候选门 1/5，本轮 3/10；合计 4/15（26.7%）。两轮共调用模型 83 次。两轮原始流水线清单合计记录 31 条影响项、9 条进入规则化；这些原始计数包含未满足 P/I/V 完整性与主要性要求的项目，**不作为合格影响项的分母或成功率**。合格分母需逐项去重并核对原报告 P/I/V 证据后再统计。上一轮有 3/5 可重放，本轮 10/10；合计 13/15 可零调用重放。样本量有限，且没有配对旧版对照或独立金标准，因此不能据此断言语义准确率相对旧版提升。

## 评估

本轮显示两件事：离线重放链路稳定（10/10），但报告到完整 P/I/V 的主链仍不稳定（候选门 3/10，核心要素阻断 7/10）。下一步应优先定位这 7 份为何在核心 P/I/V 处停止，并针对“影响项重复/边界重叠”建立明确的去重与覆盖审阅；不能只依据候选通过率判断改进有效。
