# semantic-live-14 影响项提取盲测

## 设计

模型调用前冻结了 10 份未见报告，按 case ID、报告哈希和规范化输入哈希排除历史样本，选样时不检查 Impact 内容。运行使用 DeepSeek `deepseek-flash`、`semantic-live`、Impact 标注区域受限证据目录和新版逐字引用验证。

## 结果

| 指标 | 结果 |
| --- | ---: |
| 冻结报告 | 10 |
| 提取与规则化模型调用 | 91 |
| 候选检查通过 | 5/10 |
| 需复核 | 3/10 |
| 无明确影响，按规则停止 | 1/10 |
| 来源引用校验拒绝 | 1/10 |
| 已接受影响项 | 22 |
| 完整 P/I/V | 11/22 (50.0%) |
| 逐字来源通过的已接受清单 | 9/9 |
| 零调用离线重放 | 9/10 |
| 候选报告 P/I/V 盲审 | 5/5 报告被评为 weakened |
| 盲审要素评分 | 24 pass, 9 partial, 0 fail |

9 份产物可以离线重放。Merkl 报告被来源校验器拒绝，未形成可重放的完整产物。模型将 Impact 列表项改写为连续句子，但未保留原文中的 Markdown 加粗标记和列表编号；当前逐字验证器将该格式差异判为非原文。拒绝避免了无依据文本进入 P/I/V，同时也暴露了严格引用验证对报告排版格式敏感。

一份 GTE Perps 报告的标注 Impact 区域没有明确伤害结果，因此未生成影响项，状态为 `no_explicit_impact`。这符合提取边界。

只有 5 份候选通过检查，其中 4 份完成度不是全量；5 份均有已提取影响项未完成 P/I/V。盲审由与生成相同模型族的模型执行，只作诊断，不是独立金标准。

## 逐报告结果

| Case | 接受状态 | 影响项 | 完整 P/I/V | 清单状态 | 离线重放 |
| --- | --- | ---: | ---: | --- | --- |
| `Brix_Money_qy7NXr77sDh__cSNXN84Wruw__FbVYKzVY2hR` | candidate_checks_passed | 4 | 2/4 | extracted | 通过 |
| `Covenant_d4uY8y2AMSs__otmbJXz4irq__ffSdCEexDqm` | needs_review | 1 | 0/1 | extracted | 通过 |
| `Ekubo_3FTodhsvBkM__TuLiGdJaxpt__k5SrenN4Jx2` | needs_review | 3 | 0/3 | extracted | 通过 |
| `Forte__Float128_Solidity_Library_evjHaYmvKxh__kAkKE5sSeTR__zQc6QMa9DZ8` | candidate_checks_passed | 3 | 2/3 | extracted | 通过 |
| `GTE_Perps_and_Launchpad_gtn2Umg6KsC__Vn5w25BTWbt__5TcU23PtDdi` | needs_impact_review | 0 | 0/0 | no_explicit_impact | 通过 |
| `GTE_Spot_CLOB_and_Router_qa8y3zjgyCn__LDE4mUbttzn__hT8RvDaQYeY` | candidate_checks_passed | 3 | 3/3 | needs_review | 通过 |
| `Hybra_Finance_xo4hapwL2Jy__qoJkZFiWFds__PRixjGrBzGQ` | needs_review | 3 | 0/3 | extracted | 通过 |
| `Intuition_2VUsxVJwReb__aayBh4TiWVT__9zjimEyWcgY` | candidate_checks_passed | 3 | 3/3 | needs_review | 通过 |
| `Kinetiq_k8aVPPVguSE__9ghvAQQHVB2__bhjaby9ekJn` | candidate_checks_passed | 2 | 1/2 | extracted | 通过 |
| `Merkl_T4ExvutBBXC__kvqzFvQzjLT__thfmBytrnVT` | rejected | 0 | —/— | Impact inventory text must quote its cited Impact evidence verbatim | 未通过 |

## 结论

新版硬约束让已接受的影响文本都能回指标注 Impact 证据，并且能阻止格式化内容改写后进入结果；但目前代价是至少一份报告因 Markdown/编号差异被拒绝。下一步应保持来源限制，同时在确定性校验中仅规范允许的展示标记（列表序号、Markdown 粗体边界），然后用拒绝样例和新的冻结样本复测；不要放宽成语义相似或允许从其他章节补充。P/I/V 完整率约一半且盲审仍普遍发现弱化，公式忠实性仍是主瓶颈。

本轮与 live13 使用不同报告集，不能用两轮比例声称统计显著提升。

## 产物

- `SELECTION.json`、`manifest_01.json`、`manifest_02.json`：样本冻结清单。
- `runs/`：模型输入输出、证据、状态与 P/I/V 产物。
- `OFFLINE_REPLAY.json`：逐报告零调用重放结果。
- `FAITHFULNESS_CANDIDATES.json`：报告保真度诊断。
