# 阶段二流程图与文件索引

来源：直接读 `cli/semantic_pipeline.py` 主流程代码，非文档转述。更新于 2026-10-12
（S1–S12 目录收口 + 新 SC 工作废弃后）。

本文档止于阶段二主链（报告 → P/I/V → stage3-spec）。阶段三把代码执行关系 T 与本阶段输出绑定后判断一致性（`main.py stage3-feedback`，`lib/stage3_consistency.py`）。

## 1. 主流程 `python main.py run`

```mermaid
flowchart TD
    R["report.json<br/>metadata.json"] --> S1

    subgraph L1["① 载入与身份核对（本地）"]
        S1["semantic_pipeline.load_report()<br/>report_only.report_json_input() / prose_only() / sha()"]
    end
    S1 --> A1["provenance.json<br/>original-report<br/>extraction-input.txt"]

    A1 --> S2["② 证据编号（本地）<br/>evidence_catalog.build_catalog()"]
    S2 --> A2["evidence-catalog.json"]

    A2 --> S3["③ 提取前筛选<br/>ingest.validate_readiness<br/>【模型调用 1】"]
    S3 --> G1{"信息是否充分？"}
    G1 -->|"缺受影响对象/触发/直接效果/安全关系依据"| F1["status.json<br/>excluded_before_extraction<br/>needs_input_review<br/>exit 2"]
    G1 -->|充分| S4

    S4["④ P/I/V 要素提取<br/>semantic_pipeline.request_elements()<br/>deepseek.extract_deepseek() / report_only.extract()<br/>prompts/active.py（semantic-live）<br/>【模型调用 2】"] --> A4["elements-ids.json<br/>element-attempts.json"]
    A4 --> S5["⑤ 格式/机械归一化<br/>salvage"]
    S5 --> A5["element-format-normalization.json<br/>mechanical-salvage-elements.json"]
    A5 --> S6["⑥ 证据落地校验<br/>ingest.hydrate_elements()<br/>semantic_core.validate_elements()"]
    S6 --> A6["elements.json<br/>evidence-spans.json"]
    A6 --> G2{"关键错误？"}
    G2 -->|是| F2["status.json + auto-triage.json<br/>pipeline_failure"]
    G2 -->|否| S7

    S7["⑦ 形式计划<br/>semantic_pipeline.request_formalization()<br/>【模型调用 3】"] --> A7["formal-plan.json<br/>formalization-ids.json"]
    A7 --> S8["⑧ 形式约束检查<br/>salvage.check_numeric_plan()<br/>salvage.check_address_plan()<br/>plan_synthesizer.structured_unresolved_review()<br/>plan_synthesizer.classified_relation_alignment()"]
    S8 --> A8["relation-alignment.json<br/>unresolved-review.json"]
    A8 --> G3{"可修复？"}
    G3 -->|"受限字段错误（≤2 次）"| S9["⑨ 受约束局部修复<br/>只改被标记字段"] --> S8
    G3 -->|拒绝| F3["status.json<br/>needs_review / failure"]
    G3 -->|通过| S10

    S10["⑩ 证据回填<br/>ingest.hydrate_formalization()"] --> A10["formalization.json"]
    A10 --> S11["⑪ 编译 P/I/V<br/>semantic_core.compile_bundle()<br/>report_only.relationship_review()"]
    S11 --> S12["⑫ 可观察变量审查<br/>solving.attach_review()"]
    S12 --> A12["observability-review.json"]
    A12 --> S13["⑬ Z3 求解<br/>solving.solve_queries()<br/>z3"]
    S13 --> A13["queries/claim/*.smt2<br/>constraints.json<br/>solver-results.json"]
    A13 --> S14["⑭ 自动分流<br/>solving.from_bundle()"]
    S14 --> A14["auto-triage.json"]
    A14 --> S15["⑮ 阶段三接口<br/>report_only.sha() 计算各产物哈希<br/>stage3_consistency.binding_contract()"]
    S15 --> A15["stage3-spec.json<br/>status.json"]
```

## 2. 每一步的文件与产物

