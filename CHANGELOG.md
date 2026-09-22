# Changelog

## Unreleased

- **新增 `semantic-v3.19`：修正 `access_control` 类内容规则与 grounding 规则的冲突。**
  v3.18 之后剩下的 grounding 失败，根因是**提示词两条规则无法同时满足**：
  类规则说 access control 的 `relation`
  *is the required authorization*，而 grounding 规则要求
  "those core symbols' source_ids MUST include intent_id and EVERY selected
  impact_id. Trigger/condition-only variables do not count"。授权谓词的天然来源是
  precondition，impact（一个下游回滚/损失）挂不上去；提示词里
  `outrank` / `precedence` / `conflict` 等词出现 **0 次**，从未说明谁优先。
  决定性证据：**能通过校验的编码全都违反类规则** —— `panoptic_builder_init` 通过的
  7 次把 `relation` 写成 impact 的否定形态（`builder_admin_overwritten = false`），
  没通过的 3 次写 `caller_is_authorized`；`olas_permissionless_sweep` 则 **10/10**
  都写 `caller_is_authorized`（一次都没过），其中 7 次把 impact 塞进了提示词明令
  不计的 condition 侧。模型是想服从 grounding 但没有合法落点。
  v3.19 把该句改为：condition 是受保护动作**加上缺失或被绕过的 guard**，且
  `relation` 必须能引用被选中的 impact —— 当 impact 是后果（回滚/损失/grief）而非
  授权事实时，`relation` 取**该 impact 自身可观察量的否定**。
  只改这一处，不动验证器、不动 schema（仍是 `report-formal-plan/4`）。
- **v3.19 对照实测（同样 5 例 × 10 次 = 50 次调用）**：
  校验通过 **27/50 -> 40/50（80%）**；kind 合规保持 50/50，无回归；
  `olas_permissionless_sweep` **0/10 -> 10/10**；`panoptic_builder_init` 7/10 -> **10/10**；
  `core relation observables lack intent/impact grounding` **13 次 -> 0 次**；
  `sequence_domain_fork` 仍 0/10（truth binding，与本次改动无关）；
  **没有出现任何新的失败类别**。
  副作用需记明：`intuition_pause_escrow` 的 `relation_class` 变为 access_control 5 /
  progress_or_liveness 5。两类的 `relation` 谓词形态一致、且都映射到
  `relation_obligation`，发出的公式相同，10/10 全部通过 —— 只是**标签不稳定**。
- 测试基线 292 -> 297（+5：v3.19 的旧规则已删、引用义务已写入、grounding 规则未被
  软化、progress/liveness 未被波及，以及"每个版本只在其声明的区域偏离其基线"这条
  结构性不变量改为逐版本参数化）。
- 版本号顺延：`v3.19` 已被本次仅提示词的修复占用，`semantic_axioms` / schema v6 那套
  顺延为 **v3.20**。

- **新增 `semantic-v3.18`：只改提示词，删除与编译器固定模板自相矛盾的继承文字。**
  v3.16 的正式提示词里继承了 v3.15 的三处 legacy 形状说明
  （`condition_forbids_effect` / `condition_requires_effect`），其中一段还**明确
  指示**模型："若报告称某合法操作本应完成却发生 revert，就用 condition forbids
  revert / condition requires completion"。而 `FIXED_RELATION_CLASS_PATTERN` 只允许
  `monotonicity` / `conservation` / `relation_obligation` 三种 kind，而"本应完成却
  revert"正是 `progress_or_liveness`，固定模板要求该类别用 `relation_obligation`。
  **提示词自己跟自己打架**，模型只能在两者中选一个服从。
  50 次采样的基线把两种失败分得很干净：kind 违背**只**出现在两个
  `progress_or_liveness` 案例上（各 3/10，另 7 次发出 `condition_forbids_effect`），
  其余三个案例 10/10 服从固定模板。
  v3.18 删掉这三处，不改模板、不改 schema（仍是 `report-formal-plan/4`，所以
  `lib/plan_synthesizer.py` 一行未动），只新增
  `prompts/versions/semantic_prompts_v318.py` 与 `prompts/registry.py` 的一行注册，
  `EXPERIMENTAL_VERSION` 由 v3.17 指向 v3.18。
- **v3.18 对照实测（50 次调用，5 例 × 10 次，输入与命令和基线逐字节一致）**：
  kind 合规 **36/50 -> 50/50**；两个 liveness 案例 **3/10 -> 10/10**，其
  `fixed relation template mismatch` 由 14 次降到 **0 次**；
  `panoptic_builder_init` 校验通过 0/10 -> 7/10（grounding 失败由 10/10 降到 3/10）；
  `sequence_domain_fork` 仍 0/10（truth binding，与本次改动无关）；
  **没有出现任何新的失败类别** —— 问题是被消除，不是被转移。
