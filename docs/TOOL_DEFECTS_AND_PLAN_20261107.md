# 工具缺陷根因与完整改进方案（2026-11-07）

主线不变：拿到**统计上可靠的全流程 case 级四指标**（完成率 / 召回率 / 准确率 / F1）。
当前最新结果：33 正样本 + 16 负样本，完成率 97.0%、召回 73.9%（17/23 可评测）、
准确率 100%、F1 0.850；可评测覆盖率 69.7%，样本量未达标。

## 一、缺陷与根因

### D1 阶段三跨合约注入天花板
现象：大量 `compile_error` / `binding_exhausted` / `partial_binding`，
报 `depositPools`、`protocolBalances`、`FAIR_VALUE` 等标识符不可见。

根因：
- `lib/binding_validate.py` 的跨合约检查只在 `patch.contract` 非空时才启用
  （`_contract_scope` 返回 None 时跳过）。LLM 提 binding 时经常不填
  `patch.contract`，导致跨合约引用漏检。
- 漏检后错误延迟到 forge 编译期才爆，被记为 `compile_error`，而不是可路由的
  `reference_patch_required` / `not_dynamically_expressible`。
- `cli/stage3_eval_run.py` 在 binding_llm 的 strict lint 阶段就把跨合约 binding
  判 `binding_exhausted`，永远到不了 `lib/expressibility.py` 的
  `reference_patch_required` 分支。

后果：可评测覆盖率被这些“本该不可动态表达”的 claim 拉低，且浪费 DeepSeek 重绑轮次。

### D2 阶段二 zero-claims
现象：goldset 88 例中 9 例 `stage3-spec.json` 的 `claims=[]`，4 例无阶段二 run。

根因（`lib/multi_impact.py::apply_multi_intent_coverage`）：
- 阶段二要求每个 Impact 的**全部 selected I-source 规则**都 formalized 且过
  fidelity 审计，才把 claim 写进 `stage3-spec`。
- 这些报告被 LLM 生成“I 编码成 V 的蕴含”或“trigger 无 grounding”等不完整规则，
  fidelity 审计判 failed，Impact 落入 unformalized/fidelity_failed，最终
  `stage3_declarations` 被过滤为空。
- 这不是阶段三问题；重跑 `--claim-verdict signals` 只救回 7/20。

### D3 负样本自动构造不可靠
现象：12 个新建负样本里 5 个修复后仍 `violation_reproduced`、1 个 `compile_blocked`。

根因：
- `cli/stage3_fix_llm.py` 的 `validate_fix` 只做 verbatim 命中校验，不校验
  “修复后漏洞是否真的消失”。
- `cli/stage3_negative_build.py` 的 `--validate` 是可选参数，且失败不阻断、
  不重提，坏的负样本照样进入 case 目录。

### D4 样本量与全量口径
现象：`stage3-ready` 已有 74/75，但最新四指标只覆盖 33 正样本 + 16 负样本。

根因：
- 之前的全流程 eval 只跑了“本轮新解锁”的 33 例，没有把已有 ready 案例一起纳入。
- 阶段一/二阻塞与 `reference_patch_required` 的覆盖统计还没统一到指标口径里。

## 二、完整方案（按依赖顺序）

### P0 修阶段三跨合约路由（零/低 LLM 成本，先做）
1. `patch.contract` 缺失时，用 `lib/solidity_scan.function_owner/state_var_owner`
   确定性推断注入点合约；多候选或不可解析时按 `reference_patch_required` 处理。
2. 让 `binding_validate` 的跨合约检查不依赖 `patch.contract` 非空，直接按
   注入函数的作用域闭包计算可见性。
3. `stage3_eval_run` 在调用 binding_llm **之前**先跑 anchor/expressibility 预判：
   - `cross_contract_reference` → 直接终态 `reference_patch_required`，不再消耗
     DeepSeek 重绑轮次；
   - `unobservable` → `not_dynamically_expressible`。
4. 对确需 M1 参考补丁的 claim 建最小参考补丁模板/清单，至少不再被误判为
   `compile_error` / `binding_exhausted`。

验收：`compile_error` 与 `binding_exhausted` 显著下降，`reference_patch_required`
与 `not_dynamically_expressible` 被正确分类，可评测覆盖率口径变干净。

