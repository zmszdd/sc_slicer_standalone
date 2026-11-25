# 指标对齐报告（companion，不改写权威指标）

> 权威来源始终是 `tools/stage3/evaluation/metrics/mainline_metrics.json`。本报告只固定命名、分母和禁止比较项。

protocol: `mainline/1.7.36`；locked_ready=true；vuln_companion_publishable=false；vuln_companion_status=`coverage-limited`。

主表一致性发布状态：publishable=false；status=`coverage-limited`。

覆盖：正例 35/40；负例 11/40。

## 1. 论文主表：仅以下四项

| canonical key | 名称 | 值 | 95% CI | 分母/公式 | 允许用途 |
| --- | --- | ---: | --- | --- | --- |
| `mainline_accuracy_consistency_conservative` | Accuracy (consistency, conservative) | 0.2000 | 11.2%–33.0% | 10/50：(TP_consistency + TN) / (all sampled positives + evaluated negatives) | paper main table |
| `mainline_recall_consistency_conservative` | Recall (consistency, conservative) | 0.2500 | 14.2%–40.2% | 10/40：TP_consistency / all sampled positives; unevaluated as FN | paper main table |
| `mainline_precision_consistency_evaluated` | Precision (consistency, evaluated) | 0.5000 | 29.9%–70.1% | 10/20：TP_consistency / (TP_consistency + FP_consistency) | paper main table |
| `mainline_f1_consistency_conservative` | F1 (consistency, conservative) | 0.3333 | 6.7%–50.0% | derived：derived from precision_consistency and conservative recall_consistency | paper main table |

发布阻塞：

- eligible negatives below publication floor: 11 < 24 (FPR upper95 23.8% > 12%)
- label review required for 2 negative case(s): GTE_Spot_CLOB_and_Router_qa8y3zjgyCn__W3F7ikgZG3G__MDvgv55V6yC, Kinetiq_k8aVPPVguSE__ebbaGD7Ucod__4DNu4EkJqs3

一致性发布状态：`coverage-limited`；publishable=false。
一致性覆盖：正例 35/30；witness 负例 10/24。

一致性发布阻塞：

- evaluated negatives below consistency floor: 10 < 24
- consistency FPR upper95 above publication cap: 100.0% > 20%
- label review required for 2 negative case(s)

## 2. 同协议诊断指标（不得进入主表）

| canonical key | 名称 | 值 | 95% CI | 分母/范围 |
| --- | --- | ---: | --- | --- |
| `diagnostic_completion_rate` | Completion rate | 0.9722 | — | evaluated cases + explicit failures |
| `diagnostic_completion_sample_wide` | Completion lower bound | 0.8750 | — | all sampled cases |
| `diagnostic_recall_vuln_evaluated` | Recall (vuln, evaluated) | 0.2000 | 10.0%–35.9% | evaluated positives only |
| `diagnostic_recall_sample_wide` | Recall lower bound | 0.1750 | 8.8%–31.9% | all sampled positives, unevaluated as FN |
| `diagnostic_recall_automatic` | Recall (automatic route) | 0.2000 | 10.0%–35.9% | evaluated positives, automatic route |
| `diagnostic_accuracy_vuln_evaluated` | Accuracy (vuln, evaluated) | 0.2000 | 10.0%–35.9% | vuln matrix |
| `diagnostic_recall_vuln_conservative` | Recall (vuln, conservative) | 0.1750 | 8.8%–31.9% | all sampled positives, unevaluated as FN |
| `diagnostic_precision_vuln_evaluated` | Precision (vuln, evaluated) | 1.0000 | 64.6%–100.0% | TP / (TP + FP_vuln) |
| `diagnostic_f1_vuln_conservative` | F1 (vuln, conditional) | 0.3333 | — | derived from precision_vuln and evaluated recall |
| `diagnostic_accuracy_consistency_evaluated` | Accuracy (consistency, evaluated) | 0.2222 | 12.5%–36.3% | consistency matrix; evaluated denominator |
| `diagnostic_precision_consistency` | Precision (consistency, evaluated) | 0.5000 | 29.9%–70.1% | TP / (TP + FP_consistency) |
| `diagnostic_f1_consistency_evaluated` | F1 (consistency, evaluated) | 0.3636 | — | derived from precision_consistency and recall |
| `diagnostic_f1_vuln_evaluated` | F1 (vuln, evaluated) | 0.3333 | — | derived from precision_vuln and evaluated recall |
| `diagnostic_recall_cluster_bootstrap` | Recall cluster CI | n/a | 3.1%–38.9% | project cluster bootstrap |
| `diagnostic_precision_vuln_cluster_bootstrap` | Precision cluster CI | n/a | 100.0%–100.0% | project cluster bootstrap |

## 3. dev252 开发集回顾（不得作为权威主表）

status: `development-only; not authoritative; not a locked test`

