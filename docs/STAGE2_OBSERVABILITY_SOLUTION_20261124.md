# Stage-2 Observability 根因与完整闭环方案（2026-11-24）

## 0. 结论

当前 Stage-2 observability 的问题不是“模型少写了几个字段”，也不是 Top-3
排序权重不合理。根因是 **Stage-2 的可观测性声明与 Stage-3 的代码事实被混成
了一层**：

- Stage-2 已经能声明 `observable_kind`、`scope`、`receiver`、
  `binding_risk`；
- Stage-2 不可能仅凭报告文本就给出真实代码里的 `code_fact`、
  `mutation_site`；
- 审计却把缺失代码事实写成 warning，Stage-3 A+ 又把它当 soft label 放行；
- Stage-3 绑定后没有生成可回传的逐符号代码证据；
- 因此 `observability_established` 永远是常量 `false`，高风险 warning 永远
  没有清除条件。

正确方向不是继续调 prompt 让模型“猜代码”，而是建立两层合同：

1. **Stage-2 declaration**：说明要观测什么、在哪个 checkpoint、跨哪个
   receiver、是否 derived、如果 derived 则定义是什么；
2. **Stage-3 evidence**：用真实 source/IR/binding 生成
   `bound_expr`、`source_file`、`source_function`、`mutation_site`，并回写
   给审计、排序和指标资格判断。

## 1. 已完成的 P0：只读审计

新增：

- `tools/stage3/evaluation/metrics/stage2_observability_audit.py`
- `tools/stage3/evaluation/metrics/stage2_observability_audit_20261124.json`
- `tools/stage3/evaluation/metrics/stage2_observability_audit_20261124.md`
- `tools/stage3/tests/test_stage2_observability_audit.py`

审计只读取冻结 Stage-2 产物，不修改样本、claim、标签、顺序、分母或权威指标。
复现：

```bash
cd tools/stage3
python -m evaluation.metrics.stage2_observability_audit
```

或从仓库根目录运行：

```bash
make stage2-observability-audit
```

覆盖率与 1.7.31/1.7.33 回放样本一致：54 个非零 claim case、211 个
claim、1027 个 claim 级符号、1860 次 P/I/V 角色引用。

## 2. 核心证据

| 信号 | 数值 | 解释 |
| --- | ---: | --- |
| 声明了 `observable_kind` 的符号 | 1027/1027 | 模型并非没有输出可观测性意图 |
| 声明了 `scope` 的符号 | 1027/1027 | scope 层已接通 |
| 声明了 `binding_risk` 的符号 | 1027/1027 | risk 层已接通 |
| 有 `code_fact` 的符号 | 0/1027 | Stage-2 没有任何代码事实 |
| 有 `mutation_site` 的符号 | 0/1027 | 没有任何变异点证据 |
| 无任何代码证据的符号 | 1027/1027 | `OBSERVABILITY_REQUIRES_CODE_FACT` 的全量来源 |
| `observable_kind=derived` | 354 | 占符号 34.5% |
| `derived` 但缺 `derived_definition` | 339 | 影响 170 个 claim、47 个 case |
| `binding_risk=high` 的符号 | 273 | 需要 Stage-3 清除却没有清除产物 |
| `auto_assert` claim | 58 | 都会带 warning 进入 Stage-3 |
| `binding_review` claim | 153 | 全部含 high-risk 符号 |
| `status=needs_review` 且 `route=auto_assert` | 58 | 状态与路由自相矛盾 |
| `observability-review` claim 的 `observability_established` | 263/263 false | `solving.review()` 硬编码 |

按角色看：

| 角色 | 角色引用次数 | 无代码证据 | high risk | derived 缺定义 |
| --- | ---: | ---: | ---: | ---: |
| P | 509 | 509 | 49 | 110 |
| I | 555 | 555 | 118 | 166 |
| V | 796 | 796 | 258 | 293 |

按 routing 看：

| route | claim 数 | high-risk 符号 | derived 缺定义 |
| --- | ---: | ---: | ---: |
| `auto_assert` | 58 | 0 | 37 |
| `binding_review` | 153 | 153 | 133 |

这组数据说明：

- 可观测性“意图”基本齐全；
- 可观测性“代码证据”完全缺失；
- 派生符号定义缺失是独立的真实 Stage-2 缺陷，不是 Stage-3 绑定失败；
- `auto_assert` 与 `needs_review` 并存，说明 audit 的 status 与 route 使用了
  不同的判据；
- ranking replay 不能解决此问题：当前排名已经捕获全部 8 个已知复现 claim，
  缺的是证据层，不是排序层。

