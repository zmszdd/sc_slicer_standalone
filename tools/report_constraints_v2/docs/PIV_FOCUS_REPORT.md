# P 完整性与 V/I 直接反例关系改进

日期：2026-09-15。范围仅为阶段二；未修改第一阶段、切片代码或 AST 运算符集合。本轮外部模型调用为零。

## 本轮目标

按以下优先级收缩阶段二问题：

1. 先避免报告中已经提取出的核心前置条件在正式 P 中被静默遗漏。
2. 再要求 V 在 P 下直接否定 I，而不只是表示模糊损失或下游后果。
3. 超出当前 AST 的复杂性质继续 `null/unresolved`，不做弱化替代。

## 已实现

### P 完整性

`semantic-v3.2` 的第一步会扫描报告中的条件提示词以及权限、既有状态、余额、非零值、数值和时间关系。执行完成、状态变化、回退和损失仍不得进入 P。

第二步必须使用第一步提取的全部核心 precondition 来源。严格模式会计算：

```text
unassigned_precondition_ids = extracted_preconditions - formal_P_sources
```

集合非空时加入审核原因，`acceptance_status` 不能成为 `candidate_checks_passed`。该检查只能发现“已提取但公式遗漏”，不能证明第一步已经发现报告中的全部隐含条件，因此仍保留人工审核要求。

### V 对 I 的直接否定

严格模式执行三项报告规范内部查询：

```text
P AND V
P AND V AND NOT I
P AND V AND I
```

直接反例关系通过需要：

```text
SAT(P AND V)
SAT(P AND V AND NOT I)
UNSAT(P AND V AND I)
```

如果 `P AND V AND I` 为 SAT，说明当前 V 与 I 可以同时成立，通常表示 V 只描述了损失、遗漏了关键坏状态，或 I/V 作用域不一致。结果记为 `direct_counterexample_status: failed` 并进入人工复核。UNKNOWN 同样不通过。

这只是公式关系检查，不证明报告内容正确，也不执行 PoC。

## 兼容性

- 严格门槛只在 `semantic-v3.2` 启用；v3、v3.1 和历史结果仍按原行为只读复验。
- 默认 Prompt 仍为 `semantic-v3`；v3.2 在新留出集完成真实盲测前不升级。
- `stage3-spec.json` 会明确列出 `P AND V AND I` 查询，但仍保持 `execution_ready: false`。

## 验证

- 174 项阶段二回归测试全部通过。
- v3.2 mock 管线确认严格门槛和新增查询确实进入输出。
- 74 个受保护文件哈希不变。
- 外部模型调用：0。

## 下一步

选择不属于公开参考开发集、也未参与 v3/v3.1 调参的新报告，在相同输入上分别运行冻结的 v3 与 v3.2。至少分开统计：P 完整、P 无污染、自然语言 I、正式 I、V 直接反例、模态保持。真实盲测前不能声称准确率已经提高。

