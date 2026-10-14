# 阶段二目录迁移说明

本次整理只改变工程组织和版本注册方式，不改变冻结 Prompt 文本、P/I/V 逻辑或历史实验
产物。阶段一和阶段三未修改。

## 路径迁移

| 旧路径 | 新路径 | 迁移后引用方式 |
| --- | --- | --- |
| `semantic_prompts.py` | `prompts/versions/semantic_prompts.py` | 通过 `prompts.registry` 获取 |
| `semantic_prompts_v*.py` | `prompts/versions/semantic_prompts_v*.py` | 通过 `prompts.registry` 获取 |
| `test_*.py` | `tests/test_*.py` | 使用新的 unittest discover 命令 |
| 根目录除 `README.md` 外的 `*.md` | `docs/*.md` | 从 README 使用 `docs/...` 链接 |

Prompt 迁移前后 SHA-256 保持不变。历史冻结评测中的旧文件名仍保留为清单标签；读取源码
时已映射到 `prompts/versions/`。

## 代码引用注意事项

旧代码：

```python
import semantic_prompts_v317 as prompts
```

新代码若只需指定版本：

```python
from prompts.registry import module_for

prompts = module_for('semantic-v3.17')
```

测试若必须直接比较某个冻结模块：

```python
from prompts.versions import semantic_prompts_v317 as prompts
```

不要再在 `semantic_pipeline.py`、`verify_semantic.py` 或批处理脚本中逐个导入所有 Prompt。
版本功能判断使用 `prompts.registry` 中的集合，例如 `PLAN_VERSIONS`、
`NUMERIC_GUARD_VERSIONS`、`LOCAL_REPAIR_VERSIONS`。

## 命令迁移

旧测试命令：

```bash
python -m unittest discover -s tools/report_constraints_v2 -p 'test_*.py' -q
```

新测试命令：

```bash
/root/.local/share/uv/tools/halmos/bin/python -m unittest discover \
  -s tools/report_constraints_v2/tests \
  -t tools/report_constraints_v2 -p 'test_*.py' -q
```

主流程命令不变：`semantic_pipeline.py`、`run_semantic_batch.py` 和
`verify_semantic.py` 仍保留在阶段二根目录。

## 后续新增文件规则

- 新 Prompt：`prompts/versions/semantic_prompts_vNNN.py`，并登记到 `registry.py`。
- 新测试：`tests/test_*.py`。
- 当前设计/状态文档：`docs/`。
- 单次实验报告：`evaluation/<run-id>/REPORT.md`。
- 不要在阶段二根目录继续新增散乱的 Prompt、测试或报告文件。

## 已删除的退役分支

早期“切片绑定/旧阶段三接口”实验已与当前报告驱动主线脱节，且对应切片未编译成功。
已删除 `pipeline.py`、`consumer.py`、`schema.py`、`profiles.py`、`prepare.py`、
`verify.py`、`tests/test_pipeline.py`、`docs/V2_REPORT.md`、`artifacts/` 及其专用
Panoptic 样例/结果。不要再引用这些路径；当前阶段二只使用
`semantic_pipeline.py` 产生待绑定的 `stage3-spec.json`。

同时删除了无调用者的 `prepare_id_demo.py` 和 `prepare_semantic_demo.py`。

## 2026-09-21 第二轮整理：合并与删除

| 变化 | 说明 |
| --- | --- |
| `review_semantics.py` | **删除**。核心函数 `relationship_review` 并入 `report_only.py`，消除 `semantic_core → review_semantics` 的倒置依赖；其独立 CLI 一并删除，V/I 关系检查仍由 `compile_bundle` 在 `verify` 中执行。历史 `results/**/semantic-review.json` 原样保留。 |
| `preview_report_input.py` + `preview_formal_input.py` | **合并**为 `preview.py report` / `preview.py plan`（原两个脚本无任何代码引用）。 |
| `run_report_batch.py` + `report_cases.json` | **删除**。零引用：0 个 evaluation 目录、0 处 README/HANDOFF；已被 `run_semantic_batch.py` 取代。 |
| `numeric_fidelity.py` / `address_fidelity.py` | **保留不合并**。两者公开 API 都叫 `check_plan`，合并会强制重命名，波及 9 处 import 与 3 个测试文件，收益仅为少一个文件。 |
| `prompts/registry.py` | **不改懒加载**。实测：18 个 prompt 版本模块合计仅 2.8 ms，而 `import semantic_pipeline` 共约 280 ms（其中 z3 约 90 ms、`importlib.resources`/`typing`/`email` 约 100 ms）。改造需复制 18 条 name→version 映射，属净负收益。 |

