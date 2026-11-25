# 主线架构：一条完整、可靠、通用的流水线

本文是唯一权威的主线定义。所有案例（dev、盲测、新增案例）都必须走同一条主线；
任何"只服务某个数据集"的旁路脚本都必须收敛到这条主线上，不得成为第二实现。

## 主线（唯一路径）

```
manifest (pipeline-manifest/1)
   │
   ├─ stage1 切片/复活（并行）
   │     └─ run.sh（Rust resurrect-v2，源码切片）
   │     └─ standalone_poc_pipeline.py（PoC 复活 → 自包含 contract.flattened.t.sol）
   │
   ├─ stage2 规则化（并行）
   │     └─ main.py run（report → P/I/V → formalization.json / stage3-spec.json）
   │
   └─ stage3 差分验证（join 后）
         └─ case_runner.bind_claims（唯一绑定实现）
         └─ stage3_multi → stage3_pipeline（唯一差分实现）
         └─ case_runner.derive_verdicts（唯一裁决映射）
         └─ metrics_sync → mainline_metrics（分层随机抽样，对外权威）
         │          ├─ fullset_metrics（全量诊断对照）
         │          └─ unified_metrics（105 抽样诊断对照）
```

入口（同一实现，同一 runner）：

```bash
python main.py mainline --manifest <case.json>      # 单案例主线（权威入口）
python main.py mainline --manifest <case.json> --skip-stage1   # 已切片/已 flatten
python main.py pipeline-batch --manifest <batch.json>          # 批量 fan-in，内部仍走 mainline
```

## 数据契约

| 交接 | 契约 | 生产者 | 消费者 |
| --- | --- | --- | --- |
| 输入清单 | `pipeline-manifest/1` | `manifest_gen.py` | `main.py mainline` |
| stage1 产物 | `contract.flattened.t.sol`（自包含含 PoC test harness）| `run.sh` / `standalone_poc_pipeline.py` | stage3 case builder |
| stage1 路由 | `harness-manifest.json`（route / test_entrypoint / forge command / compile hash / blocker） | `lib.harness_manifest` | stage3 case builder / 状态审计 |
| harness 资格 | `harness-qualification.json`（runnable / needs_input / blockers） | `tools/pipeline/lib/harness_qualification` | `case_run` / `manifest_gen` |
| stage2 产物 | `stage3-spec.json` + `constraints.json` + `formalization.json` | `main.py run` | stage3 case builder / binding |
| stage2 最终合同 | `stage2-restatement.json` + `stage2-restated-contract.json` | `lib.stage2_restate` | `stage3_pipeline` 门禁 / execution contract |
| 参考补丁 | `reference-patch-manifest.json`（source hash / overrides / compile validation） | `lib.reference_patch` | M1 差分路由 |
| stage3 案例 | `src/` + `stage2_run/` + `bindings/` + `foundry.toml` | `lib.case_builder.assemble_case` | `case_runner` |
| 绑定可见域 | `binding-scope.json` / `observable-ir.json` | `lib.binding_scope` + `lib.observable_ir` | `recipe_compiler` / `binding_llm` / `stage3_pipeline` |
| 源码声明索引 | `source-ir.json`（contracts/functions/state/modifiers） | `lib.source_ir` | `observable_ir` 注释 / 绑定一致性审计 |
| 绑定性反馈 | `bindability-feedback.json` | `lib.case_runner.bind_claims` | `lib.stage2_restate.build_final_contract` |
| stage3 裁决 | `consistency_verdict` per claim | `stage3_pipeline` | `stage3_multi` / metrics |
| witness 路由 | `witness_route`（primary_reason / next_action） | `lib.witness_router` | 失败归因 / metrics 排除 |
| 运行清单 | `run-manifest.json`（run_id / created_at / 协议哈希 / 输入哈希） | `stage3_pipeline` | `metrics_sync` |
| 负样本见证 | `execution-gate.json::negative_witness` | `lib.execution_gate` | `run_dev_24` / `current_denominator` |
| trusted 负样本路由 | `stage2-contract-gate.json::negative_witness` | `lib.stage2_restate` + `lib.stage2_contract` | Stage3 negative witness harness |
| 四指标（对外权威，一致性） | `mainline_metrics.json::canonical_metrics` | `metrics_sync` → `mainline_metrics.py` | 论文主表 |
| 四指标（漏洞级伴生） | `mainline_metrics.json::headline_metrics` | `metrics_sync` → `mainline_metrics.py` | 诊断对照 |
| 四指标（全量诊断） | `fullset_metrics.json` | `metrics_sync` → `fullset_metrics.py` | 诊断对照 |
| 四指标（105 抽样诊断） | `unified_metrics.json` | `metrics_sync` → `unified_metrics.py` | 诊断对照 |
| locked eval 合同 | `locked_eval_contract.json` | `lib.locked_eval` / `make locked-eval-check` | 四指标刷新门禁 |

