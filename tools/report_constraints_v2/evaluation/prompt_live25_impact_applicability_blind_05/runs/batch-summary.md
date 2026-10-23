# 阶段二批量运行汇总

- 提供方/模型: deepseek / deepseek-flash
- Prompt 版本: semantic-live-14
- 案例数: 5（新跑 5，续跑跳过 0）
- 输出目录: /root/sc_slicer_standalone/tools/report_constraints_v2/evaluation/prompt_live25_impact_applicability_blind_05/runs

| 案例 | 退出码 | 验收状态 |
| --- | ---: | --- |
| Hybra_Finance_xo4hapwL2Jy__7RVCVStDrsF__QuG7xAnjmwi | 2 | needs_impact_review |
| Covenant_d4uY8y2AMSs__Jk2Mbvck9TA__92rPRhqqUax | 2 | needs_review |
| Intuition_2VUsxVJwReb__2Funzps4cEA__2ahP5t3rQEz | 2 | needs_review |
| SukukFi_syLyTBz5KNA__SZy2Ly7Y3Cu__rdYvsZ9wY5U | 2 | needs_review |
| GTE_Perps_and_Launchpad_gtn2Umg6KsC__qFXS4TWRDTc__x3LPkkR6mRr | 2 | needs_impact_review |

Z3 结果只证明生成公式内部关系，不代表报告语义正确或 PoC 一致。
`needs_review` 不是通过。
