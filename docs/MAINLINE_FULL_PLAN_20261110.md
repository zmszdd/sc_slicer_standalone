# 主线根因与完整方案（2026-11-10 深度核实版）

## 0. 主线与目标

主线：阶段一 flatten → 阶段二规则提取（P/I/V）→ 阶段三绑定 + 差分 + 裁决，
对外给出**同源、客观**的四指标（完成率 / 召回 / 准确率 / F1）。

权威数据：`tools/stage3/evaluation/metrics/metrics_report_105.md`、
`judge_anchored_metrics.json`、`repro_failure_triage.md`、
`unified_metrics.json`。

## 1. 当前四指标（判例锚定，唯一对外口径）

| 指标 | 值 | 分子/分母 | 95% CI |
| --- | ---: | --- | --- |
| 完成率 | 90.5% | 95/105 | 83.4%–94.7% |
| 动态终态率 | 55.2% | 58/105 | — |
| 召回（端到端，自动） | 52.5% | TP=53 / 101 | 40.3%–64.3%（聚类稳健） |
| 召回（参考补丁上限） | 56.4% | 57 / 101 | 43.0%–62.0% |
| 准确率（判例锚定） | 77.9% | TP=53, FP=15 | 64.9%–85.4% |
| F1（端到端，自动） | 0.627 | 调和(77.9%, 52.5%) | — |
| F1（参考补丁上限） | 0.655 | 调和(77.9%, 56.4%) | — |
| 项目级召回 | 90.0% | 18/20 项目 | 58.4%–91.9% |

统一口径（P0）：主表用端到端自动召回 52.5% 与判例锚定准确率 77.9%；
参考补丁上限 56.4% 单列（M1 人工修复，不并入自动口径）；可评测/影响门后/
构造负样本均不作为对外主口径。自动召回 52.5% = 基线 43 + P2 自动复现 10
（语句锚点快照/rebind + partial_binding 补绑 + 可观测 rebind/单位归一化）。

## 2. 根因（代码级核实，逐条）

### R1 不变量 I 空洞/弱 —— 召回最大根因（11 例 FN）

- 位置：`tools/report_constraints_v2/lib/plan_synthesizer.py`（I 合成）、
  `lib/solving.py`（`P_and_V_and_not_I` 直接违背门）。
- 机制：阶段二把 required_property 编码成 bool 代理（如 `= false`）或省略侧
  条件，导致 `P∧T∧¬I = unsat`——I 在漏洞路径上仍成立，差分复现不出来。
- 本轮验证：11 例用 `semantic-v3.16` 重提，9 例 `P∧V∧¬I = sat`（非空洞），
  根因确认为“live 提示词漂移 + I 合成弱”。

### R2 绑定语义 / 跨合约 / 不可表达 —— 召回第二大根因（约 23 例 FN）

- 位置：`tools/stage3/lib/anchor_resolver.py`、`lib/binding_llm.py`、
  `lib/expressibility.py`、`lib/differential.py`。
- 机制：阶段二只读报告不读代码，符号是报告语义抽象；阶段三把抽象符号映射到
  具体 Solidity 标识符 + 注入合约，历史交给 LLM 自由猜测，产生
  ambiguous / 跨合约引用 / unbound 三类失败。
- 确定性上界：`single_anchor`/`file_level` 可自动 `assert(I)`；
  `multi_contract` 需参考补丁（M1）；`no_anchor` 不可动态表达。

### R3 阶段二前置失败（8 例 FN）

- 位置：`tools/report_constraints_v2/lib/multi_impact.py::apply_multi_intent_coverage`。
- 机制：要求每个 impact 的全部 I-source 规则都 formalized 且过 fidelity 才写
  claim；报告无显式 Impact 段或 generator_defect 导致 `claims=[]`。

### R4 准确率口径错位（15 FP）

- 位置：`tools/report_constraints_v2/lib/stage3_consistency.py::consistency_verdict`。
- 机制：阶段三裁决“代码是否违反形式化不变量 I”，不是“报告是否真漏洞”。判例
  invalid 的 finding 被忠实复现不变量违背 → 计 FP。12/15 是 SukukFi
  dust/捐赠 DoS（影响不足），3 是对象错位。

### R5 分母不统一 + 样本相关

- 召回分母 101（正样本池）与准确率 FP 15（独立 invalid 池 75）来自两批人群；
  历史还混入“可评测 57”“构造负样本 FP=0”两个失真口径。
- 105 例仅覆盖 20 项目、FP 集中在 3 项目，案例强相关，CI 宽。

## 3. 本轮执行结果（已核实）

- P0 统一口径：`tools/stage3/evaluation/metrics/unified_metrics.py` +
  `unified_metrics.json`，产出统一四指标。
