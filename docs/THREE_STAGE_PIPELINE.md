# SC_Slicer 三阶段流水线报告

更新时间：2026-10-30
项目目录：`/root/sc_slicer_standalone`

## 1. 总览

流水线目标：判断智能合约漏洞报告中的 PoC 是否与报告声称的漏洞效果一致。

- 阶段一（`src/` Rust slicer + `run.sh`）：对 PoC/合约代码切片，提取与目标效果相关的执行路径，输出可编译的 `.sol` 切片。
- 阶段二（`tools/report_constraints_v2/`）：把漏洞报告自然语言规则化为 P/I/V 不变量，输出 `stage3-spec.json` 等可审计规格。
- 阶段三（`tools/stage3/`）：把阶段二不变量绑定到真实 Solidity 代码，生成补丁合约，用 Foundry 跑原始版与补丁版差分，回填 `stage3-consistency.json`。

本报告重点是阶段三主线、三阶段配合通道与投产评估。

## 2. 数据流

```text
code4rena report + PoC + contract
        │
        ├─ 阶段一 ./run.sh
        │     └─ results/<run>.sol (+ .v2.json)          # 可编译切片
        │
        ├─ 阶段二 main.py run/batch
        │     └─ <stage2-run>/stage3-spec.json            # P/I/V + binding_contract
        │           + constraints.json + formalization.json
        │
        └─ 阶段三 main.py pipeline                        # 三阶段串联通道
              └─ stage3 assemble  -> cases/<name>/
                    ├─ src/        （来自阶段一切片或手工源码）
                    ├─ test/       （PoC Foundry 测试）
                    ├─ binding.json（符号→代码可观测表达式）
                    └─ stage2_run/ （阶段二三份产物副本）
              └─ stage3 run       -> runs/<run-id>/
                    ├─ original/ patched/ 两套 Foundry 工程
                    ├─ stage2/stage3-consistency.json
                    └─ stage3-summary.json
```

## 3. 各阶段职责与入口

### 阶段一

- 入口：`./run.sh`（Rust slicer，`cargo run --release -- ...`）。
- 输出：`results/slice_*.sol` 与 `results/slice_*.sol.v2.json`。
- 阶段一产物是阶段三 `--src` 的天然来源，但阶段三不依赖切片格式，接受任意可编译 `.sol` 文件或目录。

### 阶段二

- 入口：`python main.py run ...`（单案例）、`python main.py batch ...`（批量）。
- 输出目录核心三件套：`stage3-spec.json`、`constraints.json`、`formalization.json`。
- 阶段二只证明公式内部一致，不判断报告真假、不执行 PoC。

### 阶段三

- 入口：
  - `python main.py stage3 --case-dir <dir>`：单案例差分验证。
  - `python main.py stage3 assemble ...`：从阶段一/二产物组装案例。
  - `python main.py stage3 batch --cases-root <dir> --output <json>`：批量跑案例。
  - `python main.py pipeline ...`：组装 + 可选运行的一站式通道。
- 输出：
  - `runs/<run-id>/original/`、`runs/<run-id>/patched/`。
  - `runs/<run-id>/stage3-summary.json`（判定、forge 结果、code_query_results）。
  - `runs/<run-id>/stage2/stage3-consistency.json`（阶段二权威裁决回填）。

## 4. 三阶段配合通道

通道由 `lib/case_builder.py` 定义，只做复制与校验，绝不原地改写阶段一/二产物。

### 4.1 组装命令

```bash
python main.py pipeline \
  --name panoptic_builder_init \
  --src <stage1-slice.sol 或 src 目录> \
  --stage2-run <stage2-run 目录> \
  --binding binding.json \
  --test <PoC 测试文件或目录> \
  --run --run-id <run-id>
```

等价的两步写法：

```bash
python main.py stage3 assemble --name N --src S --stage2-run R --binding B --test T --out cases/N
python main.py stage3 --case-dir cases/N --run-id N_001
```

### 4.2 手工交接收契约

| 阶段三输入 | 来源 | 必需 |
| --- | --- | --- |
| `stage2_run/stage3-spec.json` | 阶段二 | 是 |
| `stage2_run/constraints.json` | 阶段二 | 是 |
| `stage2_run/formalization.json` | 阶段二 | 是 |
| `src/`（可编译 Solidity） | 阶段一切片或手工 | 是 |
| `test/`（PoC Foundry 测试） | 手工/阶段一 | 是 |
| `binding.json` | 手工或半自动 | 是 |
| `foundry.toml` / `remappings.txt` / `lib/` | 可选，复杂依赖时提供 | 否 |

`binding.json` 必须覆盖 `binding_contract` 中所有 `appears_in` 非空的符号；`patch.functions`
支持多文件、多函数，并可逐函数指定 `file` / `contract`（同名函数用 `contract` 消歧）。

