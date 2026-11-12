# binding.json 规范

一个案例一个 `binding.json`，按 claim 给出每个符号的代码侧可观测表达式。

```json
{
  "schema_version": "stage3-binding/1",
  "claim_id": "impact_claim_...",
  "bindings": {
    "<symbol>": {
      "kind": "boolean_predicate | address_value | numeric_value",
      "solidity_expr": "balances[msg.sender]",
      "checkpoint": "before | after | input",
      "source": "Vault.sol:withdraw"
    }
  },
  "probe": {
    "contract": "Vault",
    "exploit_test": "test_double_withdraw",
    "safety_test": "test_single_withdraw"
  }
}
```

规则：

- `claim_id` 必须存在于 `stage3-spec.json`。
- `bindings` 必须覆盖 `binding_contract` 中所有 `appears_in` 非空的符号。
- `solidity_expr` 是 Solidity 表达式，不得是报告原文。
- `checkpoint` 必须与阶段二符号的 checkpoint 语义一致；before 值在动作前快照。
- `probe.exploit_test` 是“原始通过、补丁失败”的 PoC 测试名；
  `probe.safety_test` 是“原始/补丁都通过”的正常路径测试名。
