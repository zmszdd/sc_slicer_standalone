# 阶段二批量运行汇总

- 提供方/模型: deepseek / deepseek-flash
- Prompt 版本: semantic-live
- 案例数: 5（新跑 5，续跑跳过 0）
- 输出目录: /root/sc_slicer_standalone/tools/report_constraints_v2/evaluation/prompt_live20_impact_qualifier_blind_10/runs

| 案例 | 退出码 | 验收状态 |
| --- | ---: | --- |
| Hybra_Finance_xo4hapwL2Jy__PdHz3nGsrbT__op5DuFWhJSM | 2 | needs_review |
| Intuition_2VUsxVJwReb__2Funzps4cEA__dxucZnmJesU | 2 | needs_impact_review |
| Kinetiq_k8aVPPVguSE__NozCq8ZgtXD__3rGNQuhoXNA | 2 | rejected |
| Merkl_T4ExvutBBXC__KCbBUkDmvZG__HjWCMPFpg29 | 2 | needs_review |
| Monetrix_L3gNZDymiju__vbdhAfq36PC__MiBxL7SMwLW | 2 | needs_review |

Z3 结果只证明生成公式内部关系，不代表报告语义正确或 PoC 一致。
`needs_review` 不是通过。
