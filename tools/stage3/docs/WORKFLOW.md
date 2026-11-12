# 阶段三工作流：先跑通，再自动化

## 主线（7 步）

1. 载入阶段二 run 目录，校验 `stage3-spec.json` / `constraints.json` /
   `formalization.json`。
2. 载入并校验 `binding.json`：`binding_contract` 中每个 `appears_in` 非空的
   符号都必须有代码侧绑定。
3. 代码生成：把 claim 的 P/I/V AST 翻译成 Solidity 布尔表达式。
4. 打补丁：`case/patched/` 存在则原样使用；否则按 `binding.patch` 自动注入。
   P 只作 I 的作用域，不写成无条件 `require`。
5. Foundry 差分：同一套测试分别跑 `original/` 与 `patched/` 两个工程。
6. 差分判定：把测试结果转成四个代码查询结果
   （`P_and_T` / `P_and_T_and_not_I` / `P_and_T_and_V` / `P_and_T_and_not_V`）。
7. 回填：调用阶段二 `ingest_feedback()`，落盘 `stage3-consistency.json`。

## 里程碑

- M0 骨架：已完成。
- M1 手工跑通：`smoke_vault` 使用参考补丁跑通，已完成。
- M2 脚本化：`cli/stage3_pipeline.py` 串联 7 步，已完成。
- M3 案例覆盖：`access_control`（地址/布尔）与 `mint_supply`（数值）已跑通。
- M4 自动化：AST 自动注入已实现，支持数值/地址/布尔快照、`P → I` 断言，
  以及多文件/多函数/合约作用域注入，已完成。
- M5 收口：真实 code4rena 案例 `panoptic_builder_init` 已端到端复现；
  新增 `stage3_assemble` / `stage3_batch` / `pipeline` 通道，进行中。
- M6 自动化闭环：注入点重构、合约作用域 lint、编译失败诊断 + 确定性
  snapshot 重定位、多轮绑定修复（`stage3_eval_run --max-binding-rounds`）、
  裁决闭环（`stage3_verdict_loop`）与验收门（`stage3_acceptance`）均已落地。
- M7 全流程自动化：`stage3_autorun` 一条命令串起 eval -> 裁决闭环 -> 验收门；
  UNBOUND 符号在注入/编译前 fail closed，产出带 `unbound_symbols` 的
  `partial_binding`，不再伪造常量绑定。
- M8 可观测性反馈：`binding_skeleton` 为每个符号计算 `observability`
  （`high`/`medium`/`low`），`binding_llm` 把该评分注入 prompt，低评分符号
  优先返回 `UNBOUND`，避免虚构标识符导致的无效重试；eval-run 汇总
  `unobservable_symbols` 供阶段二闭环回传。
- M9 编译阻塞分类：pipeline 区分 `compile_blocked`（原始切片编译失败，
  阶段一 flatten 问题，不可通过改绑定修复）与 `compile_error`（仅补丁编译
  失败，绑定问题，可修复）。裁决闭环对 `compile_blocked` 直接跳过不重试。
- M10 作用域感知可观测性（P5）：`solidity_scan` 新增
  `contract_visible_state_vars`（继承闭包内可见状态变量）与
  `poc_test_contract`（定位 PoC 测试合约）；`binding_validate` 的合约作用域
  判定改用继承闭包，修复“继承基类（如 `C4PoCTestbed`）状态变量被误判为
  跨合约”的问题；`binding_skeleton` 的候选标识符按注入合约作用域过滤，
  跨合约标识符不再作为候选。表达式扫描器跳过科学计数法（`1e18`/`1000e18`）
  与十六进制字面量，修复 `e18` 被误判为未声明标识符。
- M11 PoC 未执行分类：pipeline 在 exploit 测试未出现在 forge 输出（典型
  是 `setUp` 失败）时产出 `inconclusive` 并记录失败原因，不再以
  `SystemExit` 崩溃，避免 verdict 被置空。
