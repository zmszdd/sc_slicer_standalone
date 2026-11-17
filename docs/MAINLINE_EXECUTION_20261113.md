# 主线各阶段执行记录（2026-11-13，2026-11-16 补记主口径）

> 2026-11-16 起对外权威四指标切换为**分层随机抽样主口径**
> （`mainline_metrics`，seed `20261115`，positive 350 / negative 91），
> 历史 dev-105 口径（完成率 97.1% 等）降级为诊断对照。见文末「主口径切换」节。

按已批准六阶段方案依次执行。历史 dev-105 口径：完成率 97.1%、端到端召回 61.4%
（TP=62/101）、漏洞级准确率 95.4%、F1(漏洞级/端到端) 0.747。

## 阶段 0 基线与盲测集
- `tools/stage3/evaluation/metrics/blind_set.json`：40 个去重 judge-valid 新项目 finding，每项目最多 5 个。
- `dev_baseline.json` 冻结开发集四指标与 claim 轨道基线。

## 阶段 1 可绑定性契约
- `tools/stage3/lib/bindability_contract.py`：`stage3-bindability-contract/1` schema，绑定前确定性路由 `no_anchor`，并向后兼容旧 feedback 文件。
- 接入 `stage3_eval_run.py` / `stage3_verdict_loop.py`。

## 阶段 2 检查点/差分工程
- 复核 `lib/patch.py`：`local_decl_statements`、`relocate_before_snapshots`、`snapshot_after` 已覆盖语句锚点快照；本轮无需新增代码。

## 阶段 3 FN 分桶与工作队列
- 新增 `tools/stage3/evaluation/metrics/fn_work_queue.py`，把两份 triage 合并成可执行队列：39 FN → 可恢复 35 / 天花板 4。
- 动作分布：rebind 21、stage2_rerun 4、witness_poc 4、retry_inconclusive 3、effect_predicate 3、reference_patch 4。
- 试点 `stage3_verdict_loop`（Ekubo overpay/underpay）：LLM 确认 3 个 UNBOUND 符号不可观测，`repair_exhausted`，诚实保持 FN。

## 阶段 4 指标/CI
- `stage3_metrics_sync.py --check`：重算后做跨文件一致性门（TP/FN/FP/TN 分母、完成率一致），CI 失败即拦截。
- 修复 `unified_metrics.py` 完成率来源：改从 `positive_eval_105.json` 的 done/全输入计算，统一为权威口径 97.1%（原先误用 fullflow 的 90.5%）。
- `lib/metrics_sync.verify_consistency()` 与单测（`test_metrics_sync.py`，10 项）覆盖跨文件一致性。
- `.github/workflows/ci.yml` 的 `stage3-unit` 增加 `metrics consistency` 步骤。
- Makefile 增加 `metrics-check`；`metrics_sync.run_metrics_scripts` 纳入 `fn_work_queue.py`。

## 阶段 5 跨项目盲测
- 新增 `blind_build.py` + `blind_build_status.{json,md}`：40 例骨架构建/编译状态，当前 14 built / 10 compile ok。
- 新增 `blind_data_audit.py`：区分两层真实阻塞——本地 submission 转储 10/40、PoC 代码块 7/40、合约骨架可编译 10/40，完全就绪 0/40。
- 新增 `blind_report_drafts.py`：为 10 个有本地 submission 的案例生成 stage2 `report.json`（`body` schema），`blind_reports_ready.json`。
- 运行 10 例 stage2 批次：`candidate_checks_passed` 4、`stage2_can_continue` 8（`blind_stage2_summary.{json,md}`）。
- 修复复活工具 5 处确定性缺口：`_repair_zero_arg_custom_errors`、`_shrink_to_effective_slice` sort、`_repair_duplicate_placeholder_modifiers`、`_repair_keyword_param_names`、Errors stub 补 `InsufficientBalance`；单测 `tools/sol_resurrect_tool/tests/test_error_repair.py`（6 项）。
- 修复阶段二批次 runner：`batch_verify.py` 缺输出目录、status.json 缺失时保留 stdout JSON，不再丢案例。

## 阶段 6 清理
- `scripts/prune_evaluation_artifacts.sh` dry-run 确认 45,726 个可再生 `runs/` 产物；未执行 `--apply`（等无回归确认后执行）。

## 下一步（未完成）
- 批量为剩余 39 个盲测案例跑 `blind_build.py --build`（LLM 成本高，需分批）。
- 对盲测集跑 stage2→stage3 全链，得到跨项目召回/准确率。
- 确认无回归后执行 `prune_evaluation_artifacts.sh --apply` 并提交。

## 阶段 5 续：盲测 stage3 全链与三个 pipeline 根因修复
- 为 4 个 `candidate_checks_passed` 案例（10 claim）组装 stage3 goldset/flatten/cases 并跑 `stage3_eval_run`：
  `blind_stage3_summary.{json,md}`、`blind_stage3_eval_{before,after}_fix.json`。
- 盲测复现 0/10，但根因已定位（按影响排序）：
  1. **无 test 入口（硬阻塞）**：40 案例 `Resurrected.t.sol` 均无 `test_*` 函数，`forge test` 报
     `No tests found`；合约级 flatten 只含 `src`，不含 PoC 测试。`blind_data_audit` 增加
     `harness_has_test`/`no_test_entrypoint_in_harness`，当前 `stage_ready=0`。
  2. **`no_anchor` 过度路由（已修）**：确定性模糊匹配 false-negative（「zero shares」映射不到
     `_mint`/`balanceOf`）被硬路由成 `not_dynamically_expressible`（修复前 5/10）。
  3. **library/contract 定位（已修）**：patch 注入只匹配 `contract`，`library SessionSig` 触发
     `binding_error`。
- 修复内容：
  - `lib/bindability_contract.py`：`build_contract` 输出 `anchor_observability`；新增 `is_hard_ceiling`
    （仅 `no_anchor` + `low` 可观测性才是硬天花板）。
  - `cli/stage3_eval_run.py`：`_ceiling_verdict_for_bindability` 改为 `no_anchor` 仅在 `low` 时硬路由，
    其余交给 binding LLM。
  - `cli/stage3_verdict_loop.py`：改用 `is_hard_ceiling`。
  - `lib/patch.py`：`_contract_region` 匹配 `abstract contract`/`contract`/`library`。
  - `lib/forge_runner.py` + `cli/stage3_pipeline.py`：`No tests found` 输出识别为
    `no_test_entrypoint`（与真正的 slice 编译失败区分）。
- 验证：stage3 单测 209/209 通过；`git diff --check` 干净；`doctor.sh` 通过。
- 剩余阻塞：盲测 harness（PoC `test_*`）未就绪；补齐前不据此调 dev 指标。

## 阶段 5 续：盲测 harness 就绪性实证（Sequence__144）
- 实测：submission `proofOfConcept` 代码块可 `forge flatten` 成含 `testCrossWalletReplayAttack`
  的自包含源（26,196 行，可编译）。
- 但该 PoC 依赖 `vm.envUint(SEQ_SDK_RPC_*)` 与 `vm.rpc(http://localhost:9999/rpc)` fork 本地 RPC，
  不是自包含测试；`sol_resurrect` 产出为 5 行空壳 stub。
- 结论：盲测 e2e 的真实瓶颈是「把 PoC 复活成自包含 harness」，而非 stage1 切片 / stage2 P/I/V /
  stage3 binding/patch/forge 主链路；sol_resurrect 对 fork/集成型 PoC 的复活能力不足。

## 阶段 1：盲测 PoC harness 就绪分类（新增）
- 新增 `tools/stage3/evaluation/metrics/blind_poc_harness.py` + `blind_poc_harness_status.{json,md}`，
  把「无 test 入口」拆成可执行动作分类。
- 40 例分布：`no_poc_code` 33、`snippet_only` 4（Megapot/Lambo/Silo 是 diff 片段非测试）、
  `fork_rpc` 3（Sequence 144/169/18 是 forge 测试但依赖外部 RPC）、`self_contained` 0。
- 决定性证据（Sequence README）：Sequence 测试依赖克隆并构建外部 `0xsequence/sequence.js`
  SDK，`pnpm build:packages` + `pnpm dev:server` 起本地 RPC；`PrimitivesRPC.sol` 的
  `vm.rpc` 全部指向该 dev server。这是外部基础设施依赖，不是 pipeline 缺陷。