## 3. 根因分层

### OBS-1：Stage-2 与 Stage-3 的证据层混用（critical）

`tools/report_constraints_v2/lib/formalization_audit.py` 在
`OBSERVABILITY_REQUIRES_CODE_FACT` / `I_MUTATION_SITE_MISSING` 中要求
`source_entity`、`code_fact` 或 `mutation_site`。这些字段应由 Stage-3 的
source/IR 产生，而不是由只看报告文本的 Stage-2 产生。

结果：

- 211/211 claim 都进入“缺代码事实”状态；
- 58 个 `auto_assert` claim 也带 warning，`status` 仍是 `needs_review`；
- Stage-3 为了不全部阻塞，把这两个 code 放进 soft label。

根因不在 warning 本身，而在合同没有区分：

```text
Stage-2 declaration != Stage-3 code fact
```

### OBS-2：`derived` 类型没有强制定义（high）

`plan_synthesizer.observability_contract()` 只在 `kind == 'derived'` 且
`derived_definitions` 中找不到目标时记录 `missing=['derived_definition']`。
但这条 missing 只进入 `binding_risk=high`，没有成为 Stage-2 的硬约束。

审计结果：

- 339 个符号、170 个 claim、47 个 case；
- 其中 37 个 claim 仍被 `auto_assert`。

Stage-3 无法从“一个没有表达式的 derived 布尔”稳定恢复代码事实，只能靠
语义猜测或退回 partial binding。

### OBS-3：status 与 route 判据不一致（high）

`formalization_audit.audit_claim()` 中：

- `status` 只要有任何 warning 就是 `needs_review`；
- `route` 只在 checkpoint / high-risk / restatement warning 时转为
  `binding_review`；
- 代码事实 warning 不进入 route 判断。

所以同一 claim 可以同时是 `auto_assert` 与 `needs_review`。这不是“保守”，
而是两个字段表达不同层语义，调用方无法判断哪个是权威状态。

### OBS-4：没有 Stage-3 observability evidence / write-back（critical）

`tools/report_constraints_v2/lib/solving.py` 的 `review()` 直接返回：

```python
{
    'observability_established': False,
    'human_semantic_review_required': True,
}
```

它是结构提示，不是代码绑定结果。1.7.31 产物中 263 个 review claim 全部为
false，且 263/263 的 `review_status` 都是 `no_structural_warning`，说明
该字段不承载任何代码绑定判断。Stage-3 的 `observable_ir.py` 实际已经枚举：

- typed candidates；
- `source_ir_grounded`；
- `evidence_level=typed_code_fact`；
- `mutation_sites`；
- recipe/compile 状态。

但这些信息没有形成逐 claim、逐符号、可被 Stage-2/指标消费的 artifact。
因此 Stage-2 的 `observability_established` 永远无法变为 true，high-risk
warning 也永远无法清除。

### OBS-5：A+ soft label 没有“完成条件”（high）

`tools/stage3/lib/stage2_contract.py` 把：

- `OBSERVABILITY_REQUIRES_CODE_FACT`
- `I_MUTATION_SITE_MISSING`
- `OBSERVABILITY_HIGH_RISK`

加入 `_SOFT_LABEL_CODES`。A+ 下 `binding_review` 可被放行为
`auto_assert`，以便 Stage-3 尝试绑定。这个设计本身是合理的：Stage-3 应该
有机会用真实代码解决 Stage-2 无法知道的事实。

缺陷是 **放行后没有验收条件**：

- 绑定成功不等于符号被源码证据支持；
- 绑定成功也不等于 I 有 mutation site；
- 没有 artifact 把 high-risk 从“待解决”改为“已解决”；
- `execution_contract` 只记录 binding，不记录 observability evidence。

## 4. 目标架构：两层合同 + 状态机

### 4.1 状态机

建议使用以下 6 个状态：

| 状态 | 产生层 | 含义 | 是否可继续 |
| --- | --- | --- | --- |
| `stage2_invalid` | Stage-2 | 缺 kind/scope/receiver/derived 定义等声明字段 | 否，Stage-2 repair |
| `stage2_declared` | Stage-2 | 声明完整，代码证据待 Stage-3 | 可以绑定尝试 |
| `stage3_bound` | Stage-3 | 有 `solidity_expr`，但尚未完成 source/IR 校验 | 不可自动断言 |
| `stage3_verified` | Stage-3 | bound expr 有 typed/source 证据，mutation site 已解析或明确 N/A | 可进入 witness/metric eligibility |
| `stage3_unobservable` | Stage-3 | 无候选、scope 不可见、receiver 无法解析 | unresolved，不得转 TN |
| `stage3_mutation_missing` | Stage-3 | 绑定存在但 I 符号没有 mutation site | unresolved/repair，不得计 TP |

