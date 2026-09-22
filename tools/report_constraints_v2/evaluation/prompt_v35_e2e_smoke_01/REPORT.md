# 阶段二端到端 smoke：先跑通，再优化准确性

日期：2026-09-16。该实验只验证技术闭环，不计入真实报告准确率。输入是项目内新建的
合成授权漏洞报告，不含真实项目、PoC 或合约代码。

## 第一次完整两步调用（semantic-v3.5）

- 第一步成功生成并校验 `report-elements/2`。
- 第二步成功返回 `report-formal-plan/1`。
- 确定性合成前拒绝：`precondition_terms` 错把 impact/security_intent 当成 P 来源，
  与 `precondition_ids` 不一致。
- 失败结果原样保存在
  `results/semantic/prompt_v35_e2e_smoke_01/`，没有修补模型输出。

这证明报告输入和两次真实模型调用可运行，但 v3.5 计划约束不够明确。

## 最小版本化修正（semantic-v3.6）

不放宽校验器，不修改第一阶段。v3.6 只要求：

- 每个所选 P ID 恰好对应一个 P term，不能使用 intent/impact/action/root-cause ID；
- 无法由谓词语法表达的背景事实进入 assumption；
- 单个核心 V 只选择一个直接 impact，次级后果延期。

随后复用已经通过证据校验的第一步要素，仅进行一次真实 formalize-only 调用。

## 结果

- 模型计划通过结构和来源校验；
- 程序确定性生成 AST、claim、coverage、formula sources 和 SMT；
- Z3 完成全部 report-only 查询；
- `P AND V AND I = UNSAT`；
- `P AND V AND NOT I = SAT`；
- `verify_semantic.py` 离线重放通过，模型调用数为 0；
- `stage3-spec.json` 已生成。

最终状态为 `formalized_candidate / needs_review`，不是流程失败。原因是模型保留两条
`unresolved`，并把“收到资金”作为次级影响延期；当前策略要求这些内容经过人工语义审核。
由于没有代码 transition `T`，一致性结论仍为 `not_evaluated`。

## 结论

阶段二从报告到 P/I/V、形式约束、SMT/Z3、第三阶段接口的技术链已真实跑到底。
下一步应停止扩展流程功能，转向真实公开报告的小规模准确性评测，重点检查 P 完整性、
I 的方向/强度、V 是否直接否定 I，以及 unresolved 是否合理。
