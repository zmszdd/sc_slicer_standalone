# 阶段二批量运行汇总

- 提供方/模型: deepseek / deepseek-flash
- Prompt 版本: semantic-live
- 案例数: 5（新跑 5，续跑跳过 0）
- 输出目录: /root/sc_slicer_standalone/tools/report_constraints_v2/evaluation/prompt_live4_blind_01/runs

| 案例 | 退出码 | 验收状态 |
| --- | ---: | --- |
| Ekubo_3FTodhsvBkM__9MpUh5dZn3f__nFbsAHPP4jP | 0 | candidate_checks_passed |
| Intuition_2VUsxVJwReb__aayBh4TiWVT__9MQnPJ8ZWP6 | 0 | candidate_checks_passed |
| Merkl_T4ExvutBBXC__tcCwbNe7Mvd__F5r4vfe7fxo | 0 | candidate_checks_passed |
| Sequence__Transaction_Rails_Yn6A3eYizcQ__7rSTe38xKPK__NDFxwkWkifi | 2 | rejected |
| Monetrix_L3gNZDymiju__vbdhAfq36PC__yDKhMdFws7C | 2 | rejected |

Z3 结果只证明生成公式内部关系，不代表报告语义正确或 PoC 一致。
`needs_review` 不是通过。