关键规则：

- Stage-2 不再要求真实 `code_fact` / `mutation_site`；
- Stage-2 必须要求声明完整性和 derived 定义；
- Stage-3 允许从 `stage2_declared` 开始绑定；
- 只有 `stage3_verified` 能清除 high-risk、进入自动断言和漏洞级指标；
- `stage3_unobservable` / `stage3_mutation_missing` 保持 unresolved，
  不转 TN，不放宽 execution gate。

### 4.2 Stage-2 symbol declaration v2

在保持旧字段兼容的前提下，每个 P/I/V symbol 增加：

```json
{
  "observable_kind": "state|getter|call|derived|timestamp|balance|mapping|struct_field",
  "scope": "business|poc_instance|cross_contract",
  "receiver": "string_or_null",
  "contract_type": "string_or_null",
  "checkpoint": "before|after|input|derived|...",
  "source_entity_ids": ["report entity IDs"],
  "mutation_expectation": "state_change|call_outcome|read_only|derived|cross_contract_state",
  "code_anchor_hint": "function/event/state name explicitly stated by the report, else null",
  "observability_state": "stage2_declared",
  "code_fact": {
    "status": "pending_stage3",
    "bound_expr": null,
    "source_file": null,
    "source_function": null,
    "evidence_level": null
  },
  "mutation_site": {
    "status": "pending_stage3",
    "sites": []
  }
}
```

约束：

- `source_entity_ids` 可以直接从既有 `entity_ids` 确定性生成，不增加模型负担；
- `code_anchor_hint` 只允许复制报告中明确出现的函数/事件/变量名，不能由模型
  “推测实现”；
- `code_fact` / `mutation_site` 在 Stage-2 只能是 `pending_stage3`，不能伪造；
- `observable_kind=derived` 必须有 `derived_definition`，否则
  `observability_state=stage2_invalid`；
- `scope=cross_contract` 必须有 `receiver`；
- `checkpoint` 必须能区分 before/after/input/derived；单快照不能冒充 transition。

### 4.3 Stage-3 observability evidence v1

新增独立 artifact，建议路径：

```text
<run>/observability-evidence.json
```

结构：

```json
{
  "schema_version": "stage3-observability-evidence/1",
  "claim_id": "...",
  "binding_sha256": "...",
  "observable_ir_sha256": "...",
  "established": false,
  "mutation_site_complete": false,
  "uncovered_symbols": [],
  "symbols": {
    "c1_safe_after": {
      "roles": ["I", "V"],
      "status": "stage3_verified|stage3_bound|stage3_unobservable|stage3_mutation_missing",
      "observable_kind": "state",
      "checkpoint": "after",
      "bound_expr": "vault.allowance",
      "source_file": "Contract.sol",
      "source_contract": "Vault",
      "source_function": "unregisterVault",
      "candidate_id": "state:Vault.allowance",
      "evidence_level": "typed_code_fact",
      "mutation_sites": [{"contract": "Vault", "function": "unregisterVault"}],
      "mutation_site_status": "present|not_applicable|missing",
      "blockers": []
    }
  }
}
```

生成规则：

1. 只读取 Stage-3 已产生的 `observable-ir.json`、binding、execution contract；
2. 用 `solidity_expr` 精确匹配 IR candidate，不做语义猜测；
3. 有 typed/source-grounded candidate 才允许 `evidence_level`；
4. `mutation_sites` 来自 `observable_ir._typed_symbol_table()`，不是模型生成；
5. I 符号的 mutation site 缺失时写入 explicit blocker；
6. derived symbol 必须有 definition，否则 `stage3_unobservable`；
7. 输出文件包含 binding/IR 的 sha256，保证可追溯。

### 4.4 审计 v3

Stage-2 audit 应分成三类：

**Stage-2 hard blockers**

- `OBSERVABILITY_KIND_MISSING`
- `OBSERVABILITY_SCOPE_MISSING`
- `OBSERVABILITY_RECEIVER_MISSING`
- `DERIVED_DEFINITION_MISSING`
- `CHECKPOINT_MISSING`

**Stage-3 pending requirements**

- `OBSERVABILITY_CODE_FACT_PENDING`
- `I_MUTATION_SITE_PENDING`
- `OBSERVABILITY_HIGH_RISK_PENDING`

这些不是 Stage-2 失败，而是 stage-3 任务。它们可以有 severity=advisory 或
`blocking=false`，但必须带 `stage3_required=true` 和明确的 symbol 列表。

