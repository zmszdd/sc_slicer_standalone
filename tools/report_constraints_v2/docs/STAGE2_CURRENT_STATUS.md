# 阶段二现状与收口计划

> **当前快照（2026-11-12）**：阶段二主线未变（P/I/V 规则化 + `stage3-spec.json` 交接）；阶段二全量回归 472/472 通过。下文按时间顺序保留历史实验记录，历史“下一步”与本快照冲突时以本快照为准。

状态摘要更新于 2026-10-28。下文按时间顺序保留实验记录；若历史记录中的“下一步”与本节冲突，以本节为准。最终状态：`direct_v_prescreen` 回滚为默认 `False`。同一 20 份报告配对对照显示 prescreen OFF 优于 ON：Impact 规则化率 45/75（60.0%）vs 30/66（45.5%）、`candidate_checks_passed` 8/20 vs 6/20、`stage2_can_continue=true` 17/18（94.4%）vs 14/18（77.8%）、模型调用 362 vs 211。省调用不能以主链覆盖率与交接稳定性为代价，故保留 OFF。

# 阶段二当前状态

## direct_v_prescreen 先导与配对对照，最终回滚（2026-10-28）

先导变化是把已有的 `direct_v_prescreen` 从 False 改为 True，并同步修复
`verify` 重放端两处预筛分支，使生成端 pre-screen 只省调用、不改变权威
direct-relation gate 与分母政策：

- `prompts/current.py`：`direct_v_prescreen=True`（配对后已恢复 `False`）。
- `cli/batch_verify.py`：移除 prescreen 对 assessment 分母与 coverage_scope 的
  额外收缩，重放与生成端一致。
- `tests/test_prompt_live.py`：对应断言先改 `True`，配对后恢复 `False`。

全量回归 472/472 通过。30 份全新报告盲测（与预筛前 30 份不同留出集）：

| 指标 | 预筛前 30 | 预筛后 30 |
| --- | ---: | ---: |
| 有分母报告 | 28 | 25 |
| 有分母 Impact | 86 | 61 |
| 规则化 Impact | 46/86（53.5%） | 38/61（62.3%） |
| candidate 通过报告 | 13/30（43.3%） | 10/30（33.3%） |
| stage2_can_continue=true | 26/28（92.9%） | 23/25（92.0%） |
| 实际模型调用 | 511 | 291（-43%） |
| 零调用 verify | 29/30 | 30/30 |

结论：30 份先导样本曾显示规则化率 +9 个百分点、调用 -43%、主链续跑保持 92%，
但该比较不是同一样本的配对对照。后续在同一 20 份报告上做 prescreen ON/OFF 配对：

| 指标 | prescreen ON | prescreen OFF |
| --- | ---: | ---: |
| 有分母 Impact | 66 | 75 |
| 规则化 Impact | 30/66（45.5%） | 45/75（60.0%） |
| candidate 通过报告 | 6/20 | 8/20 |
| stage2_can_continue=true | 14/18（77.8%） | 17/18（94.4%） |
| 实际模型调用 | 211 | 362 |

配对结果证明 prescreen 省调用是以主链覆盖率与阶段三交接稳定性为代价的，4 个被
prescreen 直接弃权的报告在 OFF 后 3 个恢复可继续。因此 `direct_v_prescreen`
回滚为 `False`，权威 direct-relation gate 与分母政策不变。逐案数据见
`evaluation/prompt_live24_prescreen_blind_20_confirm_prescreen_off/REPORT.md`。

## 机械抢救收口与最新 10 份盲测（2026-10-27）

围绕主线连续跑了两轮盲测后，把阶段二的机械失败族逐项收口，不做任何放宽门禁：

- `cli/semantic_pipeline.py`：local-repair 增加角色作用域校验，P/I/V 审计修复必须
  改动对应公式字段（P 改 `precondition_terms`、I 改 `pattern`、V 改
  `impact_outcome/impact_context_terms`），拒绝“只改 symbols 不改公式”的无效修复。
- `cli/semantic_pipeline.py`：local-repair 在 frozen field 被恢复后，确定性回填仍被
  引用的符号声明与 derived definition，落盘 `frozen-symbol-restore.json`；
  `cli/batch_verify.py` 同步重放，旧产物 15/15 仍可零调用 verify。
- `lib/salvage.py`：新增 DeepSeek 尾随 `}` 与重复 `relationship_trace` 两种机械
  抢救，统一走 `salvage_formal_response` 与离线重放日志。
- `cli/semantic_pipeline.py`：impact-inventory 重试提示明确 ID 必须为小写
  snake_case 且首字符是字母；type/unit 重试提示明确 timestamp+duration 的编码方式。

全量回归 472 项通过。最新 10 份全新报告盲测：

- 有分母 Impact 31，formalized 24（77.4%）；`candidate_checks_passed` 5/10；
  `stage2_can_continue=true` 10/10；真实模型调用 142；零调用 verify 10/10。
- 剩余 7 个 pending 全部是生成后 P/I/V 忠实度审查：3 个 `needs_review` 是报告
  缺显式 bridge（按设计留 review），4 个 `failed` 是谓词方向/语义与引用陈述不一致
  （按设计留档为未规则化）。本轮没有 `Extra data`、`local repair removed a symbol`
  或 `type/unit mismatch`。
- 逐案数据见
  `evaluation/prompt_live24_trailingbracefix_blind_10/REPORT.md`。

## 忠实度修复与新盲测（2026-10-27）

围绕主线做了一次 10 份全新报告的 DeepSeek 盲测，定位到主要瓶颈不是重放契约，
而是生成端把 P 前置符号写进 I 条件/触发词、以及 access_control 否定授权的极性写反。
本轮修改全部沿主线收紧，不改变分母政策与零调用重放契约：

- `prompts/current.py`：I 的 condition/trigger 必须来自 TARGET INTENT 自身的适用
  范围；无条件的 I 从 Intent 命名的操作/状态取触发词，禁止用 P attacker/权限符号
  当条件。access_control 的 `authorization_guard` 明确支持“必须为假”的否定授权。
- `cli/semantic_pipeline.py`：忠实度修复反馈在审计指出“多加 guard/恒真/反向授权”时
  给出定向重写指引，仍只允许改动公式字段。
- `lib/ingest.py`：Markdown Impact 区域内的粗体子标签（如 `**Scenario 1...**`）
  不再提前关闭区域，避免只截到标题行。
- `cli/semantic_pipeline.py`/`cli/batch_verify.py`：local-repair 的修复基底落盘为
  `repair-base.json`，verify 按 `repair-base → generated-rule-candidate →
  model-claim` 顺序回放，覆盖“前一次尝试未成功合成规则”的 fresh_restate 路径。

全量回归 465 项通过。新盲测（10 份全新报告）Impact 规则化率 24/32（75.0%）、
`candidate_checks_passed` 3/10、`stage2_can_continue=true` 9/10、零调用 verify
10/10。剩余未完成项中 4 项是 `direct_relation_infeasible`——主线直接关系门禁按设计
拦截下游/间接后果，不通过弱化 V 来通过；2 项数量表达式修复、1 项忠实度 failed、
1 项忠实度 needs_review。逐案数据见
`evaluation/prompt_live24_fidelityfix_blind_10/REPORT.md`。

## 主链生成/重放契约修复（2026-10-24）

围绕主线做了一次未使用报告的盲测，发现并修复两处生成端与零调用重放端不一致：

1. **live-24 两层响应未解包**。live-24 Prompt 要求返回
   `{formal_plan, relationship_trace}` 两个顶层键，但 `request_formalization`
   只弹出 `relationship_trace`，没有解包 `formal_plan`；忠实遵循两层结构的候选全部
   被 `unexpected formal plan fields` 拒绝。现在生成端确定性解包 `formal_plan`，
   `verify` 重放端同步解包并剥离已 salvage 的顶层 `relationship_trace`
   （`cli/semantic_pipeline.py`、`cli/batch_verify.py`）。
2. **成功多 I 规则无法重放 `relation_context`**。`verify_multi_intent_plans` 重放
   成功 Impact/I 对时没有把 `relation_context` 加回请求，而 live-23/24 生成端会加，
   导致成功规则被 `saved Impact/I formal request escaped its frozen sources` 拦下。
   现在重放端按相同规则补回 `relation_context`。
3. **入口默认预算会覆盖显式 `--readiness-retries 0`**。`main.py` 的 readiness
   append 原本只以 `--provider` 为冲突标记，用户显式传 `--readiness-retries 0`
   （未显式 provider）时会被追加的 `--readiness-retries 1` 覆盖。现在冲突标记扩展为
   `--provider` / `--readiness-retries` 任一，显式预算与其它 retry flags 一样生效。

新增回归测试 `FormalPlanEnvelopeTests`；全量自动化测试 474 项通过。修复后同一份
盲测报告（Silo Finance `W66hJ3tzotg`）的 `formalization_rate` 从 0 提升到 0.5：
1/2 个 Impact 通过忠实度审查，另一个 Impact 的 I 被审查判为恒真式（`x implies x==x`）
而正确留档为 `unformalized`。

## 多案例盲测与 local-repair 重放修复（2026-10-26）

对 5 份全新报告（GTE Spot、GTE Perps、Covenant×2、Olas）跑真实 `run` + 零调用 `verify`：

- 总 Impact 10，formalized 8，`formalization_rate=0.8`；忠实度 13 通过 / 2 失败。
- 0/5 `stage2_can_continue=true`：formalized 的 claim 仍全部被
  `direct P/I/V relationship is absent or infeasible` 拦下。生成端倾向把 I 写成
  `¬V ⇒ condition`，使 `P∧V∧I` 恒可满足，是当前主线最主要的语义缺口，不是重放契约问题。
- 发现并修复 local-repair 重放不一致：成功重试会从上一版恢复 `unresolved/limitations`
  等非可变字段，但 `verify` 未重放 `restore_frozen_repair_fields`，导致
  `saved Impact/I plan differs from normalized model response`。现在
  `verify_multi_intent_plans` 按 attempt 记录重放该恢复步骤，5/5
  `offline_verified=true`、`model_calls=0`。

## 主线极性门禁（2026-10-27）

盲测暴露的最终阻塞是：生成端把 I 写成 `¬V ⇒ condition` 或自蕴含，使
`P ∧ V ∧ I` 恒可满足，而阶段二续跑门要求它 UNSAT。修复沿主线收紧生成侧，
不改变 `continuation_blockers` 与零调用重放：

- `prompts/current.py` 要求 I 对 V 无条件；只支持间接后果、无法让 V 直接
  falsify I 时返回阻塞 `unsupported_relation`，不再凑 `¬V ⇒ ...`。
- `lib/solving.py` 新增 `direct_relation_feasible`，与 `continuation_blockers`
  完全同口径地判断 `P∧V`、`P∧V∧¬I`、`P∧V∧I` 三个查询。
- `lib/plan_synthesizer.py` 新增 `reject_vacuous_safety`，先做 V 守卫/自蕴含的
  语法拦截，再做上述语义拦截。
- `cli/semantic_pipeline.py` 在规则生成后调用该拦截，不通过的 pair 直接标记为
  `unformalized`、`failure_family=direct_relation_infeasible`，不再进入
  `formalized_candidate`。

同份 Morpheus `Y2BDLFiSWVh` 复测：两条原先“忠实度通过但恒真”的 claim 现在都
被正确标记为 `direct_relation_infeasible`，`formalization_rate` 从 1.0 降到 0.0
（诚实计数），`verify` 仍 `offline_verified=true`。全量测试 476 项通过。

另取 6 份全新报告做门禁下复测：1 份在 Impact inventory 失败，
其余 5 份共 20 个 Impact、`formalized=0`、`stage2_can_continue=0/5`，5 份
`verify` 均 `offline_verified=true`。根因是 live schema 让 V 独立于 I，生成器
倾向给出下游后果，`P∧V∧I` 仍 SAT。

随后把 `direct_relation_infeasible` 接回 `request_formalization` 的有界修复：

- `cli/semantic_pipeline.py` 在 `accepted_for_validation` 前调用
  `reject_vacuous_safety`，失败进入既有 local-repair/重试反馈，不再只做最终拒绝。
- 新增 `direct P/I/V relationship is absent or infeasible` 的 role-scoped
  重试提示，mutable 范围锁定 `pattern/impact_outcome/impact_context_terms/
  symbols/derived_definitions`。
- `prompts/current.py` 把“V 不强制否定 I”改为“V 必须直接 falsify I
  （`P∧V∧I` UNSAT），只给下游后果则不接受”。

全量测试 476 项通过。该改动让能写出直接见证的 pair 获得修复机会，写不出时
诚实落为 `unformalized`，不再虚假进入 `formalized_candidate`。

新门禁下另取 3 份全新报告（GTE Perps、SukukFi、Hybra）复测：Hybra 有 3/8
个 Impact 正式化（`formalization_rate=0.375`），通过 claim 的 V 已是对应 I
的直接违反（如 `required_effect` 的 condition 真且 effect 假）；另外两份
`formalization_rate=0.0`。三份 `stage2_can_continue=0/3`，`verify` 均
`offline_verified=true`、`model_calls=0`。

本次复测同时暴露 `fresh_restate` 成功重试的 replay 缺口：生成端在
fresh-restate attempt 上没有记录 `mutable_top_level_fields`，导致 `verify`
把“saved plan”与“normalized model response”判为不一致。修复为生成端补记该字段，
replay 端按“最近一个有 generated-rule-candidate 的前序 attempt”回放
`repair_base`，三份新盲测与全量 476 项测试均通过。