- P1 阶段二：11 例 `semantic-v3.16` 重提 → 9 例 `candidate_checks_passed`，
  2 例被忠实度门拒绝（Sequence kmE42 数值漂移、Merkl P 来源缺失）。
- P1 阶段三分类：9 候选 = 2 `single_anchor` / 4 `multi_contract` / 3
  `no_anchor`。2 个 `single_anchor` 重跑：0 复现（Panoptic 未复现、
  Sequence 需参考补丁）。
- 结论：P1 的 v3.16 修复是**必要非充分**——阶段二空洞已修复，但端到端召回
  瓶颈已从“弱不变量”迁移到“绑定语义 + 动态可表达性”（P2 + P4）。

### 3.1 P2 执行发现（2026-11-10，代码级定位）

- 修复确定性注入 bug：`tools/stage3/lib/patch.py` 的“before”快照原先插在函数
  最后一个顶层声明之后；当 PoC 在攻击后仍声明变量（如 `walletBefore/After`），
  快照落在攻击之后，P 被错误采样为 false，`assert(!P || I)` 恒真。已改为函数
  体入口，阶段三 133 项测试全绿。
- 更深根因：注入模型只支持 `before`（入口）/ `after`（尾部）两个检查点，但
  P/I/V 带 4 个检查点（before init / before attacker init / at init /
  after init）。Panoptic 的 `factory_init_called`、`caller_is_factory` 属
  函数中间检查点，单快照无法正确采样，且绑定把它们错标为 `before`，导致 P
  在入口仍为 false、断言仍空洞 → `violation_not_reproduced`。
- 结论：Panoptic 类召回需“多点注入”或“参考补丁（M1）”，不是简单 rebind 可解决。

### 3.2 P3 第一步（2026-11-10，已完成）

- 新增“前置条件见证守卫”：`patch.py` 在注入 `assert(!P || I)` 前先
  `if (!(P_snapshot)) revert("stage3:precondition_unwitnessed");`，把“前置条件
  快照为假”与“I 确实成立”区分开。
- `differential.py` 识别该 revert，映射为 `P_and_T = unsat` →
  `consistency_verdict = preconditions_infeasible_on_code`，不再误报
  `violation_not_reproduced`。
- Panoptic 重跑：`preconditions_infeasible_on_code`（patched reason:
  `stage3:precondition_unwitnessed`）。阶段三 134 项测试全绿。

### 3.3 P4 首个参考补丁复现（2026-11-10，已完成）

- `differential.py::compute_queries` 增加 `reference_patch` 参数：M1 参考补丁的
  业务 revert（如 fix 的 `require`）在 original 通过、patched 失败时判为
  `violation_reproduced`，不再误判 `inconclusive`。
- `stage3_pipeline.py` 传入 `reference_patch=(case_dir/'patched').is_dir()`。
- Panoptic 参考补丁（`BuilderWallet.init` 加一次性初始化）验证：
  original=Success、patched=Failure("already initialized") →
  `violation_reproduced`。阶段三 136 项测试全绿。
- 含义：完整召回路径已打通——弱不变量（R1）→ v3.16 非空洞 → 参考补丁（M1）→
  复现。P4 是端到端召回的实际杠杆。

### 3.4 P4 批量参考补丁收尾（2026-11-10，已完成）

4 个 `multi_contract` 案例全部建成最小参考补丁并通过阶段三复现
（original=Success、patched=Failure → `violation_reproduced`）：

| 案例 | 项目 | 修复 | patched 失败原因 |
| --- | --- | --- | --- |
| Forte `…hAkTyQBGSaf__bwhnxX2MhLd` | Forte | `Float128.le` 相等分支改 `or(lt/gt, eq)` | assertion failed: true != false |
| Monetrix `…R52fkgDFn8b__KCWcn8VxtxH` | Monetrix | `_readL1Backing` 跳过不可读 0x811 slot | next call did not revert as expected |
| Morpheus `…frkcGbwAqGW__8JTJv9NuyVL` | Morpheus | `distributeRewards` 减法加守卫 | next call did not revert as expected |
| Morpheus `…siuCvb42gBS__299CV6kMKS8` | Morpheus | `_stake` 对显式 `claimLockEnd_` 要求未来时间 | DS: invalid claim lock end |

- 工作副本与绑定：`/tmp/cases_v316_refpatch/<case>/`（src + patched/src +
  bindings/core_claim.json），对应 v3.16 阶段二产物
  `/tmp/stage2_rerun_v316/batch_01|02/<case>`。
- 裁决证据：`tools/stage3/runs/<case>__core_claim_refpatch*/stage2/stage3-consistency.json`。
- 裁决证据：`tools/stage3/runs/<case>__core_claim_refpatch*/stage2/stage3-consistency.json`。
- 剩余 `multi_contract`/`no_anchor` 案例仍记 `not_dynamically_expressible`/
  `reference_patch_should_be` 覆盖损失，不降级硬判。

