# Changelog

## Unreleased

- **修复 S12 引入的回归：`main.py batch` 曾完全不可用。**`main.py` 会为
  `batch` 注入 `--claim-verdict signals`，但 `cli/batch_verify.py` 既没有声明该
  参数（argparse 直接 `unrecognized arguments` 并退出 2），也没有把它转发给
  `run` 子进程（即使不报错，每个 batch run 也会静默落回 `legacy`，而子进程写下的
  `provenance.claim_verdict_policy` 正是 `verify` 重放的依据）。现已声明并转发。
- 新增两条回归防护（`tests/test_main_entry.py`），均已做负向验证：
  1. `test_every_injected_flag_is_declared_by_its_target_script` —— 静态检查
     `main.py` 注入的每个 flag 都出现在目标脚本的 parser 源码里。**`cmd --help`
     冒烟测试在结构上不可能发现这类问题**：argparse 处理 `--help` 时就退出 0，
     早于报告未识别参数；而不给必填参数同样无效，argparse 会先报
     `the following arguments are required`，同样早于未识别参数。
  2. `test_verdict_policy_reaches_the_run_subprocess` —— patch 掉
     `subprocess.run`，断言 `--claim-verdict signals` 确实进了子进程 argv，
     全程零模型调用。
- 测试基线 266 -> 268。
- **S12: 断言策略改为可切换。** `compile_bundle()` 新增 `verdict_v2` 形参，
  `cli/semantic_pipeline.py` 新增 `--claim-verdict {legacy,signals}`（默认
  `legacy`）。`main.py` 对 `run` / `batch` 自动注入 `--claim-verdict signals`
  （`STAGE2_VERDICT_DEFAULTS`），`verify` 按 `provenance.claim_verdict_policy`
  记录的策略重放，不猜测。
- `signals` 策略下，模型自报的不确定性不再否决整条断言：
  `elements.ambiguities`、`formalization.limitations`、`claim.unresolved`、
  `claim.modality != 'asserted'`、effect coverage 不完整，以及 bundle 级
  `report impacts not assigned` / `unused preconditions`，全部从否决票改为
  信息性字段；`acceptance_status` 只由结构性原因决定。
- 新增 `coverage_status`（`complete` / `partial`）与 `coverage_gaps`
  （`impacts_not_assigned` / `preconditions_not_used` /
  `effect_coverage_partial`），替代原先混在 `report_warnings` 里的覆盖率信号。
  `verdict_policy` 记录 `signals-v2`。
- `legacy` 策略下输出与 S12 之前**逐字节一致**，8 个测试文件与 78 份冻结产物
  不受影响。72 个可重算 run 上实测（零模型调用）：`candidate_checks_passed`
  由 0/72 升至 **68/72（94.4%）**；剩余 4 个 `needs_review` 全部是真问题
  （3 个 `effects_feasibility` / `safety_negation_feasibility` unsat，
  1 个 I/V 倒置）。
- **修正 `V` 的规范定义**（`prompts/definitions.py`）：原文写作 "makes I
  false"，等于把 `P AND V AND I` unsat 检查要证的结论写进了定义，使该检查退化
  为套套逻辑。现改为独立于 `I` 的可观察事实，"与 `I` 矛盾"降级为待验证的义务；
  `excludes` 同步去掉对 `I` 的引用。该文本只用于
  `preview-prompt --part definitions` 的人读呈现，**不进入发给模型的提示词**
  （运行时提示词来自冻结的 `prompts/versions/*`），故不影响任何重放。
- 再次重设 `evaluation/` 清单的 `code_sha256`：`semantic_core.py` 与
  `semantic_pipeline.py` 共 10 个 key、7 份清单。
  `prompts/definitions.py` 不在 `CODE_PATHS` 中，不受哈希约束。

- Removed the 14 root-level compatibility shim files from
  `tools/report_constraints_v2/`. The stage-2 root now contains **no `.py` at all**:
  entrypoints live in `cli/`, shared modules in `lib/`.
- The pre-refactor module names (e.g. `fidelity`, `evidence_catalog`,
  `verify_semantic`) are now served by a single `lib/compat.py` using a
  `sys.meta_path` finder that resolves them lazily and preserves module identity
  (`sys.modules['fidelity'] is sys.modules['lib.salvage']`). Registered from
  `main.py`, `tests/__init__.py`, `cli/__init__.py` and `lib/__init__.py`.
- The 3 `subprocess` call sites that used to spawn the root `semantic_pipeline.py`
  shim now use `python -m cli.semantic_pipeline` with `cwd` set to the stage-2
  directory, which removes the long-standing `sys.path[0]` pitfall.
- 10 scripts under `evaluation/` and `review_samples/` now import the real module
  paths (`lib.*` / `cli.*`) instead of relying on the alias mechanism.
- `main.py doctor` gained a self-check that all 14 legacy names still resolve.
- Re-baselined 9 `code_sha256` values in the frozen `evaluation/` manifests
  (affected by the `lib/salvage.py` subprocess change); all 46 keys re-derivable.
- Removed the obsolete guarantee that the historical root-path commands in
  `docs/` remain replayable; use `python main.py run` / `python main.py verify`.


- Refactored stage 2 (`tools/report_constraints_v2/`) into two layers: `cli/` for
  entrypoints and `lib/` for shared modules. Implementation code no longer lives at
  the stage-2 root; the 14 root-level `.py` files are now 3-4 line compatibility
  shims that alias themselves into `sys.modules` so existing importers keep working
  unchanged.
- Merged same-layer modules: `evidence_catalog.py` + `report_readiness.py` ->
  `lib/ingest.py`; `symbolic_queries.py` + `review.py` -> `lib/solving.py`;
  `fidelity.py` + `mechanical_salvage.py` -> `lib/salvage.py`;
  `run_semantic_batch.py` + `verify_semantic.py` -> `cli/batch_verify.py`.
- `main.py` now resolves command scripts in `cli/` -> `lib/` -> stage-2 root order,
  and no longer lists `solving.py` / `salvage.py` as library-only modules (both are
  also command targets).
- Re-baselined the `code_sha256` fields in the 7 frozen `evaluation/` manifests so
  they resolve to the files that now contain the code. Stage-1 assets in
  `PROTECTED_HASHES.json` are unchanged (`main.py frozen` still passes 21/21).
- Stage 1 and stage 3 untouched.

## 0.2.0

- Removed the legacy v1 resurrection path and its `--resurrect` / `--v1` entry points.
- Promoted source-backed Resurrection V2 as the only resurrection pipeline.
- Moved the preflight source normalizer into `src/source_normalizer.rs`.
- Improved target-oriented analysis so functions are included only when their AST references the focus variable, with conservative fallbacks for complex statements.
- Kept quick slicing mode available for non-resurrection output.

## 0.1.0

- Initial standalone SC_Slicer CLI.