| canonical key | 值 | 分子/分母 | 允许用途 |
| --- | ---: | --- | --- |
| `dev252_conditional_recall` | 0.6865 | 173/252 | development retrospective with denominator |
| `dev252_full_pool_recall_lower_bound` | 0.1181 | 173/1465 | coverage-only; not dev252 recall |
| `dev252_completion` | 0.1720 | 252/1465 | coverage-only; not performance |
| `dev252_judged_precision` | 0.9251 | 173/(173+14) | development retrospective only |
| `dev252_vulnerability_precision` | 0.9830 | — | development retrospective only |
| `dev252_conditional_f1` | 0.7880 | — | development retrospective only |
| `dev252_full_pool_f1_rough` | 0.2094 | — | rough lower bound only |

关键点：`173/252 = 68.7%` 是 dev252 条件 recall；`173/1465 = 11.8%` 是全正例覆盖感知下界，不是 dev252 recall。

## 4. A+/hardened/top3 smoke（不得与主线比较）

protocol: `mainline/1.6.1`；reportable=false；scope: resolved-only 64-case smoke; blind-invalid negative pool。

| metric | 值 |
| --- | ---: |
| `accuracy` | 0.7297 |
| `recall` | 0.8125 |
| `precision_vuln` | 1.0000 |
| `precision_consistency` | 0.8667 |
| `f1_vuln` | 0.8966 |

## 5. 命名规则

| 歧义写法 | canonical key | 规则 |
| --- | --- | --- |
| `accuracy` | `mainline_accuracy_consistency_conservative` | must state consistency level and conservative denominator |
| `recall` | `mainline_recall_consistency_conservative` | must state consistency level and conservative denominator |
| `precision` | `mainline_precision_consistency_evaluated` | must state whether consistency, vuln, judged, or smoke |
| `F1` | `mainline_f1_consistency_conservative` | must state which precision and recall denominators are paired |
| `vuln precision` | `diagnostic_precision_vuln_evaluated` | vuln-level precision is a companion diagnostic, not the paper main table |
| `dev252 recall` | `dev252_conditional_recall` | must state the frozen 252-case conditional denominator |
| `173/1465` | `dev252_full_pool_recall_lower_bound` | must not be named dev252 recall |
| `A+/hardened recall` | `smoke_aplus_hardened_recall` | must carry reportable=false and old-protocol status |
| `completion rate` | `diagnostic_completion_rate` | must not be used as accuracy, recall, or precision |

## 6. 禁止比较

| id | 对象 | 判定 | 原因 |
| --- | --- | --- | --- |
| `dev252_vs_mainline_recall` | dev252_conditional_recall, diagnostic_recall_vuln_conservative | conditional-only-with-explicit-labels | different sample, protocol, tuning history, and negative pool |
| `full_pool_as_dev252_recall` | dev252_full_pool_recall_lower_bound, dev252 recall | forbidden | 173/1465 answers coverage, not the dev252 denominator |
| `smoke_vs_mainline` | smoke_aplus_hardened_metrics, mainline canonical four | forbidden | old protocol, resolved-only smoke, reportable=false |
| `precision_flavors` | diagnostic_precision_vuln_evaluated, mainline_precision_consistency_evaluated, dev252_judged_precision, dev252_vulnerability_precision | forbidden-without-explicit-name | different FP semantics and denominators |
| `completion_as_performance` | diagnostic_completion_rate, mainline_accuracy_consistency_conservative, mainline_recall_consistency_conservative | forbidden | completion measures execution, not vulnerability detection |
| `claim_case_unit` | claim-level verdicts, case-level confusion matrix | forbidden-without-unit-label | one case can contribute multiple claims |
| `stage2_quality_as_end_to_end` | stage2 faithfulness/formalization rates, mainline canonical four | forbidden | stage2 quality is not stage3 reproduction |
| `historical_snapshot_as_current` | 2026-11-23 historical metrics, current mainline metrics | forbidden | revert-witness re-adjudication changed TP/FN |

## 7. 论文写作合同

- Main table contains only the four canonical consistency metrics with CI, coverage, protocol, and publishable status.
- Vulnerability-level metrics appear only as explicitly named companion diagnostics and never replace the consistency main table.
- dev252 appears only as a development retrospective; 68.7% is conditional recall over 252 cases and 11.8% is a separate coverage-aware lower bound.
- A+/hardened smoke appears only as an appendix diagnostic and must carry reportable=false and protocol mainline/1.6.1.
- Precision must be named as consistency, vuln, judged, or smoke; bare "precision" is not acceptable.
- Completion, stage2 quality, and claim-level verdicts must not be presented as end-to-end case-level performance.

## 8. 数据来源

| path | sha256 |
| --- | --- |
| `tools/stage3/evaluation/metrics/mainline_metrics.json` | `d2a3bd8ea0eebfa12f2f663a689abb927820aec052b394ecda2c8f5f5b913168` |
| `tools/stage3/evaluation/metrics/aplus_hardened_report.md` | `0cbb939fc7bff188c93acc7b466f33ffe9e57410d0f5dc9927c7a70af2f91e67` |