- M12 注入点锚定与不崩溃（P6）：`solidity_scan` 新增 `poc_test_function`
  （发现 PoC 测试合约 + 测试函数名）与 `contract_has_function`；
  `binding_llm` 用发现的注入点强制覆盖 LLM 编造的 `patch.contract` /
  `patch.functions[].name` / `probe.contract` / `probe.exploit_test`；
  `binding_validate` 前置校验 patch 函数与 exploit 测试真实存在，把
  “补丁目标不存在”从 forge/patch 崩溃提前到 lint 可修复；
  pipeline 捕获 `SpecError` 产出 `binding_error`（可修复重试）而非崩溃，
  消除 50 案例中 31.6% 的 null 判定。
- M13 partial_binding 归因与定向补绑（P1）：`propose_binding` 对每个
  UNBOUND 符号回传 `unbound_detail`（observability + candidates）；新增
  `existing` 定向补绑模式，只重绑 UNBOUND 符号、保留已绑定部分；
  `solidity_scan` 候选池从「全部标识符」收紧到「可观测运行时值」
  （状态变量 / 函数参数 / 可调用函数），排除常量/枚举/结构体等类型名。


## 动态判定的边界

- 原始切片编译失败 → `compile_blocked`（切片/flatten 问题，不重试绑定）。
- 原始编译通过、补丁编译失败 → `compile_error`（绑定问题，可修复重试）。
- 原始通过 + 补丁在 I 断言失败 → `violation_reproduced`。
- 原始失败 + 补丁通过 → 不采信为“漏洞成立”，标 `unknown/inconclusive`。
- 两者都通过 → `violation_not_reproduced`（仅限给定测试范围）。
- 两者都失败 → `unknown`；补丁在 P 失败时解释为绑定错误。
- 安全路径在补丁上通过 → `P_and_T_and_not_V = sat`。
- M14 复合表达式绑定与汇总判空（P1.5）：`binding_llm` 系统提示加入
  复合表达式规则与第三个 few-shot（函数调用 + 比较 + getter 链等），
  使语义级不变量（如 `_extractValidUntil(sig) < block.timestamp`）可被
  绑定，而不再要求单一标识符；`stage3_multi` 抽取 `_dig` 安全取值，
  修复 `forge.exploit` 为 `None`（`binding_error`/`compile_blocked`）时
  整批汇总崩溃、`stage3_eval_run` 的 `verdicts` 因此置空的问题。

## P1.5 复测结论（5 个 Intuition 案例）

- 可绑定率从修复前的 0%（null/partial）提升到 93.3%（14/15 claim）。
- 但终局 verdict 仍是 0 复现：`compile_error` 8、`partial_binding` 6、
  `violation_not_reproduced` 1。
- 失败模式从「绑不上」上移到「绑上后无法编译 / 仍是部分绑定」，且出现
  跨合约符号（如 `SIG_VALIDATION_SUCCESS` 属于非注入合约）被 lint 拒绝。
- 结论：P1.5 提升表达力但未提升复现率，主瓶颈已不在绑定提示词，而在
  阶段二 PIV 的语义范围跨越单一注入合约、与 flatten 后代码不对齐。
- M15 文件级常量跨合约误报修复（P1.6a）：`solidity_scan` 新增
  `file_level_state_vars`，识别 flatten 文件顶层 `uint256 constant X = ...`
  等合约外声明；`binding_validate` 对这类标识符跳过跨合约检查。修复
  `SIG_VALIDATION_SUCCESS` 被误判为「PoCCore 外状态变量」导致
  `binding_exhausted` 的问题。实测 case1 从 1 bound + 1 binding_exhausted
  变为 2 bound。
- M16 汇总判空（P1.6a）：`stage3_multi` 抽取 `_dig` 安全取值，修复
  `forge.exploit` 为 `None` 时整批崩溃、`stage3_eval_run` 的 `verdicts`
  置空（详见 M14 备注）。

## P1.6a 复测结论（Intuition case1）

- 文件级常量修复后，binding 不再 exhaustion：2 claim 全部 bound。
- 但终局 verdict 转为 2 个 `compile_error`：不变量引用的函数
  `_extractValidUntilAndValidAfterFromSignature` 定义在 `AtomWallet` 合约，
  而注入点仍被 P6 锁死在 PoC 测试合约 `PoCCore`，跨合约函数在 forge
  编译期才失败（lint 只校验状态变量跨合约，不校验函数）。