## 每步唯一实现（Single Source of Truth）

| 步骤 | 唯一模块 | 禁止重复 |
| --- | --- | --- |
| 案例组装 | `tools/stage3/lib/case_builder.py::assemble_case` | 不得在 CLI 里手写 copy |
| 绑定提案 | `tools/stage3/lib/case_runner.py::bind_claims` | `stage3_bind` / `stage3_eval_run` 都调用它 |
| 差分执行 | `tools/stage3/cli/stage3_multi.py` → `stage3_pipeline.py` | 只有这一条 |
| 裁决映射 | `tools/stage3/lib/case_runner.py::derive_verdicts` | eval/runner 共用 |
| 锚点解析 | `tools/stage3/lib/anchor_resolver.py::resolve_anchors` | binding LLM 只消费其结果 |
| 绑定可见域恢复 | `tools/stage3/lib/binding_scope.py` | 不得在审计脚本按案例重写 patch target |
| 确定性 recipe 编译 | `tools/stage3/lib/recipe_compiler.py` + `observable_recipes.py` | 只有类型/检查点/可见性/唯一性全满足才补绑 |
| 绑定性反馈 | `tools/stage3/lib/bindability_feedback.py` + `case_runner.py` | `partial_binding`/`binding_error` 必须回到 Stage2 重述，不得猜绑 |
| Stage2 弱不变量重述 | `tools/stage3/lib/stage2_restate.py::restate_claim` / `build_final_contract` | 不得在 CLI 临时改 I/V 语义 |
| Stage2 强不变量门禁 | `tools/stage3/lib/strong_invariant.py` + `stage2_contract.decide(strict=True)` | snapshot-only/unclassified 不得 auto_assert，除非有已验收重述 |
| trusted 负样本路由 | `tools/stage3/lib/stage2_restate.py::build_final_contract` + `tools/stage3/lib/execution_gate.py::trusted_rejection` | 不得在 runner 里按 case_id 特判；重述未验收时保持 unresolved |
| negative witness 准入 | `tools/stage3/lib/stage2_contract.py::decide` | trusted invalid 只关闭自动漏洞断言，不允许阻断 negative witness；仍不得转 TN |
| Stage1 harness 路由 | `tools/stage3/lib/harness_manifest.py` | 不得在审计脚本重复判定 |
| Stage1 harness 资格 | `tools/pipeline/lib/harness_qualification.py` | no entrypoint / live RPC / no skeleton 必须 needs_input |
| witness 单一主因 | `tools/stage3/lib/witness_router.py` | mixed 失败必须归到单一 primary_reason |
| 参考补丁物化 | `tools/stage3/lib/reference_patch.py::build_reference_patch` | 不得按案例手改 `patched/` |
| 指标口径 | `tools/stage3/lib/metrics_sync.py` + `mainline_metrics.py`（分层抽样，对外权威）+ `fullset_metrics.py`/`unified_metrics.py`（诊断对照） | 四指标同源，分层抽样口径为准 |
| 负样本见证 | `tools/stage3/lib/execution_gate.py::negative_witness` | 三查询不全不得从 unresolved 转 TN |

## 协议版本与运行可复现性

`tools/stage3/lib/mainline_protocol.py` 是主线协议的唯一版本定义。它对
`tools/stage3/mainline-protocol.json` 中的基线进行校验，哈希覆盖 Stage1 入口/
Rust 源码、Stage2 核心与 Prompt、Pipeline runner、Stage3 核心与指标生成器；
不读取任何私钥配置。

每个 Stage3 run 同时写出 `artifact-fingerprint.json` 和 `run-manifest.json`：
前者供指标入口判断是否为当前协议，后者提供确定的 `created_at` 排序依据。
`metrics_sync` 不再依赖文件系统 mtime；带清单的 run 按清单时间排序，
历史 run 退化为名称中的 UTC 时间戳，二者都没有时保持未排序。