备份：`archives/stage2_refactor_20260921/`（含被删/被合并前的原始文件）。

## 2026-09-21 第三轮：同层合并 + 入口收敛为阶段二

| 变化 | 说明 |
| --- | --- |
| `numeric_fidelity.py` + `address_fidelity.py` | **合并**为 `fidelity.py`，导出 `check_numeric_plan` / `check_address_plan`（原名都叫 `check_plan`，合并必须重命名）。 |
| `automatic_triage.py` + `review_observability.py` | **合并**为 `review.py`（求解后的分流与审查层）；它的 `main()` 就是 `observability` 命令。 |
| `main.py` | **不再包含阶段一**。`stage1` 子命令、`STAGE1_ENTRY`、`_stage1()`、`os.access` 全部移除；阶段一请直接用 `./run.sh`。 |
| `main.py` 模型默认 | 阶段二全流程默认官方 DeepSeek：`run` 注入 `--provider deepseek`，`batch` 再注入 `--model deepseek-flash`。**只在调用者未指定 provider/model 时注入**，因此测试用的离线传输与历史命令不受影响。 |
| `evaluation/fresh_holdout_01/manifest.json` | `code_sha256` **重新基线**：`automatic_triage.py`→`review.py`，`numeric_fidelity.py`/`address_fidelity.py`→`fidelity.py`。该批次 `attempted == 0`（从未产出结果），因此不存在被伪造的出处；已写入 `rebased_utc` / `rebased_reason`。 |

为什么没把 pipeline 的 `--provider` 默认值直接改成 `deepseek`：有 4 个测试文件用
`patch.object(report_only, 'extract')` 拦截调用并依赖默认 provider 为离线传输；
若把默认改成 deepseek，这些测试会打到真实 API。改在 `main.py` 注入既满足"全流程
DeepSeek"，又不破坏测试安全边界。

备份：`archives/stage2_refactor_20260921/`。

## 2026-09-21 第四轮：进一步消除冗余流程

| 变化 | 说明 |
| --- | --- |
| `screen_cases.py` -> `preview.py screen` | `preview.py` 现在承载三个同层的本地检查/预览模式：`screen` / `report` / `plan`。 |
| `audit_precondition_support.py` + `repair_preconditions.py` -> `preconditions.py` | 两个可选分支合成一个模块，子命令 `audit` / `repair`。**两者原本都不被 `semantic_pipeline` 调用**，仍是 opt-in。 |
| `replay_mechanical_salvage.py` -> `mechanical_salvage.py` | 该模块现在同时是库（管线用它）和 CLI（`salvage-replay` 命令）。 |
| 命名冲突处理 | `main`→`audit_main`/`repair_main`；`make_payload`→`make_repair_payload`（audit 侧保留原名）；`PROMPT`→`REPAIR_PROMPT`（否则 repair 的定义会静默覆盖 audit 的）。 |

**程序化合并的教训**：整模块搬运时，Python 对顶层重名静默取最后一个定义。已加入
重名检测（`def`/`class`/`NAME =`），合并后必须跑一次；本轮据此发现并修掉了
`PROMPT` 覆盖。

备份：`archives/stage2_refactor_20260921/`（本轮 4 个文件已在合并前备份）。

## 2026-09-22：活动目录收敛与退役文件归档

| 变化 | 说明 |
| --- | --- |
| `tools/report_constraints/` | **删除活动副本**。该目录是已退役 v1，删除前已逐文件核对 `archives/report_constraints_v1_20260912.zip`，归档无缺失且 CRC 正常。 |
| `prompt_versions/` | **删除重复快照目录**。v3.0--v3.4 已保存在 `archives/stage2_v3_removal_20260922/`；当前冻结版本统一位于 `prompts/versions/`。 |
| `prepare_observable_demo.py`、`verify_report_only.py` | **移出活动源码树**。它们只服务旧演示/旧候选验证，备份位于 `archives/stage2_legacy_cleanup_20260922/`。 |
| `INCIDENT_20260922.md` | **移入同一归档**，避免事故记录与当前操作文档混排。 |
| `main.py` | 删除三个退役命令，并把入口分为日常流程与高级诊断；默认路径不再暴露旧演示和旧 verifier。 |

