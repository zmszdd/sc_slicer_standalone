# 阶段二批量运行汇总

- 提供方/模型: deepseek / deepseek-flash
- Prompt 版本: semantic-live
- 案例数: 5（新跑 5，续跑跳过 0）
- 输出目录: /root/sc_slicer_standalone/tools/report_constraints_v2/evaluation/prompt_live8_blind_01/runs

| 案例 | 退出码 | 验收状态 |
| --- | ---: | --- |
| GTE_Perps_and_Launchpad_gtn2Umg6KsC__rNLC57pRsAp__JwTZ4f4LcDt | 0 | candidate_checks_passed |
| Hybra_Finance_xo4hapwL2Jy__7LKTwwSAteH__RJL265RJLXi | 0 | candidate_checks_passed |
| SukukFi_syLyTBz5KNA__6N4VUdiTEaa__iyMosE3F6dn | 0 | candidate_checks_passed |
| Merkl_T4ExvutBBXC__Sg7JmYgNm2Q__YDk3PgCazED | 0 | candidate_checks_passed |
| Ekubo_3FTodhsvBkM__uPQxpkt7qin__YcMX4iofLQq | 2 | needs_review |

Z3 结果只证明生成公式内部关系，不代表报告语义正确或 PoC 一致。
`needs_review` 不是通过。