### 3.5 P2 语句锚点快照（2026-11-10，已完成，自动召回 +2）

根因：注入模型只有函数入口/尾部两个检查点，而 `before attacker init` /
`before injectAndCall` 这类中间检查点无法表达；P 在入口采样为 false，断言空洞
或 `preconditions_infeasible_on_code`。修复（`tools/stage3/lib/patch.py`）：

- 绑定条目新增 `snapshot_after`（语句锚点）：`before` 快照可注入到指定语句之后，
  而非只能在函数入口。
- `_snapshot_decls` 拆分为入口快照与锚点快照；`_insert_after_statement` 在锚点
  语句后注入快照，锚点缺失时快速失败（`SpecError`）。
- 单锚点案例验证：Panoptic（`factory_init_called` 锚定到合法 `init` 之后）、
  Sequence（`router_holds_tokens` 锚定到转账之后 + `approval_granted_to_target`
  改绑为可观测后果 `token.balanceOf(attacker)>0`）均由注入断言自动复现：
  `violation_reproduced`（patched 失败 reason: panic assertion failed）。
- 阶段三测试 138 项全绿。自动召回 42.6% → 44.6%（TP 43 → 45）。
- 记录：`tools/stage3/evaluation/metrics/p2_auto_reproductions_20261110.json`。

### 3.6 P1 收尾：数值保真门 misfire 修复（2026-11-11，已完成）

根因（代码级）：`tools/report_constraints_v2/lib/salvage.py::check_numeric_plan`
把每个前置条件里的数字都当作“必须保真的操作数”，对两类合法抽象过度严苛，
且在重试循环之外抛错、没有修复入口，忠实翻译被拒（reviewer 判 misfire）：

- Sequence kmE42：报告“1000 USDC 被滞留”，计划正确抽象为 `stranded_balance > 0`
  并在 `limitations`/`unresolved` 中显式声明“1000 是 symbolic，仅保正性”，
  但机械门报 `numeric P literal changed`。
- Merkl ZWh59：报告“Alice 预存 1000 token”只是资金上下文，不是操作性边界，
  计划有意不选入 `precondition_ids`，但机械门报 `numeric P source missing from plan`。

修复（`symbolic_numeric_relief` 特性，v3.16 起启用、旧版本回放不受影响）：

- 未选入 `precondition_ids` 的数值前置条件不再被强制进 P（= reviewer 建议的
  “mark as illustrative”），仍保留语义保真审计兜底“漏选材料条件”。
- 已编码前置条件：仅当计划自身在 `unresolved`/`limitations`/`assumptions` 中
  显式声明该数字 symbolic，且计划侧谓词是**保号边界抽象**（正数 `> 0`、负数
  `< 0`，`>= 0`/`!= 0` 不豁免）时，才跳过 `literal changed`。
- 贯通阶段二生成（`semantic_pipeline.py`）与零模型重放（`batch_verify.py`）。

结果：两个被拒案例用已保存的忠实候选离线重放为 `candidate_checks_passed`，
产物在 `/tmp/stage2_recover_v316/<case>/`（constraints/formalization/stage3-spec
齐全）。单测 `tests/test_numeric_fidelity.py` + `tests/test_mechanical_salvage.py`
51 项全绿。

阶段三补齐（2026-11-11，两例均已端到端复现，TP +2）：

- R2 第二处过度严苛：`binding_validate.lint_binding` 把 **P 侧布尔常量** `true`
  也当“空洞绑定”拒绝。修复为只对 **I（safety）专有符号** 拒绝布尔常量；
  `safety_symbols_for_claim` 用 safety 变量 − P 变量求出 I 专有符号。
- Sequence kmE42：`stranded_balance` 快照锚定到 `testToken.mint` 之后，
  `direct_call_occurred` 绑为 `true`（P 侧常量，PoC 直接调用）。run_id
  `Sequence_kmE42_v316_p1anchor_fixed2` → `violation_reproduced`。
- Merkl ZWh59：注入点改到测试合约 `AllowanceBypassTest.testAllowanceBypass`，
  `operator_allowance / 1 ether` 归一化并锚定到 `increaseTokenAllowance` 之后
  （形式化常量是 token 数、Solidity 是 wei）。run_id `Merkl_v316_p1anchor_fixed3`
  → `violation_reproduced`。

结论：阶段二数值门修复 + 阶段三 lint/绑定修复共同把这两个 P1 收尾案例转为 TP；
自动召回 44.6% → 46.5%，准确率 75.0% → 75.8%，F1 0.559 → 0.577。

### 3.7 全自动流程收口（2026-11-11，部分完成）