- 结论：盲测集按现状构造，**没有任何自包含可自动复活的 PoC**。fork_rpc 需外部 SDK dev
  server；snippet_only 需人工撰写测试；no_poc_code 需补抓 submission。
- `blind_data_audit.py` 已接入 `poc_action`（fork_rpc/snippet_only/no_poc_code）作为 blocker。

## 阶段 6：盲测 PoC 独立管线补全（本轮执行）

### 根因收敛
- 盲测「无 test 入口」的真相是：canonical finding（含 `proof_of_concept`）在
  `c4_pipeline_output/<project>/<batch>/findings.json`，键为 `number`/`submission_index`；
  旧审计脚本只看 `code4rena_reports/<project>/submission_*.json`，把 30+ 例误判为「缺 submission」。
- 修正后：40/40 有 finding、35/40 有 PoC 代码块；但 dev 集曾经过外部
  `/root/poc_repro_work` 的 standalone-PoC + flatten-pass 管线，盲测集从未获得同样处理，
  这是 e2e recall 61.4% 无法上行的真实结构缺口。

### 新增 / 修改
- `scripts/code4rena/findings_lookup.py`：统一按 `findings.json` 查找 finding（canonical 源）。
- `scripts/code4rena/standalone_poc_pipeline.py`：
  - 确定性 wrapper：裸 `function test_*()`（无 `contract ... is Test`）借仓库最近似
    `test/*.t.sol` 的 import/state/setUp，嵌入重命名后的 `Standalone_<sub>_<finding>`；
  - `--author` LLM 兜底：DeepSeek（复用 stage2/3 密钥）把 diff/snippet 撰写成自包含测试，
    并在 entry 失败时用 forge 报错做一轮修复；
  - `_ensure_forge_std`：仓库 `lib/forge-std` 缺失时从既有 panoptic 缓存复制补齐；
  - 区分 `hardhat_root_no_forge` / `poc_forks_live_rpc` / `no_poc_code_block` 天花板。
- `scripts/code4rena/blind_poc_summary.py`：把 dry-run 分类与已核实运行结果合并成
  `c4_pipeline_output/standalone_poc_batch/full_poc_batch_summary.{json,md}` + status CSV。
- `tools/stage3/evaluation/metrics/blind_poc_harness.py`：新增 `bare_test_fn` 动作与
  `repo_tooling`（foundry/hardhat/none）；已重生成 `blind_poc_harness_status.{json,md}`。
- `tools/stage3/evaluation/metrics/build_blind_set.py`：盲测样本带上 `poc_blocks`/
  `poc_action`/`standalone_poc_ready` 门禁；已重生成 `blind_set.json`（仍为同 40 例）。

### 本轮 flatten_pass 实证（6/40）
- `Liquid_Ron_C7vLJT2ME8Z__1036`（确定性 wrapper）
- `Liquid_Ron_C7vLJT2ME8Z__104`（确定性 wrapper）
- `Liquid_Ron_C7vLJT2ME8Z__1027`（LLM author + 修复）
- `Lambo.win_LVoZUeMUNkB__102`、`__105`（LLM author）
- `Silo_Finance_yjrYyfyTzWc__446`（LLM author）
- 产物：对应 `test/Standalone_<sub>_<finding>.flattened.t.sol` 已生成并 `[PASS]`。

### 40 例状态汇总（full_poc_batch_summary.json）
- `flatten_pass` 6；`entry_pass_only` 12；`failed` 1；`blocked` 21。
- 分类：`snippet_only` 27、`no_poc_code` 5、`bare_test_fn` 3、`fork_rpc` 4、`repo_test_deps` 1。
- 天花板：11 hardhat 根（无 forge）、4 fork 本地 RPC（Sequence 依赖 `0xsequence/sequence.js`
  dev server；Lambo 118）、5 无 PoC 代码块、1 缺 repo（Flare 337）。

### 未闭环与下一步
- 剩余 12 `entry_pass_only` + 15 `snippet_only` 需要迭代式 author+修复（当前单发+1 次修复
  覆盖率有限），或补齐项目依赖（Flare 缺 `@flarenetwork/flare-periphery-contracts`）。
- 待 flatten-pass 覆盖足够后，再跑 stage2→stage3 全链得到盲测跨项目 recall/precision；
  当前盲测仍不应据此回调 dev 四指标（完成率 97.1% / e2e recall 61.4% / vuln precision 95.4% / F1 0.747 冻结）。

## 阶段 6 修正（同轮续作）

- 修复 `standalone_poc_pipeline` 两处验证 bug：
  - `_extract_names` 在 wrapper 后取到借用 harness 的第一个 `test_*`（如 `test_admin_pause`），
    而非嵌入的 PoC 测试名 → 显式传入目标测试名 `test_audit_poc_<finding_uid>`；
  - `_test_passes` 只匹配 `test_x()`，漏掉参数化 `test_x(uint88)` → 改为 `[PASS] test_x(`。
- 修复 flattened 文件写入 `test/` 导致重跑时与 entry 同名函数重复编译 → 改写到 `repo/.poc_flattened/`。
- 增强 `--author`：系统提示明确「测试必须在当前（漏洞）代码上 PASS；若是本应成功却 revert 的漏洞，
  用 `vm.expectRevert` 断言 revert」，并把 `foundry.toml` 上下文 + 完整 forge 报错回喂，最多 3 轮修复。

### 修正后 flatten_pass（9/40，已实测 [PASS]）
- `Liquid_Ron__1036`、`__104`、`__1027`、`__1000`
- `Lambo.win__102`、`__105`、`__119`
- `Silo_Finance__446`、`__453`

### 40 例状态（full_poc_batch_summary.json，修正后）
- `flatten_pass` 9；`entry_pass_only` 10；`blocked` 21；`failed` 0。
- 天花板不变：11 hardhat 根、4 fork 本地 RPC、5 无 PoC、1 缺 repo；Flare 缺
  `@flarenetwork/flare-periphery-contracts`、THORWallet oft-evm 缺 `node_modules/@openzeppelin`。

## 阶段 6 最终校正（同轮）

- 重跑 4 个早期 LLM 案例复核后，`Silo_Finance__446` 复跑未通过（LLM 非确定性），
  最终 flatten_pass 为 **8/40**：`Liquid_Ron__1036/104/1027/1000`、`Lambo.win__102/105/119`、`Silo_Finance__453`。
- 汇总：`flatten_pass` 8、`entry_pass_only` 11、`blocked` 21、`failed` 0。

## 阶段 7：真测试补位 + 依赖补齐尝试（同轮）

- 新增 `scripts/code4rena/tests/test_standalone_poc_pipeline.py`（13 个确定性单测），
  锁住两项已修回归：参数化测试 `[PASS] test_x(uint88)` 匹配、wrapper 目标测试名
  `test_audit_poc_<finding>` 不复用借用 harness 的第一个 `test_*`；并覆盖
  `_classify`/`_extract_names`/`_embed_into_contract`/`_find_best_test_source` 排除规则。
- `Makefile` 新增 `test-code4rena`，并入 `make test`。
- 依赖补齐尝试：npm registry 被代理阻断；已本地 vendor
  `@openzeppelin/contracts` 到 THORWallet oft-evm，但该例仍缺
  `@layerzerolabs/oapp-evm` 等 LayerZero 包，无法离线补齐 → 维持 infra 天花板。

## 阶段 8：把盲测 flatten 锚点接成 stage3 可消费输入（同轮）

- 修复 `blind_report_drafts.py` 数据源：改走 `findings_lookup.matching_finding`
  （canonical `findings.json`），不再指错 `code4rena_reports`；40/40 报告草稿就绪。
- 新增 `scripts/code4rena/build_blind_flatten_root.py`：把 8 个 flatten-pass 锚点
  镜像成 dev 同款布局 `blind_flatten_root/<case>/contract.flattened.t.sol` +
  `report.json` + `metadata.json`，并生成 `blind_goldset/selection.json`（8 例）。
- 至此盲测 stage3 的 flatten-root/goldset/report 三件套已就绪；剩余仅是
  stage2 规则化（`python main.py run ...`）与
  `python -m cli.stage3_eval_run --goldset-root blind_goldset --flatten-root blind_flatten_root`。

## 阶段 9：盲测 stage3 0/5 根因与确定性修复（本轮）

