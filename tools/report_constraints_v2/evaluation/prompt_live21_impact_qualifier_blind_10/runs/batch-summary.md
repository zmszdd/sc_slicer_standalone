# 阶段二批量运行汇总

- 提供方/模型: deepseek / deepseek-flash
- Prompt 版本: semantic-live
- 案例数: 5（新跑 5，续跑跳过 0）
- 输出目录: /root/sc_slicer_standalone/tools/report_constraints_v2/evaluation/prompt_live21_impact_qualifier_blind_10/runs

| 案例 | 退出码 | 验收状态 |
| --- | ---: | --- |
| Intuition_2VUsxVJwReb__6YNDfbQYkTa__2eVNL5tctSs | 2 | rejected |
| Kinetiq_k8aVPPVguSE__RgR7qqbXSj5__j9vyLbDrzTF | 2 | needs_review |
| Merkl_T4ExvutBBXC__9JnmzBSjjfp__akaphVqkuAe | 2 | needs_impact_review |
| Monetrix_L3gNZDymiju__XdnQZTBJovh__KpjbQkQpi7c | 2 | needs_impact_review |
| Morpheus_kdPtwopH6ws__HiE7tespTT5__kYHHiGvqEun | 2 | needs_review |

Z3 结果只证明生成公式内部关系，不代表报告语义正确或 PoC 一致。
`needs_review` 不是通过。
