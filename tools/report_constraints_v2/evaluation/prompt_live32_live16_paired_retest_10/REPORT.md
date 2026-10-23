# semantic-live-17 在 semantic-live-16 同一批报告上的配对复测

## 设置

- 固定使用 `prompt_live30_live16_complete_piv_blind_10` 的原始 10 份报告及相同 report 输入。
- 当前流程为 `semantic-live-17`、`report-json-input/5`、DeepSeek Flash；模型未获得参考答案。
- 两个五例批次，并发 2；readiness、要素和规则阶段各允许一次重试；与上一轮相同配置。
- 对每份产物执行零模型调用离线重放。

## 汇总

| 指标 | semantic-live-16 | semantic-live-17 复测 |
|---|---:|---:|
| 完整来源 P/I/V Impact 分母 | 24 | 28 |
| 完整规则化 Impact | 3（12.5%） | 5（17.9%） |
| 候选检查通过报告 | 1/10 | 0/10 |
| 模型调用 | 84 | 181 |
| 零调用离线重放 | 10/10 | 10/10 |

## 逐报告结果

| 报告 | 完整 P/I/V Impact | 完成规则化 | I 来源对 | 规则生成 | 忠实度通过/失败/未完成 | 候选状态 |
|---|---:|---:|---:|---:|---:|---|
| Ekubo_3FTodhsvBkM | 2 | 0 | 4 | 4 | 1/1/2 | needs_review |
| GTE_Perps_and_Launchpad_gtn2Umg6KsC | 4 | 0 | 8 | 8 | 1/0/7 | needs_review |
| GTE_Spot_CLOB_and_Router_qa8y3zjgyCn | 3 | 0 | 6 | 5 | 2/2/2 | needs_review |
| Hybra_Finance_xo4hapwL2Jy | 3 | 2 | 3 | 2 | 2/0/1 | needs_review |
| Intuition_2VUsxVJwReb | 2 | 0 | 4 | 3 | 0/1/3 | needs_review |
| Merkl_T4ExvutBBXC | 1 | 0 | 2 | 2 | 1/0/1 | needs_review |
| Monetrix_L3gNZDymiju | 4 | 0 | 4 | 4 | 0/2/2 | needs_review |
| Olas_j3PRAMM3fVq | 0 | 0 | 0 | 0 | 0/0/0 | needs_impact_review |
| Panoptic_Hypovault_c9MhophgwGP | 5 | 2 | 8 | 8 | 4/4/0 | needs_review |
| Panoptic | 4 | 1 | 4 | 4 | 2/1/1 | needs_review |

## 解读

在同一批输入上，live-17 的完整 Impact 规则化比率为 5/28，高于 live-16 的 3/24；但报告级候选通过从 1/10 降至 0/10，整份报告的可用结果没有改善。live-17 的分母由模型适用性输出形成，较 live-16 多 4 项；逐轮调用仍有模型随机性，不能把 17.9% 对 12.5% 当作纯实现效果差异。

结果仍集中在未完成规则和候选门未通过。Z3/离线重放只核对确定性工程产物，不代表语义正确或 PoC 一致。逐项原因见各报告目录中的 `stage2-assessment.json`。
