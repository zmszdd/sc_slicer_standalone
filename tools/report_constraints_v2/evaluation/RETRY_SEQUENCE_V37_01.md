# Sequence 第二步受控重试复验

输入：`gold_v1/inputs/sequence_domain_fork.report.json`；复用盲测保存的 `elements-ids.json`，
只测试第二步形式计划。提示版本 `semantic-v3.7`，`--formal-retries 1`，最多两次外部调用；
未发送合约或 PoC。输出保存在 `results/semantic/retry_sequence_v37_01/`。

结果：模型运行程序首次调用直接返回 exit 1；状态为 `RuntimeError` / `rejected`，
自动分流为 `pipeline_failure`。实际外部调用尝试 1 次；按策略运行时错误不重试，
所以没有产生形式计划或 SMT/Z3 结果。当前无法断言空响应重试在真实服务上能否提高完成率。
运行时退出的具体外部原因未确认，不推断为网络、额度或模型质量问题。
本次运行发生在不可重试错误日志补丁之前，因此该目录没有 `formalization-attempts.json`；
实际尝试次数以 `status.json` 为准，后续运行会保存该日志。

离线测试已验证空/非法 JSON、超时和无效计划的受控重试分支，并验证不可重试错误只调用一次。
另用 Panoptic 保存输出离线重放，自动分流为 `review`，原因包括未覆盖的影响、未使用的
前提及报告歧义；没有误报为“语义已证实”。该重放不调用外部模型。

本次不是新的 P/I/V 准确率评测。五份盲测的历史文件和人工待审草案均未修改。