- 根因收敛：阶段二 PIV 的语义不变量跨合约，阶段三当前仅支持单合约注入。

## P1.8 注入点迁移（已完成 P1.8a，发现语义天花板）

- M17 P1.8a：`binding_llm` 解耦 `patch` 与 `probe`——`probe` 仍锚定 PoC 测试
  合约/函数；`patch.contract`/`patch.functions[0].name` 允许指向持有不变量
  符号的业务合约，仅当 LLM 编造的目标不存在时才回退到 PoC。系统提示同步
  更新 PATCH/PROBE RULES。
- M18 归属查询辅助：`solidity_scan` 新增 `function_owner` / `state_var_owner`
  （返回声明该函数/状态变量的合约集合，`None` 表示文件级），供后续确定性
  注入点迁移使用。
- 实测 Intuition case1：绑定表达式已不再退化为 `true`，但 patch 仍停在
  `PoCCore`（LLM 未选业务合约），跨合约函数 `_validateSignature` 在 forge
  编译期才失败；自动迁移尝试因「嵌套函数调用提取不完整 + 函数名继承歧义」
  而回退。
- **关键发现（语义天花板）**：Intuition 的不变量是「时间窗口应被签进 hash」
  的 *should-be* 语义——当前代码根本不计算该值，注入 `assert(I)` 无处可观察。
  这类漏洞只能用 M1 参考补丁（`case/patched/`）验证，自动 assert 注入只能
  覆盖「代码已计算的可观察状态不变量」（如 panoptic 访问控制）。

## P1.8c 可表达性分类与路由（根因修复，非样本表象修复）

- 根因：阶段三把两类 claim 混用 `assert(I)` 处理——「代码已计算的可观察
  不变量」（`observable_assertable`，可动态验证）与「报告说应该如此但代码
  根本没计算该值」（`should_be_reference`，无论怎么重绑/迁移都不可复现）。
  旧的 `verdict_loop` 把 `compile_error` 一律当「可修复」无限重绑，产生噪音
  且污染评测（把「无法表达」错报为「编译错误」）。
- M19 `lib/expressibility.py`：新增确定性可表达性分类层，复用
  `binding_validate.lint_binding` 已有的源可见性分析，输出
  `expressible / cross_contract_reference / unobservable / binding_error`。
  - `cross_contract_reference`：不变量引用注入点可见闭包之外的函数/状态变量
    → 标记 `reference_patch_required=true`（需 M1 参考补丁），不重绑。
  - `unobservable`：符号无代码锚点（`UNBOUND`、未声明标识符）→ 不重绑。
  - `expressible`：无跨合约/未声明问题，走正常差分断言路径。
- M20 `verdict_loop.py`：新增终态 `not_dynamically_expressible`（`skip`，不重绑）；
  `repair_hint` 输出阻塞符号。
- M21 `stage3_pipeline.py`：在 forge 前计算 `expressibility`；当原始切片编译通过
  但补丁失败且 `dynamically_expressible=false` 时，verdict 改为
  `not_dynamically_expressible` 并跳过 compile-retry 黑名单重试；成功路径也
  记录 `expressibility` 供评测分层。
- M22 `stage3_eval_run.py` / `stage3_acceptance.py`：新增
  `not_dynamically_expressible` 统计与 `not_dynamically_expressible_total`，
  让评测暴露「动态验证真实天花板」，不再让 `compile_error` 淹没有效努力。
- 实测：Intuition `dos_via_expired_window` 由 `compile_error` 改为
  `not_dynamically_expressible`（2 个跨合约符号 `_validateSignature`）；
  `smoke_vault` 仍正常输出 `violation_reproduced`。
- 后续：`cross_contract_reference` 类走 M1 参考补丁路径（`case/patched/`），
  `unobservable` 类标记为「代码不可观察、无法动态验证」。

## P1.9 确定性锚点解析与可绑定性通道（根因修复，P1.8b/P1.9 合流）

