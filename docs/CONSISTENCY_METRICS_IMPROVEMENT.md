# 一致性四指标改进方案（主线）

本文只服务于主线问题：**自然语言报告声称的效果 V，是否在源码执行路径上被独立 witness 见证**。
漏洞级四指标仍是伴生诊断。本文不改变冻结样本、标签、协议版本或发布门槛，也不把
dev252 / dev24 放进权威分母。

## 1. 当前事实

权威主表来自 `mainline_metrics.json::canonical_metrics`：

| 指标 | 当前值 | 当前分母 |
| --- | ---: | --- |
| Accuracy_consistency（保守） | 0.2000 | 10/50 |
| Recall_consistency（保守） | 0.2500 | 10/40 |
| Precision_consistency（已评测） | 0.5000 | 10/20 |
| F1_consistency（保守） | 0.3333 | TP 10 / FP 10 / 未评测正例 5 |

混淆矩阵为 `TP_consistency=10 / FN_consistency=25 / 未评测=5 / TN=0 /
FP_consistency=10`；漏洞级伴生为 `TP=7 / FN=28`。发布状态仍为
`coverage-limited`：负例仅 10/40，consistency FPR 上界 100%，2 例 label review。

## 2. 根因分解

### 2.1 负例标签与一致性问题不同构（主要根因）

当前 40 个负例来自 Code4rena 官方 `invalid`，这是**判例有效性/影响**标签，不是
“报告声称的效果在源码中不存在”标签。10 个已评测负例全部有独立 V witness，
所以按一致性定义只能是 FP；没有一个负例同时满足 `negative_witness.eligible=true`
且无 V，因此 TN=0。

这不是报表 bug。逐 run 核查显示这些 FP 均有
`code_query_results.P_and_T_and_V=sat`、`forge.effect.status=Success` 与
`witness.effect_witnessed=true`。把它们改成 TN 需要把“V 已见证”改判为“V 未见证”，
等于重标案例，明确禁止。

即使把剩余 30 个负例全部执行成 TN，10/40 的 FP 比例对应单侧 95% FPR 上界
38.7%，仍高于 20% 发布上限；若发布下限 24 例里出现 10 个 FP，上界为 60.3%。
因此**现有负例池在本协议下不可能达到可发表一致性门槛**。要发表，必须另建
“consistency-negative”队列：仍来自 invalid finding，但只有当报告声称的 V 在源码
路径上缺席、且 negative witness eligible 时才作为一致性 TN。该队列需要新协议版本、
明确授权和独立冻结，不能通过当前样本改名实现。

### 2.2 正例执行失败吃掉了 TP

35/40 正例进入矩阵，其中只有 10 个 case 有独立 V witness。已评测正例 claim 的
终态分布中，`stage2_review_required` 28、`effect_not_witnessed` 14、
`binding_error` 8、`partial_binding` 4、`reference_patch_required` 5，
另有 5 个正例完全没有 Stage-3 run。主要失败模式是跨合约符号不可见、stage2
review 未释放 claim、弱 invariant 与参考补丁缺失，不是一致性判定口径错误。

### 2.3 Provider 额度耗尽阻断了模型相关恢复

最新 `make provider-check` 显示 OpenCode 端点可达，但返回
`HTTP 429 / GoUsageLimitError：OpenCode Go usage limit reached（weekly）`，
约 4 天 22 小时后重置；此前还观察到 Cloudflare `403 / error code 1010`。
Stage-2 与 binding repair 都依赖该 provider，因此 8 个
`awaiting_stage2`、3 个 `zero_claim_stage2`、1 个 impact-review 负例以及
binding_error 类正例暂时无法继续执行。无模型重试也不可行：`--skip-llm`
只在 bindings 完整时复用，缺 binding 的 claim 仍会回退到 `stage3_binding_llm`。

## 3. 上界估算（不用于改指标，只用于判断可行性）

