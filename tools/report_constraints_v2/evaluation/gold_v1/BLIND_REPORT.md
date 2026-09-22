# semantic-v3.7 五报告盲测报告

日期：2026-09-16。模型：`opencode-go/deepseek-v4-flash`。五份输入在 manifest 中标为
公开、非敏感，只发送标题和描述/影响；不发送 PoC、代码、修复建议或 `gold.json`。
最多两次调用/案例，并发 2，无重试、无人工修补。

## 结论

- 第一步报告要素提取：5/5 完成。
- 产生可用形式计划：3/5。
- 完成确定性形式化、SMT 和 Z3：2/5（40%）。
- 成功结果离线重放：2/2 通过。
- 自动 `candidate_checks_passed`：0/5。
- 失败：空形式响应 1、形式化超时 1、schema/类型错误 1。

当前最主要的瓶颈仍是第二步模型输出的稳定性和 schema 遵循，而不是 Z3。

## 分案例结果

| 案例 | 第一步 | 形式计划 | SMT/Z3 | 状态/直接原因 |
| --- | --- | --- | --- | --- |
| Panoptic init | 完成 | 完成 | 完成 | `needs_review` |
| Sequence fork | 完成 | 空响应 | 未执行 | `JSONDecodeError` |
| Intuition pause | 完成 | 完成 | 完成 | `needs_review` |
| Olas sweep | 完成 | 超时 | 未执行 | `TimeoutExpired` |
| GTE dust | 完成 | 返回但非法 | 未执行 | int symbol 的 `unit:null`；pattern 形状也不合 schema |

Panoptic 和 Intuition 均满足：

```text
P AND V             = SAT
P AND V AND NOT I   = SAT
P AND V AND I       = UNSAT
```

这证明生成的 V 能直接否定 I，但不证明语义已经与人工金标准一致。

## structured unresolved 效果

Panoptic 和 Intuition 各返回两条非阻塞 advisory，均生成：

```text
blocking_count = 0
advisory_count = 2
claim.unresolved = []
```

因此 v3.7 已实现目标：非阻塞说明保留审计记录，但不再因“符号值没有具体常量”等理由直接
阻塞正式 claim。两份结果仍为 `needs_review`，原因是未分配次级影响、报告 ambiguities 和
模型 limitations，而不是结构化 unresolved。

不过 unresolved 内容的语义精度仍不理想：Intuition 把“谁设置 pause”以及报告已表达的
pause-before-call 顺序列为不确定；GTE 还加入与核心性质无关的调用权限问题。这些错误不会再
阻塞公式，但说明 unresolved 分类仍需通过人工金标准继续约束。

## 效率

| 指标 | 结果 |
| --- | ---: |
| 外部调用尝试 | 10 |
| 留下 usage 的已完成调用 | 9 |
| 已记录 total tokens | 97,801 |
| input tokens | 17,417 |
| output tokens | 64,256 |
| cache-read tokens | 16,128 |
| 已记录估算成本 | 0.041214534 |
| 已完成调用耗时之和 | 966.559 s |

Olas 第二步超时没有留下 usage，因此 token、成本和耗时合计都是**已记录下限**，不是完整账单。
高 output tokens 和 240 秒超时说明当前模型/Prompt 效率仍不足以稳定批量运行。

## 错误原因

1. **Sequence：空响应。** 第二步 usage 存在，但 `model-response.txt` 为 0 字节，JSON 解析失败。
2. **Olas：服务/生成超时。** 第一步完成，第二步超过 240 秒；按协议不重试。
3. **GTE：schema 服从失败。** `dust_amount`、`unfilled_amount` 是 int，却使用 `unit:null`；
   同时 pattern 使用 `{condition_forbids_effect:{...}}`，而不是规定的 `{kind:...}`。
4. **Panoptic：覆盖和歧义审核。** 核心 P/I/V 可形式化，但费用盗取作为次级影响未分配。
5. **Intuition：P 选择错误。** 形式 P 选择“继承这些入口”，没有选择实际 paused-window 调用。

## 准确率边界

`ratings.assistant-preliminary.json` 仅为助手初评，评分脚本会主动拒绝它。`REVIEW.md` 尚未由
人工全部确认，所以本报告不提供“可信准确率”。在人工批准金标准和逐项评分后，
`evaluate.py` 才会输出：

- 五维严格 pass-cell accuracy；
- 五维全部通过的 exact-case accuracy；
- 每个维度的 pass/partial/fail/not-evaluable 计数。

本轮可以客观报告的工程完成率是 2/5（40%），不能把它称为语义准确率。
