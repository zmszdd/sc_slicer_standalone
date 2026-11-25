# 论文指标证据表（development-only companion）

> 本表解释权威四指标；权威数值只来自 `tools/stage3/evaluation/metrics/mainline_metrics.json`。

## 1. 权威主表

- protocol: `mainline/1.7.36`
- scope: `source-code/report consistency`
- 正例已评测: 35/40
- 负例已评测: 10/40 (witness eligible 0)

| 指标 | 数值 | 95% CI |
| --- | ---: | --- |
| Accuracy（consistency，保守） | 20.0% | 11.2%–33.0% |
| Recall（consistency，保守，未评测计 FN） | 25.0% | 14.2%–40.2% |
| Precision（consistency，已评测） | 50.0% | 29.9%–70.1% |
| F1（consistency，保守） | 0.3333 | 6.7%–50.0% |

> 已评测条件口径 recall=20.0%、F1=0.3333 只作诊断；主表口径与 `metric_alignment_report` 一致。

混淆矩阵：TP_consistency 10 / FN_consistency 25 / 未评测 5 / TN 0 / FP_vuln 0 / FP_raw 10（影响不足 10）。

## 1a. 同协议漏洞级伴生口径

- Precision（vuln，诊断）：100.0% 95% CI 64.6%–100.0%
- Recall（vuln，诊断）：20.0%
- F1（vuln，诊断）：0.3333

## 1b. consistency 已评测条件口径

- Precision（consistency，条件）：50.0% 95% CI 29.9%–70.1%
- Recall（consistency，诊断）：28.6%
- F1（consistency，诊断）：0.3636

> 主表 consistency 口径由独立 V witness 决定 TP/FP；TN 必须有 eligible negative witness 且没有 V witness。漏洞级指标只作伴生诊断，不替代主表。

- revert-witness 重新裁决：2 个 TP（policy `revert-call-is-vulnerable-operation/1`，原始 verdict 保留）

## 2. dev252 开发集对照（不得作为主表）

| 口径 | 数值 | 分子/分母 | 说明 |
| --- | ---: | ---: | --- |
| 条件 recall | 68.7% | 173/252 | 仅已跑完 252 例 |
| 覆盖感知下界（不是 dev252 recall） | 11.8% | 173/1465 | 全部相关正例候选，另一个问题 |
| 判例 precision | 92.5% | 173/(173+14) | 开发期 blind-invalid 负例 |
| 漏洞级 precision | 98.3% | — | 排除影响不足 FP |
| 条件 F1 | 0.7880 | — | 使用条件 recall |
| 全正例 F1 粗算 | 0.2094 | — | 使用全正例 recall 下界 |
| 完成率 | 17.2% | 252/1465 | dev252 是已完成子集 |

## 3. 当前失败根因（claim 级）

unit: claim-level verdicts in current-protocol eval files; not case-level confusion matrix

| 分组 | claims | 正例 | 负例 | 说明 |
| --- | ---: | ---: | ---: | --- |
| `stage2_review_required` | 35 | 34 | 1 | stage2 contract blocked by feedback or review |
| `binding_or_observability` | 27 | 11 | 16 | P/I/V cannot be bound to code observables |
| `no_violation_observed` | 17 | 5 | 12 | ran to completion without reproducing the claimed violation |
| `effect_witness` | 15 | 11 | 4 | exploit action ran but independent effect was not witnessed |
| `reference_or_external_route` | 12 | 6 | 6 | needs reference patch or external-state witness |
| `compile_or_harness` | 10 | 3 | 7 | forge harness or injected project failed to compile |
| `reproduced` | 8 | 7 | 1 | claim reproduced |

## 4. 门禁证据

| gate | value |
| --- | --- |
| protocol | `mainline/1.7.36` |
| protocol sha256 | `0bd0e65e2f609b7675429fac3dadec7225913d19ca044308e0502542def3ed15` |
| locked_ready | true |
| locked_publishable | false |
| publication status | `coverage-limited` |
| primary publishable | false |
| primary publication status | `coverage-limited` |
| positive coverage | 35/40 = 87.5% |
| negative coverage | 11/40 = 27.5% |
| dev252 eligible_current | 0 |
| dev252 in authoritative denominator | false |
| mainline current-only | true |
| legacy diagnostics gating | false |

### Publication blockers

- eligible negatives below publication floor: 11 < 24 (FPR upper95 23.8% > 12%)
- label review required for 2 negative case(s): GTE_Spot_CLOB_and_Router_qa8y3zjgyCn__W3F7ikgZG3G__MDvgv55V6yC, Kinetiq_k8aVPPVguSE__ebbaGD7Ucod__4DNu4EkJqs3

## 5. 解释

- dev252 recall 68.7% is correctly computed on the frozen 252 development cases; cases outside dev252 are not part of that denominator.
- 173/1465 is not dev252 recall; it is a separate coverage-aware lower bound over all relevant positive candidates because only 252/1465 candidates had completed stage3 when dev252 was frozen.
- current authoritative consistency recall is 25.0% over 10/40 sampled locked positives with unevaluated cases counted as FN; conditional recall over evaluated cases is 20.0% over 10/35.
- the conditional-vs-conditional gap (68.7% dev vs 20.0% locked) remains real and is attributable to development tuning, older protocol, semantic observability and distribution shift, not merely denominator choice.
- the main technical bottleneck is semantic observability and effect witness, not a single compile/API failure; negative cases without an eligible witness remain unresolved and do not become TN.

## 6. 方案执行状态

- `phase_a_evidence_closure`: executed by this report
- `phase_b_protocol_upgrade_and_full_rerun`: not executed; requires explicit quota approval because prior bounded repairs produced 0 TP
- `dev252_negative_substitution`: rejected