`evaluation/`、`results/`、`samples/`、`review_samples/` 没有删除：当前回归测试仍读取其中的
冻结响应、SMT、金样例和人工审核材料。它们不参与生产控制流，但不是无引用文件；若后续要把
活动树继续缩小，应先把测试路径统一迁到单独的测试夹具归档，而不是直接删除。

## 2026-09-22：S1–S9 重构记录（阶段二收敛为 `lib/` + `cli/`）

目标：阶段二只保留**入口层 `cli/`** 与**共享库层 `lib/`**，实现代码不再留在
阶段二根目录；根目录只保留迁移期兼容 shim。**只搬组织，不改语义**：迁移后的
函数体逐字未改，并由备份做了字节级比对。

每一步的原始文件都备份在 `archives/stage2_refactor_20260921/S<n>_originals/`。

| 步骤 | 做了什么 |
| --- | --- |
| S1 | 建立 `lib/`、`cli/` 两个空层；`main.py` 的脚本解析改为按 `cli/` → `lib/` → 根目录的顺序查找（`_script_path`），并加入 `STAGE2_ARG_PREFIX` 与 `LIBRARY_MODULES` 两张表 |
| S2 | `semantic_core.py` → `lib/semantic_core.py`；`plan_synthesizer.py` → `lib/plan_synthesizer.py` |
| S3 | `report_only.py` → `lib/report_only.py`；**删除其中的 `main()` / `VERSION` / `__main__`**（死代码）；因下沉一层而修正 `ROOT` 的 `parents` 深度；`tests/__init__.py` 补 `lib/` 与 `cli/` 到 `sys.path` |
| S4 | `semantic_pipeline.py` → `cli/semantic_pipeline.py`；`preview.py` → `cli/preview.py`；`preconditions.py` → `cli/preconditions.py` |
| S5 | `evidence_catalog.py` + `report_readiness.py` → **合并**为 `lib/ingest.py`（两个旧名现在指向同一个模块对象） |
| S6 | `symbolic_queries.py` → `lib/solving.py`；`fidelity.py` → `lib/salvage.py`（纯搬运）；同时修正 `tests/test_main_entry.py` 的脚本存在性判断口径（原来只看根目录，与 `main.py` 的 `cli/` → `lib/` → 根目录顺序不一致，造成假失败） |
| S7 | `review.py` → 并入 `lib/solving.py`（80 → 226 行）；`observability` 命令恢复可用 |
| S8 | `mechanical_salvage.py` → 并入 `lib/salvage.py`（180 → 385 行）；`salvage-replay` 命令恢复可用 |
| S9 | `run_semantic_batch.py` + `verify_semantic.py` → **合并**为 `cli/batch_verify.py`（330 行）；`batch` 与 `verify` 命令恢复可用 |

### S3：`report_only.main()` / `VERSION` 已删除

`lib/report_only.py` 不再有 `main()`、`VERSION` 常量或 `__main__` 块。
全仓库检索确认无任何调用方引用它们。根入口从未公开过 `report-only` /
`legacy-verify` / 演示命令，因此这一步不影响任何可用命令。

### S8：`mechanical_salvage` 的 `__file__` 与自引用 import

合并 `mechanical_salvage.py` 进 `lib/salvage.py` 时踩到两个坑，都已修复：

1. **自引用 import。** 被并入的文件里有
   `from fidelity import check_address_plan, check_numeric_plan`。合并后
   `fidelity` 就是本模块自己的 shim，该行变成自引用，抛
   `ImportError: cannot import name ... from partially initialized module`。
   已删除该行（名字现在就在本文件内）。
2. **`__file__` 深度。** 子进程调用原本写作
   `Path(__file__).with_name('semantic_pipeline.py')`，搬到 `lib/` 后
   `with_name` 会指向 `lib/semantic_pipeline.py`（不存在）。已改为
   `Path(__file__).resolve().parents[1] / 'semantic_pipeline.py'`，即阶段二根目录
   下的 shim。

**为什么必须指向根目录的 shim**：`subprocess [sys.executable, <script>]` 会把
**子进程的 `sys.path[0]` 设为该脚本自己所在的目录**。若直接生成 `cli/x.py`，
子进程的裸名 import（`from fidelity import ...`）就会 `ModuleNotFoundError`。
指向根目录 shim 后，`sys.path[0]` 是阶段二根目录，所有 shim 都在那里。