### 4.3 批量命令

```bash
python main.py stage3 batch \
  --cases-root tools/stage3/cases \
  --output /tmp/stage3-batch-summary.json \
  --max-cases 0 --filter panoptic
```

每个案例在独立子进程运行，互不污染；汇总 JSON 含总数、成功/失败、裁决分布与逐案例 forge 状态。

### 4.4 并行编排（阶段一 ∥ 阶段二 → 阶段三）


阶段一吃代码/PoC、阶段二吃报告，互不依赖；编排器把它们并行启动，阶段三在二者
产物齐备后再 join。入口：

```bash
python main.py pipeline-run --manifest <case.pipeline.json>
python main.py pipeline-batch --manifests-root <dir> --output summary.json
```

manifest 契约见 `tools/pipeline/lib/manifest.py`（`pipeline-manifest/1`）：

```json
{
  "schema_version": "pipeline-manifest/1",
  "case_id": "panoptic_builder_init",
  "stage1": {"input": "...", "contract": "...", "variable": "...",
             "function": "...", "level": 2, "compile_guarantee": true,
             "output_slice": "runs/<case>/stage1/slice.sol"},
  "stage2": {"run_dir": "<stage2-run>"},
  "stage3": {"binding": "...", "case_dir": "...", "run_id": "..."}
}
```

- 阶段二支持两种模式：`run_dir`（复用已产物）或 `report` + `output` + `args`（真跑）。
- `stage3.binding` 与 `stage3.test` 均可省略：省略 `binding` 时阶段三自动绑定
  （`cli.stage3_bind`），省略 `test` 时使用自包含 flatten（PoC 测试函数内嵌在
  `src/` 中，与评估路径一致）。
- 每例写 `runs/<case_id>/timeline.json`，记录三阶段起止与 `overlap`。
- `--skip-stage1/2` 续跑，`--serial` 串行调试。
- 失败隔离：单边失败不触发阶段三，退出码非 0。

已用 `panoptic_builder_init` 验证：`overlap=true`，阶段三在二者完成后启动，最终
`violation_reproduced`。

## 5. 阶段三主线现状

### 5.1 已实现

- 单案例端到端：绑定校验 → 补丁 → Foundry → 差分 → 裁决回填。
- 两种补丁路径：
  - M1 参考补丁：`case/patched/` 存在则原样使用。
  - M4 AST 注入：把 P/I/V 翻译为 Solidity 断言注入函数体。
- 多文件/多函数/合约作用域注入（`lib/patch.py`）。
- 案例级 `foundry.toml` / `remappings.txt` / `lib/` 依赖透传。
- 批量运行与汇总（`cli/stage3_batch.py`）。
- 案例组装通道（`lib/case_builder.py` + `cli/stage3_assemble.py`）。
- 判定语义：
  - 原始通过 + 补丁在 I 断言失败 → `violation_reproduced`。
  - 两者都通过 → `violation_not_reproduced`（给定测试范围内）。
  - 原始失败 + 补丁通过 / 补丁在 P 失败 → `unknown/inconclusive`。

### 5.2 测试与回归

- 阶段三单元测试 13/13 通过（覆盖绑定、codegen、差分、单/多函数注入、组装校验）。
- 阶段二回归 484/484 通过。
- 批量运行 `tools/stage3/cases` 下 4 个案例：4/4 成功，裁决均为 `violation_reproduced`。

### 5.3 真实案例端到端复现

- 案例：`tools/stage3/cases/panoptic_builder_init`
- 对应报告：code4rena `2025-12-panoptic`（Panoptic Next Core）finding 17（`CUEQdPu878N`）。
- 漏洞：`BuilderWallet.init` 无访问控制，任意调用者可覆盖 `builderAdmin` 并 `sweep` 手续费。
- 源码：`code-423n4__2025-12-panoptic__a4361d6d8dc6420c09187d80ea1a7ce851d1ca36/contracts/RiskEngine.sol` 第 2296-2410 行。
- 结果：原始版 PoC 成功，补丁版失败于 `panic: assertion failed (0x01)`，安全路径通过；`consistency_verdict = violation_reproduced`。
- 产物：`tools/stage3/runs/panoptic_builder_init_001/`。

### 5.4 端到端串行验证（方案 A 已完成）

同一个真实案例 `panoptic_builder_init` 已完整跑通 阶段一 → 阶段二 → 阶段三：

- 阶段一：`stage1_input/BuilderWalletInitPoC.sol`（自包含扁平 PoC）经 `./run.sh`
  切片，产出 `results/slice_BuilderWalletInitPoC_*.sol`，forge test 通过。