| # | 步骤 | 调用文件（函数） | 产物 | 模型调用 |
|---|---|---|---|---|
| ① | 载入与身份核对 | `cli/semantic_pipeline.py` `load_report()` → `lib/report_only.py` `report_json_input()` / `prose_only()` / `sha()` | `provenance.json`、`original-report`、`extraction-input.txt` | 否 |
| ② | 证据编号 | `lib/ingest.py` `build_catalog()` | `evidence-catalog.json` | 否 |
| ③ | 提取前筛选 | `cli/semantic_pipeline.py` `request_readiness()`；Prompt 来自 `prompts/active.py` | `neural-input-screen/prompt.txt`、`input-readiness.json` | **1 次** |
| ④ | P/I/V 要素提取 | `cli/semantic_pipeline.py` `request_elements()` → `lib/deepseek.py` `extract_deepseek()`（或 `lib/report_only.py` `extract()`）；Prompt 来自 `prompts/active.py` | `elements-ids.json`、`element-attempts.json` | **1 次**（可重试 1 次） |
| ⑤ | 格式/机械归一化 | `lib/salvage.py` `normalize_element_ids()` / `normalize_attack_step_roles()` / `drop_unused_invalid_symbols()` | `element-format-normalization.json`、`mechanical-salvage-elements.json` | 否 |
| ⑥ | 证据落地校验 | `lib/ingest.py` `hydrate_elements()`、`lib/semantic_core.py` `validate_elements()` | `elements.json`、`evidence-spans.json` | 否 |
| ⑦ | 形式计划 | `cli/semantic_pipeline.py` `request_formalization()` → `lib/deepseek.py` `extract_deepseek()` | `formal-plan.json`、`formalization-ids.json` | **1 次**（可重试 2 次） |
| ⑧ | 形式约束检查 | `lib/salvage.py` `check_numeric_plan()` / `check_address_plan()`；`lib/plan_synthesizer.py` `structured_unresolved_review()` / `classified_relation_alignment()` | `relation-alignment.json`、`unresolved-review.json` | 否 |
| ⑨ | 受约束局部修复 | `cli/semantic_pipeline.py` `formal_repair_fields()` / `local_repair_payload()`（≤2 次，**会再调模型**） | 追加到 `formalization-attempts.json` | 每次 1 次 |
| ⑩ | 证据回填 | `lib/ingest.py` `hydrate_formalization()` | `formalization.json` | 否 |
| ⑪ | 编译 P/I/V | `lib/semantic_core.py` `compile_bundle()` → `lib/report_only.py` `relationship_review()` | （内存 bundle） | 否 |
| ⑫ | 可观察变量审查 | `lib/solving.py` `attach_review()` | `observability-review.json` | 否 |
| ⑬ | Z3 求解 | `lib/solving.py` `solve_queries()`（`z3`） | `queries/<claim>/*.smt2`、`constraints.json`、`solver-results.json` | 否 |
| ⑭ | 自动分流 | `lib/solving.py` `from_bundle()` / `from_failure()` | `auto-triage.json` | 否 |
| ⑮ | 阶段三接口 | `lib/report_only.py` `sha()`；`lib/stage3_consistency.py` `binding_contract()` | `stage3-spec.json`、`status.json` | 否 |

一次成功的 run 通常是 **3 次模型调用**；被筛选拦掉时只有 1 次。

## 3. 检查门一览

| 门 | 位置 | 判断内容 | 不通过的表现 |
|---|---|---|---|
| 输入充分性门 | `lib/ingest.py` `validate_readiness()` | 受影响对象、触发/行为、直接效果、安全关系依据 | `excluded_before_extraction` / `needs_input_review`，exit 2 |
| 证据编号门 | `lib/ingest.py` `hydrate_elements()` | 未知证据 ID、来源角色 | 拒绝 |
| schema/类型门 | `lib/semantic_core.py` `validate_elements()` / `validate_formalization()` | kind、modality、角色隔离、字段集 | 拒绝 |
| 角色隔离门 | `lib/semantic_core.py:130-142` | P←precondition/assumption，I←security_intent，V←impact | `property source role mismatch` |
| 数值保真门 | `lib/salvage.py` `check_numeric_plan()` | 显式阈值不得退化成布尔量；协议编号不算数值 | 拒绝 |
| 地址保真门 | `lib/salvage.py` `check_address_plan()` | `address(0)` 相关性质须落到地址相等约束 | 拒绝 |
| 关系对齐门 | `lib/plan_synthesizer.py` `classified_relation_alignment()` | 关系类别 ↔ 模板兼容 | 拒绝 |
| P 来源本地化 | `lib/plan_synthesizer.py`（EXPANDED_PLAN_VERSION） | 每条 P 的符号须由该条 P 自己的来源支撑；不同来源不得复用同一谓词 | 拒绝 |
| Z3 门 | `lib/solving.py` `solve_queries()` | `P∧V` 可满足、`P∧V∧I` 不可满足等 | 只证明**生成公式内部**关系 |

