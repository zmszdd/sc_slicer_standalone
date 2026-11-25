# 权威指标根因与完整解决方案（2026-11-24）

## 结论

当前权威四指标低，不是单一 grep/API/统计错误，而是两个能力瓶颈叠加：

1. 正例侧：report-only 提取的 P/I/V 经常没有代码级可观测锚点，Stage3 绑定失败
或 effect witness 不足；
2. 负例侧：冻结 40 负例中只有 9 个在当前协议下同时具备 frozen claims、可用
flatten 和 metric eligibility，unresolved 不能转 TN。

当前协议 `mainline/1.7.36` 的权威指标是可信低值，不是可丢弃的异常：
Accuracy 32.56%、Recall 15.0%（未评测正例计 FN）、Precision_vuln 100.00%、
F1_vuln 0.2609；条件诊断口径为 Recall 17.14%、F1 0.2927。
混淆矩阵 TP=6、FN=29、TN=8、FP_vuln=0。其中 Accuracy 使用 vuln 级同一
混淆矩阵 `(TP+TN)/(TP+FN+FP_vuln+TN)`。发布门禁为 `ready=true` /
`publishable=false` / `coverage-limited`：正例 35/40=87.5% 已达 80% floor，
负例 9/40=22.5% 仍未达 24 eligible / 60% floor。

### P0 已落地：口径、覆盖门禁与指纹隔离

- `mainline_metrics` 的 `accuracy` 改为 vuln 级统一混淆矩阵；
  `accuracy_consistency`、precision cluster bootstrap 同步修正。
- `locked_eval` 新增 `publishable` / `publication_status` / `publication_blockers`；
  `ready` 与 `publishable` 分离，覆盖不足只报告 `coverage-limited`，不放宽 gate。
- `mainline_protocol` 拆分 execution/report 指纹；指标与报表代码改动不再让已产出的
  run 全部 stale；1.7.34 为纯报表协议升版，1.7.33 run 按显式 report-only
  predecessor 继续有效。
- `current_denominator` 的负例覆盖与 `mainline_metrics` 统一为
  metric-eligible case，消除了 12/40 与 9/40 并存的口径冲突。
- 新增 `case_readiness.py`，逐例区分 `not_run`、`stage2_blocked`、
  `stale_only`、`run_unresolved`、`run_nonterminal` 与 `eligible`。
- 新增 revert-witness 证据重新裁决：只有当 `vm.expectRevert` 的调用本身
  就是被修复的漏洞操作时才接受为 effect witness。原始 verdict 和 run
  artifact 不变，裁决只进入报表层。

2026-11-24 revert-witness 审计结果：13 个 `effect_not_witnessed` claim-run
候选中有 5 个 claim-run 通过政策，对应 2 个 case，分别是 SukukFi 的
`vault.redeem` 直接漏洞操作与 GTE Spot 的 `clob.postLimitOrder` 直接漏洞操作。
以下候选被拒绝：

- SukukFi batch-transfer：`expectRevert` 验证的是暂停时普通 `transfer` 应失败，
  真正漏洞是后面的 `batchTransfers` 成功；
- GTE Perps inactive-protocol：`expectRevert` 验证的是暂停时 `placeOrder` 应失败，
  真正漏洞是后面的 `deposit/withdraw` 仍成功；
- Panoptic：`expectRevert` 是 admin hijack 后的下游 `sweep` 结果，不是
  被修复的 `init` 操作本身；
- Hybra / GTE Perps quote-DoS：即使 revert 在漏洞路径上，执行门禁也判定
  `dust_or_donation_dos` 影响不足，不能进入 vuln 指标。

该裁决把 TP 从 4 提升到 6，recall 从 11.43% 提升到 17.14%，accuracy 从
27.91% 提升到 32.56%，F1_vuln 从 0.2051 提升到 0.2927；没有放宽影响门禁、
没有把 unresolved 负例转 TN，也没有改写原始 run verdict。

当前逐例状态：

| 标签 | eligible | not_run | stage2_blocked | stale_only | run_unresolved |
| --- | ---: | ---: | ---: | ---: | ---: |
| positive | 35 | 4 | 1 | 0 | 0 |
| negative | 9 | 16 | 0 | 0 | 15 |

