# 仓库导航与清理边界

本文说明当前仓库中哪些内容是主线权威资产，哪些是可再生缓存。给老师或合作者看代码时，按本文顺序阅读即可。

## 1. 权威入口

| 内容 | 位置 |
| --- | --- |
| 主线架构 | `docs/MAINLINE_ARCHITECTURE.md` |
| 权威指标口径与历史记录 | `docs/OBJECTIVE_METRICS_20261121.md` |
| 根因与完整方案 | `docs/ROOT_CAUSE_AND_FULL_SOLUTION_20261124.md` |
| Stage-2 可观测性方案 | `docs/STAGE2_OBSERVABILITY_SOLUTION_20261124.md` |
| 当前流程图 | `docs/origin2.drawio` |
| 权威四指标 | `tools/stage3/evaluation/metrics/mainline_metrics.json` / `.md` |
| 论文证据表 | `tools/stage3/evaluation/metrics/paper_evidence_report.json` / `.md` |
| 口径对齐表 | `tools/stage3/evaluation/metrics/metric_alignment_report.json` / `.md` |
| 发布门禁 | `tools/stage3/evaluation/metrics/locked_eval_contract.json` / `.md` |
| 协议基线 | `tools/stage3/mainline-protocol.json` |
| 数据来源与第三方材料 | `docs/DATA_SOURCES.md` |

当前权威状态为 `ready=true`、`publishable=false`、`coverage-limited`。不要使用 dev252、A+/hardened smoke 或旧协议结果替换主表。

## 2. 必须保留的本地数据

以下内容虽然由脚本生成或被 `.gitignore` 排除，但当前权威指标依赖它们，不能删除：

- `c4_pipeline_output/`：外部数据根，含官方负样本来源 `findings.json`、
  verified/negative flatten 语料与 pinned submodule 缓存。不是缓存，不能用
  “重新生成”代替恢复。
- `code4rena_reports/`：官方报告缓存，负例标签溯源的原始输入。
- `tools/stage3/runs/`：当前协议 stage3 run artifact。
- `tools/stage3/evaluation/metrics/mainline_goldset_1_7_31_pos/`
- `tools/stage3/evaluation/metrics/mainline_goldset_1_7_31_neg/`
- `tools/stage3/evaluation/metrics/mainline_stage2_out/`
- `tools/stage3/cases/panoptic_builder_init/`：pipeline 端到端测试使用的复用案例。
- `config/llm.env`：本地 API 配置；不纳入版本控制。

## 3. 可再生产物

以下内容不进入版本控制，需要时由脚本或外部数据重新生成：

- `foundry_runs/`、`logs/`、`results/`、`runs/`（根目录）：旧运行与日志。
- `target/`：Rust 编译产物。
- `tools/stage3/evaluation/metrics/mainline_negative_*/`：P0–P4 负例恢复候选与 rejected runs；汇总报告保留在同级 `*.json` / `*.md`。
- `docs/2025-1357-paper.pdf`：外部论文，不在项目源码内。

`scripts/cleanup_generated.sh` 默认 dry-run；加 `--apply` 后只删除 Python/tooling
缓存（`__pycache__`、`*.pyc`、`.pytest_cache` 等）。它内置第 2 节的保护路径清单，
不修改 Git index，也不会删除外部数据根、run artifact 或任何 tracked 文件。
Makefile 入口为 `make hygiene`（只读盘点）与 `make hygiene-apply`（仅清缓存）。

## 4. 验证顺序

```bash
make doctor
make test
make protocol-check
make metrics-check
make locked-eval-check
make paper-evidence
make metric-alignment
```

仓库中 `tools/report_constraints_v2/evaluation/` 与 `results/` 下的历史小文件主要是旧提示实验和回归 fixture；它们体积很小且部分测试直接读取，保留不删。历史方案文档也保留作溯源，但阅读优先级低于第 1 节列出的权威文档。

## 5. 工程卫生根因（2026-11-25）

`c4_pipeline_output/` 曾被本节旧版误列为“可再生缓存”，并交给一个无条件
`rm -rf` 的清理脚本处理，导致该外部数据根整体缺失。实际它是负例来源、
flatten 语料与 submodule 快照的唯一本地副本，且未被 Git 跟踪，因此无法用
`git restore` 恢复。当前数据根仍未恢复；`make doctor` 会明确报告缺失。

修复后的边界：

- 清理脚本默认只读，保护路径清单覆盖数据根、goldset、stage3 runs 与协议文件；
  只删除缓存，不碰 tracked 文件。
- 数据根只能从备份恢复，或通过 `config/paths.local.env` /
  `C4_OUTPUT_ROOT` 指向已有副本；不允许通过删目录“重建”。
- 2026-11-25 已做**源文件级部分恢复**：
  `python3 scripts/code4rena/restore_frozen_case_sources.py` 按冻结案例表的
  URL 和目标目录中的 commit 恢复了 60 个负例源文件（27 个唯一文件），清单在
  `c4_pipeline_output/_frozen_case_source_restore_manifest.json`。脚本会跳过
  已存在文件，不改标签、协议或指标。原数据根中的完整仓库 checkout、
  `findings.json`、flatten corpus、submodule 快照仍未恢复；`make doctor`
  仍因 `negative_flatten_root` 缺失而失败，不能用这份部分恢复冒充完整数据根。
- 工作树中大量主线源码/文档仍是 untracked，属于历史提交纪律问题，不是垃圾；
  清理与提交必须分开处理，不能因为 `git status` 脏就批量删除。
- 同一脚本还删除了 `mainline_negative_p1/p3/p4_rejected_runs`，而
  `label_review_gate.json` 仍引用这些路径作为 label-review 证据。恢复数据根时
  必须同时核查这三个目录；在恢复前不能把 label-review 视为已重新验证。