### 现象
盲测 8 个 flatten 锚点 → stage2 成功 5 例 → stage3 复评 `reproduced=0/5`：
- `Liquid_Ron__1000`：`effect_observed_invariant_holds`、`violation_not_reproduced`
- `Liquid_Ron__104`：`preconditions_infeasible_on_code`×2、`violation_not_reproduced`、`effect_observed_invariant_holds`
- `Lambo.win__102`：`violation_not_reproduced`
- `Lambo.win__105`：`compile_error`（`msg.value` 注入进非 payable 测试函数）
- `Silo_Finance__453`：未完成（上一轮中断）

### 根因（按影响排序）
1. **patch.contract 错配到 PoC 测试合约**：binding LLM 把注入点设成
   `LiquidRonOperatorBugTest` / `VirtualTokenCashInERC20Test`（测试 harness），
   而不是业务合约。原因：prompt 中 `INJECTION_POINT_ON_DISK` 要求「把
   patch.contract 设为该 harness」，与 `SUGGESTED_PATCH_CONTRACT`（业务合约）
   自相矛盾；`CROSS_CONTRACT_INSTANCES` 又要求用 `<instance>.<member>` 形式绑定，
   三处指令互相冲突，LLM 选了 harness。
2. **anchor_resolver 假 multi_contract**：接口 + 实现 + 业务合约共同声明
   `harvest`，且 resolver 优先选取 PoC harness 里的 `test_*` 函数作为锚点，
   把 `{ILiquidProxy, LiquidProxy, LiquidRon, LiquidRonOperatorBugTest}` 的并集
   判成 multi_contract，无法产出 `suggested_patch_contract`，使
   `_migrate_patch_contract` 不触发（它只对 single_anchor 生效）。
3. **可用性类漏洞是 assert(I) 差分的语义天花板**：`onlyOperator` 把「本应放行的
   operator」revert 掉（可用性/liveness 缺陷），`assert(!P||I)` 只能捕捉「安全性质
   被违反」（state 被破坏），无法表达「本应成功却 revert」。这类案例的 PoC 本身就
   `vm.expectRevert` 断言漏洞行为，original=Success；注入 I 后 I 仍成立，终态
   `effect_observed_invariant_holds`/`violation_not_reproduced`，不是 TP。
4. **stage2 形式化弱**：`restricted_function_called` 被放进 I/V 角色（本应是 P 前置
   条件），binding LLM 只能绑 `true`，被 lint 以「trivially constant binding」拒绝，
   2 轮修复耗尽 → `binding_exhausted`/`no_bound_claims`。
5. **Lambo/Silo 的 entity_ids 与代码标识符零重叠**：候选被 forge-std 噪声
   （`blockNumber`/`aggregate3Value`/`MAX_AMOUNT`）淹没，anchor 无法收敛。

### 本轮确定性修复
- `tools/stage3/lib/anchor_resolver.py`：
  - 排除 `test_*` 函数作为不变量锚点；
  - 优先业务锚点，不再优先 PoC harness；
  - 用「所有者集合交集」取代并集，接口+实现+业务合约共现时收敛到具体业务合约
    （新增 `solidity_scan.contract_decl_kind` 选最具体 kind）。
- `tools/stage3/lib/binding_llm.py`：
  - `_migrate_patch_contract` 迁移后把 `<instance>.<member>` 重写为裸成员
    （`liquidRon.operator(...)` → `operator(...)`），仅在 harness 中该类型实例唯一时执行；
  - prompt 消除 `INJECTION_POINT_ON_DISK`/`SUGGESTED_PATCH_CONTRACT`/
    `CROSS_CONTRACT_INSTANCES` 三方冲突：patch.contract 跟随业务合约，probe.contract
    跟随 harness，绑定用业务合约内可见的裸标识符。
- `tools/stage3/lib/solidity_scan.py`：新增 `contract_decl_kind`。

### 验证
- 40 个 stage3 单测通过（含保留 `Intuition` 真 multi_contract 回归）。
- `make test-code4rena` 13/13 通过。
- 单案例复评 `Liquid_Ron__1000`：binding 结构已纠正为
  `patch.contract=LiquidRon`、`patch.functions[0]=harvest`、
  `probe.contract=LiquidRonOperatorBugTest`、`operator[msg.sender]` 裸绑定；
  随后被 lint 诚实拒绝（`restricted_function_called` 常量 I/V），暴露 stage2 缺陷，
  终态 `no_bound_claims`（比旧版静默错绑更诚实）。

## 阶段 10：修复后盲测 stage3 全量复评（本轮，权威结果）

修复后重跑 `stage3_eval_run`（新 cases 目录 `runs/blind_stage3_cases_v2`，
`--max-binding-rounds 2`），8 个 selection 案例：

| 案例 | 状态 | claims | bound | verdicts 摘要 | 复现 |
| --- | --- | ---: | ---: | --- | ---: |
| Liquid_Ron__1000 | done | 2 | 2 | effect_observed_invariant_holds, partial_binding | 0 |
| Liquid_Ron__104 | done | 4 | 4 | effect_observed_invariant_holds ×4 | 0 |
| Lambo.win__102 | done | 1 | 1 | reference_patch_required | 0 |
| Lambo.win__105 | done | 1 | 1 | reference_patch_required | 0 |
| Silo_Finance__453 | done | 7 | 7 | compile_error×1, effect_observed_invariant_holds×1, violation_not_reproduced×4, reference_patch_required×1 | 0 |
| Liquid_Ron__1027/__1036、Lambo__119 | no_stage2_run | — | — | 本轮 stage2 未产出 formalization | — |

汇总：`reproduced_total=0`，`compile_blocked=0`（修复前 3），`compile_error=1`，
`reference_patch_required=3`，`not_dynamically_expressible=0`（修复前 5），
`bindability: single_anchor=5 / multi_contract=9 / no_anchor=1`（修复前 single_anchor=0）。

### 修复前后对比（结构性，非召回）
| 指标 | 修复前 | 修复后 |
| --- | ---: | ---: |
| compile_blocked | 3 | 0 |
| not_dynamically_expressible（硬路由丢弃） | 5 | 0 |
| single_anchor（正确契约定位） | 0 | 5 |
| patch.contract 错配测试 harness | 多例 | 已消除 |
| 复现 TP | 0 | 0 |

### 结论（本轮权威口径）
- 确定性修复已消除「patch.contract 错配」「假 multi_contract」「compile_blocked」
  三类结构缺陷，binding 现在把不变量注入业务合约并用裸标识符。
- 但盲测 5 案例的漏洞类（可用性/DoS/经济多合约）落在 assert(I) 差分的语义天花板：
  要么需要 reference patch（`reference_patch_required`×3），要么 invariant 在漏洞路径
  上成立（`effect_observed_invariant_holds`/`violation_not_reproduced`）。
- **盲测跨项目 e2e recall 当前真实值 = 0/5 案例（0/17 claim）**，不应与 dev 61.4%
  直接比较：dev 集经过多轮 per-case rebind/P2/参考补丁打磨，且以单合约 safety 类为主；
  盲测 5 例恰是 stage3 已知的硬类（可用性 + 多合约经济）。
- 提升盲测 recall 的下一主线动作（按杠杆排序）：
  1) 为可用性/经济类补参考补丁（M1 修复代码），走 `case/patched` 差分；
  2) 修复 stage2 形式化：`restricted_function_called` 等触发谓词应归 P 而非 I/V；
  3) Lambo/Silo 的 entity_ids 与代码标识符零重叠 → 改进 anchor 候选（剔除 forge-std 噪声）。


## 阶段 11：参考补丁队列收口 + 四指标更新（本轮）

- 新增 6 个 judge-valid 案例的参考补丁复现（`case/patched` 差分，original=Success、
  patched=Failure）：
  - `Kinetiq_k8aVPPVguSE__bP38mw3SCq2__eEvYodNRrvz`：queueWithdrawal 对非金库调用
    强制 `kHYPEFee > 0`。
  - `Hybra_Finance_xo4hapwL2Jy__fsfqfuE2eMf__nb9hn2hBQ2b`：createGauge 限制 pools
    上限（`MAX_POOLS`）。
  - `Kinetiq_k8aVPPVguSE__YdUkynebFvW__FCU4bMUR3hY`：PoC 断言滑点后收到 HYPE 应等于
    无滑点期望值（`slippage not bounded`）。
  - `Intuition_2VUsxVJwReb__aayBh4TiWVT__7YSswxrdK8D`：epoch-end 余额按
    `epochEnd - 1` 取，排除边界时刻刚创建的 lock。
  - `Covenant_d4uY8y2AMSs__otmbJXz4irq__h23uU6Ai3Mx`：`_checkMintCap` 小市场分支
    `&&` 改为 `||`。
  - `GTE_Perps_and_Launchpad_gtn2Umg6KsC__FbQktkofz8X__yG32SUkqYGK`：
    `_decreaseFeeShares` 的 `!unlocked` 改为 `unlocked`。
