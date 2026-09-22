# 证据编号、模块化 SMT 与 Z3 反例完善

日期：2026-09-12。本轮只改第二阶段，不新增外部模型调用；保留之前两次真实模型失败结果，未手工修复后冒充自动成功。

后续真实编号复验已完成一次调用，见 [EVIDENCE_IDS_REAL_REPORT.md](EVIDENCE_IDS_REAL_REPORT.md)：证据编号取回成功，但模型动作列表引用了根因陈述，被结构检查拒绝；约束生成及 Z3 未执行。以下“尚未运行”描述为实现轮的历史状态。

## 1. 证据由程序编号和取回

`evidence_catalog.py` 先对提取输入的非空行生成片段，长行按最多 700 字符分片。每片有 ID、精确原文、字符区间及行号。ID 带报告输入哈希前缀，防止把另一报告的编号当作本报告证据。

模型接口升级为 `report-elements/2` 和 `report-formalization/2`，使用 `evidence_ids`，不再要求模型复制长引文。模型可为跨片段支持选择多个 ID；程序将它们分别解析为原文片段，不拼接伪造连续引文。未知/重复编号、被篡改的片段表、混用引文和编号均拒绝。

原始 ID 输出、编号表和程序解析后的材料同时保存。程序解析后的内部格式继续兼容 /1，沿用类型/单位、来源角色、子公式映射、覆盖及 I/V 关系检查；没有取消证据检查或模糊匹配引文。观测符号的旧格式只接受单条引文，取首条作兼容字段，完整选中 ID 仍保留在原始文件。

编号证明“引用了哪段原文”，不证明“这段原文支持模型的解释”。主体、条件、安全方向和影响完整性仍需检查。多行代码/修复/PoC 过滤保持不变，编号表不是代码切片，也不预置漏洞公式。

## 2. 模块化合成与求解

`symbolic_queries.py` 将模型/助手候选 AST 经类型校验后确定性编译为符号、P/I/V 定义，并逐项合成 SMT 查询。不是在固定漏洞模板中挑一条公式，也不声称实现可微符号编程或训练算法。

当相应性质存在时，生成 P、P∧I、P∧¬I、P∧V、P∧V∧¬I、P∧V∧I。每项保存独立 SMT、SAT/UNSAT/UNKNOWN 和查询哈希；SAT 保存 Z3 变量赋值，UNSAT/UNKNOWN 不伪造反例。变量若由 model completion 补值会明确标记，不能把任意补值当成代码观察。

`verify_semantic.py` 会重新求解、核对文件哈希，并检查保存赋值满足相应查询。地址反例按符号身份验证，不当成真实链上地址。已有 /1 历史输出仍可复验，新目录额外保存求解结果；不覆盖旧输出。

## 3. 离线结果

新的助手来源示例在 `results/semantic/brix_fee_ids_offline_final/`。其编号材料由已有助手示例迁移，AST 未改变，不是外部模型的自动提取结果。

本例得到：P∧V∧¬I = SAT，P∧V∧I = UNSAT。Z3 给出的报告规范反例包括：quoted_fee=0、paid_fee=1、fee_mismatch_reverted=true、message_dispatched=false。

这说明该数学状态满足所建模前提/坏效果并违反候选 I，**不证明这种费用关系能由真实缓冲 helper 产生，不证明 PoC 真能执行到该状态**。当前没有代码 T、helper 数值关系或 EVM 回退模型；不能称漏洞已复现或报告已验证。

核心 I 状态为 formalized_candidate，整体验收仍 needs_review：全局 UX 不可用与无直接资金损失没有完整形式化。该状态不因代码尚未绑定而否定 I 的形式化。

## 4. 文件

```text
evidence-catalog.json       程序编号的原文片段
elements-ids.json           原始编号核心要素
formalization-ids.json      原始编号约束候选
elements.json              程序取回引文的兼容材料
formalization.json         程序取回引文的兼容候选
constraints.json           类型、来源、覆盖及关系验收
solver-results.json        各项状态、赋值和查询哈希
queries/<claim>/*.smt2      可复跑的模块化查询
stage3-spec.json            待绑定接口，execution_ready=false
```

离线复验：

```bash
/root/.local/share/uv/tools/halmos/bin/python tools/report_constraints_v2/verify_semantic.py \
  tools/report_constraints_v2/results/semantic/brix_fee_ids_offline_final
```

自动路径默认使用编号。得到针对选定报告、最多两次调用的外发授权后，使用 `semantic_pipeline.py --report FILE --extract --allow-report-upload --output NEW_DIR`。第一步失败就不执行第二步，无自动重试。`--evidence-mode quotes` 仅用于旧模式兼容，不绕过原文检查。

## 5. 验证和限制

84/84 回归测试通过，覆盖未知编号、跨报告编号、精确取回、篡改、ID 两步模拟、SMT 重放、反例检查和地址身份。模拟调用不算真实自动提取质量评测。保护检查确认 74 个文件未变，第一阶段、原缓存及冻结 v1/ZIP 未修改。

新的真实模型编号路径尚未运行；本轮只证明框架和离线示例能工作，尚未证明模型会选择正确编号或生成正确 I/V。下一步应只选 Brix 做有预算的两步真实复验，再决定是否扩大样例。
