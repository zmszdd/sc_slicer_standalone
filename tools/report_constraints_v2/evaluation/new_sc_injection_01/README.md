# new-SC 注入原型（方案①：PoC 钩挂 + Foundry 机械裁决）

## 目的

验证"阶段二规则化结果 + 阶段一切片 → 新 SC → 阶段三机械检验"闭环的最小可行版本：
确定性地把 stage-2 的 P/I/V 公式（constraints.json，与 Z3 查询同源）翻译成
Solidity 断言测试，挂到已复现通过的 PoC 切片上，用 forge 跑出四分支裁决，
再经既有 `stage3-feedback` 通路落盘 `stage3-consistency.json`。

**零模型调用**。绑定映射（`bindings/ekubo.json`）是本原型的手工输入
（stage-3 侧绑定工作的替代物），如实披露，不属于阶段二产物。

## 预注册判读表（运行前冻结）

guard 测试只输出一行 `STAGE2_VERDICT {"p":..,"i":..,"v":..}`（P/I/V 在
绑定代码上的实际取值），**测试本身只在绑定不可能时失败**——I 被违反是
预期的好消息，不是测试失败。判读：

| p | i | v | 裁决 | 含义 |
| --- | --- | --- | --- | --- |
| true | false | true | **violation_reproduced** | 报告主张在代码层机械证实 |
| true | true | true | i_too_weak | I 应违反而未违反 → 阶段二 I 推导/绑定错 |
| false | * | * | precondition_mismatch | 阶段二 P 与代码现实不符（P 或绑定错） |
| true | * | false | violation_not_observed | PoC 通过但 V 观察量未见 → 绑定错 |

## 工件

- `bindings/ekubo.json`：符号 → Solidity 表达式绑定 + setup/attack/post 代码段
- `inject.py`：确定性注入器（读 live4 Ekubo run 的 constraints.json +
  绑定映射 → 生成 guard 测试、foundry.toml、injection-map.json、sc-spec.json）
- `new_sc__Ekubo.../`：新 SC（原切片原样复制 + 注入物；不覆盖任何既有目录）
- `run_injection.sh`：forge 运行 + 判读 + 映射为 stage3 一致性反馈 + ingest
- `run_copy__Ekubo/`：live4 Ekubo run 的副本（smoke 纪律：ingest 只写副本，
  冻结 run 永不被改写）

## 预期（Ekubo：Transfer 事件 source 错误）

- P：`spender != from ∧ transferFrom 已调用` → true
- I：`(event_emitted ∧ spender != from) ⇒ event_source == from` → **false**
  （缺陷合约的事件 from 用的是 msg.sender/operator）
- V：`... ∧ event_source != from` → **true**
- 期望裁决：violation_reproduced，随后 ingest 落盘
  `consistency_verdict: violation_reproduced`。

## 结果（2026-10-08 运行）

| 项 | 结果 |
| --- | --- |
| guard 测试 | PASS（原 PoC 测试在新 SC 中也原样通过——切片完整性保持） |
| STAGE2_VERDICT | `{"p":true,"i":false,"v":true}`（与预注册预期逐项一致） |
| 四分支裁决 | **violation_reproduced**——报告主张（Transfer 事件 source 应为
  from 而非 msg.sender）在代码层机械证实 |
| 绑定健全性 | transferFrom 成功、Transfer 事件均在日志中找到（零绑定错误） |
| ingest | run 副本上落盘 `stage3-consistency.json`：
  `consistency_verdict: violation_reproduced`，全部符号 bound，
  查询 sat/unsat 与 P/I/V 真值一一对应 |
| 模型调用 | 注入 + 运行 + 裁决 + ingest 全程 **0 次** |

运行中修正的一个 case 对齐错误（如实记录）：最初误选了同 finding 的
另一提交（`__Hx5YyBY7hGy`）作语料 case；live4 run 的真实来源是
`__nFbsAHPP4jP`（target test `testPoCIncorrectEventEmission`），已按
provenance.json 修正——阶段二 run 与新 SC 的报告/PoC 必须同源。

## 已知边界（本原型不处理）

- 绑定映射手工提供；自动绑定（名字/单位/来源匹配）是后续工作
- 数值单位缩放（本例全为 address/bool，无数值符号）
- P 的时序简化：全部符号在动作后取值（本例 pre 符号是场景常量，
  相位不变；含状态突变的案例需要 pre 捕获段）