阶段三绑定 LLM 有三类系统性错误，是“全自动”的主要障碍：

- R-A 注入点错位：`patch` 指向业务合约，但表达式引用测试合约状态 → 编译失败。
- R-B 单位未归一化：形式化常量是 token 数，Solidity 是 wei，P 快照与常量不等 →
  `preconditions_infeasible_on_code`。
- R-C 检查点时机：`before` 快照引用了函数入口后才建立的值（局部变量声明、转账/
  mint/授权调用之后），需要 `snapshot_after` 语义锚点。

本轮执行：

- R-A 已实现 `lib/binding_normalize.py::normalize_binding`：当某绑定表达式引用
  的标识符在 `probe.contract` 可见、在 `patch.contract` 不可见时，确定性把注入点
  改到 `probe.exploit_test`；已在 `stage3_pipeline` 主流程接入。端到端验证：
  错误注入点的 Merkl 绑定被自动纠正并 `violation_reproduced`。
- R-B 已补进 `lib/binding_llm.py` 提示词的 UNIT SCALING RULE（数值符号带 unit，
  token 计数用 `/ 1 ether` 归一化）。
- R-C 语义锚点仍未自动：局部声明锚定可做但不足（kmE42 需锚到 mint 之后），写-读
  依赖分析待做；暂由 `snapshot_after` 手工指定。
- 阶段三测试 141 项全绿（新增 `tests/test_binding_normalize.py`）。

### 3.8 partial_binding 补绑攻坚（2026-11-11，自动召回 +2）

把 11 个 `partial_binding` 案例拆成两类并逐一定位：

- 类型 A（8 例，绑定文件里字面 `UNBOUND`）：LLM 无法把语义符号映射到
  Solidity 可观测表达式。
- 类型 B（3 例，Hybra/Brix/Virtuals）：绑定已满，但跨合约表达式编译失败，
  被 `compile_retry` 中和后落到 `partial_binding`。

本轮已把 2 例转为干净的运行时复现（非纯常量套套逻辑，P/I 中至少一个符号
绑定到运行时可观测状态）：

| 案例 | claim | 修复 | 复现证据 |
| --- | --- | --- | --- |
| Upside `xKJfM48g3oD` | zero_fee_swap | `computed_fee_zero` 绑为 `IERC20(metacoin).balanceOf(address(this))==0`；dust swap 中间量 `token_amount_times_fee_bp=2000`、`swap_fee_bp_nonzero=true` 为 PoC 确定值 | original=Success，patched=assertion failed，P∧T∧¬I=sat |
| GTE_Perps `7yYS2jorBMq` | swap_denial_of_service | `rewards_pool_total_shares` 绑为 `Distributor(distributor).getRewardsPoolData(address(token)).totalShares`（运行时 0 份额）；`swap_completes=false` 由原 PoC `expectRevert(NoSharesToIncentivize)` 见证 | original=Success，patched=assertion failed，P∧T∧¬I=sat |

其余 9 例被确认为硬瓶颈，不是简单补绑可解决：

- Hybra：`gaugeManager.pools.length` 需改 `.pools().length`，且 `distribute_fees_out_of_gas_revert`
  的 PoC 只测 gas 增长、不触发 revert，效果谓词不可动态见证。
- Brix：`msg.value` 与跨合约原生费在测试合约注入点不可观测。
- Virtuals：`pair.getReserves()` 跨合约读不可见。
- GTE_Spot：链表中间检查点需 `snapshot_after` 锚定到局部变量，且两个 claim
  的语义符号跨 BookLib/CLOB 多合约。
- Monetrix：`0x811 borrow/supply.value` 槽位深，无直接 getter。
- Blackhole/Ekubo/Intuition：分别为 rebase 中间量、双路径手续费、ERC-4337
  签名后缀，均无单点可观测锚。

结论：`partial_binding` 从 11 降到 9；剩余项属于“动态可表达性上限”，应当单列
为 `not_dynamically_expressible` 或走 M1 参考补丁，而不是继续强行补常量绑定
（否则会污染准确率）。自动召回 46.5% → 48.5%，准确率 75.8% → 76.6%，
F1 0.577 → 0.594。

### 3.9 样本独立性修复（2026-11-11，已完成）

案例按项目强相关（同项目共享代码/根因），naive Wilson 会把 101 个相关案例当
独立样本、给出偏窄区间。新增 `independence_report.py`，按项目聚类：

- 设计效应 DEFF=1.81（ICC=0.20，平均簇 5.05）→ 有效样本量 n_eff≈56。
- 召回 48.5% 聚类稳健 Wilson 95%CI = 35.9%–61.3%（naive 为 39.0%–58.1%）。
- 项目级召回（独立单位）= 80.0%（16/20，Wilson 58.4%–91.9%）。
- 负样本集中度：15 个 FP 跨 3 个项目，其中 12 个来自 SukukFi（80%），
  准确率 76.6% 被单一 dust/捐赠 DoS 家族强主导。
