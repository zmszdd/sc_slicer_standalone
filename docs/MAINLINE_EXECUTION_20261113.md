# 主线各阶段执行记录（2026-11-13）

按已批准六阶段方案依次执行。权威四指标未漂移：完成率 97.1%、端到端召回 61.4%
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
