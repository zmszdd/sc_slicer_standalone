# 阶段二批量运行汇总

- 提供方/模型: deepseek / deepseek-flash
- Prompt 版本: semantic-live
- 案例数: 5（新跑 5，续跑跳过 0）
- 输出目录: /root/sc_slicer_standalone/tools/report_constraints_v2/evaluation/prompt_live29_complete_piv_denominator_blind_10/runs

| 案例 | 退出码 | 验收状态 |
| --- | ---: | --- |
| Kinetiq_k8aVPPVguSE__bP38mw3SCq2__eEvYodNRrvz | 2 | needs_review |
| Merkl_T4ExvutBBXC__kvqzFvQzjLT__nzJVM5K6Bwq | 2 | needs_review |
| Monetrix_L3gNZDymiju__R52fkgDFn8b__EkeRfzKwDzz | 0 | candidate_checks_passed |
| Olas_j3PRAMM3fVq__imB3UBHVTuv__mGy2UeVHNXC | 2 | needs_review |
| Panoptic_Hypovault_c9MhophgwGP__F87EJt3PoCN__zWcesfvRJ9N | 0 | candidate_checks_passed |

Z3 结果只证明生成公式内部关系，不代表报告语义正确或 PoC 一致。
`needs_review` 不是通过。
