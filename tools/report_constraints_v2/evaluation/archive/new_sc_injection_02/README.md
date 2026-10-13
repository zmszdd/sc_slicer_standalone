# new-SC 单文件合并管线（new_sc_injection_02）

> 2026-10-12：本目录是新 SC 的**唯一目录**。原型 `new_sc_injection_01`
> （注入器+运行脚本两段逻辑）已按惯例 git mv 归档至
> `../archive/new_sc_injection_01/`——其绑定与 Ekubo 判读工件均已被本目录
> 的逐字节重放覆盖，无代码依赖。下文提及 01 处均指该归档原型。

## 目的

把（已归档的）`new_sc_injection_01` 原型中"注入器 + 运行脚本"两段逻辑收成
**一个文件、一条命令**，完成：阶段二规则化结果 + 阶段一切片 → **一个
Solidity 文件的新 SC** → forge 机械执行 → 四分支判读 → 经既有
`stage3-feedback` 通路投入阶段三。**零模型调用**；每案例输入只有三样数据
（stage-2 run、切片、绑定映射 JSON），没有任何逐案例代码。

流程图（合并 → 执行 → 判读 → ingest 全链及检查门）：
[../../docs/new_sc_flow.svg](../../docs/new_sc_flow.svg)。

## 用法

```bash
# 单案例（Ekubo 即默认批次）
/root/.local/share/uv/tools/halmos/bin/python new_sc.py <case_key> \
    [--batch prompt_live4_blind_01]

# 批判读：批次内所有已编译出 core_claim 的 run 一律执行
/root/.local/share/uv/tools/halmos/bin/python new_sc.py --all \
    --batch final_holdout_01

# 新案例第一步：从 formal-plan 生成绑定骨架（符号预填，人只填 TODO）
/root/.local/share/uv/tools/halmos/bin/python new_sc.py --template <case_key>

# 差异重放归因（判读回流仪器）：对隔离工作区换件重跑（见"判读回流"节）
/root/.local/share/uv/tools/halmos/bin/python new_sc.py <case_key> \
    --batch <batch> --experiment bisection/<dir>
```

语料根默认 `/root/poc_repro_work/verified_flatten_pass_1568_exact_cases`，
可用环境变量 `STAGE2_CORPUS` 覆盖（换机器/换语料不必改代码）。

批模式逐案例独立成败：缺绑定映射的案例记为 error 并继续（绝不静默
跳过），末尾打印汇总表并落盘 `adjudication_summary__<batch>.json`。

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

**绑定 schema 门**（2026-10-09 新增）：绑定映射是管线唯一的人工输入，
`check_binding_schema` 在写任何文件之前机械校验它——九个顶层键精确齐
全、`case_key` 自洽、每符号五行（phase/type/expr/unit/binding_description）
精确齐全、type 匹配 formal-plan 的 sort（bool→bool、address→address、
int→uint256/int256）、**数值符号的 unit 必须等于 formal-plan 声明的单位
且换算显式写在 expr 里**。类型/单位错配的绑定原本可以编译通过并产出
自信但错误的四分支裁决，现在 fail-fast。schema 与编写指南见
`bindings/README.md`；入库绑定由 `RealBindingsConformTests` 守护。

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
- `verdict__<case_key>.json` / `stage3_feedback__<case_key>.json` /
  `forge__<case_key>.log`：判读与证据，**逐案例命名**（后跑不覆盖先跑）
- `stage3-consistency__<case_key>.json`：ingest 结果自动留档（重跑结果
  不同则拒绝写，防陈旧覆盖；相同则为幂等 no-op）
- `adjudication_ledger.json`：**判读回流台账**（见下节）——每条判读的
  归因与回流处置，判读→阶段二的唯一受控接口
- `bisection/<case_key>/`：差异重放工作区（`run/` 冻结 run 的副本 +
  变体、`binding.json` 变体绑定、`EXPERIMENT.md` 预注册预期、全部输出
  落在本目录内，绝不动冻结批次与入库工件）
