# Brix 阶段二本地评测

日期：2026-09-14。新增外部模型调用：0。只评估现有输出，不修改原报告、历史模型候选、第一阶段或底层校验逻辑。

## 样本与标准

独立真实报告 1 份：Brix；评估其最新真实模型候选 `brix_fee_ids_core_model_01`。不同轮次使用同一报告、提示不同，不作为独立报告重复计数。助手修正的 `brix_observable_control_01` 单列作对照，不计入模型成绩。

参考为用户已认可的 [审核卡](REVIEW.md)，不是独立专家认证。助手将其窄核心义务手工映射到模型符号：

```text
P = buffered_flow_used && msg_value > native_fee
I = !paynative_reverted                  （限定 P 下）
V = paynative_reverted && !message_dispatched
```

`paynative_reverted` 按候选文字表示特定 NotEnoughNative 回退，不是任意失败。这种映射未经过实际代码绑定验证。比较域另加 `msg_value >= 0`、`native_fee >= 0`，仅用于本次评估，不写回原候选。没有 helper 算术、EVM 或代码转移关系 T。

## 实测结果

参考前提及数学域可满足。P 比较查询为域内 `XOR(P参考, P候选)`；I、V 比较还限定参考 P。UNSAT 表示在该抽象范围内等价，SAT 表示存在差异，UNKNOWN 不计为正确。

| 检查 | 最新真实模型候选 | 助手修正对照 |
| --- | --- | --- |
| 核心 P 公式 | 等价，UNSAT | 等价，UNSAT |
| 核心 I 公式 | 不等价，SAT | 等价，UNSAT |
| 核心 V 公式 | 等价，UNSAT | 等价，UNSAT |
| 三项窄公式全部等价 | 否 | 是，不计模型成绩 |

真实候选 I 差异赋值：`msg_value=1, native_fee=0, buffered_flow_used=true, excess_tolerated=false, paynative_reverted=false, message_dispatched=false`。此时参考 I 为真，模型 I 为假。它是规范层反例，不证明真实 helper 可产生该状态。原关系查询也允许坏效果和 I 同时成立，因此自由布尔旗标确实没有表达已审核的安全义务。

语义审核另发现：helper 与付款的关系、完整有效调用条件和金额域尚未完整约束；退款文字未落实为公式；持续失败和全体用户影响仅部分覆盖。潜在持续影响本轮没有升级为确定效果，但仅此一轮不能证明稳定改善。

结论：在本次 1 个模型候选中，核心 P/I/V 全部对齐的数量为 **0/1**。这只是单样本评测结果，**不能称总体准确率为 0%，也不能将两项等价称为 66.7% 的语义准确率**。助手对照通过仅说明目标窄义务可用观察量表达。

## 重放与保护检查

真实候选和助手对照的 `verify_semantic.py` 重放均通过，但都保持 `needs_review`、`consistency_verdict=not_evaluated`。观察量审核再次标出真实候选的 `excess_tolerated` 问题；受保护的 74 个文件哈希检查通过。

参考卡 SHA-256：`123c0c591482de8c38b5ef0184a007924899ecb2e8755f44e4b15ce064f4261a`。

实际比较的 hydrated formalization.json SHA-256：

- 真实候选：`f4f6b94638b168dbea723a8019e3a8fd6b6294dc170e5e713acf5d105e4980d6`。
- 助手对照：`5bf3b6467a07aa53a8dcf2cb580f2440b5f07c98b3d4f413658fae4e3ea3465a`。

只读复跑，完整 JSON 结果打印到终端，无模型调用：

```bash
/root/.local/share/uv/tools/halmos/bin/python \
  tools/report_constraints_v2/review_samples/brix_report/evaluate.py
```

下一步：先用最新观察量提示进行一次预算明确、单独授权的真实复验；新模型不得看到审核卡或参考公式。随后增加少量清晰真实报告作为留出样本，分别评估条件完整性、I 语义、公式对应、模态/范围及未覆盖影响。只有结构/证据通过、公式等价不够判定完整推导正确。