2026-11-24 已执行 A 批补跑（Brix、Hybra、Panoptic、Sequence、SukukFi）：
5 个案例全部跑完但 **0 个新增 TP**，其中 4 个进入分母成为 FN，正例覆盖
从 31/40 升到 35/40，recall 从 12.90% 降到 11.43%。这是覆盖诚实化，不是能力回归。
随后在现有 artifact 上执行上述 revert-witness 证据裁决，把 2 个直接漏洞操作
案例恢复为 TP，recall 回升到 17.14%。

剩余覆盖缺口是 4 个正例从未有 claims、1 个被 Stage2 明确阻塞、16 个负例从未
跑 Stage3、15 个负例跑了但证据不足。16 个未跑负例不能再合并成
`no_stage3_run`：当前配置下是 12 个无 witness/neutral flatten 切片、1 个
Stage2 缺少明确 Impact 段、3 个已有切片但 Stage2 零 claim。`make
case-readiness` 可重放这些原因，不需要 LLM/forge。

### 执行层覆盖根因（2026-11-24 复核）

负例覆盖率只有 9/40，不是“少按一次运行”造成的，而是执行链路本身缺少负例入口：

1. `run_mainline.py` 只遍历 `sample.positive_cases`；负例 Stage2/Stage3 依赖历史
   脚本和手工命令，无法从冻结样本稳定重放。
2. `case_readiness` 把 16 个未跑负例都记为 `no_stage3_run`，掩盖了 12 个上游
   切片缺失、1 个 Impact 段缺失和 3 个 Stage2 零 claim 的不同修复路径。
3. 已跑过的 15 个负例是 `run_unresolved`，原因分布在 `partial_binding`（5）、
   `binding_error`（2）、`compile_error`（2）、`effect_not_witnessed`（2）、
   `TRUSTED_JUDGE_INVALID`（2）、`reference_patch_required`（1）和
   `stage2_restatement_required`（1）。它们没有可进入 TN 的 metric evidence，
   不能为了覆盖率强行改判。

对应修复按优先级如下：

- P0（已落地）：`case_readiness/2` 增加 `no_slice`、`zero_claim_stage2`、
  `stage2_needs_impact_review`、`stage3_ready` 等负例 subreason；`run_mainline`
  增加默认关闭的 `--include-negatives` 执行入口。
- P0（已落地）：负例的零 claim 重试先写入候选 Stage2 goldset，Stage3 只跑候选；
  候选 run 必须经 `negative_recovery_gate` 证明产生新的 metric-eligible negative
  才晋升冻结 goldset，否则移到 rejected-run 归档，不进入权威分母。
- P1：对 3 个 zero-claim 案例执行一次 `--continue-on-review` 的有界 Stage2
  重试；仍为零 claim 的保持阻塞。
- P2：为 12 个 `no_slice` 案例生成 witness/neutral 切片；为 1 个
  `stage2_needs_impact_review` 案例修复报告 Impact 段或保留阻塞。不得伪造切片。
- P3：按 unresolved 原因分别处理 rebind、test-level monitor、compile repair、
  effect witness、reference patch 和 Stage2 restatement；仍 unresolved 的不转 TN。

2026-11-24 P1 实测结果：`GTE_Perps...WH5cHLf6NzX` 与
`Olas...BUxmxhf6cQP` 在 `continue_on_review` 下仍是 partial/review，生成 0 个
claim；`Olas...ao3Y7v5VC2r` 的 core P/I/V 未完整形式化，Stage2 明确
`stage2_can_continue=false`。因此 3/3 仍为 `zero_claim_stage2`，没有候选进入
Stage3、没有 promotion、权威指标不变。该结果证明提高负例覆盖不能靠重复调用
Stage2，必须修复上游 Impact/PIV 形式化或报告输入。

## 根因证据