- `adjudication_summary__<batch>.json`：批模式汇总
- `run_copy__<case_key>/`：冻结 run 的副本 + `stage3-consistency.json`
  （smoke 纪律：ingest 只写副本，冻结 run 永不被改写）
- 翻译器（translate/collect_vars/check_binding_coverage/四分支表）有
  单元测试钉死：`tests/test_new_sc_injection.py`（17 例，`python main.py test`）

## 验证案例（Ekubo）

与 `new_sc_injection_01` 同一案例重跑，预期逐项一致：
`{"p":true,"i":false,"v":true}` → violation_reproduced → ingest 落盘
`consistency_verdict: violation_reproduced`。

## 已知边界（与 01 原型相同）

- 绑定映射手工提供，但格式/类型/单位现在由 schema 门机械校验
  （见上）；自动绑定（名字/单位/来源匹配）仍是后续工作
- 数值单位缩放未处理（Ekubo 全为 address/bool 符号）
- P 的时序简化：phase `pre` 符号自 2026-10-09 起在攻击动作前求值并快照
  （`<name>__pre`，被强制语义，见 bindings/README.md）；剩余边界是 I 的
  单检查点采样——攻击过程中瞬时被违反又恢复的不变量观测不到

## 判读回流（2026-10-12 起启用）

判读（阶段三侧）→ 阶段二规则改进的受控单向接口。按项目分工，阶段二对新
SC 的职责到**生成**为止；本节是反方向的那条边界。

**回流标准（四条全过才回流）**：

1. 判读分支非正向（precondition_mismatch / i_too_weak /
   violation_not_observed；violation_reproduced 只入对照计数）
2. **差异重放归因**确认肇事者是阶段二侧（见下）
3. 缺陷可泛化成模式（描述得成"模式"而非"值"，预计其他案例也会出现）
4. 修复能落进修复阶梯且能写回归测试

**差异重放（归因仪器，`--experiment`）**：非正向判读的归因不是读后感，
而是控制变量换件重跑——工作区里放冻结 run 的**副本**（携带待试变体，
如同一次重新形式化的 constraints.json）与变体绑定，`new_sc.py` 原样执行；
换绑定不改结果排除绑定侧，换 P/I/V 改结果确认阶段二侧，两者都不改则
肇事者是报告本身。归因证据是**可重放的机械事实**（forge，零模型），
最终归因由人确认并记入 `adjudication_ledger.json`；未经确认的判读不
触发任何规则改动。

**修复阶梯**：第 0 层机械门/advisory（零模型可单测，优先）→ 第 1 层
提示词规则 → 第 2 层 schema/plan 约束。**度量卫生**：任何规则改动使
旧测量作废，须冻结下一个 holdout。

**首次归因（Merkl，2026-10-12）**：precondition_mismatch 经差异重放归因
为 `scenario-pinned-preconditions` 缺陷族（阶段二表示侧，报告示例算术
为诱因）——同一报告/切片/观测下仅换一般化 P/I/V，判读翻转为
violation_reproduced。证据与处置见 `adjudication_ledger.json` 与
`bisection/Merkl_…/EXPERIMENT.md`（预注册）。对应第 0 层 advisory 尚未
实现（记为 open——那是 live 迭代的一步，须带回归测试与度量卫生）。

2026-10-09 更新：翻译器已支持算术（add/sub/mul）、负常量（int256）、
`{"const": N}` 节点与 **n 元**布尔/算子（左折叠）；新增绑定覆盖前置校验
（P/I/V 引用的符号必须在绑定映射中且不得多余，写任何文件前 fail-fast）。
两处缺陷由 Merkl 数值案例首跑暴露（Ekubo 无常量节点、全 2 元，未触发）：
const 叶节点无 `args`/`op` 键、`and` 可为 4 元。Ekubo 回归逐项不变。

## 第二案例预注册（Merkl，final_holdout_01，运行前冻结）