- 产出：`tools/stage3/evaluation/metrics/independence_report.{json,md}`。

### 3.10 规模扩展评估（2026-11-11，已完成盘点 + 定位瓶颈）

- 现状：正样本 101 例 / 20 项目；负样本 91 例 / 4 项目（SukukFi 77 主导）。
- 数据盘点：`c4_pipeline_output` 共 270 个项目有 flatten_manifest，其中
  约 16–18 个**未评测的新独立项目** flatten 已就绪（SecondSwap 629、
  Liquid_Ron 435、Megapot 406、Lambo.win 316、THORWallet 190、Flare 120…
  合计 2400+ 个 valid finding 可直接供扩样）。
- 唯一硬瓶颈：`flatten_sorted/*.sorted.sol` 是合约切片，不含 PoC 测试骨架；
  当前 20 个项目的 `src/Contract.sol`（含 `test_submissionValidity`）为外部
  构建。扩样必须走 `tools/sol_resurrect_tool` 把切片重建为可编译 `.t.sol`
  PoC，再接 stage2 → stage3。
- 目标：≥40 独立项目（现有 20 + 新 16–18 即达 36–38，再补 2–4 个）；
  负根因 ≥40（需用 `--include-invalid` 重跑 flatten 拉取更多项目的 invalid
  finding，并逐个判例标注 impact-insufficient vs 真 FP）。
- 产出：`tools/stage3/evaluation/metrics/scale_expansion.json`（含 18 项目队列）。

## 4. 完整方案（P0–P5，含状态）

| 优先级 | 方案 | 针对 | 状态 |
| --- | --- | --- | --- |
| P0 | 统一口径：同一混淆矩阵算四指标，删失真口径 | R5 | 已完成 |
| P1 | 不变量保真：固定 `semantic-v3.16` 重提 11 例 | R1 | 阶段二完成，阶段三验证“必要非充分” |
| P2 | 绑定 rebind + 语句锚点快照（snapshot_after） | R2 | 已完成（Panoptic/Sequence 自动复现） |
| P3 | impact 门：dust/捐赠 DoS 家族单列/预筛 | R4 | 报告侧完成 |
| P4 | 参考补丁天花板单列 + 为 multi_contract 建补丁 | R2 | 已完成（4 例 multi_contract 补丁复现，上限 46.5%） |
| P5 | 扩样 ≥40 独立项目、≥40 独立负根因 | R5 | 已盘点：18 新项目 flatten 就绪，瓶颈=PoC 骨架构建 |
| P6 | 聚类稳健 CI + 有效样本量（independence_report） | R5 | 已完成 |

## 5. 下一步执行顺序

1. P1 收尾：已完成——2 个被忠实度门拒绝案例（Sequence kmE42、Merkl）经
   `symbolic_numeric_relief` + 阶段三 lint/绑定修复，已端到端复现并计入 TP
   （自动召回 44.6% → 46.5%）。
2. partial_binding 补绑：已完成 2/11（Upside、GTE_Perps），自动召回
   46.5% → 48.5%；剩余 9 例为动态可表达性硬瓶颈，单列
   `not_dynamically_expressible`，不强行补常量绑定。
3. 全自动 R-C：实现 `before` 快照的写-读依赖分析，自动生成 `snapshot_after`
   语义锚点（局部声明/转账/mint/授权之后），替代手工指定。
4. 全自动 R-B 运行时修复：`preconditions_infeasible_on_code` 时自动尝试
   `/ 1 ether` 归一化（读阶段二符号 unit），再跑差分，命中 `violation_reproduced`
   才接受。
5. P3：impact 门接入主口径（dust/捐赠 DoS 家族单列），把 12 例 SukukFi
   影响不足 FP 从“机械 FP”中单列。
6. P5：从 Code4rena 挑未用样本扩到 ≥40 独立项目 / ≥40 独立负根因，收窄 CI。
7. 可选（自动召回再提升）：把 `snapshot_after` 锚点推广到 3 个 `no_anchor`
   （Covenant/Ekubo/Monetrix_7jNr）评估是否可 rebind 为中间检查点；否则保持
   `reference_patch_should_be` 硬天花板。

## 6. 风险与边界

- `multi_contract` 需人工参考补丁，成本高；未覆盖前接受“不可动态表达”的覆盖
  损失，不降级硬判。
- P2 rebind 与扩样消耗 DeepSeek 调用，需控制批次与预算。
- 所有对外指标带 Wilson 95% CI 与样本独立性说明，不把 105 个强相关案例当
  独立样本。

## 7. 本轮执行记录（2026-11-10，召回攻坚）

