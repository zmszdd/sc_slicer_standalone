# 开发集与锁定测试集合同（2026-11-17）

本文件冻结当前主线的数据划分与指标口径。目标是避免把 dev 案例反复当作
测试集，也避免把同一项目的相关 finding 当成独立样本。

## 数据划分

| 数据集 | 规模 | 用途 | 是否可调参 |
| --- | ---: | --- | --- |
| dev252 | 252 正样本，约 72 个可评测负样本 | 开发、失败归因、回归 | 是 |
| reserve_same_project | 1213 正样本 | 同项目诊断保留池 | 不作为独立测试 |
| locked test | 待分配 | 论文最终一次性评估 | 否 |

dev252 已覆盖全部 20 个项目；剩余 1213 个正样本仍来自同一批项目，因此不能
作为独立泛化测试集。锁定测试集必须来自新项目，并在代码、prompt、绑定规则、
质量门和 reference patch 冻结后一次性运行。

当前主口径抽样已排除全部冻结 dev252/dev24 正例以及已用于调参的负例。剩余
未参与调参的负例只有 7 个，因此现有样本不能给出可信的精确率区间；锁定测试
集必须优先补足至少 40 个未用于调参的负样本。

建议测试集最低规模：80 个正样本 + 40 个负样本；更稳妥的规模是 150 个正样本
+ 60 个负样本，并覆盖至少 5 个项目。

## 四指标

主表固定为准确率、精确率、召回率、F1：

| 指标 | 定义 |
| --- | --- |
| 准确率 | `(TP + TN) / (TP + FP + FN + TN)` |
| 精确率 | `TP / (TP + FP)` |
| 召回率 | `TP / (TP + FN)` |
| F1 | `2 * precision * recall / (precision + recall)` |

四个指标来自同一个冻结混淆矩阵，但分母按定义不同。不能为了“分母统一”而
强行让精确率和召回率共用一个分母。

完成率是单独的漏斗指标，不是四指标之一：

`stage3 terminal done / eligible inputs`

dev252 的完成率是 100%，只说明这 252 个已选案例跑完，不代表全量覆盖。

## 项目聚类

同一项目的多个 finding 高度相关。置信区间必须同时提供：

- Wilson 区间，用于单案例二项比例。
- 按项目 cluster bootstrap 的区间，用于避免把同项目 finding 当独立样本。

当前 dev252 指标合同在：

- `tools/stage3/evaluation/metrics/dev252_contract_20261117.json`
- `tools/stage3/evaluation/frozen/experiment_split_20261117.json`

## dev24 回归集

`tools/stage3/evaluation/frozen/dev24_20261117.json` 是冻结的分层开发集：

- 18 个正样本：覆盖 `partial_binding`、`invariant_holds_on_exploit_path`、
  `poc_not_witnessed`、`mixed_non_dynamic`、`compile_error`、
  `binding_error`、`reference_patch_required` 和 1 个 TP。
- 6 个负样本：SukukFi 影响不足家族、GTE Perps、GTE Spot、Kinetiq。
- 覆盖 11 个项目。

运行命令不调用 LLM，只复用已有 stage2/bindings：

```bash
cd tools/stage3
python evaluation/metrics/run_dev_24.py
```

最近一次结果见 `tools/stage3/evaluation/metrics/dev24_results.md`。该结果只用于
开发回归，不进入论文测试集。

验收门：

- 负样本 `violation_reproduced` 为 0。
- 负样本不能被 `binding_error` / `compile_error` / `partial_binding` 记为 TN；
  未决负样本必须保持 `unresolved`，并使验收失败。
- 正样本 TP 不低于冻结基线。dev24 刻意覆盖 17 个 FN 和 1 个 TP，基线
  TP 为 1/18；因此 50% 是独立报告目标，不是这个失败过采样回归集的通过线。
- 所有运行完成；`binding_error` / `compile_error` 保留为未决失败，不能算 TN。

## 生成合同

```bash
cd /root/sc_slicer_standalone
python tools/stage3/evaluation/metrics/build_dev_24.py
python tools/stage3/evaluation/metrics/experiment_contract.py
```

## 测试集纪律

- 开发期间不读取、不运行锁定测试集。
- 测试集运行前冻结代码、prompt、绑定规则、质量门和 reference patch。
- 测试集统一全跑一次，不按案例挑选、不在看结果后逐例改绑定。
- 测试失败后重新调优，再跑同一测试集只能记作新一轮 dev，不能继续声称无偏测试。