## 生成器关系路径与追加式 trace 的机械容错（semantic-live-24，2026-10-23）

live-24 让生成器随形式计划返回仅供审查的 `relationship_trace`：在冻结的 `relation_context` 中引用一条连接 P/I/V 来源的路径（引用的 action/root-cause 片段及其证据 ID）。trace 在合成前被剥离，不能成为规则条件或新来源；审查把 trace 当作未验证指针独立核对每个引用 ID——不支持的 trace 不能改善判定，缺失的 trace 也不能抹去已有片段。要素提示同时要求 action/root-cause 陈述保留完整的因果/时序桥并引用全部支持片段。

同一批 52 组冻结来源上，live-24 生成 41 组（live-23 为 46），其中 37 组通过、4 组待复核、0 组失败（通过占生成数 90.2%，live-23 为 78.3%），11 组未生成；模型调用 117 次。按预登记护栏（忠实率上升不得以丢弃完整规则为代价），这是混合结果：忠实率改善，但生成率从 88.5% 降到 78.8%。新增未生成家族经原始响应离线核对（零模型调用）确认：4 组是同一畸形形状——模型写完扁平 plan 对象后把 `,"relationship_trace":{...}}` 追加在闭括号之外；针对该形状的确定性容错 `merge_appended_relationship_trace`（`lib/salvage.py`）已按 v3.20 规范化契约接入生成与 `verify` 重放（原始响应不改写，`response-normalization.json` 记录变换），离线对 4/4 原始响应均可恢复；其效果待下一次配对复测度量。Panoptic Hypovault 5 组未生成仍是既有的类型/单位与 schema 家族，未回归；Monetrix 2 组 bool 比较失败尚未归因。详见[live-24 冻结来源 relationship-trace 复测](../evaluation/prompt_live24_relation_trace_frozen_10/REPORT.md)。本轮全量自动化测试 473 项通过。

## 关系上下文进入生成端（semantic-live-23，2026-10-22）

live-23 在保持 P/I/V 来源冻结的基础上，把已提取 action/root-cause 所引用的精确报告片段同时提供给规则生成器和原有生成后忠实度审查。上下文只帮助表达/判断已有 P/I/V 来源之间由报告描述的关系，不能新增来源 ID、替换来源角色或给公式增加无来源条件。规则仍只经过一次生成后审查，只有 `passed` 进入阶段三。另增加针对恒真、自蕴含或空泛 I 公式的生成提示检查；审查理由应引用其使用的 statement/evidence ID。

同一批 52 组冻结来源上，live-23 生成 46 组，36 组通过、9 组待复核、1 组失败，6 组未生成；相较 live-22 的 33 通过、10 待复核、3 失败、6 未生成，净增 3 组通过。生成规则中的通过率从 33/46（71.7%）升到 36/46（78.3%），总来源组通过率从 63.5% 升到 69.2%。Panoptic Hypovault 的已生成组从 6/7 通过升到 7/7；Monetrix 从 0/8 到 2/8 通过，仍有 6 组待复核。采样模型输出仍有波动，结果是方向性证据，不是外部准确率。模型调用 122 次。逐组与配对转移见[live-23 冻结来源关系上下文复测](../evaluation/prompt_live23_relation_context_generation_frozen_10/REPORT.md)。

## 关系审查与局部修复边界（semantic-live-22，2026-10-22）

保留完整 P/I/V 来源冻结后直接生成规则的主线，不增加生成前公式筛选。生成后忠实度审查仍在一次调用中分别判断来源转写与 P/I/V 关系；审查输入额外携带已提取 action/root-cause 所引用的精确报告片段，仅用于判断报告是否明确支持直接或间接关系，不替换或补写 P/I/V 来源。关系 weakened 单列为 needs_review，不等同于公式失真；明确 mismatch 仍不通过。live-22 的局部修复只针对 P/I/V 角色公式失配，不能仅因关系审查存疑或不匹配而改写已经忠实的公式。只有 passed 的来源组合计入正式通过和阶段三接口；needs_review、failed、unavailable 分开留档。

形式化提示改为尊重已冻结的目标 Impact，不再要求生成器在其他影响中重新挑选；修正了把 V 要求为 I 的直接逻辑否定、或把 I 条件/关系描述为 Impact 的矛盾要求。旧 run 保留原 prompt 快照及原有重放行为。

在 live-21 的同一批 52 组冻结来源上进行 live-22 复测：生成 46 组，33 组通过、10 组待复核、3 组失败、6 组未生成；审查不可用为 0。live-23 后续将关系上下文同时提供给生成端，见上节。

## I 公式隔离与忠实度修复收窄（semantic-live-21，2026-10-22）

在同来源 live-19/live-20 配对结果中，生成后的审查多次发现 I 公式被 V 后果错误地用作条件，或把时序要求改写成后果谓词。live-21 在规则提示中增加 I 单独转写步骤：I 的条件/关系必须来自目标安全意图或明确适用的 P；只受 Impact 支持的变量不得进入 I 公式。提示给出了 accounting、执行先后和时间比较方向的错误模式。

忠实度失败后的单次局部修复现在按失败角色限定可变字段：P 失败改 P 谓词，I 失败改安全关系 pattern，V 失败改直接 Impact 谓词/限定词；只有整体 P/I/V 关系失败时才允许联动修改公式。来源 ID 与 relation class 在此类修复中保持固定。live-20 提示及其 feature matrix 已保存为历史快照，可继续复现旧结果。

对 live-20 同批冻结来源的 live-21 复测：52 组中生成规则 46 组，生成后完整忠实度通过 21 组；24 组审查失败，1 组审查不可用，6 组未生成可用规则。完成的 45 次来源审查中，P 失配 0/82，I 失配 6/45，V 失配 1/45；整体 P/I/V 关系一致 21、减弱 9、不一致 15。live-20 同来源比较为 34 组生成、5 组完整通过。live-21 的通过数有明显提高，但 I/V 联合关系仍是主要失败点，且每组重新调用模型会带来采样变化，结果为方向性证据。详见[live-21 冻结来源复测](../evaluation/prompt_live23_frozen_source_repair_10/REPORT.md)。本轮全量自动化测试 467 项通过。

## 独立生成 P/I/V 与生成后忠实度审查（semantic-live-20，2026-10-22）

live-20 修正了旧规则合成器把 V 固定写成 `Impact 条件 AND NOT I` 的结构：形式计划新增 `impact_outcome`，模型直接把已选 Impact 原文编码为 V；程序分别编译 I 和 V，再运行生成后忠实度审查。历史 live-18/19 仍按旧 schema 解释，保证已有产物可重放。该改动没有增加规则化前的筛选步骤。

同一批 10 份报告复测：规则生成 43 条，忠实度通过 7、失败 36；覆盖状态为 formalized 3、partial 8、fidelity_failed 19、unformalized 9；报告级候选通过 0/10；模型调用 151 次；零调用重放 10/10。独立 V 使审查能直接看见报告影响，但整体语义质量尚未改善。和 live-18 的 6/28、12 条忠实度通过相比不能作严格因果归因，因为每轮上游选出的 P/I 来源对和候选集有模型随机性。定向 Monetrix 与 Panoptic Hypovault 仍有 I 语义或 I/V 对应失败。逐报告数据见[semantic-live-20 同批复测报告](../evaluation/prompt_live20_live16_paired_retest_10/REPORT.md)。

## 规则直接生成与生成后忠实度审查（semantic-live-18，2026-10-22）

规则化前仍由来源完整性判定冻结合格的 P/I/V 及其来源；一旦进入规则化，不再重选来源，也不以数值、地址、单位、重复谓词、公式可行性、关系对齐、未决项、候选门或局部修补筛选规则。规则计划经必要的 JSON/schema、引用、表达式类型校验并合成为正式规则后，才运行一次 P/I/V 忠实度审查。审查失败或审查器不可用时，生成的规则和状态仍落盘，不触发重生成；失败/不可用项不进入阶段三。

这里仍保留结构和类型校验，因为无法将不符合规则表示结构的响应编译为正式规则；这些校验只判断能否构造规则，不判断来源是否值得规则化或规则语义是否合格。冻结的每个 P 来源都会进入生成后审查；若生成规则遗漏其谓词，审查输入会明确标记为空谓词，由忠实度审查给出结果。每对 `(Impact, I 来源)` 只合成一次，审查使用并保留同一份合成规则，避免审查后再次合成。

同一批 10 份报告真实复测结果：完整 P/I/V 分母 28，完整规则化 6/28（21.4%）；45 条规则生成后，忠实度通过 12、失败 33、未完成 4；schema/validation 失败 2 项、公式构造失败 2 项；模型调用 147 次，零调用重放 10/10；报告级候选通过 0/10。相较 live-17 同批的 5/28（17.9%），多 1 个完整 Impact 通过，但来源对选择和模型输出有随机性，不能把差值单独归因于代码改动。结果表明额外 schema/筛选失败明显减少，主要瓶颈已转到生成规则的 P/I/V 关系忠实度。逐报告数据见[semantic-live-18 同批复测报告](../evaluation/prompt_live18_live16_paired_retest_10/REPORT.md)。忠实度评审与生成器同属 DeepSeek Flash 模型家族，不等同于独立人工金标准。

## 多 I 来源独立规则化（semantic-live-17，2026-10-22）

主链已扩展为：对每个 Impact 冻结适用性判定选出的全部 P/I 来源，再对每个 `(Impact, I 来源)` 独立生成一条规则。每条请求只携带一个 I，不在规则化时合并多个 I，也不推断它们之间的 AND/OR 关系；每条规则仍须保留该 Impact 和全部选中 P 来源。每个 Impact 的规则化覆盖只有在其所有已选 I 规则都通过时才记为 `formalized`；部分成功记为 `partial`，失败项仍保留在完整 P/I/V 分母中。完整候选规则化后继续经过忠实度审查和既有确定性检查。

零模型调用 `verify` 已加入对应重放路径，核对冻结来源对、每对输入卡/请求、形式计划、合并后的 P/I/V 及按 Impact 汇总的覆盖状态。规则 schema 最多容纳 64 个 claim，因此适用性判定最多可选择 64 个 `(Impact, I)` 对；超限整体作为 schema 错误重试/失败，不截断来源。批次调用预算按 64 个规则上限计算。

这是实现状态，不是效果结论：semantic-live-17 尚未运行测试或真实盲测，暂时没有可报告的通过率或重放评估。改造动机是上一轮 semantic-live-16 的 10 份报告中，24 个完整来源项仅 3 个规则化通过；其中 9 个因单 I schema 不能承载多 I 而未生成规则，历史结果见[semantic-live-16 盲测报告](../evaluation/prompt_live30_live16_complete_piv_blind_10/REPORT.md)。该历史结果不代表 live-17 效果。

## 完整 P/I/V 候选直入规则化（semantic-live-16，2026-10-22）

规则化边界已按主线收敛：逐 Impact 适用性判定是唯一候选来源筛选步骤；选中的 Impact、P 来源和 I 来源进入规则化后冻结。当前规则 schema 每个 Impact 表达一个 I 性质，因此适用性判定应选一个直接相关 I；若报告中的多个不同 I 性质必须联合表达、当前 schema 无法承载，该完整来源项保留在分母并记录 `unsupported_rule_schema`，不在规则化中重新挑选一个来源蒙混通过。所有选中的 P 来源必须进入公式计划；报告无明确 P 时以 `P=true` 表示无前提。

规则生成后，顺序为结构解析/确定性合成 → P/I/V 忠实度审查 → 数值、地址和编译关系检查。忠实度审查前不再运行来源重选、重复 P 谓词拒绝、Impact qualifier 缺失硬拒绝或编译后 P/I/V 可行性门。重复 P 谓词保留来源映射，由忠实度审查判断它们是重复证据还是不同事实被折叠。来源到核心观测量的关系对齐改为可重放的审查产物，不单独拒绝规则。完整来源分母在适用性判定后冻结；规则化成功和失败都保留在分母。`stage2-assessment.json` 增加按失败阶段分类的计数。

本次主线实现后已完成一轮 semantic-live-16 真实报告盲测：10 份未见报告、完整来源 P/I/V 分母 24，规则化通过 3/24（12.5%），10/10 份产物零调用 verify 通过。失败阶段中有 9 项为 `unsupported_rule_schema`、5 项语义忠实度失败、4 项 schema/校验失败、1 项证据/覆盖失败、2 项公式构造失败。结果与逐报告数据见[semantic-live-16 新一轮盲测报告](../evaluation/prompt_live30_live16_complete_piv_blind_10/REPORT.md)。该分母尚未由独立人工逐项裁定，不能解读为语义准确率。多 I 来源的表达能力仍受当前单 I 规则 schema 限制；本轮的 9 项 schema 不支持需逐项审阅后再确定是否扩展结构。

## 主线精简（2026-10-21）

