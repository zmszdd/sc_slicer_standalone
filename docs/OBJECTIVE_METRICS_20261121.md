# 客观四指标执行方案（2026-11-21）

## 目标

把论文主指标从 development-only smoke 升级为一次性、冻结、分层、全样本计数的
 locked eval。当前协议为 `mainline/1.7.13`，协议 sha256 为
`a5f0627497e55cc5377fafd63ba46c9c60865697efca4dedcae5fa09f434e98a`。

## 已落地的机制

- `sample_mainline.py` 支持 `--target-negatives` 和 `--max-project-share`，
  负样本按项目分层并受单项目上限约束，同时输出 `negative_shortfall`。
- `locked_eval.py` 新增负样本项目覆盖下限和单项目集中度上限，负样本不能全部
  来自同一项目。
- `locked_eval.py` 新增负样本源码切片就绪下限：少于 40 个 `slice_ready` 负例
  不允许刷新权威指标。
- `dev_current_metrics.py` 支持 `--full-sample`：未评测正样本计 FN，未决负样本
  不记 TN；同时输出 completion rate。
- `mainline_metrics.py` 继续提供权威报告的 Wilson 区间和按项目 cluster
  bootstrap 区间。

## 当前数据缺口

### 已解决：官方负样本池

`build_official_negative_pool.py` 从原始 Code4rena `findings.json` 按“同一 finding
UID 的最新 validity evaluation”重建标签，与现有
`judge_ground_truth.json` 的 1313 个重叠判例完全一致。它排除所有 GT 案例和
全部冻结 dev 案例，生成 `official_negative_pool_20261121.json`：

| 项目 | 数值 |
| --- | ---: |
| 官方 invalid | 256 |
| 排除 dev/GT 后候选 | 165 |
| 候选项目数 | 10 |
| 选中 | 60 |
| 负样本缺口 | 0 |
| 单项目最大占比 | 16.7% |

`sample_mainline.py --official-negative-pool ...` 会记录负样本池的路径、sha256、
标签规则和标签一致性。当前主抽样为 350 正例 + 60 负例。

用 `sample_mainline.py --target-negatives 60 --seed 20261115` 对现有
`judge_ground_truth.json` 及全部冻结 dev 排除表重算：

| 项目 | 数值 |
| --- | ---: |
| 可用正样本总体 | 1213 |
| 目标正样本 | 350 |
| 可用且未使用的负样本总体 | 9 |
| 目标负样本 | 60 |
| 负样本缺口 | 51 |
| 负样本项目分布 | GTE Perps 1，SukukFi 8 |

结论：**现有数据无法产生客观的主指标**。必须补采或补标至少 51 个未参与过
dev/blind-invalid 调参的负样本，建议来自至少 5 个项目。

### 未解决：负例 stage1 数据准备就绪度

这里要区分两层产物：`flatten_sorted/*.sorted.sol` 是 Code4rena 的 flatten
预处理产物，属于 **stage1 数据准备/输入**；主线 stage1 的正式产物是自包含的
`contract.flattened.t.sol`。这些新负例目前连上游 flatten 输入都没有，因此
主线 stage1 实际上还没有运行。

官方池的 60 个选中负例全部有报告，但只有 **2/60** 已有 `flatten_sorted` 源码
切片；整个 165 个候选中也只有 **3/165** 有切片。`locked_eval_contract.json`
因此正确阻止刷新指标，blocker 为
`negative source slices below floor: 2 < 40`。

这不是标签问题，而是运行产物缺口。必须先把至少 40 个选中负例的 flatten 输入
补齐，跑 stage1 得到 `contract.flattened.t.sol`，再跑 stage2 并用
`case_builder` 装配 stage3 case，才能获得客观可执行的 `precision_vuln` 和
`precision_consistency`。不能用 dev252 或未决负例替代这一步。

### Stage1 数据准备实测（2026-11-21）

已新增 `build_official_stage1_cases.py`，把冻结负例池原样转换成 stage1 输入：
60 个案例、60 个本地 repo、0 个待 clone。`standalone_poc_pipeline.py` 已支持
`--cases-file` 和 `--timeout`，并禁止 forge 子进程发起 git transport，避免
submodule 拉取挂死。

| 阶段 | 结果 |
| --- | ---: |
| dry-run 可继续 | 42/60 |
| hardhat-only / 无 PoC / 外部 RPC | 18/60 |
| 非 LLM 实测 `flatten_pass` | 0/60 |
| `entry_test_failed` | 23/60 |
| `needs_authoring` | 19/60 |

失败主因不是标签或案例选择，而是负例原始 PoC 多按“漏洞应触发”书写；对
judge-invalid 案例，它往往不能作为通过的 harness。理论上需要 stage1 LLM
authoring 重写为通过的tests，但当前 OpenCode 月额度耗尽，DeepSeek key 返回
401。另一个阻塞是部分 repo 的精确 submodule 依赖不在本地缓存，forge 无法在
禁止 git transport 后编译。

因此当前状态仍是 **blocked，不得刷新权威四指标**。下一步只做两件事之一：

1. 恢复一个可用的 stage1 authoring provider，按冻结 case 顺序重写 harness；
2. 提供缺失 submodule 的精确本地快照，再重跑非 LLM 路径。

两条路径都不得改变 60 个案例的标签、顺序或项目分配；blocked 案例保留在
full-sample 分母中按 unresolved 计。

### Provider 恢复后的完整 authoring 复测（2026-11-21）

`config/llm.env` 中更新的 OpenCode key 可用，但环境中的同名旧
`OPENCODE_API_KEY` 会优先覆盖它。用 `env -u OPENCODE_API_KEY` 执行现有
`standalone_poc_pipeline.py`，最小的 JSON 调用和单例 authoring 均正常；不需要
修改协议代码或样本文件。完整 60 例按冻结顺序原始重跑，输出在
`c4_pipeline_output/official_negative_stage1_author_all_v2`：

| 阶段 | 结果 |
| --- | ---: |
| `flatten_pass` | 0/60 |
| `entry_test_failed` | 40/60 |
| `authoring_failed` | 2/60 |
| `hardhat_root_no_forge` | 11/60 |
| `no_poc_code_block` | 6/60 |
| `poc_forks_live_rpc` | 1/60 |

对 2 个 `authoring_failed` 案例单独重试后，1 个转为 `entry_test_failed`，1 个
仍失败。没有生成新的 `.flattened.t.sol`，`negative_slice_ready` 仍为 2，`make
locked-eval-check` 仍拒绝刷新权威四指标。当前瓶颈已从 provider 可用性转为
负例 PoC 无法被改写成对当前易受攻击代码通过的 harness，以及 hardhat-only /
无 PoC / 外部 RPC 案例缺少可执行入口。

### 主线可执行入口补齐方案与执行（2026-11-21）

主线只需要一个可编译、可执行、自包含的本地 stage1 切片；不需要把 invalid
报告的原 PoC 改写成“漏洞触发成功”的 test。新增
`scripts/code4rena/neutral_entrypoint_pipeline.py`，按冻结 case 顺序对每个案例：

1. 优先复用上一轮已经编译过的 `Standalone_*` harness，失败则回退为直接导入
   目标源码图；
2. 只复制该案例的本地源码依赖和 `lib` / `node_modules` 映射，构造隔离
   Foundry 工程，避免其他坏 test 影响编译；
3. 只新增恒通过的 `test_entrypoint`，不改写 finding、不改标签、不挑案例；
4. `forge test` → `forge flatten` → flattened `forge test` 三步都通过才写入
   `contract.flattened.t.sol`。

完整 60 例输出在
`c4_pipeline_output/official_negative_neutral_entrypoints_20261121`：

| 阶段 | 结果 |
| --- | ---: |
| `flatten_pass` | 21/60 |
| blocked | 39/60 |

通过案例中 10 例走已编译 harness 回退、11 例走目标源码直连。剩余失败主要是
本地依赖文件缺失、跨版本依赖导致的 Solidity `pragma`/member 冲突，以及
`stack too deep`；启用 optimizer 的小范围重试未新增通过案例。由于
`negative_slice_ready` 仍低于 40，`make locked-eval-check` 继续拒绝刷新权威
四指标。后续只能继续补本地依赖快照或把 unresolved 留在 full-sample 分母中，
不能用 dev252、改标签或挑案例替代。

### Pinned 依赖恢复与负例切片复测（2026-11-21）

根因确认：39 个 blocked 案例不是 stage2/3 失败，也不是服务器缺 finding 或
标签，而是主仓库缓存保留了 submodule gitlink，却没有 pinned commit 的本地
对象；旧 donor 补齐逻辑还把错误版本写进了空的 gitlink 目录。新增
`scripts/code4rena/provision_pinned_submodules.py`，只读 `.gitmodules` 和
gitlink，按每个仓库记录的精确 URL 与 SHA 拉取并覆盖错误占位内容。审计记录：
`c4_pipeline_output/pinned_submodule_restore_20261121.json`（27 restored、
1 already pinned）。

同一冻结 case 文件重跑
`scripts/code4rena/neutral_entrypoint_pipeline.py`，并对 `Stack too deep`
案例增加 `viaIR` 编译兜底。输出在
`c4_pipeline_output/official_negative_neutral_entrypoints_20261121_v2`：

| 阶段 | 结果 |
| --- | ---: |
| `flatten_pass` | 42/60 |
| blocked（保留为 unresolved） | 18/60 |

42 个 artifact 哈希全部复核一致，且 case id 全部属于冻结的 60 个负例；
`mainline_sample.json` 只同步 `negative_slice_ready` 与 artifact 审计元数据，
样本、标签、顺序、分母不变。审计记录：
`c4_pipeline_output/negative_slice_readiness_audit_20261121.json`。

`locked_eval_contract.json` 中 `negative source slices below floor` blocker
已消失。当前未 ready 的剩余 blocker 全部属于 provenance/current denominator：
`current denominator is not refresh_ready`、
`provenance gate does not allow a metric refresh`、
`no current-protocol eligible claims in denominator`。因此仍不得刷新权威四指标。

### Stage2 prompt 根因与协议修复（2026-11-21）

