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