- 测试基线 286 -> 292（+6：legacy 形状已清除、固定模板指令仍保留、schema 未迁移、
  以及"两个版本只在声明的三处不同"这条结构性不变量）。
- `code_sha256` 零漂移：8 个清单、9 个 key 全部一致；`prompts/registry.py` 与
  `semantic_prompts_v318.py` 不在任何清单的跟踪范围内。
- HANDOFF 原先把 "v3.18/schema v6" 预留给了 `semantic_axioms` / I 空真那套更大的改造。
  本次 v3.18 是**仅提示词**的窄修复、schema 仍为 `/4`；那套 schema-v6 工作顺延为 v3.20。

- **`temperature: 0` 没能带来确定性，而且移动了输出分布。**追加该字段后，同一提示词
  两次运行的 `model-claim.json` **语义仍不同**（`dimensions`/`summary`、
  `ambiguities`/`statements`、`intent_id`/`impact_ids`/`assumptions` 均异）。且
  `gte_fok_dust` 由改动前的 2/2 通过变为 1/3 —— 它不是中性的"收紧采样"。
  唯一改善：失败模式稳定了（两次 probe 在同一处以同一 `ValueError` 失败）。
- **盲测三采样分布（5 例 × 3 次，45 次调用，114739 prompt / 32829 completion tokens）**：
  `intuition_pause_escrow` 2/3、`panoptic_builder_init` 1/3、`gte_fok_dust` 1/3、
  `sequence_domain_fork` 0/3、`olas_permissionless_sweep` 0/3。合计 **4/15 = 26.7%**，
  **没有任何案例 3/3 通过**。
  失败原因：`fixed relation template mismatch` 5 次（**抖动型**：同一案例有时过有时不过）、
  `core relation observables lack intent/impact grounding` 3 次、`invalid truth binding`
  3 次（后两者在各自案例上 3/3 一致 → **系统性**，不是运气）。
  结论：单次运行的通过/拒绝不是关于报告的属性，而是一次抽样的属性。
- 结构按前提恢复：规范化并入 `lib/semantic_core.py`（`lib/` 回到 8 个文件），其测试并入
  `tests/test_semantic_core.py`（`tests/` 回到 32 个文件）；`lib/normalization.py` 与
  `tests/test_normalization_boundary.py` 已删除。
- 重设 `code_sha256`：`semantic_core.py` + `report_only.py`，14 个 key。
- **新增规范化边界（在 `lib/semantic_core.py` 内）。**lib 层原本从 **228 个判废点**中止一轮
  运行（`require(...)` 加直接 `raise`），而且**一个都没被分类** —— 那不是边界，是雷区：
  任何一处形状失误都会静默丢掉一轮本来正确的结果。gold-v1 盲测里
  `intuition_pause_escrow` 就死于 `invalid report-readiness fields`，而它四个筛查维度
  全部存在、判断正确、证据 ID 真实。
- 判据：**规范化只能改"怎么写下来"，不能改"声称了什么"。**
  三分法 `NORMALIZE`（机械修正，语义断言不变）／`WARN`（不改编声称，只改编我们有多确信）／
  `REJECT`（修正会改变 P/I/V 对报告的声称）。
  `WARN` 目前**按设计为空**：这些校验器只检查**声明格式**是否合法，格式错误仍应
  `reject`；"已声明的未确定性不否决断言"那层语义在 `compile_bundle` 的 `signals`
  策略里（S12），两层不可混。
- 边界表 `BOUNDARY` 逐条列出全部 **210 条**不同消息（2 `NORMALIZE` / 208 `REJECT`）。
  `tests/test_semantic_core.py` 用 `ast` 从源码重新导出判废面，任何未登记的
  消息都会让测试失败 —— 边界因此无法静默漂移。防护用 `exact_entry_for`（精确匹配），
  而不是 `entry_for`（带前缀兜底）：前缀兜底会让一条被截短的条目继续"覆盖"它本该声明
  的消息，从而悄悄丢掉一个点。
- 首个落地修复器 `normalize_readiness()`：把模型嵌套错一层的 `missing_dimensions`/
  `summary` 上提。**在真实失败产物上端到端验证**：修复前 `ValueError: invalid
  report-readiness fields` → 修复后 `decision = ready`。它是纯函数（不修改输入），
  原始响应保持可审计，改正内容写进 `neural-input-screen/normalization-log.json` 与
  `provenance.input_screening_normalizations`。
