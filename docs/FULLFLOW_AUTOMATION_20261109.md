# 全流程自动化收口（2026-11-09）

本文件记录 P0→P1→P2 三条主线的实现结果。四指标口径仍以
`docs/METRICS_METHODOLOGY_20261108.md` 为准；本条只说明“自动化闭合到哪里”。

## 结论

- 中段链路早已可自动跑（阶段二 `main.py run/batch`，阶段三
  `cli.stage3_autorun`，跨阶段 `tools/pipeline`）。
- 本次收口三处：输入端不再产出无理由的 `TODO_` 骨架（P0）；阶段三跨合约
  注入点做确定性迁移（P1）；四指标 + 判例锚定串成一条命令（P2）。

## P0 输入归一化

- `tools/pipeline/cli/manifest_gen.py`：未匹配 flatten 的 finding 改写成
  `kind: needs_input` + `blockers: [needs_flatten]` 的结构化占位，写进
  `manifests/needs_input/`；summary 新增 `needs_input_manifests` 与
  `needs_input_reasons`。匹配 finding 的 `test_name` 缺失时从
  `contract.flattened.t.sol` 自动提取 `test_*` 函数名。
- `tools/pipeline/cli/pipeline_batch.py`：跳过 `needs_input/` 目录。

## P1 跨合约注入点迁移

- `tools/stage3/lib/binding_llm.py` 新增 `_migrate_patch_contract`：当
  `anchor_resolver` 判定为 `single_anchor` 且 LLM 仍把 `patch.contract`
  留在 PoC 测试合约时，若 binding 表达式中恰有一个由目标合约拥有的函数
  标识符，则确定性迁移 `patch.contract` 与 `patch.functions[0].name`；
  歧义/不可判定时保留原样并记录 `migration` 结果，不做猜测。
- 提案结果新增 `migration` 字段，离线可审计。

## P2 四指标一条命令

- 新增 `tools/stage3/cli/stage3_fullflow.py`（入口 `python main.py stage3 full-flow`）：
  正样本 eval → 按需负样本构造（`--negative`，只对已复现 claim 用
  `stage3_negative_build --validate`）→ `judge_anchor` 判例锚定 →
  `metrics_report` 多口径四指标，合并写 `fullflow_report.json`。
- 支持 `--positive-eval` / `--negative-results` 复用既有产物，避免重复跑模型。

## 回归

- 阶段二 484、阶段三 125、pipeline 35 项测试全绿。

## 第二轮（同日追加）

- P1 TP-2：`tools/stage3/lib/binding_llm.py` 的 `_migrate_patch_contract` 新增
  回退路径——绑定表达式里没有业务函数时，从 PoC exploit 测试函数体里扫描被
  调用的、由目标合约拥有的函数，唯一时作为注入函数；歧义仍跳过并记录
  `migration`。
- P2 权威口径：`docs/METRICS_METHODOLOGY_20261108.md` 冻结“判例 invalid 全量
  普查”为唯一对外准确率（43/58=74.1%，CI 61.6%–83.7%，FP 率 20%）。
  `judge_anchor.py` 输出新增 `fp_project_counts`（FP 家族分布：SukukFi 12 /
  GTE Perps 2 / GTE Spot 1），`judge_anchored_metrics.json` 已重新生成。
- P4 CI：`.github/workflows/ci.yml` 补齐 z3 与 foundry 依赖，四作业
  （stage1 rust / stage2 offline / stage3 unit / pipeline e2e）+ `git diff --check`。
- P4 gating：`python main.py stage3 full-flow` 新增
  `--min-reproduction-rate` / `--min-terminal-rate` / `--max-fp-rate`，失败非零退出。

## 回归

- 阶段二 484、阶段三 126、pipeline 35 项测试全绿。
