# 阶段二批量运行汇总

- 提供方/模型: deepseek / deepseek-flash
- Prompt 版本: semantic-live
- 案例数: 5（新跑 5，续跑跳过 0）
- 输出目录: /root/sc_slicer_standalone/tools/report_constraints_v2/evaluation/prompt_live23_impact_qualifier_blind_10/runs

| 案例 | 退出码 | 验收状态 |
| --- | ---: | --- |
| Kinetiq_k8aVPPVguSE__Et2e5TnpUga__ABT7GcH3UgF | 2 | needs_review |
| Merkl_T4ExvutBBXC__V6VRqYmA4BA__MZCDvNevrjd | 2 | needs_review |
| Monetrix_L3gNZDymiju__R52fkgDFn8b__WpPX8bBkuU9 | 0 | candidate_checks_passed |
| Olas_j3PRAMM3fVq__zS6WfDd68Ch__kg2Rc6xU9ez | 2 | needs_review |
| Panoptic_Hypovault_c9MhophgwGP__hUApqN6dqiF__TXCtshwSvS2 | 2 | needs_review |

Z3 结果只证明生成公式内部关系，不代表报告语义正确或 PoC 一致。
`needs_review` 不是通过。
