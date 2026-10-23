# 阶段二批量运行汇总

- 提供方/模型: deepseek / deepseek-flash
- Prompt 版本: semantic-live
- 案例数: 5（新跑 5，续跑跳过 0）
- 输出目录: /root/sc_slicer_standalone/tools/report_constraints_v2/evaluation/prompt_live22_impact_qualifier_blind_10/runs

| 案例 | 退出码 | 验收状态 |
| --- | ---: | --- |
| Intuition_2VUsxVJwReb__6YNDfbQYkTa__EiQdak9ZfiR | 2 | needs_review |
| Kinetiq_k8aVPPVguSE__YdUkynebFvW__FCU4bMUR3hY | 0 | candidate_checks_passed |
| Merkl_T4ExvutBBXC__kvqzFvQzjLT__JePi2VXoFto | 2 | needs_impact_review |
| Monetrix_L3gNZDymiju__R52fkgDFn8b__KCWcn8VxtxH | 0 | candidate_checks_passed |
| Olas_j3PRAMM3fVq__imB3UBHVTuv__TBstmwTKUq5 | 2 | needs_impact_review |

Z3 结果只证明生成公式内部关系，不代表报告语义正确或 PoC 一致。
`needs_review` 不是通过。