行为变更必须先提升 `PROTOCOL_VERSION`、执行 `make protocol-baseline`，
再重跑评测。未提升版本却改动受控文件时，`make protocol-check` 必须失败，
旧 run 也必须被 `current_denominator` 排除。

## 入口与别名（旧入口一律收敛，不再新增）

| 入口 | 状态 | 说明 |
| --- | --- | --- |
| `python main.py mainline --manifest ...` | 权威 | 唯一主线入口 |
| `python main.py pipeline-run ...` | 别名 | 与 mainline 同一 runner |
| `python main.py pipeline ...` | 旧别名 | 单案例组装+运行，仅手工绑定场景 |
| `python main.py case ...` | 旧别名 | 扁平案例，内部走 manifest_gen → mainline |
| `python main.py pipeline-batch ...` | 批量 | 并行 fan-in，内部仍走 mainline |
| `python main.py stage3 autorun ...` | 旧别名 | 组装+绑定+差分+验收的串联，底层复用 case_runner |

## 盲测不再是旁路

盲测（Code4rena 跨项目）与 dev 走完全相同的契约：

1. `standalone_poc_pipeline.py` 产出 `contract.flattened.t.sol`（stage1 契约）。
2. `manifest_gen.py` 为每个 finding 生成 `pipeline-manifest/1`。
3. `main.py mainline --manifest ...` 跑 stage2 → stage3（与 dev 相同 runner）。
4. `metrics_sync` 出统一四指标：`mainline_metrics.py` 以分层随机抽样（seed 固定）为对外权威口径并带 95% CI；`fullset_metrics.py`（全量判例分母）与 `unified_metrics.py`（105 抽样）保留为诊断对照。

旧的 `blind_*` 脚本只做数据抓取与 flatten 预处理，是 stage1 数据准备，
不是第二条验证主线；它们不直接产出 verdict。

## 参考补丁与端到端召回

`case/patched` 是 stage3 差分主线的正式路由（`stage3_pipeline` 的
`reference_patch` 分支）。机制天花板案例（`not_dynamically_expressible` /
`reference_patch_required`）无法用 `assert(I)` 注入复现时，走参考补丁差分：
`original` 成功 + `patched` 失败 = `violation_reproduced`，与自动口径共用同一
`derive_verdicts` / `metrics_sync` 裁决链。

参考补丁只有两个数据源，由 `lib.reference_patch` 唯一实现：
`case/patched/`（已修复的源码树，逐字使用）或 `case/patched.diff`
（针对 `case/src` 的 unified diff，`patch -p1` 确定性物化出 `case/patched/`）。
stage3_pipeline 在需要 M1 路线时自动物化，不再要求人工预建目录。

因此 `unified_metrics` 的端到端召回已并入参考补丁复现；`recall_automatic`
单列自动口径（assert 注入 + rebind，不含人工修复），便于观察机制差异。

## 本次落地

- 抽取 `tools/stage3/lib/case_runner.py`，`bind_claims`/`run_multi`/
  `derive_verdicts` 成为 stage3 绑定与裁决的唯一实现；`stage3_bind` 与
  `stage3_eval_run` 已改为调用它。测试数量以当前 `make test` 输出为准。
- `main.py mainline` 作为唯一权威入口，`pipeline-run` 为其同义别名。
- Stage2 弱不变量重述支持 V 中正向断言的 after/配置边界违反：只取未被
  `not` 包裹的数值原子，仍由共享审计裁决；旧 formal-plan 生成的
  `contract_present=false` observability 合同不再把历史声明误路由到
  `reference_patch_candidate`。

## 实验合同（2026-11-17）

- dev252 只作为开发集；1213 个同项目正样本标记为诊断保留池，不作为独立测试集。
- 独立测试集来自新项目，冻结后一次性运行；最低建议 80 正 + 40 负。
- 四指标固定为准确率、精确率、召回率、F1；完成率单列为漏斗指标。
- 指标合同：`docs/DEV_EVAL_CONTRACT_20261117.md`。
- dev24 分层回归：`tools/stage3/evaluation/frozen/dev24_20261117.json`。
- 生成合同：`make eval-contract`；运行 dev24：`make dev24`。

