# semantic-v3.1 错误一致性复测：预先参考

状态：`assistant_preliminary_reference`，未经用户或独立专家确认。日期：2026-09-15。模型调用前仅依据五份新报告的 description/impact 编写；不读取 PoC、模型输出或其他案例答案，不发送给模型。

冻结 Prompt：`semantic-v3.1`；SHA-256：`8c661155868411f9c6668b25a4bd954d97ea9e8d28bfe996802e81323b71e331`。评分仍为范围/主体、P、安全意图、正式 I、V、限定/覆盖六维；partial 不算完整 pass。超时/调用失败留在分母。重点观察 v3.1 上批的 schema 缺失、模态升级、等式/义务弱化和 V 不保证 `not I` 是否再次出现。

## panoptic_builder_init

- P：BuilderWallet 已由工厂初始化或已有 builderAdmin；未经授权者再次调用未加 guard 的 `init`。若形式化盗取，还需要钱包持有 builder fees。
- I：已初始化钱包的 builderAdmin 不得被未经授权的再次 init 改写；可写 `admin_changed => caller_authorized`，或 `already_initialized && !caller_authorized => admin_after==admin_before`。
- V：任意调用者覆盖 builderAdmin，继而可通过受该地址保护的 sweep 取走累积费用。核心 V 应先表达未授权 admin 变化；盗币是后续条件效果。
- 模态：未授权覆盖与盗取能力由作者 asserted；具体已发生损失未报告。

## sequence_domain_fork

- P：当前 chain ID 与部署时不同，用户为新链/当前域生成签名并进入 intent 验证。
- I：验证使用的 EIP-712 域必须对应当前 chain ID；在不直接解码哈希时，可窄表达“当前域有效签名进入验证后不应仅因缓存旧 chain ID 被拒绝”。不得用无定义 `domain_is_current` 布尔量替代关系。
- V：immutable separator 仍绑定旧 chain ID，使新链签名验证失败并永久阻断相关 intent 流程。
- 模态：fork/change 条件下的 DoS 是 asserted 条件能力，不等于已经发生 fork。

## ekubo_swap_deadline

- P：用户提交 swap，交易在 mempool 被持有至用户认可的期限之后，随后尝试/完成执行；市场不利变化是影响条件，不是所有核心 I 必需。
- I：超过用户批准的 expiration/deadline 后，swap 不得完成；可写 `swap_completed => execution_time<=user_expiry`。虽然实现缺少 deadline 参数，该值可作为报告推导的规范输入，但必须标 inferred/unresolved for binding。
- V：被长期持有的交易在过期后仍执行；不利价格和损失是 potential 下游影响。
- 模态：缺少 deadline asserted；延迟执行/损失保持 can/potential，不升级为已发生。

## intuition_pause_escrow

- P：TrustBonding 的 paused flag 为 true，调用一个应受紧急暂停约束的继承 escrow mutator。核心优先 lock creation/modification；withdraw 是否故意保留存在报告明确歧义。
- I：暂停时这些敏感 escrow 状态转换不得完成，可写 `sensitive_state_changed => !paused`。
- V：paused=true 时 create_lock/increase 等状态仍可改变；运营者无法实际冻结 reward-relevant state。
- 模态：入口仍 live 是 asserted；具体 incident/损失未报告。withdraw 范围需限制或 unresolved。

## olas_permissionless_sweep

- P：buyback contract 持有非零 secondToken inventory；未经授权者在 keeper buyBack 前调用 permissionless `transfer(secondToken)`。
- I：移除买回所需库存的 sweep 必须由授权主体执行，可写 `inventory_removed => caller_authorized`；授权角色名称未知，不强造 owner/keeper。
- V：未授权调用将全部 secondToken 转到 treasury，使随后 buyBack 看到零余额并以 ZeroValue 回退。核心先表达未授权库存移除，后续回退为有序影响。
- 模态：grief/DoS 能力 asserted；“potentially preventing cadence”保持 potential，不冒充既成长期损失。

## 防污染边界

模型只收到编号原文；第二步只收到第一步要素和其引用片段。PoC、本文、旧输出、评分均不发送。每例最多两次调用、无重试、失败不修补。此批检验错误是否再次出现，不估计总体准确率；即使重复出现，也只是小样本一致性证据。
