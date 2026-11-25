# 数据来源与第三方材料

本文说明仓库内数据的来源、未随仓库上传的外部数据，以及展示或论文写作时的引用边界。
它不是法律意见；公开再分发第三方报告文本前，请确认对应来源的使用条款。

## 1. 仓库内数据

| 数据 | 位置 | 来源 | 用途与边界 |
| --- | --- | --- | --- |
| 审计项目清单 | `data/code4rena/*.csv` | Code4rena 公开审计列表 | 选取项目 ID，不含报告正文 |
| 官方负例池 | `tools/stage3/evaluation/metrics/official_negative_pool_20261121.json` | Code4rena 官方 `invalid` findings | 冻结负例候选与分层；标签按官方判例保留，不重标 |
| 负例 Stage-1 案例表 | `tools/stage3/evaluation/metrics/official_negative_stage1_cases_20261121.json` | 上述 findings 对应的 GitHub 审计仓库 | 记录冻结 `source_url` / `source_path`，不改标签 |
| 正负例 goldset | `tools/stage3/evaluation/metrics/mainline_goldset_1_7_31_pos/`、`mainline_goldset_1_7_31_neg/` | 上述公开来源经本项目冻结抽样 | `selection.json` / `manifest.json` 记录协议、标签与案例来源；`original-report` 为第三方报告文本 |
| 权威指标与证据 | `tools/stage3/evaluation/metrics/mainline_metrics.json` / `.md`、`paper_evidence_report.*`、`metric_alignment_report.*`、`locked_eval_contract.*` | 本项目工具生成 | 论文主表与发布门禁依据；不是外部数据 |
| 协议与样本 | `tools/stage3/mainline-protocol.json`、`tools/stage3/evaluation/frozen/` | 本项目冻结 | 协议指纹与样本定义 |
| `solar/` | `solar/` | 上游 `argotorg/solar` | 第三方代码，保留其自有许可 `solar/LICENSE-MIT`、`solar/LICENSE-APACHE` |

## 2. 未随仓库上传的外部数据

以下路径由本机保存，靠 `config/paths.local.env` 或环境变量解析；配置方法见
`docs/PORTABILITY_20261123.md`。它们不是源码，不进入 GitHub：

| 配置变量 | 内容 | 说明 |
| --- | --- | --- |
| `VERIFIED_FLATTEN_ROOT` | `/root/poc_repro_work/verified_flatten_pass_1568_exact_cases` | 正例 flatten 语料，约 1.9GB |
| `C4_OUTPUT_ROOT` | `c4_pipeline_output/` | flatten 输出、`findings.json`、pinned submodule 快照；当前仅恢复冻结案例源文件，见 `docs/REPOSITORY_GUIDE.md:78` |
| `CODE4RENA_REPORTS_ROOT` | `code4rena_reports/` | 官方报告缓存，负例标签溯源输入 |
| `NEGATIVE_FLATTEN_ROOT` | `c4_pipeline_output/objective_negative_flatten_20261121` | 官方负例 flatten corpus |
| `FORGE_STD_CANDIDATES` | 本机 `forge-std` 路径 | 负例 witness authoring 依赖 |
| LLM provider key | `config/llm.env`、`config/*.local.env` | 凭据，永不上传 |

`tools/stage3/runs/` 是当前协议的 stage3 run artifact，约 21GB，也只在本地保留。
仓库内的 goldset 与指标文件足以阅读和核对结果；要全量重跑仍需上述外部数据与 provider。

当前仓库已包含 `c4_pipeline_output/_github_repos_by_project/` 下 27 个冻结案例源文件，
以及 `c4_pipeline_output/_frozen_case_source_restore_manifest.json`。这只是源文件级
部分恢复，不包含完整仓库 checkout、`findings.json`、flatten corpus 或 submodule 快照。

## 3. 展示与论文口径

- 论文主表使用 `canonical_metrics` 的 consistency 四指标；漏洞级四指标只是伴生诊断。
- 当前状态为 `coverage-limited`、`publishable=false`：负例有效覆盖不足，FPR 上界超过发布上限。
- `dev252`、`dev24`、`A+/hardened/top3` 与其他 smoke 结果只作诊断，不进入权威分母。
- 展示第三方报告文本时，请保留 Code4rena 来源说明；`solar/` 保留上游许可。
- 本仓库不分发任何 API key；模型生成产物只记录结果和 usage，不含凭据。
