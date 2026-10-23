# 阶段二批量运行汇总

- 提供方/模型: deepseek / deepseek-flash
- Prompt 版本: semantic-live
- 案例数: 5（新跑 5，续跑跳过 0）
- 输出目录: /root/sc_slicer_standalone/tools/report_constraints_v2/evaluation/prompt_live9_blind_01/runs

| 案例 | 退出码 | 验收状态 |
| --- | ---: | --- |
| Intuition_2VUsxVJwReb__2Funzps4cEA__gqU56aaTN9t | 0 | candidate_checks_passed |
| GTE_Perps_and_Launchpad_gtn2Umg6KsC__SBwfMsREtBu__Zp2vYG5pWXh | 2 | needs_review |
| Ekubo_3FTodhsvBkM__NCCWNLzZ86f__bKb5Sm2R6Jq | 2 | needs_review |
| SukukFi_syLyTBz5KNA__x8fhQug5RF4__mkWW7kCx5mP | 2 | needs_review |
| Merkl_T4ExvutBBXC__tcCwbNe7Mvd__AyWtdKJuDBM | 2 | needs_review |

Z3 结果只证明生成公式内部关系，不代表报告语义正确或 PoC 一致。
`needs_review` 不是通过。
