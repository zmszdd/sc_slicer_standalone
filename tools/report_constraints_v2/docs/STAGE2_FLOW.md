# 阶段二流程图与文件索引

来源：直接读 `semantic_pipeline.py` 主流程代码，非文档转述。更新于 2026-09-22。

> 本文档止于阶段二主链（报告 → P/I/V → stage3-spec）。**下游**"新 SC 生成"
> （阶段二 run + 阶一切片 → 单文件新 SC → forge → 四分支判读 → 阶段三
> ingest）见 [new_sc_flow.svg](new_sc_flow.svg)。

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

    A2 --> S3["③ 提取前筛选<br/>report_readiness<br/>【模型调用 1】"]
    S3 --> G1{"信息是否充分？"}
    G1 -->|"缺受影响对象/触发/直接效果/安全关系依据"| F1["status.json<br/>excluded_before_extraction<br/>needs_input_review<br/>exit 2"]
    G1 -->|充分| S4

    S4["④ P/I/V 要素提取<br/>semantic_pipeline.request_elements()<br/>report_only.extract_deepseek()<br/>prompts/versions/semantic_prompts_v3NN<br/>【模型调用 2】"] --> A4["elements-ids.json<br/>element-attempts.json"]
    A4 --> S5["⑤ 格式/机械归一化<br/>mechanical_salvage"]
    S5 --> A5["element-format-normalization.json<br/>mechanical-salvage-elements.json"]
    A5 --> S6["⑥ 证据落地校验<br/>evidence_catalog.hydrate_elements()<br/>semantic_core.validate_elements()"]
    S6 --> A6["elements.json<br/>evidence-spans.json"]
    A6 --> G2{"关键错误？"}
    G2 -->|是| F2["status.json + auto-triage.json<br/>pipeline_failure"]
    G2 -->|否| S7

    S7["⑦ 形式计划<br/>semantic_pipeline.request_formalization()<br/>【模型调用 3】"] --> A7["formal-plan.json<br/>formalization-ids.json"]
    A7 --> S8["⑧ 形式约束检查<br/>fidelity.check_numeric_plan()<br/>fidelity.check_address_plan()<br/>plan_synthesizer.structured_unresolved_review()<br/>plan_synthesizer.classified_relation_alignment()"]
    S8 --> A8["relation-alignment.json<br/>unresolved-review.json"]
    A8 --> G3{"可修复？"}
    G3 -->|"受限字段错误（≤2 次）"| S9["⑨ 受约束局部修复<br/>只改被标记字段"] --> S8
    G3 -->|拒绝| F3["status.json<br/>needs_review / failure"]
    G3 -->|通过| S10

    S10["⑩ 证据回填<br/>evidence_catalog.hydrate_formalization()"] --> A10["formalization.json"]
    A10 --> S11["⑪ 编译 P/I/V<br/>semantic_core.compile_bundle()<br/>report_only.relationship_review()"]
    S11 --> S12["⑫ 可观察变量审查<br/>review.attach_review()"]
    S12 --> A12["observability-review.json"]
    A12 --> S13["⑬ Z3 求解<br/>symbolic_queries.solve_queries()<br/>z3"]
    S13 --> A13["queries/claim/*.smt2<br/>constraints.json<br/>solver-results.json"]
    A13 --> S14["⑭ 自动分流<br/>review.from_bundle()"]
    S14 --> A14["auto-triage.json"]
    A14 --> S15["⑮ 阶段三接口<br/>report_only.sha() 计算各产物哈希"]
    S15 --> A15["stage3-spec.json<br/>status.json"]
