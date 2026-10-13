# 绑定映射编写指南（stage2-newsc-binding/1）

绑定映射是 new-SC 管线**唯一的人工输入**：它把 formal-plan 声明的抽象
符号接到切片代码里可观测的 Solidity 表达式上。本文件是唯一格式规范；
`new_sc.py` 的 `check_binding_schema` 在写任何文件之前机械执行同一套
规则（`tests/test_new_sc_injection.py` 的 `RealBindingsConformTests`
保证入库的绑定与规范永不漂移）。

## 一份绑定 = 一个案例的数据文件

```
bindings/<case_key>.json
```

**加新案例不改任何代码**。第一步永远是生成骨架（符号名、type、unit、
meaning 全部从 formal-plan 预填，人只填 TODO）：

```bash
new_sc.py --template <case_key> [--batch <batch>]
```

然后填空（expr、四段代码、sanity 断言），跑 `new_sc.py <case_key>` 一条
命令完成合并→执行→判读→ingest。填漏的 TODO 会在 schema 门或 forge
编译期响亮失败，不会静默通过。

## 顶层字段（必须精确等于这九个键）

| 键 | 形态 | 说明 |
| --- | --- | --- |
| `schema_version` | `"stage2-newsc-binding/1"` | 固定值 |
| `case_key` | 字符串 | **必须等于文件名（案例键）**；跨案例复用会被拒 |
| `binding_provenance` | 非空字符串 | 披露绑定出自谁手、有无单位换算（诚实披露人工环节） |
| `state.inherits` | 合约标识符 | guard 合约继承的 PoC 测试合约名 |
| `state.declarations` | Solidity 行数组 | guard 合约的成员声明（多数案例为空，局部变量放 setup/post） |
| `setup` | Solidity 行数组 | 场景准备（PoC 的攻击前状态） |
| `attack` | Solidity 行数组 | 攻击动作（T 转换） |
| `post` | Solidity 行数组 | 动作后可观测量的计算 |
| `binding_sanity` | Solidity 行数组 | 绑定不可能时的硬断言（见下） |
| `symbols` | 对象 | 符号 → 绑定行（见下） |

## 符号绑定行（必须精确等于这五个键）

| 键 | 规则 |
| --- | --- |
| `phase` | `"pre"`（值在攻击动作前固定/有意义）或 `"post"`（动作后观测）。**这是被强制的语义**：`"pre"` 符号的 expr 在攻击动作**之前**求值并快照进 `<name>__pre`，P/I/V 编译引用快照——一个依赖攻击后才能计算的局部变量的 pre 绑定会在 forge 编译期直接报错，而不是静默错判 |
| `type` | `address` / `bool` / `uint256` / `int256`，**必须匹配 formal-plan 的 sort**（见对照表） |
| `expr` | 非空 Solidity 表达式，**求值结果类型必须等于 `type`**（guard 里 `bool pHolds = <expr>` 会在编译期强制这一点） |
| `unit` | 数值符号必须**等于 formal-plan 声明的 unit**；非数值符号必须为 `null` |
| `binding_description` | 非空，说清绑定的语义（这是人给后续审阅者的接口） |

### sort ↔ type 对照（机械校验）

| formal-plan sort | 允许的 type |
| --- | --- |
| `bool` | `bool` |
| `address` | `address` |
| `int` | `uint256` 或 `int256` |

### 单位规则（防"小数点绑定错"）

formal-plan 的 int 符号声明了单位（如 `"tokens"`）。绑定**必须**就地把
代码侧观测换算到该单位，并把换算显式写进 `expr`——例如观察到 wei 时：

```json
"expr": "(physicalBalanceWei / 1e18)", "unit": "tokens"
```

**禁止**静默换算（把 `physicalBalanceWei` 直接当 tokens 绑）、也禁止
声明与 plan 不同的单位。单位或缩放错了，schema 门会在写任何文件之前
拒绝，而不是让 forge 产出一个自信但错误的判读。

### binding_sanity 约定

断言消息以 `STAGE2_BINDING_ERROR:` 开头。它们断言的是**绑定本身的
前提**（"transferFrom 确实被调用"、"日志里确实有 Transfer 事件"），
不是阶段二的主张——I 被违反是预期的好消息，绑定不可能才是硬失败。
判读表中 `precondition_mismatch` 分支的语义是"P 或绑定错"，sanity
断言就是用来区分这两者的。

## 规范范例

- [Ekubo](Ekubo_3FTodhsvBkM__9MpUh5dZn3f__nFbsAHPP4jP.json)——address/bool
  符号、事件日志观测（`vm.recordLogs` + topics 解析）
- [Merkl](Merkl_T4ExvutBBXC__9JnmzBSjjfp__No9Y37ndFs5.json)——int 符号、
  wei→tokens 显式换算、binding_sanity 数值锚定（把 PoC 的已知结果钉住）

## 已知边界（如实披露）

- **绑定仍是手工编写**——schema 门保证它"格式正确、类型/单位对齐"，
  不保证"语义选对了观测"。绑定语义错误会走 `precondition_mismatch`
  / `violation_not_observed` 分支暴露，需要人回来审。自动绑定
  （名字/单位/来源匹配）是后续工作。
- `phase` 自 2026-10-09 起是被强制执行的语义（pre 符号在攻击前快照，
  见字段表）；guard 对 P/I/V 的求值时机固定在 post 段之后，攻击过程中
  瞬时被违反又恢复的不变量仍然观测不到（单检查点采样）。
