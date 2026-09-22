# 阶段二整理归档（2026-09-21）

## 已在此处的完整原件

| 文件 | 来源 | 说明 |
| --- | --- | --- |
| `review_semantics.py` | 第二轮 | 其 `relationship_review` 已并入 `report_only.py` |
| `run_report_batch.py` | 第二轮 | 零引用，已删除 |
| `report_cases.json` | 第二轮 | 只被 `run_report_batch.py` 读取 |
| `preview_report_input.py` | 第二轮 | 已并入 `preview.py report` |
| `preview_formal_input.py` | 第二轮 | 已并入 `preview.py plan` |

## 未单独快照的 4 个文件（代码仍逐字保存在合并模块中）

第三轮合并时这些文件已在更早的步骤中删除，`cp` 未能取到，因此这里没有它们的副本。
**代码本身没有丢失**，位置如下：

| 原文件 | 现位置 | 被剥离的内容 |
| --- | --- | --- |
| `numeric_fidelity.py` | `fidelity.py` 第 5–147 行 | 模块 docstring；`from decimal import Decimal, InvalidOperation`、`import re`；`check_plan` 已改名为 `check_numeric_plan` |
| `address_fidelity.py` | `fidelity.py` 第 148–180 行 | 模块 docstring；`import re`；`check_plan` 已改名为 `check_address_plan` |
| `automatic_triage.py` | `review.py` 第 5–72 行 | 模块 docstring；无 import |
| `review_observability.py` | `review.py` 第 73–138 行 | 模块 docstring；`import argparse`、`import json`、`from pathlib import Path` |

除上表列出的剥离项与两处 `check_plan` 改名外，函数体逐字未改。
`evaluation/fresh_holdout_01/manifest.json` 的 `code_sha256` 记录了改动前
`numeric_fidelity.py` / `address_fidelity.py` / `automatic_triage.py` 的哈希，
可用于核对——但该字段已在第三轮重新基线，原值只保留了前 12 位。
