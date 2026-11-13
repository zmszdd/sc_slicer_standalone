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
         └─ metrics_sync → unified_metrics（唯一四指标）
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
| stage2 产物 | `stage3-spec.json` + `constraints.json` + `formalization.json` | `main.py run` | stage3 case builder / binding |
| stage3 案例 | `src/` + `stage2_run/` + `bindings/` + `foundry.toml` | `lib.case_builder.assemble_case` | `case_runner` |
| stage3 裁决 | `consistency_verdict` per claim | `stage3_pipeline` | `stage3_multi` / metrics |
| 四指标 | `unified_metrics.json` | `metrics_sync` | 对外报告 |

## 每步唯一实现（Single Source of Truth）

| 步骤 | 唯一模块 | 禁止重复 |
| --- | --- | --- |
| 案例组装 | `tools/stage3/lib/case_builder.py::assemble_case` | 不得在 CLI 里手写 copy |
| 绑定提案 | `tools/stage3/lib/case_runner.py::bind_claims` | `stage3_bind` / `stage3_eval_run` 都调用它 |
| 差分执行 | `tools/stage3/cli/stage3_multi.py` → `stage3_pipeline.py` | 只有这一条 |
| 裁决映射 | `tools/stage3/lib/case_runner.py::derive_verdicts` | eval/runner 共用 |
| 锚点解析 | `tools/stage3/lib/anchor_resolver.py::resolve_anchors` | binding LLM 只消费其结果 |
| 指标口径 | `tools/stage3/lib/metrics_sync.py` + `unified_metrics.py` | 四指标同源 |

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
4. `metrics_sync` 出统一四指标。

旧的 `blind_*` 脚本只做数据抓取与 flatten 预处理，是 stage1 数据准备，
不是第二条验证主线；它们不直接产出 verdict。

## 参考补丁与端到端召回

`case/patched` 是 stage3 差分主线的正式路由（`stage3_pipeline` 的
`reference_patch` 分支）。机制天花板案例（`not_dynamically_expressible` /
`reference_patch_required`）无法用 `assert(I)` 注入复现时，走参考补丁差分：
`original` 成功 + `patched` 失败 = `violation_reproduced`，与自动口径共用同一
`derive_verdicts` / `metrics_sync` 裁决链。

因此 `unified_metrics` 的端到端召回已并入参考补丁复现；`recall_automatic`
单列自动口径（assert 注入 + rebind，不含人工修复），便于观察机制差异。

## 本次落地

- 抽取 `tools/stage3/lib/case_runner.py`，`bind_claims`/`run_multi`/
  `derive_verdicts` 成为 stage3 绑定与裁决的唯一实现；`stage3_bind` 与
  `stage3_eval_run` 已改为调用它（209 个 stage3 单测 + 35 个 pipeline 单测通过）。
- `main.py mainline` 作为唯一权威入口，`pipeline-run` 为其同义别名。

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