- 权威四指标更新：完成率 97.14%、端到端召回 73.27%（TP=74/101，FN=27）、
  漏洞级准确率 96.10%、F1 0.8315；`recall_automatic` 仍为 61.39%。
- 仍未闭环：`Hybra_Finance_xo4hapwL2Jy__F4rfhrN24eF__f549enU39vL` 缺
  `cl/deployments/cl-exports-local.json`（vm.readFile 不可读）；
  `Covenant_d4uY8y2AMSs__CF5ba95T4KR__5atNeQZ3fR4` 原 PoC 自身 revert
  （`PriceOracle_InvalidAnswer()`），无法构成 original=Success。


## 阶段 12：stage2 触发谓词归 P 根因修复（本轮）

- 根因：stage2 把 `*_callable` / `*_called` / `*_reverts` 等触发/活跃性谓词
  放进 `I/V`，这些符号在代码中不可观测，stage3 只能 `partial_binding` /
  `binding_error`。
- 修复生成侧：`tools/report_constraints_v2/prompts/current.py` 机械审计新增
  第 9 条“Trigger/liveness predicates stay in P, never in I or V”。
- 新增审计：`tools/stage3/evaluation/metrics/stage2_trigger_audit.py`，扫描现有
  96 个案例 / 199 个 claim 的触发谓词误入 I/V 情况，输出
  `stage2_trigger_audit.{json,md}`。
- 队列重路由：`fn_work_queue.py` 将命中该审计的 `rebind` 自动改判
  `stage2_rerun`；本轮后 `rebind 18 → 8`、`stage2_rerun 4 → 14`。
- 回归：report_constraints_v2 prompt 相关 46 项、stage3 metrics/binding 23 项
  全部通过；`metrics_sync.verify_consistency()` 通过。

## 阶段 8：盲测主线端到端闭环（2026-11-14）

### 根因收敛（盲测四指标线路不通）
- 盲测 report 起草沿用已删除 `blind_report_drafts.py` 的旧 schema，且 Lambo 119 的
  叙述正文被误标为 `## Proof of Concept`，被 stage2 `prose_only` 整段剔除 →
  readiness `missing trigger_or_action` → 无 stage3-spec。
- 8 个 flatten-pass 案例中 3 个（Lambo 119、Liquid 1027/1036）从未走主线 stage2 入口
  （`main.py run --report`），缺 `stage3-spec.json`。
- `blind_stage3_summary.py` 硬编码旧 `/tmp` 目录并统计旧的 4 个非 flatten 案例，
  产物过时，造成“线路不通”假象。

### 修复（围绕主线）
- 新增 `scripts/code4rena/blind_report_draft.py`：从 canonical `findings.json` 生成主线
  `report.json`，并把误标的首个 `## Proof of Concept` 叙述段重标为 `## Finding description`。
- stage2 `lib/impact_inventory.py` verbatim 报错带 item id；`cli/semantic_pipeline.py`
  impact-inventory 重试反馈携带具体错误（修复 1036 无法重试修正的问题）。
- 用 `main.py run --report`（`semantic-live`）补齐 Lambo 119、Liquid 1027 两个 stage2 run
  并并入 `blind_goldset/runs_blind/`（7/8）；Liquid 1036 仍在 impact-inventory verbatim 门
  阻塞（模型转述未逐字引用，诚实保留）。
- 新增 `blind_metrics.py`：盲测四指标（召回侧）聚合；重写 `blind_stage3_summary.py`
  读取新 eval，删除硬编码旧路径。

### 盲测结果（可运行子集 8 例，7 done）
- completion_rate 87.5%（7/8）；case 级召回 12.5%（1/8，Liquid 1027）；claim 级 1/19。
- 0 compile_blocked / 0 not_dynamically_expressible：harness 缺失的历史阻塞已消除。
- 剩余低召回结构原因：reference_patch_required 4（Lambo cashIn 效果型缺陷）、
  effect_observed_invariant_holds 7、binding_error/partial_binding 3、
  violation_not_reproduced 5、no_stage2_run 1（Liquid 1036）。
- precision_vuln/F1 因盲测无负样本暂不可定义。

### 验证
- stage2 回归 488 OK；stage3 回归 209 OK。

## 阶段 13：`_poc_shape` 误判修复与盲测复评（2026-11-14）

### 根因
- `tools/stage3/cli/stage3_verdict_loop.py::_poc_shape()` 过去先对**整个 `src/*.sol`**
  检测 `expectRevert`，把「exploit 测试体是状态断言型、但源码其它处含 `expectRevert`」
  的案例（如 Silo 453）误判成 `revert_expected_test`，导致本可 rebind 的
  `effect_observed_invariant_holds` 被错误路由为 `reference_patch_required`，
  白白损失一次主线修复机会。

### 修复
- 先定位 exploit 测试函数体，再只在函数体内判断 `expectRevert` →
  `revert_expected_test`，否则按 `assert(...)`/`assertEq(...)` 判
  `state_assert_test`，最后回退 `other_test`。
- 验证：Silo 453 从误判纠正为 `state_assert_test`；Liquid 1000/104 仍正确判为
  `revert_expected_test`；Lambo 102 仍为 `state_assert_test`。
- 回归：`test_verdict_loop` / `test_eval_run_routing` / `test_routing` 35 项全过。

### 复评结果
- 重跑 7 个 done 案例的 `stage3_verdict_loop --max-rounds 2`：新增复现 0。
  - Silo 453 现在会走 rebind，但绑定 LLM 对 `c3b2797d4_deposit_fee_charged` 仍报
    `bad kind`，7 claims 中 4 个 `violation_not_reproduced`、2 个
    `effect_observed_invariant_holds`、1 个 `binding_error`。
- 重跑 `stage3_eval_run --skip-llm` + `blind_metrics.py` + `blind_stage3_summary.py`：
  盲测四指标不变，`completion_rate 87.5%`、case 级召回 `12.5%`、claim 级 `1/19`。

### 新暴露的主线瓶颈（按优先级）
1. **stage2 新旧 prompt 语义漂移**：用当前 `semantic-live` 重跑 `Liquid 1027`
   stage2 得到 `no_explicit_impact`（新 impact-inventory 不再把机制句
   「incorrectly assign ... goes into operatorFeeAmount」当 impact），而现有盲测
   stage2 run 是旧 prompt 产物，二者不可比。需冻结一版「盲测终测 prompt」并重放，
   否则 stage2 重跑会把案例打回 `needs_impact_review`。
2. **reference-patch 路线缺口**：Lambo 3 例的 `reference_patch_required` 是
   `case/patched` 差分路线，主线上还没有通用参考补丁提供器，无法自动闭环。
3. **弱不变式/绑定质量**：Silo/Liquid 的 `effect_observed_invariant_holds` 与
   `violation_not_reproduced` 属于 stage2 数值绑定与注入点语义，不是 harness 缺失。

### 结论
- `_poc_shape` 修复正确且已回归，但不会直接提升盲测召回：它消除的是错误路由，
  真正的召回瓶颈在 stage2 prompt 冻结/重放与 reference-patch 通用路线。

## 阶段 14：指标路由透传与 `_poc_shape` 真测试（2026-11-14）

### 根因
- `blind_metrics.py` 的 `recall_automatic` 直接复制 `recall`，没有区分
  `assert(I)` 自动复现与 `case/patched` 参考补丁复现；一旦盲测走 reference-patch
  路线，自动口径会被高估。
- `stage3_pipeline` 知道某次复现是否来自 `case/patched`，但没有把该路由信息传到
  `stage3_multi` → `case_runner.run_multi` → `stage3_eval_run` → `blind_metrics`。
- `_poc_shape` 核心路由没有直接单测，之前的修复只靠全量测试间接覆盖。