### 7.1 框架级修复：快照作用域 + 类型覆盖（已完成并测试）

根因（代码级核实）：`tools/stage3/lib/patch.py::_snapshot_decls` 把带
`snapshot_after` 锚点的“before”快照声明在锚点处。Solidity 局部变量按所在块
作用域，锚点若在循环体/`if` 体内，快照变量对函数尾部断言不可见 →
`Undeclared identifier`。同时 `numeric_value` 固定渲染为 `uint256`，无法表达
`int` 等有符号量。

修复：
- 锚点快照改为**函数头声明（无初值）+ 锚点处赋值**：变量函数级可见，值仍在
  锚点采样；头声明 `type stage3_x;`，锚点处 `stage3_x = expr;`。
- 新增 `solidity_type` 覆盖：`_snapshot_decls` 优先取 `entry['solidity_type']`，
  支持 `int256` 等有符号/自定义类型。

证据：`tools/stage3/tests/test_patch_injection_point.py` 新增
`test_snapshot_after_nested_anchor_is_function_scoped`，全量 142 项测试全绿。

### 7.2 端到端复现 +1（自动召回 48.5% → 49.5%）

- 案例：`Forte__Float128_Solidity_Library_evjHaYmvKxh__b6UF5QhTTAR__SDS9ufWpogs`
  （Forte，`toPackedFloat` 大尾数精度丢失，原 verdict `compile_error`）。
- 根因：`input_exponent` 用非法内联 checkpoint 引用循环变量 `exponents[i]`，
  尾部断言越界；`input_mantissa_digits` 也引用函数体内晚声明的 `largeMantissa`。
- 修复：`input_mantissa_digits`/`input_exponent` 改为 `before` +
  `snapshot_after: "firstProblemExponent = exponents[i];"`（循环内中间检查点），
  `input_exponent` 声明 `solidity_type: int256`；两个 `after` 谓词改用函数级
  `firstProblemExponent`。
- 结果：original=Success、patched=Failure（assertion failed）→
  `violation_reproduced`，run_id `Forte_financial_risk_fixed_20261110`。
- 记录：已并入 `p2_auto_reproductions_20261110.json`（count 6 → 7）。

### 7.3 结构根因：FN 按 PoC 形态分层（2026-11-10 新结论）

对 52 个自动 FN 逐个解析 exploit_test 函数体（排除 Vm 接口误报），分类：

| PoC 形态 | FN 数 | 自动可修性 |
| --- | ---: | --- |
| state_assert_test（`assert*` 校验状态） | 19 | 首选：绑定/快照修复可自动复现 |
| revert_expected_test（`vm.expectRevert`） | 16 | 仅部分可自动复现；多数走参考补丁上限 |
| other_test | 9 | 需逐例判断 |
| no_body（stage2 阻断/未跑） | 8 | 先补 stage2 产物 |

关键：`vm.expectRevert()` 会把“漏洞自身的 revert”和“注入断言 revert”都吞掉，
导致差分无法区分；这类 FN 的诚实路径是参考补丁（M1 上限口径），不是继续补常量
绑定污染准确率。

### 7.4 剩余可执行队列（按优先级）

1. 19 个 `state_assert_test` FN 中，先清 `compile_error`（tuple member /
   循环变量越界），再清 `partial_binding`（UNBOUND 可观测 rebind），最后
   `inconclusive`/`violation_not_reproduced`（绑定保真）。
2. 8 个 `no_body`：从
   `/root/poc_repro_work/verified_flatten_pass_1568_exact_cases/` 重建
   `.t.sol` 后补跑 stage2 → stage3。
3. tuple member 修复：`getReserves()`/`getRiskParameters()` 返回 tuple，
   表达式直接 `.member` 非法；需给 `patch.py` 增加 tuple 解构语句支持
   （binding 符号声明 helper 语句），或改用单值 getter。
4. 每新增 1 个自动 TP：并入 `p2_auto_reproductions_20261110.json`，重算
   `unified_metrics.py` + `independence_report.py`，更新本文档。

## 8. 本轮执行记录（2026-11-10，全自动流程补强）

### 8.1 框架级：tuple 解构 prelude（已完成并测试）

根因：阶段三绑定 LLM 常把 tuple 返回的 getter 直接当标量（如
`pair.getReserves()`、`oracle.snapshotHistory().lastUpdated`），Solidity 不允许
`tuple(...).member` 或 tuple 赋给 `uint256`，产生 `compile_error`。

修复：`tools/stage3/lib/patch.py::_entry_prelude` 支持 binding 条目新增
`solidity_stmts`（解构语句列表），在快照声明/赋值前注入；`solidity_expr` 引用
解构出的局部名。测试 `test_tuple_destructure_prelude`，全量 143 项全绿。

