# 第二阶段：报告驱动的不变量推导与形式化

日期：2026-09-12。当前主线不再以切片绑定成功为前提。旧 v2 迁移/切片定代码已在工程整理中删除；新入口为 `report_only.py`，不运行 InvCon/Trace2Inv。

后续已扩充三样例本地验证、过滤修复及授权开关，最新记录见 [BATCH_REPORT.md](BATCH_REPORT.md)。本文件保留首次 Brix 验证结果。

## 本轮结果

选择 Brix Money 的精确配对报告 `3hfE23tsgzG` / `PGwVR6CTD6U`，目标测试 `test_PoC_bufferedFee_reverts`。配对标识、源/请求标识及合约 SHA 均通过检查。合约仅用于本地身份校验，不提供给提取模型。

推导输入只含报告描述与影响，排除标题有效性标签、修复建议、PoC 段落及 fenced 代码。描述中的行内代码名作为自然语言指代保留；此过滤不能保证报告 prose 中完全没有代码逻辑。

从“提供缓冲报价，让调用者支付较多费用并依赖退款”的意图，推导以下**候选安全性质**，而非把报告描述的有缺陷实现条件当成安全规则：

```text
P：paid_fee > quoted_fee ∧ quoted_fee ≥ 0
I：paid_fee ≥ quoted_fee ⇒ ¬fee_mismatch_reverted
V：fee_mismatch_reverted ∧ ¬message_dispatched
```

I 表示该缓冲支付流程不应仅因足额/超额支付触发费用不匹配回退；不是“任何 unstake 都必须成功”，也没有推导永久锁仓或资金损失。费用非负、同一次调用与同一执行时报价的假设明确列出。安全性质是调用/状态转换上的义务，不必强行写成所有状态恒成立的余额不变量。

每个符号含 sort、单位、语义、检查点及原文引文；每个性质含 AST、原文证据、自然语言含义与推导解释。SMT 使用数学整数、布尔值、非数值地址身份；不假装实现 Solidity 溢出、交易回退或跨链语义。P/I/V 通过类型检查、P 可行性及性质可行性检查，SMT 可解析；这些检查不能证明语义抽取正确或 PoC 一致。

## 自动化与权限边界

自动入口让模型自行提出符号和性质，不预置攻击类别、公式或本案变量。默认仅一次调用，无自动反馈重试或备用假公式。

本轮普通模型进程退出 1；扩大权限调用被审核拒绝，因为未明确授权向已配置的外部模型服务发送报告文本。没有绕过拒绝。**尚无本案外部模型自动提取结果或可报告的模型 token 用量。**

保存的成功样例来自当前助手直接阅读原文后的推导，来源标记为 `assistant_review`，不是外部模型命令输出，不能计作自动提取准确率。初次离线验证因引文遗漏 Markdown 反引号而拒绝；仅修正引文，未改变公式。失败目录保留，最终结果位于 `results/report_only/brix_fee_assistant_final/`。

## 接口与验收

- `constraints.json`：`report-semantics/1`，动态符号与 P/I/V；仅 I 已形式化也可以是完整的第二阶段候选结果。
- `predicates.smt2`：声明和 `report_preconditions/report_safety/report_effects` 定义，不断言 I/V 成立，不含 T。
- `stage3-spec.json`：规范文件哈希、配对身份、待绑定事项；`execution_ready=false`，不得冒充执行就绪输入。
- `formalization_status` 与 `code_alignment_status` 分离；本例分别为 `formalized_candidate`、`not_attempted`。
- `human_semantic_review_required=true` 表示候选仍需语义核对，不是每份输入都必须人工编写公式。

新增 12 项编译/过滤控制测试，加上旧 22 项，共 34/34 通过；不是 34 份报告评测。旧保护检查确认 74 个文件未变，第一阶段、缓存与冻结 v1/ZIP 未修改。

## 下一步

获得发送报告文本到配置模型服务的明确授权后，对同一份报告进行一次真实自动提取，与本轮助手候选比较，允许等价表达而不要求字面一致。再增加 3–5 份非同类的精确配对报告，记录语义忠实性、假设、不可表达比例及成本；之后才做可选代码绑定。当前仍未完成自动泛化评测或第三阶段符号执行。
