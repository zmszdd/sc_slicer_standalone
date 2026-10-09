# semantic-v3.3 单案例 smoke

日期：2026-09-16。目的不是测准确率，而是验证两个局部修复：`report.json` 标题去重，
以及第二步 impact/source ID 白名单。案例为此前在第二步虚构 `fok_fill_reverted` 的 GTE
FOK dust 报告。模型 `opencode-go/deepseek-v4-flash`，最多两次调用，无重试、无修补。

## 已确认

- 冻结的 `semantic-v3.2` Prompt 未被改写；旧 A/B 哈希和离线重放继续通过。
- 新逻辑独立注册为 `semantic-v3.3`。
- `report-json-input/2` 能对 `report.json.title` 与正文首个同名 H1 去重。
- 第二步 payload 会由程序生成 `allowed_statement_ids`，分别限定 P、I、V 来源。
- Prompt 明确要求 `impact_ids` 与 `effect_coverage.statement_id` 逐字复制 effects 白名单，
  且 coverage 行禁止额外 `impact_id` 字段。
- 本地合成测试及完整回归通过；受保护文件未变。

## 真实 smoke 结果一：完整两步

第一步返回了结构完整的 GTE 要素，但新增 assumption `asm_caller_permitted` 的
`evidence_ids` 为空。证据解析器按既有严格规则以 `invalid/duplicate evidence IDs` 拒绝，
第二步没有调用。

因此本轮说明无证据事实仍会被阻止进入形式化，但没有真正运行到新的 impact-ID 白名单，
不能据此宣称真实模型修复成功，也不能计算 P/I/V 准确率。原始失败保留在
`../../results/semantic/prompt_v33_smoke_01/`。

## 真实 smoke 结果二：只复用已验证要素进行形式化

新增 `--formalize-only` 受控入口后，复用上一轮已经通过证据校验的 GTE
`elements-ids.json`，只调用形式化一步：

- 模型正确把 claim `impact_ids` 写为已提取的 `imp_fok_fail`，没有再虚构
  `fok_fill_reverted`。
- coverage 行不再包含 schema 禁止的额外 `impact_id` 字段。
- 但模型同时为未放入 claim `impact_ids` 的 `imp_availability_reduced` 输出一条
  `unformalized` coverage，导致 coverage ID 集合大于 claim impact 集合。
- 校验器以 `impact coverage missing or duplicate` 拒绝，未进入 Z3。

这说明本次目标 ID 修复在真实第二步输出中有效，但 coverage 必须“恰好等于 claim
impact_ids”的约束仍需加强。该次单调用记录 11,625 tokens、估算 0.004758576；原始输出位于
`../../results/semantic/prompt_v33_formalize_only_01/`。

## 当前判断

标题去重与 ID 白名单本地逻辑正确，旧实验可复现；真实形式化已确认不再虚构 impact ID，
但 coverage 集合仍不合法，端到端状态仍是 `rejected`。`--formalize-only` 已可避免为验证
第二步重复消耗第一步调用。下一步应只增加 coverage 等式规则，不应放宽校验器或自动删除
模型多写的覆盖项。