```

## 2. 每一步的文件与产物

| # | 步骤 | 调用文件（函数） | 产物 | 模型调用 |
|---|---|---|---|---|
| ① | 载入与身份核对 | `semantic_pipeline.py` `load_report()` → `report_only.py` `report_json_input()` / `prose_only()` / `sha()` | `provenance.json`、`original-report`、`extraction-input.txt` | 否 |
| ② | 证据编号 | `evidence_catalog.py` `build_catalog()` | `evidence-catalog.json` | 否 |
| ③ | 提取前筛选 | `report_readiness.py` `PROMPT` / `model_payload()` / `validate_readiness()` | `neural-input-screen/prompt.txt`、`input-readiness.json` | **1 次** |
| ④ | P/I/V 要素提取 | `semantic_pipeline.py` `request_elements()` → `report_only.py` `extract_deepseek()`；Prompt 来自 `prompts/registry.py` → `prompts/versions/semantic_prompts_v3NN.py` | `elements-ids.json`、`element-attempts.json` | **1 次**（可重试 1 次） |
| ⑤ | 格式/机械归一化 | `mechanical_salvage.py` `normalize_element_ids()` / `normalize_attack_step_roles()` / `drop_unused_invalid_symbols()` | `element-format-normalization.json`、`mechanical-salvage-elements.json` | 否 |
| ⑥ | 证据落地校验 | `evidence_catalog.py` `hydrate_elements()`、`semantic_core.py` `validate_elements()` | `elements.json`、`evidence-spans.json` | 否 |
| ⑦ | 形式计划 | `semantic_pipeline.py` `request_formalization()` → `report_only.py` `extract_deepseek()` | `formal-plan.json`、`formalization-ids.json` | **1 次**（可重试 2 次） |
| ⑧ | 形式约束检查 | `fidelity.py` `check_numeric_plan()` / `check_address_plan()`；`plan_synthesizer.py` `structured_unresolved_review()` / `classified_relation_alignment()` | `relation-alignment.json`、`unresolved-review.json` | 否 |
| ⑨ | 受约束局部修复 | `semantic_pipeline.py` `formal_repair_fields()` / `local_repair_payload()`（≤2 次，**会再调模型**） | 追加到 `formal-attempts` | 每次 1 次 |
| ⑩ | 证据回填 | `evidence_catalog.py` `hydrate_formalization()` | `formalization.json` | 否 |
| ⑪ | 编译 P/I/V | `semantic_core.py` `compile_bundle()` → `report_only.py` `relationship_review()` | （内存 bundle） | 否 |
| ⑫ | 可观察变量审查 | `review.py` `attach_review()` | `observability-review.json` | 否 |
| ⑬ | Z3 求解 | `symbolic_queries.py` `solve_queries()`（`z3`） | `queries/<claim>/*.smt2`、`constraints.json`、`solver-results.json` | 否 |
| ⑭ | 自动分流 | `review.py` `from_bundle()` / `from_failure()` | `auto-triage.json` | 否 |
| ⑮ | 阶段三接口 | `report_only.py` `sha()` | `stage3-spec.json`、`status.json` | 否 |

一次成功的 run 通常是 **3 次模型调用**；被筛选拦掉时只有 1 次。

## 3. 检查门一览

| 门 | 位置 | 判断内容 | 不通过的表现 |
|---|---|---|---|
| 输入充分性门 | `report_readiness.validate_readiness()` | 受影响对象、触发/行为、直接效果、安全关系依据 | `excluded_before_extraction` / `needs_input_review`，exit 2 |
| 证据编号门 | `evidence_catalog.hydrate_elements()` | 未知证据 ID、来源角色 | 拒绝 |
| schema/类型门 | `semantic_core.validate_elements()` / `validate_formalization()` | kind、modality、角色隔离、字段集 | 拒绝 |
| 角色隔离门 | `semantic_core.py:130-142` | P←precondition/assumption，I←security_intent，V←impact | `property source role mismatch` |
| 数值保真门 | `fidelity.check_numeric_plan()` | 显式阈值不得退化成布尔量；协议编号不算数值 | 拒绝 |
| 地址保真门 | `fidelity.check_address_plan()` | `address(0)` 相关性质须落到地址相等约束 | 拒绝 |
| 关系对齐门 | `plan_synthesizer.classified_relation_alignment()` | 关系类别 ↔ 模板兼容 | 拒绝 |
| P 来源本地化 | `plan_synthesizer`（EXPANDED_PLAN_VERSION） | 每条 P 的符号须由该条 P 自己的来源支撑；不同来源不得复用同一谓词 | 拒绝 |
| Z3 门 | `symbolic_queries.solve_queries()` | `P∧V` 可满足、`P∧V∧I` 不可满足等 | 只证明**生成公式内部**关系 |

注意：Z3 通过不等于报告语义正确，也不等于 PoC 与报告一致。`needs_review` 不是通过。

## 4. 其它命令

```mermaid
flowchart LR
    subgraph Auto["main.py batch（自动化）"]
        B1["run_semantic_batch.py<br/>--reports-root 发现 */report.json"] --> B2["逐例子进程调用<br/>semantic_pipeline.py"]
        B2 --> B3["batch-summary.json<br/>batch-summary.md"]
    end
    subgraph Ver["main.py verify（零模型调用）"]
        V1["verify_semantic.py"] --> V2["plan_synthesizer / fidelity<br/>review / symbolic_queries"]
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
| `batch` | `run_semantic_batch.py` | `semantic_pipeline.py`（子进程）、`prompts/registry.py` | `batch-summary.json`、`batch-summary.md`、每例一个子目录 |
| `verify` | `verify_semantic.py` | `report_only`、`semantic_core`、`plan_synthesizer`、`fidelity`、`evidence_catalog`、`symbolic_queries`、`review`、`mechanical_salvage`、`prompts/registry` | 控制台 JSON（`offline_verified`） |
| `screen` | `preview.py`（`screen`） | `evidence_catalog`、`semantic_pipeline.load_report` | 可选 `--output` JSON |
| `preview-report` / `preview-plan` | `preview.py`（`report` / `plan`） | `evidence_catalog`、`semantic_core`、`semantic_pipeline` | 仅标准输出（不写文件） |
| `audit-preconditions` / `repair-preconditions` | `preconditions.py`（`audit` / `repair`） | `report_only`、`evidence_catalog`、`semantic_core`、`semantic_pipeline` | 审计/修复 JSON（**主流程不调用，opt-in**） |
| `observability` | `review.py`（CLI） | 自身 | 审查提示 |
| `salvage-replay` | `mechanical_salvage.py`（CLI） | `fidelity`、`plan_synthesizer`、`semantic_pipeline`（延迟导入） | 重放结果目录 |

## 5. 模块清单（16 个）

| 类别 | 文件 |
| --- | --- |
| 入口(8) | `semantic_pipeline.py`、`run_semantic_batch.py`、`verify_semantic.py`、`preview.py`、`preconditions.py`、`review.py`、`mechanical_salvage.py`、`report_only.py`（仅历史直调兼容） |
| 库(6) | `semantic_core.py`、`plan_synthesizer.py`、`symbolic_queries.py`、`evidence_catalog.py`、`report_readiness.py`、`fidelity.py` |

Prompt 版本：`prompts/versions/` 共 14 个（v3.5 – v3.17），由 `prompts/registry.py` 统一注册。
推荐稳定版 `semantic-v3.16`，实验版 `semantic-v3.17`。
