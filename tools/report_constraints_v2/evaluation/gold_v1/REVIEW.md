# 阶段二真实报告金标准审核卡

状态：助手草案，尚不是金标准。请直接把认可项的 `[ ]` 改成 `[x]`；任何一项不确定时保持
未勾选并修改 `gold.json`。五个案例共 25 项全部确认后，才能生成 `approved-gold.json`。

## 1. panoptic_builder_init

- P：钱包已有 `builderAdmin`；任意未授权调用者调用 `init` 试图替换管理员。
- I：管理员配置后，未授权的 `init` 不能改变它。
- V：未授权调用者成功调用 `init` 并覆盖 `builderAdmin`。
- 次级影响：随后 sweep builder fees，不并入核心 V。

- [ ] P 完整且没有混入结果。
- [ ] I 的方向、强度和范围正确。
- [ ] V 是 I 的直接违反。
- [ ] 次级影响处理合理。
- [ ] 无必须记录的 unresolved。

## 2. sequence_domain_fork

- P：当前 chain ID 与部署时不同；用户生成并提交当前链签名。
- I：当前链的签名验证应使用绑定当前 chain ID 的 EIP-712 domain。
- V：合约继续使用旧 domain，导致当前链签名无效并阻断 intent 流程。

- [ ] P 完整且没有混入实现结果。
- [ ] I 没有被错误强化为“任何签名都必须成功”。
- [ ] V 是当前 domain 不匹配导致的直接违反。
- [ ] DoS 作为下游影响处理合理。
- [ ] 无必须记录的 unresolved。

## 3. intuition_pause_escrow

- P：暂停标志已经设置；调用者调用列出的继承状态修改入口之一。
- I：暂停期间这些核心 escrow 状态修改不能完成。
- V：暂停期间某个列出的入口仍完成状态修改。

- [ ] P 包含 pause 和具体入口调用。
- [ ] I 范围仅限报告列出的核心状态变化。
- [ ] V 是 I 的直接违反。
- [ ] reward 影响作为次级后果处理合理。
- [ ] 无必须记录的 unresolved。

## 4. olas_permissionless_sweep

- P：burner 持有 buyback 所需 second-token；未授权调用者在 keeper buyback 前调用 transfer。
- I：清空 buyback inventory 的 sweep 必须要求授权调用者。
- V：未授权 sweep 成功，库存归零，keeper buyback 随后回退。
- unresolved：报告未明确命名应获授权的具体角色；这是非阻塞说明。

- [ ] P 完整且没有把 ZeroValue 回退当前提。
- [ ] I 的权限方向正确。
- [ ] V 是 I 的直接违反并保留后续回退。
- [ ] griefing/cadence 作为次级影响处理合理。
- [ ] `ambiguous_actor` 应为非阻塞 unresolved。

## 5. gte_fok_dust

- P：FOK；余量为 lot-size rounding dust；`0 < remaining < lot_size`。
- I：该条件下不能仅因正余量触发 `FOKOrderNotFilled`。
- V：同一 dust 条件下触发该特定回退。

- [ ] P 包含 FOK、正余量和小于 lot size。
- [ ] I 只禁止该特定原因的回退，不保证交易无条件成功。
- [ ] V 是 I 的直接违反。
- [ ] availability 作为次级影响处理合理。
- [ ] 无必须记录的 unresolved。

## 批准命令

全部确认后运行：

```bash
python3 tools/report_constraints_v2/evaluation/gold_v1/approve_gold.py \
  --reviewer YOUR_NAME
```

该命令不会修改草案，只会创建带草案哈希和审核人信息的 `approved-gold.json`。