| 场景 | Accuracy | Recall | Precision | F1 | FPR 上界 |
| --- | ---: | ---: | ---: | ---: | ---: |
| 当前 | 0.2000 | 0.2500 | 0.5000 | 0.3333 | 100.0% |
| 30 个剩余负例全为 TN，TP 不变 | 0.5000 | 0.2500 | 0.5000 | 0.3333 | 38.7% |
| 5 个未评测正例全部成为 TP，负例不变 | 0.3000 | 0.3750 | 0.6000 | 0.4615 | 100.0% |
| TP=35，30 个剩余负例全为 TN | 0.8125 | 0.8750 | 0.7778 | 0.8235 | 38.7% |
| 理论上限 TP=40、FP=10、TN=30 | 0.8750 | 1.0000 | 0.8000 | 0.8889 | 38.7% |

结论：负例扩样主要改善 accuracy 与 FPR；precision/recall/F1 的主要杠杆是
让更多正例产生独立 V witness。两者都不能靠放宽 gate 或改标签完成。

## 4. 完整执行方案

### P0：保持权威主表诚实（已完成）

- 不改冻结样本、标签、协议版本、发布门槛。
- 保留最新 run，不回退被更新或超时的结果。
- `make metrics` 只读冻结样本与既有 run；重采样仍只能走显式
  `make metrics-resample`。

### P1：恢复 provider，然后扩大负例覆盖（当前阻塞）

按冻结负例列表执行，不重选、不重标：

1. 等待 OpenCode 周额度重置、开通 Extra Usage，或提供另一个与协议记录的
   provider、model、prompt version 一致的可用端点。执行前先跑
   `make provider-check`，返回 `ok=true` 才继续。
2. 运行 `run_mainline --include-negatives --only-negatives`，让 8 个
   `awaiting_stage2`、3 个 `zero_claim_stage2`、1 个 impact-review 负例重新进入
   Stage-2；零 claim 恢复只走既有 `--continue-on-review` 候选链。
3. 对 14 个 `run_unresolved` 负例做有界 rebind / compile repair；仍失败的
   保留 unresolved，不转成 TN 或 FP。
4. 只有 `negative_recovery_gate` 证明新增 eligible 负例且不丢失既有正/负例时才
   晋级；未晋级 run 留在隔离目录。
5. `make metrics` 刷新权威指标，保留 `coverage-limited` 直到负例下限与 FPR
   上界同时达标。

### P2：恢复正例 TP（当前阻塞，需 provider）

1. 对 5 个 `not_run` 正例补齐 Stage-2；对 1 个 `core_piv_not_fully_formalized`
   做一次明确的 Stage-2 修复。
2. 对 6 个 rebind 队列正例重跑 Stage-3；跨合约符号不可见的 case 只能靠
   reference patch 或工具能力修复，不能把 partial binding 当作 V witness。
3. 对 3 个 `reference_patch_required` case 提供与报告声称效果对应的补丁，再按
   同一协议重跑。
4. 所有结果保留最新 run；未产生独立 V witness 的仍计 FN。

### P3：工程能力修复（需要协议版本升级与全量重跑）

这些改动会改变 Stage-2/3 执行语义，不能混在当前 `mainline/1.7.36` run 中：

- 跨合约状态读取的 binding projection：把外部合约状态改写为可注入观测点，
  而不是因 `cross-contract reference` 直接停在 `reference_patch_required`。
- Stage-2 review 释放规则：区分“不可观测”与“可观测但 impact 不足”，只释放
  前者进入 Stage-3，后者仍保留诊断。
- 有界超时分层：把 1800 秒整体超时拆成 binding / compile / forge 子预算，
  避免 Ekubo、Panoptic 这类 case 吞掉整个预算且没有归因。

执行顺序：先完成 P3 代码改动与单测 → bump `PROTOCOL_VERSION` → 重新生成
`mainline-protocol.json` baseline → 对所有 frozen case 重跑 → 新协议下重算四指标。
旧协议指标只能作为历史对照，不能与新协议混表。

### P3a：非协议稳定性修复（已执行）

