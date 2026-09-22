# semantic-v3 新 Prompt 真实留出集测评

日期：2026-09-15。状态：真实模型运行完成；评分为助手初评，尚未由用户或独立专家确认。

## 结论

新 Prompt 的**自然语言理解部分表现较好，但形式化生成目前不稳定**。

- 5 份未参与 Prompt 设计的真实报告，共 10 次模型调用，无重试。
- 第一阶段式的报告要素提取全部生成并通过结构、证据编号与原文回填校验。
- 排除 formal I 后，五个语义维度共有 25 个评分单元：严格 pass 22、partial 3、fail 0，严格通过单元率为 **88%**。
- 正式不变量 I：pass 1/5，即 **20%**；端到端正式化完成也是 1/5。
- 其余 4/5 均在第二次形式化调用中达到 240 秒超时，不是证据或 schema 校验拒绝。
- 唯一完成案例 Virtuals 的 I 为 `state_modified => caller_is_authorized`，V 为 `!caller_is_authorized && state_modified`，与预先参考语义对应；Z3 仅验证规范内部关系，不验证 PoC。

这里的 88% 是助手对 25 个定性单元的初步严格评分，**不是总体准确率，也不是 88% 的报告能够直接进入第三阶段**。当前对第三阶段真正关键的端到端可用率只有 20%。

## 分报告结果

| 报告 | 要素提取五维 | 正式 I | 管线结果 | 主要问题 |
| --- | --- | --- | --- | --- |
| Upside dust fee | 3 pass / 2 partial | fail | timeout | P 缺少正 amount/rate 的完整限定；重复能力模态偏强；未能正式弃权 |
| Virtuals updateImpact | 5 pass | pass | needs_review | 核心公式正确；授权角色和下游影响仍未知，需人工审核 |
| Morpheus past lock | 5 pass | fail | timeout | 要素与隐含安全意图正确，第二步未产出 |
| Forte `le` equality | 5 pass | fail | timeout | 正确区分数值相等与表示相等，第二步未产出 |
| Covenant self-transfer | 4 pass / 1 partial | fail | timeout | P 未完整固定正出金额/全部有效调用条件，第二步未产出 |

逐项理由和原始候选哈希见 [ratings.json](ratings.json)，冻结前参考见 [REFERENCE.md](REFERENCE.md)，可重放指标见 [metrics.json](metrics.json)。原始模型结果位于 `../../results/semantic/prompt_v3_holdout_model_01/`。

## Prompt 实际帮助

与之前发现的错误相比，本轮第一步明显具备这些能力：

- 能从报告中自行推出 `security_intent`，而不是只抄根因或坏效果。
- 能区分数值相等与 packed 表示、未授权修改与潜在下游损害、直接状态失配与后续 DoS。
- 能保留未知授权角色、缺失具体输入和未观察 incident 等歧义。
- Virtuals 正确采用可观察的调用授权/状态修改变量，没有用一个布尔量替代整个安全性质。

但 Prompt 从旧版约 2,044/4,880 字符扩展到约 4,472/8,320 字符后，模型第一步输出也很长；第二步还输入完整要素和全部证据。四份报告因此未在固定时间内返回，说明当前设计规则覆盖较全、生成负担过重。

## 成本与边界

十次调用中只有五次要素调用和一次成功正式化调用保存了 usage，共记录 60,958 tokens、模型返回估算成本 0.02512711；四次超时调用没有 usage 文件，因此总 token/费用未知，该数字不是账单总额。

本批是定向选择的 5 份短报告，不是随机总体。参考和评分均为助手初评。旧 Prompt 的 40% 核心 I 数据来自另一批报告，不能与本轮 20% 作严格因果 A/B；只能确认 v3 当前端到端稳定性不足。

本轮没有向模型提供 PoC、参考答案、旧输出或第一阶段结果，没有修改第一阶段、Rust/Solar、`run.sh` 或底层验证逻辑，也没有作 PoC/报告一致性结论。

归档后完整本地回归为 **151/151 通过**；受保护文件检查为 **74/74 未变化**。

## 下一步建议

先做 v3.1 的**输出预算化**，不增加新工具：

1. 第一调用仅保留一个核心攻击路径、一个核心安全意图和直接影响；限制实体与 statement 数量，把下游影响压到 limitations。
2. 第二调用只传核心 statement、其证据片段和允许的 AST schema，不再回传完整报告目录。
3. 要求只生成一个 core claim；无法用当前算子表达时立即返回 `null + unresolved`。
4. 本地回归后，再用一组新的 5 份报告测试；不要在本批上反复调参后宣称泛化提升。

后续状态：上述预算化方案已在本地实现为 [Prompt v3.1](../../docs/PROMPT_V31_REPORT.md)，但尚未对外部模型复验；本报告中的 v3 原始成绩保持不变。

离线重放（零模型调用）：

```bash
cd /root/sc_slicer_standalone/tools/report_constraints_v2
/root/.local/share/uv/tools/halmos/bin/python \
  evaluation/prompt_v3_holdout_01/evaluate.py
```
