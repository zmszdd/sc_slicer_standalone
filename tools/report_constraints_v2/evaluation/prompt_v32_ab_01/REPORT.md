# semantic-v3 与 v3.2：P/V 优先改进真实 A/B 测试

日期：2026-09-15。三份新报告；同一模型、同一输入、相同并发和 240 秒超时；无重试。参考在模型调用前冻结，未经用户或独立专家确认。

## 结论

`semantic-v3.2` **明显改善了本轮管线完成率，但尚未证明 P/I/V 准确率提高**。

| 指标 | semantic-v3 | semantic-v3.2 |
| --- | ---: | ---: |
| 报告数 | 3 | 3 |
| 尝试调用数 | 4 | 6 |
| 超时案例 | 3/3 | 0/3 |
| 完整形式化管线 | 0/3 | 3/3 |
| Z3 `P∧V∧I=UNSAT` 门槛 | 不可评价 | 3/3 |
| P 完整性严格通过 | 已产生要素中 1/1 | 1/3 |
| P 角色纯度严格通过 | 已产生要素中 1/1 | 0/3 |
| 自然语言 I 严格通过 | 已产生要素中 1/1 | 3/3 |
| 正式 I 严格通过 | 0/3 可评价 | 0/3 |
| 语义 V 直接反例严格通过 | 已产生要素中 1/1 | 2/3 |
| 七维全部通过 | 0/3 | 0/3 |

v3 的 Sukuk、Hybra 在第一步超时，GTE 在第二步超时；因此不能把 v3.2 的差异完全归因于 Prompt。v3.2 的六次调用均完成，记录 76,470 tokens、估算 0.03476925；超时调用可能已有未记录消耗，所以两组成本不能完整比较。

## v3.2 分案例

### Sukuk 未授权提款

- 好：主体、受害者存款、self-allowance、`caller != owner`、窄授权意图和未授权支出 V 均被识别；V 对生成的 I 是直接反例。
- 问题：遗漏“caller allowance 不足”这一明确条件；把 arbitrary-owner 接口、只检查 self-allowance 等实现原因标成 P。
- 正式 I 使用未展开的 `caller_authorized` 布尔量，没有表达报告给出的 `caller == owner OR allowance >= shares`。
- 把报告声称的攻击能力从 asserted 降成 potential，模态不准确。

### Hybra maturity 未初始化

- 好：自然语言 I 正确说出提款应等到 maturity；即时提款与潜在 flash-staking 被分开。
- 问题：P 主要是“检查存在、mapping 未初始化、默认零”等实现原因，`deposit_capable` 也不等于“用户已经存款”。
- 正式 I 错写成 `withdraw_completed -> maturity_time > 0`；正确核心应是 `withdraw_completed -> current_time >= intended_maturity_time`。
- V 正好否定错误 I，因此 Z3 门槛通过。这证明关系门槛只能验证候选内部一致，不能证明 I 忠实于报告。

### GTE FOK dust

- 好：dust 场景、特定 `FOKOrderNotFilled` 回退、安全意图和直接 V 均正确，机械关系门槛通过。
- 问题：把“用户不为 dust 付费”这一并列期望当成 P，并加入 I 的前件。这会把原本的“只剩 dust 就不应回退”弱化成“只剩 dust 且未收费时才不应回退”。
- 因报告正文没有精确数值阈值，使用 `only_dust_unfilled` 只能作为待绑定观察量，不能宣称已经形成精确数值公式。

## 对优先路线的判断

1. **V/I 方向取得局部进展**：三份 v3.2 候选的 Z3 直接关系均成立，人工语义审核有两份 pass、一份 partial。
2. **P 仍是首要瓶颈**：模型为了“完整”把实现原因和期望结果塞入 P；自动的 `unassigned_precondition_ids` 只能防止第二步漏用，不能修复第一步错分类。
3. **不能继续只强化 `V => not I`**：否则会出现 Hybra 这种“先写错 I，再正确否定错 I”的机械成功。

下一版只应做两个小改动：第一步增加逐句角色判定，明确静态实现缺陷属于 root_cause、并列期望属于 security_intent；第二步在关系检查之前增加 I 文本与 AST 的关系槽位检查，特别核对比较双方、检查点和 implication consequent。暂不扩展复杂不变量或 AST。

原始输出位于 `../../results/semantic/prompt_v32_ab_01_v3/` 和 `../../results/semantic/prompt_v32_ab_01_v32/`。评分见 [ratings.json](ratings.json)，冻结材料见 [FROZEN_INPUTS.json](FROZEN_INPUTS.json)。

