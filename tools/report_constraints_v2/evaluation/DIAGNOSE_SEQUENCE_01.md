# Sequence 第二步模型退出诊断与对照复验

日期：2026-09-16。输入为已归档的公开非敏感 Sequence `report.json`，复用此前通过证据校验的
`elements-ids.json`。本轮只调用第二步形式计划，不上传合约或 PoC；不使用人工修补。

## 结果

| 环境 | 结果 | 模型尝试 | 后续 |
| --- | --- | ---: | --- |
| 受限终端 | CLI 约两秒内 exit 1，脱敏类别 `unknown_runtime_error` | 1 | 未生成计划；`pipeline_failure` |
| 允许外部访问的对照环境 | 模型一次返回可校验计划 | 1 | 形式化、SMT、Z3 完成；`review` |

对照输出在 `results/semantic/diagnose_sequence_v37_01/` 和
`results/semantic/diagnose_sequence_v37_02/`。同一输入与提示在允许外部访问时成功，
因此受限运行环境是先前 `exit 1` 的**高度可能原因**；当前 CLI 没有明确返回具体的网络或
文件权限错误，不能进一步断言是哪一项限制。此前“模型服务本身故障”的假设没有证据支持。

成功调用耗时 83.091 秒，上报 21,399 tokens，估算成本 0.01063485（仅该次调用）。
`P∧V` 和 `P∧V∧¬I` 为 SAT，`P∧V∧I` 为 UNSAT；这仅检查公式内部关系。
自动分流仍为 `review`，因为永久 DoS 被延后为次级影响、报告有歧义、形式计划有限制说明。
这不是经独立核验的 P/I/V 语义正确性结论，也不是完整两步新运行。

## 已做的防泄漏改进

`report_only.extract` 在 CLI 非零退出时记录 `model-runtime-diagnostic.json`：只写退出码、
白名单错误类别、耗时，不保存原始 stderr/stdout 或请求正文。不可重试错误仍不会触发盲目重试。
只有显式 `--formal-retries 1` 才允许对空/非法 JSON、超时、无效计划重试一次。

下一步如需验证批量完成率，应在可访问模型的环境中对**新抽样报告**按固定协议运行，并
单列工程失败、`review`、`abstain` 和候选。旧五例与助手草案不能直接当总体准确率。