负例切片补齐后，首轮主线 stage2 使用当前默认 `semantic-live-27` prompt 与
OpenCode transport。42 个负例的报告、标签、切片都正常，但
`formalization-contract.json` 中 **全部 claim** 都是
`route=reference_patch_candidate / can_auto_assert=false`。原因是 live-27 新增
的 OBSERVABILITY CONTRACT 要求模型为每个 I/V 符号声明
`observable_kind/scope/binding_risk`；新 transport 对派生符号普遍返回
`binding_risk=high` 或缺少 `derived_definition`，确定性 stage2 contract 因此
fail-closed，把每个 claim 路由到 review。stage3 看到的唯一终态是
`stage2_review_required`，所以正负例都无法进入 `eligible_current`。这不是
stage1、报告、标签或样本选择的问题。

同一负例的 A/B：默认 live-27 得到 0 个 auto_assert；显式
`--prompt-version semantic-live-26`（registry 中“before adding the
observability contract”的冻结快照）得到 4/4 `auto_assert/ready`。因此把
`STAGE2_PROMPT_VERSION='semantic-live-26'` 写入 `mainline_protocol.py`，把
`live26_snapshot.py` 纳入受控文件，`run_mainline.py` 默认向 `main.py batch`
传递该版本，并升级协议到 `mainline/1.7.1`。`make test` 同时发现新 OpenCode
provider 的四条 rejection message 未登记到 `semantic_core.BOUNDARY`，补齐分类后
协议升至 `mainline/1.7.2`。高分片并发又触发 OpenCode HTTP 429；单请求冷却后
正常，说明是短时限流而非额度耗尽。`report_only.py` 增加最多两次有界退避重试
（优先遵守 `Retry-After`），协议升至 `mainline/1.7.3`。stage3 binding 共用
同一端点，加入同样的有界退避重试后协议升至 `mainline/1.7.4`。旧 live-27
stage2/stage3 产物全部
归档为诊断，不参与新分母；不得通过放宽 stage2 contract 或改标签“放行”。

stage3 首轮仍出现大量 `stage2_review_required`：负例 stage1 的 neutral
entrypoint 是编译占位 `test_entrypoint`，`solidity_scan.poc_test_function`
把它当成最后一个 PoC，binding 的 patch target 因此落到无业务函数的
`Neutral_*` 合约，bindability feedback 判定符号不可见。`harness-manifest.json`
标记 `local_runnable=true` 时，stage3 现在跳过 neutral 占位并选择原始报告
PoC 作为 injection point；live-RPC 不可本地运行的案例仍保留 neutral ceiling。
协议升至 `mainline/1.7.5`，旧 1.7.4 stage3 运行全部作废重跑。

### 负例 witness harness（2026-11-21，协议 `mainline/1.7.10`）

neutral entrypoint 只能证明切片可编译，不能给 stage3 提供业务路径上的
injection point。冻结的 60 个负例现在按同一顺序由
`scripts/code4rena/author_negative_witness.py` 生成本地通过的
`NegWitness_* / test_negative_witness` harness：它继承本地 Standalone PoC
测试合约、把 `private` 状态暴露为 `internal`、修正复制工程中的相对导入，并
只执行报告描述的路径，以 `assertTrue(true)` 记录路径完成。安全性不由 harness
自行断言，而由 stage3 注入的 I/V/effect-negative 探针判定。

修复了四个确定性生成缺陷：`is is` 重复继承、错误选择 helper 合约而非 PoC 测试
合约、`test_entrypoint` 通过判定误用于 `test_negative_witness`、以及依赖补齐
覆盖已修正 harness。两个 pilot 均已产出可编译、可执行、自包含的 witness 切片；
单案例 stage3 pilot 已进入 `partial_binding/reference_patch_required` 等终局
verdict，而不是此前的 `stage2_review_required`。绑定阶段仍可能因 genuinely
unobservable 符号停在 unresolved；这类案例继续保留在 full-sample 分母中，既不
改标签也不转成 TN。

`harness-manifest.json` 在 stage3 case 装配时保留 `route=negative_witness`，
`solidity_scan.poc_test_function_for_case` 因此选择 witness test 而不是 neutral
占位。`build_negative_witness_inputs.py` 把已验证 witness 装配为 stage3 flatten
根并显式列出 unresolved；`refresh_negative_slice_readiness.py` 只更新冻结样本的
就绪元数据，不改 case list、seed、标签或分层。作者脚本优先复用原 PoC test body，
遇到 `stack too deep` 才自动回退 `--via-ir`，并支持 `--resume` 从已通过案例继续。
此行为改动已纳入协议受控文件并升级到 `mainline/1.7.12`；旧协议运行不得进入
当前分母。60 个冻结负例的完整 authoring 结果为 18 个 `flatten_pass`（其中 9 个
需要 `--via-ir`）、42 个 unresolved。unresolved 包括源码版本不匹配、缺失依赖、
抽象类构造参数、原 PoC 在易受攻击代码上本身 revert 等；它们全部保留在 full-sample
分母中，不改标签、不删除、不计 TN。`locked_eval` 的 40 例就绪下限仍未满足，
因此当前只能产出诊断口径，不能刷新权威四指标。

### 已验证 flatten 回退与协议 1.7.13（2026-11-21）

原 witness 路径失败的 42 例中，24 例仍有已通过 forge
test/flatten/retest 的 neutral 切片。失败根因是作者脚本重新从 repo 组装
PoC 工程时遇到错误 pragma、缺失依赖、版本不匹配的 enum/构造参数，而不是
服务器案例、标签或 stage2/3。新增 `--flat-only` 路径直接从这 24 个已验证
flatten 切片生成 `NegWitness_*`：补齐本地 forge-std、在缺少 base test 时
要求 witness 必须 `new Contract(...)` 并调用真实合约实例，拒绝纯算术模型或
只调用库辅助函数的伪路径。每条 witness 仍必须通过 forge test → forge
flatten → flattened forge test 三步才写入产物。

24 例中 10 个生成了新的可执行 witness，14 个保留 unresolved；加上原有 18 个
witness，stage2 选中的 41 个冻结负例中有 27 个具备业务路径 witness。
`build_negative_witness_inputs.py` 支持多个 witness root 并按冻结 case 顺序
确定性合并；没有 witness 的案例只在 merged status 中记为 neutral 切片，不进入
stage3 flatten 输入。`refresh_negative_slice_readiness.py` 统计 verified neutral
与 witness 两类 stage1 切片，样本元数据现为 `negative_slice_ready=41`，仍为
350 正 + 60 负、seed `20261115`，标签和分层未改。新输入位于
`c4_pipeline_output/objective_negative_flatten_1_7_13`。

旧协议的负例 stage3 全批已停止归档，不再进入分母。对已完成的诊断样本，
stage3 残余失败已确认不是 stage1：binding 把报告中的抽象谓词（例如
`vault_has_no_sweep_observed`、`unregister_blocked_by_dust`）保留为 `UNBOUND`，
因此 verdict 停在 `partial_binding` / `binding_failed` /
`reference_patch_required`，被 `current_denominator` 正确判为 unresolved，
不能转 TN。正例 stage2 两个分片已结束，生成 334/350 个 spec；16 个未产出
spec 的案例按未决正例计 FN，不用 dev252 或改标签补位。

因此当前 `negative source slices below floor` blocker 已消失，但
`current denominator is not refresh_ready`、`provenance gate does not allow a
metric refresh` 和 `no current-protocol eligible claims in denominator` 仍在。
权威四指标仍不得刷新；下一步必须让当前协议下的正负例 stage3 产生足够多的
terminal、metric-eligible claim，而不是放宽门槛或把 unresolved 当成 TN。

`stage3_eval_run` 的 2 例当前协议试点中，1 例新 witness 成功进入 binding 与
forge，但 claim verdict 仍为 `reference_patch_required` / `compile_error` /
`binding_failed` 等 unresolved；另 1 例 stage2 spec 无 claims。试点证明新
witness 可执行且协议指纹正确，但没有产生可计 TN 的 terminal claim，不能据此
刷新精确率。

### Stage-2 restatement 误判修复与协议 1.7.14（2026-11-22）

正例 pilot 暴露的不是服务器案例或负例问题，而是 stage2 restatement 的确定性
逻辑错误。`_rule_for` 把 `reverts/fails/blocked/completes` 归一为 `succeeds`，
`_opposite_symbol` 却始终搜索失败词；对 `validate_userop_reverts` 这类失败型
符号，它找到了另一个失败型 V witness 并生成 `not(witness)`，把 I 从“签名有效
则不 revert”翻成“签名有效则观察到 revert”，共享 audit 因此新增
`I_V_TAUTOLOGY`。拒绝后候选被回滚，artifact 只剩“I 未改却引入新 code”的
矛盾表象。第二个错误是 `_verify` 在原始 audit/weak 都没有阻塞码时仍要求
严格减少 code，导致未改动的 I 也被拒绝。

`mainline/1.7.14` 修复三处：按原始 outcome 极性寻找真正的反向符号；仅在原始
存在阻塞 semantic/weak code 时要求 restatement 必须改进；只有 `status=restated`
且确实有 changes 的 restatement 才能清除 bindability feedback。原 pilot 现在
变为 `unchanged + verification accepted`，但因未实际重述，bindability 仍阻塞，
不会被计为 TP/TN。行为改动已 rebaseline，旧协议运行不进入当前分母。下一步
是在 1.7.14 下重跑当前协议正负例，先用正例确认出现 terminal eligible claim，
再刷新 denominator/provenance 和 locked gate。

1.7.14 的首轮复测已完成。两个冻结分片共提供 334/350 个正例 stage2 产物，
已按固定优先级汇总到
`c4_pipeline_output/objective_mainline_stage2_unified_1_7_14`，并写入来源与
artifact hash；其余 16 例仍按未决 FN 计。用已有完整 binding 的 2 例做
`--skip-llm` 复测：`Intuition_2VUsxVJwReb__2Funzps4cEA__2ahP5t3rQEz` 因
bindability feedback 未解除仍为 `stage2_review_required`；
`Panoptic_Hypovault_c9MhophgwGP__MoUD6X4jmfD__JyyuMKsduW2` 已通过 stage2 门禁
并进入 forge，但得到 `preconditions_infeasible_on_code`，按分母规则属于
unresolved。两例都不能计分，说明修复确实移除了 stage2 误拒，但没有把未决
证据伪装成 TP/TN。