- 归责结论（离线重放，零 API 调用）：
  - `sequence_domain_fork` → **`reject` 正确**。其第 3 条 P term 的符号
    `new_chain_signature_valid` 的 `source_ids` 是 impact + intent，没有任何前置条件支撑
    —— 即模型把自己的坏结果当成了前提。这正是 `HANDOFF.md` §6.4 记录的缺陷。
  - `panoptic_builder_init` / `olas_permissionless_sweep` → 归 `reject`：impact 只支撑
    条件侧，关系侧由 intent 支撑，等于把"声称的对象"换了。
- 测试基线 276 -> 286（+8 边界覆盖/修复器测试，+2 接线与纯函数）。两条关键防护均负向
  验证：新增未分类判废点、删条目、截短条目文字，三者都以预期断言失败。
- 已知覆盖缺口（与 `cli/batch_verify.py` 同类）：(该边界决定一轮是否
  中止)，但它**不在**任何清单的 `code_sha256` 里 —— 清单只记历史遗留的 11 个名字。
- 重设 `code_sha256`：`semantic_pipeline.py`，7 个 key。
- **新增 `--deepseek-proxy` 开关，神经流程默认直连。**官方传输此前**隐式**继承
  环境里的 `*_proxy` 变量（`build_opener` 会自动装 `ProxyHandler(getproxies())`）。
  当 `HTTPS_PROXY` 指向一个不响应 HTTP CONNECT 的端口时，urllib 把请求交给它并立刻
  被掐断，而失败信息只有 `DeepSeek network failure; details not saved` —— 完全看不出
  是代理造成的，所有真实调用都会失败。
  - `lib/report_only.py`：`extract_deepseek(..., proxy=...)`，取值 `environment`
    （历史行为）／`direct`（忽略环境变量）／一个 `http(s)://` URL。`direct` 通过传入
    空的 `ProxyHandler` 实现 —— 它既注册"无代理"，又阻止 `build_opener` 装上默认的
    读环境变量那个。`socks5://` 会被**前置拒绝**并给出明确原因（urllib 不支持 SOCKS），
    而不是留到运行期变成一个神秘的网络错误。
  - `cli/semantic_pipeline.py`：`--deepseek-proxy`；用 `functools.partial` 绑定，
    保持三处调用点的位置参数元数不变。
  - `main.py`：`STAGE2_PROXY_DEFAULTS` 为 `run`／`batch` 注入 `direct`（独立函数，
    与 `_with_deepseek_defaults` 分开，理由同 S12）。该标志仅对 `--provider deepseek`
    生效，`opencode` 路径保持不变。
  - `cli/batch_verify.py` 转发给每个子进程。
- 失败可诊断：`model-runtime-diagnostic.json` 与 `model-usage.json` 新增
  `proxy_in_effect`（**脱敏**，只记 `scheme://host:port`，绝不写代理 URL 里的凭据）；
  `provenance.json` 新增 `deepseek_proxy_policy` 与 `deepseek_proxy_endpoint`。
- 实测 A/B（同一个 shell，`HTTPS_PROXY=http://127.0.0.1:7897` 仍在）：
  `--deepseek-proxy environment` → `DeepSeek network failure`；
  默认（注入 `direct`）→ `candidate_checks_passed`，3 次真实调用成功。
- 6 条新测试 + 1 条接线测试（`test_pipeline_binds_the_proxy_policy_through_to_the_transport`），
  两条关键防护都做了负向验证。测试基线 269 -> 276。
- 重设 `code_sha256`：`report_only.py` + `semantic_pipeline.py`，14 个 key。
- **DeepSeek 注入改为仅神经流程，修掉"离线 `run` 必然失败"。**`main.py` 原先
  无条件为 `run` 注入 `--provider deepseek`，于是纯离线 run（给 `--elements` /
  `--formalization`）撞上 `--provider deepseek requires neural extraction or
  formalization`，每次都以退出码 2 失败，必须显式补 `--provider opencode` 才能跑。
  现在 `run` 只在带 `--extract` 或 `--formalize-only` 时注入；`batch` 恒为神经
  流程，注入不变。条件表是新增的 `STAGE2_NEURAL_ONLY_DEFAULTS`，
  `STAGE2_DEEPSEEK_DEFAULTS` 仍是静态防护测试的唯一来源（`run` 保留在其中）。
- 测试基线 268 -> 269。
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
