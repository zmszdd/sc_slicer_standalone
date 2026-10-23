# 评测目录索引

本目录保存冻结选择、模型原始输出、评分和单次实验报告。目录名中的版本号是实验身份，不能
因为代码升级而覆盖或改名。

## 布局（2026-10-12 新 SC 工作废弃后）

```text
evaluation/
  prompt_live1–4_blind_01/   live 时代盲测批次
  prompt_live5_fidelity_01/  2026-10-20 当前 live 忠实度测量（n=5）
  prompt_live6_fidelity_01/  2026-10-20 覆盖/关系精度修改后的复测（n=5）
  final_holdout_01/ 02/      终测批次（含 stage3 一致性回路）
  fresh_holdout_01/          首批八份新报告测试
  accuracy_gold_01/          两阶段盲金裁判准确率测评
  gold_v1/ multi_report_01/  金标准材料 / 多报告实验
  archive/                   只读历史（v3.x 批次 + new_sc_injection_01/02）
```

2026-10-12：**新 SC 生成/注入工作整体废弃**。`new_sc_injection_01/`（原型）
与 `new_sc_injection_02/`（单文件管线 + bisection 归因实验）均按
"零删除、git mv 归档"惯例移入 `archive/`。阶段二→阶段三的闭环走
`main.py stage3-feedback`（`lib/stage3_consistency.py`），与新 SC 无关。
活跃代码（lib/、cli/、tests/）零依赖这两个目录。

## 当前优先查看

| 目录 | 作用 |
| --- | --- |
| `prompt_live23_relation_context_generation_frozen_10/` | semantic-live-23 将报告关系上下文同时交给规则生成与一次生成后审查；基于 live-21 的 52 组冻结来源与 live-22 配对复测 |
| `prompt_live22_relation_context_frozen_10/` | semantic-live-22 只向生成后审查提供关系上下文；作为 live-23 的同来源基线 |
| `accuracy_gold_01/` | 准确率测评（两阶段盲金裁判，含可信度边界分析） |
| `final_holdout_02/` | semantic-live 收口后终测 |
| `prompt_live5_fidelity_01/` | 当前 semantic-live 忠实度测量、两阶段盲评和异构复核 |
| `prompt_live6_fidelity_01/` | 覆盖和关系精度修改后的冻结复测；含数值门回归、双重盲评、离线重放及覆盖清单 |
| `prompt_live10_blind_20/` | 20 例 P/I/V 报告忠实度复核；新旧评分口径及盲评原始数据分别留存 |
| `prompt_live20_impact_qualifier_blind_10/` | 八项 Impact 上限与 `/6` 限定语契约的 10 例盲测；含逐字来源检查、零调用重放和未完成项说明 |
| `prompt_live16_impact_modal_blind_10/` | Impact 提取漏项及 P/I/V 弱化的人工对照记录 |
| `prompt_live23_impact_qualifier_blind_10/` | 修正逐类别模板字段后的 10 例盲测；含 P/I/V 盲审和零调用重放 |
| `prompt_live28_report_scope_blind_10/` | semantic-live-15 + report-json-input/5 的 10 例新盲测；检查推荐修复中的 I 证据、完整来源候选和零调用重放 |
| `prompt_live29_complete_piv_denominator_blind_10/` | 当前阶段二完整 P/I/V 分母口径盲测；10 例、7/31 规则化通过、10/10 零调用重放 |
| `prompt_live31_multi_i_blind_10/` | semantic-live-17 多 I 来源独立规则化；10 例、9/28 Impact 完整通过、43 个 I 来源对、10/10 零调用重放 |
| `prompt_live4_blind_01/` | live-4 最终迭代批次 |
| `archive/` | v3.x 迭代史 + 新 SC 01/02 归档（含 GENERALIZATION_PROTOCOL.md 等旧索引） |

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
| 确定性脚本生成物（如归档 new-SC 的 `new_sc__*/`、`run_copy__*/`、forge 产物） | 能（输入+脚本全在仓库，一条命令重跑） | 可删，只留结论留档 |

例：归档前 `new_sc_injection_02` 的生成物目录已删除，ingest 结果留档为
`stage3-consistency__<case>.json`（02 曾逐项复现归档的 01 原型结果，
可重放性已实证；重放需 checkout 归档前的提交）。

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

## 当前标准：只评 P/I/V 是否忠于报告

新评测只对已经生成的 P、I、V 公式逐项评分：`pass` 表示报告支持且关键方向、条件和限定语得到保留；`partial` 表示仍有报告依据但弱化或遗漏了重要条件；`fail` 表示与报告矛盾或加入无依据的实质内容；没有公式时标记 `not_evaluable`。

影响清单是否完整、未形式化的数量、求解器结果及后续阶段就绪状态不进入忠实度评分。它们不会降低某个已生成 P/I/V 与报告之间的忠实度判断。没有可评公式时，整体结果为 `not_evaluable`；其他情况下，整体结果只由可评的 P/I/V 评分汇总。

阶段二规则化成功率单独统计：分母只包含适用性判定选中的、P/I/V 各有报告依据的影响项；报告没有明示前提时允许 P 为空。缺少必要 P/I/V 来源的项不计入该指标的分子、分母或汇总数量。完整来源项后续公式失败仍保留在分母；分子为完成规则化且通过候选检查的项数。运行产物记录合格项 ID 和适用性判定，方便零模型调用复核。没有合格项时成功率为不适用。该指标的自动资格判定基于模型选择及确定性来源校验，不等同于独立人工确认。

此前批次按覆盖与忠实度混合口径产生的报告保留为历史记录，不能与此标准下的 P/I/V 忠实度分数直接比较。评审复用生成模型时，必须说明这不是独立人工金标准。