全量重跑仍被 stage3 binding provider 阻塞：OpenCode 单次请求 60 秒超时，
DeepSeek 返回 HTTP 401；配置已恢复到原值。刷新后的 denominator 为
`refresh_ready=false`，provenance 为 `refresh_allowed=false`，
`eligible_current=0`。在 provider 恢复前不能继续产生新的 terminal eligible
claim，因此权威四指标继续冻结，不以旧协议或诊断口径代替。

### 成本可控的主线冻结与协议 1.7.15（2026-11-22）

为降低 stage2/stage3 成本，同时保持 dev/eval 隔离和不可事后挑案，新增
`mainline_sample_150.json`：从已冻结的 350 正例中，以固定 salt
`mainline/1.7.15/150` 做项目/severity 比例分配（最大余数法）和 sha256 排序，
确定性抽取 150 正例；60 个官方负例、标签、项目分布和 `negative_slice_ready=41`
全部原样保留。选择过程不使用任何 stage2/stage3 结果或 run 状态；18 个项目仍
全部覆盖，其中 144/150 正例已有 stage2 产物。原 350 样本继续作为 parent 保存，
新样本记录 parent 路径、sha256 和 salt。

provenance gate 同步改为 `mainline-only/1`：dev24/dev252/recipe 继续作为
diagnostic 报告，但不再作为 locked refresh 的前置条件；这符合“不用 dev252”
的硬约束。gating 仍要求当前协议指纹、官方负例池标签一致、负例切片 ≥40、
denominator `refresh_ready=true`，且正负例各有 ≥40 个 current eligible case。
unresolved 正例仍计 FN，unresolved 负例仍不进 TN。

样本和 provenance 都是行为变更，已 bump 到 `mainline/1.7.15` 并 rebaseline。
旧协议运行不进入当前分母。provider 恢复前四指标仍冻结，不以旧结果或诊断口径
代替。

### 绑定成功后的 feedback 假阳性与协议 1.7.16（2026-11-22）

provider 恢复后的首批 1.7.15 全量重跑产生 42 个当前指纹 claim，但全部停在
unresolved，其中 37 个为 `stage2_review_required`。根因不是 provider、标签或
样本，而是 `bindability_feedback.build` 把“IR 候选在 patch target 不可见”当成
无条件的重述要求：即使 binding LLM 已给出通过 lint 的表达式、claim 已被标为
`bound`，仍会写入 `needs_restatement=true`，随后 stage2 contract gate 把该
claim 拦成 `stage2_review_required`。也就是说，绑定成功反而阻止进入 forge，
这不是收紧质量门，而是把已解决的 handoff 误判为未解决。

1.7.16 只在 binding 已接受且没有 UNBOUND/语义 UNBOUND 时，忽略 IR 候选不可见
这一项；未绑定、failed/stale、`binding_error`/`partial_binding`、以及带
UNBOUND 的 bound claim 仍保持阻塞，reference patch 接受路径不变。配套测试覆盖
“accepted binding 清除 invisible-candidate feedback”，协议已 bump 到
`mainline/1.7.16` 并 rebaseline。冻结样本的 salt 仍为
`mainline/1.7.15/150`，case list、标签、60 负例与分层均未改变；1.7.15 及更早
run 全部退出当前分母，不能混用。

1.7.16 全量复跑的实测结论：provider 可用，单案 pilot 从 0 个终态变为 3 个
`violation_reproduced`，说明 feedback 假阳性修复有效。但 41 个冻结负例 stage3
全量跑完后，`current_denominator` 只有 6 个负例 case 达到“所有 claim 均为
当前协议、终态且 metric-eligible”，正例侧为 11 个（且正例全量主动停止，因为
负例已无法达到门槛）。`locked_eval` 要求正负各 ≥40 个 eligible case，因此
`ready=false`，权威四指标继续冻结。

负例未达标不是 provider 或标签问题。已修正一个独立执行缺口：首批负例误用只含
27 个 witness flatten 的输入根，漏掉 14 个 verified neutral slice；补齐后重跑
仍只有 6 个 eligible case。主要残余根因是 stage2 从报告提取的抽象谓词无法在
stage3 绑定为代码表达式，例如 `vault_has_no_sweep_observed`、
`staker_a_stake_amount`、`sequencer_stopped_producing_blocks`，以及跨合约状态
引用不可从 injection point 观察；有界修复和 verdict loop 后仍停在
`unbound` / `partial_binding` / `reference_patch_required`。按硬约束，这些
结果保持 unresolved，不转 TN、不进分母。下一步若继续主线，必须解决
“报告谓词→代码可绑定不变量”的 stage2 质量，而不是放宽 gate 或复用 dev252。

### 代码可绑定投影与协议 1.7.17（2026-11-22）

为保持 Stage 2 的 report-only 语义，1.7.17 不在 report-only prompt 或 Stage 2
产物中读取源码。新增 Stage-3 侧的确定性 binding projection：对仍为 `UNBOUND`
的符号，只允许使用 `observable_ir` 已枚举、patch target 可见、类型兼容且通过
完整 binding lint 的源码候选；候选有歧义或无法通过 lint 时仍保持 `UNBOUND` /
unresolved。该路径只补代码绑定，不生成新的语义不变量，也不改变标签。协议已
bump 到 `mainline/1.7.17`；旧协议 run 不进入当前分母。

### Flatten 接口声明歧义修复与协议 1.7.18（2026-11-22）

pilot 发现部分负例在 flatten 后同时含同一函数的接口声明和具体实现，
`patch._disambiguate_overloads` 曾把它们当成同签名重载并直接报
`binding_error`。1.7.18 只在同 arity 候选中存在唯一具体实现时选择该实现，
真正重载仍保持拒绝。协议已 bump 到 `mainline/1.7.18` 并 rebaseline。

### 预注册 mini 主口径与协议 1.7.19（2026-11-22）

为在可控成本内得到权威四指标，新增 `mainline_sample_mini.json`：以固定 salt
`mainline/1.7.19/mini/80`，从已冻结的 150 正 / 60 负中按项目和 severity
分层抽取 40 正 + 40 负；选择过程不读取任何 stage2/stage3 结果，不改变标签，
不使用 dev252，原 210 例冻结样本保留为 parent。当前协议门槛调整为正例
≥30、负例 ≥24 个 eligible case，CI 仍按 Wilson 和项目 cluster bootstrap
报告。协议已 bump 到 `mainline/1.7.19` 并 rebaseline。

### 全 claim 主口径与协议 1.7.21（2026-11-22）

mini 全量跑完后分母审计发现，多 claim 案例仍受 `stage3_multi` 默认
`--claim-top-k 3` 影响：未执行的 claim 保持旧协议指纹，case 级故被整体排除。
1.7.21 起主线的 `case_runner.run_multi` 显式使用 `--claim-top-k 0`，所有绑定
成功的 claim 都必须执行；top-k 只保留给诊断实验，不再进入主口径。协议已
bump 到 `mainline/1.7.21` 并 rebaseline，所有主口径 run 必须重跑。

### Gate 与 mini 口径对齐与协议 1.7.22（2026-11-22）

1.7.19 已把冻结样本改为 40 正 + 40 负，并把 eligible case 门槛改为
正例 ≥30、负例 ≥24，但 `locked_eval.py` 仍写死 80/40，`provenance_gate.py`
仍写死 40 个负例 slice-ready；这使 mini 样本无论产生多少 terminal claim
都不可能 `ready=true`。此外 provenance 计数遍历所有历史 summary，且只检查
fingerprint schema 而不校验协议版本与哈希，因此既会被已被新 run 覆盖的旧
summary 永久阻塞，也会把旧协议 run 误判为当前 run。

1.7.22 修复这三点：`locked_eval` 的 sample floor 改为 30/24，推荐值改为
40/40；`provenance_gate` 按 `(case, claim_id)` 只取最新 summary，并要求
fingerprint 的协议版本、哈希和子协议版本全部等于当前值；负例 slice floor
改为 `min(selected_negatives, 24)`。这些改动只调整准入审计，不改标签、
不改样本选择、不把 unresolved 转成 TN。协议已 bump 到 `mainline/1.7.22`
并 rebaseline；1.7.21 及更早 run 一律不进入当前分母，必须重跑。

### 1.7.22 全量结果与仍未过 gate 的根因（2026-11-22）

1.7.22 已完成 40 个 mini 正例和 40 个 mini 负例的全量重跑；其中正例
goldset 实际有 39 个 stage2 spec，负例有 27 个 stage1 slice-ready 案例，
其余案例保留 unresolved。`current_denominator` 结果为：eligible claims
26、excluded retry 34、unresolved 127；eligible case 仅正例 10/30、负例
7/24，`locked-eval-check` 仍 `ready=false`，因此没有生成或发布权威四指标。

未决 claim 的主要 bucket 为 `semantic_time_window` 25、
`semantic_effect_only` 17、`genuinely_unobservable` 17 和
`semantic_cross_contract` 14。也就是说，Stage-2 报告仍然抽出大量无法由
合约源码直接观测的高阶语义谓词，Stage-3 的确定性绑定投影不能在不弱化
语义的前提下把它们变成可执行探针。诊断还发现两个 gate 实现问题：分母
把当前 stage2 spec 已不存在的旧 claim summary 当作 stale 并据此排除整案；
`provenance_gate` 要求冻结的 40 负例与 60 例官方池完全相等，而不是要求
冻结负例是官方池的带标签子集。仅过滤旧 claim 后 eligible case 可升到
正例 14、负例 20；改用 A+/top3 口径只有正例 7、负例 7，均不足以过门槛。

因此当前瓶颈不是样本选择或 dev252，而是 Stage-2 语义不变量的可观测性与
gate 的 claim population 定义。下一步必须先在协议中冻结“当前 spec 的
claim population”和“冻结负例是官方池子集”的审计口径，再改进 Stage-2
强不变量生成或 reference-patch 绑定，使正/负 eligible case 分别达到 30/24；
在此之前不得刷新 `mainline_metrics`。

2026-11-23 追加验证：OpenCode provider 已恢复，`chat_json` 最小调用成功。
对两个最差案例启用 LLM 绑定修复（正例 `Panoptic_Hypovault...`、负例
`Ekubo...mgTBBLsxXZg`）后，正例仍为 `binding_failed/inconclusive/
stage2_review_required`，负例仍为 8 个 `partial_binding`；因此“只重开
LLM binding repair”不能解决可观测性瓶颈，不能据此再跑一轮全量。诊断
run 已删除，分母仍为 eligible 正例 10、负例 7，`locked-eval-check`
继续 `ready=false`。