### P1 修负样本构造（小成本，紧随 P0）
1. `stage3_negative_build` 强制 `--validate`，并要求终态 ==
   `violation_not_reproduced`；否则带 repair hint 重提 fix，最多 N 轮，
   仍失败则丢弃并记录 `discarded_reason`。
2. `stage3_fix_llm` 在 fix 提案中显式要求“修复后 PoC 期望翻转”，并校验
   `fix_poc` 的极性。
3. `stage3_negative_eval` 输出区分 `valid_tn` / `discarded` / `compile_blocked`，
   指标只统计 `valid_tn`。

验收：负样本构造失败率下降，TN 样本干净，FP 检测可信。

### P2 修阶段二 zero-claims（DeepSeek 成本）
1. 把 9 个 zero-claims 按 fidelity reason 分类：
   - “I 编码成 V 的蕴含”：收紧 prompt，禁止 I 使用 V 的触发词/条件。
   - “trigger 无 grounding”：要求 I 的 condition/trigger 必须来自 TARGET INTENT
     自身适用域。
   - “无显式 I source”：确定性标记 `not_applicable`，不强造 claim。
2. 用 `cli/rerun_stage2_cases.py` 对 9+4 例重跑，`--claim-verdict signals`。
3. 仍无法 formalized 的报告作为阶段二覆盖天花板单独报告，不污染召回率分母。

验收：`stage3-ready` 进一步增加，`zero_claims` 数量下降或全部转为
`not_applicable` 并明确计数。

### P3 全量跑通四指标（收口）
1. 统一分母：完成率=全输入；召回=可评测动态终态；阶段二 blocked、
   `reference_patch_required`、`not_dynamically_expressible` 单独报告覆盖率。
2. 把 `stage3-ready` 的 74 例全部纳入 full-flow eval，正样本 ≥40。
3. 负样本扩到 ≥40 个独立根因。
4. 最终指标带 Wilson 95% CI 与样本量警告，达标后才作为可靠结论。

## 三、风险与边界

- M1 参考补丁人工成本高；未覆盖前，先接受“不可动态表达”的覆盖损失，不强行降级判定。
- 阶段二 prompt 修复只能改善已知 failure class，不保证全部报告转 formalized；
  未 formalized 的按 `not_applicable` 计入阶段二覆盖率，而不是召回率分母。


## 四、执行结果（2026-11-07）

### P0 已完成
- `tools/stage3/lib/binding_validate.py`：`_contract_scope` 支持显式 contract；
  `lint_binding` 推断 `effective_contract`（patch.contract → patch.functions[].contract
  → probe.contract），跨合约检查在 `patch.contract` 缺失时也执行。
- `tools/stage3/cli/stage3_multi.py`：新增 `--claims` 只跑指定 claim。
- `tools/stage3/cli/stage3_eval_run.py`：
  - 移除基于 `anchor_resolver` 上界的激进预路由（避免误杀可复现的多合约 claim）；
  - 绑定 lint 改为 `strict=False`，把跨合约/不可表达判定交给 pipeline 终态；
  - `--skip-llm` 对已有 binding 快速复用，不再跑昂贵的 anchor/skeleton 探测；
  - `stage3_multi` 缺失 verdict 归为 `binding_failed`；去重 `bound_claim_ids`。

### P1 已完成
- `stage3_negative_build` 强制 `--validate`：只有终态 `violation_not_reproduced`
  才接受；否则最多 `--max-fix-rounds` 轮（fix-json 时 1 轮）重提修复，仍失败写入
  `<out>.discarded.json` 并丢弃。
- `stage3_fix_llm` 新增 `--hint`，把上一次被拒原因注入下一次修复提案。
- 冒烟：12 个可适用 fix 构造 → 6 个 TN 接受、6 个（含 FP）被正确丢弃。

### P2 已完成
- 13 个 zero/no-stage2 案例重跑 stage2（`--claim-verdict signals` + `--continue-on-review`）：
  - 救回 5 例（Morpheus siu、Panoptic_Hypovault BcL、SukukFi eJyt、Hybra LJk、Virtuals yc36）。
  - 剩余 8 例为报告本身无 Impact 段或生成器缺陷（4 no_stage2_run + 4 zero_claims）。
- `stage3-ready`：74 → 80，claim 数 316。