### S9：`cli/batch_verify.py` 的 `HERE` 修复

`run_semantic_batch.py` 原本用 `HERE = Path(__file__).resolve().parent` 表示
阶段二根目录，并据此生成子进程 `HERE / 'semantic_pipeline.py'`。搬到 `cli/`
后 `parent` 变成了 `cli/`，同一个表达式会指向 `cli/semantic_pipeline.py`——
正是上一节说的"不能直接生成 `cli/` 文件"的情形。已改为：

```python
HERE = Path(__file__).resolve().parents[1]  # 阶段二根目录（shim 所在）
```

`verify_semantic.py` 的模块级 argparse 被包进 `verify_main()`（函数体逐字未改，
只加缩进），并在文件末尾加入统一分派器：

```python
if __name__ == '__main__':
    if sys.argv[1:2] == ['verify']:
        del sys.argv[1]           # 去掉 main.py 注入的前导参数
        raise SystemExit(verify_main())
    raise SystemExit(main())
```

同时修正 `lib/salvage.py` 的 `__main__` 块：`replay_main()` 改为
`raise SystemExit(replay_main())`，使退出码能真正传播。

### 迁移期的三条经验

1. **合并会制造自引用 import。** 若 B 里有 `from A import name`，而 `name` 定义
   在 A 中，合并 A+B 后该行会经 A 的 shim 变回自引用。必须删掉这行。
2. **顶层重名会静默覆盖。** Python 对同一模块里的重复顶层定义取最后一个。历史上
   `preconditions.py` 的 `PROMPT` 就这样被静默覆盖过。合并前后都要做
   `def` / `class` / `NAME =` 的重名扫描。
3. **shim 的 `__main__` 转发不能省。** 省略后会静默退出 0 而不执行任何逻辑，
   且没有测试能发现。详见 `STRUCTURE.md` 的「shim 的 `sys.modules` 别名机制」。

### 本节取代下列旧说法

S1–S9 之后，本文档前面几节中这几句已经过时，以本节为准：

- 「主流程命令不变：`semantic_pipeline.py`、`run_semantic_batch.py` 和
  `verify_semantic.py` 仍保留在阶段二根目录。」
  → 现在实现位于 `cli/semantic_pipeline.py` 与 `cli/batch_verify.py`
  （`batch_verify.py` 是 `run_semantic_batch.py` + `verify_semantic.py` 的合并体）；
  阶段二根目录已无同名文件，旧名字由 `lib/compat.py` 提供（见 S11 一节）。
- 「`numeric_fidelity.py` / `address_fidelity.py` 保留不合并」（第二轮）
  → 第三轮已合并为 `fidelity.py`，S6/S8 又并入 `lib/salvage.py`。
- 「`evaluation/fresh_holdout_01/manifest.json` 的 `code_sha256` 重新基线」
  → S10 再次重新基线，并改用「按现在真正包含该代码的文件解析」的新规则，
  映射表见 `STRUCTURE.md` 的「另一套冻结哈希」一节。

## 2026-09-22：S11 收尾 —— 删除 14 个兼容 shim

目标：阶段二根目录 **0 个 `.py`**，同时保持全部旧模块名可用。做法是**用 1 个文件
取代 14 个别名文件**。

| 项 | 变化 |
| --- | --- |
| 新增 | `lib/compat.py`：`ALIASES` 表（14 个旧名字 → 10 个真实模块）+ `sys.meta_path` finder（延迟解析、`insert(0)`） |
| 删除 | 根目录 14 个别名文件：`semantic_core.py` `plan_synthesizer.py` `report_only.py` `evidence_catalog.py` `report_readiness.py` `review.py` `symbolic_queries.py` `fidelity.py` `mechanical_salvage.py` `semantic_pipeline.py` `preview.py` `preconditions.py` `run_semantic_batch.py` `verify_semantic.py` |
| 注册点 | `main.py`、`tests/__init__.py`、`cli/__init__.py`、`lib/__init__.py` 各调一次 `compat.install()` |
| 改显式 import | `evaluation/` 8 个（6 个 `evaluate.py` + 2 个 `select.py`）+ `review_samples/` 2 个，共 23 处改指 `lib.*` / `cli.*`，不再依赖别名 |
| 3 处子进程 | 由"生成根目录别名文件 + 依赖子进程 `sys.path[0]`"改为 `python -m cli.semantic_pipeline` + `cwd=阶段二目录` |
| 测试 | `test_main_entry.py` 的 `test_stage2_layout_is_where_the_entry_point_expects_it` 改用 `entry._script_path(...)` 判断，不再断言根目录文件存在 |
| `doctor` | 新增自检 `历史模块名兼容层(14 个)` |
| 冻结哈希 | `evaluation/` 清单中 9 个值因 `lib/salvage.py` 改动而重新基线；46 个键全部可复算 |