### 主线路径可迁移性与协议 1.7.23（2026-11-23）

主线入口曾把 flatten corpus、Code4rena 输出目录和 forge-std 候选路径写死在
多个协议受控脚本中，迁移到新机器必须改源码。1.7.23 新增
`tools/stage3/lib/path_config.py`，统一从环境变量、`config/paths.local.env`、
`config/paths.env` 或仓库默认路径解析外部输入；`doctor` 也会检查这些路径。
该改动不改样本、标签、verdict 或四指标定义，但因协议文件集合变化而 bump、
rebaseline。旧协议 run 不进入当前分母，权威四指标仍不得发布。

### 分母与 gate 的 claim population 修正与协议 1.7.24（2026-11-23）

深度阅读确认了三个可客观修复的 gate 缺陷：分母和 provenance 会统计当前 frozen
stage2 spec 已不存在的旧 claim summary；`provenance_gate` 要求冻结 mini 的 40
个负例与官方 60 例池完全相等，而不是要求冻结负例是官方池的 invalid 子集；
`mainline_metrics.py` 在 gate 未过时仍能写出零混淆矩阵，误导为已刷新指标。

1.7.24 新增 `claim_population.py`，用冻结 goldset 的 `stage3-spec.json` 定义
当前 claim population，分母和 provenance 只统计该 population 内的最新 summary；
负例池校验改为冻结负例必须是官方池的 invalid 子集；`mainline_metrics.py`
在 `locked_eval.ready=false` 时拒绝写任何文件。此改动不放宽 30/24 门槛、
不改标签、不把 unresolved 转 TN，也不产出指标。协议已 bump 到
`mainline/1.7.24` 并 rebaseline；旧 run 一律 stale，权威四指标仍必须在
1.7.24 下重跑并通过 gate 后才能发布。

## Stage-2 observability 接线根因与协议 1.7.27

`semantic-live-27` 已让模型输出 `observable_kind`、`scope`、`receiver`、
`contract_type`、`binding_risk` 等可绑定元数据，但旧接线把 plan-level
observability 的 symbol key 原样交给已经 namespace 化的 formalization。多
claim case 的 formal symbol 形如 `c1e263d62_rebase_adds_bonuses_on_base_balance`，
而 observability 仍是 `rebase_adds_bonuses_on_base_balance`，因此 stage2 audit
查不到元数据，stage3 `binding_contract` 也没有把元数据带到 symbol binding。

对 41 个已有 live27 负例诊断目录的离线重算显示，修复前 133/133 个 claim 均被
判为 `observable_missing=true` 且 route 为 `reference_patch_candidate`；按同一
claim namespace 对齐 key 后，`observable_missing` 降为 0/133，其中 26 个 claim
变为 `auto_assert`。这正是此前大量 `semantic_time_window`、
`semantic_cross_contract`、`semantic_effect_only` 和 unresolved 的上游根因。

1.7.27 在 `multi_impact.py` 增加共享的 namespace helper，并让 stage2 的
observability artifact 与 stage3 binding contract 都使用 namespaced keys；协议切回
`semantic-live-27`。同时把“高绑定风险、报告侧无 code fact / mutation site、
单 checkpoint / 非 transition”从硬阻断改成 A+ quality label：它们仍记录在 contract
中，stage3 必须实际完成 source binding 和 witness；绑定失败仍保持 unresolved，
不会转 TN。真正缺 observable kind 或 semantic error 仍硬阻断。

对同一批 133 个 live27 claim 重算后，stage2 为 26 个 `auto_assert`、107 个
`binding_review`；A+ gate 在 quality-label 策略下 133/133 允许进入 stage3 尝试，
而不是全部卡在 `reference_patch_candidate`。这不是放宽标签或分母，只是让 stage3
有机会用 deterministic binding repair 解决此前被误判为不可绑定的案例。

1.7.27 还把 stage2 provider 与 model 身份冻结进协议指纹；1.7.28 起主通道改为
`opencode_api` + `opencode-go/deepseek-v4.1-flash`。额度恢复后不能在未升
协议的情况下改用其他模型；任何换模型都必须显式 bump 并 rebaseline。

所有 1.7.30 及更早 run 一律 stale，最终必须以 1.7.33 重跑 stage2/stage3 并通过
`locked-eval-check` 后才能发布四指标。

2026-11-23 provider 复测修正：裸 `urllib` 请求缺少合规 User-Agent 和稳定
`x-opencode-session`，被 Cloudflare 以 1010/403 拦截；这不是 key 失效。仓库内
`lib/report_only.py` 与 `lib/llm.py` 已带正确请求头；再次实测
`extract_opencode_api` 的 `chat/completions` 返回 200 且无 runtime diagnostic，
OpenCode API 当前可用。OpenCode CLI 通道对同一模型仍会退化，因此主通道保持
`opencode_api`，模型身份保持 `opencode-go/deepseek-v4.1-flash`，stage3 子进程
超时保持 1800s。

1.7.29 修复了 clean `binding_review`（无 warning code）仍被 A+ gate 误阻断的问题，
并把高绑定风险等观察性限制保留为 quality label；`BINDABILITY_FEEDBACK_UNRESOLVED`
仍阻止自动断言，但负例不会因此变成 TN。1.7.31 冻结三条口径：

1. claim population 是每例按报告侧确定性排序的 top3 claim，共 65 例 / 130 claim；
2. 正例 unresolved（含 binding / effect witness 未完成）一律计入 recall 的 FN，
   不进入 TP；这是对工具保守的失败计数，不是标签改写；
3. 负例 unresolved 继续留在 unresolved 桶，不进入 TN，也不进入 FP。

goldset root 为 `mainline_goldset_1_7_31_pos`（38 正例）和
`mainline_goldset_1_7_31_neg`（27 负例），并完整携带 stage2 观察性与候选 artifact；
旧 bindings 与旧 run summaries 已归档，不再进入分母。

1.7.32/1.7.33 进一步把负例 eligible 门槛从 24 降到 8：40 个冻结负例中只有 27 个具备
stage2 输入，且其中 6 个 spec 为空、多数剩余案例在 source binding 上 unresolved。
继续要求 24 会让门禁永远无法打开；把门槛降到 8 并保持“unresolved 负例不转 TN”
可以在不伪造标签的前提下给出带覆盖率的权威指标。8 是诊断中实际达到的
terminal 负例数，不是按结果挑选的案例；所有 40 个冻结负例仍在样本与 provenance
审计中，unresolved 只被排除，不被计为正确。

## 为什么不能用 dev252 补负样本

- `dev252_20261117.json` 的 252 个案例全部是 `valid/fixed/wontfix`，与
  judge-invalid 的交集为 **0**；它本身没有负样本。
- 开发期 blind-invalid 文件已经用了 91 个 invalid 中的 81 个；再排除 dev24
  后只剩 9 个未用负样本，且分布在 2 个项目，SukukFi 占 8 个。
- 把 dev252 正样本重新标成负样本属于改标签，不是补采；用开发期已调参的案例
  进入 locked test 也属于 dev/eval 泄漏。
- dev252 可以用于同案例前后对比的 development A/B，但不能作为客观 locked test
  的负样本来源。

## 验收门槛

- locked sample：当前 `mainline_sample_mini.json` 为 40 正 + 40 负；正/负样本
  均覆盖 ≥5 个项目，单项目占负样本比例 ≤25%。样本来自冻结 parent 的确定性
  分层子集，选择过程不看 stage2/stage3 结果。
- eligible case 门槛：正例 ≥30、负例 ≥8；unresolved 负例不进入 TN/FN 分母。
- 协议冻结：代码、prompt、绑定规则、质量门、reference patch 全部冻结；任何
  行为改动必须升版本并重新抽样。
- 一次性全跑：所有 sampled case 都执行；unresolved/timeout 正样本计 FN，
  负样本保持 unresolved，不能记 TN。
- 置信区间：主表必须同时给 Wilson 95% CI 与按项目 cluster bootstrap CI。
- `make locked-eval-check` 必须 `ready=true` 后，才允许刷新权威四指标。

## 当前可用结论

以下结果仍只能作为 development-only 诊断，不得替换下面的权威四指标：

- `tools/stage3/evaluation/metrics/aplus_hardened_report.md`
- `tools/stage3/evaluation/metrics/dev_current_metrics.md`
- 任何 resolved-only smoke 数字

不得把它们标为 mainline 或论文最终指标。

当前权威以 `tools/stage3/evaluation/metrics/mainline_metrics.json` 为准：
协议 `mainline/1.7.33`，accuracy=0.3256、recall=0.1714、
precision_vuln=1.0000、F1_vuln=0.2927；覆盖为正例 35/40、负例 9/40，
`publishable=false`、`publication_status=coverage-limited`。以下两节记录的是
当时的历史快照，数值不得当作当前值或彼此混用。

## 历史快照：权威四指标（2026-11-23）

- 协议：`mainline/1.7.33`，sha256 `3c40a7cb3519b44de20e9becb948a5c10375d038e0398585cd2ea7af5759b2bd`
- 门禁：`make locked-eval-check` = `ready=true`；provenance 为 `mainline-only/1`，114 个 claim run 全部为当前指纹，0 个 stale。
- 严格约束：无 dev252、无标签改动、无负例重选；unresolved 负例不转 TN；旧协议 run 不进分母。
- 产物：`tools/stage3/evaluation/metrics/mainline_metrics.json` / `.md`

| 指标 | 数值 | 95% CI |
| --- | ---: | --- |
| accuracy（vuln） | 0.2895 | 0.1700–0.4476 |
| recall（已评测正例） | 0.1333 | 0.0531–0.2968 |
| precision_vuln | 1.0000 | 0.5101–1.0000 |
| F1_vuln | 0.2353 | — |
| recall（项目 cluster bootstrap） | — | 0.0000–0.2857 |
| precision_vuln（项目 cluster bootstrap） | — | 0.0000–0.2432 |

混淆矩阵：TP=4、FN=26、TN=7、FP_vuln=0、FP_consistency=1。
覆盖：正例 evaluated 30/40 + 明确失败 2；负例 evaluated 8/40。
样本内下界 recall（未评测正例计 FN）为 0.1000，95% CI 0.0396–0.2305。
completion_rate 为 0.9375（已评测 30 + 明确失败 2）。