**Stage-3 resolution**

- `OBSERVABILITY_CODE_FACT_VERIFIED`
- `I_MUTATION_SITE_VERIFIED`
- `OBSERVABILITY_HIGH_RISK_CLEARED`
- `OBSERVABILITY_UNOBSERVABLE`

这样：

- `status` 和 `route` 不再矛盾；
- `observability_established` 由 Stage-3 evidence 决定，而不是常量；
- high-risk 有“如何清除”的路径；
- pending 不会被误读成“已失败”，也不会被 soft label 永远忽略。

## 5. 分阶段实施计划

| 优先级 | 阶段 | 改动 | 协议影响 | 当前状态 |
| --- | --- | --- | --- | --- |
| P0 | 证据审计 | 只读统计、JSON/MD、单测 | 无 | 已完成 |
| P1 | Stage-2 schema v2 | plan/observability 字段、derived 硬约束、状态机 | 需要 1.7.35 | 待执行 |
| P2 | Stage-2 audit v3 | 拆 hard blocker / pending / resolution | 需要 1.7.35 | 待执行 |
| P3 | Stage-3 evidence | 逐符号证据生成、execution contract 接入 | 需要 1.7.35 | 待执行 |
| P4 | Gate + feedback | 只有 verified 才能自动断言/计 TP；回写证据 | 需要 1.7.35 | 待执行 |
| P5 | Ranking | 用真实 evidence 排序，不再用缺失 warning | 需要 1.7.35 + 全量重跑 | 待执行 |
| P6 | Metrics | 重建 denominator/provenance/locked-eval | 需要全量重跑 | 待执行 |

### P1：Stage-2 schema v2

改动点：

- `tools/report_constraints_v2/lib/plan_synthesizer.py`
  - `PLAN_SYMBOL_OPTIONAL_FIELDS` 增加 `source_entity_ids`、
    `mutation_expectation`、`code_anchor_hint`；
  - `observability_contract()` 输出 `observability_state`、
    `code_fact`、`mutation_site`、`stage3_requirements`；
  - `derived` + 无 definition 直接作为 Stage-2 invalid；
  - `cross_contract` + 缺 receiver 保持 hard failure；
  - 保持旧 plan 的 replay 兼容，旧 plan 继续按历史缺省处理。
- `tools/report_constraints_v2/prompts/current.py`
  - 新增 `mutation_expectation` 和 `code_anchor_hint` 的严格定义；
  - 明确“报告没有写代码事实时只能写 pending/null，禁止推测”；
  - 明确 `derived` 必须有 `derived_definitions`；
  - prompt version 升为 `semantic-live-28`，旧 live-27 冻结保留。
- `tools/report_constraints_v2/lib/stage3_consistency.py`
  - binding contract 透传 `source_entity_ids`、`mutation_expectation`、
    `code_anchor_hint`、`observability_state`。

验收：

- 新 run 中所有被引用符号都有 `observability_state`；
- `derived` 符号缺定义数为 0；
- `auto_assert` 不再与 `needs_review` 并存；
- 旧 1.7.34 run 仍可回放，不被新 schema 改写。

### P2：Stage-2 audit v3

改动点：

- `formalization_audit.py`
  - 将代码事实缺失改为 `stage3_pending`，不参与 Stage-2 hard fail；
  - 为每 claim 输出 `observability_blockers` 和
    `observability_requirements`；
  - `can_auto_assert` 只依赖 Stage-2 declaration 完整性 + restatement /
    independence 等语义 gate；
  - 增加 `status_route_conflict` 自检，禁止再次出现 auto_assert +
    needs_review。
- `solving.py`
  - 删除硬编码 `observability_established=False`；
  - Stage-2 review 输出 `observability_established=null` 或
    `stage2_declared`，Stage-3 才有权填 true/false；
  - `human_semantic_review_required` 由实际 blocker 派生。

### P3：Stage-3 evidence write-back

新增：

- `tools/stage3/lib/observability_evidence.py`
- `tools/stage3/cli/stage3_observability_evidence.py`（可选离线命令）

接入点：

- `case_runner.bind_claims()` 在 binding accepted 后生成
  `observability-evidence.json`；
- `stage3_pipeline` 将 evidence 摘要写入 `execution-contract.json`；
- `observable_ir` 的 `mutation_sites`、`evidence_level`、`candidate_id`
  原样传递，禁止二次猜测；
- evidence 文件写入 binding / IR 的 sha256。

验收：

- 每个 bound symbol 有 `status`、`bound_expr`、source 信息；
- I 符号有 `mutation_site_status`；
- 没有 candidate 的符号显式 `stage3_unobservable`；
- evidence 生成不调用 LLM。

