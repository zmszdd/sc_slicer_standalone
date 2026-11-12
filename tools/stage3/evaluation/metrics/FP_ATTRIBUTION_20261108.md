# FP 口径归因表（全量 invalid 普查，2026-11-09）

判例 invalid 全量普查：91 例中 **75 例可评测**（13 例阶段二阻塞、3 例未到阶段二）。
可评测 invalid 中 **15 例被主线复现（FP）**，FP 率 **15/75 = 20.0%**。

根因不变：阶段三裁决“代码是否违反形式化不变量 I”，不是“报告是否真漏洞”。判例
`invalid` 的 finding 被主线忠实复现其不变量违背，在“真漏洞口径”下计 FP。
15 个 FP 全部归因口径错位，**未发现 binding/probe/compile 机制性误报**。

## 关键发现：FP 高度集中在单一报告家族

15 个 FP 中 **12 个是 SukukFi「vault 注销 dust/捐赠 DoS」变体**（同一底层代码属性：
转入 dust/捐赠资产可阻塞 `unregisterVault`）。其余 3 个为 GTE 2 例 + SukukFi 偿付规则 1 例。
即：FP 率 20% 不是均匀分布，而是被一个代码级问题家族放大。

## 15 个 FP 清单

| # | 案例 | 判例标题（invalid） |
|---|------|--------------------|
| 1 | SukukFi `eJytFti7FNb__yobHFACVbAH` | Dust 转账 DoS 阻止 Vault 注销 |
| 2 | GTE Perps `ajDovMJcy4Z__YrXwPeSsimz` | 盘口偏离带外时清算停滞 |
| 3 | GTE Perps `xK7NZycdpFR__wcadjiLKTWZ` | Launchpad 奖励从池余额支付 |
| 4 | GTE CLOB `EXx2KHrPZfx__DtY9gGhmWN6` | 过期订单清理失败致资金锁定 |
| 5 | SukukFi `A78JaZeDQAg__5KXgCEAVocF` | 缺少链上偿付/损失处理规则 |
| 6 | SukukFi `7gXLhGcETg4__2mSX6c75bFA` | `unregisterVault` 未完整实现 |
| 7 | SukukFi `6fdjyFwscLe` | Zero-Cost Vault 注销 DoS |
| 8 | SukukFi `Kx3vZpduYVc` | 前置跑+转入资产 DoS `unregisterVault` |
| 9 | SukukFi `v7L9MfaQfqJ` | 前置跑 `unregisterVault` 致 DoS |
| 10 | SukukFi `4BQSmkwiXf4` | 捐赠攻击永久 DoS Vault 注销 |
| 11 | SukukFi `go6WTxic9yS` | 永久阻止全部 Vault 注销 |
| 12 | SukukFi `4ECPc7LoTkm` | Dust 存款 griefing Vault 注销 |
| 13 | SukukFi `zbittuS4KWd` | Dust 攻击永久 DoS `unregisterVault` |
| 14 | SukukFi `QUxuGoHzZcW` | 发送 Dust 阻止 Vault 注销 |
| 15 | SukukFi `htv6vNdTbfQ` | Dust 捐赠 DoS Vault 注销 |
