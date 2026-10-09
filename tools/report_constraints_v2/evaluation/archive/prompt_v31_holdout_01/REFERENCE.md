# semantic-v3.1 留出集预先参考

状态：`assistant_preliminary_reference`，未经用户或独立专家确认。日期：2026-09-15。本文件在模型调用前依据报告 description/impact 编写，不读取 PoC、模型输出或旧案例答案，不发送给模型。

冻结 Prompt：`semantic-v3.1`；`semantic_prompts_v31.py` SHA-256：`8c661155868411f9c6668b25a4bd954d97ea9e8d28bfe996802e81323b71e331`。

沿用六维评分：范围/主体、核心 P、安全意图、正式 I、核心 V、限定/覆盖。取值 pass/partial/fail/not_evaluable；partial 不算完整通过。核心 I 必须语义、文字/AST、观察量、执行限定、类型/算子均正确。调用失败和超时留在分母；真正因 AST 不支持而明确 `null+unresolved` 才可记 not_evaluable。

## blackhole_circulating_supply

- P：`calculate_rebase` 在无符号数量上运行；报告的危险关系为 `blackTotal < veTotal + smNFTBalance`。若表达正常值，还需 `veTotal <= blackTotal` 等域条件，不可把 underflow 本身放进 P。
- I：circulating supply 应按一致的总量口径计算且不因漏计 smNFTBalance 发生下溢；报告建议对应核心数值关系可写为修正后 `circulatingBlack == blackTotal - veTotal`，并明确无符号域条件。
- V：错误式等价于 `blackTotal-(veTotal+smNFTBalance)`，可能下溢使 rebase DoS；未下溢时也可能错误估算 rebaseAmount。
- 边界：具体“50%”阈值与各余额关系未完整定义，不强造；DoS 是作者声称的条件能力。

## ekubo_transfer_event

- P：一次完成的 `transferFrom(from,to,amount)`，由 spender/msg.sender 代持授权执行；核心差异场景需 `msg.sender != from`。余额/allowance 是示例有效条件，可保留但不要扩成报告外协议规则。
- I：完成后 Transfer 事件的第一地址必须等于实际被扣款的 `from`，即 `transfer_completed => event_from == from_address`。
- V：余额从 Alice/from 扣除，但事件把 Bob/msg.sender 记录为来源；在两者不等时 `event_from != from_address`，下游 bridge 可能错记/错铸。
- 边界：事件错误 asserted；bridge 错铸是报告给出的下游影响，不需要把全部生态行为形式化。

## intuition_validity_window

- P：77-byte/带 suffix 的签名包含 signer 意图的 `validUntil/validAfter`； relayer 保留同一 65-byte ECDSA 签名并修改未签名 suffix，验证仍接受。具体攻击路径可简化为成功接受/执行具有被改窗口的 operation。
- I：执行必须处于签名者批准的时间窗口；可用 `operation_executed => now>=signed_valid_after && (signed_valid_until==0 || now<=signed_valid_until)`，其中 0 表示无上限只有在报告/接口约定支持时使用，否则列 unresolved。
- V：operation 在签名者 intended `validAfter` 之前或 `validUntil` 之后仍执行。
- 边界：malicious bundler 是能力；没有具体已发生交易或量化损失。不能用自由布尔量 `metadata_bound` 代替时间关系。

## monetrix_net_backing

- P：被读取账户存在 `borrow.value > 0`，0x811 同时返回 supply.value 和 borrow.value，消费者计算 backing。
- I：报告声称 backing 必须是 signed net，而非纯 supply；核心式可写 `reported_backing == supply_value - borrow_value`，并保持相同资产/USDC-notional 单位。
- V：实现只取 supply.value，因此 `reported_backing == supply_value`，相对净值恰好高估 `borrow_value`。
- 边界：不同资产借款需要 oracle 换算，当前 AST 无乘除/调用；只能在已经统一为 USDC-notional 的观察量上表达，否则 partial/unresolved。

## olas_twap_spot

- P：`elapsedTime > 0` 且执行 `validatePrice`；为避免当前 AST 的比例/乘除限制，核心可限定报告明确提到的 `slippage=0`，并观察独立历史 TWAP 与当前 spot。
- I：零容忍校验通过意味着当前 spot 与真实历史 TWAP 相等，即 `validation_passed => spot_price == historical_twap`。
- V：操纵使 `spot_price != historical_twap`，但错误计算令校验仍通过。公式自身的乘除推导可留作 root cause，不强行进入 P/I/V AST。
- 边界：即时操纵能力与保护失效为 asserted；具体 bad execution/value loss 为 potential，不能升级为既成损失。

## 防污染边界

模型只接收编号报告原文；第二次接收第一步要素及其引用片段。参考文件、PoC、旧输出和其他报告均不发送。原始候选失败不修补、不重试。v3.1 与 v3 使用不同报告，因此只能比较完成率趋势，不能作严格同集 A/B 或总体准确率声明。