以下改动只影响运维/传输，不改变 prompt、model、binding 语义、verdict 映射或
样本，因此不需要协议 bump：

- `make provider-check`：15 秒内返回 provider 健康状态，并区分
  `usage_limit`、`rate_limited`、`access_blocked`、`quota_or_billing` 与网络错误。
- LLM 传输层：401/402/403 与含 `GoUsageLimitError` / `usage limit reached` 的
  429 不再重试；只有真正的临时 429 才保留有界 backoff，避免额度耗尽时每个
  binding 调用等待数个 240 秒周期。
- `make execution-preflight ARGS=...`：执行前同时检查 provider 与每个 selected
  case 的 binding 完整性。provider 不可用时，只有所有 claim 都已有非空、
  非 `UNBOUND` 的 binding 才允许进入 `offline` 模式，否则直接阻塞。

### P4：新建一致性负例队列（需明确授权）

这是达到可发表门槛的唯一数据侧方案：

1. 从官方 invalid finding 中筛选“报告声称效果在源码路径上缺席”的候选，
   不复用当前 `invalid` 标签作为一致性真值。
2. 为每个候选建立负 witness slice，要求
   `P_and_T=sat`、`P_and_T_and_not_V=sat`、`P_and_T_and_not_I=unsat`。
3. 新队列与当前 40 个正例一起冻结为新样本，记录来源、hash、标签规则与
   项目分层上限；新协议版本下重跑全部 case。
4. 只有当一致性 FPR 上界 ≤20%、负例数 ≥24、label review 清零时才可从
   `coverage-limited` 晋升。

## 5. 本轮已执行与结论

- 已核查所有评测路径、门禁、失败队列与 10 个负例 FP 的原始 witness 证据。
- 已实测 OpenCode API 可达但周额度耗尽（`429 / GoUsageLimitError`），模型相关
  恢复当前无法执行；传输层已改为对此类错误立即失败。
- 已尝试对 5 个有冻结 Stage-2 和 bindings 的 unresolved 负例做无模型重跑；
  工具仍会为缺 binding 的 claim 调用 `stage3_binding_llm`，因此已停止该无效重试，
  未产生新的权威 run。
- 当前四指标保持 `0.2000 / 0.2500 / 0.5000 / 0.3333`，发布状态保持
  `coverage-limited`。这不是“不改进”，而是拒绝用改标签、放宽门槛或挑案例换数值。
- 本轮又发现外部数据根 `c4_pipeline_output/` 整体缺失（原约 11GB）。根因已定位：
  `docs/REPOSITORY_GUIDE.md` 旧版把它误列为可再生缓存，`scripts/cleanup_generated.sh`
  旧版以无条件 `rm -rf` 实现了该错误口径。该目录未被 Git 跟踪，也未找到可用备份，
  因此 Stage-1 重切片与负例 witness authoring 额外受数据根缺失阻塞。
  后续已按冻结案例表完成源文件级部分恢复（60 个负例源文件，27 个唯一文件），
  但完整 checkout、`findings.json`、flatten corpus 与 submodule 快照仍未恢复；
  详见 `docs/REPOSITORY_GUIDE.md` 第 5 节。`make doctor` 仍明确报告缺失。
  `mainline_metrics.json` 与 `tools/stage3/runs/` 仍完整，权威四指标不受影响。
  清理脚本已改为 dry-run 默认 + 保护路径守卫，文档口径已纠正；`make doctor`
  仍明确报告缺失，不能用放宽自检的方式掩盖。
- 同一误清理还删除了 `mainline_negative_p1/p3/p4_rejected_runs`；
  `label_review_gate.json` 引用它们作为 label-review 证据。该证据链当前同样
  不完整，恢复时需要与数据根一起核查，不能据此把 2 个 label review 清零。

优先执行顺序：先恢复外部数据根并确认 `make doctor` 通过，再按 P1 → P2 → P3 → P4 执行。
P1/P2 在 provider 与数据根恢复后可立即执行且不改协议；P3/P4 需要先取得协议版本与
样本变更授权。

