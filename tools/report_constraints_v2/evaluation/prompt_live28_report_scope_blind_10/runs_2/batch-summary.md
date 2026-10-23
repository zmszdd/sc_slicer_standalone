# 阶段二批量运行汇总

- 提供方/模型: deepseek / deepseek-flash
- Prompt 版本: semantic-live-15
- 案例数: 5（新跑 5，续跑跳过 0）
- 输出目录: /root/sc_slicer_standalone/tools/report_constraints_v2/evaluation/prompt_live28_report_scope_blind_10/runs_2

| 案例 | 退出码 | 验收状态 |
| --- | ---: | --- |
| Hybra_Finance_xo4hapwL2Jy__7LKTwwSAteH__nVjdnogBPTM | 2 | needs_review |
| Intuition_2VUsxVJwReb__vtU4cDUiiDR__xCkRvABHXC4 | 2 | needs_review |
| Kinetiq_k8aVPPVguSE__6GBi6WQdSse__7tVr98jQuEc | 2 | needs_review |
| Merkl_T4ExvutBBXC__V6VRqYmA4BA__JdnfEeMGsvL | 0 | candidate_checks_passed |
| Monetrix_L3gNZDymiju__XdnQZTBJovh__BqP968JWuuF | 0 | candidate_checks_passed |

Z3 结果只证明生成公式内部关系，不代表报告语义正确或 PoC 一致。
`needs_review` 不是通过。
