# 主口径四指标（分层随机抽样）

- 抽样：`mainline_sample_mini.json`，salt `mainline/1.7.19/mini/80`；dev252/dev24 与开发负例已排除。
- 入组：仅 fingerprint 匹配当前协议、终态且 `metric_eligibility` 为真的 claim；过期 run 正例 `0`、负例 `14` 已排除。
- refresh gate：`refresh_ready=True`，dev252 `eligible_current=0`。
- 完成率分母：已评测 `35` + 有明确失败归因 `1`（未跑 `stage3_ready` / 无归因不计入）。
- 召回分母：已评测 positive `35`（未评测 `5` 不计入）；negative 已评测 `10/40`。
- 一致性发布状态：`coverage-limited`；publishable=`False`。
- 一致性 FPR 上界（10/10）：
  100.0%，发布上限 20%。
- 负例证据：V witness FP `10` / TN witness `0`。
- 漏洞级伴生发布状态：`coverage-limited`；publishable=`False`。
- Revert-witness 重新裁决：2 个 case / 5 个 claim；仅接受 revert 发生在漏洞利用路径上的证据，原始 verdict 不变。

| 指标 | 数值 | 95% CI |
| --- | ---: | --- |
| 完成率（已评测+明确失败） | 97.2% | — |
| 完成率（样本内下界，全部 sampled positives） | 87.5% | — |
| 准确率（vuln） | 20.0% | 10.0%–35.9% |
| 准确率（consistency） | 22.2% | 12.5%–36.3% |
| 召回率（已评测口径） | 20.0% | 10.0%–35.9% |
| 召回率（项目聚类 bootstrap） | — | 3.1%–38.9% |
| 召回率（样本内下界，未评测计 FN） | 17.5% | 8.8%–31.9% |
| 召回率（自动口径，已评测） | 20.0% | 10.0%–35.9% |
| 精确率（vuln，对外主口径） | 100.0% | 64.6%–100.0% |
| 精确率（项目聚类 bootstrap） | — | 100.0%–100.0% |
| 精确率（consistency，机制一致性） | 50.0% | 29.9%–70.1% |
| F1（vuln，已评测口径） | 0.3333 | — |
| F1（保守，项目聚类 bootstrap） | — | 7.1%–50.8% |

## 主表推荐四指标（保守口径）

| 指标 | 数值 | 95% CI |
| --- | ---: | --- |
| 准确率（consistency，保守） | 20.0% | 11.2%–33.0% |
| 召回率（consistency，保守） | 25.0% | 14.2%–40.2% |
| 精确率（consistency，已评测） | 50.0% | 29.9%–70.1% |
| F1（consistency，保守） | 0.3333 | 6.7%–50.0% |

## 漏洞级伴生四指标（诊断）

| 指标 | 数值 | 95% CI |
| --- | ---: | --- |
| 准确率（vuln，已评测） | 20.0% | 10.0%–35.9% |
| 召回率（vuln，保守） | 17.5% | 8.8%–31.9% |
| 精确率（vuln） | 100.0% | 64.6%–100.0% |
| F1（vuln，保守） | 0.2979 | 7.1%–50.8% |

> 一致性主表衡量“自然语言声称效果 ↔ 源码实际效果”；漏洞级四指标只作判例影响口径的伴生诊断。
> 已评测口径 consistency recall=28.6%、F1=0.3636
> 保留为条件诊断值；主表采用未评测正例计 FN 的保守口径。
> 一致性 TP/FP 由独立 V witness 决定，I 只用于漏洞级伴生口径。
> 负例 TN 必须满足 `negative_witness.eligible=true` 且没有 V witness；
> 有 V witness 的负例记 consistency FP，无两类证据的终态负例留在 unresolved。

混淆矩阵（已评测口径）：TP 7 / TP_consistency 10 / FN 28 / 未评测 5 / FP_raw 10（影响不足 10，vuln 0）/ TN 0。

> 口径说明：论文主表使用 `canonical_metrics` 的 consistency 四指标；
> vuln 级 `accuracy` / `recall` / `precision_vuln` / `f1_vuln` 仅作伴生诊断。
> consistency 准确率使用 `(TP_consistency+TN)/(全部 sampled positives+evaluated negatives)`；
> V witness 已见证的负例仍进入 consistency FP，不因影响不足或 I 成立转 TN。
> 完成率分母 = 已评测 `35` + 明确失败归因 `1`；`stage3_ready`
> （未跑完）与 `stage2_not_attempted`（无失败原因）不计入分母。
> `completion_sample_wide` 是按全部 sampled positives 的样本内下界，仅作透明度对照。
> 主表召回与 F1 使用全部 sampled positives 作分母，未评测计 FN；
> `recall` / `f1_vuln` 是已评测 positive 的条件诊断口径，不能替代主表。
