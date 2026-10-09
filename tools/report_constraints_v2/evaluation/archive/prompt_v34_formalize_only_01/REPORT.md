# semantic-v3.4 coverage 等式复验

日期：2026-09-16。目标是修复 v3.3 真实输出中 coverage 集合大于 claim
`impact_ids` 的问题。v3.3 保持不变，新建 v3.4，只增加以下生成规则：

```text
set(effect_coverage.statement_id) == set(claim.impact_ids)
```

每个 claimed impact 恰好一行；未认领影响只能写入 limitations，不能生成 coverage。
校验器没有放宽，也没有自动删除模型输出。

## 本地结果

- v3.4 已独立注册并使用 v3.3 的 statement-ID 白名单。
- `--formalize-only` 复用已通过证据校验的 GTE elements，只需一次第二步调用。
- 专项测试 9/9 通过；随后完整阶段二测试 188/188 通过。
- 冻结的 v3.2/v3.3 文件和历史结果未改写。

## 真实结果

使用 `opencode-go/deepseek-v4-flash` 对 GTE 已验证要素进行一次形式化调用。模型在 240 秒
上限内未返回候选，状态为 `TimeoutExpired`；无自动重试、无候选修补、无 usage 文件。

因此只能确认本地编排和规则已经接入，不能评价真实模型是否遵守 coverage 等式，也没有
进入 SMT/Z3。准确状态是 `not_evaluated`，不是成功或语义失败。

原始输出位于 `../../results/semantic/prompt_v34_formalize_only_01/`。
