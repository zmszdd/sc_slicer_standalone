# 原始 report.json 的 P/I/V 完整性抽查

## 范围与判断口径

逐份读取本批 10 个盲测样本对应冻结数据目录中的 `report.json`，只依据原文，不把模型产物当成原始证据。

- **P**：导致/界定问题的先决状态、触发条件或操作。
- **I**：原文直接表达的预期规则/性质。明确的 NatSpec、标准要求、正文中的规范性陈述或推荐修复可以支持 I；仅凭漏洞后果反推则不算明确。
- **V**：原文直接声称或展示的错误行为/影响。

## 逐份结论

| 报告 | P | I | V | 原文层面的结论 |
|---|---|---|---|---|
| SukukFi `…35X8HSswRc6` | 明确：自授权 permit 已签发，任意地址调用 withdraw/redeem | 明确：NatSpec 写明调用者须为 owner 或获准 delegate | 明确：攻击者可烧掉受害者 shares 并收到底层资产 | **P/I/V 完整** |
| SukukFi `…NWyWHUbc8h8` | 明确：用户设 self-allowance 后，第三方可指定 owner 调用 | 明确：NatSpec/修复建议要求 owner 或授权 operator | 明确：可盗取用户及投资金库资产 | **P/I/V 完整**；影响项较多，但核心授权关系清楚 |
| SukukFi `…4xd9CjGVS2n` | 明确：存在未领取的 cancel-deposit 资产时尝试注销 vault | 在 mitigation 中明确要求移除该限制；正文解释 cancel 流程不依赖 ShareToken | 明确：一个用户不领取时，协议将无法注销 vault（DoS） | **整体可组成 P/I/V**；I 位于推荐修复，不在 Impact 段 |
| Monetrix `…5yjseW7eSkE` | 明确：用户提出有效 redeem 请求后，在 claim 前被 USDC 拉黑，escrow 已有资金 | **较弱**：原文提出 redirect-to-recipient claim 或 governor force-cancel/refund 两种恢复方案，但没有单独凝练成唯一的规范性 I | 明确：USDM、escrow USDC 和 obligation 被困，正常重试仍失败 | **P/V 明确，I 有修复意图但不唯一**；应保留为需审阅项，不宜强行造唯一 I |
| Hybra `…pG2nZWsvvjH` | 明确：NFT 带有 pending rewards 时 merge/split，且 operator 尚未 claim | 推荐“split/merge 前 claim”；预期保全奖励可由该修复直接支持，但原文没有单列 invariant 句 | 明确：用户奖励及 gHybr rebase amounts 丢失 | **P/V 明确，I 可由明确 mitigation 支持**；规则化时需标注 I 来源是修复建议 |
| SukukFi `…K8iEhnzEysb` | 明确：大量不同 controller 创建极小 redeem request，唯一 requester 超过 100 | 明确给出两种修复目标：限制最小请求额，或 view 返回至多 100 项而不 revert | 明确：`getActiveRedeemRequesters()` 总是 revert、不可用 | **P/I/V 完整**；有两种可选 I/修复路径，不能把它们误合成同一条规则 |
| Intuition `…deVmwC5DHi7` | 明确：在 epoch 边界建 lock，边界 checkpoint 被前一 epoch 的 inclusive snapshot 纳入 | 明确：mitigation 指定用 epoch end 前一时间点计算，使下一 epoch checkpoint 不进入上一 epoch | 明确：攻击者领取上一 epoch emissions 并稀释诚实质押者 | **P/I/V 完整**；I 在 mitigation 段 |
| Sequence `…vuyPaaLuUXu` | 明确：chain ID fork 后，部署时固定的 domain 与当前 chain ID 不同 | 明确：正文引用 EIP-712 动态重算建议，Recommendation 要求 chainid 变化时动态计算 DOMAIN_SEPARATOR | 明确：合法签名验证失败，协议功能被 DoS | **P/I/V 完整**；I 在标准说明/Recommendation 段 |
| SukukFi `…8j5nFX9rNe8` | 明确：非 owner 且无授权的地址调用 withdraw/redeem | 明确：NatSpec 明文 owner 或 allowance；mitigation 再次说明 | 明确：任意地址可未经许可提取 owner 资产 | **P/I/V 完整** |
| Monetrix `…jczYF4pgf3U` | 明确：PM account 同时有供给资产与借款负债，计算 backing 时漏减负债 | 明确：原文明说核心 peg-solvency invariant，并要求完整读取 borrow 和 supply、将负债纳入净 backing | 明确：phantom yield 被分发，USDM 实际 backing 短缺/资不抵债 | **P/I/V 完整** |

## 结论

严格说，**不是每份报告都在 Impact 小节里把 P、I、V 三项并排写全**。本批 10 份中，P 和 V 基本都在正文/Impact 中明确；I 经常出现在 NatSpec、标准要求或 Recommended Mitigation，而不是 Impact 段。多数报告可从全篇中找到明确的 I 来源，但有些 I 只以修复建议表达，正式规则化时应保留该证据位置。Monetrix blacklist 报告给出了两种恢复方案，I 的目标存在选择空间，宜人工确认，不应强行合并。

这说明“报告全篇有没有可用 P/I/V”与“Impact 段是否单独写全 P/I/V”是两个不同问题。当前这批运行保存的要素提示写着 `Read description/impact only`（见运行目录的 `prompt-element.txt`），若这一范围没有读到推荐修复/NatSpec/标准要求，就可能漏掉报告全篇明确存在的 I。遇到这种情况应先标明证据位置并复核来源范围，而不是直接断言原报告没有 I。