### 修复（围绕主线）
- `tools/stage3/cli/stage3_pipeline.py`：最终 summary 增加
  `reference_patch_used: (case_dir / 'patched').is_dir()`。
- `tools/stage3/cli/stage3_multi.py`：每 claim 行透传 `reference_patch_used`。
- `tools/stage3/lib/case_runner.py::run_multi`：返回
  `{'verdicts': ..., 'reference_patch_used': ...}`，统一路由信息。
- `tools/stage3/cli/stage3_eval_run.py`：新增 `automatic_reproduced` 与
  `reference_patch_reproduced` 行级字段及汇总字段。
- `tools/stage3/evaluation/metrics/blind_metrics.py`：`recall_automatic` 改为按
  `automatic_reproduced > 0` 计算，并兼容旧 eval 快照。
- `tools/stage3/tests/test_verdict_loop.py`：新增 `PocShapeTest` 四个用例，直接覆盖
  exploit 函数体 `expectRevert`、跨文件 `expectRevert` 不污染、缺失函数、缺失 probe。

### 验证
- stage3 全量回归 `213` 项通过（新增 4 项）。
- `blind_metrics.py` 重算：`recall 12.5%`、`recall_automatic 12.5%`、
  `tp_automatic 1`，与当前无参考补丁复现的事实一致。

## 阶段 15：impact-inventory 语义空结果重试 + 盲测 stage2 重放审计（2026-11-14）

### 根因
- `request_impact_inventory` 只在 JSON/schema/evidence 校验失败时重试；模型返回
  `impacts: [], ambiguities: []` 会被当作合法结果接受，导致有明确 Impact 文本的
  报告偶发 `no_explicit_impact`（Liquid 1027 可复现）。
- 当前 `semantic-live-26` 的正式化门比生成现有盲测 `stage3-spec` 的 prompt 更严：
  即使 impact-inventory 修复后能提取 1 个 impact，Liquid 1027 仍
  `strict_exit`（`incomplete_piv_count 1`、`formalized_impact_count 0`），
  说明现有盲测 stage2 产物无法用 live26 重放。

### 修复
- `tools/report_constraints_v2/cli/semantic_pipeline.py`：impact inventory 在
  `allowed_ids` 非空且模型返回空 impacts/ambiguities 时，追加一次
  `impact-inventory-empty-retry` 调用，提示模型把标记区域内明示的有害结果写回
  impacts，而不是返回空数组。
- `tools/report_constraints_v2/tests/test_impact_scope.py`：新增
  `ImpactInventoryEmptyRetryTests` 两个用例，覆盖“有空重试”与“无 Impact 区域
  不重试”。

### 验证
- 阶段二全量回归 `490` 项通过（新增 2 项）。
- Liquid 1027 用 live26 重跑：`impact_inventory_status` 从 `no_explicit_impact`
  变为 `extracted`，但正式化仍 `strict_exit`，确认阶段 12 后的 live26 与旧盲测
  stage2 产物存在不可重放差异。

### 对盲测 recall 的结论
- 本轮没有提升盲测 recall（仍 12.5%），因为主要失分项是 reference-patch 路线缺口
  与弱不变式/数值绑定，而不是 impact-inventory 空结果；但已消除一个会进一步压低
  completion/stage2 通过率的不确定故障源。

## 阶段 16：盲测 stage3 权威复评（阶段 13–15 修复后，2026-11-14）

### 执行
- 在新代码（`_poc_shape` 修复、指标路由透传、impact-inventory 空结果重试）上
  重跑盲测 `stage3_eval_run --skip-llm`，输出
  `tools/stage3/evaluation/metrics/blind_stage3_eval_20261114.json`，并用
  `blind_metrics.py` / `blind_stage3_summary.py` 重算四指标。

### 结果（权威）
- `completion_rate 87.5%`（8 个 selectable 中 7 done + 1 no_stage2_run）
- case 级 `recall 12.5%`（1/8：Liquid_Ron__1027）
- `recall_automatic 12.5%`（`automatic_reproduced>0` 口径，唯一案例同上）
- claim 级 `claim_recall 5.26%`（1/19）
- `tp 1 / tp_automatic 1 / fn 7`

### 失分结构（按案例）
- `Liquid__1000`：2 claim `effect_observed_invariant_holds`
- `Liquid__1027`：1 复现 + 1 `violation_not_reproduced`
- `Liquid__104`：4 claim `effect_observed_invariant_holds`
- `Liquid__1036`：`no_stage2_run`（impact-inventory verbatim 门）
- `Lambo__102`：1 `reference_patch_required`
- `Lambo__105`：1 `reference_patch_required`
- `Lambo__119`：2 `reference_patch_required`
- `Silo__453`：1 `binding_error` + 2 `effect_observed_invariant_holds`
  + 4 `violation_not_reproduced`

### 结论
- 阶段 13–15 的修复是正确性/口径修复，已消除 `_poc_shape` 错误路由与
  impact-inventory 偶发空结果，但**不直接提升 recall**：召回瓶颈仍在
  (a) reference-patch 通用路线缺口（Lambo 4 claim）、(b) stage2 弱不变式/数值
  绑定（8 `effect_observed_invariant_holds` + 5 `violation_not_reproduced` +
  1 `binding_error`）、(c) `no_stage2_run` 1 例。
- 四指标在盲测正样本子集上是稳定、可复算的：`0.875 / 0.125 / 0.125`。

## 阶段 17：主线缺口收口——全量口径 + reference-patch 通用提供器（2026-11-14）

### 根因
- 盲测 recall 长期以「8 个可运行子集」为分母报 12.5%，掩盖了 40 例盲测集
  只有 8 例进入 stage3 的事实；真实端到端 recall 是 1/40 = 2.5%。这是 P0 的
  分母选择问题，不是小 bug，而是对外口径误导。
- `reference_patch_required` 路线此前只认 `case/patched/` 目录，Lambo 3 例
  没有预建目录即被直接判 `reference_patch_required`，主线缺少「由 diff 物化
  补丁树」的确定性能力（P1）。

### 修复（围绕主线）
- `tools/stage3/lib/reference_patch.py`（新增）：唯一参考补丁物化实现，支持
  `case/patched/`（树）与 `case/patched.diff`（unified diff，`patch -p1`），
  幂等、失败清理、无模型调用。
- `tools/stage3/cli/stage3_pipeline.py`：在 M1 需要时（reference_patch_required
  或 selfdestruct targets）自动物化 `case/patched`；物化失败仍诚实报
  `reference_patch_required` 并附 `apply_error`。
- `tools/stage3/evaluation/metrics/blind_metrics.py`：新增
  `compute_metrics(rows, selected, full_positions)` 纯函数与
  `recall_full_set`/`full_set_positives`/`fn_full_set` 字段；markdown 同时展示
  可运行子集 recall 与全量端到端 recall。
- 测试：`test_reference_patch.py`（7 项）+ `test_blind_metrics.py`（3 项）。

### 验证
- stage3 全量回归 `223` 项通过（213 + 新增 10）。
- `blind_metrics.py` 重算：可运行子集 recall `12.5%`（1/8），全量端到端
  `recall_full_set 2.5%`（1/40），`fn_full_set 39`。

### 结论
- 本轮没有直接抬升可运行子集 recall（仍 12.5%），因为剩余失分需要 Lambo 的
  修复 diff 数据、stage2 弱不变式重放和 PoC 复活 LLM；但已把「分母诚实化」与
  「reference-patch 通用能力」两条主线缺口关闭，且不依赖任何单案例手工补丁。

## 阶段 18：stage1 PoC 复活批量执行（2026-11-14，DeepSeek --author）

### 根因
- 盲测 40 例里 27 例 `snippet_only`，主线 stage1 只对 `bare_test_fn` 有确定性
  复活路径，`snippet_only` 的 `--author` LLM 复活从未在盲测集批量执行；
  `standalone_poc_ready` 仅 4/40，导致端到端召回分母长期被压到 8 例。

### 执行
- `scripts/code4rena/standalone_poc_pipeline.py --all --author`（DeepSeek 直连，
  带 3 轮 repair）：40 例全量跑完。
