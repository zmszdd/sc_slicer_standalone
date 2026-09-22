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
  根目录同名文件只剩 3–4 行的兼容 shim。
- 「`numeric_fidelity.py` / `address_fidelity.py` 保留不合并」（第二轮）
  → 第三轮已合并为 `fidelity.py`，S6/S8 又并入 `lib/salvage.py`。
- 「`evaluation/fresh_holdout_01/manifest.json` 的 `code_sha256` 重新基线」
  → S10 再次重新基线，并改用「按现在真正包含该代码的文件解析」的新规则，
  映射表见 `STRUCTURE.md` 的「另一套冻结哈希」一节。