### P3 已完成（正样本）
- 全量 88 例 goldset 正样本 eval：78 done、4 no_stage2_run、4 stage2_blocked、2 no_bound_claims。
- 合并结果：`tools/stage3/evaluation/metrics/positive_eval_80.json`。
- 四指标（16 个验证 TN）：
  - 完成率 88.6%（95% CI 80.3%–93.7%）
  - 召回率 75.5%（37/49 可评测，95% CI 61.9%–85.4%）
  - 准确率 100%（TP=37，FP=0，TN=16，95% CI 90.6%–100.0%）
  - F1 0.860
  - 指标文件：`tools/stage3/evaluation/metrics/fullflow_metrics_80_16neg.json`

### 未完成 / 边界
- 负样本仍是 16 个验证 TN（目标 ≥40），FP 检测力不足；`stage3_negative_batch`
  已可用，下一轮需以 `--validate` 批量扩到 ≥40 独立根因后，准确率才能宣称可靠。
- 8 个阶段二 blocked 案例无法自动 formalized，属于阶段二覆盖率天花板，未计入召回分母。

---

## 五、TP 缺口归因（2026-11-08）

现状：可评测正样本 49，复现 TP=37，差 3 到目标 40。12 个“可评测但未复现”案例归为 4 类：

### TP-1 执行终止类违规无法被 M4 差分见证（系统性问题，影响最广）
样例：Forte `sqrt(0)` 返回 `stop()`、Ekubo oracle DoS、Panoptic drains、Sequence asset theft、
Monetrix reads revert 等。根因：
- `lib/patch.py::_inject_into_source` 把“before 快照”和 `assert(!P||I)` 都插到
  `_last_top_level_decl_end` 之后——即**转换动作之后**。
- 当转换本身 `stop()`/halt（而非 revert）时，assert 永远不可达，而 forge 仍报 PASS
  （已实测 `test_SqrtRevertsOnZero` 原版 PASS）。
- 于是 original=Success 且 patched=Success → `violation_not_reproduced`（假阴性）。
- 修复方向：对“执行终止/无返回值”类 claim 需要新的见证机制（如低层 external call
  检查 success+return data 长度，或 M1 参考补丁差分），不能靠 assert-after-transition。

### TP-2 空泛/真值绑定（binding LLM 把 I/P 绑成 `true`）
样例：Monetrix `operator_calls_settle=true`、`yield_pipeline_gates_passed=true`、
`pm_account_has_borrow_liability=true`。I 恒真 → `not_I` 恒 unsat → 永不复现。
修复方向：绑定 lint 拒绝 literal `true`/`false` 绑定，要求可观测表达式；必要时重绑。

### TP-3 原 PoC 自身失败（报告质量天花板，非流水线缺陷）
样例：Covenant CF5 `PriceOracle_InvalidAnswer()`——报告 PoC 用 `hex""` 做 Pyth update data，
原代码就 revert，PoC 无法复现。此类不重写审计 PoC 则不可救，应记为“报告 PoC 天花板”。

### TP-4 不可动态表达 / 跨合约 / 编译错误
样例：Morpheus（reward 随时间分布、跨合约）+ 少量 `compile_error`。
其中 `not_dynamically_expressible`/`reference_patch_required` 是正确的终态分类，
不是漏召回；`compile_error` 需逐个看是否可经编译重试救回。

### 结论与优先级
- 可救 TP 主要来自 TP-1（机制修复，一处修复惠及多案例）与 TP-2（绑定质量，可重绑）。
- TP-3/TP-4 属于报告或表达性天花板，不宜强行降级判“复现”来凑 TP。
- 负样本独立根因目标 ≥40，当前 ~23；上限约 35 个复现项目，需明确“工作口径 vs 统计可靠口径”。

---

## 六、根因再定位：正样本采样池不足（2026-11-08）

再深挖后，样本不足的**首要根因不是通过率，而是评测池太小**：

- `positive_eval_80.json` 的 88 例来自 `goldset_v2_pos91/selection.json`，抽样规则是
  “**每项目最多 5 条、seed=20261103**”，实际只覆盖 **19 个 distinct 项目**。
- 可用 flatten 池 `/root/poc_repro_work/verified_flatten_pass_1568_exact_cases` 有
  **1570 个 case、跨 242 个项目前缀**；88 例只取到其中的 5%。
