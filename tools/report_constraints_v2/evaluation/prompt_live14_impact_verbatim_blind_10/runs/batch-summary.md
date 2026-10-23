# 阶段二批量运行汇总

- 提供方/模型: deepseek / deepseek-flash
- Prompt 版本: semantic-live
- 案例数: 5（新跑 5，续跑跳过 0）
- 输出目录: /root/sc_slicer_standalone/tools/report_constraints_v2/evaluation/prompt_live14_impact_verbatim_blind_10/runs

| 案例 | 退出码 | 验收状态 |
| --- | ---: | --- |
| GTE_Spot_CLOB_and_Router_qa8y3zjgyCn__LDE4mUbttzn__hT8RvDaQYeY | 0 | candidate_checks_passed |
| Hybra_Finance_xo4hapwL2Jy__qoJkZFiWFds__PRixjGrBzGQ | 2 | needs_review |
| Intuition_2VUsxVJwReb__aayBh4TiWVT__9zjimEyWcgY | 0 | candidate_checks_passed |
| Kinetiq_k8aVPPVguSE__9ghvAQQHVB2__bhjaby9ekJn | 0 | candidate_checks_passed |
| Merkl_T4ExvutBBXC__kvqzFvQzjLT__thfmBytrnVT | 2 | rejected |

Z3 结果只证明生成公式内部关系，不代表报告语义正确或 PoC 一致。
`needs_review` 不是通过。
