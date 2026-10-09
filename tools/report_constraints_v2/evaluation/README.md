# 评测目录索引

本目录保存冻结选择、模型原始输出、评分和单次实验报告。目录名中的版本号是实验身份，不能
因为代码升级而覆盖或改名。

## 布局（2026-10-08 结构优化后）

```text
evaluation/
  prompt_live1–4_blind_01/   live 时代盲测批次（当前证据链）
  final_holdout_01/ 02/      终测批次（含 stage3 一致性回路）
  fresh_holdout_01/          首批八份新报告测试
  accuracy_gold_01/          两阶段盲金裁判准确率测评
  gold_v1/ multi_report_01/  金标准材料 / 多报告实验
  new_sc_injection_01/ 02/   新 SC 注入（01 原型；02 单文件管线）
  archive/                   2026-09 v3.x 时代全部批次（只读历史）
```

## 当前优先查看

| 目录 | 作用 |
| --- | --- |
| `accuracy_gold_01/` | 准确率测评（两阶段盲金裁判，含可信度边界分析） |
| `final_holdout_02/` | semantic-live 收口后终测 |
| `new_sc_injection_02/` | 新 SC 单文件管线：一条命令合并→执行→判读→投阶段三 |
| `prompt_live4_blind_01/` | 最新盲测批次（accuracy_gold 与 new-SC 的 run 来源） |
| `archive/` | v3.x 迭代史（含 GENERALIZATION_PROTOCOL.md 等旧索引） |

## archive/ 边界（如实披露）

- 内容 = 2026-09-16 ~ 09-23 的全部 v3.x 批次（v3 ~ v320、deepseek pilot、
  recovery、input gate 等），**零删除**，git mv 归档。
- archive 内脚本因目录深度加深一级（`HERE.parents[1]` 假设被打破）**不再
  原地可运行**；重放历史分析需 checkout 归档前的提交。
- 未来选样的历史排除集不受影响：`select.py` 系用 `rglob` 扫全 evaluation
  树的 `provenance.json` / `SELECTION.json`，archive 仍在树内。
- `archives/`（仓库根）与本目录无关，是更早的遗留清理快照。

## 可再生即删规则（成文）

| 产物类别 | 能否再生 | 处置 |
| --- | --- | --- |
| 模型产物（neural-*、prompt、冻结 run 全套） | 不能（模型输出不可复现） | 必须保留 |
| 结论记录（REPORT/README、verdict、判读表、bindings） | 不能（是当时结论的事实记录） | 保留 |
| 确定性脚本生成物（new-SC 的 `new_sc__*/`、`run_copy__*/`、forge 产物） | 能（输入+脚本全在仓库，一条命令重跑） | 可删，只留结论留档 |

例：`new_sc_injection_01/02` 的生成物目录已删除，ingest 结果留档为
`stage3-consistency__<case>.json`；重跑 `run_injection.sh` / `new_sc.py
<case_key>` 即复原（02 曾逐项复现 01 的结果，可重放性已实证）。

## 命名规则

```text
prompt_v<版本>_<性质>_<序号>/
```

- `development`：允许用于改规则，只能说明缺陷是否复现；
- `holdout`：规则冻结后才运行，用于观察泛化；
- `smoke` / `pilot`：只证明工程链或传输可用；
- `recovery` / `salvage`：失败恢复实验，不计原批次成绩。

每次新实验必须创建新目录，并至少保存：输入清单、运行参数、原始结果、汇总 `REPORT.md`
和准确率边界。不要删除失败输出，也不要把开发集比例写成总体准确率。