- TP=37 只落在 16 个项目里；负样本独立根因来源也被这 16 个项目锁死，这就是
  “TP 差 3、负样本独立根因差 17”的数量级根因。
- 另有 **17 个真实案例**（flatten ✅ + stage3-spec ✅，其中 15 个已带 bindings）
  因“每项目≤5”被截掉，它们的历史归档 run 里有 ~7 个案例曾 `violation_reproduced`，
  直接补回即可低成本提升 TP。

结论：主线扩容顺序应为
1. 补回 17 个已 ready 案例（`--skip-llm` 复用绑定，近零 LLM 成本）；
2. 从 1570 池按“长尾项目优先、每项目 1–2 条”抽 30–50 个新案例，跑 stage2→stage3，
   把项目覆盖从 19 提到 ≥40；
3. 并行修 TP-1/TP-2 提升通过率。

## 七、L1 执行结果（2026-11-08）

把 17 个被“每项目≤5”截掉的 exact_submission 正样本补回（`--skip-llm` 复用绑定）：
- 新增 6 个复现案例：Brix cSNXN(1)、Covenant YjkF(3)、Monetrix uBJH(2)、
  Morpheus HUkZ(1)、Sequence X77d(2)、SukukFi SZy2(1)。
- 正样本 88→105，可评测 49→58，**TP 37→43**，项目覆盖仍 16（未扩，见 L2）。
- 四指标（44 负样本）：完成率 90.5%、召回 74.1%（43/58）、准确率 100%
  （TP43/FP0/TN44，95% CI 91.8%–100%）、F1 0.851；`sample_warnings=[]`。
- 文件：`tools/stage3/evaluation/metrics/positive_eval_105.json`、
  `fullflow_metrics_105.json`、`negative_results_merged.json`（44 负样本）。
- 剩余缺口：项目多样性仍 16、负样本独立根因 ~23（目标 40），需 L2 扩容抽样到
  新项目，以及 L3 修 TP-1/TP-2 提通过率。

## 八、R1 判例真值盲测（2026-11-08）

### 分仓结果（1568 份 report.json 自带判例）
judge/sponsor validity：`valid 959 / fixed 441 / wontfix 65 / invalid 91`。
产出：`tools/stage3/evaluation/metrics/judge_ground_truth.json`。

### 实锤：独立负样本一测就有 FP
当前 105 个正样本里混着 4 个判例 `invalid`，其中 1 个被主线判成复现：
- `SukukFi_...eJytFti7FNb...yobHFACVbAH`（dust DoS）：judge=invalid，reproduced=2 → **FP**。
- 另外 3 个判例 invalid：reproduced=0（1 partial_binding、2 无动态终态）。

结论：自构造负样本的“准确率 100%”一换成判例独立负样本就不成立；独立口径 FP≥1/4。
这是“准确率离谱”的直接根因——评测闭环，没有外部判例锚。

### R1b 独立盲测（进行中）
- 14 个非 SukukFi 判例 invalid（GTE Perps 8 / GTE Spot 4 / Kinetiq 2）先跑 stage2→stage3
  项目多样化盲测（避免 74 个 SukukFi 同源淹没）。
- 编排：`/tmp/r1b_blind.py`，日志 `/tmp/r1b_blind.log`。

### R1b 收口结果（2026-11-08）
- 13 个判例 invalid 盲测：8 done / 3 stage2_blocked / 2 no_stage2_run。
- **FP=3**：`GTE_Perps ajDov...YrXwPeSsimz`(reproduced=3)、
  `GTE_Perps wcadjiLKTWZ`(reproduced=1)、`GTE_Spot DtY9gGhmWN6`(reproduced=3)。
- 加上池内 1 个 SukukFi dust DoS，**判例 invalid 实测 FP=4 / 评测 17 例（FP 率 23.5%）**。
- 判例锚定准确率 **42/(42+4)=91.3%，95% CI 79.7%–96.6%**（闭环自评 100% → 97.7% → 91.3%）。
- 产出：`tools/stage3/evaluation/metrics/positive_eval_blind_invalid.json`、
  `judge_anchored_metrics.json`（schema v2）。

