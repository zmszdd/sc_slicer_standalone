# 主线根因与改进方案（2026-11-10）

本文冻结当前主线四指标口径、已逐例定位的根因、以及围绕主线的改进方案与执行状态。
权威数据文件：`tools/stage3/evaluation/metrics/metrics_report_105.md`、
`judge_anchored_metrics.json`、`repro_failure_triage.md`。

## 1. 目标与当前四指标

主线目标：把 stage1 flatten -> stage2 规则提取 -> stage3 差分复现串成一条可评测链路，
对外给出**同源、客观**的完成率 / 召回 / 准确率 / F1。

判例锚定口径（唯一对外）当前值：

| 指标 | 值 | 分子/分母 | 95% CI |
| --- | ---: | --- | --- |
| 完成率 | 91.4% | 96/105 stage3 done | 84.5%–95.4% |
| 动态终态率(覆盖率) | 56.2% | 59/105 | — |
| 召回(端到端) | 43.6% | TP=44 / 判例相关 101 | 34.3%–53.3% |
| 召回(可评测) | 75.9% | TP=44 / 相关动态 58 | 63.5%–85.0% |
| 召回(端到端天花板) | 93.1% | 扣除 7 例机制天花板(缺补丁/不可动态) | — |
| 准确率(判例锚定) | 74.6% | TP=44 FP=15 | 62.2%–83.9% |
| F1(端到端) | 0.550 | 调和(74.6%,43.6%) | — |
| F1(可评测) | 0.752 | 调和(74.6%,75.9%) | — |
| 召回(项目级) | 80.0% | 16/20 项目 | 58.4%–91.9% |

影响门后（二级口径，不替代权威）：准确率 93.6%（CI 82.8%–97.8%），
F1 端到端 0.595 / 可评测 0.838。

混淆矩阵：`valid/fixed/wontfix(+)` TP=44 / FN=57（101）；`invalid(-)` FP=15 / TN=60（75）。

## 2. 根因（已逐例定位，非猜测）

### 2.1 召回损失：57 个 FN 分层

| 根因 | 案例数 | 实质 |
| --- | ---: | --- |
| invariant_holds_on_exploit_path | 11 | 阶段二安全不变量 I 太弱，`P∧T∧¬I=unsat`，PoC 原/补丁都通过 |
| mixed_non_dynamic | 12 | compile_error / partial_binding / binding_failed 混杂 |
| ceiling_dominated | 4 | 缺参考补丁/不可动态表达占多数：机制天花板，不计可恢复损失 |
| partial_binding | 11 | 绑定 UNBOUND 符号 |
| inconclusive | 5 | LLM 裁决弃权 |
| stage2 前置失败 | 8 | no_stage2_run 4 + stage2_blocked 3 + no_bound_claims 1 |
| poc_not_witnessed | 3 | 前置条件未被 PoC 见证 |
| not_dynamically_expressible | 2 | 机制天花板（应单列） |
| reference_patch_required | 1 | 缺参考补丁 |
| compile_error | 1 | 绑定作用域/类型错误 |

核心判断：**最大瓶颈是阶段二->三交接的语义质量（不变量保真 + 绑定作用域），
不是阶段一 flatten、也不是阶段三差分机制本身。**

### 2.2 准确率损失：15 个 FP

- 12/15 是 SukukFi「dust/捐赠 DoS」家族：机制忠实复现，但判例认定影响不足。
- 3/15 是对象错位（GTE Perps 2 + GTE Spot 1）。
- 本质：阶段二把「报告写的不变量违背」当目标，而这些报告本身被判为无效/影响不足。

### 2.3 口径与样本

- 105 例仅覆盖 20 个项目、FP 集中在 3 个项目，案例强相关，CI 仍宽。
- 曾用「构造负样本 FP=0」算 F1 得到失真的 0.851；已改为判例锚定 0.541/0.748。

## 3. 围绕主线的方案