### 为什么 `lib/__init__.py` / `cli/__init__.py` 也必须是注册点

`cli/__init__.py` 是唯一能覆盖 `-m` 子进程的位置：`python -m cli.semantic_pipeline`
会先导入 `cli` 包，其 `__init__` 在子进程里必然执行，finder 得以注册。

但它们**不能单独作为机制**：`cli/`、`lib/` 的消费者 import 的是旧名字
（`from fidelity import ...`），从不 `import lib`，所以这两个 `__init__` 在主进程里
根本不会被执行。主进程依赖 `main.py` 与 `tests/__init__.py` 两处注册。

### 为什么必须 `insert(0)` 而不是 `append`

删掉旧文件名后 `cli/` 与 `lib/` 都在 `sys.path` 上。若让 PathFinder 先跑，
`import report_only` 会把 `lib/report_only.py` 加载为名为 `report_only` 的**独立
模块**，与 `lib.report_only` 变成两份互不相干的对象。`insert(0)` 才能保证别名就是
真模块本身（`sys.modules['fidelity'] is sys.modules['lib.salvage']` 为真）。

### 执行顺序（每步都跑全套验证）

1. 装 finder + 4 个注册点 + 改 10 个脚本的 import → `doctor` / 266 test / 21 frozen / 3 replay / 漂移 / 11 命令 全绿
2. **演练**：把 14 个文件移到 `/tmp` → 全绿（仅剩计划内的 `test_main_entry.py` 断言）
3. 恢复 → 改 3 处子进程 + 1 处断言 → **再演练，零文件全绿** → 正式删除

第 2、3 步的两次演练把"删除不可逆"变成了"演练全绿后再删"。

### 已知损失

`docs/` 中历史实验报告里的命令行（`tools/report_constraints_v2/semantic_pipeline.py ...`、
`.../verify_semantic.py ...` 等）不再可直接重放。这些报告是历史记录，按
"docs/ 中的历史报告不控制程序行为"的约定未改写；重放请改用
`python main.py run` / `python main.py verify`。

## 2026-09-22：S12 —— 断言策略开关 + `V` 定义修正

### 为什么要加开关，而不是直接放宽

`acceptance_status` 原先把两类东西混在一起否决：真正的结构失败（公式 unsat、
I/V 倒置），和模型自报的歧义/局限/未决项。在 72 个可重算 run 上实测，前者只占
4 个，后者却把通过率压在 0/72 —— 等于"越诚实越不通过"。

直接放宽不可行：`cli/batch_verify.py` 的
`require(bundle == saved, 'bundle replay mismatch')` 是严格相等比较，任何输出
变动都会让 78 份冻结产物与 8 个测试文件失效。所以改为**加形参 + 加开关**：
默认 `legacy` 逐字节不变，新行为经 `--claim-verdict signals` 显式启用，
并把策略写进 `provenance.claim_verdict_policy` 供 `verify` 重放。

`main.py` 里的注入是与 DeepSeek 注入**分开**的两组默认值
（`STAGE2_VERDICT_DEFAULTS` vs `STAGE2_DEEPSEEK_DEFAULTS`）：
`tests/test_main_entry.py` 断言了后者返回的**精确 argv**，合并会破坏该断言。

### 顺带修正的规范缺陷

`prompts/definitions.py` 中 `V` 的 `meaning` 原为
"a … change that **makes I false** under the same applicability context"。
但管线正是靠 `P AND V AND I` unsat 来**验证** `V` 确实否定 `I`；定义里已经假定
了结论，该检查就退化为套套逻辑。现改为独立于 `I` 的可观察事实，把"与 `I`
矛盾"写成待验证的义务。