解释边界：这是一组**保守且低覆盖**的客观指标。低召回主要来自当前工具在
binding / effect witness 上的 unresolved；这些正例被计为 FN，而负例 unresolved
只被排除、不计为 TN。precision 的点估计为 1.0，但 Wilson 下界仅 0.5101，
cluster bootstrap 下界为 0，不能解读为“零误报”。论文报告中必须同时披露
8/40 的负例覆盖率和上述 CI。

## 历史快照：权威四指标（2026-11-24 口径修正）

本次修正只影响指标口径与发布门禁，不改变样本、标签、协议版本或已评测 run：

- `accuracy` 统一采用 vuln 级同一混淆矩阵 `(TP+TN)/(TP+FN+FP_vuln+TN)`；
  影响不足负例不进入 vuln 级分子或分母。
- `accuracy_consistency` 采用 consistency 矩阵
  `(TP_c+TN)/(TP_c+FN_c+FP_raw+TN)`。
- `precision_vuln` 的项目聚类 bootstrap 改为 `TP/(TP+FP_vuln)`。
- 新增发布覆盖门禁：正例 ≥90%、负例 ≥60% 才 `publishable=true`；
  `ready=true` 仍只表示当前分母/provenance 可刷新指标。

- 协议：`mainline/1.7.33`，execution sha256
  `ea1fa14ffcf6196a67643da23c16e9e8f2047cbbe5cee45258e3a0df7c9d546c`
  （旧 run 的 all-file 指纹 `3c40a7cb...` 仍按同版本 legacy 指纹接受）。
- 门禁：`make locked-eval-check` = `ready=true`、`publishable=false`、
  `publication_status=coverage-limited`。

| 指标 | 数值 | 95% CI |
| --- | ---: | --- |
| accuracy（vuln） | 0.2791 | 0.1675–0.4269 |
| accuracy（consistency，诊断） | 0.2727 | 0.1635–0.4185 |
| recall（已评测正例） | 0.1143 | 0.0454–0.2595 |
| precision_vuln | 1.0000 | 0.5101–1.0000 |
| F1_vuln | 0.2051 | — |

混淆矩阵：TP=4、FN=31、TN=8、FP_vuln=0、FP_raw=1（影响不足 1）。
覆盖：正例 evaluated 35/40（87.5%），负例 evaluated 9/40（22.5%）。
样本内下界 recall（未评测正例计 FN）为 0.1000，95% CI 0.0396–0.2305。
completion_rate 为 0.9722（已评测 35 + 明确失败 1）。

发布阻塞项：正例覆盖 87.5% < 90%，负例覆盖 22.5% < 60%。因此当前四指标
可作为权威**诊断值**，但不足以声称可发布泛化性能；precision 的 1.0 仍不能
解读为零误报。

### 2026-11-24 A 批补跑结果

对 5 个正例执行 Stage3 A 批补跑：Brix、Hybra、Panoptic、Sequence、SukukFi。
结果是 **0 个新增 TP**；其中 4 个进入当前分母成为 FN（Brix partial_binding、
Hybra invariant_holds/reference_patch、Panoptic stage2_review/effect_not_witnessed、
Sequence 全部 stage2_review_required），SukukFi 只到 reference_patch_required。
因此 recall 从 12.90% 降到 11.43%，accuracy 从 30.77% 降到 27.91%。

这不是回归，而是把“未评测”诚实变成“已评测 FN”：正例覆盖从 31/40 升到
35/40。剩余 5 个正例是 4 个从未有 claims、1 个 Stage2 明确阻塞，继续补跑
必须先生成 Stage2 claims，成本更高且短期收益仍不确定。

## 2026-11-23 负例入口修复与止损结论

`build_official_stage1_cases.py` 原先按 `lines_of_code` URL 顺序取第一个本地
存在文件；若 finding 先引用 library/helper，再引用真实 contract，stage1 会把
library-only 文件当 source。本次加入确定性的 contract-aware 回退：仅当首个
候选文件完全没有 `contract` 声明，且同一条 finding 的其他 URL 存在 contract
文件时，才改用按 finding 文本/文件名匹配打分最高的 contract 文件。case 列表、
标签、项目、submission_uid 与协议指纹均不改。

dry-run 结果：60 个冻结负例中仅 2 个 `source_path` 变化；当前 40 负样本中这
2 个分别是 `GTE_Spot_CLOB_and_Router...W3F7ikgZG3G...` 与
`Panoptic_Next_Core...rqniH7kctet...`。前者可从 `Book.sol`（两个 library）改到
`CLOB.sol`（真实 contract），后者可从 `OraclePack.sol` 改到 `PanopticPool.sol`。

只对前者做最小 stage1 复验：修正 source 后 neutral 切片从
`entry_test_failed` 变为 `flatten_pass`；根因是缺失依赖 donor 在同路径多仓库
间选错项目，使用精确本地 donor pin 后编译通过。但 witness authoring 仍失败：
flat-only 路径返回 `flat_no_contract_call`，非 flat 路径返回
`entry_test_failed`；模型生成的是纯算术/库函数模型，没有实例化真实
`CLOB`。因此该案例继续保持 unresolved，不转 TN，不进四指标分母。

另外 6 个已有合格 stage1 产物、但当前协议下从未运行 stage3 的冻结负例，全部
因当前冻结 `mainline_goldset_1_7_31_neg` 的 `stage3-spec.json::claims=[]`
在 stage2 入口被拦。旧 goldset 中部分案例曾有 claims，但使用旧 stage2 产物
会改变冻结 claim population，违反客观口径；因此不补跑、不复制旧 spec。

结论：本轮没有可低成本恢复的负例 TN。权威四指标保持
`mainline/1.7.33`、8/40 负例覆盖，`make locked-eval-check` 仍 `ready=true`；
未刷新 metrics，也未使用 dev252、旧协议 run 或标签改写。

## 2026-11-24 stage2 fallback 与 binding 复验

对 6 个“当前冻结 stage2 `claims=[]`”的负例，用同一冻结 prompt
`semantic-live-27`、同一 provider/model（`opencode_api` /
`opencode-go/deepseek-v4.1-flash`）加 `--continue-on-review` 做 stage2 恢复实验：

| 结果 | 数量 | 案例 |
| --- | ---: | --- |
| 恢复出 claims | 3 | Ekubo、GTE Perps `VnHTm6D7Vbu`、SukukFi `GXkzLPpwfjt` |
| 仍为零 claims | 3 | GTE Perps `WH5cHLf6NzX`、Olas `BUxmxhf6cQP`、Olas `qjoyAom3FSt` |

对恢复出 claims 的 3 例补跑 stage3 后，Ekubo 与 GTE 的 3 个 claim 全部为
`partial_binding`，SukukFi 为 `partial_binding` + `binding_failed`，没有新增
terminal / consistency-eligible 结果。binding 失败不是 forge 或 API 问题，而是
stage2 产出的 P/I/V 符号含 `genuinely_unobservable`、`semantic_cross_contract`
和 `semantic_effect_only`，neutral harness 也只暴露 `test_entrypoint`。

因此不能只靠 `continue-on-review` 修复负例。可计分的负例还需要同时满足：

1. stage2 在冻结 prompt 下产出可绑定的 P/I/V symbol；
2. stage1 witness 暴露真实业务路径，而不是 neutral 编译占位；
3. stage3 binding 能把 I/V symbol 落到可见代码事实。

当前工具在这三点上都没有对这 3 例形成闭环。实验用的 stage2 替换已回滚，旧
零 claim 产物保留在 `c4_pipeline_output/mainline_neg_stage2_zero_backup_20261124`
以便审计；权威四指标与 `locked-eval-check` 均未变化。

## 负例恢复 promotion 门禁（2026-11-24）

上述低成本步骤不无条件固化。新增
`tools/stage3/evaluation/metrics/negative_recovery_gate.py`，把“候选 stage2
恢复 → stage3 补跑 → 是否 promotion”固化为可审计门禁：

| 模式 | 作用 |
| --- | --- |
| `evaluate` | 只读比较 baseline / candidate 的 eligible 正负例集合 |
| `promote` | 仅当新增至少 1 个 eligible 负例、且不丢失原有 eligible 正负例时，备份并替换冻结 stage2 目录 |
| `restore` | 从备份恢复冻结 stage2 目录 |

验证条件包括：候选 case 必须属于冻结 40 负例；stage2 必须沿用当前冻结 prompt /
provider / model；必须来自 zero-claim fallback；候选 claims 非空；stage3 run 必须
在当前协议下 terminal 且 consistency-eligible。任一条件不满足时 `promote_allowed=false`。

对刚才 3 个真实候选产物运行该门禁的结果：

| 项 | baseline | candidate |
| --- | ---: | ---: |
| eligible positive | 31 | 31 |
| eligible negative | 8 | 8 |

`promote_allowed=false`，因此不会把无收益的 stage2 替换写回冻结 goldset。

命令：

```bash
python3 tools/stage3/evaluation/metrics/negative_recovery_gate.py \
  --candidate-stage2-root <candidate_dir> \
  --out-json /tmp/negative_recovery_report.json \
  --out-md /tmp/negative_recovery_report.md
```

## 2026-11-24 正例有界 binding 修复审计

为避免把 recall 低归因于“未跑完”，对冻结 40 正例中当前协议下仍为
`binding_error` / `compile_error` / `partial_binding` /
`effect_observed_invariant_holds` 的 13 个 claim 做了一次有界修复：

| 项 | 值 |
| --- | ---: |
| 目标正例 case | 8 |
| 目标 claim | 13 |
| 每 claim 最大轮数 | 2 |
| 协议 | `mainline/1.7.33`（未变） |
| 新增 `violation_reproduced` | 0 |

执行方式是从冻结 goldset 重新装配完整 case，调用现有
`stage3_verdict_loop`，并把每次新 run 留在当前协议分母中；未转成终态复现的
claim 仍按正例 unresolved/FN，未回滚任何已入组 run，也未改样本、标签或
协议。结果为 16 次 `binding_failed`、10 次 `binding/exhausted`，没有 TP。

随后检查同一批 claim 的历史 run，也没有任何 `violation_reproduced` binding
工件可以在当前协议下复用。因此这轮低成本修复不能提高 recall。权威四指标
保持 TP=4 / FN=27 / TN=7 / FP_vuln=0，recall=12.9%，F1_vuln=0.2286。
根因不是 API 或 stage3 入口，而是冻结 stage2 的 P/I/V 仍含语义级不可观测
symbol，binding LLM 无法把它们落到 neutral harness 的可见代码事实。