## 清理记录（冗余文件与分支）

已删除的冗余/一次性脚本（全部无代码引用或仅被历史日志引用，数据产物已保留在磁盘）：

- `tools/stage3/cli/stage3_eval_assemble.py`（被 `stage3_assemble.py` + `case_builder.assemble_case` 取代）
- `tools/stage3/evaluation/metrics/precision_recall.py`（被 `unified_metrics.py` 取代）
- `scripts/code4rena/cleanup_flatten_caches.py`、`run_code4rena_flatten_local_reports.py`、
  `run_code4rena_repo_fallback_flatten.py`（被 `standalone_poc_pipeline.py` 取代）
- `scripts/code4rena/build_blind_flatten_root.py`、`blind_poc_summary.py`、
  `tools/stage3/evaluation/metrics/blind_report_drafts.py`、`build_blind_set.py`
  （一次性盲测数据准备桥，主线上由 `standalone_poc_pipeline.py` + `manifest_gen.py` 取代）

保留：`standalone_poc_pipeline.py`、`findings_lookup.py`、`fetch_code4rena_reports.py`
（stage1 数据准备），以及 `blind_goldset/`、`blind_flatten_root/`、`blind_set.json`
（权威度量输入数据，非脚本分支）。

### 2026-11-24 产物清理

主线边界保持不变：权威输入仍是冻结样本、官方负例池、`mainline_goldset_1_7_31_pos`、
`mainline_goldset_1_7_31_neg`、`mainline_stage2_out` 与其 manifest 指向的
`mainline_stage2_1_7_28_api_pos`；权威执行仍是
`main.py mainline → case_runner → stage3_multi → metrics_sync → mainline_metrics`；
权威报表仍是 `current_denominator.json`、`locked_eval_contract.json`、
`mainline_metrics.json`、`paper_evidence_report.json`、`metric_alignment_report.json`、
`case_readiness.json` 与 `label_review_gate.json`。

本轮删除的都是无代码/文档引用、也不在 provenance 中的历史副本：

- `tools/stage3/evaluation/metrics/`：旧 goldset 副本
  （`mainline_goldset_1_7_15/16`、`mainline_goldset_mini`、
  `mainline_negative_goldset_1_7_16`），P0/P1-obs/P2 候选 goldset 与 raw
  rejected runs，P0/P2 候选 Stage2 输出，以及 `mainline_stage2_out` 中
  149 个 `.incomplete-*` 临时目录。
- `c4_pipeline_output/`：1.7.26～1.7.33 的旧 backup/pilot、旧 negative
  stage2/cases/flatten 快照和三个 `official_negative_witness_flat_all*`
  重复目录。
- 保留 `mainline_negative_p1_rejected_runs`：其中一条当前协议的
  `violation_reproduced` 是冻结负例的 label-review 证据，不能随候选结论一起删除。
- 保留 `negative_recovery_p0_report.json`、`negative_recovery_p3_report.json`、
  `negative_recovery_p4_report.json`、P0/P1/P1-obs/P2/P3/P4 的 candidate eval
  摘要，以及
  `mainline_negative_p1_obs_preflight_stage2/preflight-report.json`：
  它们记录“无新增 eligible 负例”的结论，体积极小且不进入分母。
  P3 的 2 个候选 run 隔离在 `mainline_negative_p3_rejected_runs`，P4 的 5 个
  候选 run 隔离在 `mainline_negative_p4_rejected_runs`；其中没有 label-review
  信号。

上述“删除”仅指旧子集的历史清理；外部数据根 `c4_pipeline_output/` 整体删除不属于
授权操作，恢复边界见 `docs/REPOSITORY_GUIDE.md` 第 2、5 节。

清理后重新生成 `label_review_gate.json`，复核来源收敛为 `runs` 与
`mainline_negative_p1_rejected_runs`，复核案例仍为 2 个；协议、样本、标签、
混淆矩阵和四指标均未变化。

`stage2_observability_preflight.py` 与
`stage2_restatement_binding_candidate.py` 都属于候选区诊断工具，不在
`main.py mainline` 权威执行链上；它们只能产出隔离候选，必须由
`negative_recovery_gate` 证明新增 eligible 负例且不丢失既有样本后才能晋升。

## report-only A+（2026-11-20）