这段文本**不进入运行时提示词**（运行时用冻结的 `prompts/versions/*`），
所以不影响任何重放；受影响的只有 `preview-prompt --part definitions` 的输出，
以及 `tests/test_prompt_active.py` 里的一条断言（已同步改为校验独立性）。
`prompts/active.py` 校验的 `ELEMENT_CONTRACT_MARKERS` /
`FORMAL_CONTRACT_MARKERS` 是**另两个常量**，本次未动 —— 改它们会一次性破坏
全部 14 个冻结版本。

### 本次重设的哈希

`semantic_core.py`、`semantic_pipeline.py` 共 10 个 key，分布在 7 份清单
（`deepseek_flash_pilot_01`、`deepseek_v41_fresh_01`、`fresh_holdout_01`
的 `manifest.json`，以及 `prompt_v314/v315×2/v316_holdout_01` 的
`SELECTION.json`）。`prompts/definitions.py` 不在 `CODE_PATHS` 中，故不在哈希
约束范围内。

## 2026-10-13：S13 —— 架构收口（新 SC 生成废弃 + 管线/入口简化 + 基线修复）

### 废弃"生成新 SC"工作线

新 SC（smart contract）生成/注入是**纯评测侧**工作：主管线对它零 import，
废弃不触碰任何运行时代码。按零删除归档惯例执行：

- `evaluation/new_sc_injection_01`、`new_sc_injection_02` 整体 `git mv` 至
  `evaluation/archive/`（含未提交内容）
- 删除 `docs/new_sc_flow.svg`、`pipeline_overview.svg` 及两个生成器脚本
- 库侧在途改动回滚：`lib/solving.py` / `lib/stage3_consistency.py` /
  `tests/test_stage3_contract.py` 中仅为新 SC 服务的
  `queries_from_piv` / dsl 引用全部移除（`git diff` 对 HEAD 为空）
- stage2→stage3 回路由 `stage3-feedback` 承担（见
  `docs/STAGE2_CURRENT_STATUS.md` 2026-10-12 条目）

### 管线与入口简化（行为逐字节不变）

- `cli/semantic_pipeline.py`：readiness/elements 两段近重复的模型调用重试
  环合并为共享骨架 `_bounded_model_call`（per-attempt 工件目录名、
  attempts.json 键序、outcome 标签、可重试异常元组全部保持不变）；
  两张平行的错误消息表（formal_repair_fields / formal_retry_hint 背后）
  合并为单一注册表 `_FORMAL_ERROR_RULES`，48 个消息用例逐一比对零失配
- `main.py`：4 个默认值注入字典 + 3 个包装函数收敛为单一
  `STAGE2_ARG_DEFAULTS` 表 + `_with_arg_defaults`
- 死代码清理：`cli/preconditions.py` 两处误缩进的 `main()` 尾随调用
  （成功 audit/repair 后向 stderr 重打印 usage）、`lib/salvage.py`
  replay_main 不可达的 `raise SystemExit(main())`

### 基线测试修复（投入工作前提：392 全绿）

四个失败在纯 HEAD 上复现，均为历史遗留而非本次引入：

- `test_automatic_triage` ×2：`from_bundle` 自 416d78a 起路由与
  continuation gate 对齐（空 claims → abstain），测试包改为携带完整
  claim（`complete_review_bundle` 同构），`candidate`/`review` 路由照旧覆盖
- `test_semantic_batch`：416d78a 将三级重试默认值 0→1，`retry_count`
  期望从 0 更新为 2（opencode 下 readiness 重试被 provider 门控为 0）
- `test_semantic_core`：`formalization requires at least one claim`
  补入 `BOUNDARY`（未列出本就默认 REJECT，仅满足 ast 覆盖守卫，分类不变）

### 验证

392 测试全绿；`doctor` 全过；三个时代的冻结 run 重放（live4/live3/
final_holdout_01 各一例）`offline_verified: true`。

已知且如实上报：`fresh_holdout_01/manifest.json` 的 8 个 `code_sha256`
在 HEAD 上即已全部漂移（冻结于更早迭代），本次重构进一步远离该基线；
重设哈希不在本次范围内。

## 2026-10-13：S14 —— 修复环反馈定位（三处同族缺陷）

