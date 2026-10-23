# 阶段二批量运行汇总

- 提供方/模型: deepseek / deepseek-flash
- Prompt 版本: semantic-live
- 案例数: 5（新跑 5，续跑跳过 0）
- 输出目录: /root/sc_slicer_standalone/tools/report_constraints_v2/evaluation/prompt_live11_impact_scope_01/runs

| 案例 | 退出码 | 验收状态 |
| --- | ---: | --- |
| GTE_Spot_CLOB_and_Router_qa8y3zjgyCn__vcmNqStwjRg__j3xMh3SVNn4 | 0 | candidate_checks_passed |
| Hybra_Finance_xo4hapwL2Jy__jegipCJB5Kv__kLAgbLmbZBr | 2 | needs_review |
| Intuition_2VUsxVJwReb__tL7q4xnt4Jh__5N5xEprmme7 | 2 | rejected |
| Kinetiq_k8aVPPVguSE__RgR7qqbXSj5__9bsTwrtqCED | 0 | candidate_checks_passed |
| Merkl_T4ExvutBBXC__kvqzFvQzjLT__TdqjXibtNq9 | 0 | candidate_checks_passed |

Z3 结果只证明生成公式内部关系，不代表报告语义正确或 PoC 一致。
`needs_review` 不是通过。