P/I/V 定义与公式来源角色现在集中在 [`lib/piv_contract.py`](../lib/piv_contract.py)，提示词定义页作为兼容导出；`semantic_core.py` 和 `plan_synthesizer.py` 使用同一组 P/I/V 字段与来源角色。live 提示词从该契约渲染规范定义，并明确同一字段在不同时点必须使用不同观测变量和 checkpoint 描述。阶段二主线仍是：证据化影响清单；逐影响生成 P/I/V；在编译后的候选门统一检查 P/I/V 关系；最多进行一次针对失败公式字段的修复。只有完整 P/I/V 的影响进入规则 claim 和 `stage3-spec.json`；未能完整规则化的影响不生成空公式 claim，也不交给阶段三。规则化成功率的分母仅使用适用性判定选出的、具有完整报告依据的 P/I/V 影响项；缺要素项不进入成功数、分母或汇总计数，其逐项状态仍留在运行产物中供审计。完整 P/I/V 项即使规则化失败，也保留在分母。公式细节记录在 `constraints.json`，合格项规则化结果记录在 `stage2-assessment.json`。

## 逐影响适用性判定与完整项统计口径（semantic-live-15，2026-10-21）

逐 Impact 公式生成前新增一次适用性判定：对 Impact 清单中的每项选择直接适用且有原文依据的 P/I 来源，或标为 `explicit_but_insufficient` / `needs_review`。P 可来自有证据的前提/假设；I 可来自报告正文、明确的 NatSpec/标准要求或直接说明预期安全关系的修复建议。不得仅凭 Impact 后果、漏洞常识或实现修复步骤推造 I，也不得把其他章节的内容扩写成新的 Impact。

Impact 提取只扫描报告明确标注的 Impact 区域，按原文逐条提取主要且彼此不同的有害结果，每份报告最多 16 项；不合并相互独立的结果，不重复计入同一结果的解释性子句。完整 P/I/V 指每个角色均有正确且可追溯的报告依据；按当前契约，只有报告没有明示前提时 P 才允许为空。规则化成功率分母只含适用性判定选中的完整 P/I/V 项；缺 I、V 或应有而缺失的 P 的 Impact 不进入该分母，也不计入成功数或该项评测的汇总计数。逐项状态和未纳入原因保存在运行产物中，但不汇总为这项指标的数量。资格在公式生成前确定，因此后续规则化失败仍属于分母。若没有完整项，成功率记为不适用。重复、非主要或无明确原文依据的结果不作为额外合格项。

每张 `semantic-card.json` 只列该 Impact 判定选中的 P/I 及其证据；公式请求同样只含目标 Impact 和选中的来源与证据片段。无选中来源的项不调用公式模型，状态与理由保留。判定 prompt、模型响应、重试记录及逐项状态均落盘。`verify` 零模型调用校验判定 schema、原始候选范围、响应与保存结果、逐项卡片、公式请求范围及 `stage3-spec.json` 卡片哈希；历史 `source-scoped-v1` 产物仍走旧卡片重放路径。输入策略 v5 纳入 prose mitigation/recommendation 作为潜在 I 证据，同时继续排除 PoC、fenced code 和代码字段；历史策略仍可重放。

批次最大调用预算按 readiness、Impact inventory、核心要素、适用性判定和逐 Impact 形式化分别计算；语义忠实度审查及其格式重试也计入上限。

## semantic-live-15 真实报告复测（2026-10-22）

对冻结集中新抽且未运行的 10 份精确提交报告进行两批真实 DeepSeek Flash 运行；使用 `report-json-input/5`，无参考答案。10/10 输入筛选充分、都含明确 Impact 区域，共提取 32 条 Impact；适用性判定选中 25 条有 P/I 来源的候选，7 条因缺直接适用的明确 I 而标为 `explicit_but_insufficient`。6/25 条选中候选形成通过规则化和候选检查的完整规则（24%），4/10 报告通过候选门；其余 19 条选中候选主要失败于 schema/validation（12）、证据或影响覆盖对齐（3）、语义忠实度（2）和公式构造（2）。32 条 Impact 尚未经过独立去重/主要性审核，因此 25 项只是按来源选择结果得到的暂定分母，不能当作金标准。10/10 产物通过零模型调用 `verify`，本轮实际调用 106 次。详见[semantic-live-15 盲测报告](../evaluation/prompt_live28_report_scope_blind_10/REPORT.md)。

策略 v5 的输入范围扩展在这 10 份上确实被用到：10 份都有推荐/修复章节；共 18 条 I 候选引用了 v4 未纳入、v5 新增的文字。但这没有解决规则生成不稳定。与前一批 v14 的 3/10 候选通过相比，本批为 4/10；两批样本不同，且前批合格分母未逐项审核，不能据此断言整体准确率提升。

本轮全量工程回归 **458/458** 通过。测试期间修复了 live Prompt 别名兼容、策略 v5 的筛选边界分类和相应旧断言；`semantic-live` 稳定别名与 `semantic-live-15` 修订标签都可解析。

## 完整 P/I/V 分母口径盲测（semantic-live，2026-10-22）

在新的 complete-P/I/V 分母实现后，另从冻结精确提交集抽取 10 份未使用报告，保持 `semantic-live`、report-json-input/5 和 DeepSeek Flash 配置不变，无参考答案。仅把适用性判定选出的证据完整 P/I/V 项计入规则化分母；缺要素项完全排除，分母为零的报告记为不适用。结果为 **7/31（22.6%）**，6/10 份报告通过工程候选门；10/10 运行零模型调用重放成功，总模型调用 129 次。24 个有完整来源但未通过规则化的项中，16 个归为 schema/validation、4 个来源或影响对齐、4 个语义忠实度失败。两例分母为零，不参与汇总率。逐报告数据见[本批报告](../evaluation/prompt_live29_complete_piv_denominator_blind_10/REPORT.md)，冻结选择和配置也保存在同目录。

上一批 6/25（24%）与本批 7/31（22.6%）来自不同报告集，不能据此判断效果变好或变差。本批主要验证新分母在真实运行、落盘和 `verify` 重放中的行为；适用性分母仍由模型选择与确定性证据校验产生，尚未由独立人工逐项审定，也不等于语义准确率或 PoC 一致性结论。全量工程回归现为 **460/460** 通过。

## 分步 Impact 清单（semantic-live-12，2026-10-21）

Impact 提取是独立阶段：影响提取器只接收显式标注区域的证据目录；核心提取器另行生成 P/I、原因和步骤，若它误产影响项则丢弃并留存审计记录；经过来源校验的 Impact 清单再并入要素，逐影响生成 P/I/V。新清单要求影响文本逐字摘自所引 Impact 证据（仅允许空白规范化），且不允许 `inferred` 影响项；历史 `/1` 清单仍可离线重放。没有明确标注区域、区域内没有明确伤害结果、区域存在歧义分别记录为 `no_marked_impact_section`、`no_explicit_impact`、`needs_review`，均停止 P/I/V 规则化。P/I 可引用报告中明确支持其角色的内容，但不得据此新增影响或扩写 V；V 只能来自对应 Impact 原文，并保留其条件和语气。

10 份新冻结报告的盲测结果：0 例 Impact 来源越界拒绝、校验重试或核心提取器误产影响项；10/10 零调用重放通过。8 份生成了影响评估，共识别 22 项、9 项完整规则化（40.9%），5/10 通过候选检查。5 份候选的同模型族盲审为 3 faithful、2 weakened。相较上一轮这是不同留出集，不能做配对提升判断；来源边界问题已被输入隔离控制，但完整率和语义忠实度仍是瓶颈。详见[本轮报告](../evaluation/prompt_live12_impact_inventory_01/REPORT.md)。

对来源依据、意图范围、示例绑定、占位谓词、混合单位和符号表的独立诊断已从 `semantic-live` 主线关闭，避免并行产出多套诊断门；必要的来源/类型/数值/关系确定性验证仍保留，语义忠实度审计仍作为唯一额外模型复核。`--formal-retries` 默认最多一次，局部修复失败即把该影响项标为未规则化，不再升级为整份计划的重新生成。

## 已生成规则的忠实度评测（2026-10-21）

按当前评测口径，只统计已生成 P/I/V 公式是否忠于报告，不评影响覆盖，也不把没有生成公式的项算作不忠实。在 30 份产出规则的报告中，共盲审 63 个 claim、189 条 P/I/V 角色公式；逐公式完全忠实率为 133/189（70.4%），P 为 42/63、I 为 47/63、V 为 44/63。P/I/V 三条公式同时完全忠实的 claim 为 28/63（44.4%），其余 35 个 claim 至少有一条公式被评为部分忠实；未评出 fail。评审器与生成器同属 DeepSeek Flash 模型家族，结果不等同于独立人工金标准。详见[规则忠实度报告](../evaluation/piv_contract_checkpoint_regression/REPORT.md)和[逐条评分](../evaluation/piv_contract_checkpoint_regression/FAITHFULNESS_ALL_RULES.json)。评测时发现并修复了 `solve_queries()` 的 `p_name` 变量作用域错误。

## 主线目标

阶段二的唯一主线是：**把漏洞报告明确声称的安全性质，转成带原文证据、语义角色和适用范围的可审计规格，并稳定交给阶段三。**

Impact 只从报告明确标注的 Impact 区域提取；P/I 证据可从报告正文、明确的 NatSpec/标准要求及直接说明预期安全关系的修复建议中寻找。输出以 P/I/V 表示报告中的前提、应满足的性质和直接违反效果，再生成确定性 AST、SMT/Z3 查询及 `stage3-spec.json`。每项输出都要能追溯到报告证据，未表达或无法判断的内容须保留为未决项。Z3 只检查公式内部关系；阶段二不判断报告真假，也不证明 PoC 与报告一致。

因此阶段二的完成标准不是“模型总能给公式”或“所有案例都通过”，而是以下交付闭环成立：

1. **报告到规格可追溯**：原文、证据编号、P/I/V 角色、符号来源、公式子项和限制能相互核对；关键语义缺失时能拒绝或明确标为部分表达。
2. **规格构造可重复**：程序确定性合成并执行结构、来源、类型、单位、数值、关系和逻辑检查；候选、待审、拒绝与流水线故障有不同状态。
3. **运行结果可审计、可重放**：模型请求与响应、提示词快照、功能开关、修复记录、审查产物及其哈希链完整；`verify` 不调用模型即可重放已保存的运行。
4. **交接边界稳定**：`stage3-spec.json` 清楚表达待绑定规格及其证据/哈希；不把未完成的代码绑定或执行结论伪装成阶段二结果。
5. **质量结论有边界**：开发集与冻结留出集分开；报告完成率、语义忠实度、拒绝质量、误放行/误拒绝、调用成本及评审局限，不以候选率或 Z3 通过代替语义正确性。

## 当前判断

- **核心工程链已建成**：报告独立输入、提取前筛选、证据化 P/I/V、确定性合成、Z3 检查及阶段三规格输出均已实现。阶段二不是从零开发状态。
- **S19 工程收口验证已完成（2026-10-20）**：全量本地回归 **435/435** 通过；另有一条预算回归断言，确认 `semantic-live` 的批次最大调用数包括语义忠实度审查及其一次重试。`git diff --check` 通过。交接文档指定的 v3.17 Monetrix/Olas 两个历史候选和最近 `prompt_live5_fidelity_01` 的 4 个候选均通过零模型调用 `verify`；其中 4 个最新候选也各自通过 `stage3-spec` 接口哈希检查。
- **收口后的首项语义质量修正**：针对 Covenant 报告内 `2^noCapLimit` 且同句给出 `noCapLimit = 60` 被误拒的问题，数值门现可解析同句唯一整数绑定，并对缺失/冲突绑定继续拒绝。保存的 Covenant 模型计划现通过数值门；全量回归 **437/437** 通过。未调用模型、未改 Prompt，也未把这次单例机制验证当作泛化评测。详见[离线修正记录](../evaluation/semantic_quality_symbolic_bound_01/REPORT.md)。
- **历史重放范围说明**：对仓库中 130 个含 `constraints.json` 的目录做了额外离线扫描，94 个通过，36 个未通过。未通过项均来自归档/旧结果，错误分布为原报告缺失 6、旧 Prompt 版本名 8、Prompt 与现存冻结模块不匹配 16、历史数值 P 来源校验不匹配 3、旧 ID 形式解析不匹配 1、SMT/bundle 重放不匹配 1、正式 Prompt 文件缺失 1。它们不在本轮指定的当前及 v3.17 兼容锚点中；因此结论限定为当前交付与指定历史锚点通过，**不声称所有历史归档产物均可由当前 verifier 重放**。这次扫描是范围盘点，不把旧归档失败归因于 S19。
- **最新忠实度测量**：2026-10-20 冻结 5 份新报告并真实运行当前 `semantic-live`，工程候选 4/5；两阶段盲评把 4 个候选均评为 `weakened`，没有评为 `unfaithful`，另有 1 例疑似数值门误拒。异构评审对其中 3/4 个候选的影响覆盖不足给出 partial。4 个候选的零模型调用 `verify` 均通过。详细拆分和改进建议见[本批报告](../evaluation/prompt_live5_fidelity_01/REPORT.md)。
- **覆盖/关系精度提示复测**：随后冻结 5 份未见报告，进行两阶段盲评和异构复核。4 份生成候选、1 份被 P 忠实度审查拒绝；复核认为该拒绝理由存在误读。12 项报告侧影响中，4 项进入 claim、6 项未形式化、2 项因拒绝而无规格；4 个候选的核心 P/I/V 均被盲评为 weakened。初次运行的覆盖清单字段错误已修正，4 份保存产物离线重放均通过 `verify`。评审为同一模型、小样本，不能据此宣称忠实度提升；详见[复测报告](../evaluation/prompt_live6_fidelity_01/REPORT.md)。
- **核心忠实度与影响覆盖现已分开记录**：对 `prompt_live5_fidelity_01` 的回溯重评分显示，4 个候选核心 P/I/V 全部 faithful 的为 1/4；分项 P 为 2 faithful / 2 partial，I 为 2/2，V 为 2/2。报告侧 12 项候选直接影响中有 2 full、2 partial、6 deferred、2 not extracted；另有 Covenant 3 项因误拒未形式化。详见[范围调整评分](../evaluation/prompt_live5_fidelity_01/SCOPE_ADJUSTED_REVIEW.json)和[评测口径](../evaluation/README.md)。这是同模型评审理由的事后重编码，提示影响覆盖和抽取都值得后续测量，但不足以单独决定多 claim 架构；需由后续新批次按分层协议复核。
- **阶段二不以无限加规则作为完成条件**：只有出现可复现、可泛化的缺陷模式并通过冻结留出验证，才立项扩展表示或规则。
- **阶段三的代码变量绑定、PoC 执行分析和一致性结论不属于阶段二收口项**；它们消费 `stage3-spec.json`，应由阶段三完成。