| 优先级 | 方案 | 针对 | 依赖 | 状态 | 预期 |
| --- | --- | --- | --- | --- | --- |
| P1 | 阶段二不变量保真：I 判例对齐再提取，`P∧T∧¬I=unsat` 且 forge 双 Success 时回退重提 | 11 例召回 | DeepSeek LLM | 未启动（密钥阻塞） | 端到端召回 42.6%→50%+ |
| P2 | 绑定作用域前置 lint + LLM rebind | ~20 例召回 | LLM | 确定性部分已完成 | 绑定失败转可评测 |
| P3 | impact 门：dust/捐赠 DoS 家族单列或预筛 | 12/15 FP | 规则/LLM | 报告侧已完成 | 准确率口径 93.5% |
| P4 | 参考补丁策略：无补丁计入端到端天花板 | 7 例 | 策略 | 已完成 | 端到端天花板 93.1% 明确 |
| P5 | 扩样：≥40 独立项目、≥40 独立负根因 | CI 宽 | 外部判例数据 | 未启动 | CI 收窄 |

### 3.1 已完成改动（确定性、无 LLM）

- `tools/stage3/evaluation/metrics/judge_anchor.py`：判例锚定准确率 + 召回/CI + 混淆矩阵字段。
- `tools/stage3/cli/metrics_report.py`：F1 用判例锚定精度；完成率 90.5% 恢复；
  影响门后/漏洞级口径并列；`--judge-metrics` 入口。
- `tools/stage3/cli/stage3_fullflow.py`：把 judge_metrics 整体传给指标计算。
- `tools/stage3/cli/full_flow_metrics.py`：`--judge-metrics` 嵌套判例锚定块，不污染构造口径。
- `tools/stage3/lib/compile_retry.py:66`：幂等中性化。
- `tools/stage3/cli/stage3_pipeline.py:232`：编译回退多轮化（最多 3 轮）。
- `tools/stage3/lib/forge_runner.py:36`：编译错误摘要只保留 Error 块，避免 warning 淹没。
- `tools/stage3/evaluation/metrics/repro_failure_triage.py`：FN 根因自动分层脚本，
  新增 `ceiling_dominated` 拆分缺补丁/不可动态表达支配案例。
- `tools/stage3/lib/binding_llm.py`：P 侧 `before` 布尔前置条件在低可观测性下
  确定性回退为 `true`（仅当符号不进入安全不变量 I 且确在 P 表达式中），并把
  `precondition_symbols_for_claim` 加入 `lib/spec_loader.py`。
- `tools/stage3/cli/stage3_eval_run.py`：绑定 lint 传入 `safety_symbols`，
  使 P 侧常量布尔不再被误判为“trivially constant binding”。
- `tools/report_constraints_v2/cli/rerun_stage2_cases.py`：新增 `--prompt-version`
  （默认 `semantic-v3.16`），用于把 `stage2_blocked/no_stage2_run` 案例按冻结
  prompt 重提。
- `tools/stage3/evaluation/metrics/judge_anchor.py`：新增 `ceiling_rows`、
  `recall_end_to_end_ceiling` / `ceiling_count` / `recoverable_fn_count`。
- `tools/stage3/cli/metrics_report.py`：报告新增「召回(端到端天花板)」，
  覆盖损失拆分 `stage3:ceiling_dominated`。
- 负样本扩容：`negative_results_merged_78.json`（44+34 全 TN）。

## 4. 阻塞与下一步

- P1 / P2-full 需重跑 DeepSeek，但 `config/stage2_deepseek.local.env` 的
  `DEEPSEEK_API_KEY=<key>` 是占位符，无法调用。
- P5 需外部 code4rena 判例数据。

下一步：
1. P4 已完成（端到端天花板 93.1%，7 例机制天花板单列）。
2. 拿到真实 DeepSeek 密钥后启动 P1 + P2-full（最大召回杠杆）。
3. 确认新 code4rena 判例数据可及后启动 P5。

## 5. P1/P2 试点结论（2026-11-10，DeepSeek 密钥已就绪）

密钥 `config/stage2_deepseek.local.env` 已填真实值，官方 DeepSeek 连通验证通过
（阶段二与阶段三共用同一 key 文件）。

对 `invariant_holds_on_exploit_path` 的 Covenant 例做三方对照重跑：

| 条件 | 结果 |
| --- | --- |
| 当前 `semantic-live` 重跑 | 回归：1 条候选 → 0 条（fidelity 门拒绝 impact-scope 链接） |
| 稳定版 `semantic-v3.16` 重跑 | 复现候选，且 I 更忠实：`P∧V∧¬I=sat`（非空洞） |
| v3.16 spec 再跑 stage3 | `binding_failed`，bindability=`multi_contract`（跨合约） |