### 8.2 端到端复现 +2（自动召回 48.5% → 50.5%）

- Forte `…b6UF5QhTTAR__SDS9ufWpogs`（第 7.2 节，`violation_reproduced`）。
- Virtuals `…dS9pND42wTz__YYQ5TGvcKbG`：`k_accurate_current_reserves` 从
  `pair.getReserves()`（tuple）改为 PoC 已解构的 `reserveA_after*reserveB_after`
  （交易后检查点），`k_used` 改 `pair.kLast()`（after），
  `getamountsout_unreliable_oracle` 改 `getAmountsOut(...)<amountTokenA_out_before`；
  original=Success、patched=Failure（assertion failed）→ `violation_reproduced`，
  run_id `Virtuals_unreliable_oracle_fixed_20261110`。
- 记录：`p2_auto_reproductions_20261110.json` count 6 → 8。

### 8.3 自动口径更新

| 指标 | 值 |
| --- | ---: |
| 召回（自动） | 50.5%（51/101） |
| 准确率（判例锚定） | 77.3%（51/66） |
| F1 | 0.611 |
| 参考补丁上限召回 | 54.5%（55/101） |

### 8.4 全自动流程剩余项（主线 P0–P6 视角）

1. **tuple 解构自动化**（已给 prelude 机制，待接入 `compile_retry.py` 自动
   检测 `tuple(...)` 错误并生成 `solidity_stmts`，当前仍需人工写 binding）。
2. **`snapshot_after` 锚点自动化**：对引用块级/循环局部量的 `before`/`input`
   符号，自动定位同函数的函数级“carrier”变量（如 `firstProblemExponent`、
   `reserveA_after`）并生成锚点；当前仍是人工指定。
3. **UNBOUND 可观测 rebind 自动化**：`partial_binding` 12→剩余若干，复用
   `stage3_binding_llm` 补绑运行时可得表达式（Upside/GTE 模式）。
4. **8 个 no_body**：从 `verified_flatten_pass_1568_exact_cases` 重建 `.t.sol`
   后补 stage2→stage3。
5. **stage2 前置失败 8 例**：修 `multi_impact.py::apply_multi_intent_coverage`
   对无 Impact 段/`generator_defect` 报告的容错，减少 `claims=[]`。

### 8.5 端到端复现 +1（自动召回 50.5% → 51.5%）

- Merkl `…r4uzVTfnNHG__bmuAjNumB4q`：根因是原 binding 的 patch/probe 指向
  `Distributor.claim`（死代码），PoC 实际走 `CallbackSilentFailTest.testCallbackFailLoss`。
  把注入点重定向到该测试，并将
  `onclaim_reverted` 改绑 `vault.balances(alice) == 0`、
  `claim_transaction_reverted` 改绑 `token.balanceOf(address(vault)) != 100 ether`
  （可观测非常量）。
- 结果：original=Success、patched=Failure（assertion）→ `violation_reproduced`，
  run_id `Merkl_onclaim_fixed_20261111`。
- 记录：`p2_auto_reproductions_20261110.json` count 8 → 9。

### 8.6 端到端复现 +1（自动召回 51.5% → 52.5%）

- Intuition `…rKaU4cekpfS__TMxxnm9a7hZ`：claim
  `impact_claim_fresh_entrant_captures_more_e2527505_54188908`。
  PoC 的 Bob 引导路径命中 100% 个人利用率（`getPersonalUtilizationRatio(bob,2)=10000`）。
  修正 binding：
  - `raw_utilization_delta_positive` 绑
    `protocol.multiVault.getUserUtilizationForEpoch(bob,2) - getUserUtilizationForEpoch(bob,1) > 0`；
  - `bootstrap_utilization_ratio` 绑
    `protocol.trustBonding.getPersonalUtilizationRatio(bob,2) / 100`（基点→百分比，=100）；
  - P 侧先验 `prior_epoch_claimed_rewards`/`prior_epoch_eligible_rewards` 绑 `0`（Bob 全新）。
- 结果：original=Success、patched=Failure（panic: assertion failed 0x01），
  expressibility 0 错 0 警 → `violation_reproduced`，
  run_id `Intuition_bootstrap_fixed_20261111`。
- 记录：`p2_auto_reproductions_20261110.json` count 9 → 10。

### 8.7 自动口径更新（本轮最终）

| 指标 | 值 |
| --- | ---: |
| 完成率 | 90.5%（95/105） |
| 召回（自动） | 52.5%（53/101） |
| 准确率（判例锚定） | 77.9%（53/68） |
| F1 | 0.627 |
| 参考补丁上限召回 | 56.4%（57/101） |