五例盲测批（见 `docs/STAGE2_CURRENT_STATUS.md` 同日条目）暴露一个
共同缺陷家族：**确定性校验的报错只报家族名、不带定位**，修复模型拿
不到可操作的信息，只能盲改或原样重交。三处修复：

1. 数值保真门 `numeric P literal changed` 补计划侧常量
   （`_numeric_detail` 增 `plan uses` 段；`constants - literals`
   即模型实际写错的常量）
2. 空修复不再顶掉原始缺陷：`repair_error` 在
   `local repair made no change` 时保持上一次实质错误
   （此前第三次修复请求里原始数值错误已被覆盖为循环指令）
3. `expr_type` 的三个裸消息（`type/unit mismatch` /
   `unsupported multiplication types` / `unsupported operator/types`）
   补操作符与两侧操作数类型；`_FORMAL_ERROR_RULES` 相应规则改前缀
   匹配并新增 `_type_unit_hint` 透出 `Failing comparison` 定位

约束保持：报错前缀全部不变（BOUNDARY 三个条目改为带 `: ` 的字面
前缀，分类仍 REJECT）；frozen run 重放不受影响（重放不跑模型调用，
错误消息只进新 run 的 attempts 记录）。新增 3 个回归测试，
全量 396 项通过。

真实验证：Kinetiq（盲批中被拒案例）重跑转 `candidate_checks_passed`
（3 次调用、零重试——该轮首答即干净，通过本身归因于模型方差，
修复效果由单测钉死；修复环不再空转已在 refix_02 的 attempts 记录
中可见：字段确有改动、不再是字节级重交）。

## 2026-10-14：S15 —— 占位化防御（A 等价折叠门 + B advisory 审查）

盲批 03 的忠实性弱点（weakened 28/30、4/5 collapsed_facts）集中在
占位化家族，其中两类是**机械可查**的，据此做两项修复：

1. **A：重复谓词门升级为等价感知**（`lib/plan_synthesizer.py`）
   - `identical_p_predicates` 从 JSON 严格相等改为 `predicate_keys`
     键折叠：谓词两侧操作数规范化（裸字符串与 `{"symbol": ...}` 同键，
     `_operand_key`）；`eq/ne` 两侧排序折叠；`lt/le` 镜像为 `gt/ge`
     （`_MIRROR`）后按方向折叠——镜像对 `real ne derived` /
     `derived ne real` 判同一谓词（GTE 盐值对）
   - 第二键 `zero` 族：同一符号对 `const 0` 的 `gt/ge/le/ne` 全折叠
     ——`borrow_value > 0` 与 `borrow_value != 0` 判同一谓词
     （Monetrix 两条事实实为一条）；不同符号互不影响
   - **语义注意**：镜像对严格等价；zero 族是"同可观察量的零界
     至多承载一条报告事实"的近似（>0 与 ≠0 不等价但都不编码
     原文事实），按门的既有职责（每个 P 来源一条独立谓词）收紧
2. **B：`placeholder_predicate_review` advisory**（同文件）
   - `truth_placeholder`：来源文本含结构推导线索
     （`STRUCTURAL_DERIVATION_CUES`：keccak/create2/salt、hash of、
     derived from、abi.encode）而谓词是裸 truth 符号
   - `trivial_zero_bound`：非严格零界（`ge/le` vs `const 0`）且原文
     无字面 zero——恒真下界不承载事实
   - 恒不阻断（`blocks_candidate_acceptance: False`）；经
     `placeholder_predicate_review` 功能键写入
     `placeholder-predicate-review.json` 并纳入接口哈希链，
     `verify` 按录制功能键回放

**行为变更披露**：录制时带 `duplicate_predicate_gate=True` 的历史
run 重放会因新折叠键失败——批 03 的 /tmp run 中 3/5（GTE 镜像对、
两例 Monetrix）如今 `verify` 被拒，正是该门要拦的塌缩家族；
仓库内 frozen run 之前已全量扫过（65 verified / 0 failed）不受影响。

验证：全量 403 项测试通过（+7：镜像对、zero 族、异符号零界、
truth 占位、纯状态事实不标、无字面 zero 的零界、有字面 zero 不标）；
Monetrix 真实重跑证明 B 落盘生效（2 个 trivial_zero_bound 旗标），
该轮 plan 用了不同符号未触发 A、最终因 P∧V 不可行诚实拒绝
（fail-closed，与占位化无关的家族）；`verify` 重放全过。