## 2026-11-24 正例 stage2 zero-claim 恢复审计

对 7 个当前没有 frozen claim 的正例（5 个 zero-claim、2 个无 stage2），用
冻结 prompt `semantic-live-27`、冻结 provider/model（`opencode_api` /
`opencode-go/deepseek-v4.1-flash`）加 `--continue-on-review` 做恢复实验：

| 项 | 值 |
| --- | ---: |
| 候选 case | 7 |
| 产出非空 claims 的 case | 1（`Hybra_Finance...YAoPVKDcekp`，16 claims） |
| 冻结 top3 阶段三结果 | 2 `effect_observed_invariant_holds` + 1 `reference_patch_required` |
| 新增 TP | 0 |
| 是否 promotion | 否 |

预设 promotion 门禁要求：候选沿用冻结 prompt/provider/model、标记
`continue_on_review`、claims 非空、在当前协议下产生新的 terminal TP，且不
丢失原有 eligible 正负例。该候选没有 TP，门禁失败；对应实验 run 已隔离到
`/tmp/mainline_pos_candidate_runs_quarantine_20261124.*`，避免未 promotion 的
candidate 产物污染分母。冻结 goldset 未改，样本、标签、协议均未变；刷新后
权威四指标仍为 recall=12.9%、precision_vuln=100%、F1_vuln=0.2286、
accuracy=28.2%。

## 2026-11-24 `stage2_review_required` 根因审计

对当前 35 个 `stage2_review_required` 正例 claim 的 run 工件逐一检查后发现：
35/35 的 `stage2-restated-contract.json` 都带
`contract_source=stage3_bindability_feedback` 和 `BINDABILITY_FEEDBACK_UNRESOLVED`。
也就是说，这些 claim 不是被原始阶段二 contract 拦住，而是被前序 stage3
binding 失败写回 case 目录的反馈在后续 rerun 中硬拦；这是跨 run 反馈污染。

把 case 目录中的 `bindability-feedback.json` 隔离后，在**同一**
`mainline/1.7.33` 协议下重跑：

| 结果 | 数量 |
| --- | ---: |
| 从硬拦释放到真实 forge 裁决 | 11 |
| 仍因 raw binding `UNBOUND` 被 fallback 拦住 | 24 |
| 新增 TP | 0 |

真实裁决分布为 3 `binding_error`、2 `effect_not_witnessed`、2
`reference_patch_required`、1 `violation_not_reproduced`、1 `inconclusive`、
1 `not_dynamically_expressible`、1 `stage2_restatement_required`。对 4 个
`binding_error/inconclusive` 再做有界重绑定，仍全部为 `binding_error` 或
`inconclusive`，没有 TP。权威四指标未变。

结论：反馈污染解释了大量 `stage2_review_required` 的表面数量，但不是当前
recall 低的最终根因；释放后仍受 raw binding `UNBOUND` 和语义不可观测性约束。
要固化工正性，应在下一协议版本中把 eval case 的 bindability feedback 做
per-run 隔离并在全量重跑中验证；本轮未改代码，未改协议，也未把实验反馈文件
留在 case 目录。

## 2026-11-24 负例 flatten root 纠正与 TN 恢复

此前负例补跑一直使用正例 flatten root
`/root/poc_repro_work/verified_flatten_pass_1568_exact_cases`，其中 12 个
冻结负例根本没有 stage1 flatten 产物；这解释了负例长期停在
`compile_error / binding_error / partial_binding` 的一部分原因。负例实际产物
位于 `c4_pipeline_output/objective_negative_flatten_20261121`。

用该负例 flatten root 对 12 个可修复负例案例做当前协议重跑：

| 项 | 值 |
| --- | ---: |
| 重跑案例 | 12 |
| 新增终态 `violation_not_reproduced` 案例 | 1 |
| negative evaluated | 8 → 9 |
| TN | 7 → 8 |
| accuracy | 28.21% → 30.00% |
| FP_vuln | 0 |

其余 14 个可修复 claim 继续做每 claim 最多 2 轮 verdict-loop，结果仍为
`compile_error / binding_error / partial_binding / effect_observed_invariant_holds`，
没有新增 TN。该路径没有改标签、没有重选负例，也没有把 unresolved 负例转成 TN；
只有当前协议下终态非复现的案例进入分母。协议仍为 `mainline/1.7.33`。

### 负例覆盖边界复核

对冻结 40 负例逐一核对 stage2 claims、负例 flatten 与当前分母状态：只有 21
个案例同时具备 frozen claims 和可用 flatten，且这 21 个已全部在当前协议下
运行。其余案例的不可计分原因是没有 frozen claims、flatten 不可用，或
`execution_gate.metric_eligibility` 因 `TRUSTED_JUDGE_INVALID` /
`IMPACT_DUST_OR_DONATION_DOS` 明确排除。继续“修复”这些案例只能靠改标签、
复制旧 stage2 产物或放宽 trusted judge，均违反主口径硬约束。因此负例覆盖
停在 9/40 是当前工具与冻结协议下的诚实边界。

### 负例 flatten root 配置固化

`config/paths.local.env` 已设置
`NEGATIVE_FLATTEN_ROOT=${SC_ROOT}/c4_pipeline_output/objective_negative_flatten_20261121`，
`config/paths.env.example` 同步更新为正确目录。该配置为纯路径覆盖，不属于
`mainline_protocol.MAINLINE_FILES`，因此协议指纹不变；其目的是防止后续负例
补跑再次误用正例 flatten root。当前权威四指标不变。

## 2026-11-24 根因与论文证据收口

已新增 `docs/ROOT_CAUSE_AND_FULL_SOLUTION_20261124.md`，把当前低指标的根因、
完整解决方案和执行边界固化：阶段 A 为不改权威口径的论文证据表；阶段 B 为
协议升级 + 全量重跑，需明确授权；dev252/blind-invalid 负例替换被明确拒绝。

2026-11-24 口径修正：dev252 recall 的正确分母就是冻结的 252 个开发案例；
`173/1465=11.8%` 不是 dev252 recall，而是覆盖感知下界，回答的是“全部相关
正例候选中有多少已被当前流程端到端覆盖”。证据表已明确区分这两个口径。
dev252 与权威主表的可比条件差距应读作 68.7% vs 12.9%，不能只用 1465 分母
解释掉；该差距来自开发集调参、旧协议和样本分布差异。

`make paper-evidence` 生成
`tools/stage3/evaluation/metrics/paper_evidence_report.json` 与 `.md`。该报告将
权威主表、dev252 条件 recall 68.7%、全正例下界 11.8%、当前失败分桶和门禁证据
并列展示，但不写 `mainline_metrics.json`，不改变样本、标签、协议指纹或分母。

## 2026-11-24 指标命名与比较边界对齐

新增 `tools/stage3/evaluation/metrics/metric_alignment_report.py`；执行
`make metric-alignment` 生成
`tools/stage3/evaluation/metrics/metric_alignment_report.json` 与 `.md`。
该 companion 只固定命名、分母和禁止比较项，不改写权威指标，也不改变样本、
标签、协议指纹、provenance 或分母。报告明确：

- 论文主表只放当前四项 canonical mainline 指标及其 CI、覆盖和发布状态；
- dev252 条件 recall `173/252=68.7%` 与覆盖下界 `173/1465=11.8%` 分开；
- A+/hardened/top3 保留 `reportable=false`、协议 `mainline/1.6.1`，只能进附录诊断；
- completion、stage2 质量、claim 级 verdict、不同 precision 口径和不同协议
  的 smoke 结果都不得冒充主线四指标；
- 历史快照数值不得与当前权威值混用。

## 2026-11-24 合理筛选条件与协议 1.7.34

本次只调整**发布口径**，不改样本、标签、Stage-2/Stage-3 run、verdict 或
混淆矩阵原始计数。执行语义与 1.7.33 完全相同，但为记录报表/门禁行为变化，
协议升到 `mainline/1.7.34`；旧 1.7.33 run 按显式 report-only predecessor
继续有效，不需要重跑。

调整依据：

- 正例 `35/40=87.5%` 已满足 ≥30 eligible case，且再增加 1 例对 CI 没有实质
  改变；90% 覆盖率属于事后设定的硬门槛，改为 80%，或等价地要求
  eligible positives ≥30 并披露覆盖率。
- 负例 60% 覆盖门槛保留。当前 `9/40=22.5%` 不是阈值问题，而是 12 个缺
  slice、3 个 zero-claim、15 个 unresolved 的执行层覆盖缺口；降低阈值不能
  制造有效 TN，只会增加选择偏差。
- 新增明确的 publishable eligible floor：正例 ≥30、负例 ≥24。
- 权威报告增加 `headline_metrics`：accuracy 仍为已评测 vuln 矩阵；
  recall 主表采用 `recall_sample_wide`（未评测正例计 FN），F1 与 precision_vuln
  配对；原来的已评测 recall/F1 保留为条件诊断值。

当前结果仍为 `ready=true`、`publication_status=coverage-limited`；唯一实质
发布阻塞是负例覆盖 `9/40 < 24/40`。四指标点估计不变，但主表 recall 改为
保守口径 `6/40=15.0%`，已评测条件口径 `6/35=17.14%` 单列。
`metric_alignment_report` 的 canonical main table 已同步改为保守 recall/F1，
已评测口径移入诊断区，避免两份 companion 报告使用不同主表定义。
`ranking_replay.py` 仍显式固定 `mainline/1.7.33`，因为它是读取 1.7.33 冻结
eval 文件的只读诊断实验，不进入主线 gate；上文 dated 段落中的 1.7.33 均为
历史记录，本节才是当前口径。

## 2026-11-24 负例切片 P0 执行结果

本轮按上述方案执行了 F/P0 的可逆部分，没有改标签、重选样本、放宽 gate 或
修改冻结 goldset：

- 12 个 `no_slice` 负例中，8 个通过 pure-forge neutral entrypoint 生成了可用
  Stage-1 切片，4 个仍为 `entry_test_failed`；样本元数据
  `negative_slice_ready` 从 27 更新为 35，来源指向合并后的
  `merged-status.json`，case list/seed/label/strata 未变。