Stage2 仍在 `report.json` 的自然语言边界内工作。A+ 把一次性的 P/I/V 主 I
决策改为候选抽取、确定性排序和兼容输出：canonical I 与显式 intent 备选写入
`invariant-candidates.json`，checkpoint 归一化后供 Stage3 排序。Stage3 A+ gate
只把 checkpoint、observable、independence 当硬门槛，snapshot/review 类标签
保留为 quality label；`stage3_multi` 默认按质量执行 top-3 claim。

该路径不改变历史报告忠实性审计，也不把软标签转成真实阴性；`--stage2-gate-mode
strict` 与 `--claim-top-k 0` 仍可复现旧口径。

### 一致性证据收口（mainline/1.6.1）

- `revert_expected` 路线不再豁免独立 effect gate：原始/补丁差分只是复现证据，
  没有独立 V witness 时判为 `effect_not_witnessed`，不再进入一致性 FP。
- `execution_gate.metric_eligibility.consistency` 只使用报告文本推导的
  impact sufficiency；trusted judge label 仍只控制漏洞级 eligibility，避免把
  标签泄漏进工具行为。
- reference-patch 路线仍由补丁本身裁决，不受独立 effect gate 影响。

### 一致性一等主表（report-only，mainline/1.7.36）

主线目标不是漏洞分类，而是判断“自然语言报告声称的效果”与“源码实际效果”
是否一致。`mainline_metrics.json::canonical_metrics` 是唯一论文主表：

刷新派生指标使用 `make metrics`：它只读冻结样本与既有 run，不调用
`sample_mainline.py`。重新选样必须显式执行 `make metrics-resample`，且只在
新协议版本和明确授权下进行。

| 指标 | 公式 | 口径 |
| --- | --- | --- |
| Accuracy_consistency | `(TP_consistency + TN) / (全部 sampled positives + evaluated negatives)` | 未评测正例计为错误，未被独立证据评测的负例不入分母 |
| Recall_consistency | `TP_consistency / 全部 sampled positives` | 未评测正例计 FN |
| Precision_consistency | `TP_consistency / (TP_consistency + FP_consistency)` | 负例上独立见证 V 即为 FP，不受 I 或影响等级豁免 |
| F1_consistency | 上述 precision 与保守 recall 的调和平均 | 项目聚类 bootstrap CI |

一致性 ground truth 是冻结样本上的操作化定义：正例来自冻结的 accepted
finding；负例来自官方 invalid 池。一致性判定只问“报告声称的效果 V 是否在
源码执行路径上被独立 witness 见证”，I 只决定漏洞级伴生口径，不再决定
一致性 TP/FP。正例 V 见证为 TP；负例 V 见证为 FP；负例只有
`negative_witness.eligible=true` 且无 V witness 才是 TN。两类证据都没有的
终态负例保持 unresolved，不计 TN、不进入 FP/FN 分母。漏洞级四指标
（`headline_metrics`）保留为伴生诊断，不再进入论文主表。

主表发布门禁与漏洞级伴生门禁分离：`mainline_metrics.json::consistency_gate`
和 `locked_eval_contract.json::primary_gate` 是一致性主表的权威发布状态；
`locked_eval_contract.json::publishable` 只表示漏洞级伴生口径。一致性负例
下限 24 对应“已观察到 1 个 FP 时单侧 95% FPR 上界 ≤20%”，当前 10 个已评测
负例中有 10 个 V witness FP，对应上界 100%，因此仍为 `coverage-limited`。

`current_denominator.py`、`case_readiness.py`、`locked_eval` 与
`mainline_metrics.py` 现在使用同一负例入组规则：有独立 V witness 构成
consistency FP，或有 eligible negative witness 且无 V 构成 TN。`make metrics`
会先重建
current denominator 再生成其余报表，避免不同报表显示不同负例覆盖。

report 文本的 impact sufficiency 只保留在漏洞级 `vulnerability` 门禁；
终态 verdict 一旦存在，报表层不再用它阻断 consistency 入组，否则
“低影响但仍可观测到 V”的案例会被错误排除。

该改动只改变报表口径，不改变 Stage-1/2/3 执行语义，因此协议版本仍为
`mainline/1.7.36`；只刷新 report-only baseline 与 report hash，既有 run
不被判过期。`metric_alignment_report.json::sources` 记录权威指标与 A+ smoke
报告的 sha256。