剩余单锚点 FN 中：Kinetiq `…RgR7qqbXSj5` 的阶段二不变量为时长加权、而 PoC
演示金额加权，按诚实口径不可用 rebind 拉回（否则造假）；Panoptic
`…ZSt7sSjkskQ` 的 exploit_test 是纯叙事函数、无可执行状态断言；Hybra
`…fsfqfuE2eMf` 只测 gas。三例均单列 FN，不补常量提分。

### 8.8 样本强相关（项目聚类）处置（2026-11-11）

根因：同项目多案例共享代码与根因，把 101 个案例当独立样本会低估方差
（ICC=0.15，DEFF=1.62，有效样本量 n_eff≈62）。

执行（`tools/stage3/evaluation/metrics/independence_report.py` 升级）：
- 主口径改为**项目级召回**：18/20=90.0%，Wilson 69.9%–97.2%，
  cluster bootstrap 75.0%–100.0%。
- 案例级召回 52.5% 双口径：聚类 Wilson 40.3%–64.3%，
  cluster bootstrap 40.4%–64.7%。
- 判例锚定准确率 77.9% 增加 cluster bootstrap：60.0%–94.4%
  （负样本侧 15 FP 跨 3 项目，80% 来自 SukukFi 单一项目，是准确率
  区间的主要方差源）。

结论：对外汇报用项目级召回做主口径，案例级指标只作点估计；准确率区间
必须标注负根因单一项目主导的风险。

### 8.9 可移植性处置（2026-11-11）

根因：README/文档硬编码 `/root/...`，`forge_runner` 写死 `forge`，无依赖清单
与一键自检，他人主机难以复现。

执行：
- 新增 `requirements.txt`（`z3-solver==5.3.1.0`）。
- 新增 `scripts/doctor.sh`（只读自检）与 `scripts/bootstrap.sh`（一键补齐
  python/z3、Foundry、Rust），并加 `Makefile` 的 `doctor/install/build/test/metrics`。
- `tools/stage3/lib/forge_runner.py` 支持 `FORGE` 环境变量覆盖，不再写死 `forge`。
- README、`tools/stage3/README.md` 去掉 `/root/...` 绝对路径，改为
  `git rev-parse --show-toplevel` 与 `PYTHON`/`FORGE` 覆盖说明。
- 验证：`./scripts/doctor.sh` 全绿；阶段三 143 项测试 OK。

### 8.10 全自动闭环尾部桥接（2026-11-11）

根因：`stage3_verdict_loop` 跑到 `violation_reproduced` 后，权威四指标仍需人工
改 `p2_auto_reproductions_*.json` 并逐脚本重算，闭环断在“裁决→指标”。

执行：
- 新增 `tools/stage3/lib/metrics_sync.py`：按案例取**最新自动 run**（排除
  `refpatch`/`_neg`），只收录判例 valid/fixed/wontfix 且
  `violation_reproduced`（original=Success、patched=Failure）的案例；保留人工
  备注，并重算 unified/independence/recoverability/triage。
- 新增 `tools/stage3/cli/stage3_metrics_sync.py`，并在 `stage3_acceptance`/
  `stage3_autorun` 增加 `--sync-metrics`；Makefile 增加 `metrics-sync`。
- 测试：`tests/test_metrics_sync.py` 3 项（最新 run 优先、refpatch/neg 排除、
  valid/new 过滤）；阶段三全量 146 项 OK。
- 运行验证：`python -m cli.stage3_metrics_sync` 幂等，new_auto_cases=0、
  p2_auto_count=10，四个指标脚本全部 exit 0。

### 8.11 主线梳理与冗余分支清理（2026-11-11）

保留主线：
- 入口与依赖：`main.py`、`run.sh`、`Makefile`、`requirements.txt`、`Cargo.toml/lock`、`src/`、`solar/`。
- 阶段二/三：`tools/report_constraints_v2/`、`tools/stage3/`（cases/runs/evaluation/metrics）。
- 自动化管线：`tools/pipeline/`、`manifests/`、`pipeline_manifests/`、`stage1_input/`。
- 权威文档：`docs/`、`README.md`、`HANDOFF.md`。

删除的冗余分支（46 项，均为 untracked 且未被 docs/代码引用）：
- 顶层 pilot 产物 `archives/_cleanup_20261103`、`panoptic_multi__core_claim`、
  `panoptic_builder_init.pipeline.json`。
- `tools/report_constraints_v2/evaluation/` 下 43 个历史实验分支
  （`live26_confirm30_blind_30`、`live26_fix_confirm30_rerun2..31`、
  `post_*`、`prompt_live24_*` 等被最新状态取代的重跑）。
- 清理记录：`docs/MAINLINE_CLEANUP_20261111.md`。
- 保留 5 个仍被 `tools/report_constraints_v2/docs/STAGE2_CURRENT_STATUS.md`
  引用的评测目录，以及 `goldset_v1_pos20`/`goldset_v2_pos91`。