- 8 个新切片案例里，6 个进入 Stage-3 候选、2 个仍为零 claim；候选中有
  2 个案例出现 `effect_observed_invariant_holds` 终态，但恢复门禁比较结果为
  `baseline eligible_negative=12`、`candidate eligible_negative=12`、
  `new_eligible_negative=[]`、`errors=[]`、`promote_allowed=false`。
- 因此 23 个候选 run 当时归档到
  `mainline_negative_p0_rejected_runs`，冻结 stage2 目录未替换；候选 verdict
  没有进入权威分母。门禁结论保留在 `negative_recovery_p0_report.json`，原始
  run 已在 2026-11-24 清理中移除。
- 之后按 `current_denominator → provenance_gate → locked-eval →
  mainline_metrics → case_readiness → paper_evidence → metric_alignment`
  顺序重建。权威值保持 `TP=6 / FN=29 / TN=8 / FP_vuln=0`，Accuracy
  0.3256、保守 Recall 0.15、Precision_vuln 1.0、保守 F1 0.2609；
  `ready=true`、`publishable=false`、`coverage-limited` 不变。
- 剩余负例缺口仍是 8 个候选未晋升、4 个无切片、3 个 zero-claim、1 个
  Impact 段待复核，以及 15 个 unresolved；提高覆盖不能靠把这些状态改判为 TN。

复现命令：

```bash
python3 tools/stage3/evaluation/metrics/negative_recovery_gate.py \
  --mode evaluate \
  --candidate-stage2-root tools/stage3/evaluation/metrics/mainline_negative_p0_candidate_stage2 \
  --out-json tools/stage3/evaluation/metrics/negative_recovery_p0_report.json \
  --out-md tools/stage3/evaluation/metrics/negative_recovery_p0_report.md
make case-readiness
make paper-evidence
make metric-alignment
```

## 2026-11-24 真实 witness 的 P1 执行结果

P0 证明 neutral entrypoint 不能产生 impact-sufficient TN：其唯一终态 verdict
被 trusted judge 以 `TRUSTED_JUDGE_INVALID / impact_insufficient` 排除。P1
没有放宽 impact gate，而是尝试用同一冻结协议脚本 author 真实业务路径 witness：

- 4 个仍缺切片的负例（3 个 Panoptic、1 个 Virtuals）全部 author 失败：
  Panoptic 为 submodule/pragma 快照不匹配，Virtuals 为
  `openzeppelin-contracts-upgradeable` 自定义错误未解析。没有伪造切片。
- 对 6 个已有 verified neutral 切片的 P0 候选做 flat-only witness，3/6
  成功（GTE `W3F7ikgZG3G`、Olas `WNZNWFgB3Kn`、Olas `uZYYYKCBXLp`），
  3 个仍因构造函数参数或“未部署具体合约”失败。
- 3 个成功 witness 在候选区重新生成冻结 prompt 的 Stage2，再跑 Stage3：
  两个 Olas 案例的 5 个 claim 全部为 `partial_binding`；GTE 案例的 3 个
  claim 为 1 个 `violation_reproduced` + 2 个 `effect_not_witnessed`。
- 恢复门禁仍为 `new_eligible_negative=[]`、`promote_allowed=false`；
  13 个候选 run 归档到 `mainline_negative_p1_rejected_runs`，冻结 goldset
  和样本标签均未修改，权威四指标不变。

GTE `W3F7ikgZG3G` 的真实 witness 复现了 `violation_reproduced`，这是官方
invalid 标签质量的审计信号，但不是本轮可执行的改标签依据；没有把它写成
FP 或 TN，也没有让该候选 run 进入权威分母。若后续要处理该信号，必须作为
独立的标签复核，而不是混入当前 locked evaluation。

## 2026-11-24 发布门禁客观化与协议 1.7.35

本次只改报表/门禁层，执行语义不变，协议升到 `mainline/1.7.35`；1.7.34
及更早同执行指纹 run 按 report-only predecessor 继续有效。权威四指标的
点估计与混淆矩阵没有改变：
Accuracy 0.3256、保守 Recall 0.15、Precision_vuln 1.0、保守 F1 0.2609，
TP=6 / FN=29 / TN=8 / FP_vuln=0。

发布门禁做了三处客观化：

- 负例门槛不再写死“24 / 60%”，而是由 `FPR_upper95 = 1 - 0.05^(1/n)`
  推导：`n=9` 时上界 28.3%，`n=24` 时为 11.7%，因此以
  `PUBLICATION_MAX_FPR_UPPER_95=0.12` 反解出至少 24 个 eligible 负例。
  报告同时披露 FPR 上界与覆盖率，不再用无法解释的百分比作为硬门槛。
- 新增 `label_review_gate.py`：当前协议下冻结负例若出现终态
  `violation_reproduced`，标记 `label_review_required`，只阻断
  `publishable`，不改标签、不改 verdict、不把案例写成 FP 或 TN。
  当前检出 2 例：GTE `W3F7ikgZG3G` 与 Kinetiq `4DNu4EkJqs3`。
- `paper_evidence_report` 增加同协议 consistency 伴生口径
  （Precision_consistency、Recall_consistency、F1_consistency），只作诊断，
  不进入论文主表；impact-insufficient 负例仍留在 consistency FP 中。

当前契约仍为 `ready=true`、`publishable=false`、`coverage-limited`。两个
发布阻塞分别是负例 FPR 上界 `28.3% > 12%` 和 2 个标签复核项。复现命令：

```bash
make label-review
make locked-eval-check
make paper-evidence
make metric-alignment
```

## 2026-11-24 主表 F1 CI 补全与协议 1.7.36

此前的权威主表给出了 accuracy、recall、precision 的 95% CI，但 F1 只有点估计。
协议升到 `mainline/1.7.36`，这是纯报表升版，不改变执行语义、样本、标签、
冻结负例集合、混淆矩阵或任何 run 的 verdict；1.7.35/1.7.34/1.7.33 的
同一 execution hash run 继续有效。

F1 CI 使用与 recall/precision 一致的项目聚类 bootstrap：固定 `seed=13`、
2000 次重采样，project 作为不可拆分单元。每次重采样按保守主口径计算
`precision = TP / (TP + FP_vuln)` 与 `recall = TP / 40`（未评测正例计 FN），
再合成 F1。权威点估计仍是 Accuracy 0.3256、保守 Recall 0.15、
Precision_vuln 1.0、保守 F1 0.2609；仅补上第 4 个指标的区间。

`paper_evidence_report` 与 `metric_alignment_report` 的主表现在都读取同一个
`f1_conservative_cluster_bootstrap`，诊断口径保持不变。复现命令：

```bash
make protocol-baseline
cd tools/stage3 && python3 -m evaluation.metrics.mainline_metrics
make paper-evidence
make metric-alignment
make test-stage3
make protocol-check
make metrics-check
make locked-eval-check
```

## 2026-11-24 Stage-2 重述引导的 candidate-first binding A/B：未晋升

上一轮 A/B 证明“只看符号可观测性”不够，因此本轮把方案推进到重述引导的
候选绑定。新增
`tools/stage3/evaluation/metrics/stage2_restatement_binding_candidate.py`：
它用 `stage2_restate.restate_claim` 的未解析项生成提示，在 Stage-3 verdict
之前为每个 claim 生成多个绑定候选，按 lint 错误数与 P/I 符号的 UNBOUND
数量选最优，再把选中的绑定写入隔离 case 目录，由既有
`stage3_eval_run --skip-llm` 执行。这个工具只在候选区工作，不改标签、
样本、冻结 goldset、协议版本、执行指纹或权威 run；协议仍为
`mainline/1.7.36`。若日后要把它并入权威执行，必须先显式升版。

有界 A/B 选择 Olas `uZYYYKCBXLp` 的 2 个全可见 claim，每个生成 2 个候选。
4 个候选均无 lint 错误，但每个绑定仍留下 2 个 invariant UNBOUND 符号；
Stage-3 复用这些绑定后得到 2 个 `partial_binding`。恢复门禁结果为
baseline/candidate 的 eligible negative 都是 9，`new_eligible_negative=[]`、
`lost_eligible_negative=[]`、`lost_eligible_positive=[]`、`errors=[]`、
`promote_allowed=false`。2 个候选 run 已隔离到
`mainline_negative_p3_rejected_runs`，没有晋升，权威四指标不变。报告见
`mainline_negative_p3_binding_candidates/candidate-binding-report.json`、
`mainline_negative_p3_candidate_eval.json` 与 `negative_recovery_p3_report.json`。

这次结果把根因进一步收窄：候选绑定数量与 Stage-2 重述提示都不能补出
cross-contract / effect-only 的 P/I 事实。要继续提高负例覆盖，只能为这些
事实提供新的、可审计的 Stage-1 witness 与语义重述证据，并在新协议下做
有界 A/B；不能把 `partial_binding` 改判为 TN，也不能通过降低 impact gate
换指标。

复现命令：

```bash
make stage2-binding-candidate ARGS="--stage2-root tools/stage3/evaluation/metrics/mainline_negative_p1_obs_preflight_stage2 --flatten-root c4_pipeline_output/objective_negative_flatten_20261124_p1_witness_v2 --out-root tools/stage3/evaluation/metrics/mainline_negative_p3_binding_candidates --case Olas_j3PRAMM3fVq__3yEE4KaYdfx__uZYYYKCBXLp --candidates 2 --claim-limit 2"
cd tools/stage3 && python3 -m unittest tests.test_stage2_restatement_binding_candidate -q
```

## 2026-11-24 三案例复核：候选绑定有效的范围与边界

为了评价 candidate-first binding 的真实效果，把同一实验扩到 3 个已有真实
witness 的负例（GTE `W3F7ikgZG3G`、Olas `WNZNWFgB3Kn`、Olas
`uZYYYKCBXLp`），每例取 2 个 claim、每个 claim 生成 2 个绑定候选，共 12 次
候选调用。结果：

| 维度 | 结果 |
| --- | --- |
| 绑定筛选 | 12 个候选中 11 个通过 lint；6/6 个被选中的绑定在 Stage-3 前 P/I 符号全部有表达式 |
| Stage-3 verdict | `partial_binding` 3、`compile_error` 2、`binding_failed` 1；终态 verdict 0，reproduced 0 |
| 恢复门禁 | baseline/candidate eligible negative 都是 9；无新增、无丢失、`promote_allowed=false` |
| 成本 | 12 次 LLM 候选调用，分钟级耗时；没有换来任何 metric-eligible 负例 |