结论：
1. live prompt 已漂移变严，盲目重跑会拉低召回；P1 必须固定 `semantic-v3.16`。
2. 不变量保真重提后，11 例的瓶颈会从“弱不变量”迁移为“跨合约绑定”，
   落入 P2 / reference-patch（P4 天花板）域，需逐例重分类后按需 rebind。
3. 下一步：对 11 例以 `--prompt-version semantic-v3.16` 重提阶段二（先入 /tmp，
   不 copy-back），逐例重跑 stage3 后重分类：复现→召回；binding_failed→P2；
   multi_contract→reference-patch 天花板。

## 6. 弱不变量/差分未复现：根因闭环（2026-11-11）

### 6.1 根因（代码级证据，非猜测）

“端到端召回低”的弱不变量分支不是阶段三差分机制本身，而是两层叠加：

1. **阶段二 relation_obligation 模板的 condition 语义倒置**：
   - 模板构造 `I = condition → relation`、`V = condition ∧ ¬relation`。
   - 对“缺失检查/访问控制”类漏洞，LLM 把 `condition` 编码为“守卫触发”
     （如 `mint_cap_validation_rejects`），而不是“被保护动作发生”
     （如 `mint_attempted`）。
   - 后果：漏洞路径上 `condition` 恒假 → `I` 空真、`V` 不可满足
     （代码层）。`tools/report_constraints_v2/prompts/versions/semantic_prompts_v316.py`
     的 `_FIXED_PATTERNS` 与 `_CLASS_BINDING_RULES` 中的 access_control
     condition 描述即触发点。
   - 阶段二 SMT 可行性（`safety_negation_feasibility` / `P_and_not_I`）检测不到
     这种**代码层空真**（数学上 `P∧¬I` 仍 sat），所以旧门禁失效。

2. **阶段三差分把 `P_and_T_and_V` 硬编码为 unsat**：
   - `tools/stage3/lib/differential.py` 在 `original_ok and patched_ok` 分支
     无条件写 `P_and_T_and_V = unsat`，从未独立见证 effect V。
   - 当 I 空真时，原版 PoC 成功（V 实际发生）但 I 探针通过（¬I 不可见证），
     于是误判 `violation_not_reproduced`。

### 6.2 已执行修复（确定性）

- `tools/stage3/lib/patch.py`：`_assert_tail` 支持 `probe_kind='effect'`，
  新增 `build_effect_project`，注入 `assert(!P || V)` 独立见证 effect。
- `tools/stage3/lib/differential.py`：`compute_queries` 新增 `effect_result`，
  “both pass” 分支不再硬编码 `P_and_T_and_V=unsat`，而按 effect 探针实测
  置 `sat`，从而正确产出 `effect_observed_invariant_holds`（restate-I），
  与 `violation_not_reproduced` 区分。
- `tools/stage3/cli/stage3_pipeline.py`：两版本都通过时构建 effect 项目、
  跑 forge、传入 `effect_result`，并写入 summary。
- 测试：阶段三 146/146 通过。

### 6.3 P1+P2 试点（已复现）

Covenant `otmbJXz4irq__h23uU6Ai3Mx`：
- P1：goldset 内 v3.16 重提已产出忠实 I（`P → ¬mint_cap_bypassed`）。
- P2：绑定把 `violates_one_check` 快照锚定到
  `uint256 exploitMintAmount = marketBaseTokenSupply * 10` 之后。
- 结果：`violation_not_reproduced` → `violation_reproduced`（TP）。

剩余弱-I 案例正以 `--prompt-version semantic-v3.16` 批量重提（/tmp/stage2_rerun_p1_weakinv），
重提后仍需逐例绑定修复（P2）再复测。

## 7. 绑定失败：根因闭环（2026-11-11）

### 7.1 根因（逐例验证）

绑定失败不是单一 bug，是阶段二→三语义鸿沟在绑定通道的三层表现：

