# 全流程 case 级四指标（2026-11-06）

数据来源：
- 正样本：`evaluation/metrics/positive_eval_33.json`（33 个 stage1→stage2→stage3 连贯跑）
- 负样本：`evaluation/metrics/negative_results_16.json`（16 个有效负样本，全部 violation_not_reproduced）
- 指标：`evaluation/metrics/fullflow_metrics_33.json`

## 结果

| 指标 | 值 | 95% CI |
| --- | ---: | --- |
| 完成率 | 97.0%（32/33） | 84.7%–99.5% |
| 召回率（case 级） | 73.9%（17/23 可评测） | 53.5%–87.5% |
| 准确率 | 100.0%（TP=17 FP=0 TN=16） | 81.6%–100.0% |
| F1 | 0.850 | — |
| 可评测覆盖率 | 69.7%（23/33） | — |

## 分母口径

- 完成率分母 = 全部 33 个输入案例。
- 召回率分母 = 可评测案例（status=done 且至少一个动态差分终态：
  violation_reproduced / violation_not_reproduced）。
- 阶段一/二阻塞（no_stage2_run / stage2_blocked / zero_claims / no_flatten /
  no_bound_claims）与全部 claim 为 not_dynamically_expressible 的案例计入完成率与
  覆盖率，不计入召回率分母，避免把“尚未能评测”算成“漏召回”。
- 准确率 = TP / (TP+FP)；FP 只来自负样本判 violation_reproduced。

## 样本量警告（未达标）

- 正样本 33 < 40，可评测 23 < 40，复现 17 < 40。
- 有效负样本 16 < 40。
- 当前四指标只能作为链路验证，不能作为统计上可靠的最终结论。

## 本轮扩容与根因

- 26 个“有阶段二、缺 binding”正样本已批量补 binding 并跑差分（`/tmp/eval_run_nobind26.json`）。
- 20 个阶段二阻塞案例已用 `--claim-verdict signals` 重跑阶段二：7 个产出 claim 并进入
  阶段三（`/tmp/eval_run_rerun7.json`）；9 个仍 zero-claims（I-source 规则不完整），
  4 个仍无阶段二产物。
- 负样本按复现 claim 自动构造，复用 `stage3_fix_llm` 的 verbatim 修复门禁；
  6 个构造失败的负样本（5 个 Olas 修复后仍复现、1 个 compile_blocked）已剔除，不计入 TN/FP。