- 阶段二：沿用 finding `CUEQdPu878N` 的 run（`stage3_smoke_01`）。
- 阶段三：`main.py pipeline --src <切片> --stage2-run ... --binding ... --test ... --run`
  组装案例并差分，结果 `violation_reproduced`。
- 产物：`tools/stage3/cases/panoptic_builder_init_stage1`、
  `tools/stage3/runs/panoptic_builder_init_stage1_001/stage3-summary.json`。

这证明串行链路无断点，且 `pipeline` 通道能直接消费阶段一切片。

## 6. 投产评估

### 6.1 可以做什么

- 对单个已绑定案例做可重放的动态一致性验证，适合开发/审计复核工具。
- 通过 `pipeline` 通道把阶段一/二产物组装成阶段三案例并批量运行。
- 已在一个真实案例上完整串通 阶段一 → 阶段二 → 阶段三。

### 6.2 尚不能直接全面投产

- 绑定已由 `cli.stage3_bind` 自动提出并 lint，失败 claim 会回退人工；吞吐仍受 LLM 调用约束。
- codegen 只支持有限 DSL 子集（and/or/not/implies/eq/ne/lt/le/gt/ge/add/sub），更复杂不变量无法注入。
- 复杂真实合约仍需人工预打包依赖（`foundry.toml`/`remappings`/`lib`），尚未自动解析 import 图。
- 阶段二权威裁决只用 `P_and_T`、`P_and_T_and_V`，更直接的 `P_and_T_and_not_I` 尚未接入权威路径（已知 TODO）。
- 真实案例只验证 1 个；缺乏批量负样本与统计置信度。

### 6.3 建议补齐顺序

1. `P_and_T_and_not_I` 接入阶段二裁决逻辑。
2. 绑定半自动化：由 `binding_contract` 生成 `binding.json` 草稿供人工确认。
3. import 图解析 + 自动生成 `foundry.toml`/`remappings`/`lib`。
4. 扩大真实案例回归集（目标 5-10 个，覆盖复现/未复现/绑定错误三类）。
5. 接入 CI 与冻结资产校验（现有 `main.py frozen`）。

## 7. 运行速查

```bash
# 单案例
python main.py stage3 --case-dir tools/stage3/cases/panoptic_builder_init

# 三阶段通道（组装 + 运行）
python main.py pipeline --name N --src slice.sol --stage2-run <dir> \
  --binding binding.json --test poc.t.sol --run --run-id N_001

# 批量
python main.py stage3 batch --cases-root tools/stage3/cases --output /tmp/summary.json

# 绑定骨架（从 stage2 binding_contract 生成，人工补 solidity_expr/patch/probe）
python main.py stage3 binding-skeleton --stage2-run <dir> --claim-id <id> --out binding.json

# 多 claim 逐条差分（bindings 目录下每个 <claim_id>.json）
python main.py stage3 multi --case-dir <case> --bindings-dir <dir> --run-id-prefix <p>

# 三阶段并行编排（单案例）
python main.py pipeline-run --manifest panoptic_builder_init.pipeline.json

# 全新自包含扁平案例（阶段二 + 自动绑定 + 差分）
python main.py case --case-dir <flatten_case> --out-dir runs/demo

# 三阶段并行编排（批量）
python main.py pipeline-batch --manifests-root pipeline_manifests --output /tmp/summary.json \
  --resume --skip-stage1

# 自动绑定（逐 claim，已有 binding 可用 --reuse 跳过）
python main.py stage3 bind --case-dir <case> --stage2-run <dir> --binding-rounds 3 --reuse

# findings.json -> report 草稿 + 可运行 manifest（匹配 flatten 后自动绑定）
python main.py manifest-gen --findings <findings.json> --out-dir <dir> \
  --flatten-root /root/poc_repro_work/verified_flatten_pass_1568_exact_cases

# 编排回归
cd tools/pipeline && python -m unittest discover -s tests

# 阶段三回归
cd tools/stage3 && python -m unittest discover -s tests

# 阶段二回归
python main.py test
```

## 8. 自动化回归

- 端到端串行链路由 `tools/pipeline/tests/test_e2e_pipeline.py` 固化：
  - `TestSerialChainReusingArtifacts`（默认，CI 安全）：复用已提交的阶段一切片与冻结阶段二 run，
    经 `lib.runner.run_pipeline` 组装并跑阶段三 forge 差分，断言 `violation_reproduced`。
  - `TestSerialChainFromStage1Input`（opt-in，`RUN_STAGE1_E2E=1`）：用 `run.sh` 从
    `stage1_input/BuilderWalletInitPoC.sol` 重新切片后跑同一链路。
- CI 门禁见 `.github/workflows/ci.yml`：`cargo test`、`python main.py test`、
  `python main.py frozen`、阶段三 `unittest`、pipeline `unittest`（含 e2e）。