数值案例：公式含 int 符号与常量（990/1000/1990/2000）、eq/le 数值比较；
绑定以 `/1e18` 显式把 wei 观察量换算到报告的 token 单位（显式声明，
绝不静默缩放）。

**预注册预期**（绑定忠实于 PoC 实际场景——两笔 FoT 存款，无标准代币存款）：

- P：`fot==990` ✓（990）；`std==1000` **✗**（PoC 无标准存款，观察量 0）；
  `bal==1990` **✗**（实际 1980）；`liab==2000` ✓ → **p = false**
- I：前件（fot==990 ∧ std==1000）为假 → 空真 → i = true
- V：前件为假 → v = false
- 裁决：**precondition_mismatch**——四分支表首次机械抓到"阶段二 P 与
  PoC 现实不符"：阶段二 P 的常量取自报告的示例算术（一 FoT + 一标准
  存款人），而 PoC 实例化的是两笔 FoT 存款。I 本身忠于报告的一般主张，
  PoC 演示的资不抵债（1980 < 2000）由绑定健全性断言记录在案。
- 附注：final_holdout_01 批次对该例的判定为 rejected；本次机械裁决给出
  具体原因（P 语义与 PoC 不对齐），与批次结论方向一致。

## 结果（2026-10-09 运行，Merkl）

与上面预注册预期**逐项一致**：

| 项 | 结果 |
| --- | --- |
| STAGE2_VERDICT | `{"p":false,"i":true,"v":false}`（p✗ std=0≠1000、bal=1980≠1990；I 空真；V 前件假） |
| 四分支裁决 | **precondition_mismatch**（该分支首次被实际触发） |
| forge 全量 | 原 PoC `test_submissionValidity` PASS（切片完整性）+ guard PASS，共 2 passed |
| 绑定健全性 | 4 项断言全过：fot=990、liab=2000、bal=**1980**、1980<2000（PoC 实际资不抵债记录在案） |
| ingest | run 副本落盘 `consistency_verdict: preconditions_infeasible_on_code`（阶段三术语，与 precondition_mismatch 语义同向） |
| 留档 | `verdict__Merkl….json`、`stage3-consistency__Merkl….json` |
| 模型调用 | **0 次** |

含义：四分支表首次机械抓到"阶段二 P 与 PoC 现实不符"——阶段二 P 的常量
（990/1000/1990/2000）取自报告的示例算术（一 FoT + 一标准存款），而 PoC
实例化的是两笔 FoT 存款（990/990/1980/2000）。I 本身忠于报告的一般主张；
PoC 演示的资不抵债由绑定健全性断言机械记录。

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

**2026-10-09 稳定化四件套**（判读结果不变，重放实证）：

1. **语义单源**：表达式遍历与算子词汇表来自 `lib/dsl.py`（与 Z3 后端
   共享，守卫测试钉死词汇表一致；`mod` 有意仅 Z3 侧——欧几里得 vs
   截断取余语义不同，Solidity 侧保持响亮拒绝）；p/i/v → code-query
   映射来自 `lib/stage3_consistency.queries_from_piv`（与判读端同文件，
   生产者/消费者无法静默漂移）。
2. **绑定 schema 门**（见上"运行前机械门"）：唯一人工输入变成被校验
   的数据；两份入库绑定由 `RealBindingsConformTests` 守护，编写规范见
   `bindings/README.md`。
3. **`--template` 骨架生成**：新案例第一步从 formal-plan 预填符号
   （名/type/unit/meaning），加案例 = 填空。
4. **phase `pre` 实化为强制语义**：guard 在攻击动作前快照 pre 相位符号
   （`<name>__pre`），P/I/V 编译引用快照——错误标记 pre 的绑定在编译期
   失败。**guard 代码生成因此变化**（Ekubo 判读/ingest 证据重放后逐字节
   不变，forge 日志重录；Merkl 无 pre 符号，guard 逐字节不变）。
   另：语料根支持 `STAGE2_CORPUS` 环境变量覆盖。