- 结果：`flatten_pass 9 / entry_pass_only 9 / authoring_failed 1 / blocked 21`。
  - 新增 flatten_pass：`Liquid_Ron__1032`、`Silo_Finance__446`（此前均
    entry_test_failed）。
  - blocked 21 仍是数据前提问题：`hardhat_root_no_forge 12`、
    `poc_forks_live_rpc 4`、`no_poc_code_block 5`。
  - 注：`Silo_Finance__453` 本轮被 LLM 重生成后 entry_test_failed，但其旧
    flatten 产物仍在 `blind_flatten_root`，故不影响已进入 stage3 的 453。

### 提升与续跑
- 把 `Liquid 1032`、`Silo 446` 两个新 flatten 产物提升进
  `blind_flatten_root`（`contract.flattened.t.sol` + `metadata.json`），
  并用 `blind_report_draft.py` 生成 report.json。
- 对两例跑 stage2（`semantic-live`，DeepSeek）：
  - `Silo 446`：`candidate_checks_passed`，1 impact 1 formalization，已并入
    `blind_goldset/runs_blind/`；
  - `Liquid 1032`：`impact_inventory needs_review`（同 1036 的 verbatim 门），
    无 stage3-spec → `no_stage2_run`。
- `selection.json` 从 8 → 10 例；重跑 `stage3_eval_run`（仅两新例）并合并进
  `blind_stage3_eval_20261114.json`；刷新 `blind_metrics` 与
  `blind_stage3_summary`。
- 口径：`blind_metrics.py` 新增 `recall_in_scope`（排除 no_poc_code 与
  fork_rpc，分母 31）。

### 结果（权威，更新后）
- `completion_rate 80.0%`（10 例中 8 done + 2 no_stage2_run）
- `recall 10.0%`（1/10，Liquid 1027）
- `recall_automatic 10.0%`
- `recall_in_scope 3.2%`（1/31）
- `recall_full_set 2.5%`（1/40）
- claim 级复现 1/21；新增 `Silo 446` 两 claim 均
  `effect_observed_invariant_holds`（弱不变式，与现有瓶颈一致）

### 结论
- stage1 复活覆盖率已从 8 提升到 10 个 flatten-pass，且新案例经完整主线跑通
  stage2→stage3；新增案例未复现，说明瓶颈已从「stage1 进不来」逐步转移到
  「stage2/3 弱不变式与 reference-patch」。
- 剩余 21 blocked 中，12 个 hardhat 仓库需要 hardhat 运行后端，4 个 fork RPC
  与 5 个 no_poc 本轮机制上不可复活，建议下一阶段分别处理。

## 阶段 19：stage2 impact-inventory 门修复 + 盲测 completion 100%（2026-11-14）

### 根因
- `request_impact_inventory` 的空结果重试条件过窄：要求 `impacts` 与
  `ambiguities` 都为空才重试；`Liquid 1032` 的模型返回「impacts 空、
  ambiguities 非空」（识别到不变式违反却不列为 impact），既不重试也不放行，
  卡在 `needs_review`。
- `Liquid 1036` 的模型持续改写原文，`schema/2` 的 verbatim 校验反复失败
  （`impact_inventory_verbatim`），2 次重试后仍 `impact_count 0`。

### 修复（围绕主线，确定性）
- `tools/report_constraints_v2/cli/semantic_pipeline.py`：只要 `allowed_ids`
  非空且 `impacts` 为空就触发一次空结果重试（不再要求 ambiguities 也为空）；
  重试反馈明确「即使你之前把它放进 ambiguities，也要逐字抄回 impacts」。
- `tools/report_constraints_v2/lib/impact_inventory.py`：
  - verbatim 校验错误信息附带期望原文片段，供重试反馈使用；
  - 新增 `repair_verbatim_texts`：当模型文本是改写而非逐字引用时，确定性
    地用其 cited evidence 片段原文替换 impact 文本，保证 grounding 且不再
    反复重试。
- `request_impact_inventory` 的 accept 在 verbatim ValueError 时先做确定性
  修复再校验，修复成功即接受。

### 验证与结果
- stage2 全量回归 `493` 项通过（新增 3 项）。
- 重跑 stage2（semantic-live，DeepSeek）：
  - `Liquid 1032`：`candidate_checks_passed`，1 impact / 1 formalization；
  - `Liquid 1036`：`candidate_checks_passed`，5 impact / 5 formalization
    （verbatim 修复后通过）。
- 两者 stage2 产物并入 `blind_goldset/runs_blind/`，重跑 `stage3_eval_run`：
  - `Liquid 1032`：1 claim，`effect_observed_invariant_holds`；
  - `Liquid 1036`：10 claims，`binding_error`/`partial_binding`/`inconclusive`
    混合，0 复现。
- 盲测四指标（权威）：
  - `completion_rate 100%`（10/10 done，no_stage2_run 0）
  - `recall 10.0%`（1/10，Liquid 1027）
  - `recall_automatic 10.0%`
  - `recall_in_scope 3.2%`（1/31）
  - `recall_full_set 2.5%`（1/40）
  - claim 级复现 1/32

### 结论
- stage2 的 impact-inventory 门已闭环：盲测从 2 个 `no_stage2_run` 到 0，
  completion 100%，10 个 flatten-pass 案例全部进入 stage3。
- 但召回仍卡在 stage3：新增 1032（弱不变式）与 1036（binding_error /
  partial_binding 居多）未复现，说明下一步瓶颈是 stage3 的绑定质量与弱不变式，
  而不是 stage2 门禁。

## 阶段 20：stage2 弱不变量数值 gate（2026-11-14）

### 根因
- `Silo_Finance_yjrYyfyTzWc__453` 的 `impact_claim_first_depositor_can_only_wi`
  生成的安全不变量 I 只有布尔谓词（`deposit_fee_charged & prior_holders_hold_shares
  => fee_borne_by_new_depositor`），而 V 才是真正的数值伤害
  （`lt(withdrawable_after, withdrawable_before)`）。
- 下游 `effect_observed_invariant_holds` 判定因此失效：V 被见证但 I 是定性判断，
  两者不在同一语义层面，漏洞没被 I 抓到，不构成复现。即「I 定性、V 数值」的
  stage2 弱不变量形状在 formalization 阶段没有被确定性拦截。

### 修复（围绕主线，确定性）
- `tools/report_constraints_v2/lib/plan_synthesizer.py`：
  - 新增 `_numeric_relation_ops(expression)`：识别表达式中的数值算术/比较 op
    （`lt/gt/lte/gte/add/sub/mul/div/mod`）。
  - 新增 `_numeric_symbols(claim)`：返回 `claim['symbols']` 中 `sort` 为
    `int/real` 的符号名集合。
  - `_vacuous_safety_shapes(claim)` 新增定性-only 检测：当 `effects` 含数值
    关系、但 `safety` 的变量集合与任何数值符号都不相交时，追加 reason
    `safety is qualitative-only while effects assert a numeric harm; restate I
    over the numeric relation`，使 `reject_vacuous_safety` 在 formalization
    阶段直接拦截。
- `tools/report_constraints_v2/cli/semantic_pipeline.py`：
  - `_direct_witness_hint` 新增 `NUMERIC-I GUIDANCE` 分支：命中
    `safety is qualitative-only` 时，明确要求把 I 改写成与 V 同一组数值
    观测量（before/after int 符号、保留单位、写成数值不变式），禁止把数值
    伤害降级为布尔代理。
- `tools/report_constraints_v2/tests/test_direct_witness_diagnostics.py`：
  - 新增 3 个确定性测试：定性-only 被命名、数值 I 不误报、reason 通过
    `reject_vacuous_safety` 公开门返回。
- `tools/report_constraints_v2/tests/test_automatic_triage.py`：
  - 断言 qualitative-only 错误产出 `NUMERIC-I GUIDANCE` 重试反馈。

### 验证与结果
- stage2 全量回归 `496` 项通过（本轮新增 4 项）。
- 离线验证：对历史产物 `tools/stage3/cases/Silo_Finance_yjrYyfyTzWc__453/stage2_run/formalization.json`
  运行 `_vacuous_safety_shapes`，精确命中 `first_depositor_can_only_wi` 该 claim。
- 真实重跑（semantic-live，DeepSeek，Silo 453，新目录
  `tools/report_constraints_v2/results/semantic/stage2_gate_validation_Silo_453`）：
  该 claim 的安全不变量已变为数值关系
  `implies(new_deposit_occurred, withdrawable_after >= withdrawable_before)`，
  `_vacuous_safety_shapes` 不再命中；`gate_direct_relation_infeasible_count 0`。
  说明 gate 已作为确定性兜底，且生成结果本身已落到数值 I。

