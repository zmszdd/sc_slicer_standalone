# semantic-live-14 适用性判定盲测

## 设计

- 从 1,568 份冻结报告中按固定 SHA-256 排序选出 5 份；排除已有评测 manifest 及前两轮实现调试中已运行的报告。完整名单冻结在 `manifest.json`。
- 模型：DeepSeek Flash；Prompt：`semantic-live-14`；串行运行。每份最多允许 1 次 readiness 重试、1 次要素重试和 1 次公式修复重试。
- `batch-summary.json` 记录 `reference_answers_provided_to_model: false`。本轮没有使用参考答案，也没有进行对照组运行。

## 结果

| 报告 | 端到端结果 | 影响项 | 适用性判定 | 规则化结果 | 模型调用 |
|---|---|---:|---|---|---:|
| SukukFi `…rjL9FdNnrCk` | `needs_impact_review` | 0 | 未运行；影响清单待审 | 未尝试 | 3 |
| Intuition `…wC4QDwrRjko` | `excluded_before_extraction` | — | 未运行 | 未尝试 | 1 |
| Olas `…eQ6JLM2YprU` | `candidate_checks_passed` | 2 | 2 selected | 1 个候选、1 个未规则化 | 10 |
| Intuition `…Bqc899ejHRp` | `rejected` | — | 未运行 | 影响摘录未通过逐字来源校验 | 3 |
| SukukFi `…c3gncNUSyd3` | `needs_review` | 2 | 2 `explicit_but_insufficient` | 0 | 3 |

共识别 4 个影响项：2 个选中 P/I，2 个因没有明确 I 而跳过公式生成。5 份报告中 1 份通过工程候选门（20%）；4 个影响项中 1 个形成候选（25%）。实际共调用模型 20 次，批次上限为 190 次。没有报告达到完整影响覆盖；整体语义准确率未测。

适用性行为与目标一致：Covenant 不在本轮留出集。最终样本中，SukukFi 的两个明确影响没有可用的非推断 I，因而没有为其生成公式；Olas 的两个影响分别选择了直接关联的明确 I。Olas 是唯一达到候选门的报告。

对 Olas 候选作了人工抽查：选中的“poisoned baseline”影响、TWAP/oracle 条件和偏差检查意图都能追溯到列出的报告证据。不过报告把 TWAP 过期与 oracle 查询失败列为两个触发条件，生成的 P 又把两者合取；这可能漏掉单一条件触发的情形。因此该候选只是工程候选，不能据此称为语义忠实。

## 零调用重放

3 份有可复验产物的运行通过 `main.py verify`，均为 `offline_verified: true`、`model_calls: 0`；其中包括 Olas 候选、SukukFi 的显式影响但缺少 I，以及一份空影响清单。另两份在输入筛选/影响摘录阶段停止，没有生成 `elements.json`；当前 verifier 对这类不完整运行报 `FileNotFoundError`，所以未计为重放通过。

## 结论与边界

这次测试支持一个有限结论：显式 I 不适用于某个影响或不存在时，新判定会让该项停止在公式生成前；可选中的来源能进入后续单影响请求。端到端效果仍不稳定：5 份仅 1 份通过候选门，另外 4 份分别被入口门、影响来源校验或 P/I/V 完整性阻断。单批 5 份、没有配对旧版基线，也没有独立盲审评分，不能据此宣称比旧版准确率更高。

本轮评分只包括上表冻结的 5 份。此前调试运行 `prompt_live24_*`、`prompt_live25_*` 发现并修复了适用性理由长度上限和空 `scope.flow` 两个实现问题，不纳入本轮结果。