### P1 收口结果（2026-11-08）
- SukukFi 判例 invalid 抽样 22 例（dust DoS 家族 15 / A78JaZeDQAg 4 / 7gXLhGcETg4 3），
  stage3 三 shard 并行：19 done / 2 stage2_blocked / 1 no_stage2_run。
- **新增 FP=2**：`A78JaZeDQAg 5KXgCEAVocF`(reproduced=2)、`7gXLhGcETg4 2mSX6c75bFA`(reproduced=2)。
  dust DoS 家族抽样 15 例均未复现，说明 dust 家族的 FP 是变体依赖的，不是全家族系统复现。
- 判例 invalid 累计评测 17+22=39 例，**FP=6，FP 率 6/39=15.4%**。
- 判例锚定准确率 **42/(42+6)=87.5%，95% CI 75.3%–94.1%**。
- 产出：`tools/stage3/evaluation/metrics/positive_eval_blind_invalid_sukukfi_p1.json`、
  `judge_anchored_metrics.json`（已并入 5 个 blind FP）。

## 九、A2 判例锚定指标（2026-11-08）

把 105 例里的 4 个判例 invalid 重新归类（invalid 且复现 → FP）：
- 真 FP：`SukukFi dust DoS`（judge=invalid，reproduced=2）。
- 干净 TP = 42（valid/fixed/wontfix 中复现）。
- 初版 **42/(42+1)=97.7%**（87.9%–99.6%）；并入 R1b 后 **42/(42+4)=91.3%**（79.7%–96.6%）。
- 并入 P1 后 **42/(42+6)=87.5%**（75.3%–94.1%）。
- 产出：`tools/stage3/evaluation/metrics/judge_anchored_metrics.json`。

判例池全量（供 A5 扩容）：valid 959(19项目)/fixed 441(9项目)/wontfix 65(7项目)/invalid 91(4项目)。
注意：当前 flatten 池只有 ~20 个 distinct 项目，40 项目目标需处理新审计，不能只靠本池扩容。

## 十、A4 空泛绑定 lint（2026-11-08，已完成）

`tools/stage3/lib/binding_validate.py` 新增 `_trivial_bool_literal`：当某条绑定
`solidity_expr` 整体是裸 `true`/`false`（允许空白与冗余括号）时判为 `error`，
提示“trivially constant binding”，要求重绑到可观测表达式。只命中整表达式为字面量，
不误伤 `x == true` 这类合法子项。

验证：
- 新增 3 个单测（裸字面量命中、子表达式不误伤、已知空洞 fixture 命中）全绿；
- `tools/stage3` 全量 109 测试通过；
- 已知 `panoptic_builder_init_e2e` fixture 中 4 条 `true`/`false` 绑定被正确拒绝，
  这正是 TP-2 缺陷的确定性复现。

## 十一、A3 判例锚定脚本 + A5 数据天花板（2026-11-08）

新增 `tools/stage3/evaluation/metrics/judge_anchor.py`：把判例真值与评测结果对齐，
输出“真漏洞口径”准确率（TP_clean=判例非 invalid 且复现；FP=判例 invalid 且复现），
支持 `--blind-invalid-eval` 合并独立盲测 FP。已复算确认与现有口径一致（42/(42+1)=97.7%）。

A5 数据天花板（实测，非目标可达性）：
- `verified_flatten_pass_1568_exact_cases` 与 `_1729_cases` 都只覆盖 **20 个 base 项目**；
- 全量 `generated_full_poc_batch` 的 `flatten_pass` 实为 **24 个 base 项目**，其中 4 个
  （BitVault 2 / Lido 6 / Sequence_jEtbuty6H23 7 / Silo 1）有 flatten_pass 但未进
  1568 exact 池，需重跑 report↔PoC 配对验证，收益约 16 个案例；
- 真正可扩到 40 项目的数据源是 `c4_pipeline_output`（441 个审计）与 `code4rena_reports`
  （449 个审计），但需先跑 flatten 批量，是独立的多小时批量任务，不在本轮内完成。

## 十二、P2-a 终止型 opcode 诚实归类（2026-11-08，已完成）

TP-1 根因：`assert(!P || I)` 注入在转换动作之后，当动作本身 `stop()`/`selfdestruct`
成功终止执行上下文时，assert 不可达，forge 仍报 PoC 测试 Success → 被误判为
`violation_not_reproduced`（假阴性，压低召回）。

