# 阶段二批量运行汇总

- 提供方/模型: deepseek / deepseek-flash
- Prompt 版本: semantic-live
- 案例数: 5（新跑 5，续跑跳过 0）
- 输出目录: /root/sc_slicer_standalone/tools/report_constraints_v2/evaluation/prompt_live15_impact_modal_blind_05/runs

| 案例 | 退出码 | 验收状态 |
| --- | ---: | --- |
| Brix_Money_qy7NXr77sDh__PGwVR6CTD6U__5pt4vrEZuyz | 0 | candidate_checks_passed |
| Covenant_d4uY8y2AMSs__Jk2Mbvck9TA__KY7fciERz5c | 2 | needs_impact_review |
| Ekubo_3FTodhsvBkM__dtK3s8JSnTx__JjiXEStHW6S | 0 | candidate_checks_passed |
| Forte__Float128_Solidity_Library_evjHaYmvKxh__XC3hjxc6iXk__byxbibYSNcy | 0 | candidate_checks_passed |
| GTE_Perps_and_Launchpad_gtn2Umg6KsC__7yYS2jorBMq__SyZM6dWoy4F | 0 | candidate_checks_passed |

Z3 结果只证明生成公式内部关系，不代表报告语义正确或 PoC 一致。
`needs_review` 不是通过。