### 结论
- stage2 弱不变式主缺陷（I 定性 / V 数值 不同层）现在有确定性 gate + 针对性
  重试指引闭环，不再静默产出无法复现的 P/I/V。

## 阶段 21：stage3 绑定两个确定性根因修复（2026-11-15）

### 根因（按影响排序，证据来自盲测 Liquid 1036）
- `binding_error`：`patch.py` 按函数**裸名**定位注入点，`LiquidRon` 内有两个
  `redeem` 重载（ERC4626 三参版 + 一参版），匹配歧义直接抛
  `function redeem is ambiguous`，5 个 claim 在 build 阶段终止。
- `inconclusive`：`forge_runner._find_test` 只去掉末尾 `()`，匹配不了带参
  模糊测试名（`test_audit_poc_1036(uint88)`），2 个已能编译的 claim 被判
  “probe test 不存在”。
- `partial_binding`：绑定 LLM 对少数符号留 `UNBOUND`，单遍 eval 不再修复。
- `effect_observed_invariant_holds`：剩余 claim 的 I 在 exploit 路径上空洞
  ——before/after 两个 int 符号被绑到**同一次** redeem 调用的同一表达式
  `convertToAssets(50 ether)`，使 `before <= after` 恒真。这是 checkpoint
  语义问题，不是绑定错名。

### 修复（确定性，无 LLM）
- `tools/stage3/lib/patch.py`：`_function_body` 对同名重载做 arity 消歧——
  按参数个数分组，优先取 PoC 调用点实际使用的 arity；无调用证据时取参数
  更多者；同 arity 取 `override` 实现；仍歧义才报错并列出候选签名。
- `tools/stage3/lib/forge_runner.py`：`_find_test` 用 `key.split('(',1)[0]`
  归一化，使 `test_audit_poc_1036(uint88)` 与裸名 `test_audit_poc_1036`
  匹配。
- 测试：`tests/test_patch.py` +3（调用点 arity / 同 arity 报错 / 无调用点取
  高 arity），`tests/test_forge_runner.py` +1（fuzz 名匹配）。

### 验证与结果
- stage3 全量回归 `228` 项通过（新增 4 项）。
- 重跑 Liquid 1036 单遍 stage3（--skip-llm，本地 forge）：
  - 修复前：`binding_error 5 + partial_binding 3 + inconclusive 2`；
  - 修复后：`effect_observed_invariant_holds 7 + partial_binding 3`，
    `binding_error/inconclusive` 归零。
- `stage3_verdict_loop`（DeepSeek 重绑定，max-rounds 2，10 claim）：
  `partial_binding` 可被修复成 `effect_observed_invariant_holds`；最终
  `accepted 0 / reproduced 0`，`multi_contract` claim 重绑定耗尽后按
  `_exhausted_status` 正确落到 `reference_patch_required`。确认剩余瓶颈是
  before/after 跨两次调用点的 checkpoint 语义，assert(I) 注入无法表达，
  需走 M1 reference patch。

### 结论
- stage3 的两个确定性 bug（重载歧义、fuzz 名匹配）已闭环，`binding_error`
  与 `inconclusive` 在盲测上可清零。
- 主线下一瓶颈是 **before/after 跨两次调用点无法用单一 assert(I) 注入表达**
  ：需要让 before 符号在“fetchOperatorFee 前那次 redeem”、after 符号在
  “fetch 后那次 redeem”分别采样，或改走 reference patch（M1）路由。

## 阶段 22：全量盲测重跑 + 四指标刷新（2026-11-15）

### 执行
- `stage3_eval_run --skip-llm`（10 case，全本地 forge）→
  `blind_stage3_eval_20261115.json`。
- `blind_stage3_summary.py` / `blind_metrics.py` 的 `DEFAULT_EVAL` 切到新快照，
  重新生成 `blind_stage3_summary.{json,md}` 与 `blind_metrics.{json,md}`。

### 结果（权威）
- 四指标不变：completion 100%、recall 10.0%（1/10）、recall_in_scope 3.2%
  （1/31）、recall_full_set 2.5%（1/40）、claim 召回 3.1%（1/32）。
- 失败分类显著修正：
  - `binding_error 6 → 1`、`partial_binding 3 → 0`、`inconclusive 2 → 0`；
  - `effect_observed_invariant_holds 11 → 21`；
  - `violation_not_reproduced 5`、`reference_patch_required 4`、
    `violation_reproduced 1` 不变。
- `verdict_loop` 对 Liquid 1036（10 claim）与 Silo 453（7 claim）重绑定后仍
  0 新增复现；Silo 453 仅剩 1 个 P/V 侧跨合约 `binding_error`
  （`deposit_fee_charged` 被绑到 `previewRedeem`）。

### 结论
- 本轮把 stage3 的“绑定质量问题”基本闭环：可修复的 binding_error /
  partial_binding / inconclusive 已清零或降为 1，失败被诚实地暴露为
  `effect_observed`（弱 I / 跨调用点）与 `reference_patch_required`。
- 四指标没动，证明**召回天花板在 reference-patch 路由与 stage2 弱 I 语义**，
  不在绑定质量；继续循环重绑定不会提升 recall。

## 阶段 23：M1 参考补丁路由接入 Lambo，四指标 4x 提升（2026-11-15）

### 根因
- Lambo 102/105/119 的漏洞是 `VirtualToken::cashIn` 在 ERC20 路径用
  `msg.value`（=0）铸币，属于“效果型/跨合约语义”，无法用单一 `assert(I)`
  注入表达，此前被判 `reference_patch_required` 但没有任何补丁数据源。
- `lib/reference_patch.py` 已支持 `case/patched.diff`，但盲测 case 目录里
  缺少这些 diff，路由是空的。

### 修复（确定性，无 LLM）
- 为三个 Lambo case 生成 `case/patched.diff`（同一处两行修复）：
  `cashIn` 中 `_mint(msg.sender, msg.value)` → `_mint(msg.sender, amount)`、
  `emit CashIn(msg.sender, msg.value)` → `emit CashIn(msg.sender, amount)`。
- `stage3_pipeline` 在 `reference_patch_required` 且 `patched.diff` 存在时
  自动物化 `case/patched/` 并走 M1 差分。

### 验证与结果
- Lambo 3 case 共 4 claim 全部 `violation_reproduced`（reference-patch 路由）。
- 合并进全量评估并重算权威四指标：
  - `recall`（可运行子集）10.0% → **40.0%**（4/10）
  - `recall_full_set` 2.5% → **10.0%**（4/40）
  - `recall_in_scope` 3.2% → **12.9%**（4/31）
  - claim 召回 3.1% → **15.6%**（5/32）
  - `recall_automatic` 保持 10.0%（Liquid 1027；Lambo 4 例计入
    reference-patch 口径，不计 automatic）

### 结论
- M1 参考补丁路由是当前 recall 的最大杠杆：一次接入即 4x。
- 剩余失分：`effect_observed_invariant_holds 21 + violation_not_reproduced 5`
  （stage2 弱 I）+ `binding_error 1`（Silo 453 P/V 侧跨合约绑定），
  是下一轮主线目标。


## 主口径切换（2026-11-16）
- 根因：dev-105 完成率 97.1% 且经多轮修复，条件召回 92.3% 不能外推；主口径改
  为 `sample_mainline.py` 分层随机抽样（20 项目分层、项目内按 severity 分配），
  positive 350 / negative 全量 91。
- 主口径当前值（`mainline_metrics.json`）：完成率 12.3%（43/350）、端到端召回
  4.3%（TP 15，自动 8 + 参考补丁 7）、条件召回 34.9%、漏洞级准确率 93.8%、
  F1(vuln, 端到端) 0.082。低完成率主因：121/150 stage2 失败是 DeepSeek
  HTTP 402（计费），另有 162 例 stage2 已过但 stage3 未跑。
- `metrics_sync.run_metrics_scripts` 已把 `sample_mainline.py` /
  `mainline_metrics.py` / `mainline_stage2_triage.py` 纳入主口径并加 CI 一致性门；
  `fullset_metrics` / `unified_metrics` 降级为诊断对照。