- 根因：阶段二只读报告、不读代码，其 P/I/V 符号是「报告语义抽象」（如
  `c331795dd_time_window_bound_to_owner_signature`），阶段三必须把抽象符号映射
  回具体 Solidity 标识符与注入合约。此前这一映射交给 LLM 自由猜测，是
  ambiguous（25.4%）、cross-contract、unbound 三类失败的共同根因。
- M23 `lib/anchor_resolver.py`：新增确定性锚点解析器，复用
  `binding_skeleton._candidate_analysis` 的 token 重叠候选打分，但只保留
  「已声明的函数/状态变量」强候选（丢弃合约名、custom-error 名、参数名），
  并用 `function_owner`/`state_var_owner` 解析每个候选的归属合约，最终把每个
  claim 归为 `single_anchor / multi_contract / file_level / no_anchor`，
  并给出 `suggested_patch_contract`。该分类是动态可表达性的确定性上界：
  只有 `single_anchor`/`file_level` 能走 `assert(I)` 注入；`multi_contract`
  需 M1 参考补丁；`no_anchor` 即 `not_dynamically_expressible`。
- 实测：panoptic `core_claim` → `single_anchor(BuilderWallet)`（与真实
  binding.json 一致）；Intuition 两 claim → `multi_contract`（AtomWallet +
  IAggregator + BaseTest / UserOperationLib，跨合约，正确）。
- M24 `binding_llm.propose_binding`：绑定提案时把 `suggested_patch_contract`
  作为确定性约束注入 prompt（`SUGGESTED_PATCH_CONTRACT`），并把 anchor 结果
  随提案返回，供下游路由。
- M25 `stage3_eval_run`：新增 `bindabilities` 分布与
  `bindability_single_anchor/multi_contract/file_level/no_anchor_total`，
  让评测直接暴露「动态可表达性天花板」，与 P1.8c 的
  `not_dynamically_expressible` 终态口径对齐。
- 回归：阶段三 74/74 全绿（新增 2 项 anchor_resolver 测试）。
- 后续：`multi_contract` 走 M1 参考补丁（`case/patched/`）；
  `single_anchor` 时把 `suggested_patch_contract` 用作 patch 迁移的确定性
  目标（替代 LLM 回退猜测）。

## P1.10 确定性符号歧义修复（同名状态变量/函数，根因修复）

- 根因：Solidity 中同一名字可同时是「某合约的 public 状态变量」与「另一
  合约/接口的同名函数」（例如 `address public redeemEscrow` 与
  `function redeemEscrow() external view returns (address)`）。确定性扫描
  `function_owner`/`state_var_owner` 是纯文本匹配，把两者的 owner 并集，
  导致两类误判：
  1. `binding_validate.lint_binding` 的函数 cross-contract 检查把「注入点
     合约已可见的状态变量」误当成「外部合约的函数」，报
     `cross-contract reference` 并把 binding 拦下（binding_exhausted /
     compile_error）。
  2. `anchor_resolver._identifier_owners` 合并函数 owner，把本可
     `single_anchor` 的 claim 误判为 `multi_contract`。
- 修复：Solidity 裸标识符解析优先状态变量，据此确定性消歧——
  1. `binding_validate`：函数 cross-contract 检查增加 `root not in
     patch_scope` 前置条件（root 已是注入点可见状态变量时不再按函数检查）。
  2. `anchor_resolver._identifier_owners`：identifier 是状态变量时只返回
     `state_var_owner`，不合并同名函数 owner；`resolve_anchors` 用
     `poc_test_contract` 感知 PoC 测试合约，候选被 PoC 合约拥有时优先锚定
     该合约。
- 验证（goldset_v1_pos20）：
  - 单点对照（同一 binding 修复前后）：Monetrix
    `escrow_usdc_permanently` 的 binding 在旧 lint 下报 1 个 cross-contract
    error（会被拦为 binding_exhausted），修复后 lint errors=0、可编译差分。
  - 复用 `cases/<cid>/bindings/` 的既有 binding 重跑差分（不重新 LLM）：
    reproduced=13 claim（其中 Virtuals 0→2、Kinetiq 0→1、Brix 0→1、
    SukukFi 0→1、Monetrix 1→2、Covenant 2→3）。口径提示：这批 binding
    为历史遗留文件，与 `eval_full_20` 的重新绑定不完全一致，13 只能作
    参考上界；干净结论需在 P1.10 代码下重新 `stage3_eval_run`。
  - 阶段三回归 74/74 全绿。
