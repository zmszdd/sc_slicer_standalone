# semantic-live-15：真实报告盲测（10 份）

## 运行条件

- 从冻结的 1,568 份精确提交报告集中，按未使用的 case ID、原报告哈希和 report-input 哈希抽取 10 份；选择规则与哈希记录见 [`SELECTION.json`](SELECTION.json)，案例分为两个五例清单。
- 测试版本为 `semantic-live-15`，默认输入策略 `report-json-input/5`，DeepSeek Flash 串行运行；readiness、要素和公式阶段各允许一次重试，继续执行 review 状态。模型没有收到参考答案。
- 新增输入策略允许报告正文中的推荐修复作为潜在 I 证据；Impact 仍只从明确标注的 Impact 区域提取，且需引用该区域原文。
- 每个运行目录随后用 `verify` 离线重放；没有额外模型调用。

## 结果

| 报告 | Impact 项数 | P/I 来源判定 | 规则化通过 | 候选门 |
|---|---:|---:|---:|---|
| Brix Money `…MKMkLQCQdEN` | 3 | 3 selected | 0 | needs_review |
| Ekubo `…AQB7XkKMuow` | 3 | 1 selected，2 explicit_but_insufficient | 1 | candidate_checks_passed |
| Forte Float128 `…ZBFXjBXfyR2` | 2 | 2 selected | 0 | needs_review |
| GTE Perps `…xP5kuw2wBsv` | 4 | 4 selected | 2 | candidate_checks_passed |
| GTE Spot `…ndavqtk5vRc` | 5 | 3 selected，2 explicit_but_insufficient | 0 | needs_review |
| Hybra Finance `…nVjdnogBPTM` | 3 | 2 selected，1 explicit_but_insufficient | 0 | needs_review |
| Intuition `…xCkRvABHXC4` | 4 | 2 selected，2 explicit_but_insufficient | 0 | needs_review |
| Kinetiq `…7tVr98jQuEc` | 2 | 2 selected | 0 | needs_review |
| Merkl `…JdnfEeMGsvL` | 3 | 3 selected | 2 | candidate_checks_passed |
| Monetrix `…BqP968JWuuF` | 3 | 3 selected | 1 | candidate_checks_passed |
| **合计** | **32** | **25 selected，7 explicit_but_insufficient** | **6** | **4/10** |

10/10 报告通过 readiness，均找到明确标注的 Impact 区域；清单提取出 32 条原文影响项。适用性判定选中 25 条有 P/I 来源候选；另外 7 条因没有直接适用的明确 I 而标为 `explicit_but_insufficient`，按用户确定的口径不放进完整 P/I/V 规则化成功率分母。

以这 25 条**模型判定的完整来源候选**作暂定分母，6 条通过规则化及候选检查，即 6/25（24%）。另有 19 条来源候选未形成通过规则，其中 12 条遇到 schema/validation 问题、3 条是证据或影响覆盖对齐问题、2 条语义忠实度审查失败、2 条公式构造失败。4/10 报告至少有一项规则通过；其余 6 份报告未通过候选门。候选门是工程检查，不是独立语义金标准；25 项分母尚未由独立评审逐项认证。影响项有重叠风险，尤其 GTE Perps 的“奖励留在 Launchpad / 用户得到 0 / 奖励无法转出”几条可能需要合并为更少的主要结果，因此 32 条原始清单不是独立影响项金标准。

## 输入策略 v5 的实际作用

10/10 份报告都含推荐/修复章节。与同一报告按策略 v4 构造的输入相比，v5 分别多纳入 94–832 字节的正文，共 3,115 字节。18 条 I 候选引用了只在 v5 新纳入部分出现的证据，覆盖全部 10 份报告。例如 Brix 的“仅授权角色可触发 rebalance”与“保留最低链上缓冲”来自推荐修复；Ekubo 的“开始时间检查应先于 duration 计算”也来自修复建议。由此可以确认，扩大 I 证据范围已在真实报告上生效。

这并未让公式主链变稳定：25 条被选中的来源候选中仅 6 条通过。未完成项主要卡在计划字段校验、修复字段漂移、影响变量来源对齐和谓词构造；不能把结果归结为缺少 I 文本。

## 重放与调用

- 10/10 个运行通过零模型调用 `verify`，每个结果均报告 `offline_verified: true`、`model_calls: 0`。
- 共执行 106 次外部模型调用；每五例批次的预算上限为 360 次。没有将预算上限误报为实际调用数。
- `consistency_verdict` 均为 `not_evaluated`。通过候选门不等于已与合约执行一致，也不表示模型生成的自然语言语义全部正确。
- 盲测完成后，全量测试发现并修正了 live Prompt 标签的兼容别名、重放 Prompt 检查和确定性拒绝分类；没有更改本轮模型请求文本、生成提示或已经保存的候选。修改后 458/458 回归通过，10/10 产物再次零调用重放通过。

## 与前批结果的边界

上一批 `prompt_live27_impact_applicability_blind_10` 使用 semantic-live-14 和输入策略 v4，候选门通过 3/10、原始清单 27 项、8 项规则化。本批是不同的 10 份报告，结果为 4/10、32 项、6 项规则化。由于样本不同、且前批 27 项尚未按 P/I/V 完整来源逐项核定，不能据此宣称语义效果提升或下降。当前能确认的是：v5 纳入了新的 I 证据；规则生成仍不稳定。

## 结论

策略 v5 达成了“可以从报告正文明确修复建议中找到 I”的输入目标。当前瓶颈已移到逐影响公式构造和局部修复的稳定性，同时影响清单的去重/主要性仍需独立审查。后续评测应继续分别记录影响覆盖、经独立核对的完整 P/I/V 合格项、以及合格项规则化通过数，不把缺 I 的项目混入成功率分母。
