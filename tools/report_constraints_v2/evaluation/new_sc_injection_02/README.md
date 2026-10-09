# new-SC 单文件合并管线（new_sc_injection_02）

## 目的

把 `new_sc_injection_01` 原型中"注入器 + 运行脚本"两段逻辑收成**一个文件、
一条命令**，完成：阶段二规则化结果 + 阶段一切片 → **一个 Solidity 文件的新
SC** → forge 机械执行 → 四分支判读 → 经既有 `stage3-feedback` 通路投入
阶段三。**零模型调用**；每案例输入只有三样数据（stage-2 run、切片、绑定映射
JSON），没有任何逐案例代码。

## 用法

```bash
/root/.local/share/uv/tools/halmos/bin/python new_sc.py <case_key> \
    [--batch prompt_live4_blind_01]
```

（Ekubo 即默认批次；换案例 = 换 case_key，脚本同一份。）

## 单文件新 SC 的构成

`new_sc__<case_key>/new_sc.t.sol`：

```text
= 原切片 contract.flattened.t.sol 全文（字节不动的前缀）
+ 追加的 Stage2InvariantGuard 合约（阶段二合并本体）
```

- 切片**只追加、绝不编辑**：`sc-spec.json` 记录 `slice_length_bytes`、切片
  `sha256` 与前缀 `prefix_sha256`，任何人可机械复核切片完整性。
- guard 的 P/I/V 表达式与 `constraints.json`（Z3 查询同源）逐字节一致，绝不
  重推；符号绑定来自 `bindings/<case_key>.json`（stage-3 侧绑定工作的替代
  物，如实披露：手工输入，自动绑定是后续工作）。
- forge 跑**全量测试**：原 PoC 测试通过 = 切片完整性现场验证；guard 输出
  唯一一行 `STAGE2_VERDICT {"p":..,"i":..,"v":..}`。

## 运行前机械门（上次原型的手工错误变成代码）

来源对齐四项检查，任一不符直接拒绝：provenance `case_id` == case_key、
`report_path` 指向语料 case 目录、`report.json` sha256 一致、切片
`declared_code_sha256` 一致。（01 原型曾手选错同 finding 的另一提交，此处
即其机械化。）

## 预注册判读表（运行前冻结）

guard 只在绑定不可能时硬失败——I 被违反是预期的好消息。判读：

| p | i | v | 裁决 | 含义 |
| --- | --- | --- | --- | --- |
| true | false | true | **violation_reproduced** | 报告主张在代码层机械证实 |
| true | true | true | i_too_weak | I 应违反而未违反 → 阶段二 I 推导/绑定错 |
| false | * | * | precondition_mismatch | 阶段二 P 与代码现实不符（P 或绑定错） |
| true | * | false | violation_not_observed | PoC 通过但 V 观察量未见 → 绑定错 |

## 工件

- `new_sc.py`：唯一脚本（合并 → 生成 → 执行 → 判读 → ingest，确定性）
- `bindings/<case_key>.json`：逐案例绑定映射（数据）
- `new_sc__<case_key>/`：新 SC（new_sc.t.sol + foundry.toml + sc-spec.json）
- `verdict.json` / `stage3_feedback.json` / `forge.log`：判读与证据
- `run_copy__<case_key>/`：冻结 run 的副本 + `stage3-consistency.json`
  （smoke 纪律：ingest 只写副本，冻结 run 永不被改写）

## 验证案例（Ekubo）

与 `new_sc_injection_01` 同一案例重跑，预期逐项一致：
`{"p":true,"i":false,"v":true}` → violation_reproduced → ingest 落盘
`consistency_verdict: violation_reproduced`。

## 已知边界（与 01 原型相同）

- 绑定映射手工提供；自动绑定（名字/单位/来源匹配）是后续工作
- 数值单位缩放未处理（Ekubo 全为 address/bool 符号）
- P 的时序简化：全部符号在动作后取值（含状态突变案例需 pre 捕获段）

## 结果（2026-10-08 运行，Ekubo）

| 项 | 结果 |
| --- | --- |
| 单文件新 SC | `new_sc.t.sol` 1,381,479 字节 = 切片原文前缀 1,377,342（sha256 逐一核对通过，sc-spec 可复核）+ 追加 guard 4,137 |
| forge 全量 | 原 PoC 测试 PASS（切片完整性现场验证）+ guard PASS，共 2 passed |
| 来源对齐门 | case_id / report_path / report_sha256 / declared_code_sha256 四项机械检查全过 |
| STAGE2_VERDICT | `{"p":true,"i":false,"v":true}`（与 new_sc_injection_01 原型逐项一致） |
| 四分支裁决 | **violation_reproduced** |
| ingest | run 副本落盘 `stage3-consistency.json`：`violation_reproduced`，unbound 符号 0 个 |
| 模型调用 | 合并 → 执行 → 判读 → ingest 全程 **0 次** |

一条命令复现：`/root/.local/share/uv/tools/halmos/bin/python new_sc.py <case_key>`。

**2026-10-08 结构优化注**：`new_sc__Ekubo.../` 与 `run_copy__Ekubo.../` 是
本脚本（零模型调用）的可再生生成物，已按"可再生即删"规则移除；ingest 结果
留档为 `stage3-consistency__Ekubo....json`（删除后已重跑一次实证复现）。
重跑上面的命令即完整复原。
