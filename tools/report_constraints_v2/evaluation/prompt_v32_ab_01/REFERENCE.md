# semantic-v3 与 v3.2 同输入 A/B：预先参考

日期：2026-09-15。状态：`assistant_preliminary_reference`，未经用户或独立专家确认。

本参考在任何模型调用前依据三份报告的 description/impact 编写。三份报告未用于 v3/v3.1 测评，也未进入 v3.2 的五案例开发参考集。模型不接收本文、PoC、代码、推荐修复或历史答案。

## sukuk_unauthorized_withdraw

- P：受害者已存入资产且存在协议正常运行需要的 self-allowance；外部调用者不是 owner，且未取得 owner 对调用者的足额授权；调用者指定受害者为 owner、自己控制的地址为 receiver。
- I：从 owner 扣除份额并完成资产提取时，调用者必须是 owner，或者具有 owner 对调用者的足额 allowance。
- V：未经 owner 授权的外部调用者仍完成 withdraw/redeem，烧毁受害者份额并将其资产发送到攻击者接收地址。
- 模态：报告将可盗取资金表述为 asserted capability；没有声称链上已经发生盗窃事件。
- 核心关系：`withdraw_completed -> caller_is_owner or caller_allowance_sufficient`；V 必须包含完成和两种授权均不成立。

## hybra_uninitialized_maturity

- P：用户有正余额并请求正数额提款；存款后 `maturityTime[user]` 仍为默认 0；用户在预期锁定期结束前立即提款。
- I：提款完成意味着当前时间已经达到该用户应有的 maturity time。
- V：用户在应有 maturity time 之前仍完成提款。`maturityTime == 0` 是实现原因/实际错误状态，不能用它把 intended maturity 的约束平凡化。
- 模态：立即提款能力 asserted；进一步 flash-staking/reward attack 为 potential 下游影响，应分开或延后。
- 核心关系：`withdraw_completed -> current_time >= intended_maturity_time`；V 为完成且 `current_time < intended_maturity_time`。报告没有给出锁定时长，intended maturity 与代码绑定应标 inferred/unresolved。

## gte_fok_dust

- P：订单类型为 FOK；撮合后仅剩由 lot-size rounding 产生的正 dust，且 `remaining_amount < lot_size`。
- I：在该 dust 条件下，订单不得仅因仍有未成交量而触发 `FOKOrderNotFilled` 回退。它不保证交易因其他原因一定成功。
- V：实现因任意 `remaining_amount > 0` 触发该特定回退，因此合法 dust FOK 订单被拒绝。
- 模态：特定回退和可用性破坏均为 asserted；没有具体资金损失。
- 核心关系：`is_fok and 0 < remaining < lot_size -> not fok_unfilled_revert`；V 必须表达同一 dust 条件下发生该特定回退。

## 评分维度

逐案例比较：范围/主体、P 完整性、P 无结果污染、自然语言 I、正式 I、V 直接反例、模态/限定。`partial` 不计为完整通过。超时和结构失败留在分母。

本批只有三例，是针对 P 与 V/I 关系的定向小实验，不估计总体准确率。A/B 只比较同一输入上的候选质量和管线成功情况；模型生成随机性仍是限制。