## 收口结论

- S19 代码审阅、全量本地回归、指定历史候选重放和文档状态同步均已完成；阶段二**工程主线可标为完成并交接阶段三**。
- 完成范围包含报告证据化、P/I/V 规格构造、确定性检查、零调用重放以及 `stage3-spec.json` 接口。历史归档有明确兼容边界，见上文；语义评测限制和多影响覆盖缺口仍作为已知质量限制单独记录。
- 语义准确率不设“百分之百”门槛。后续若有新证据支持的质量改进，应作为独立、可测量的迭代，不倒灌为阶段二工程收口条件。

---

以下为阶段二早期设计和按日期记录的历史状态，保留实验上下文，不再作为当前待办清单。

当前活动工作流已按需求改为**提取前筛选**：DeepSeek 在生成 P/I/V 前，只判断报告是否
具备受影响对象、触发/行为、直接效果和可推导安全关系依据。明确缺失写入
`excluded_before_extraction`；仅不确定则写入 `needs_input_review`；两者均不创建 P/I/V。此前基于生成结果的 `screen_cases.py`
后筛选及独立语义复核已退出活动工作流；其历史结果保留，但不再控制新运行。
[两份真实报告入口测试](../evaluation/archive/input_gate_01/REPORT.md)确认：信息不足案例经 1 次调用后
停止且不生成要素；信息充分案例才进入 P/I/V 调用。后者随后可被原有要素合法性检查拒绝，
说明“可进入”与“生成正确”已分开处理。

最新 [DeepSeek-V4.1-Flash 三份新报告测试](../evaluation/archive/deepseek_v41_fresh_01/REPORT.md)
得到 3/3 有效要素、2/3 候选公式及 Z3、0 例语义已证实。现在可选
`--continue-on-review`：核心 P/I/V 公式和直接违反关系齐备时，
次级影响未覆盖、报告歧义等仅作为警告，不再把 `needs_review` 当作流水线失败；
仍保留 `semantic_truth_verified=false`、`execution_ready=false`，关键缺失继续拒绝。
仅复核了旧输出与离线续跑，未因这项路由调整再次调用外部模型。
旧的离线后筛选及独立复核曾用于发现 Hybra/Sequence 的语义错误，但并非用户要求的
入口筛选，因此只保留为历史实验，不再出现在推荐命令中。

最新前瞻性小测已[冻结 8 份未用于调规则的报告](../evaluation/fresh_holdout_01/README.md)，
分属 8 个项目。经用户明确授权后八例均已真实尝试：要素提取 4/8，形式化与 Z3 1/8；
2 例 JSON 错误、5 例超时。唯一完整候选仍为 `review`，且本地检查发现公式遗漏
“没有真实付款”的限定，不能报告语义准确率。详见[首次测试报告](../evaluation/fresh_holdout_01/REPORT.md)。
原批次 v3 输入还误纳入 Morpheus 报告的无标题修复建议；已停止外部调用并在本地修正。

后续[开发复验](../evaluation/archive/recovery_v312_01/REPORT.md)新增首步可选一次重试、超时元数据诊断、轻量第二步输入及保持正常执行限定的 `semantic-v3.12`。Brix 的一次网络环境复验再次在 240 秒处超时，未生成新公式；当时轻量模式的外部调用因衍生语义数据外传范围未获明确授权而被拒绝。现已新增[阶段二 DeepSeek 官方 API 可选直连](DIRECT_DEEPSEEK_SETUP.md)，并在新获授权后进行了[三报告真实开发测试](../evaluation/archive/deepseek_flash_pilot_01/REPORT.md)：首步 JSON 3/3、要素校验 2/3、有效正式计划及 Z3 均 0/3。五次调用均未超时，但三例最终皆为 `pipeline_failure`，没有证明真实流程成功率或语义准确率提高。原 8 例首次结果不变。

[机械修复与部分继续](../evaluation/archive/deepseek_flash_salvage_01/REPORT.md)保留原始成绩，另在新目录离线重放 Kinetiq、规范化 Virtuals ID 后仅补跑其第二步。继续后的 3 例要素可用、2 例有公式/Z3，但两例均 `needs_review`：Kinetiq 缺关键算术关系且 I 可能过强；Virtuals 把“报价错误”反写成 I 要求的效果。Olas 的 `elapsedTime > 0` 被布尔化，仍由数值保真门阻断。**模型响应快与 Z3 互斥均不等于忠于报告**。

最新 [v3.14 GTE/Hybra 开发复验](../evaluation/archive/prompt_v314_polarity_01/REPORT.md)增加复合限定、
乘积关系、定量信息保留和 I/V 极性自检。GTE 现已真实完成形式化与 Z3，I 为“满足条件
时不应回退”、V 为实际回退；Hybra 已生成 `shares_minted >= fair_shares`，但模型仍把
`!= 0` 弱化为未约束符号或布尔量，数值保真门正确拒绝。该结果说明工程链和方向控制有
实质进展，但数值 P 忠实性仍是当前瓶颈。

最新 [v3.14 十份冻结留出集测试](../evaluation/archive/prompt_v314_holdout_01/REPORT.md)已使用
DeepSeek `deepseek-flash` 完成：8/10 生成合法要素，7/10 生成形式候选和 Z3，6/10 可按
带警告策略继续。对 7 份候选的证据复核发现，只有 1 份 P/I/V 均无明显核心偏差；该数值
不是总体准确率，只用于定位问题。8 份合法自然语言要素的核心 P/I/V 均有报告证据，失真
主要发生在公式合成：I 范围过强/过弱、P 混入示例条件或 bug 状态、V 被替换为无关效果。
另有一例因“最多两个直接影响”的模式限制误拦截、一例被数值保真门正确拒绝、一例首步
JSON 格式失败。当前首要瓶颈因此从要素识别转为**关系框架和形式化语义保真**。

2026-09-20 已完成 `semantic-v3.15` 的本地实现：增加 12 类通用安全关系、
`relation_obligation`、`monotonicity`、`conservation` 三种确定性模板，支持有单位的
加/减/乘关系。要素层允许保留 1–4 个直接影响，单个形式计划严格选择一个影响。程序会拒绝关系类别与模板不兼容
的计划；还会要求 I/V 核心观测量的来源覆盖所选安全意图和全部直接影响，并生成
`relation-alignment.json`。v3.14 文件和冻结结果均未改写。

授权后已完成 OLAS、Merkl、Panoptic [v3.15 开发回归](V315_DEVELOPMENT_REPORT.md)，并在
规则冻结后完成[五份全新报告留出测试](../evaluation/archive/prompt_v315_holdout_01/REPORT.md)。留出集
工程完成率 4/5；4 份完整结果的关系分类初评均合理，但严格 P/I/V 公式全通过为 0/4，
2/4 只能算 partial，2/4 有关键公式错误却被放行；另有 1/5 因就绪响应多出字段被误拒绝。
因此当前瓶颈已经明确为公式忠实度和独立语义降级门，而不是关系类别数量。

随后又在规则保持冻结的情况下完成[第二批五份全新报告留出测试](../evaluation/archive/prompt_v315_holdout_02/REPORT.md)：
5/5 报告均通过输入筛选并生成合法要素，但仅 1/5 生成最终候选。其余 4 份报告信息充分，
失败分别来自关系模板兼容、来源绑定、P 证据缺失和 JSON 格式问题。唯一候选 Monetrix 的
关系分类合理，但预期小数位没有绑定为底层小数位与 offset 之和，且 P 混入错误返回值，
严格公式仍不合格。两批合计 10 份报告中 9 份生成合法要素、5 份形成最终候选，5 份候选
严格 P/I/V 全通过仍为 0；这说明当前首要问题是形式计划/公式合成稳定性与语义忠实度，
不是自然语言要素完全无法提取。

在此基础上已实现 `semantic-v3.16`：关系类别固定模板、派生量定义和字段级局部修复。
[五例开发回归](V316_DEVELOPMENT_REPORT.md)最终 5/5 形成候选，但严格公式初评只有 1/5，
说明工程完成率提高不能代表准确率。规则冻结后的
[五份全新报告测试](../evaluation/archive/prompt_v316_holdout_01/REPORT.md)得到 5/5 合法要素、3/5 最终
候选、严格公式 1/3；Sequence 为 partial/pass/pass，SukukFi 为 pass/pass/pass，Merkl 因
遗漏提现后的余额不足条件而三项公式失真。另有一例把 ERC-4337/EIP-191 误识别为未覆盖
数值 P 而被机械误拒绝。当前下一优先级是修正数值标识符识别和检查 impact 限定是否进入
公式 condition，而不是继续增加关系类别。

上述改进已在本地实验版 `semantic-v3.17` 实现：现有 12 类关系映射到权限、边界、比例、
状态对应、时序、进度、单调和守恒等专用模板；`qualifier_types` 将强限定分为时间、阈值和
状态三类，`impact_context_terms` 把对应谓词加入 I/V；
P 符号必须由各自来源支撑且不同来源不能复用同一谓词；协议标准编号不再作为数值约束。
清理退役切片绑定分支时，主线全量本地回归曾为 **300/300**；此数字是当时快照，不代表当前测试规模。v3.16 三个历史完整候选仍可离线重放。授权后的五例开发
回归得到 2/5 候选和 2/5 带警告继续；两例都通过离线重放。Olas 核心公式较完整，Monetrix
部分正确；另外三例暴露影响来源联动、派生定义结构和关系错配问题。该批是开发集，不代表
泛化准确率，推荐入口暂时仍为 v3.16。详见
[v3.17 实现报告](V317_IMPLEMENTATION_REPORT.md)和
[五例开发回归](../evaluation/archive/prompt_v317_development_03/REPORT.md)。

## 已完成

2026-10-05 起 Prompt 管理切换为**单一活文件**：`prompts/current.py`
（`semantic-live`，默认版本）是唯一可原地修改的提示词，初始文本逐字节等于
`semantic-v3.20` 的解析结果；`prompts/versions/` 16 个冻结文件转为只读存档。
功能开关经 `registry.feature_enabled` 与 live 的 `FEATURES` 声明解耦，每次 neural
运行把 prompt 快照（`prompt-element.txt`/`prompt-formal.txt`）与功能决策
（`prompt_features`）写进 run 目录，`verify` 优先回放快照，因此原地修改 live
不再破坏历史 run 的可验证性。切换时已核实 live 与 v3.16/v3.20 的功能门完全一致
（切换只改文本、不改门行为）。政策与重放契约见
[PROMPT_LIVE_POLICY.md](PROMPT_LIVE_POLICY.md)。

2026-10-06 完成第一次 live 原地修改（`semantic-live-1`），针对 blind_03 归因的
要素层 P 缺陷：**禁止后置观察量进入 P**。要素 prompt 新增两条规则——(a) 动作自身
产出的观察量（post-state、unchanged/stays 断言、动作计算的量）无论报告如何以
事实口吻陈述，都不是 precondition，而是 outcome；(b) P 使用先前状态必须有独立
片段在动作开始前确立它，否则移出 P 并在 ambiguities 记录时点循环。输出前的逐条
自审也加入"引用片段的观测时点"检查。规则有守护测试
（`test_prompt_live.py::test_live_element_prompt_keeps_p_temporal_role_mandate`）。
该改动已于 2026-10-06 在全新冻结批次
[`prompt_live1_blind_01`](../evaluation/prompt_live1_blind_01/REPORT.md)上测量
（5 份未见报告，排除全部历史 case/报告/输入哈希，DeepSeek 直连 18 次调用，
经用户授权）。结果：**目标缺陷未复现**——5/5 案例的 P 全部为动作前状态，
后置观察量进 P 为 0 例；先前状态缺乏动作前片段时模型改为在 ambiguities 如实
记录而非断言（SukukFi、Hybra 均可见此行为）。要素层 P/I/V 5/5 通过。工程
完成率 2/5 候选，两例均通过零调用离线 verify 且**首次走 `prompt_snapshots`
快照重放路径**（活 prompt 政策的可验证性契约端到端成立）。3 例拒绝全部在
形式化阶段且与要素层无关：2 例为数值保真门误伤叙事性 assumption（数字已在
P 中编码），1 例为单位门正确拦截 `expected_rate = total × 1` 伪造定义（根因
是 DSL 缺除法、rate 类量无法表达）。唯一公式缺陷（SukukFi 的 I）为形式化
阶段引入的适用范围收窄。该批 n=5 且与 blind_03 报告集不相交，比例不可跨批
比较，只用于归因。