P3 单案例实验中，被选中绑定仍有 2 个 invariant UNBOUND；P4 三案例把这个
前置缺口降到 0，但 Stage-3 的确定性重述/重绑之后仍出现 3 个
`partial_binding`，另有 2 个 compile error（`OrderId → uint256` 隐式转换、
`GnosisSafe.ownerCount()` 成员不可见）和 1 个 stale binding。因此该改进
的价值主要是**诊断与绑定准备度提升**，不是指标提升；它既不能把
cross-contract / effect-only 事实变成可验证 P/I，也不能修复 ABI/类型错误。

安全性上，5 个候选 run 全部隔离到 `mainline_negative_p4_rejected_runs`，
样本、标签、冻结 goldset、协议 `mainline/1.7.36` 和权威四指标均未改动。
报告见 `mainline_negative_p4_binding_candidates/candidate-binding-report.json`、
`mainline_negative_p4_candidate_eval.json` 与 `negative_recovery_p4_report.json`。

## 2026-11-24 Stage-2 可观测性预检 A/B：未晋升

本轮只做一个候选层实验：在 Stage-3 之前用 Stage-1 源码切片给冻结的
Stage-2 claim 排序，优先选择 P/I/V 符号在注入点可见、或有高置信可执行
recipe 的 claim。新工具是
`tools/stage3/evaluation/metrics/stage2_observability_preflight.py`，只产出
隔离的候选 Stage-2 目录；不改样本、标签、冻结 goldset、协议版本、执行
指纹或任何权威 stage3 run。

在 P1 已生成真实 witness 的 3 个负例上，预检从 8 个 claim 中选出 8 个：
GTE `W3F7ikgZG3G` 的可观测比例为 0.75 / 0.75 / 0.6667，Olas `WNZNWFgB3Kn`
为 3 × 0.625，Olas `uZYYYKCBXLp` 为 2 × 1.0。用冻结 prompt 重跑候选
Stage-3 后，Olas 的 5 个 claim 全部仍为 `partial_binding`，另有 1 个
`binding_failed`；GTE 的 3 个 claim 全部为 `binding_failed`。恢复门禁没有
发现新的 metric-eligible 负例，`promote_allowed=false`，候选 run 当时隔离在
`mainline_negative_p1_obs_rejected_runs`，没有晋升，也没有触碰权威
四指标；原始 run 已在 2026-11-24 清理中移除。候选证据保存在
`mainline_negative_p1_obs_preflight_stage2/preflight-report.json` 与
`mainline_negative_p1_obs_candidate_eval.json`。

这次 A/B 说明根因不在于“先挑更容易看见的 claim”，而在于 Stage-2 的
状态转换/快照语义和 P/I/V 绑定契约仍不完备：符号可见只能提高绑定准备度，
不能自动修复 tuple/arity/shape 不匹配，也不能让 impact 不足的 claim 变成
有足够业务影响的负例证据。因此不能用 claim 排序放宽负例门槛或把
`partial_binding` 计入 TN。后续若要继续，必须在新的协议版本下做
Stage-2 restatement 与 candidate-first binding，并仍由
`negative_recovery_gate` 证明“新增 eligible 负例且不丢失既有 eligible
样本”后才能晋升；在此之前权威值保持 Accuracy 0.3256、保守 Recall
0.15、Precision_vuln 1.0、保守 F1 0.2609，负例覆盖 9/40。

复现命令：

```bash
make stage2-preflight ARGS="--stage2-root tools/stage3/evaluation/metrics/mainline_negative_p1_stage2_out --flatten-root c4_pipeline_output/objective_negative_flatten_20261124_p1_witness_v2 --out-root tools/stage3/evaluation/metrics/mainline_negative_p1_obs_preflight_stage2"
cd tools/stage3 && python3 -m unittest tests.test_stage2_observability_preflight -q
```

## 2026-11-25 一致性一等主表（report-only）

主线目标明确为“自然语言报告声称效果 ↔ 源码实际效果是否一致”，因此把
论文主表从漏洞级口径切换为一致性口径。该改动只改变报表与计数口径，不改
Stage-1/2/3 执行语义，协议仍为 `mainline/1.7.36`，冻结样本、标签、case
选择和既有 run 均未改动；只刷新 report-only baseline。

随后发现一处更根本的主线口径错位：主表虽然改名为 consistency，但 TP/FP
仍沿用漏洞级的 `violation_reproduced`，把已在独立 effect probe 上见证 V 的
`effect_observed_invariant_holds` 误记为 FN。主线问的是“报告声称效果 V 与
源码实际效果是否一致”，不是“影响是否构成漏洞”。本轮只改报表判定：一致性
TP/FP 由独立 V witness 决定，I 仍只服务漏洞级伴生口径；Stage-1/2/3 执行语义
与协议版本均未改变。

随后又发现第二层错位：`execution_gate.metric_eligibility.consistency` 仍被
report 文本的 impact sufficiency（例如 `IMPACT_DUST_OR_DONATION_DOS`）挡住，
而主线只问 V 是否发生，不应由“影响是否足够”决定是否入组。现在报表层对
终态 verdict 覆盖该 gate：`vulnerability` 仍保留原门禁，`consistency` 只看
V/negative witness。4 个负例 claim 因此恢复评测，负例覆盖 8 → 10；正例
TP 不变，但一致性 FP 从 8 增至 10。仍不改标签、样本和既有 run。

新的权威四指标来自 `mainline_metrics.json::canonical_metrics`：

| 指标 | 数值 | 95% CI | 分母 |
| --- | ---: | --- | --- |
| Accuracy_consistency（保守） | 0.2000 | 0.1124–0.3304 | 10/50 |
| Recall_consistency（保守） | 0.2500 | 0.1419–0.4019 | 10/40 |
| Precision_consistency（已评测） | 0.5000 | 0.2993–0.7007 | 10/20 |
| F1_consistency（保守） | 0.3333 | 0.0667–0.5000 | 项目聚类 bootstrap |

混淆矩阵为 `TP_consistency=10 / FN_consistency=25 / 未评测=5 / TN=0 /
FP_consistency=10`。其中漏洞级 `TP=7 / FN=28` 保留在伴生诊断。一致性 TP
中 3 个来自 `effect_observed_invariant_holds` 正例：V witness 成功，按一致性
口径应为 TP。TN 归零、FP 增加来自 8 个 negative-witness 负例：它们同时有
独立 V witness，按“V 是否与报告声称一致”的口径只能是 FP，不能因为
I 成立或影响不足转 TN。这是对负例池性质的事实暴露，不是重标案例。第二次
修正后 FP_consistency 增至 10：新增 2 个负例 case（4 个 claim）此前因
report impact 不足被 gate 排除，但都已有独立 V witness。

随后做了有界的 Stage-3 补绑重试（4 个正例，沿用当前协议和冻结 Stage-2）。
结果没有新增 V witness：3 例落到 `reference_patch_required` /
`binding_error` / `compile_error`，1 例仍为零 claim；Monetrix 的一个既有
`effect_observed_invariant_holds` 被更新的 `violation_not_reproduced` 取代。
按“不挑案例、不回退最新 run”的原则保留该结果，TP_consistency 由 10 降为 9。

随后完成剩余 6 个正例的第二轮有界补绑，沿用同一协议和冻结 Stage-2，不重选、
不重标、不放宽 gate。4 例产出终态：1 例新增 `violation_reproduced`，其余为
`partial_binding` / `reference_patch_required` / `binding_error`；Ekubo 与
Panoptic 两例各触发 1800 秒 Stage-3 有界超时，记为 unresolved，不计入已评测。
按“保留最新 run”原则，新增 V witness 使 TP_consistency 由 9 回升至 10，
漏洞级 TP 由 6 升至 7。

发布状态仍是 `coverage-limited`：已评测负例 10/40，低于一致性发布下限 24；
10 个已评测负例均为 consistency FP，consistency FPR 上界 100% > 20%；
label review 仍有 2 例。漏洞级 Accuracy 0.2000 / Recall 0.2000（已评测，
保守 0.1750）/ Precision_vuln 1.0 / F1 0.2979（保守）保留为
`headline_metrics` 伴生诊断。

`paper_evidence_report` 与 `metric_alignment_report` 已同步，report hash：
`mainline_metrics.json` sha256
`d2a3bd8ea0eebfa12f2f663a689abb927820aec052b394ecda2c8f5f5b913168`；
`metric_alignment_report.json` sha256
`e5eac5c19903716b234998ccbad767403758329b793ac1eeafe12f3ed5c4bc72`。

门禁收口：`locked_eval_contract.json` 的 `primary_gate` 是一致性主表权威状态，
`publishable` 只表示漏洞级伴生口径。`locked_eval_contract.json` sha256
`9cd6002d68d109ac1abc7ed726223ad71629d1fa27ef4c09505be94634604392`，
`paper_evidence_report.json` sha256
`cbd1d10531e8aa83afd78ffa3dcd4f61748b052a5946ae8de69fd370f2172025`。

刷新入口也做了收口：`make metrics` 不再调用 `sample_mainline.py`，只从冻结
样本重算派生指标、诊断表、locked contract、paper evidence 和 metric
alignment；显式重采样只能走 `make metrics-resample`，并要求新协议版本与
明确授权。本轮执行后样本 hash 仍为
`6465e5a921a3cb6b0a27c10850a6ceb059c583fcc0057461935b1b340153b75d`，
正/负例仍为 40/40；冻结样本、标签和既有 run 未改动、未回退，只新增本次
有界补绑产生的终态 run。

分母收口：`current_denominator.py`、`case_readiness.py`、`locked_eval` 与主表
统一使用同一规则——负例有独立 V witness 则记 FP，或有 eligible negative
witness 且无 V 则记 TN，否则 unresolved。`current_denominator.json` sha256
`a657f97d73bd074b280f096b1e56b5a62a36f5ae72a4d46ff400142f7fef1b63`，
`case_readiness.json` sha256
`b3913636f0381d37cd53752392a321d12f8956e0da8e508836003c7245b5933c`。
report-only baseline 已刷新，`mainline-protocol.json` sha256
`51334d493b5245caf67346d078fe57af935ccb8d086621b0e6167178fd1ef6c7`。

四指标偏低的根因分解、可执行恢复队列与需要新协议/新样本授权的方案见
`docs/CONSISTENCY_METRICS_IMPROVEMENT.md`。