1. **快照作用域错位（可确定性修复，已修复）**：`before` 快照在函数入口赋值，
   但表达式读取函数体后部才声明的 PoC 局部变量 → `Undeclared identifier`
   编译失败。旧 `compile_retry` 把符号中性化为 true/0 → `partial_binding`
   （等于弃绑）。修复：新增 `relocate_before_snapshots`，自动把快照锚定到
   最后一个被引用局部变量的声明语句之后（`snapshot_after`）。
2. **P 侧绑定错位 → `preconditions_infeasible_on_code`（可恢复）**：single_anchor
   案例的 P 符号被绑到错误 observable/checkpoint，注入点 P 恒假
   （`P_and_T=unsat`）。需 rebind。
3. **结构天花板 `multi_contract` → `not_dynamically_expressible` /
   `reference_patch_required`（不可恢复）**：I/V 符号代码锚点跨多个合约，
   单注入点 `assert(I)` 看不到全部。`anchor_resolver` 已正确判定，
   只能走 M1 reference patch。

### 7.2 已执行

- `tools/stage3/lib/patch.py`：新增 `local_decl_statements` +
  `relocate_before_snapshots`。
- `tools/stage3/cli/stage3_pipeline.py`：编译重试先做快照重定位，仍失败才
  中性化；summary 记录 `relocated`。
- `tools/stage3/tests/test_patch.py`：新增 `SnapshotRelocationTest`（2 例）。
- 测试：阶段三 148/148 通过。
- Covenant 端到端复测：去掉手工 `snapshot_after` 后，自动重定位
  `violates_one_check` → `violation_reproduced`（TP），`neutralized: []`。

### 7.3 5 例 v3.16 重提 + 重跑结果（瓶颈迁移实证）

| 案例 | bindability | 新 verdict |
| --- | --- | --- |
| Covenant_CF5ba95T4KR__5atNeQZ3fR4 | multi_contract | not_dynamically_expressible |
| Ekubo_bKb5Sm2R6Jq | multi_contract | preconditions_infeasible_on_code |
| Monetrix_KCWcn8VxtxH | multi_contract | preconditions_infeasible_on_code |
| Panoptic_Y7Nqj3mb79V | single_anchor | preconditions_infeasible_on_code |
| Sequence_h4tnfm6jJf3 | single_anchor | preconditions_infeasible_on_code |

结论：P1 重提后弱不变量根因消失，瓶颈如预期迁移为
`multi_contract`（结构天花板，需 reference patch）与
`preconditions_infeasible_on_code`（P 侧绑定错位，可 rebind）。

## 8. 阶段二前置失败：根因闭环（2026-11-11）

### 8.1 根因

前置失败（no_stage2_run / stage2_blocked / no_bound_claims）经逐例核查后，
**主因不是阶段二没跑，而是评测未随 goldset 重跑刷新**：

- 9 例前置失败中 2 例判例为 invalid（SukukFi），不计入召回 FN。
- 7 例 valid/fixed 中，6 例 goldset 已由 v3.16 重提产出
  `formalized_candidate`，但 `positive_eval_105.json` 仍记旧状态——纯 stale。
- 真正卡在阶段二的仅 1 例：Ekubo `TuLiGdJaxpt__2VpY9ZKEXeo`，其报告 Impact
  明确（存储碰撞→DoS），但 input-screening 门连续误判
  `missing direct_effect / safety_relation_basis`，阶段二在筛选即被拒。

### 8.2 已执行

- 重提/重试 Ekubo 阶段二（semantic-v3.16 ×3）：screening 稳定误拒，判为
  screening 天花板，不做全局放宽（避免精度回归）。
- 刷新 7 例 valid/fixed 的 stage3 eval 并合并回 `positive_eval_105.json`。
- 重算权威指标：`judge_anchor.py` + `metrics_report.py`。

### 8.3 刷新后指标变化

| 指标 | 前 | 后 |
| --- | ---: | ---: |
| 阶段二 spec 非空 | 93.3% | 98.1% |
| 动态终态率 | 56.2% | 58.1% |
| 端到端召回 | 43.6% | 44.6% |
| 可评测召回 | 75.9% | 75.0% |
| 判例锚定准确率 | 74.6% | 75.0% |
| TP | 44 | 45 |

召回侧 1 例净转正：Covenant `oq24Vuwjp6r__segviiRDqQb`
（no_stage2_run → violation_reproduced）。剩余 recall 相关前置失败仅
Ekubo 1 例（screening 天花板）。