### P4：Gate 与 feedback

规则：

- `stage3_verified` 才能将 high-risk 标记为 cleared；
- `stage3_unobservable` / `stage3_mutation_missing` 不得进入
  `violation_reproduced`，不得计 TP，也不得转 TN；
- `metric_eligibility` 的 vulnerability 分支要求
  `observability_established=true`；
- `stage2_contract.decide()` 的 A+ 仍允许尝试绑定，但不能仅凭 soft label
  把 claim 视为已完成；
- feedback artifact 以 claim/symbol/evidence hash 索引，下一次 Stage-2
  只使用同 case、同语义、同 frozen source 的已验证 evidence，不跨案例污染。

### P5：Ranking

只有 P1-P4 完成后才调整排序：

- 第一排序键是 `stage3_verified`；
- 第二是 `mutation_site_status=present/not_applicable`；
- 第三是 transition、I/V independence、execution-ready；
- 同一 impact 只保留一个首选 claim（impact diversity）；
- 不再把 `OBSERVABILITY_REQUIRES_CODE_FACT` 计数当作排序主信号。

### P6：协议与指标闭环

执行顺序：

1. `PROTOCOL_VERSION` 升到 `mainline/1.7.35`；
2. 重新生成 protocol baseline；
3. 用新 prompt / schema / evidence 全量重跑冻结正负例；
4. 重建 current denominator、provenance、locked-eval contract；
5. 只有 `locked-eval-check` ready 后才刷新四指标；
6. 对比旧指标，同时报告完成率、binding 成功率、observability 成功率，
   不用单项 recall 掩盖覆盖变化。

## 6. 验收标准

### 必须通过

- 冻结样本、标签、顺序、分母不被修改；
- unresolved 不转 TN，execution gate / metric eligibility 不放宽；
- 所有 metric-eligible 的 TP 都有 `observability_established=true`；
- 所有进入 forge 的 I 符号都有 `mutation_site_status=present` 或明确的
  `not_applicable` 证据；
- `auto_assert` 与 `needs_review` 不再同时出现；
- `derived` 缺定义数为 0；
- 旧 1.7.34 run 仍可 replay；
- 新旧指标差异可归因到 claim population、binding、evidence、witness 四层。

### 预期改善

- `binding_error` / `partial_binding` 的 Stage-2 可预防部分下降；
- Stage-3 不再对无 observable 的 claim 反复重绑定；
- Top-3 不再把名额花在同等不可观测的 impact 变体上；
- recall 是否上升取决于 witness/forge，不能承诺“改 schema 即涨点”；
- precision 受到 evidence gate 保护，不应为了 recall 放宽。

## 7. 为什么这能改善指标

当前 8/8 已知复现 claim 已经被当前排名捕获，说明排名不是主要漏检原因。
真正的漏斗在：

```text
Stage-2 声明完整
  -> Stage-3 绑定成功
  -> 绑定符号有源码事实
  -> I 有 mutation site
  -> P/T/V/I witness 可执行
  -> metric eligible
```

现在中间三层没有独立证据，失败会被归到 `binding_error` /
`partial_binding` / `effect_not_witnessed`，无法定向修复。补齐 evidence 后：

- 可明确区分“代码不可观测”和“绑定写错”；
- 可让 Stage-3 repair 只作用于有候选的符号；
- 可让 Stage-2 只修声明错误，不再承担代码事实责任；
- 可让排序使用真实验证状态，而不是所有 claim 相同的 pending warning；
- 可让指标只接受真正可观测的 witness，避免无证据的伪 TP。

## 8. 当前状态与下一步

已完成：

- 根因量化；
- 只读审计与单测；
- 完整两层合同、状态机、evidence schema、gate 与协议升级方案。

尚未执行：

- P1-P6 的所有生产代码接入。原因是当前 `mainline/1.7.34` 已冻结，
  `formalization_audit.py`、`plan_synthesizer.py`、`solving.py`、
  `stage2_contract.py` 等均属于执行/报告协议受控文件；直接改动会让当前
  权威 run stale，并可能在未重跑的情况下污染指标解释。

建议下一步按以下顺序执行：

1. 在 `mainline/1.7.35` 分支上实现 P1 + P3（schema 与 evidence builder）；
2. 用一条正例和一条负例做端到端 evidence 验收；
3. 实现 P2 + P4 gate，跑 stage2/stage3 单测；
4. 再做 P5/P6 全量重跑与指标重建。

在协议升级和全量重跑完成前，不应修改或宣称新的权威四指标。