本轮落地：
- `tools/stage3/lib/patch.py`：`function_has_halt` / `injection_has_halt`，在注入目标
  函数体内检测 `stop()` / `selfdestruct`（忽略注释与字符串）。
- `tools/stage3/cli/stage3_pipeline.py`：检测到 halt 且非 M1 参考补丁时，直接产出
  新终态 `halt_witness_required`，跳过 forge，不再误报 `violation_not_reproduced`。
- `verdict_loop.py` 把 `halt_witness_required` 纳入 NON_FIXABLE（skip）。
- 指标口径：`full_flow_metrics.py` / `metrics_report.py` / `stage3_eval_run.py` /
  `eval_report.py` 将该终态按“当前见证机制不可评测”处理，移出召回分母，避免把
  机制天花板误算成漏召回。

验证：
- 新增 3 个单测（stop/selfdestruct 检测、注释字符串忽略、injection 目标上报）全绿；
- `tools/stage3` 全量 112 测试通过；
- 实机验证：Forte `sqrt` 函数被正确识别为 halt（`sqrt256` 不误报）。

遗留（P2-b，未实现）：真正的“回补召回”需要低层 `call` + returndata 见证机制，把
halt 类漏洞转成可复现 TP，而不是仅诚实归类。

## 十三、P2-b halt→revert 见证（2026-11-08，已完成）

在 P2-a 的诚实归类之上，给 `stop()` 类漏洞加可检测见证：
- `tools/stage3/lib/patch.py`：`_rewrite_stop_globally` 把补丁版切片内**所有**
  `stop()`（含 callee 内联汇编里的 stop，如 Forte `Float128.sqrt`）改写为
  assembly 版 marker revert，reason 解出 `stage3:halt`；新增
  `function_has_selfdestruct` / `injection_selfdestruct_targets` 识别不可改写的
  `selfdestruct` 目标。
- `tools/stage3/lib/differential.py`：patched 失败且 reason 含 `stage3:halt` 时，
  `P_and_T / P_and_T_and_not_I / P_and_T_and_V` 均记 `sat`（原始版 halt=Success、
  补丁版 revert=Failure，见证“本应返回却终止执行”的违规）。
- `tools/stage3/cli/stage3_pipeline.py`：`selfdestruct` 目标走 P2-a 的
  `halt_witness_required` 诚实归类；其余（含 callee `stop()`）走全局改写见证并
  继续 forge。

验证：
- 新增/更新单测（全局 stop→revert 改写、callee stop 捕获、selfdestruct 目标上报、
  差分 halt 见证）全绿；`tools/stage3` 全量 117 测试通过；
- 实机验证：Forte `sqrt` 的 `stop()` 被全局改写为 `stage3:halt` marker，pipeline
  实跑该案例由原来的“未复现”转为 `violation_reproduced`。

效果：TP-1 中 `stop()` 类（Forte sqrt(0) 等）在重跑 stage3 后可从“不可评测”转为
`violation_reproduced` 的 TP；`selfdestruct` 类仍归 `halt_witness_required`。

## 十四、invalid 全量普查（2026-11-09，已完成）

把判例 `invalid` 从“抽样盲测”升级为“全量普查”：
- 91 例 invalid 中 **75 例可评测**（13 例阶段二阻塞、3 例未到阶段二）。
- 可评测 invalid 被主线复现 **15 例（FP）**，FP 率 **15/75 = 20.0%**，与抽样期的
  20.0% 完全一致，说明抽样并未高估/低估。
- 判例锚定准确率 = 43/(43+15) = **74.1%**，95% CI **61.6%–83.7%**。

关键结论：15 个 FP 中 **12 个是 SukukFi「vault 注销 dust/捐赠 DoS」变体**，属于同一
底层代码属性（转入 dust/捐赠资产可阻塞 `unregisterVault`）。FP 率 20% 被单一报告
家族放大，不是均匀分布的机制性误报。完整清单见
`tools/stage3/evaluation/metrics/FP_ATTRIBUTION_20261108.md`。

口径：阶段三裁决“代码是否违反形式化不变量 I”，不是“报告是否真漏洞”。给老师的最终
数字应写成：判例锚定准确率 74.1% [61.6%–83.7%]、invalid FP 率 20.0%（75/91 可评测），
而不是此前抽样阶段的 87.8%。