2026-10-06 按该批归因完成三项修复（合称 `semantic-live-2`）：

1. **数值门 assumption 豁免**（代码）：`check_numeric_plan` 新增
   `relax_assumptions` 门（feature `assumption_numeric_relief`，live 为
   True、全部冻结版本为 False）。含字面量但未编码的叙事性 assumption
   不再强制进 P；**已编码语句的字面量保真检查与 precondition 严格行为
   完全不变**。零模型调用的离线
   [probe](../evaluation/prompt_live1_blind_01/PROBE_ASSUMPTION_RELIEF.json)
   证明 Kinetiq/Intuition 已保存的重试计划在新门下通过且可合成，冻结 run
   结果不被改写；live1 两个候选的 verify 重放不受影响（旧
   `prompt_features` 无新键，回放按严格门执行）。
2. **rate 类量规则**（live prompt）：QEXPR 无除法，禁止乘 1 等常数硬凑
   单位相等；须改写为 amount 层不变量或交叉相乘，确无重述时返回
   blocking `unsupported_relation`。**不新增 DSL 除法**：整数除法的截断
   语义会使 rate 相等产生更弱的 I，违背数值保真原则；单位组合依赖命名
   约定且给 `mul` 加单位消除会威胁冻结 run 的确定性重放。
3. **I 适用条件规则**（live prompt）：I 的 condition 须承载 intent 陈述的
   全部适用限定词（caller≠owner、任意未授权 caller 等），不得收窄到具体
   事件子场景；报告只确立子场景时保留窄形并在 limitations 记录。输出前
   自审清单新增第 7 条逐项核对。

live-2 的 prompt 规则（第 2、3 项）有守护测试
（`test_prompt_live.py::test_live_formal_prompt_keeps_rate_and_i_applicability_mandates`），
其效果已于同日在全新冻结批次
[`prompt_live2_blind_01`](../evaluation/prompt_live2_blind_01/REPORT.md)上测量
（5 份未见报告，排除含 live1 的全部历史 102 case/104 报告/108 输入哈希，
DeepSeek 直连 16 次调用，经用户授权）。结果：

- **工程完成率 3/5 候选**（live1 为 2/5），三例均通过零调用离线 verify
  （`prompt_snapshots`）；要素层 5/5 P/I/V、后置观察量 0 例。
- **`assumption_numeric_relief` 验证**：叙事性 assumption 误拒 0 例
  （live1 为 2 例）；本批数值门两次触发均为正确拦截（自比较占位符、
  界被布尔化）。
- **I 适用条件规则成立**：三例候选的 condition 均承载报告一般性限定，
  无子场景收窄。rate 规则未被本批行使（无 rate 案例）。
- 候选公式严格全通过 2/3（GTE 的 I 为可观测弱化 partial，报告无更强
  编码依据）。
- 2 例拒绝同属一个新的形式化阶段族：首次缺陷被门正确拦截，修复方向
  正确但 (a) 修复须改 `pattern`（field-scoped 冻结字段）被丢弃，(b) 离线
  复核证明修复后的计划仍不满足数值门——显式界被写成非文本字面量常量
  （2^12 vs bits [36:48)）或符号常量（`cl_gauge_type_constant` vs 常量 1）。
  下一优先级因此是"界须用报告字面量常量表达"的 prompt/修复反馈层改进，
  其次才是放行 `pattern`。

全量本地回归 342 例，失败 10 例均为既有基线（冻结 run 哈希漂移与未提交
加固遗留），无一由本次改动引入。

2026-10-06 晚按 live2 归因完成 `semantic-live-3`（第三轮原地修改），并冻结
反过拟合纪律：

- **终局保留批** `final_holdout_01`（10 例、两个 manifest）冻结于本轮任何
  修改与选样之前：永不进迭代、迭代期间不做任何语义查看；循环停止后用
  当时的 live prompt 跑一次（n=10），是整个迭代循环的唯一无偏测量。所有
  后续迭代批的 select.py 经 SELECTION.json 扫描自动排除这 10 例。
- **停止规则**：最多再迭代 2 轮（live-3、live-4）；任一轮相对上一盲批无
  实测改善即提前停。**记分口径是忠实结局**（正确通过 + 诚实的未编码/
  拒绝），不是原始候选率——目标是无损翻译，门把伪造常量拦下来是忠实行为。
- live-3 三项修改（归因：live2 两例拒绝同族，满足"≥2 独立失败案例"规则
  吝啬门槛）：
  1. formal prompt 新增显式界常量规则：界的常量必须是所引报告文本中出现的
     字面量（`right:{"const":N}`）；禁止用计算值表达（"12-bit"/bits [36:48)
     绑定 12，绝不写 2^12/4096/掩码）；枚举界（`type == 1`）用常量而非命名
     符号；文本无字面量时该界转 unresolved，不得发明常量。
  2. 修复反馈（`formal_retry_hint` 的 numeric P 分支）给出同样的常量形式
     处方，此前反馈只报错不给药。
  3. `formal_repair_fields` 的 numeric P 分支加入 `pattern`：数值门修复本就
     常须重写出问题的比较谓词本身，此前该字段被冻结导致方向正确的修复被
     机械丢弃（live2 两例的最终死因之一）。
- 守护测试：`test_prompt_live.py` 新增常量规则短语锁定与 numeric 修复字段
  含 `pattern` 断言。live1/live2 全部 5 个候选 run 在改动后仍
  `offline_verified: true`（快照重放不受 prompt 原地修改影响，重放契约
  继续成立）。全量回归 344 例，失败 10 例仍为既有基线，零新增。
- 盲测批次 `prompt_live3_blind_01`（10 例，两个 manifest，盐排序冻结、
  排除含保留批的全部历史）已于同日跑完并测量，
  [REPORT](../evaluation/prompt_live3_blind_01/REPORT.md)结果：
  - **工程完成 6/10 候选**（live2 为 3/5，同为 60%，样本翻倍），六例全部
    离线 verify 通过；要素层 9/9 可评全过、后置观察量 0；公式 I/V 全部
    6/6 严格通过，公式 P 4/6（两例重复谓词塌缩 partial）。
  - **live-2 的常量表达拒绝族清零**：live2 拒绝的 Panoptic 家族新案例被
    "门拦 → 修复通道改写谓词 → 通过" 救回；接受计划的界常量全部来自
    报告文本。三项 live-3 修复点全部验证生效。
  - 拒绝 4 例 = 1 误伤（`0x811` 十六进制协议常量被计为字面量，n=1 暂缓）
    + 2 正确拦截（伪造单位乘积定义、伪造 curve 恒等式）+ 1 诚实弃权
    （输入筛查）。数值门 assumption 误伤连续第二批为 0。
  - 顺带修复 verify 缺陷：要素层重试的 run 此前重放必误报
    `neural elements changed`（比对首次而非最后一次尝试）。
  - 按停止规则：live-3 相对 live-2 无工程完成率提升但拒绝族迁移且修复点
    全部生效；**live-4 为最后一轮迭代**（目标：重复谓词塌缩、修复纪律），
    之后进终局保留批 n=10 终测。

2026-10-07 完成最后一轮原地修改 `semantic-live-4`（归因：live3 两例重复谓词
partial 同族 + live1/live3 修复通道原样返回同族，满足"≥2 独立失败案例"规则；
hex 0x811 误伤 n=1 继续暂缓）：
- 自审第 3 条扩为禁重复谓词：两个不同前置来源不得共用同一条谓词（合取
  塌缩 = 一条事实失表达）；第二条事实无独立约束时移入 assumptions。
- 修复反馈新增 `local repair made no change` 专属分支（原样返回即"什么都没
  修"，须改出可见差异或如实迁移），type/unit 反馈补交叉相乘处方并禁止
  再定义单位乘积符号。
- 守护测试 15/15；全量回归失败集 = 已知 10 例基线的严格同集（4× element
  prompt hash mismatch、1× evidence catalog missing、1× PilotReplay、
  2× triage、1× batch retry_count、1× BOUNDARY）；live1/live2/live3 全部
  11 个候选 run 离线 verify 重放不变。live-4 盲测批见后续条目。

2026-10-07 `semantic-live-4` 盲测批（`prompt_live4_blind_01`，10 例全新报告，
排除全部历史含保留批）当日跑完并测量，
[REPORT](../evaluation/prompt_live4_blind_01/REPORT.md)结果：
- **工程完成 6/10 候选**（连续第三批 60%），六例全部离线 verify 通过；
  公式 V 6/6，P/I 各 4/6；要素层 10/10 可评，I/V 全过，P 一例捆绑动作+
  状态 partial。
- **live-3 最大拒绝族（type/unit 伪造定义）清零**：Hybra/Intuition 新实例
  全成候选；Intuition 首试 type/unit 拒绝经交叉相乘处方修复通过——live-4
  处方生效。重复谓词禁令未生效（Hybra 同形塌缩复现）；no-change 专属反馈
  在 `--formal-retries 1` 下机械不可达（最后一次尝试校验中抛出，重试已
  耗尽），两例确认。
- 拒绝 4 例 = 1 误伤（`0x811` hex 族第二独立案例，门槛凑满）+ 2 正确拦截
  （修复方向正确但单次重试耗尽；`source missing` 反馈不点名缺失源）+
  1 修复纪律失败。
- **预注册 hex 修复已应用**（`HEX_IDENTIFIER` 掩码：`0x` 前缀常量按协议/
  槽位标识处理，不计入字面量扫描；bounds 路径不受影响，真十六进制界仍
  强制）：守护测试 + Monetrix 离线解锁证明（HEX_UNLOCK_PROBE.json）+ 全量
  回归基线同集 + live1–4 全部 17 候选重放不变。方向与触发条件均在 live-3
  报告预注册，非事后调参。
- **停止规则触发：prompt 迭代到此停止**（live-1..4 共 4 轮原地修改 + 1 次
  预注册门修复）。未预注册项只披露不实施：no-change 反馈可达性（需
  retries ≥ 2）、`source missing` 反馈点名缺失源、重复谓词拒绝化。下一步
  是终局保留批 final_holdout_01 一次性终测（n=10，冻结于全部迭代前）。

2026-10-07 晚 **终局保留批终测完成，阶段二收口**。三批同模型双复核（live3/
live4/终局，共 30 次 deepseek-flash 异构审计调用）与终局批主复核
（[REPORT](../evaluation/final_holdout_01/REPORT.md)）结果：
- **终局 8/10 候选**（live1-4 均 60% → 终局 80%），八例全部离线 verify
  通过；32 次调用、超时 0、JSON 失败 0、要素层弃权 0。
- **两例拒绝均为 Z3 一致性正确拦截**（数值门拒绝 0、误伤 0）：Merkl P
  钉死违约后果（P∧I 不可满足）、Panoptic__Next_Core P 并置互斥分支
  （P∧V 不可满足）——缺陷被拦下而非作为产物放出。
- **忠实结果 8/10**（公式严格全过 6/8 + 一致性正确拦截 2；两个漏网
  缺陷 GTE_Perps 重复谓词、SukukFi 文档要求混入 P 均为"可见不拒绝"型，
  双复核独立抓到，无一被静默当真）。
- 双复核与主复核在核心缺陷形态（谓词塌缩）上跨三批收敛；分歧集中于
  适用范围收窄的严格度（双复核更严）；无案例在两套口径下互换通过/拒绝。
- 迭代披露：prompt 4 轮 + 1 次预注册门修复，全部在终局批冻结之后发生且
  与其样本不相交；终局配置与盲批一致（含已披露的 no-change 反馈不可达
  缺陷）。无独立金标准（`independent_gold: false`）为根本局限，已在终局
  报告声明。剩余已知缺陷族以披露形式移交，不再迭代。

2026-10-07 深夜 **阶段二事后准确率测评完成**（`accuracy_gold_01`，
[REPORT](../evaluation/accuracy_gold_01/REPORT.md)，全部 40 个冻结 run、
80 次 deepseek-flash 调用、零产物改动）。金标准由同模型两阶段盲裁判提供
（受全程同模型约束；Phase 1 只看报告原文写 shadow 重述，Phase 2 对照
自评，盲于接受状态/主复核/双复核；自偏好局限已披露）：
- **翻译层核心结论**：150 个维度评级 unfaithful 仅 3 例且全在 I 维度；
  P/V 维度（100 评级）0 unfaithful。逐条裁决后 2 例（live2 Intuition）
  被报告原文推翻为裁判误读（绑定缺陷在计划 condition 中、relation 是
  报告原句字面编码），1 例（live4 Panoptic 循环 I）为真实缺陷但主复核
  与双复核已同形抓到——**金裁判零新增失真发现**；其独立机械检查
  （报告外常量 0、重复谓词 6 条）全部收敛于已知缺陷族。
- **weakened 大量为单主张压缩（设计取舍），非失真**；严格六维口径
  0/25 不适合作为阶段二目标函数。
- **金裁判在机械拒绝层不可采信**（10/15 判 misfire vs 主复核 ~2 误伤）：
  漏判终局 Panoptic 的 P 自相矛盾（Z3 拦截），同一 `0x811` hex 族两批
  判出相反 verdict。拒绝归因维持主复核 + 双复核口径。