注意：Z3 通过不等于报告语义正确，也不等于 PoC 与报告一致。`needs_review` 不是通过。

## 4. 其它命令

```mermaid
flowchart LR
    subgraph Auto["main.py batch（自动化）"]
        B1["cli/batch_verify.py<br/>--reports-root 发现 */report.json"] --> B2["逐例子进程调用<br/>cli/semantic_pipeline.py"]
        B2 --> B3["batch-summary.json<br/>batch-summary.md"]
    end
    subgraph Ver["main.py verify（零模型调用）"]
        V1["cli/batch_verify.py"] --> V2["plan_synthesizer / salvage<br/>solving / semantic_core"]
        V2 --> V3["重放并校验<br/>evidence/公式/SMT/接口哈希"]
    end
    subgraph Pre["main.py preview / screen"]
        P1["preview.py screen<br/>本地输入检查"] 
        P2["preview.py report<br/>第一步报告正文"]
        P3["preview.py plan<br/>第二步精简 JSON"]
    end
```

| 命令 | 入口文件 | 依赖文件 | 产物 |
|---|---|---|---|
| `batch` | `cli/batch_verify.py` | `cli/semantic_pipeline.py`（子进程）、`prompts/registry.py` | `batch-summary.json`、`batch-summary.md`、每例一个子目录 |
| `verify` | `cli/batch_verify.py` | `lib/report_only`、`lib/semantic_core`、`lib/plan_synthesizer`、`lib/salvage`、`lib/ingest`、`lib/solving`、`prompts` | 控制台 JSON（`offline_verified`） |
| `screen` | `cli/preview.py`（`screen`） | `lib/ingest`、`cli/semantic_pipeline.load_report` | 可选 `--output` JSON |
| `preview-report` / `preview-plan` | `cli/preview.py`（`report` / `plan`） | `lib/ingest`、`lib/semantic_core`、`cli/semantic_pipeline` | 仅标准输出（不写文件） |
| `audit-preconditions` / `repair-preconditions` | `cli/preconditions.py`（`audit` / `repair`） | `lib/report_only`、`lib/ingest`、`lib/semantic_core`、`cli/semantic_pipeline` | 审计/修复 JSON（**主流程不调用，opt-in**） |
| `observability` | `lib/solving.py`（CLI） | 自身 | 审查提示 |
| `salvage-replay` | `lib/salvage.py`（CLI） | `lib/semantic_core`、`lib/plan_synthesizer`、`cli/semantic_pipeline`（延迟导入） | 重放结果目录 |
| `stage3-feedback` | `lib/stage3_consistency.py`（CLI） | 自身 | 该 run 的 `stage3-consistency.json` |

## 5. 模块清单

| 类别 | 文件 |
| --- | --- |
| 入口(4) | `cli/semantic_pipeline.py`、`cli/batch_verify.py`、`cli/preview.py`、`cli/preconditions.py` |
| 库(9) | `lib/semantic_core.py`、`lib/plan_synthesizer.py`、`lib/deepseek.py`、`lib/report_only.py`、`lib/ingest.py`、`lib/solving.py`、`lib/salvage.py`、`lib/stage3_consistency.py`、`lib/compat.py`（历史名兼容） |

Prompt：可编辑的只有 `prompts/current.py`（`semantic-live`，默认版本）；
`prompts/versions/` 是冻结只读存档（v3.5–v3.20，共 16 个）。运行时经
`prompts/active.py` 解析，`prompts/registry.py` 管版本与功能开关。
推荐稳定版 `semantic-v3.16`（冻结）。