- 新增 `mainline_backlog.py`（无 LLM/forge）把 350 正样本拆成可执行桶并求和闭环：
  done 15 / rebind 19 / stage2_rerun 4 / reference_patch 3 / other 2 /
  stage3_ready 162 / stage2_retry_402 116 / stage2_real_fail 29。
- `run_mainline.py` 新增 `--retry-402`：只清 DeepSeek HTTP 402 的 stage2 status，
  避免把 29 个真实形式化失败一并重跑烧钱。
- `mainline_metrics` 报告明确对外漏洞级精确率用 `precision_vuln`（剔除 12 例
  SukukFi 影响不足 FP），`precision_consistency` 单列为机制一致性诊断口径。
- 修复 `tools/stage3/tests/test_binding_llm.py` 3 个因生成 fixture 漂移导致的失败：
  fixture 改为 `tests/fixtures/gte_swap_dos/` 自包含、可跟踪；stage3 244 项全绿。

## 阶段 24：重绑定根因修复与 dev252 客观召回刷新（2026-11-17）

### 根因
- `tools/stage3/lib/llm.py` 固定请求 DeepSeek 官方接口，旧 key 返回 HTTP 401，
  所有阶段三重绑定实际都未生效；日志里的少量复现来自历史运行，不能计入新指标。
- 剩余失分中，`invariant_holds_on_exploit_path` 与 `mixed_non_dynamic` 占多数，
  说明瓶颈已从绑定基础设施转到阶段二弱不变量（I 在 exploit 路径上恒成立）与
  语义型 `UNBOUND`，继续无差别重绑定收益很低。

### 修复与执行
- `tools/stage3/lib/llm.py` 改为读取 `config/llm.env`，支持 provider/base URL
  配置；当前使用 OpenCode Go 的 **`deepseek-v4.1-flash`**，未切换其他模型。
- `chat_json` 透传 `x-opencode-session` / `User-Agent`，默认禁用 thinking；
  对拒绝 thinking 参数的模型自动重试兼容。
- 以 `deepseek-v4.1-flash` 跑完 dev252 的两轮修复/重绑定 campaign；第一轮将
  63.9% 推到 67.5%，第二轮仅完成部分案例且无新增客观 TP，已停止继续烧调用。
- 修复 `vm.expectRevert` 转 `try/catch` 时的代码生成 bug：多行调用参数里的
  `// ...` 行尾注释会把合成闭合括号一起注释掉，导致 `Expected ','`。
- 新增保守的未限定调用限定规则：仅当 PoC 测试函数内同一方法只有一个接收者时，
  将 `validatePrice()` / `builderAdmin()` 改写为 `oracle.validatePrice()` /
  `BuilderWallet(wallet).builderAdmin()`，随后重新跑归一化把注入点移到测试函数。
- 对 15 个受该规则影响的已有 binding 用确定性 pipeline 重跑（不调用 LLM），
  Intuition、Panoptic 与 SukukFi 各新增 1 个客观复现。
- 指标统一由 `positive_eval_252.json` 经 `_row_for` 重建，再由
  `repro_failure_triage.py` 与 `judge_anchor.py` 生成，不直接采信历史 run 的
  `violation_reproduced`。

### 权威结果（dev252，252 例全部为已跑完 stage3 的 judge-valid 案例，无挑拣）
- 端到端召回：**68.7%（173/252，95% CI 62.7%–74.1%）**
- 判例锚定精确率：**92.5%（173/(173+14)）**
- 漏洞级精确率：**98.3%**（排除 11 例影响不足 FP）
- 可评测召回：**89.6%（173/193）**
- 全量完成率：**17.2%（252/1465）**
- F1（端到端 × 判例精确率）：约 **0.788**
- 天花板：**99.2%**；机制硬天花板 2 例；可恢复 FN 77 例

### 剩余 79 例 FN
- `mixed_non_dynamic` 35
- `invariant_holds_on_exploit_path` 15
- `partial_binding` 14
- `poc_not_witnessed` 7
- `compile_error` 2
- `binding_error` 2
- 其余 4 例：`reference_patch_required` 1、`inconclusive` 1、
  `not_dynamically_expressible` 1、`patch_no_effect` 1

### 结论
- 80% 目标尚未达到；当前提升来自真实重绑定与客观重建，不是挑案例或复用旧日志。
- 下一轮应优先修阶段二数值/检查点语义 I，并处理跨合约/时间窗等语义 UNBOUND；
  不再建议对剩余案例做无差别循环重绑定。

## 阶段 25：阶段二强不变量 gate + 语义 UNBOUND 分类（2026-11-17）

### 目标
把剩余 FN 的重心从“无差别重绑定”转到两条确定性链路：阶段二保证 I 非弱、非空、
与 V 同层可观测；阶段三把语义型 `UNBOUND` 分桶处理，不可恢复项及时路由。

### 阶段二
- `lib/plan_synthesizer.py` 新增 `weak_invariant_diagnostics` 与
  `weak_invariant_bucket`，输出结构化 code：`I_HOLDS_ON_EXPLOIT_PATH`、
  `I_IMPLIED_BY_P`、`I_NOT_FALSIFIED_BY_V`、`I_TRIVIAL_BOUND`、
  `I_COPIED_FROM_V`、`I_LAYER_MISMATCH`、`I_CHECKPOINT_COLLAPSED` 等。
  `reject_vacuous_safety` 只阻断 `severity=blocking`，checkpoint 类为 advisory。
- `_direct_witness_hint` 与 `piv_failure_bucket` 已接入新 code；弱不变量缺陷保持
  在分母中，不再被误归类为 report-material 缺失。
- 计划符号 schema 新增可选可观测性字段：`observable_kind`、`scope`、
  `receiver`、`contract_type`、`binding_risk`；跨合约符号缺少 `receiver` 直接拒绝。
- `observability_contract(plan)` 输出 per-symbol 可观测性合同；缺失核心符号标
  `binding_risk=high`，`symbol_table_review` 增加 `missing_observability` 告警。
- live prompt 升级为 `semantic-live-27`，冻结 `live26_snapshot.py`；新增
  OBSERVABILITY CONTRACT 段落。
- 阶段二输出新增 `observability-contract.json`、`weak-invariant-triage.json`；
  每个 claim 带 `i_falsifier_hint`（`P∧V∧¬I` 的 SAT witness）和结构化诊断。

### 阶段三
- 新增 `lib/unbound_semantics.py`：把 `UNBOUND` 分为时间窗、跨合约、派生布尔、
  mapping/struct、balance/allowance、V-only effect、真正不可观测七桶，只做有源码
  证据且唯一的确定性修复；时间窗/接收者/互补谓词均有单测。
- `stage3_pipeline` 在既有 normalize/rebind/complement/name 修复之后运行分类器，
  写 `unbound-semantics.json`；summary 增加分桶、`route_suggestion`、
  `semantic_terminal_unresolved`。全部剩余符号真正不可观测时，verdict loop 直接
  `skip`，不再重复烧绑定调用。
- `binding_llm` 移除 P 侧 `UNBOUND→true` 静默降级，改为保留 `UNBOUND` 并标记
  `degraded/degraded_reason`，避免弱 P 制造自动 TP。
- 新增 `lib/weak_invariant.py`，stage3 注入前记录 checkpoint 塌缩、I/V 同形、
  自蕴含、数值/布尔层不匹配风险，并携带阶段二 `i_falsifier_hint`。

### 离线回归（dev252）
- 证据：`tools/stage3/evaluation/metrics/weak_invariant_offline_252.json`
- 对 252 例既有 stage2 formalization 重放新 gate，不调用 LLM：
  - TP claims 命中 blocking 诊断：3（1.19%），全部为既有 `I_LAYER_MISMATCH`；
  - 新增 code（`I_HOLDS_ON_EXPLOIT_PATH` / `I_IMPLIED_BY_P` /
    `I_TRIVIAL_BOUND` / `I_COPIED_FROM_V`）TP 误杀：0；
  - FN 命中 1 例，属 `mixed_non_dynamic`。
- 本轮未重跑 LLM campaign，因此四指标不变，仍以阶段 24 的 dev252 为准：
  recall 68.7%、判例精确率 92.5%、漏洞级精确率 98.3%。

### 测试
- `tools/report_constraints_v2`：508 项全绿。
- `tools/stage3`：303 项全绿（含新增 unbound/weak-invariant 用例）。
- `git diff --check` 干净；无后台进程。