- 剩余瓶颈（语义层，非本次 lint 问题）：
  - checkpoint 操作锚点丢失：阶段二给出 `before claimRedeem` 这类相对
    关键操作的 checkpoint，`patch._checkpoint` 只保留 before/after 并把
    快照插在 test 函数入口，导致「状态 stuck」类 I 在 PoC 路径上恒真
    （violation_not_reproduced）。需把 before 快照迁移到关键操作调用前。
  - `compile_blocked`（Panoptic flatten via_ir 编译失败）属阶段一产物问题。

## P1.11 跨合约实例引用引导（根因修复）

- 根因：跨合约不变量（如 `owner`、`getImpact`）属于业务合约，不在 PoC 测试
  合约内；LLM 反复写裸 `owner` 被 lint 正确拦截，3 轮重绑都失败
  （`binding_exhausted`），是 Virtuals 全卡、Kinetiq 部分卡的直接原因。
- 修复：`solidity_scan.contract_instances(source, contract)` 确定性解析 PoC
  测试合约里的合约类型实例（`ServiceNft public snft` -> `{"snft":
  "ServiceNft"}`）；`binding_llm.propose_binding` 把该实例映射表注入 prompt
  （`CROSS_CONTRACT_INSTANCES`），要求跨合约成员绑定为 `<实例>.<成员>`。
- 盲测：Virtuals 从 0/4 binding_exhausted 提升到 4/4 绑定成功（`snft.owner()`
  替代裸 `owner`）。阶段三回归 74/74 全绿。
- 暴露的下一层问题：绑定成功后 Virtuals 4 个全部 `inconclusive`，patched
  revert 是 `ERC721NonexistentToken(1)`（assert 表达式里 `snft.getImpact(1)`
  对未 mint token revert），不是 assert 触发——PoC harness 未 mint token，
  属 flatten 产物缺陷。

## P1.12 via_ir 编译降级回退（根因修复）

- 根因：Panoptic Next Core flatten 后 Contract.sol 达 1.5MB，`via_ir = true`
  下 solc 报 `stack too deep`，6 个 claim 全部 `compile_blocked`。
- 修复：`stage3_pipeline` 新增 `_retry_without_via_ir`——forge 编译失败且错误
  含 `too deep in the stack` 时，把 foundry.toml 的 `via_ir = true` 改写为
  `false` 后重编译。
- 盲测：Panoptic `compile_blocked` 6 -> 0；但 6 个 claim 变为 3 `compile_error`
  （patched 加 assert 后在非 via_ir 下再次 stack too deep / 声明遮蔽）+ 3
  `violation_not_reproduced`，reproduced 仍 0。
- 判定：flatten 超大文件的编译困难是阶段一产物问题，阶段三只能部分缓解。

## P1.14 差分「双失败」映射（根因修复）

- 根因：`lib/differential.py` 的 `compute_queries` 只处理 (ok,ok)/(ok,fail)/(fail,ok)
  三种组合；当原版与补丁的 exploit 测试**都失败**（修复后合约上 PoC 仍断言漏洞态）
  时落入空分支，四个 query 全 unknown → `consistency_verdict` 返回 `inconclusive`（弃权）。
- 修复：新增 `else` 分支，把「双失败」映射为 `P_and_T_and_not_I = unsat`、
  `P_and_T_and_V = unsat` → `violation_not_reproduced`（违规未被见证）。
- 验证：10 个 code-fix 负样本全部从 `inconclusive` 翻转为 `violation_not_reproduced`；
  阶段三回归 74/74 全绿。
- 边界：`not original_result or not patched_result` 的 setUp/缺测早退分支不受影响，
  只有「两个 exploit 测试都真正运行且失败」才进入新分支。

## 30 例大范围盲测 + 负样本金标（precision/recall）