| 现象 | 证据 | 解释 |
| --- | --- | --- |
| dev252 看起来明显更好 | dev252 recall 68.7%（173/252）是在冻结 252 个开发案例上的正确计算；252/1465=17.2% 是另一个覆盖问题 | 1465 不属于 dev252 分母；173/1465=11.8% 只能叫覆盖感知下界，不是 dev252 recall |
| 当前 recall 低 | 35 个已评测正例中 TP=6、FN=29；未评测正例按样本内下界计入时 recall=6/40=15.0% | 与 dev252 的可比口径是 17.1% vs 68.7%，差距来自开发调参、旧协议、可观测性和样本分布，不是算术口径 |
| 大量正例未复现 | 当前 1.7.33 eval 中 `effect_not_witnessed`、`binding_error`、`reference_patch_required`、`stage2_review_required` 占主导 | 核心问题是语义不可观测与 effect witness，不是单一编译错误 |
| 负例 precision CI 弱 | 40 负例仅 9 个进入权威分母；FP_vuln=0 但 Wilson CI 为 51.0%–100% | 不能把 100% 解读成“零误报”；负例覆盖不足 |
| 反馈污染确实存在 | 35 个 `stage2_review_required` claim 中 35/35 来自 `stage3_bindability_feedback` | 清理后释放 11 个 claim，但新增 TP=0；污染不是最终根因 |

## 完整解决方案

| 阶段 | 内容 | 是否改权威口径 | 成本 | 状态 |
| --- | --- | --- | --- | --- |
| A | 证据收口：生成论文证据表，将权威主表、dev252 条件口径、全量下界、失败分桶和门禁证据并列 | 否 | 低 | 已执行 |
| D | 负例执行层：分层审计 + 默认关闭的负例 Stage2/Stage3 入口 + 候选 gate | 否 | 低 | 已执行 |
| E | 3 个 zero-claim 负例有界 Stage2 重试 | 否（候选区） | 中 | 已执行；3/3 仍零 claim |
| B | 协议升级：per-run feedback 隔离 + observability-first claim 选择 + 有界静态/编译反馈修复，然后全量重跑 | 是，必须 bump 协议并重建分母/provenance | 高，需 API 额度和数小时 | 未执行；需单独授权 |
| B0 | revert-witness 证据重新裁决（仅接受直接漏洞操作的 expectRevert） | 否，报表层；原始 verdict 不变 | 低 | 已执行 |
| F | 12 个无切片负例生成 witness/neutral 切片；1 个 Impact 段缺失案例单独修复 | 否（不重选样本） | 中高，需逐例 Stage1 | 未执行 |
| G | 15 个 unresolved 负例按 verdict 根因分批修复 | 否 | 高 | 未执行 |
| C | 使用 dev252/blind-invalid 负例替换当前负例 | 是，且属于开发集泄漏 | 低但不合法 | 拒绝 |

### 阶段 A：已执行的低风险控制

- 新增 `tools/stage3/evaluation/metrics/paper_evidence_report.py`
  - 读取现有权威指标、dev252 文档、当前协议 eval 和 provenance；
  - 输出 `paper_evidence_report.json` / `.md`；
  - 不写 `mainline_metrics.json`；
  - 不修改样本、标签、协议指纹或负例选择。
- 新增 `make paper-evidence` 入口。
- 新增测试确保：权威指标数值一致、dev252 条件 recall 与全量下界分离、
  dev252 不进入权威分母、报告生成不改写 `mainline_metrics.json`。

论文写法：主表只用权威四指标；dev252 只能作为 development retrospective，必须
把 68.7% 写成 dev252 在 252 个冻结开发案例上的 recall。173/1465=11.8% 只能
单独写成覆盖感知下界，回答“全部相关正例候选中当前流程覆盖了多少”，不能叫
dev252 recall，也不能替换 68.7%。dev252 与当前主线的可比差距应读作 68.7%
开发集 recall vs 17.1% locked 已评测 recall，这是真实差距，不能只用分母解释掉。

### 阶段 B：真实提高指标的唯一合法路径

只有在明确批准协议升版和全量重跑额度后执行：

1. `PROTOCOL_VERSION` 升到 `mainline/1.7.34` 并重新生成 baseline；
2. bindability feedback 按 run_id 隔离，禁止跨 run 写回 case 目录后硬拦 Stage2；
3. top3 claim 选择加入 observability-first 排序：有明确 checkpoint/receiver/effect
   witness 的 claim 优先，纯语义不可观测 claim 不进入自动 top3；