- 系统准确率多层：严格 12%（0+5）/40、忠实 70%（23+5）/40；采信口径
  重述为 **25 候选中 24 无失真评级（96%）、15 拒绝中 12 正确拦截/诚实
  弃权**。金与主复核公式层一致 24/54，分歧全为主复核 pass vs 金
  weakened（口径差，无通过/拒绝互换）。
- 既有"仍未解决"第 1 条（无独立核实的准确率）就此部分补足：同模型
  盲金已测，人类金标准仍未获得。

2026-10-08 **收口后按任务目标补充一次结构性迭代（`semantic-live-5`）**。
依据用户的任务定位（从自然语言报告**推导**声称的不变量，再形式化为
第三阶段可用的约束——不变量不是给定规则而是要被推导出来的），在
不回改任何冻结产物的前提下完成五项修改，全部经 feature 门与
`semantic-v3.16`/`semantic-v3.20` 冻结集解耦（四个新 feature：
`duplicate_predicate_gate` / `requirement_source_review` /
`intent_scope_review` / `partial_formalization`，live=True、冻结=False，
历史 run 按自身 `prompt_features` 回放）：
1. **阶段三绑定契约 + 反馈闭环**（新模块 `lib/stage3_consistency.py` +
   命令 `stage3-feedback`）：每次 run 的 `stage3-spec.json` 附带
   `binding_contract`（P/I/V 每个符号的 `appears_in` 角色与
   binding_kind：boolean_predicate / address_value / numeric_value），
   第三阶段代码侧执行后回填 `stage3-consistency-feedback/1`，程序
   落盘**真实** `consistency_verdict`（partial_binding /
   preconditions_infeasible_on_code / violation_reproduced /
   violation_not_reproduced / inconclusive）。落盘一次性、拒绝覆写
   （replay 不改判定）。这补上"金标准只能来自代码执行"缺的环：
   此前 `poc_consistency_verdict` 恒为 `not_evaluated`。
2. **重复谓词门收口**（`check_distinct_p_predicates`，生成期拒绝）：
   终局 GTE_Perps 的"可见不拒绝"缺陷（两个 P 来源共用同一 truth
   谓词）此前只有 prompt 自审约束，live-4 已证无效；现在机械拒绝，
   消息与 v5 schema 同串（修复通道与 BOUNDARY 表路由不变）。
3. **来源混入 advisory**（`requirement_source_review` →
   `requirement-source-review.json`）：P 来源文本引用文档/规范
   要求（终局 SukukFi 缺陷族）时列出但不拦截——n=1，按阈值纪律
   只披露不设门。
4. **意图范围 advisory**（`intent_scope_review` →
   `intent-scope-review.json`）：intent 含全称线索（for any 等）而
   condition 符号只被 impact 证据支撑时标记 scope_narrowing_risk，
   同为 advisory。
5. **部分形式化通道**（`partial_formalization`）：DSL 无法表达的
   rate 类关系（live1 Hybra `expected_rate = total × 1` 伪造同根因）
   改为允许**一个**声明的 bool 符号代表整个关系（source_ids 须覆盖
   关系全部来源），同时把缺失的数值定义记为**非阻塞**
   unsupported_relation 交阶段三绑定——机械降级仅在计划已表示该
   关系时发生，不发明语义；审计落 `partial-formalization.json` 并
   进 verify 重放（含"审计缺失即失败"的反向门）。
两项 advisory 与绑定契约哈希均链入 interface 指纹（verify 校验）。
**测量边界如实声明**：本迭代只有本地回归测量——新增 19 项测试
（`tests/test_stage3_contract.py`）全过，守护/快照 39/39，全量回归
失败集与已知 10 例基线严格同集，live1–4 + 终局批共 25 个候选 run
离线 verify 重放全部不变（中途发现并修复 `-m cli.*` 子进程的
`stage3_consistency` 裸名 import 缺失，compat ALIASES 15 名）。

2026-10-08 当晚 **final_holdout_02 终测完成**（判据预注册的
[REPORT](../evaluation/final_holdout_02/REPORT.md)，n=10 全新报告实例、
46 次模型调用、经用户授权）。semantic-live-5 的测量结论：
- **工程完成 5/10 候选**（全部离线 verify 通过）；**五例拒绝全部为
  正确拦截、误伤 0**（退化谓词、模板形状错误、数值字面量替换、定义
  混入 P、数值来源丢失——全部是既有门拦下真实缺陷，Z3 一致性拦截 0）。
- **H1 重复谓词门：零误伤、零触发**（本批无塌缩尝试，门的必要性未
  被演示）；**H2 部分形式化通道：零使用**（空转，价值待阶段三）；
  **H3 完成率 ≥6/10：不满足**（5/10，但缺口全在缺陷侧）。
- **忠实结果 9/10**（严格 4 + 正确拦截 5）；唯一漏网缺陷为 Hybra
  候选的交叉相乘配对歧义（`total_shares_after` 的声明语义与配对
  不可同真，公平实现也可能被该不变量误判违规），主/双复核均判
  partial，未被机械拦截——与终局批 GTE_Perps 同为"可见不拒绝"型。
- 双复核与主复核收敛模式同终局批：核心缺陷两边独立抓到，分歧仍在
  适用范围收窄的严格度，无通过/拒绝互换；`independent_gold: false`
  局限不变。
- 测后即停，不再迭代。

2026-10-08 深夜 **semantic-live-6（缺陷侧收口，final_holdout_02 发现
的三项复发/漏网缺陷的机械层修复 + 阶段三冒烟）**。背景：终测后用户
批准按发现改进；本条即按 README 披露纪律记录的"测后改动"，**改动使
9/10 数字失效，重新测量需冻结 final_holdout_03**（尚未冻结、未跑）。
四项改动（全部零模型调用验证）：
1. **数值门反馈点名缺失来源**（`lib/salvage.py`）：`numeric P source
   missing from plan` 等四条消息现在携带 `<source_id> states <字面量>`
   尾巴，重试提示同转述——终测 Kinetiq 的复发缺陷是模型拿到"缺"却
   不知道缺哪个，重试换掉而非补上。
2. **空响应免费重问一次**（`cli/semantic_pipeline.py`）：修复通道的
   字节级原样重交（终测 GTE_Perps 复发）不再消耗最后一次尝试——
   空响应未产生任何新内容，判定其为 null 并追加恰好一次携带
   no-change 处方的重问（仅一次，二次原样重交仍终止运行）。
3. **示例钉死 advisory**（`example_pinning_review` →
   `example-pinning-review.json`，feature `example_pinning_review`，
   所有冻结版本关闭）：P 等值钉死的常量若只在 impact/PoC 演算示例
   出现、或多个钉死常量同源于一条 impact 的示例（终测 Hybra：P 钉死
   10000/5000，把示例复述成了前提源），标记但不拦截。在全部可用的
   真实 run 上验证：仅 Hybra 被标红（真实缺陷），其余零误报。
4. **阶段三冒烟发现并修复查询命名断裂**（`lib/stage3_consistency.py`）：
   `stage3-spec.json` 声明的查询名是空格式（`"P AND T"`），而判决逻辑
   读下划线格式——真实反馈即使过校验也永远判 `inconclusive`（测试用
   合成 spec 恰为下划线格式故未暴露）。ingest 现在归一化两种命名，
   新增回归测试；真实候选冒烟（复制 Panoptic run + 手写反馈）走通
   全链路，判决 `violation_reproduced` 正确落盘。
测量：新增 8 项测试（379 全过，失败集 = 已知 10 例基线严格同集）；
冒烟零模型调用。**final_holdout_02 的 9/10 不再代表当前代码**，投产
测量前须冻结并终测 final_holdout_03（选样逻辑自动排除全部 147 例）。

2026-10-08 深夜（二） **new-SC 注入原型（方案①，`new_sc_injection_01`，
[REPORT 见目录 README](../evaluation/archive/new_sc_injection_01/README.md)；
2026-10-12 已按惯例 git mv 归档）：
阶段二公式 + 阶段一切片 → 新 SC → forge 机械裁决 → stage3 ingest 闭环
一例打通**。Ekubo（live4 候选）：
- 确定性注入器（`inject.py`，零模型调用）把 constraints.json 的
  P/I/V 表达式（与 Z3 查询同源、未再推导）翻译成 Solidity，连同手写
  绑定映射（`bindings/ekubo.json`，stage-3 侧绑定工作的原型输入，
  已披露）生成 guard 测试合约——继承 PoC 测试合约复用全套场景。
- guard 输出 `STAGE2_VERDICT {"p":true,"i":false,"v":true}`，按预注册
  四分支判读表裁决 **violation_reproduced**：报告主张（Transfer 事件
  source 应为 from）在代码层机械证实；guard 只在绑定不可能时失败
  （I 被违反是发现不是失败），原 PoC 测试在新 SC 中原样通过。
- 经既有 `stage3-feedback` 通路在 run 副本上 ingest，落盘
  `stage3-consistency.json`（`violation_reproduced`，符号全 bound），
  冻结 run 未被触碰。阶段一完全未动（切片只读复制，sha256 记入
  sc-spec）。注入 + 运行 + 裁决 + ingest 全程 0 次模型调用。
- 边界（如实）：绑定映射手工提供（自动绑定是后续工作）；数值单位
  缩放未处理（本例全 address/bool）；P 时序简化为动作后取值。

2026-10-08 深夜（三） **new-SC 单文件管线（`new_sc_injection_02`，
[REPORT 见目录 README](../evaluation/archive/new_sc_injection_02/README.md)）：
01 原型的"注入器 + 运行脚本"收成**一个文件一条命令**（`new_sc.py <case_key>`，
零模型调用，逐案例输入只有 stage-2 run、切片、绑定映射三样数据）**。
- 新 SC 是**一个 Solidity 文件** `new_sc.t.sol`：切片原文逐字节前缀 +
  追加的 guard 合约（切片绝不编辑，`sc-spec.json` 记录切片长度/双 sha256
  可机械复核；Ekubo 实测前缀 1,377,342 字节核对通过）。
- 01 的手工错误（选错同 finding 提交）已机械化：case_id / report_path /
  report_sha256 / declared_code_sha256 四项来源对齐门，不符即拒绝。
- forge 跑全量：原 PoC 测试 PASS = 切片完整性现场验证；guard 输出
  STAGE2_VERDICT。Ekubo 重跑与 01 逐项一致（`{"p":true,"i":false,"v":true}`
  → violation_reproduced → ingest 副本落盘同判，unbound 0 个）。
- 边界与 01 相同：绑定映射手工、数值单位缩放未处理、P 时序简化。

2026-10-12 **判读回流通道（差异重放 + 台账，`new_sc_injection_02`，
[REPORT 见目录 README](../evaluation/archive/new_sc_injection_02/README.md)）**：
阶段三判读 → 阶段二规则改进的受控接口建成，首次归因完成。
- `new_sc.py --experiment bisection/<dir>`（差异重放）：对隔离工作区换件
  重跑——冻结 run 的**副本**（携带变体）+ 变体绑定，全部输出留在工作区内，
  冻结批次与入库工件绝不触碰。归因从"读后感"变成可重放的控制变量实验。
- 回流标准四条（非正向分支 / 差异重放确认阶段二侧 / 可泛化成模式 /
  修复能落阶梯+回归测试）与六步流水成文于 02 README；登记簿
  `adjudication_ledger.json`。
- **首次归因（Merkl，precondition_mismatch）**：预注册预期（EXPERIMENT.md，
  运行前冻结）逐项命中——同一报告/切片/观测（sanity 4/4），仅把 P/I/V
  一般化（fot>0 族，不钉 990/1000/1990/2000），判读翻转为
  `{"p":true,"i":false,"v":true}` → **violation_reproduced**。肇事者 =
  阶段二表示选择（缺陷族 scenario-pinned-preconditions，报告示例算术为
  诱因）；对应第 0 层 advisory 记为 open（实现属 live 迭代步骤，须带回归
  测试与度量卫生）。零模型调用。
- 附注：归因实验发现一个接口事实——阶段三绑定契约的符号集从
  formalization.json（而非 constraints.json）推导，变体须两处一致换件，
  已记入台账。

2026-10-12（晚） **新 SC 生成/注入工作整体废弃**：01/02 两目录连同
bisection 归因实验一并 git mv 归档至 `evaluation/archive/`；lib 侧
new-SC 专属代码（`stage3_consistency.queries_from_piv`、`lib/dsl.py`
双后端遍历层）回退/删除，对应测试移除，两张新 SC 流程图删除。理由：
方向收敛——阶段二→阶段三闭环由既有 `stage3-feedback` 通路承担
（`lib/stage3_consistency.py`），新 SC 生成不再属于阶段二工作面。
上述 01/02/回流三段为历史记录，如实保留。


