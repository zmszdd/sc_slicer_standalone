# 阶段二工程结构

## 目录总览

```text
tools/report_constraints_v2/
├── README.md                 # 操作说明（唯一入口是仓库根目录的 `main.py`）
├── STRUCTURE.md              # 本结构说明
├── MIGRATION.md              # 旧路径到新路径的映射
├── semantic_pipeline.py      # 主流程 CLI
├── run_semantic_batch.py     # 批量 CLI
├── verify_semantic.py        # 候选离线重放 CLI
├── prompts/                  # Prompt 注册表与冻结版本
│   ├── definitions.py        # P/I/V 集中式语义定义
│   ├── active.py             # 生产 Prompt 显式解析与哈希
│   ├── registry.py
│   └── versions/
├── tests/                    # 全部自动测试
├── docs/                     # 设计、状态和历史说明
├── evaluation/               # 冻结评测与运行报告
├── results/                  # 本地运行产物
├── samples/                  # 本地固定样例
└── review_samples/           # 人工审核材料
```

## 唯一入口

对外的唯一入口是仓库根目录的 `main.py`：

当前完整依赖环境位于 `/root/.local/share/uv/tools/halmos/bin/python`；系统 Python
没有 Z3。下列 `python` 表示已激活等价环境，未激活时请换成该完整路径。

```bash
cd /root/sc_slicer_standalone
python main.py <command> [参数...]           # 阶段二 / 工程命令
python main.py stage2 <command> [参数...]    # 同上，显式前缀写法
python main.py test | versions | doctor | status | frozen
```

`main.py` 只做分发：参数原样转发给对应脚本，子进程退出码原样返回。不要在 `main.py` 里实现阶段逻辑，也不要在本目录新增入口文件。

本目录的 Python 文件分两类，`main.py` 顶部的 `STAGE2_COMMANDS` 与 `LIBRARY_MODULES` 两张表就是权威清单：

| 类别 | 数量 | 说明 |
| --- | ---: | --- |
| 入口脚本 | 8 | 有 `if __name__ == '__main__'`；根入口只公开仍有维护价值的流程 |
| 库模块 | 6 | 无 `__main__`，只被 import |

为什么保留这些脚本的 `__main__` 而不删：冻结评测报告、`HANDOFF.md` 和 `docs/` 中的历史命令必须继续可重放。它们是历史命令，不是推荐入口。

自行判定某个文件属于哪一类：

```bash
cd tools/report_constraints_v2
grep -l "if __name__" *.py     # 有输出的就是入口脚本
```

## 根目录 Python 文件职责

> 下表按职责描述各文件。推荐入口始终是仓库根目录的 `main.py`。

### 主入口

| 文件 | 作用 |
| --- | --- |
| `semantic_pipeline.py` | 报告筛选、两步模型调用、规则化、Z3 和输出 |
| `run_semantic_batch.py` | 限量并发运行多个真实报告 |
| `verify_semantic.py` | 不调用模型，重放证据、公式和 Z3 结果 |
| `preview.py` | `screen` 本地输入检查 / `report` 第一步预览 / `plan` 第二步预览 |
| `preconditions.py` | 可选：`audit` P 证据审查 / `repair` 受约束 P 修复 |
| `preview.py report` | 预览第一步将发送的报告文本 |
| `preview.py plan` | 预览第二步结构化输入 |

### 核心规则引擎

| 文件 | 作用 |
| --- | --- |
| `semantic_core.py` | P/I/V schema、类型、编译与基础校验 |
| `plan_synthesizer.py` | 形式计划校验和确定性公式合成 |
| `symbolic_queries.py` | SMT/Z3 查询和 witness 校验 |
| `evidence_catalog.py` | 原文片段编号、ID 回填与证据映射 |
| `report_readiness.py` | 提取前信息充分性门 |
| `review.py` | 分流与可观察变量审查（同时是 `observability` 命令） |
| `fidelity.py` | 数值约束与零地址保真守卫 |
| `mechanical_salvage.py` | 显式启用的非语义机械修复 |

### 报告输入和辅助入口

| 文件 | 作用 |
| --- | --- |
| `report_only.py` | 报告解析、模型传输、DeepSeek 私密配置 |
| `preview.py screen` | 本地检查案例文件和输入；不是提取后筛选 |
| `preconditions.py audit` | 可选 P 证据/时序审查 |
| `preconditions.py repair` | 受约束 P 修复 |
| `mechanical_salvage.py` | 重放机械修复结果 |

`report_only.py` 仍保留少量历史 CLI 兼容代码，但当前职责是报告解析、表达式编译和
DeepSeek 传输库；根入口不再公开早期 `report-only` / `legacy-verify` / 演示命令。

## Prompt 管理原则

- 所有运行时版本从 `prompts/registry.py` 获取。
- 主流程通过 `prompts/active.py` 解析最终 Prompt，不直接追踪版本继承链。
- P/I/V 的人类可读规范只在 `prompts/definitions.py` 维护。
- `prompts/versions/` 中每个文件对应一个冻结实验版本，内容不可原地改写。
- 功能开关集中在注册表，不在主流程重复写版本元组。
- 新版本新增文件；不要复制一套新的 pipeline。

使用 `python main.py preview-prompt --part definitions|element|formal` 可查看集中定义或
生产流程实际使用的最终文本；该命令不读取 API Key，也不调用模型。

## 冻结资产

阶段一 Rust 源码、`run.sh` 和 v1 ZIP 归档一旦定稿
不得原地改写，否则历史实验无法重放。清单在仓库根目录 `PROTECTED_HASHES.json`：

```bash
python main.py frozen        # 校验，有漂移则退出码 1
python main.py frozen --write  # 确认是预期变更后重新生成
```

覆盖范围见 `main.py` 的 `FROZEN_SCOPES`。`.slicer_cache.json` 是可变的运行
缓存，故意不纳入冻结清单。

## 产物与源码的边界

- `evaluation/`、`results/` 中的 JSON/SMT/响应属于实验产物，不是运行时代码。
- `docs/` 中的历史报告不控制程序行为。
- `tests/` 可以读取冻结产物做重放，但不能覆盖产物。
- `config/stage2_deepseek.local.env` 位于项目根目录且被 Git 忽略，任何阶段二文件都不得保存
  API Key。
