# Brix 报告：首次真实自动提取验证

后续已实现核心要素分层、逐影响覆盖与自动符号验收，见 [SECOND_STAGE_DESIGN.md](SECOND_STAGE_DESIGN.md)。新的神经路径尚未做真实质量复验，不能因此称本次模型错误已解决。

日期：2026-09-12。结果：**模型调用与形式化流程成功运行，但本次安全性质推导语义不合格。** 不能把类型/SMT 检查通过算成不变量抽取正确。

## 实验范围

用户在了解报告外发方式与服务器影响后要求继续验证；权限审核批准一次 Brix 报告提取。使用配置的 `opencode-go/deepseek-v4-flash`，仅发送提取提示及约 3 KB 的报告描述/影响文本。

未发送 PoC 合约、已有助手候选公式或密钥文件；服务认证由现有客户端处理。不向模型提供案件专用语义变量，不运行 InvCon/Trace2Inv。一次调用后停止，无反馈重试。模型返回事件未报告工具使用。

原始实验目录：`results/report_only/brix_fee_model_01/`。保留原提示、报告输入、模型响应、声明、用量、来源、形式化文件及接口。本轮没有覆盖或手工改正模型公式。

## 模型实际输出

模型自行提出 exact_fee、buffered_fee、msg_value、message_sent、reverted 等符号，并正确捕捉到缓冲支付条件：

```text
P：msg_value = buffered_fee ∧ buffered_fee > exact_fee
模型 I：P ⇒ ¬message_sent
模型 V：在 P 下 reverted ∧ ¬message_sent
```

V 原始 AST 还加入 `reverted = ¬message_sent`，原文件保留完整结构。以上是方便阅读的 P 范围内简写。

关键错误：模型虽然在解释中认识到“缓冲流程本应工作”，却把“消息未发出”的坏效果写进 I。这个 I 描述漏洞表现，而非预期安全义务；执行发生坏效果时会满足 I，反而可能被后续错误解释为没有违反安全性质。

本案合理的安全方向应至少是“符合该缓冲支付流程时，不因费用不匹配回退”。若改成“必须发送消息”，还需另外限定其他执行条件，不能无条件保证成功。

其他需审查的问题：excess_equals 符号未使用；模型文字提到 bounded ints，但实际规范没有整数界限；退款行为没有形式化。原文引文正确不保证这些推导正确。

## 离线验证与审查

原有检查通过：字段格式、动态符号类型/单位、原文引文、P 可行性、I/V 可行性、SMT 解析、保存文件与模型原始声明一致。原始 `formalization_status=formalized_candidate` 仅表示语法/逻辑形式候选，不能当成语义验收。

新增独立审查器 `review_semantics.py`，检查声称效果与安全性质的关系：

| 查询（仅报告规范，不含代码 T） | 自动输出 | 既有助手 Brix 候选 |
|---|---|---|
| P ∧ V | SAT | SAT |
| P ∧ V ∧ ¬I | UNSAT | SAT |
| P ∧ V ∧ I | SAT | UNSAT |

自动输出中 V 在 P 下蕴含 I，触发“可能 I/V 反转、安全性质过弱或配对错误”警告。结合原文人工语义核对，本次确定属于安全方向反转。审查保存为 `semantic-review.json`，状态 `needs_review`、`eligible_for_stage3=false`，不改写原始模型结果。

该关系检查是一项通用合理性警报，不是语义真值判定器，也不是代码一致性证明。V 不一定覆盖全部安全性质；缺少 I/V 时只标记检查未完成。即便无警报，也仍需语义核对与第三阶段 T。

## 用量与保护

- 一次外部模型调用，用时 25.301 秒。
- 服务上报 total 6,426 tokens：input 1,392、output 3,242、cache read 1,792；reasoning 0。
- 服务上报 cost 字段为 0.002159376；这里只记录返回值，不据此承诺实际账单。
- 独立审查新增 5 项回归检查，加上原 40 项，共 45/45 通过；保存的自动输出及助手候选均通过离线文件复验。
- 保护检查确认 74 个文件未变；第一阶段、Solar、原缓存和冻结 v1/ZIP 未修改。没有部署服务或执行 PoC。模型客户端可能产生自身日志/缓存，本轮不声称整台服务器零写入。

## 复验

```bash
/root/.local/share/uv/tools/halmos/bin/python tools/report_constraints_v2/verify_report_only.py \
  tools/report_constraints_v2/results/report_only/brix_fee_model_01
/root/.local/share/uv/tools/halmos/bin/python -m unittest discover \
  -s tools/report_constraints_v2/tests \
  -t tools/report_constraints_v2 -p 'test_*.py'
```

关系审查结果已保存。`review_semantics.py DIR` 会创建新 `semantic-review.json`，已有文件时拒绝覆盖；测试会重新计算关系且不改写保存文件。

## 结论与下一步

真实自动链路已运行，证明工具能够接收模型自提符号并输出形式化文件；**没有证明自动不变量推导可靠，本次实际发现错误。** 仅一例一次调用，不计算泛化准确率。

下一步应先强化“预期安全 I / 已声称坏效果 V”的语义区分，并将关系审查纳入自动验收，再对同案做一次有预算的复验。不能手工替换本次 I 后称自动提取成功，也不宜直接扩大批量或接入第三阶段。新的外部调用须另行明确范围，本轮不继续调用。
