# semantic-v3.5：模型选择、程序合成

日期：2026-09-16。目标是把模型职责缩减为语义选择，把机械结构交给程序。

## 实现

第二步模型只返回 `report-formal-plan/1`：

- 选择的 P、I、V statement IDs；
- 最多 8 个可观察符号及来源；
- P predicate 绑定；
- 一个通用逻辑构造：condition forbids/requires effect、effect requires authorization，
  或 state preservation；
- assumptions、unresolved 和 limitations。

`plan_synthesizer.py` 确定性生成 AST、claim、精确 coverage、formula_sources、来源证据和
未认领影响 limitations。之后仍由原校验器和 Z3 检查，不自动修补语义选择。

## 本地验证

- 四类逻辑构造均生成类型正确的 Boolean I/V。
- 非法 impact ID 在生成正式约束前被拒绝。
- coverage 集合由程序生成，严格等于 selected impact IDs。
- 合成控制满足 `P AND V AND I = UNSAT`、`P AND V AND NOT I = SAT`。
- 模型计划、程序正式化和离线重放三者可相互核验。
- 阶段二完整测试 193/193 通过。

## 外部验证状态

计划复用已验证的 GTE 要素，只调用 `opencode-go/deepseek-v4-flash` 一次。安全审查因报告
语义可能属于未公开数据而拒绝外发；调用未启动、数据未发送。真实模型效果因此是
`not_attempted_permission_blocked`，不是超时、失败或成功。

完成真实评测需要用户明确确认：允许将该 GTE 报告筛选后的自然语言及已提取要素发送到
`opencode-go/deepseek-v4-flash`，仅用于一次 v3.5 形式计划生成。