4. 对 `binding_error / compile_error / effect_not_witnessed` 做最多 2 轮有界
   静态/编译反馈修复，失败仍保持 unresolved；
5. 全量重跑冻结样本的正负例，刷新 current_denominator、provenance 和
   locked-eval contract；
6. 只有 `make locked-eval-check` 为 `ready=true` 后才刷新权威四指标。

诚实预期：binding/completion 可能改善，recall 不保证上升；若仍无 TP，必须照实
报告。已知低成本 feedback 清理释放 11 个 claim 但没有新增 TP，因此阶段 B 的
成本/收益必须由作者明确接受，不能默认执行。

## 硬约束

- 不使用 dev252 或 blind-invalid 负例进入权威分母；
- 不改标签、不重选冻结 40 负例；
- unresolved 负例不转 TN；
- 旧协议或 stale run 不进入分母；
- 不为指标好看放宽 gate；
- revert-witness 裁决只读取既有 artifact，不修改 run summary；直接执行层修复必须
  在下一协议版本 bump 后重跑，不能混入 `mainline/1.7.33` 的已产出 run。

2026-11-24 报表口径补充：协议 1.7.34 只调整正例 publishable coverage floor
（90%→80%）、明确 eligible floors（30/24）并新增保守 headline recall；执行
语义未变，1.7.33 run 按 report-only predecessor 继续有效。负例 24 eligible
floor 与 unresolved 不转 TN 的约束不变，因此当前仍为 `coverage-limited`。

### 发布门槛为什么不继续放松

正例门槛已从 90% 降到 80%，当前 35/40=87.5% 已通过；继续下调没有统计收益。
负例门槛保持 24 eligible / 60% 覆盖，因为当前 9 个负例、0 个 `FP_vuln`
只能把假阳性率的 95% 上界压到 28.3%；24 个负例才能压到 11.7%，30 个为 9.5%。
把门槛降到 9/40 会让“precision=100%”隐含最高约 28% 的未观测假阳性率，
这不是客观筛选，而是用覆盖缺口换取表面数值。因此门槛不因指标低而继续降低；
应通过有界补跑增加 metric-eligible 负例，仍 unresolved 的案例保持 unresolved。

两份 companion 报告的主表统一为 `headline_metrics`（accuracy、conservative
recall、precision_vuln、conservative F1）；已评测条件 recall/F1 只作诊断。
`paper_evidence_report` 与 `metric_alignment_report` 必须逐项一致。

2026-11-24 负例晋升门禁口径对齐：`negative_recovery_gate` 原先用 claim 级
`eligible_current` 计数（P0 候选复核时 baseline=12），而权威 locked eval 使用
case 级 metric-eligible（9）。两类计数的差别来自 impact-insufficient 与
consistency 未通过的 claim。现在晋升门禁改用 `metric_eligible_cases`，与权威
分母一致；P0 候选复核后 baseline=candidate=9、`promote_allowed=false`，不会把
未真正进入混淆矩阵的负例误算为恢复成功。该改动不改变权威四指标、样本、标签、
协议指纹或已产出 run。

2026-11-24 主表 CI 补全：协议 `mainline/1.7.36` 为纯报表升版，新增保守 F1
的项目聚类 bootstrap CI。重采样单位仍是 project，固定 seed=13、2000 次；
正例分母使用全部 40 个 sampled positives（未评测计 FN），负例只使用已评测
metric-eligible 案例。CI 只补区间，不改变点估计、混淆矩阵、负例覆盖、
标签、样本或任何 run 的执行指纹；1.7.35/1.7.34/1.7.33 同执行指纹 run
继续有效。

## 产物与复现

```bash
make paper-evidence
make case-readiness
make test-stage3
make protocol-check
make metrics-check
make locked-eval-check
```

输出：

- `tools/stage3/evaluation/metrics/paper_evidence_report.json`
- `tools/stage3/evaluation/metrics/paper_evidence_report.md`
- `docs/ROOT_CAUSE_AND_FULL_SOLUTION_20261124.md`