- 阶段二可独立从 `report.json` 的描述与影响建立证据编号，提取 P（前提）、I（报告声称应满足的性质）、V（直接违反 I 的行为/结果），生成形式计划、SMT 和交接用 `stage3-spec.json`，并运行本地 Z3 一致性查询。没有执行 PoC 或改变阶段一、三。
- 程序拒绝未知证据编号和不合法的形式计划；`auto-triage.json` 区分候选、待审、弃权和流水线故障。`review` 不等于已证实漏洞。
- 可选的前提审查 v5 同时检查 `precondition` 和 `assumption` 的证据支持及前提/动作/结果时序。受约束修复仅能改动被标记的 P 项，修复后必须重审，且不能自动认证覆盖完整。
- 可选的 v3.10 数值保真检查拒绝将显式阈值比较改写成无定义布尔量；v3.11 地址保真检查要求显式 `address(0)` 相关的接收者、所有者性质落到地址相等约束。默认提示版本和历史结果未覆盖。
- 输入预处理 v3 可在 PoC/修复章节后恢复独立影响段；本地 v4 又补上无 Markdown 标记的修复建议过滤。v2/v3 历史输入仍可精确重放，原八例结果不被 v4 覆盖。[输入覆盖报告](../evaluation/archive/input_coverage_01/REPORT.md)。
- 新入口门已有本地测试，覆盖四项均满足后继续、关键项缺失时在 P/I/V 前停止、未知证据 ID 拒绝；关系分类、专用模板、限定分类、来源绑定、协议编号过滤及二次局部修复均有本地回归覆盖。当前准确测试数以 `python main.py test` 的实时结果为准（Halmos Python / Z3 4.12.6），避免文档中的历史计数被误当作最新结论。

## 真实案例边界

| 案例 | 实际观察 | 判定边界 |
| --- | --- | --- |
| Intuition（开发回归） | v5 审查找到旧版遗漏的混入 P 的完整退出动作；修复并重审后，用 v3.10 重跑得到显式阈值 `offset18 < 1000000000` 等约束和 Z3 结果 | `review`；修复是否遗漏关键 P 尚未独立核实，不能计为准确 |
| Hybra（首次 v3.10 留出运行） | 提取、形式化、Z3 跑通；但 P 混入转账动作，地址事实被压成布尔量 | `review`；发现了新错误，不能算成功提取 |
| Hybra（之后的开发回归） | 受约束修复、重审和 v3.11 形式化后，出现 `recipient == zero_address`、`owner_after == zero_address` 等地址约束；Z3 中 `P∧V` 可满足而 `P∧V∧I` 不可满足 | `review`；该案例已用于修改规则，不再是独立留出集 |

上表中的 Z3 结果只说明**生成的公式内部**满足预期的逻辑关系，不证明报告语义被准确理解，也不证明 PoC 与报告一致。三个运行的 `poc_consistency_verdict` 均为 `not_evaluated`。

## 仍未解决

1. 没有经独立核实、覆盖多类漏洞的标准答案，因此目前不能给可信的 P/I/V 准确率或泛化率。既有审核卡和小样本只适合发现错误，不能替代代表性评测。
2. 审查模型与生成模型都可能接受报告未支持的推断；修复可能删去必要前提。程序能核对 ID、结构及部分字面约束，却不能全面判定语义蕴含。
3. 数值和零地址保真规则只覆盖已明确表达的局部模式；单位、量词、跨状态关系、复杂因果链仍需更多案例检验。严格规则也可能误拒正确表达。
4. 下游损失等次级影响仍常被留在未认领项；目前没有证明修复后性质满足或 PoC 行为是否真实发生。第三阶段对代码执行的核验不属于此阶段结果。
5. 旧八例中工程链仅 1 例完成，超时／空或截断 JSON 曾是吞吐瓶颈。当前 GTE 已端到端
   完成，但 Hybra 仍出现超时、非法 JSON 和数值 P 弱化；不能把单例跑通或模型返回快当作
   总体完成率与准确率。
6. v3 首次运行中 Morpheus 发送文本含无标题修复建议，超出本次授权的数据范围；v4 已在本地修复，但原上传不可撤回，不能把这例称为范围完全合规。
7. v3.17 把派生定义写入 `definition ⇒ I`，定义不成立时 I 可能空真；该行为不能在原版本中
   静默修改，否则会破坏既有产物的确定性重放。
8. 局部修复尚不能稳定联动修改谓词、符号来源和派生表达式；GTE Spot 与 Intuition 的
   开发回归均因此在三次尝试后被拒绝。

下一步应建立 `semantic-v3.18` 和新 schema，不回写 v3.17：将派生定义改为显式公理，
联动修复谓词与符号来源，并增加 P 时序角色及 impact—模板一致性检查。先用五例开发集
回归，再冻结规则并运行全新留出集；统计工程完成率、严格核心语义、误放行和误拒绝，不能
把 `review`、带警告继续或 Z3 通过当作语义通过。展示用总结见
[阶段二阶段性成果汇报](STAGE2_PRESENTATION_REPORT.md)。

## 2026-10-13：live-6 后首次真实端到端冒烟 + 盲审（单例，测量型记录）

背景：S13 收口（重试环合并、错误注册表合一、run 默认值注入收敛）后做投入性
冒烟。盲样从 1464 份未用报告随机抽取（种子 20261013）：
`Sequence__Transaction_Rails_Yn6A3eYizcQ__7rSTe38xKPK__JuBKoErDbar`。

**两轮 run（共 7 次模型调用）**：
- 直跑默认预算（当时 `--formal-retries` 默认 0）：3 次调用，被重复谓词门
  拒绝——三条 P 来源全部塌缩到 `direct_call_occurred`，门按设计拦截
- 评测同款预算（retries=1）：4 次调用，第 1 次同因被拦后 `_FORMAL_ERROR_RULES`
  开出 field_scoped 处方，模型重试只改 `precondition_terms`+`symbols`，引入
  按函数区分的符号解开塌缩，**转为候选**；`verify` 离线重放 8 项检查全过

**两阶段盲审**（`evaluation/smoke_e2e_01/`，复用 accuracy_gold_01 冻结协议，
prompt 原文照抄，裁判 deepseek-flash）：
- 候选 run：要素/公式的 P、I 两维 faithful；V 维 weakened——V 只编码
  "直调成功"，资金损失未入 V。核查确认这是 prompt 的**既定取舍**（V 定义
  优先未授权完成而非下游损失），危害已按设计披露在 limitations；与
  accuracy_gold_01 "weakened 大量为单主张压缩（设计取舍）"结论同形
- 被拒 run：同一裁判两次裁定相互矛盾（REJECTED 口径判 misfire/过严，
  CANDIDATE 口径判该尝试公式 unfaithful）——单例冒烟暴露同模型裁判的
  prompt 敏感性，不下定论

**修复落地（本条即披露记录）**：
1. `main.py run` 神经流程现注入 `--formal-retries 1 --element-retries 1`
   （requires 门槛与目标 parser 守卫对齐；显式传参不被覆盖）——直跑与
   batch 预算不一致是本轮冒烟暴露的直接缺陷
2. 五个冻结评测脚本（accuracy_gold_01/gold_review.py + 四批
   dual_review.py）`from lib.report_only import extract_deepseek` 在
   DeepSeek 单源化后失效，统一改为 `lib.deepseek`（测量仪器修复，
   历史产物零改动）
3. 重复谓词修复提示核验已覆盖盲裁判建议的两条出路（合并来源 / 独立
   符号），冒烟实测引导出正确修复，不改
4. V 优先级为既定设计，未经新冻结盲批不改动

**已知局限不变**：单例 n=1；裁判与管线同模型（自偏好）；无独立金标准。

## 2026-10-13：五例盲测批（生产形态直跑 + 两阶段盲审）

用户要求"多测量几个，记得是盲测"后执行。选样：`random.Random(
'stage2-blind-batch-2026-10-13-01')` 从 1462 份从未用于任何评测/调规则的
报告池抽 5 例，选样与运行互不重合历史用例（含当日两例冒烟样）。
run 形态即生产默认（`main.py run --extract`，S13 注入的重试预算生效），
产物在 /tmp（不入库）。

**工程链结果：3/5 候选、2/5 按设计拒绝（exit 2）**
- 3 例候选各 3 次调用（门+提取+形式化，零重试），
  `verify` 离线重放 8 项检查全过、`redundant_p_predicates []`
- Kinetiq：第 1 次方案谓词 `exchange_ratio_low == 2`，报告原文为
  0.2——数值保真门**正确拦截**（常量 {2} ⊄ 字面量 {0.2}）；随后两次
  field-scoped 修复模型均**原样返回同一 plan**（字节级零改动），触发
  `local repair made no change` 拒绝。裁判判 misfire，但人工核对确认
  门没有误报，裁判漏看了数值细节（同模型局限）
- Intuition：机器把"不应回滚"的安全意图形式化为
  `preview_withdraw_reverts == false`，而所选 P 恰是报告断言**必然
  回滚**成立的条件——与报告自相矛盾。裁判判 correct_catch，拒绝正确

**忠实性（两阶段盲审，裁判只见报告原文做影子复述）：**
3 例候选共 18 项维度评分：faithful 9、weakened 9、unfaithful 0；
`constants_not_in_report` 与 `collapsed_facts` 三例全空。weakened 均为
已知设计取舍且计划自身在 limitations 披露：GTE 生命周期前提移入
assumptions、下游"Dex 永久停摆"推迟；Hybra `(parts-1) wei` 量化界
推迟；SukukFi 正向授权要求让位于"坏结果不发生"（V 维既定优先级）。

**与前次单例冒烟合并的结论**：无捏造、无塌缩、无误放行；两例拒绝
均为 fail-closed（一例确属应拒，一例损失在模型修复能力而非门误报）。
局限不变：n=5；裁判与管线同模型；无独立金标准。

**S14 修复环反馈定位（同日收口）**：上表 Kinetiq 的"模型不肯改"根因
经拆解是三处同族缺陷——报错只报家族名不带定位、空修复顶掉原始错误。
三处修复见 MIGRATION.md S14；修复后 Kinetiq 真实重跑转
`candidate_checks_passed`（该轮首答即干净，零重试；修复环不再空转
由 attempts 记录证实）。效果归因如实：通过本身是模型方差，
修复效果由 396 项全绿的单测钉死。

## 2026-10-14：五例盲测批 03（忠实率第二测点）

选样：`random.Random('stage2-blind-batch-2026-10-14-03')`，池 1457 份
未用报告。批内 2×GTE_Perps、2×Monetrix、1×Intuition（不同 finding，
项目级与批 02 有重叠，案例级零重合）。

**工程链：5/5 候选通过（历批最高）**，其中 4 例经修复环转正
（调用数 5/3/4/4/4）；全部 `verify` 离线重放 8 项检查通过。
批 02 的修复环卡壳在本批未复现——S14 定位反馈与模型方差共同作用，
无法单独归因。

**忠实性显著弱于批 02**：30 项维度评分 faithful 2 / weakened 28 /
unfaithful 0；4/5 例出现 collapsed_facts。弱化的性质与批 02 不同——
批 02 以"下游后果推迟"（设计取舍）为主，本批以**占位化**为主：
- 结构性事实（4 参 vs 2 参 keccak 盐值）压成共享一个
  derived_pair_address 概念的 truth 符号（两个不同来源、谓词字面
  不同，重复谓词门按规格放行，属语义塌缩而非机械可查）
- `borrow_value > 0` 与 `borrow_value != 0` 逻辑等价，两条事实
  实际一条未表示
- 恒真下界（`>= 0`）作占位谓词

**已知张力（不擅动）**：`>= 0` 无文本字面量的模式在 live-3/4 盲批
曾被判为"方向正确"并被预注册修复**放行**（hex 掩码 + 测试
test_hex_slot_identifiers_are_not_numeric_bounds 钉死）；同一裁判
如今称同类谓词为占位。收紧该门需用户裁决：以完成率换严格度。

**累计三批（含冒烟）**：54 项维度评分 unfaithful 0（严格失真率
0%，95% CI 上界 ≈5.6%）；faithful 15 / weakened 39；完成率
盲批 8/10、含修复复跑 10/13。裁判与管线同模型、无独立金标准的
局限不变。

**S15 占位化防御（同日收口）**：把上段两类机械可查的占位化收进门
与 advisory——A：重复谓词门折叠镜像对与同符号零界族（GTE 盐值对、
Monetrix `>0`/`≠0` 从放行转拒绝）；B：`placeholder_predicate_review`
advisory 标记结构事实裸 truth 符号与无字面 zero 的恒真下界。修复与
验证细节见 MIGRATION.md S15（403 项全绿；批 03 的 /tmp run 3/5 重放
被新门拒绝，属预期行为变更；仓库 frozen run 不受影响）。
已知张力仍未擅动：`>= 0` 无文本字面量是 B 的 advisory 旗标而非
门拒绝，收紧与否仍待用户裁决。未做（候选）：C（v3.18 提示层反占位
规则）、D（更高档模型）、独立裁判。

## 2026-10-14：五例盲测批 04（S15 后忠实率测点）

选样：`random.Random('stage2-blind-batch-2026-10-14-04')`，池 1452 份
未用报告。批内 2×SukukFi、2×Hybra、1×GTE_Perps（案例级零重合）。

**工程链：4/5 候选（调用数 4/3/3/3）、1/5 拒绝**；4 例候选 `verify`
离线重放全过。S15 两件防御本批均未触发：占位 advisory 零旗标、
扩展重复谓词门零命中——批内 P 谓词全部为独立可观察量（对比批 03
的镜像对与零界族）。被拒例（SukukFi go6WTxic9yS）链路：首答缺
常量 10（数值门正确拦截）→ 修复答写出 5 项 `all_of`（schema 上限
4 项）→ 耗尽 1 次修复预算拒绝。裁判判 misfire，理由是该错误是
"机械 schema 投诉非实质失真"；人工核对：门无 bug，5 项恰为报告
的 5 条前提，**schema 的复合谓词上限把忠实编码挡在门外**——记为
S16 候选（上限 4 项 vs 报告事实条数，二者无因果关系；嵌套复合可
表达但模型未用）。

