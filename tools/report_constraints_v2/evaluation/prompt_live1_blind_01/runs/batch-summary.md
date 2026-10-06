# 阶段二批量运行汇总

- 提供方/模型: deepseek / deepseek-flash
- Prompt 版本: semantic-live
- 案例数: 5（新跑 5，续跑跳过 0）
- 输出目录: /root/sc_slicer_standalone/tools/report_constraints_v2/evaluation/prompt_live1_blind_01/runs

| 案例 | 退出码 | 验收状态 |
| --- | ---: | --- |
| GTE_Spot_CLOB_and_Router_qa8y3zjgyCn__w9QuR2FriYW__bdMabawBBvS | 0 | candidate_checks_passed |
| SukukFi_syLyTBz5KNA__SZy2Ly7Y3Cu__9HhbRPvDBh5 | 0 | candidate_checks_passed |
| Hybra_Finance_xo4hapwL2Jy__SvyBC8wE6Xf__FXEN4GU5xVq | 2 | rejected |
| Kinetiq_k8aVPPVguSE__NozCq8ZgtXD__nayg2eGrYFC | 2 | rejected |
| Intuition_2VUsxVJwReb__aayBh4TiWVT__JfcE4eZnVpe | 2 | rejected |

Z3 结果只证明生成公式内部关系，不代表报告语义正确或 PoC 一致。
`needs_review` 不是通过。
