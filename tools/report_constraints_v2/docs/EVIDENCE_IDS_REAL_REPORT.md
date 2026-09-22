# Brix 编号路径真实复验

后续改进提示的复验见 [BRIX_RETEST_REPORT.md](BRIX_RETEST_REPORT.md)：第一步已通过，第二步生成候选但因可能性升级被拒绝，仍未端到端成功。本文件保留首次编号测试历史。

日期：2026-09-12。用户明确授权向 `opencode-go/deepseek-v4-flash` 发送同一份 Brix 报告片段及提取要素，最多两次调用、不重试、不发送 PoC。本轮实际调用一次，未修改提示词、校验器或第一阶段。

## 结果：未端到端跑通

```text
同一份报告 → 20 个编号片段 → 模型返回 11 个实体、20 条陈述
          → 编号取回成功 → 动作步骤类型检查拒绝
          → 约束生成未调用 → Z3 未执行
```

报错为 `attack step must reference action`。原始 `attack_steps` 最后一项为 `st_mismatch_revert`，但该陈述被模型标记为 `root_cause`，不是 `action`。编号存在且原文可精确取回，当前问题不是引文拼接或未知证据编号，而是模型输出的结构关系不符合接口。

**没有手工删除该项、改写类型或追加模型调用。** 原始输出和拒绝状态完整保存。本次不能称约束生成成功，也没有本轮 Z3 SAT/UNSAT 结果或 PoC 一致性结论。

## 本地复核

- 报告原始文件与既有 `brix_fee_ids_offline_final` 完全相同。
- 输入 SHA-256：`5d2a1d54551d336aae12511eb950bbd160f9a7dc340db9bd0e411cc2eec72b97`，共 3,019 字符、20 片段。
- 重新生成编号表完全一致；解析原始模型编号所得材料与保存的 `elements.json` 一致。此前发生的长引文改写问题，本次未发生；这仍不证明所有解释都正确。
- 第二步目录、`constraints.json`、`solver-results.json` 均未生成；失败结果不适用完整成功包的 `verify_semantic.py`。
- 74 个受保护文件未变，未运行切片、修改缓存或冻结 v1。

## 用量与归档

模型上报耗时 44.204 秒，总 tokens 9,034：输入 3,955、输出 2,905、reasoning 2,174、缓存读写为 0。服务返回的 `cost` 字段为 0.00364065；不把该字段当作已核实的实际账单。

结果目录：[results/semantic/brix_fee_ids_model_01](../results/semantic/brix_fee_ids_model_01)。重点文件：

```text
status.json                         拒绝原因及调用次数
provenance.json / original-report    报告来源与原始快照
evidence-catalog.json                编号片段及原文区间
elements-ids.json / elements.json    原始编号结果及取回后的材料
neural-elements/model-response.txt   未修补的模型回答
neural-elements/model-usage.json      本轮上报用量
```

## 下一步建议

这是第一步的结构接口问题，不能据此否定从报告推导不变量的方向，但也不能宣称真实链路已跑通。最小改进是明确要求 `attack_steps` 只引用 `kind=action` 的陈述，并增加针对这条真实失败的回归用例；继续保留错误类型拒绝，不静默修复。另一个设计选项是将根因链与动作序列分开，不用同一个列表承载两者。改进后再单独安排一次有预算的真实验证；本轮不继续外部调用。