**忠实性（24 项维度评分，两阶段盲审）**：faithful 4 / weakened 20 /
unfaithful 0；`constants_not_in_report` 0；`collapsed_facts` 1/5
（SukukFi fcwk：三条 cannot- 影响 → 一个布尔）。
weakened 主因与批 03 不同，回到批 02 型设计取舍：具体代币身份
（USDC/DAI）降为通用不等式（schema 无字符串常量）、下游影响推迟
（GTE 滞留代币、SukukFi 未注册/注册受阻）、liveness 性质部分编码。
与批 03 对比：完全忠实维度 4/24 vs 2/30，塌缩 1/5 vs 4/5——
占位化家族消失，弱化集中于表达力上限而非偷懒。

**累计四批（含冒烟）**：78 项维度评分 unfaithful 0（严格失真率
0%，95% CI 上界 ≈3.8%）；faithful 19 / weakened 59；完成率盲批
12/20。局限不变：裁判与管线同模型、无独立金标准；n 仍小。

**S16+C（同日）**：盲批 04 misfire 的收口——复合谓词上限 4→8
（报告事实数、而非 schema，决定项数）+ `invalid compound predicate`
修复教学 + 提示层反占位规则（live-6，恒真界与结构事实裸 truth
符号入审计清单第 8 条）。408 项全绿；被拒例重跑转候选、verify 全过
（归因如实：该轮恰用 4 项复合，模型方差；上限效果由单测钉死）。
细节见 MIGRATION.md S16。

## 2026-10-14：五例盲测批 05（S16+C 后测点）

选样：`random.Random('stage2-blind-batch-2026-10-14-05')`，池 1447 份
未用报告。批内 2×Panoptic、2×GTE_Perps、1×GTE_Spot（案例级零重合）。

**工程链：4/5 候选（调用数 3/3/4/3）、1/5 拒绝**；4 例候选 `verify`
离线重放全过。被拒例（Panoptic NYHGmaXp7CP）为**真实 catch**：模型
写出自引用占位定义 `intended_twap = 1 * intended_twap`（"乘 1 凑
单位"家族，live-2 提示明令禁止）并以任意不等式替代实际事实——
裁判判 correct_catch，fail-closed 有效。

**S15/S16 防御触发情况**：占位 advisory 零旗标、扩展重复谓词门
零命中（批内 P 谓词均独立）。唯一 collapsed_facts（GTE cjpGNf9X68J）
经人工核对是**符号级死重复**：`ninety_pct_sold_flag` 与已引用的
`ninety_pct_sold` 含义、来源全同但从未被引用——公式层事实未丢
（该事实被表示了一次），属符号表瑕疵而非谓词门职责；记为后续
候选检查（同源同义符号去重；S18 `symbol_table_review` 已收口）。

**忠实性（24 项维度评分）**：faithful 8 / weakened 16 /
unfaithful 0；`constants_not_in_report` 0。完全忠实份额 33%——
历批第二高（批 02 为 50%，批 03 为 7%，批 04 为 17%）。weakened
集中于既有设计取舍（下游影响推迟、具体身份降为通用不等式）。
归因如实：批 05 案例构成无 Monetrix，且 n=5、裁判与管线同模型，
提升不能单独归因于 S16+C；二者针对的占位/复合家族在本批本就
未出现——修复的防复发效果由单测钉死。

**累计五批（含冒烟）**：102 项维度评分 unfaithful 0（严格失真率
0%，95% CI 上界 ≈2.9%）；faithful 33 / weakened 69；完成率盲批
16/25。局限不变。

## 2026-10-14：五例盲测批 06（S16+C 后第二测点）

选样：`random.Random('stage2-blind-batch-2026-10-14-06')`，池 1442 份
未用报告。批内 SukukFi、Sequence、2×GTE_Perps、Hybra。

**工程链：4/5 候选（调用数 3/3/4/3）、1/5 拒绝**；4 例候选 `verify`
离线重放全过。S15/S16 防御零触发（P 谓词均独立、无占位旗标）。

**首次出现 unfaithful 判定（2/24 维度），人工核对属实**：GTE
feLafF5S5sM 把"A launchpad fee is accrued but not distributed
because timeElapsed == 0"编码为 `undistributed_fee == 0`——报告事实
是费用存在（>0），机器把属于 time_elapsed 的零常量错安到费用量上，
**事实反转**。漏检根因：数值保真门只验证常量字面量出现在引文
（引文确有 == 0）；零界族检查不适用（eq 非 ge/le）。语义级反转在
现有确定性门的职责之外——S17 候选（需用户裁决：词法启发式对
"x == 0 且零属他量"易误报，语义判定需模型介入；S17 语义交叉
审计已收口，反转方案归因补测见 S18 探针）。

**被拒例判 misfire，人工核实**：报告原文即 "pending × 1e12 <
totalShares" 跨单位比较，单位门按 DSL 纪律拒收——单位规范与
报告自身混合单位公式的真实张力（忠实编码需把两侧声明为同量纲
的原始值，缩放常量内联为字面量），S18 `mixed_unit_scaling_review`
advisory 与 `_type_unit_hint` 教学已收口。

**忠实性（24 项维度评分）**：faithful 4 / weakened 18 /
unfaithful 2；`constants_not_in_report` 0；`collapsed_facts` 0。

**累计六批（含冒烟）**：126 项维度评分 unfaithful 2（1.6%，严格
失真率首次非零，95% CI ≈0.2%–5.6%）；faithful 37 / weakened 87；
完成率盲批 20/30。批 05 的 33% 忠实份额未在本批复现（4/24）——
单批 n=5 波动大，两批合并 12/48（25%）更接近 S16+C 后的当前水平
估计。局限不变。

## 2026-10-14：盲测批 07（D 杠杆 A/B：管线切 deepseek-v4-pro）

选样：`random.Random('stage2-blind-batch-2026-10-14-07')`，池 1437 份
未用报告（SukukFi、Panoptic、Merkl、Olas、Intuition 各一）。A/B 设计：
唯一变量为管线模型（`--model deepseek-v4-pro`），裁判保持
deepseek-flash，与批 05/06 直接对比。`thinking` 仍为 disabled
（lib/deepseek.py 对两档统一设置——pro 为推理档位，此组合的适用性
存疑，见下）。

**工程链：2/5 候选（历批最低；flash 批 04-06 均为 4/5）**。三例
被拒中两例经哈希证实为**字节级原样重交**（三次提交同一 SHA256）：
Panoptic（首答派生定义单位自相矛盾：`user_profit_share` 声明
unit profit 却定义为 shares×profit——真实缺陷，门拦截正确，正确
修法是删除该定义，关系式本身交叉相乘无误）与 Olas（P 符号未
接地，同样真实缺陷）；Intuition 首答 truth 绑定错、修复答写出
自比较谓词。修复环"无改动即拒绝"按设计触发，但两例缺陷修复
方向都明确——**模型不肯改而非不可改**，损失归因于修复环无法
升级策略（记为 S17 候选：no-change 时清空反馈全新再生成一次）。

**忠实性（12 项维度评分）**：faithful 2 / weakened 10 /
unfaithful 0。与 flash 批 05+06 合并（12/48，25%）对比无优势
（2/12，17%）；首答干净率 2/5。裁判对被拒例判 2×correct_catch
（与人工核对一致：缺陷真实）+ 1×misfire（自比较被判"局部装饰性
缺陷，核心形式化无误"——即 Layer B 论点：局部可修缺陷拖死整份
忠实计划）。

**结论（D 杠杆暂不采纳）**：thinking-disabled 的 v4-pro 在本批
完成率与忠实份额均低于 flash，未发现收益；不切换默认模型。
如实披露局限：n=5 单批、裁判同模型、未测 pro+thinking 组合。
**"让产物忠于报告"的剩余主杠杆**是语义交叉审查调用（验收前
逐 P 来源比对原文与谓词的方向/常量/符号，裁决路由复用 S14 修复
环）——批 06 的事实反转与批 07 的局部缺陷都属其可拦范围。

## 2026-10-14：S17 落地 —— 语义忠实交叉审计 + 空修复升级

批 06 事实反转的根因（全链无语义检查）以 S17 闭合：验收前独立
交叉审计调用逐 P 来源判断谓词是否忠实编码其声明（方向/常量/
符号/真值对应），非一致裁决经 `ValueError` 路由进既有修复环。
特征键 `semantic_faithfulness_audit` live-only、所有冻结版本
frozenset()（回放各自行为）；verify 零模型调用确定性重放裁决
（形状/覆盖校验 + 零 mismatch + stage3-spec 哈希链）。审计通道
独立参数化 `--audit-provider/--audit-model`（构建期 GLM 审
DeepSeek，生产双 DeepSeek，限制披露）；调用计入
external_model_invocations。

同批落地空修复升级（批 07 教训）：null_reprompts 授予改为
`fresh_restate` 完整重述（跳过 promote，不再把重发件冻结为修复
基底，反馈命名原始缺陷），仍一次性。

验证：420 项测试全过（+12）。真实 GTE feLafF5S5S5sM 重跑：
本轮模型自身产出忠实方案（费用存在以 bool 真值符号编码，
批 06 的 `undistributed_fee == 0` 反转未复现），审计判
consistent，全链 verify 过、审计调用 1 次。批 06 原反转方案的
直接审计归因（应判 inverted）在 opencode 通道两次 240s 超时后
待通道恢复补测；亦待配置 `DEEPSEEK_API_KEY` 后走
`--provider deepseek` 直连复核（生产通路）。

## 2026-10-14：S18 —— 混合单位缩放 + 符号表 advisory + S17 归因补测通路

批 06 跨单位 misfire（GTE QS7NsxmTjRa 混合单位公式被判误）
与批 05 死符号（`ninety_pct_sold_flag`）两条遗留以两件
advisory 评审闭合（n=1 证据不足以立门，全量记录积累证据）：
`mul(symbol, const)` 缩放比较实例记录（常量是否见于原文）、
未引用符号与同源近名重复声明。`_type_unit_hint` 补齐内联常量
处方与按来源字面量警告（两条门语义已离线实测钉死）。另有
S17 归因补测探针（`evaluation/s17_audit_retest_01/audit_retest.py`，
dry-run 已过、载荷含反转谓词与双 sha256，真实调用待用户授权）。
特征键两枚 live-only，verify 零模型重放，artifact 哈希链入
stage3-spec。430 项测试全过（+10）。

## 2026-10-15：盲测批 08（S17+S18 后测点：flash 回归主线）

选样：`random.Random('stage2-blind-batch-2026-10-15-08')`，池 1432 份
未用报告（Intuition 2、Kinetiq、GTE_Perps、Olas 各一，案例级零重合）。
A/B 唯一变量 = 相对批 06 的代码态（S17 交叉审计 + fresh_restate + S18
两件 advisory + 单位修复教学）；管线与裁判均 deepseek-flash，与批
04–06 直接可比。

**工程链：5/5 候选（并列历批最高，批 05 同为 5/5）**，每案恰好 4 次
调用（screening+要素+形式化+审计），零重试零修复环触发——批 07 的
"不肯改"家族本批未复现（样本未触及 fresh_restate 路径，不能归因为
其修复，如实记录）。`verify` 五案离线重放全过。S17 审计 17 项 P 来源
全判 consistent、零 mismatch（无误杀）；S18 两 advisory 零旗标
（n=1 家族未复发，无回归）。

**传输层事件（如实披露）**：首跑 Intuition tG7w 在 DeepSeek outage
窗口死于 screening 响应 JSON 截断（readiness 步骤无重试预算，409
completion tokens 处截断即致命）。同窗口另有 503 与 valid-JSON-坏
信封两形态，已以 `TransientModelError` 可重试类收口（commit fc8a34a，
432 测试 +2）。截断属内容级故障不在该改动覆盖内，重跑即过（5 案
全部干净完成，未再触发）。

**忠实性（30 项维度评分）**：faithful 0 / weakened 30 / unfaithful 0。
weakened 主桶高度一致：**核心断言范围收窄**——报告陈述多重危害/性质
（如 GTE _rewards_unclaimable、Kinetiq 永久盗取+协议损失、Intuition
validUntil 侧、Olas MEV 提取），core 范式只形式化单一直接 impact，
其余显式 defer；required_property 多为 bool 代理（= false）而非报告
的构造性属性（密码学绑定、公平性、有意义最小输出）。preconditions
两例弱化均为省略侧条件。该桶为 core-claim 设计的本征损耗候选，
升级需动 DSL/多断言结构（大改），未立项，待 weakened 分桶凑满
n≥2 独立家族再裁决。

**累计七批（含冒烟）**：156 项维度评分 unfaithful 2（1.3%）、
faithful 37 / weakened 117；完成率盲批 25/35。批 08 完全忠实份额
0%（批 05 为 33%）——S16+C 后各批在 faithful/weakened 边界上波动
大，边界由判卷措辞敏感度主导，核心信号是 unfaithful 稳定为极低。
调用预算：管线 20 + 判卷 10 = 30 次。