- 正样本 `goldset_v2_pos91`（30 例）：TP=25/127=19.7%（全分母）、25/60=41.7%（可验证子集）。
- 根因归因：`multi_contract` claim 占 65%，贡献 26 partial_binding + 23 inconclusive
  + 13 binding_error + 11 compile_error + 6 binding_failed + 4 nde；`single_anchor`
  是唯一稳定复现源。阶段三 `assert(I)` 单点注入无法表达跨合约不变量（需 M1 reference patch）。
- 负样本 `evaluation/goldset_v2_neg01`（10 个 code-fix 负样本，7 独立根因）：
  FP=0、TN=10 → precision=25/25=100%。修复前 11/12 为 `inconclusive`（弃权），
  P1.14 后全部主动翻转为 `violation_not_reproduced`。
- 剩余 `inconclusive` 的第二根因（GTE Perps 9 例）：`(fail, ok)` 组合——原版 exploit
  测试自身失败（PoC 未在切片上复现），非差分映射问题，需修 PoC/切片。

## P1.15 平坦化 artifact 路径引用重写（根因修复）

- 根因：阶段一 flatten 把所有文件合并为 `Contract.sol`，PoC 的 `setUp` 里
  `deployCodeTo("TestUSDC.sol", ...)` / `vm.getCode("MEVCapture.sol")` 等按
  **原文件路径**取 artifact，Foundry 报 `vm.getCode: no matching artifact found`，
  exploit 测试根本没跑 → `inconclusive`（setUp 早退）。
- 修复：`lib/patch.py` 新增 `_normalize_artifact_refs` / `_normalize_project_src`，
  在 `build_projects` 复制 original/patched 后把 `fn("path/Name.sol")` 重写为
  `fn("Name")`（取 basename 去 `.sol`，合约名仍是合法 artifact 引用）。
- 验证：GTE Perps `Xrgn2WT5sTG`（TestUSDC.sol）9 个 claim 从
  `9 inconclusive` → `7 violation_reproduced + 1 violation_not_reproduced
  + 1 partial_binding`（召回 0 → 7）。阶段三回归 74/74 全绿。
- 边界：`GTELaunchpadV2Pair.sol` 案例 setUp 修复后 original 恢复 Success，但
  patched 以 `EvmError: Revert` 失败（assert 表达式内调用 revert），仍 `inconclusive`
  —— 保守起见不把泛型 revert 当 assert 触发，避免假阳性。

## P1.16 根因全景（30 例）

- 第一根因 `multi_contract`（65% claim）：26 partial_binding + 23 inconclusive
  + 13 binding_error + 11 compile_error + 6 binding_failed + 4 nde；需 M1 reference patch。
- 第二根因 `setUp vm.getCode("*.sol") no artifact`：P1.15 修复，Xrgn2WT5sTG 0→7。
- 第三根因差分双失败：P1.14 修复，负样本全部主动 `violation_not_reproduced`。

## P1.15 flatten 产物 artifact 路径归一化（根因修复）

- 根因：阶段一 flatten 把所有源文件改名为 `Contract.sol`，但 PoC 的 `setUp` 里
  `deployCodeTo("TestUSDC.sol", ...)` / `vm.getCode("X.sol")` 仍按原文件路径
  找 artifact，Foundry 报 `setUp(): vm.getCode: no matching artifact found`，
  exploit 测试根本没运行 → 整案例 `inconclusive`。
- 修复：`lib/patch.py` 新增 `_normalize_artifact_refs` / `_normalize_project_src`，
  在 `build_projects` 复制 src 后把 `vm.getCode("X.sol")`、`deployCodeTo("X.sol")`
  的路径参数改写为合约名（basename 去掉 `.sol`）。
- 实测：GTE Perps `Xrgn2WT5sTG` 9 个 claim 从 0 reproduced 提升到
  7 reproduced + 1 not_reproduced + 1 partial_binding；GTE Perps `FbQktkofz8X`
  1 claim 仍 inconclusive（该案例另有根因）。阶段三回归 74/74 全绿。
- 效果：30 例全分母召回 19.7%→25.2%，可验证子集召回 41.7%→54.2%，
  案例级召回 44.4%→48.1%。
